#!/usr/bin/env python3
"""
Redeploy the WAF Databricks App using the same API as install.ipynb.

Usage:
  python redeploy_app.py <app_name> [workspace_path]

  app_name       e.g. wafauto-20260219-2204
  workspace_path e.g. /Users/abhishekpratap.singh@databricks.com/wafauto-20260219-2204
                  (default: /Users/<current_user>/<app_name> if not set)

Requires: DATABRICKS_HOST and DATABRICKS_TOKEN in environment (or ~/.databrickscfg).
"""
import os
import sys
import requests

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    app_name = sys.argv[1].strip()
    workspace_path = (sys.argv[2].strip() if len(sys.argv) > 2 else "").strip()
    if not workspace_path:
        # Default: /Users/<user>/<app_name> — adjust if your workspace path differs
        workspace_path = f"/Users/<your_user>@databricks.com/{app_name}"
        print(f"Using workspace_path: {workspace_path}")
        print("Pass workspace_path as second argument if different.")

    host = os.environ.get("DATABRICKS_HOST", "").rstrip("/")
    token = os.environ.get("DATABRICKS_TOKEN", "")
    if not host or not token:
        print("Set DATABRICKS_HOST and DATABRICKS_TOKEN (or use ~/.databrickscfg).")
        sys.exit(1)

    api_url = host
    source_code_path = f"/Workspace{workspace_path}"

    resp = requests.post(
        url=f"{api_url}/api/2.0/apps/{app_name}/deployments",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"source_code_path": source_code_path},
        timeout=120,
    )
    if resp.status_code in (200, 201):
        d = resp.json()
        print(f"Redeploy started: deployment_id={d.get('deployment_id')}")
        print(f"Source: {source_code_path}")
    else:
        print(f"Redeploy failed: {resp.status_code} — {resp.text[:400]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
