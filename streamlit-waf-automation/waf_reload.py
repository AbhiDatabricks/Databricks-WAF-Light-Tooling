# Databricks notebook source
# COMMAND ----------

# WAF Reload — Databricks Job notebook
# Uses spark.sql() + ThreadPoolExecutor for parallel execution.
# No subprocess, no JDBC — runs natively on the job cluster.

import os, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import yaml

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
dbutils.widgets.text("catalog", "main")
catalog = dbutils.widgets.get("catalog").strip() or "main"

# dashboard_queries.yaml lives next to this notebook in the workspace
_nb_path   = ctx.notebookPath().get()           # e.g. /Users/.../wafauto-20260219-0317/waf_reload
_ws_dir    = "/Workspace" + "/".join(_nb_path.split("/")[:-1])
yaml_path  = _ws_dir + "/dashboard_queries.yaml"

print("WAF Reload starting")
print(f"  Catalog  : {catalog}")
print(f"  YAML     : {yaml_path}")

# COMMAND ----------

with open(yaml_path, "r", encoding="utf-8") as _f:
    _config = yaml.safe_load(_f)

_datasets = _config.get("datasets", [])
active    = [d for d in _datasets if not d.get("is_coming_soon")]

print(f"  Datasets : {len(active)} active / {len(_datasets)} total")

# COMMAND ----------

# Ensure schema + _run_log table
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`waf_cache`")
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS `{catalog}`.`waf_cache`.`_run_log` (
        run_id           INT,
        triggered_at     TIMESTAMP,
        finished_at      TIMESTAMP,
        status           STRING,
        tables_succeeded INT,
        tables_failed    INT
    ) USING DELTA
""")

_run_id_row = spark.sql(
    f"SELECT COALESCE(MAX(run_id), 0) + 1 FROM `{catalog}`.`waf_cache`.`_run_log`"
).collect()[0]
run_id = int(_run_id_row[0])
triggered_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

spark.sql(f"""
    INSERT INTO `{catalog}`.`waf_cache`.`_run_log`
    (run_id, triggered_at, status, tables_succeeded, tables_failed)
    VALUES ({run_id}, TIMESTAMP('{triggered_at}'), 'running', 0, 0)
