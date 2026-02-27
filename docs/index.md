---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

<div class="hero-title">Databricks WAF Light Tooling</div>

<div class="hero-subtitle">
<strong>One-click install.</strong> Instant visibility into how your Databricks Lakehouse scores against the Well-Architected Framework — across 4 pillars, with score history, targeted recommendations, and an AI assistant to answer follow-up questions.
</div>

<div class="hero-buttons" markdown>
[Get Started :material-arrow-right:](installation/quickstart.md){ .md-button .md-button--primary }
[View on GitHub :fontawesome-brands-github:](https://github.com/AbhiDatabricks/Databricks-WAF-Light-Tooling){ .md-button }
</div>

</div>

---

## 🎬 Demo

<video width="100%" controls style="border-radius: 8px; margin: 0.5rem 0 1.5rem;">
  <source src="WAF2.0Demo.mp4" type="video/mp4">
</video>

---

## Run one notebook. Get all of this.

<div class="grid cards" markdown>

-   :material-eye: &nbsp;**Visibility across all 4 pillars**

    ---

    See how your Lakehouse scores on **Reliability, Governance, Cost Optimization, and Performance Efficiency** — in real time, from a single dashboard. No manual analysis, no spreadsheets.

    [:octicons-arrow-right-24: Dashboard features](features/dashboard.md)

-   :material-chart-timeline-variant: &nbsp;**Score history across runs**

    ---

    Every time data reloads, a new data point is recorded. **View Progress** shows how your WAF scores evolve across runs and pillars — so you can visualise improvement and prove ROI over time.

    [:octicons-arrow-right-24: View Progress](features/app.md#progress)

-   :material-clipboard-list: &nbsp;**Targeted recommendations**

    ---

    **Recommendations (Not Met)** lists every failing control with the WAF ID, current score, threshold gap, and the exact action to take — no guesswork, no digging through docs.

    [:octicons-arrow-right-24: Recommendations](features/app.md#recommendations-not-met)

-   :material-robot: &nbsp;**AI-powered follow-up questions**

    ---

    **Genie** is pre-loaded with all 15 WAF tables and pillar-specific instructions. Ask *"Which controls are failing and what should I prioritise?"* in plain English and get instant answers.

    [:octicons-arrow-right-24: Genie AI Space](features/genie.md)

</div>

---

## See it in action

=== "Dashboard"

    ![WAF Assessment App Dashboard](assets/images/waf-app-dashboard.png){ .screenshot }

    *The Databricks App — your single URL for all WAF Assessment capabilities. Pillar scores, AI Assistant, Recommendations, and Progress all in one place.*

=== "Recommendations"

    ![WAF Recommendations Not Met](assets/images/waf-recommendations.png){ .screenshot }

    *Every failing control — WAF ID, score vs threshold gap, and the exact fix — surfaced automatically. No manual analysis needed.*

    ![WAF Recommendations Detail](assets/images/waf-recommendations-detail.png){ .screenshot }

=== "Progress"

    ![WAF Assessment Progress](assets/images/waf-progress.png){ .screenshot }

    ***View Progress** — WAF scores across all reload runs, broken out by pillar. Visualise how remediations move the needle over time and demonstrate improvement to stakeholders.*

=== "Genie"

    ![WAF Genie Space](assets/images/waf-genie.png){ .screenshot }

    *Genie AI Space — ask follow-up questions about your WAF data in plain English. Pre-loaded with all 15 WAF tables and ready to use from the moment install completes.*

---

## What gets deployed

The install notebook deploys a **Databricks App** — the central hub — backed by four components that work together:

| Component | What it does |
|---|---|
| :material-application: **Databricks App** | Central hub — embeds the dashboard and surfaces all capabilities from one URL |
| :material-view-dashboard: **Lakeview Dashboard** | Real-time WAF scores per pillar with AI Assistant tab |
| :material-robot: **Genie AI Space** | Natural-language Q&A over all WAF tables |
| :material-refresh: **WAF Reload Job** | Refreshes all scores on demand or on schedule |

---

## 4 pillars. Fully automated.

| Pillar | What it measures |
|---|---|
| :shield: **Reliability** | System resilience, backup coverage, recovery posture |
| :scales: **Governance** | Data governance, access controls, Unity Catalog adoption |
| :moneybag: **Cost Optimization** | Compute efficiency, idle resources, right-sizing |
| :zap: **Performance Efficiency** | Query performance, warehouse utilization, serverless adoption |

---

## Why not a custom dashboard?

| | Custom dashboards | WAF Light Tooling |
|---|---|---|
| Setup time | Days–weeks | **~10 minutes** |
| Maintenance | Manual | **Auto-updated** |
| Score history | Build it yourself | **Included — View Progress** |
| Recommendations | Manual analysis | **Automated, per-control** |
| AI assistant | Build it yourself | **Genie Space — ready on install** |
| Consistency | Varies per customer | **Standardized WAF scoring** |

---

## Ready to install?

[Quick Start :material-arrow-right:](installation/quickstart.md){ .md-button .md-button--primary }
[Check required permissions](installation/permissions.md){ .md-button }
