# Streamlit App

The WAF Automation Tool is a Databricks App (Streamlit) that wraps the Lakeview dashboard in an interactive interface. It is the primary entry point for end-users.

![WAF App Dashboard View](../assets/images/waf-app-dashboard.png){ .screenshot }

---

## Pages

### Dashboard (default view)

The main view embeds the full Lakeview dashboard in an `<iframe>`. All pillar tabs and the AI Assistant tab are accessible here.

**Toolbar buttons:**

| Button | Action |
|---|---|
| **Reload Data** | Triggers the WAF Reload Job — refreshes all WAF cache tables (~3–5 min) |
| **Open Dashboard in Databricks** | Opens the published dashboard in a new tab |
| **Ask Genie** | Deep-links to the Genie Space for natural-language queries |

---

### Recommendations (Not Met)

![WAF Recommendations](../assets/images/waf-recommendations.png){ .screenshot }

Click **View Recommendations (Not Met)** to open a dedicated page listing every failing control.

Each row includes:

| Column | Description |
|---|---|
| **WAF ID** | Control identifier (e.g. `RE-01-01`) |
| **Pillar** | Reliability / Governance / Cost / Performance |
| **Principle** | High-level WAF principle |
| **Best Practice** | Specific practice being evaluated |
| **Current Score** | Score at last reload |
| **Threshold** | Minimum passing score |
| **Gap** | How far below threshold |
| **Recommendation** | Exact action to take to remediate |

![WAF Recommendations Detail](../assets/images/waf-recommendations-detail.png){ .screenshot }

Use this page to prioritize remediation work — sort by pillar or gap size to focus on the biggest wins first.

---

### Progress

![WAF Progress](../assets/images/waf-progress.png){ .screenshot }

Click **View Progress** to see a trend chart of WAF scores over time, broken out by pillar. Each data point represents one reload run.

Use this to demonstrate improvement to stakeholders or track the impact of remediation work.

---

## WAF Guide sidebar

The app includes a collapsible sidebar with:

- **Score calculation methodology** — how each metric is derived from system tables
- **Threshold explanations** — what each band means and why thresholds are set where they are
- **Code examples** — SQL and Python snippets for common WAF improvements
- **Control reference** — quick lookup for any WAF ID

---

## Navigation

The app uses session-state navigation to switch between pages without reloading the page. Each page has a **← Back to Dashboard** button that returns to the main view cleanly.

!!! note
    Query parameters (`?page=recommendations`) are cleared when navigating back, so the back button always works correctly regardless of how you arrived at the page.

---

## App URL

The App URL is printed at the end of `install.ipynb`. It follows the pattern:

```
https://<workspace>-waf-automation-tool.databricksapps.com
```

Share this URL with your team after completing [Step B — Grant App access](../installation/grant-access.md#step-b-grant-app-access).