""")
print(f"  Run ID   : {run_id}  |  Started: {triggered_at} UTC")

# COMMAND ----------

def _sub_dates(sql: str) -> str:
    now = datetime.utcnow()
    sql = sql.replace(":date_range_start", f"'{(now - timedelta(days=30)).strftime('%Y-%m-%d')}'")
    sql = sql.replace(":date_range_end",   f"'{now.strftime('%Y-%m-%d')}'")
    sql = sql.replace(":rollback_days",    "30")
    return sql.rstrip().rstrip(";")

def _safe_col(name: str) -> str:
    c = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    c = re.sub(r"_+", "_", c).strip("_")
    return ("col_" + c if (not c or c[0].isdigit()) else c) or "col"

def _run_one(ds: dict):
    """Run one dataset query and append to its _hist table. Returns (table_name, ok, err)."""
    table = ds["table_name"]
    label = ds.get("display_name", table)
    sql   = _sub_dates(ds.get("sql", ""))
    if not sql:
        return table, False, "no sql"
    try:
        from pyspark.sql.functions import lit, to_timestamp
        df = spark.sql(sql)
        # Sanitize column names (special chars → underscores)
        renamed = [_safe_col(c) for c in df.columns]
        for old, new in zip(df.columns, renamed):
            if old != new:
                df = df.withColumnRenamed(old, new)
        df = (df
              .withColumn("_run_id",         lit(run_id))
              .withColumn("_run_started_at", to_timestamp(lit(triggered_at))))
        (df.write
           .mode("append")
           .option("mergeSchema", "true")
           .saveAsTable(f"`{catalog}`.`waf_cache`.`{table}_hist`"))
        return table, True, None
    except Exception as exc:
        return table, False, str(exc)[:400]

# Run all datasets in parallel — 8 threads (Spark handles concurrency safely)
print(f"\nRunning {len(active)} datasets in parallel (max 8 threads)...")
succeeded, failed = [], []

with ThreadPoolExecutor(max_workers=8) as pool:
    futures = {pool.submit(_run_one, ds): ds["table_name"] for ds in active}
    for fut in as_completed(futures):
        table, ok, err = fut.result()
        label = next((d.get("display_name", table) for d in active if d["table_name"] == table), table)
        if ok:
            succeeded.append(table)
            print(f"  ✅ {label}")
        else:
            failed.append(table)
            print(f"  ❌ {label}: {err}")

# COMMAND ----------

# Create/replace views for succeeded tables — each view points to the latest successful run
print(f"\nCreating views for {len(succeeded)} table(s)...")
for table in succeeded:
    try:
        spark.sql(f"""
            CREATE OR REPLACE VIEW `{catalog}`.`waf_cache`.`{table}` AS
            SELECT * FROM `{catalog}`.`waf_cache`.`{table}_hist`
            WHERE _run_id = (
                SELECT MAX(run_id)
                FROM `{catalog}`.`waf_cache`.`_run_log`
                WHERE status IN ('success', 'partial')
            )
        """)
    except Exception as ve:
        print(f"  ⚠️  View for {table}: {ve}")

# COMMAND ----------

# Create view: waf_recommendations_not_met (join controls with recommendations table, filter Not Met)
# Depends on: waf_controls_g, waf_controls_c, waf_controls_p, waf_controls_r, waf_controls_with_recommendations
try:
    spark.sql(f"""
        CREATE OR REPLACE VIEW `{catalog}`.`waf_cache`.`waf_recommendations_not_met` AS
        SELECT
            r.waf_id,
            r.pillar_name,
            r.principle,
            r.best_practice,
            r.capabilities,
            r.details,
            r.query_table_name,
            r.threshold_percentage AS rec_threshold_pct,
            r.metric_definition,
            r.recommendation_if_not_met,
            c.score_percentage,
            c.threshold_percentage AS control_threshold_pct,
            c.threshold_met
        FROM (
            SELECT waf_id, 'Data & AI Governance' AS pillar, principle,
                   description AS best_practice,
                   score_percentage, threshold_percentage, threshold_met
            FROM `{catalog}`.`waf_cache`.`waf_controls_g`
            UNION ALL
            SELECT waf_id, 'Cost Optimization', principle, best_practice,
                   score_percentage, threshold_percentage, threshold_met
            FROM `{catalog}`.`waf_cache`.`waf_controls_c`
            UNION ALL
            SELECT waf_id, 'Performance Efficiency', principle, best_practice,
                   score_percentage, threshold_percentage, threshold_met
            FROM `{catalog}`.`waf_cache`.`waf_controls_p`
            UNION ALL
            SELECT waf_id, 'Reliability', principle, best_practice,
                   score_percentage, threshold_percentage, threshold_met
            FROM `{catalog}`.`waf_cache`.`waf_controls_r`
        ) c
        INNER JOIN `{catalog}`.`waf_cache`.`waf_controls_with_recommendations` r
          ON r.waf_id = c.waf_id
        WHERE c.threshold_met = 'Not Met'
    """)
    print("  ✅ View: waf_recommendations_not_met")
except Exception as ve:
    print(f"  ⚠️  View waf_recommendations_not_met: {ve}")

# COMMAND ----------

# Finalize _run_log
_status      = "success" if not failed else ("partial" if succeeded else "failed")
_finished_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

spark.sql(f"""
    UPDATE `{catalog}`.`waf_cache`.`_run_log`
    SET finished_at      = TIMESTAMP('{_finished_at}'),
        status           = '{_status}',
        tables_succeeded = {len(succeeded)},
        tables_failed    = {len(failed)}
    WHERE run_id = {run_id}
""")

print(f"\n✅ Run {run_id} complete: {len(succeeded)} succeeded, {len(failed)} failed → {_status}")
if failed:
    print(f"   Failed: {', '.join(failed[:20])}")
if _status == "failed":
    raise Exception(f"All {len(failed)} datasets failed — check output above")
