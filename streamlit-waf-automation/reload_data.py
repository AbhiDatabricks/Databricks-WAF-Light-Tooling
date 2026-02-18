#!/usr/bin/env python3
"""
Reload WAF dashboard data:
  1. Read dashboard_queries.yaml (single source of truth)
  2. For each active dataset, run the SQL on a Databricks warehouse
  3. Materialise results as Delta table  → {catalog}.waf_cache.{table_name}
  4. Sync results to Lakebase (Postgres) → public.{table_name}

Usage:
    python reload_data.py [--yaml PATH] [--creds PATH]

Environment overrides:
    WAF_CREDS_PATH   – path to .creds file
    WAF_YAML_PATH    – path to dashboard_queries.yaml
"""
import argparse
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import unquote

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    from databricks import sql as dbsql
except ImportError:
    print("ERROR: databricks-sql-connector not installed. Run: pip install 'databricks-sql-connector>=3.0.0'")
    sys.exit(1)

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Credentials helper
# ---------------------------------------------------------------------------

def load_creds(path: str) -> dict:
    """Parse a simple KEY=VALUE credentials file."""
    creds: dict = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            creds[k.strip()] = v.strip().strip("'\"")
    # PGPASSWORD placeholder → use the Databricks token
    if creds.get('PGPASSWORD', '').startswith('${'):
        creds['PGPASSWORD'] = creds.get('token', '')
    return creds


