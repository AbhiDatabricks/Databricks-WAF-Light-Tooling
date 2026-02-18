#!/usr/bin/env python3
"""
Reload WAF dashboard data:
  1. Read dashboard_queries.yaml (single source of truth)
  2. For each active dataset, run the SQL on a Databricks warehouse
  3. Materialise results as Delta table → {catalog}.waf_cache.{table_name}

Credentials (never hardcoded):
  - Databricks App: DATABRICKS_HOST and DATABRICKS_TOKEN are injected automatically
  - Local dev:      falls back to .creds file (excluded from git via .gitignore)

Environment variables:
    DATABRICKS_HOST   – workspace URL (auto-injected in Databricks Apps)
    DATABRICKS_TOKEN  – OAuth token  (auto-injected in Databricks Apps)
    WAF_CATALOG       – Unity Catalog name (set in app.yaml by install.ipynb)
    WAF_CREDS_PATH    – path to .creds file (local dev override)
    WAF_YAML_PATH     – path to dashboard_queries.yaml (override)
"""
import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

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

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Credentials helper (local dev only)
# ---------------------------------------------------------------------------

def load_creds(path: str) -> dict:
    """Parse a simple KEY=VALUE credentials file (local dev only)."""
    creds: dict = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            creds[k.strip()] = v.strip().strip("'\"")
    return creds


def find_creds(override: Optional[str] = None) -> str:
    """Locate the .creds file for local development."""
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
    sql = sql.replace(':rollback_days', '30')
    return sql


def strip_trailing_semicolon(sql: str) -> str:
    return sql.rstrip().rstrip(';').rstrip()


def sanitize_col_name(name: str) -> str:
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
    """CREATE OR REPLACE TABLE in waf_cache stamped with run_id."""
    wrapped = (
        f"SELECT _q.*,\n"
        f"  '{run_id}' AS _run_id,\n"
        f"  TIMESTAMP('{run_started_at}') AS _run_started_at\n"
        f"FROM (\n{sql}\n) AS _q"
    )
    full_sql = f"CREATE OR REPLACE TABLE `{catalog}`.`waf_cache`.`{table}` AS\n{wrapped}"
    try:
        cursor.execute(full_sql)
    except Exception as first_err:
        if 'DELTA_INVALID_CHARACTERS_IN_COLUMN_NAMES' not in str(first_err):
            raise
        tmp = f"_waf_tmp_{table}"
        cursor.execute(f"CREATE OR REPLACE TEMPORARY VIEW `{tmp}` AS\n{sql}")
        cursor.execute(f"SELECT * FROM `{tmp}` LIMIT 0")
        raw_cols = [desc[0] for desc in cursor.description]
        renames = ', '.join(f'`{c}` AS `{sanitize_col_name(c)}`' for c in raw_cols)
        cursor.execute(
            f"CREATE OR REPLACE TABLE `{catalog}`.`waf_cache`.`{table}` AS\n"
            f"SELECT {renames},\n"
            f"  '{run_id}' AS _run_id,\n"
            f"  TIMESTAMP('{run_started_at}') AS _run_started_at\n"
            f"FROM `{tmp}`"
        )
        cursor.execute(f"DROP VIEW IF EXISTS `{tmp}`")


def ensure_run_log(cursor, catalog: str):
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
    cursor.execute(
        f"INSERT INTO `{catalog}`.`waf_cache`.`_run_log` "
        f"(run_id, triggered_at, status) VALUES "
        f"('{run_id}', TIMESTAMP('{triggered_at}'), 'running')"
    )


