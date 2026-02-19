# Databricks notebook source
# COMMAND ----------

# WAF Reload — runs as a Databricks Job so credentials come from notebook context
# (no DATABRICKS_TOKEN env var injection issues)

import subprocess, sys, os

ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
host  = ctx.apiUrl().get().rstrip("/")
token = ctx.apiToken().get()

dbutils.widgets.text("catalog", "main")
catalog = dbutils.widgets.get("catalog").strip() or "main"

print(f"WAF Reload starting")
print(f"  Host   : {host}")
print(f"  Catalog: {catalog}")

# COMMAND ----------

script_path = os.path.join(os.getcwd(), "reload_data.py")
print(f"  Script : {script_path}")

if not os.path.exists(script_path):
    raise FileNotFoundError(f"reload_data.py not found at {script_path}")

env = os.environ.copy()
env["DATABRICKS_HOST"]  = host
env["DATABRICKS_TOKEN"] = token
env["WAF_CATALOG"]      = catalog

result = subprocess.run(
    [sys.executable, script_path],
    env=env,
    capture_output=True,
    text=True,
    timeout=600,
    cwd=os.path.dirname(script_path),
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:3000])

if result.returncode != 0:
    raise Exception(f"reload_data.py exited with code {result.returncode}")

print("✅ WAF reload complete")
