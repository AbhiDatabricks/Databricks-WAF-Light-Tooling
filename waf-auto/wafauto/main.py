import os
from pathlib import Path
from typing import Iterable

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

DEFAULT_DASHBOARD_URL = (
    "https://e2-demo-field-eng.cloud.databricks.com/"
    "dashboardsv3/01f0baa507dd186ebe42b8c9c427d868?o=1444828305810485"
)

app = FastAPI(title="wafauto", version="0.1.0")


def _candidate_env_files() -> Iterable[Path]:
    # Try repo root, waf-auto root, and package directory.
    current = Path(__file__).resolve()
    for parent in [current.parent.parent.parent, current.parent.parent, current.parent]:
        candidate = parent / ".env"
        if candidate.exists():
            yield candidate


def _load_env_file() -> None:
    for env_file in _candidate_env_files():
        with env_file.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")
                os.environ.setdefault(key, value)


_load_env_file()


def _dashboard_url() -> str:
    url = os.getenv("DASHBOARD_URL", "").strip()
    if url:
        return url

    host = os.getenv("DATABRICKS_HOST", "").strip()
    path = os.getenv("WAF_DASHBOARD_PATH", "").strip()
    if host and path:
        return f"{host.rstrip('/')}/{path.lstrip('/')}"

    if DEFAULT_DASHBOARD_URL:
        return DEFAULT_DASHBOARD_URL

    raise ValueError("Dashboard URL cannot be resolved from environment or defaults")


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    try:
        url = _dashboard_url()
        # Convert to embed URL if it's a regular dashboard URL
        if '/dashboardsv3/' in url and '/embed/' not in url:
            url = url.replace('/dashboardsv3/', '/embed/dashboardsv3/')
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>wafauto | Databricks WAF Dashboard</title>
    <style>
      :root {{
        color-scheme: light dark;
      }}
      body {{
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background-color: #f6f8fa;
        height: 100vh;
        display: flex;
        flex-direction: column;
      }}
      header {{
        padding: 1rem 1.5rem;
        background-color: #1f3b63;
        color: #ffffff;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
        z-index: 1;
      }}
      h1 {{
        font-size: 1.25rem;
        margin: 0;
      }}
      p {{
        margin: 0.25rem 0 0;
        font-size: 0.95rem;
        opacity: 0.85;
      }}
      iframe {{
        flex: 1;
        border: 0;
        width: 100%;
      }}
      .iframe-container {{
        flex: 1;
        padding: 0;
      }}
    </style>
  </head>
  <body>
    <header>
      <h1>Databricks WAF Dashboard</h1>
      <p>Embedded Lakeview dashboard for well-architected assessments.</p>
    </header>
    <div class="iframe-container">
      <iframe
        src="{url}"
        title="Databricks WAF Dashboard"
        allowfullscreen
      ></iframe>
    </div>
  </body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/api/config")
def config() -> JSONResponse:
    try:
        url = _dashboard_url()
        embed_url = url.replace('/dashboardsv3/', '/embed/dashboardsv3/') if '/dashboardsv3/' in url and '/embed/' not in url else url
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JSONResponse({
        "dashboard_url": url,
        "embed_url": embed_url,
        "iframe_code": f'<iframe src="{embed_url}" width="100%" height="600" frameborder="0"></iframe>'
    })
