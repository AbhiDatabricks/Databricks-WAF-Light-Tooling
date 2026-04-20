# Scoring Methodology — Overview

This section documents how the WAF Assessment Tool scores your Databricks workspace across the four Well-Architected Framework pillars. Each pillar has its own scoring page describing the SQL logic, control thresholds, and remediation guidance.

## How scoring works

The WAF Reload job (`waf_reload.py`) runs a set of SQL queries against Databricks [system tables](https://docs.databricks.com/aws/en/admin/system-tables/) and stores the results in `waf_cache` — a catalog created in your workspace during installation.

For each control:

1. A **scoring query** is executed against system tables (billing, compute, information_schema, access).
2. The result is expressed as a **percentage** (0–100).
3. The percentage is compared against a **threshold** defined per control.
4. If the percentage meets or exceeds the threshold, the control is marked **Met**; otherwise **Not Met**.

!!! note "Data freshness"
    Scores reflect the state of your workspace at the time the WAF Reload job last ran. Re-run the job from the **Databricks App** or the **WAF Reload job** directly to refresh.

## Pillars

| Pillar | WAF ID Prefix | Controls | Cache Table |
|---|---|---|---|
| [Data & AI Governance](governance.md) | `DG-` | 8 | `waf_controls_g` |
| [Cost Optimization](cost-optimization.md) | `CO-` | 8 | `waf_controls_c` |
| [Performance Efficiency](performance.md) | `PE-` | 7 | `waf_controls_p` |
| [Reliability](reliability.md) | `R-` | 7 | `waf_controls_r` |

## Score interpretation

| Score vs Threshold | Status |
|---|---|
| `score >= threshold` | **Met** |
| `score < threshold` | **Not Met** |

!!! tip "Governance column naming"
    The `waf_controls_g` table uses a `description` column where other pillar tables use `best_practice`. This is because the governance controls were built from a different source schema. The scoring logic and Met/Not Met semantics are identical across all pillars.

## Pillar pages

- [Cost Optimization](cost-optimization.md)
- [Performance Efficiency](performance.md)
- [Data & AI Governance](governance.md)
- [Reliability](reliability.md)
