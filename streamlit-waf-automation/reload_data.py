#!/usr/bin/env python3
"""
Reload WAF dashboard data:
  1. Read dashboard_queries.yaml (single source of truth)
  2. For each active dataset, run the SQL on a Databricks warehouse
  3. Materialise results as Delta table → {catalog}.waf_cache.{table_name}

Credentials come exclusively from environment variables (injected by Databricks Apps):
    DATABRICKS_HOST   – workspace URL  (e.g. https://dbc-xxx.cloud.databricks.com)
    DATABRICKS_TOKEN  – OAuth token
    WAF_CATALOG       – Unity Catalog name (set in app.yaml by install.ipynb)
    WAF_YAML_PATH     – optional override path to dashboard_queries.yaml
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("ERROR: requests not installed.")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed.")
    sys.exit(1)

try:
    from databricks import sql as dbsql
except ImportError:
    print("ERROR: databricks-sql-connector not installed.")
    sys.exit(1)

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# YAML discovery
# ---------------------------------------------------------------------------

def find_yaml(override=None):
    if override:
        if os.path.exists(override):
            return override
        raise FileNotFoundError(f"YAML not found at: {override}")
    candidates = [
        os.environ.get('WAF_YAML_PATH', ''),
        os.path.join(SCRIPT_DIR, 'dashboard_queries.yaml'),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError("Could not find dashboard_queries.yaml next to reload_data.py.")


# ---------------------------------------------------------------------------
# Warehouse discovery
# ---------------------------------------------------------------------------

def get_warehouse_id(host, token):
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

def substitute_date_params(sql):
    now = datetime.now()
    date_end = now.strftime('%Y-%m-%d')
    date_start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    sql = sql.replace(':date_range_start', f"'{date_start}'")
    sql = sql.replace(':date_range_end', f"'{date_end}'")
    sql = sql.replace(':rollback_days', '30')
    return sql


def strip_trailing_semicolon(sql):
    return sql.rstrip().rstrip(';').rstrip()


def sanitize_col_name(name):
    import re as _re
    cleaned = _re.sub(r'[^a-zA-Z0-9_]', '_', name)
    cleaned = _re.sub(r'_+', '_', cleaned).strip('_')
    if not cleaned or cleaned[0].isdigit():
        cleaned = 'col_' + cleaned
    return cleaned or 'col'


def drop_all_tables(cursor, catalog):
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


def create_delta_table(cursor, catalog, table, sql, run_id, run_started_at):
    """CREATE OR REPLACE TABLE in waf_cache stamped with integer run_id."""
    wrapped = (
        f"SELECT _q.*,\n"
        f"  {run_id} AS _run_id,\n"
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
            f"  {run_id} AS _run_id,\n"
            f"  TIMESTAMP('{run_started_at}') AS _run_started_at\n"
            f"FROM `{tmp}`"
        )
        cursor.execute(f"DROP VIEW IF EXISTS `{tmp}`")


def ensure_run_log(cursor, catalog):
    """Create _run_log with INT run_id. Auto-migrates from old STRING schema."""
    try:
        cursor.execute(f"DESCRIBE TABLE `{catalog}`.`waf_cache`.`_run_log`")
        schema = {row[0]: row[1].lower() for row in cursor.fetchall()}
        if schema.get('run_id', '') == 'string':
            print("  Migrating _run_log: upgrading run_id STRING → INT")
            cursor.execute(f"DROP TABLE IF EXISTS `{catalog}`.`waf_cache`.`_run_log`")
    except Exception:
        pass  # table doesn't exist yet

    cursor.execute(
        f"CREATE TABLE IF NOT EXISTS `{catalog}`.`waf_cache`.`_run_log` ("
        f"  run_id INT,"
        f"  triggered_at TIMESTAMP,"
        f"  finished_at TIMESTAMP,"
        f"  status STRING,"
        f"  tables_succeeded INT,"
        f"  tables_failed INT"
        f") USING DELTA"
    )


def get_next_run_id(cursor, catalog):
    cursor.execute(
        f"SELECT COALESCE(MAX(run_id), 0) + 1 FROM `{catalog}`.`waf_cache`.`_run_log`"
    )
    return int(cursor.fetchone()[0])


def insert_run_started(cursor, catalog, run_id, triggered_at):
    cursor.execute(
        f"INSERT INTO `{catalog}`.`waf_cache`.`_run_log` "
        f"(run_id, triggered_at, status) VALUES "
        f"({run_id}, TIMESTAMP('{triggered_at}'), 'running')"
    )


def update_run_finished(cursor, catalog, run_id, finished_at, status, succeeded, failed):
    cursor.execute(
        f"UPDATE `{catalog}`.`waf_cache`.`_run_log` SET "
        f"  finished_at = TIMESTAMP('{finished_at}'),"
        f"  status = '{status}',"
        f"  tables_succeeded = {succeeded},"
        f"  tables_failed = {failed} "
        f"WHERE run_id = {run_id}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--yaml', help='Path to dashboard_queries.yaml')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    # Credentials from Databricks Apps environment only
    host = os.environ.get('DATABRICKS_HOST', '').rstrip('/')
    token = os.environ.get('DATABRICKS_TOKEN', '')
    catalog = os.environ.get('WAF_CATALOG', 'main')

    if not host or not token:
        missing = []
        if not host:
            missing.append('DATABRICKS_HOST')
        if not token:
            missing.append('DATABRICKS_TOKEN')
        print(f"ERROR: Missing environment variable(s): {', '.join(missing)}")
        print("These are automatically injected by Databricks Apps.")
        print("If running locally, set them manually before calling this script.")
        sys.exit(1)

    print(f"Workspace: {host}")
    print(f"Catalog:   {catalog}")

    yaml_path = find_yaml(args.yaml)
    print(f"YAML:      {yaml_path}")
    with open(yaml_path, encoding='utf-8') as f:
        data = yaml.safe_load(f)

    datasets = data['datasets']
    active = [d for d in datasets if not d.get('is_coming_soon')]
    print(f"\nDatasets: {len(datasets)} total, {len(active)} active, "
          f"{len(datasets) - len(active)} coming-soon (skipped)\n")

    if args.dry_run:
        for ds in active:
            print(f"-- {ds['display_name']} → {catalog}.waf_cache.{ds['table_name']}")
            print(substitute_date_params(ds['sql'])[:200])
            print()
        return

    print("Discovering SQL warehouse...")
    warehouse_id = get_warehouse_id(host, token)
    hostname = host.replace('https://', '').replace('http://', '')
    http_path = f"/sql/1.0/warehouses/{warehouse_id}"

    run_started_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    successes, failures = [], []
    run_id = None
    run_finished_at = run_started_at
    final_status = 'failed'

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
            run_id = get_next_run_id(cursor, catalog)
            print(f"\nRun #:   {run_id}")
            print(f"Started: {run_started_at} UTC")

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
            print(f"\nRun log updated: status={final_status}")

    finally:
        db_conn.close()

    run_info = {
        "run_id": run_id,
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
    except Exception as e:
        print(f"Warning: could not write run_info.json: {e}")

    print(f"\n{'='*60}")
    print(f"DONE: {len(successes)} succeeded, {len(failures)} failed  |  Run #{run_id}")
    if failures:
        print("\nFailed datasets:")
        for name, err in failures:
            print(f"  - {name}: {err}")
        sys.exit(1)


if __name__ == '__main__':
    main()
