# Databricks App

The WAF Automation Tool is a **Databricks App** — the central hub that brings the entire WAF Assessment experience together in one place. The dashboard, Genie AI Space, Reload Job, and Recommendations are all accessible from here; users never need to navigate directly to individual Databricks resources.

![WAF App Dashboard View](../assets/images/waf-app-dashboard.png){ .screenshot }

---

## The App as central hub

```
┌─────────────────────────────────────────────────────┐
│              WAF Automation Tool (Databricks App)    │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         Lakeview Dashboard (embedded)        │   │
│  │  Reliability · Governance · Cost · Perf      │   │
│  │  Summary · AI Assistant (Genie embedded)     │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  [Reload Data]  [Recommendations]  [Progress]        │
│  [Open in Databricks]  [Ask Genie]                   │
│                                                      │
│  ◀ WAF Guide sidebar                                 │
└─────────────────────────────────────────────────────┘
```

Everything the user needs is surfaced from a single URL — no need to share links to the dashboard, Genie Space, or job separately.

---

## Pages

### Dashboard (default view)

The main view embeds the full Lakeview dashboard. All pillar tabs (Reliability, Governance, Cost, Performance, Summary) and the AI Assistant tab (Genie) are accessible here without leaving the app.

**Toolbar actions:**

| Button | What it does |
|---|---|
| **Reload Data** | Triggers the WAF Reload Job — all WAF cache tables refresh in ~3–5 min |
| **Open in Databricks** | Opens the published dashboard directly in Databricks (new tab) |
| **Ask Genie** | Deep-links to the Genie Space for natural-language WAF queries |

---

### Recommendations (Not Met)

![WAF Recommendations](../assets/images/waf-recommendations.png){ .screenshot }

Every failing WAF control — in one table. No need to open the dashboard or query tables manually.

| Column | Description |
|---|---|
| **WAF ID** | Control identifier (e.g. `RE-01-01`) |
| **Pillar** | Reliability / Governance / Cost / Performance |
| **Principle** | High-level WAF principle |
| **Best Practice** | Specific practice being evaluated |
| **Current Score** | Score at last reload |
| **Threshold** | Minimum passing score |
| **Gap** | How far below threshold |
| **Recommendation** | Exact remediation action |

![WAF Recommendations Detail](../assets/images/waf-recommendations-detail.png){ .screenshot }

---

### Progress

![WAF Progress](../assets/images/waf-progress.png){ .screenshot }

Score trend across all reload runs, broken out by pillar. Use this to demonstrate improvement to stakeholders or track the impact of remediation work — all without leaving the app.

---

## WAF Guide sidebar

Built-in reference documentation:

- **Score methodology** — how each metric is derived from system tables
- **Threshold guide** — what each band (Critical / At Risk / Progressing / Mature) means
- **Code examples** — SQL snippets for common WAF improvements
- **Control reference** — quick lookup for any WAF ID

---

## App URL

Printed at the end of `install.ipynb`:

```
https://<workspace>-waf-automation-tool.databricksapps.com
```

This is the **only URL users need to bookmark**. The dashboard, Genie Space, and reload job are all accessible from here.

!!! warning "Grant App access before sharing"
    Users need **CAN USE** on the app before the URL works for them.
    See [Grant Access — Step B](../installation/grant-access.md#step-b-grant-app-access).