def find_creds(override: Optional[str] = None) -> str:
    """Locate the .creds file, searching common locations."""
    if override:
        if os.path.exists(override):
            return override
        raise FileNotFoundError(f".creds not found at: {override}")
    candidates = [
        os.environ.get('WAF_CREDS_PATH', ''),
        os.path.join(SCRIPT_DIR, '.creds'),
        os.path.join(SCRIPT_DIR, '..', 'DONOTCHECKIN', '.creds'),
        os.path.join(SCRIPT_DIR, '..', '.creds'),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError(
        "Could not find .creds file. Set WAF_CREDS_PATH or place .creds in the script directory."
    )


def find_yaml(override: Optional[str] = None) -> str:
    """Locate dashboard_queries.yaml."""
    if override:
        if os.path.exists(override):
            return override
        raise FileNotFoundError(f"YAML not found at: {override}")
    candidates = [
        os.environ.get('WAF_YAML_PATH', ''),
        os.path.join(SCRIPT_DIR, 'dashboard_queries.yaml'),
        os.path.join(SCRIPT_DIR, '..', 'DONOTCHECKIN', 'dashboard_queries.yaml'),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError(
        "Could not find dashboard_queries.yaml. Run extract_queries.py first."
    )


# ---------------------------------------------------------------------------
# Warehouse discovery
# ---------------------------------------------------------------------------

def get_warehouse_id(host: str, token: str) -> str:
    """Return the ID of the first available SQL warehouse."""
    resp = requests.get(
        f"{host}/api/2.0/sql/warehouses",
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
        timeout=30,
    )
    resp.raise_for_status()
    warehouses = resp.json().get('warehouses', [])
    if not warehouses:
        raise RuntimeError("No SQL warehouses found in this workspace.")
    # Prefer running/stopped warehouses
    for wh in warehouses:
        if wh.get('state') in ('RUNNING', 'STOPPED'):
            print(f"  Using warehouse: {wh['name']} ({wh['id']})")
            return wh['id']
    wh = warehouses[0]
    print(f"  Using warehouse: {wh['name']} ({wh['id']})")
    return wh['id']


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def substitute_date_params(sql: str) -> str:
    """Replace known dashboard parameters with concrete values."""
    now = datetime.now()
    date_end = now.strftime('%Y-%m-%d')
    date_start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    sql = sql.replace(':date_range_start', f"'{date_start}'")
    sql = sql.replace(':date_range_end', f"'{date_end}'")
    sql = sql.replace(':rollback_days', '30')  # look-back window default: 30 days
    return sql


def strip_trailing_semicolon(sql: str) -> str:
    """Remove a trailing semicolon so it can be used inside CREATE ... AS."""
    return sql.rstrip().rstrip(';').rstrip()


def sanitize_col_name(name: str) -> str:
    """Convert any string to a valid Delta column identifier."""
    import re as _re
    cleaned = _re.sub(r'[^a-zA-Z0-9_]', '_', name)
    cleaned = _re.sub(r'_+', '_', cleaned).strip('_')
    if not cleaned or cleaned[0].isdigit():
        cleaned = 'col_' + cleaned
    return cleaned or 'col'


def drop_all_tables(cursor, catalog: str):
    """Drop every data table in {catalog}.waf_cache, preserving _run_log."""
    cursor.execute(
        f"SELECT table_name FROM `{catalog}`.information_schema.tables "
        f"WHERE table_schema = 'waf_cache' AND table_type = 'MANAGED'"
        f"  AND table_name != '_run_log'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    if not tables:
        print("  waf_cache has no data tables to drop.")
        return
    for t in tables:
        cursor.execute(f"DROP TABLE IF EXISTS `{catalog}`.`waf_cache`.`{t}`")
        print(f"  Dropped: {t}")
    print(f"  Dropped {len(tables)} table(s).")


def create_delta_table(cursor, catalog: str, table: str, sql: str,
                       run_id: str, run_started_at: str):
    """
    CREATE OR REPLACE TABLE in waf_cache.
    Every table gets _run_id and _run_started_at so all tables from the same
    reload share the same identifier regardless of when each query finished.
    Falls back to sanitising column names if Delta rejects them.
    """
    wrapped = (
        f"SELECT _q.*,\n"
        f"  '{run_id}' AS _run_id,\n"
        f"  TIMESTAMP('{run_started_at}') AS _run_started_at\n"
        f"FROM (\n{sql}\n) AS _q"
    )
    full_sql = (
        f"CREATE OR REPLACE TABLE `{catalog}`.`waf_cache`.`{table}` AS\n{wrapped}"
    )
    try:
        cursor.execute(full_sql)
    except Exception as first_err:
        if 'DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES' not in str(first_err):
            raise
        # Sanitise column names via a temp view
        tmp = f"_waf_tmp_{table}"
        cursor.execute(f"CREATE OR REPLACE TEMPORARY VIEW `{tmp}` AS\n{sql}")
        cursor.execute(f"SELECT * FROM `{tmp}` LIMIT 0")
        raw_cols = [desc[0] for desc in cursor.description]
        renames = ', '.join(
            f'`{c}` AS `{sanitize_col_name(c)}`' for c in raw_cols
        )
        cursor.execute(
            f"CREATE OR REPLACE TABLE `{catalog}`.`waf_cache`.`{table}` AS\n"
            f"SELECT {renames},\n"
            f"  '{run_id}' AS _run_id,\n"
            f"  TIMESTAMP('{run_started_at}') AS _run_started_at\n"
            f"FROM `{tmp}`"
        )
        cursor.execute(f"DROP VIEW IF EXISTS `{tmp}`")


def ensure_run_log(cursor, catalog: str):
    """Create _run_log table if it doesn't exist."""
    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS `{catalog}`.`waf_cache`.`_run_log` ("
        f"  run_id STRING,"
        f"  triggered_at TIMESTAMP,"
        f"  finished_at TIMESTAMP,"
        f"  status STRING,"
        f"  tables_succeeded INT,"
        f"  tables_failed INT"
        f") USING DELTA"
    )


def insert_run_started(cursor, catalog: str, run_id: str, triggered_at: str):
    """Insert a run record the moment the UI button is clicked — before any queries."""
    cursor.execute(
        f"INSERT INTO `{catalog}`.`waf_cache`.`_run_log` "
        f"(run_id, triggered_at, status) VALUES "
        f"('{run_id}', TIMESTAMP('{triggered_at}'), 'running')"
    )


def update_run_finished(cursor, catalog: str, run_id: str,
                        finished_at: str, status: str,
                        succeeded: int, failed: int):
    """Update the run record once all tables are written."""
    cursor.execute(
        f"UPDATE `{catalog}`.`waf_cache`.`_run_log` SET "
        f"  finished_at = TIMESTAMP('{finished_at}'),"
        f"  status = '{status}',"
        f"  tables_succeeded = {succeeded},"
        f"  tables_failed = {failed} "
        f"WHERE run_id = '{run_id}'"
    )


# ---------------------------------------------------------------------------
# Delta table writer
# ---------------------------------------------------------------------------

def refresh_delta_table(cursor, catalog: str, table_name: str, sql: str):
    """Create or replace a Delta table in {catalog}.waf_cache from SQL."""
    prepared = strip_trailing_semicolon(substitute_date_params(sql))
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`waf_cache`")
    cursor.execute(
        f"CREATE OR REPLACE TABLE `{catalog}`.`waf_cache`.`{table_name}` AS\n{prepared}"
    )


def fetch_from_delta(cursor, catalog: str, table_name: str):
    """Fetch all rows from the just-created Delta table."""
    cursor.execute(f"SELECT * FROM `{catalog}`.`waf_cache`.`{table_name}`")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return columns, rows


# ---------------------------------------------------------------------------
# Lakebase (Postgres) writer
# ---------------------------------------------------------------------------

def pg_connect(creds: dict):
    """Open a psycopg2 connection to Lakebase."""
    return psycopg2.connect(
        host=creds['PGHOST'],
        dbname=creds['PGDATABASE'],
        user=unquote(creds.get('PGUSER', '')),
        password=creds['PGPASSWORD'],
        sslmode=creds.get('PGSSLMODE', 'require'),
        connect_timeout=30,
    )


def write_to_lakebase(pg_conn, table_name: str, columns: list, rows: list):
    """Full-refresh a table in Lakebase (DROP + CREATE + INSERT)."""
    with pg_conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')

        # All columns stored as TEXT for simplicity; add refresh timestamp
        col_defs = ', '.join(f'"{c}" TEXT' for c in columns)
        col_defs += ', "_refreshed_at" TIMESTAMP DEFAULT NOW()'
        cur.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

        if rows:
            placeholders = ', '.join(['%s'] * len(columns))
            col_names = ', '.join(f'"{c}"' for c in columns)
            insert_sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
            # Convert all values to strings (or None for NULL)
            str_rows = [
                tuple(str(v) if v is not None else None for v in row)
                for row in rows
            ]
            psycopg2.extras.execute_batch(cur, insert_sql, str_rows, page_size=500)

    pg_conn.commit()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Reload WAF dashboard data into Lakebase and Delta tables.')
    parser.add_argument('--creds', help='Path to .creds file')
    parser.add_argument('--yaml', help='Path to dashboard_queries.yaml')
    parser.add_argument('--dry-run', action='store_true', help='Print SQL but do not execute')
    parser.add_argument('--skip-lakebase', action='store_true', help='Skip Lakebase (Postgres) sync, write Delta only')
    args = parser.parse_args()

    # --- Load credentials ---
    # In Databricks App environment, DATABRICKS_HOST and DATABRICKS_TOKEN are injected automatically.
    # Fall back to .creds file for local development.
    host = os.environ.get('DATABRICKS_HOST', '').rstrip('/')
    token = os.environ.get('DATABRICKS_TOKEN', '')
    catalog = os.environ.get('WAF_CATALOG', '')

    if host and token:
        print(f"Using Databricks App environment credentials")
        catalog = catalog or 'main'
    else:
        creds_path = find_creds(args.creds)
        print(f"Using creds: {creds_path}")
        creds = load_creds(creds_path)
        host = creds['host'].rstrip('/')
        token = creds['token']
        catalog = catalog or creds.get('DATABRICKS_CATALOG', 'main')

    print(f"Workspace: {host}")
    print(f"Catalog:   {catalog}")

    # --- Load YAML ---
    yaml_path = find_yaml(args.yaml)
    print(f"YAML:      {yaml_path}")
    with open(yaml_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    datasets = data['datasets']
    active = [d for d in datasets if not d.get('is_coming_soon')]
    print(f"\nDatasets: {len(datasets)} total, {len(active)} active, "
          f"{len(datasets) - len(active)} coming-soon (skipped)\n")

    if args.dry_run:
        print("DRY RUN — SQL only (no execution):\n")
        for ds in active:
            print(f"-- {ds['display_name']} → {catalog}.waf_cache.{ds['table_name']}")
            print(substitute_date_params(ds['sql'])[:200])
            print()
        return

    # --- Discover warehouse ---
    print("Discovering SQL warehouse...")
    warehouse_id = get_warehouse_id(host, token)
    hostname = host.replace('https://', '').replace('http://', '')
    http_path = f"/sql/1.0/warehouses/{warehouse_id}"

    # --- Connect to Postgres (optional — skip gracefully if unavailable) ---
    pg_conn = None
    if not args.skip_lakebase:
        print("\nConnecting to Lakebase (Postgres)...")
        try:
            pg_conn = pg_connect(creds)
            print("  Connected.")
        except Exception as pg_err:
            print(f"  WARNING: Lakebase unavailable ({pg_err})")
            print("  Proceeding with Delta-only writes. Use --skip-lakebase to suppress this warning.")

    # --- Generate run_id once — same for every table in this reload ---
    run_id = str(uuid.uuid4())
    run_started_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nRun ID:    {run_id}")
    print(f"Started:   {run_started_at} UTC")

    # --- Process datasets ---
    successes, failures = [], []
    db_conn = dbsql.connect(
        server_hostname=hostname,
        http_path=http_path,
        access_token=token,
    )

    try:
        with db_conn.cursor() as cursor:
            # Ensure schema exists
            print(f"\nEnsuring schema {catalog}.waf_cache exists...")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`waf_cache`")

            # Ensure _run_log table exists
            ensure_run_log(cursor, catalog)

            # INSERT run record immediately — before any queries run
            # (mirrors what the UI button click will do)
            print(f"Logging run start to _run_log...")
            insert_run_started(cursor, catalog, run_id, run_started_at)

            # Drop all stale data tables (not _run_log)
            print(f"\nDropping all existing data tables in {catalog}.waf_cache...")
            drop_all_tables(cursor, catalog)

            for i, ds in enumerate(active, 1):
                name = ds['display_name']
                table = ds['table_name']
                t0 = time.time()
                print(f"[{i:2d}/{len(active)}] {name} → {catalog}.waf_cache.{table}")

                try:
                    prepared_sql = strip_trailing_semicolon(substitute_date_params(ds['sql']))

                    # Create Delta table — stamped with run_id + run_started_at
                    create_delta_table(cursor, catalog, table, prepared_sql,
                                       run_id, run_started_at)

                    # Optionally sync to Lakebase
                    if pg_conn is not None:
                        cursor.execute(f"SELECT * FROM `{catalog}`.`waf_cache`.`{table}`")
                        columns = [desc[0] for desc in cursor.description]
                        rows = cursor.fetchall()
                        write_to_lakebase(pg_conn, table, columns, rows)
                        lakebase_note = f", {len(rows)} rows → Lakebase"
                    else:
                        lakebase_note = " (Lakebase skipped)"

                    elapsed = time.time() - t0
                    print(f"       ✓ {elapsed:.1f}s{lakebase_note}")
                    successes.append(name)

                except Exception as exc:
                    elapsed = time.time() - t0
                    print(f"       ✗ FAILED ({elapsed:.1f}s): {exc}")
                    failures.append((name, str(exc)))
                    if pg_conn is not None:
                        try:
                            pg_conn.rollback()
                        except Exception:
                            pass

            # Update run log with final status
            run_finished_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            final_status = 'success' if not failures else 'partial' if successes else 'failed'
            update_run_finished(cursor, catalog, run_id, run_finished_at,
                                final_status, len(successes), len(failures))
            print(f"\nRun log updated: status={final_status}, finished={run_finished_at} UTC")

    finally:
        db_conn.close()
        if pg_conn is not None:
            pg_conn.close()

    # --- Persist run info for the Streamlit app to display ---
    import json as _json
    _run_info = {
        "run_id": run_id,
        "short_id": run_id[:8],
        "triggered_at": run_started_at,
        "finished_at": run_finished_at,
        "status": final_status,
        "tables_succeeded": len(successes),
        "tables_failed": len(failures),
        "catalog": catalog,
    }
    # /tmp is always writable in both Databricks Apps and local dev
    _run_info_path = "/tmp/waf_run_info.json"
    try:
        with open(_run_info_path, "w", encoding="utf-8") as _f:
            _json.dump(_run_info, _f)
        print(f"Run info written to {_run_info_path}")
    except Exception as _e:
        print(f"Warning: could not write run_info.json: {_e}")

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"DONE: {len(successes)} succeeded, {len(failures)} failed")
    print(f"Run ID: {run_id}")
    if failures:
        print("\nFailed datasets:")
        for name, err in failures:
            print(f"  - {name}: {err}")
        sys.exit(1)


if __name__ == '__main__':
    main()
