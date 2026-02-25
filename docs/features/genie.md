# Genie AI Space

The WAF Genie Space is an AI assistant pre-loaded with all 15 WAF cache tables and detailed pillar-specific instructions. It is created automatically during install and linked as the **AI Assistant** tab inside the Lakeview dashboard.

![WAF Genie Space](../assets/images/waf-genie.png){ .screenshot }

---

## What you can ask

Genie understands the full WAF data model. Example questions:

=== "Failing controls"

    - *"Which controls are failing and what should I do?"*
    - *"Show me all controls below threshold for the Reliability pillar"*
    - *"What are the top 5 gaps across all pillars?"*

=== "Scores & trends"

    - *"What is the overall WAF score?"*
    - *"How has Governance improved over the last 30 days?"*
    - *"Which pillar has the lowest score?"*

=== "Cost & performance"

    - *"Which clusters are running without autoscaling?"*
    - *"What percentage of compute uses spot instances?"*
    - *"Show me queries running longer than 10 minutes"*

=== "Recommendations"

    - *"Give me a prioritized remediation plan"*
    - *"What quick wins can I achieve this week?"*
    - *"Which teams have the lowest governance scores?"*

---

## Tables available to Genie

Genie has access to all 15 WAF cache tables:

| Table | Contents |
|---|---|
| `waf_controls_c` | Cost Optimization controls |
| `waf_controls_p` | Performance Efficiency controls |
| `waf_controls_g` | Governance controls |
| `waf_controls_r` | Reliability controls |
| `waf_principal_percentage_c/p/g/r` | Per-principal scores per pillar |
| `waf_total_percentage_c/p/g/r` | Total pillar percentages |
| `waf_total_percentage_across_pillars` | Aggregated cross-pillar scores |
| `waf_controls_with_recommendations` | Full recommendations catalog |
| `waf_recommendations_not_met` | View — failing controls only |

---

## Pre-built SQL examples

The Genie Space ships with 6 pre-built SQL example queries covering the most common WAF questions:

1. Controls below threshold across all pillars
2. Overall WAF score by pillar
3. Score trend over the last N reload runs
4. Top failing controls by gap size
5. Per-principal breakdown for Governance
6. Cost controls with highest improvement potential

---

## Accessing Genie

**From the app:** Click **Ask Genie** in the toolbar
**From the dashboard:** Open the **AI Assistant** tab
**Direct URL:** Shown in the installation summary

!!! warning "Genie access requires Step D"
    Users must be granted **CAN USE** on the Genie Space before they can interact with it. See [Grant Access — Step D](../installation/grant-access.md#step-d-grant-genie-space-access).

---

## How Genie is linked to the dashboard

The Genie Space ID is embedded in the dashboard JSON at creation time via:

```json
"uiSettings": {
  "genieSpace": {
    "isEnabled": true,
    "overrideId": "<genie_space_id>",
    "enablementMode": "ENABLED"
  }
}
```

This is handled automatically by `install.ipynb` — no manual linking in the UI is required.