def update_run_finished(cursor, catalog: str, run_id: str,
                        finished_at: str, status: str,
                        succeeded: int, failed: int):
    cursor.execute(
        f"UPDATE `{catalog}`.`waf_cache`.`_run_log` SET "
        f"  finished_at = TIMESTAMP('{finished_at}'),"
        f"  status = '{status}',"
        f"  tables_succeeded = {succeeded},"
        f"  tables_failed = {failed} "
        f"WHERE run_id = '{run_id}'"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Reload WAF dashboard data into Delta tables.')
    parser.add_argument('--creds', help='Path to .creds file (local dev only)')
    parser.add_argument('--yaml', help='Path to dashboard_queries.yaml')
    parser.add_argument('--dry-run', action='store_true', help='Print SQL but do not execute')
    args = parser.parse_args()

    # --- Credentials ---
    # Databricks Apps injects DATABRICKS_HOST and DATABRICKS_TOKEN automatically.
    # Local dev falls back to .creds file (never committed to git).
    host = os.environ.get('DATABRICKS_HOST', '').rstrip('/')
    token = os.environ.get('DATABRICKS_TOKEN', '')
    catalog = os.environ.get('WAF_CATALOG', '')

    if host and token:
        print("Credentials: Databricks App environment (env vars)")
        catalog = catalog or 'main'
    else:
        creds_path = find_creds(args.creds)
        print(f"Credentials: local .creds file ({creds_path})")
        creds = load_creds(creds_path)
        host = creds['host'].rstrip('/')
        token = creds['token']
        catalog = catalog or creds.get('DATABRICKS_CATALOG', 'main')

    print(f"Workspace:   {host}")
    print(f"Catalog:     {catalog}")

    # --- Load YAML ---
    yaml_path = find_yaml(args.yaml)
    print(f"YAML:        {yaml_path}")
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

    # --- Generate run_id — shared across all tables in this reload ---
    run_id = str(uuid.uuid4())
    run_started_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nRun ID:  {run_id}")
    print(f"Started: {run_started_at} UTC")

    # --- Process datasets ---
    successes, failures = [], []
    db_conn = dbsql.connect(
        server_hostname=hostname,
        http_path=http_path,
        access_token=token,
    )

    try:
        with db_conn.cursor() as cursor:
            print(f"\nEnsuring schema {catalog}.waf_cache exists...")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`waf_cache`")

            ensure_run_log(cursor, catalog)

            print("Logging run start to _run_log...")
            insert_run_started(cursor, catalog, run_id, run_started_at)

            print(f"\nDropping existing data tables in {catalog}.waf_cache...")
            drop_all_tables(cursor, catalog)

            for i, ds in enumerate(active, 1):
                name = ds['display_name']
                table = ds['table_name']
                t0 = time.time()
                print(f"[{i:2d}/{len(active)}] {name} → {catalog}.waf_cache.{table}")
                try:
                    prepared_sql = strip_trailing_semicolon(substitute_date_params(ds['sql']))
                    create_delta_table(cursor, catalog, table, prepared_sql,
                                       run_id, run_started_at)
                    elapsed = time.time() - t0
                    print(f"       ✓ {elapsed:.1f}s")
                    successes.append(name)
                except Exception as exc:
                    elapsed = time.time() - t0
                    print(f"       ✗ FAILED ({elapsed:.1f}s): {exc}")
                    failures.append((name, str(exc)))

            run_finished_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            final_status = 'success' if not failures else 'partial' if successes else 'failed'
            update_run_finished(cursor, catalog, run_id, run_finished_at,
                                final_status, len(successes), len(failures))
            print(f"\nRun log updated: status={final_status}, finished={run_finished_at} UTC")

    finally:
        db_conn.close()

    # --- Persist run info for the Streamlit app header ---
    run_info = {
        "run_id": run_id,
        "short_id": run_id[:8],
        "triggered_at": run_started_at,
        "finished_at": run_finished_at,
        "status": final_status,
        "tables_succeeded": len(successes),
        "tables_failed": len(failures),
        "catalog": catalog,
    }
    try:
        with open("/tmp/waf_run_info.json", "w", encoding="utf-8") as f:
            json.dump(run_info, f)
        print("Run info written to /tmp/waf_run_info.json")
    except Exception as e:
        print(f"Warning: could not write run_info.json: {e}")

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
