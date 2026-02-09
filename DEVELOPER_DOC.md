# WAF Dashboard - Developer Documentation

## Overview

The WAF Assessment Dashboard uses a **consistent 3-dataset pattern** for each of the 4 pillars (Reliability, Governance, Cost Optimization, Performance Efficiency), plus a **Summary dataset** that aggregates across all pillars.

---

## 📊 Dataset Architecture

### Dataset Pattern (Per Pillar)

Each pillar follows the same 3-dataset structure:

1. **`total_percentage_[pillar]`** - Overall completion percentage (1 row)
2. **`waf_controls_[pillar]`** - Individual metrics with scores (N rows, one per metric)
3. **`waf_principal_percentage_[pillar]`** - Completion per principle (M rows, one per principle)

### Summary Dataset

- **`total_percentage_across_pillars`** - Aggregates scores from all 4 pillars (4 rows, one per pillar)

---

## 🏗️ Complete Dataset List

| Pillar | Dataset Name | Display Name | Dataset ID | Purpose |
|--------|-------------|--------------|------------|---------|
| **Reliability (R)** | `total_percentage_r` | total_percentage_r | `03babf4f` | Overall Reliability completion % |
| | `waf_controls_r` | waf_controls_r | `60cfe928` | Individual Reliability metrics |
| | `waf_principal_percentage_r` | waf_principal_percentage_r | `011cf80a` | Reliability completion per principle |
| **Governance (G)** | `total_percentage_g` | total_percentage_g | `920a8759` | Overall Governance completion % |
| | `waf_controls_g` | waf_controls_g | `1eab9fe1` | Individual Governance metrics |
| | `waf_principal_percentage_g` | waf_principal_percentage_g | `95258030` | Governance completion per principle |
| **Cost Optimization (C)** | `total_percentage_c` | total_percentage_c | `06f2987c` | Overall Cost completion % |
| | `waf_controls_c` | waf_controls_c | `dbdc9433` | Individual Cost metrics |
| | `waf_principal_percentage_c` | waf_principal_percentage_c | `81f0a6aa` | Cost completion per principle |
| **Performance Efficiency (P)** | `total_percentage_p` | total_percentage_p | `87deca0d` | Overall Performance completion % |
| | `waf_controls_p` | waf_controls_p | `4745a0f9` | Individual Performance metrics |
| | `waf_principal_percentage_p` | waf_principal_percentage_p | `13e29e6c` | Performance completion per principle |
| **Summary** | `total_percentage_across_pillars` | total_percentage_across_pillars | `b39d7f91` | Aggregated scores from all pillars |

---

## 🔗 Dataset Relationships

### 1. Within Each Pillar (3-Dataset Pattern)

```
┌─────────────────────────────────────────────────────────┐
│              total_percentage_[pillar]                  │
│              (Overall completion: 1 row)                  │
│                                                          │
│  Example: total_percentage_r = 38%                      │
└───────────────────────┬─────────────────────────────────┘
                        │
        Aggregates all metrics in the pillar
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────────┐ ┌──────────────────┐ ┌──────────────────┐
│waf_controls_  │ │waf_principal_    │ │  (Same base      │
│[pillar]       │ │percentage_[pillar]│ │   calculations)  │
│               │ │                  │ │                  │
│ N rows        │ │ M rows           │ │  Shared CTEs:    │
│ (one per      │ │ (one per         │ │  - metric_1     │
│  metric)      │ │  principle)      │ │  - metric_2     │
│               │ │                  │ │  - metric_3     │
│ Individual    │ │ Principle-level  │ │  - ...           │
│ scores,       │ │ completion       │ │                  │
│ thresholds,   │ │                  │ │                  │
│ status        │ │                  │ │                  │
└───────────────┘ └──────────────────┘ └──────────────────┘
```

### 2. Across All Pillars (Summary Aggregation)

```
┌─────────────────────────────────────────────────────────┐
│         total_percentage_across_pillars                 │
│         (Summary: 4 rows, one per pillar)               │
│                                                          │
│  pillar          | completion_percent                    │
│  ----------------|-------------------                    │
│  Reliability     | 38                                   │
│  Governance      | 65                                   │
│  Cost            | 45                                   │
│  Performance     | 72                                   │
└──────────────────┬──────────────────────────────────────┘
                    │
    Aggregates from individual pillar totals
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│total_    │  │total_    │  │total_    │  │total_    │
│percentage│  │percentage│  │percentage│  │percentage│
│_r        │  │_g        │  │_c        │  │_p        │
│          │  │          │  │          │  │          │
│38%       │  │65%       │  │45%       │  │72%       │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

---

## 📋 Dataset Structure Details

### Pattern 1: `total_percentage_[pillar]`

**Purpose**: Calculate overall completion percentage for the pillar

**Output Structure** (1 row):
```sql
total_controls | implemented_controls | completion_percent
--------------|----------------------|-------------------
      8       |          3           |        38
```

**Logic**:
- Evaluates all metrics in the pillar
- Counts how many have `implemented = 'Pass'` (or `'Yes'` in older versions)
- Calculates: `(implemented_controls / total_controls) × 100`

**Used For**:
- Main completion percentage display at top of pillar page
- Summary tab aggregation

---

### Pattern 2: `waf_controls_[pillar]`

**Purpose**: Show detailed breakdown of each individual metric

**Output Structure** (N rows - one per metric):
```sql
waf_id  | principle              | best_practice              | score_percentage | threshold_percentage | threshold_met | implemented
--------|------------------------|----------------------------|------------------|---------------------|---------------|-------------
R-01-01 | Design for failure     | Use Delta format...        | 85.5             | 80                  | Met           | Pass
R-01-03 | Design for failure     | Use DLT for data quality   | 25.0             | 30                  | Not Met       | Fail
...
```

**Columns**:
- `waf_id`: WAF identifier (e.g., R-01-01, G-02-03)
- `principle`: WAF principle name
- `best_practice`: Description of the best practice
- `score_percentage`: Actual calculated percentage for this metric
- `threshold_percentage`: Required threshold to pass
- `threshold_met`: 'Met' or 'Not Met'
- `implemented`: 'Pass' or 'Fail' (was 'Yes'/'No' in older versions)

**Logic**:
- Shows all metrics individually
- Calculates actual percentage for each metric using percentage-based logic
- Compares against threshold to determine `implemented` status
- Provides threshold reference for each metric

**Used For**:
- Detailed "WAF Controls Table" chart
- Users can see which specific metrics need improvement
- Conditional formatting (red rows for unmet thresholds)

---

### Pattern 3: `waf_principal_percentage_[pillar]`

**Purpose**: Calculate completion percentage grouped by principle

**Output Structure** (M rows - one per principle):
```sql
principle              | total_controls | implemented_controls | completion_percent
-----------------------|----------------|----------------------|-------------------
Design for failure     |       4        |          2           |        50
Manage data quality    |       2        |          1           |        50
Design for autoscaling |       2        |          1           |        50
```

**Logic**:
- Groups metrics by their principle
- Counts total and implemented per principle
- Calculates: `(implemented_controls / total_controls) × 100` per principle

**Used For**:
- "Completion percentage of implemented controls per principle" chart
- Shows which principles need more attention
- Helps prioritize improvement efforts

---

### Pattern 4: `total_percentage_across_pillars` (Summary)

**Purpose**: Aggregate scores from all four pillars

**Output Structure** (4 rows - one per pillar):
```sql
pillar          | completion_percent
----------------|-------------------
Reliability     | 38
Governance      | 65
Cost            | 45
Performance     | 72
```

**Logic**:
- Queries each pillar's `total_percentage_[pillar]` dataset
- Extracts the `completion_percent` value
- Combines into a single result set with pillar names

**SQL Pattern**:
```sql
SELECT 'Reliability' as pillar, completion_percent 
FROM total_percentage_r
UNION ALL
SELECT 'Governance' as pillar, completion_percent 
FROM total_percentage_g
UNION ALL
SELECT 'Cost' as pillar, completion_percent 
FROM total_percentage_c
UNION ALL
SELECT 'Performance' as pillar, completion_percent 
FROM total_percentage_p
```

**Used For**:
- Summary tab showing all pillar scores
- Overall WAF assessment view
- Comparison across pillars

---

## 🔄 Data Flow and Dependencies

### Calculation Flow

```
1. System Tables (Data Sources)
   ↓
2. Shared CTEs (Common Calculations)
   - delta_usage
   - dlt_usage
   - serverless_usage
   - photon_usage
   - cluster_metrics
   - warehouse_metrics
   - table_metrics
   - etc.
   ↓
3. Individual Metric Evaluation
   - Each metric calculated with percentage-based logic
   - Threshold comparison
   - Pass/Fail determination
   ↓
4. Aggregation (3 different views)
   ├── waf_controls_[pillar] (detailed, no aggregation)
   ├── waf_principal_percentage_[pillar] (GROUP BY principle)
   └── total_percentage_[pillar] (aggregate all)
   ↓
5. Summary Aggregation
   └── total_percentage_across_pillars (UNION ALL from all pillars)
```

### Consistency Guarantees

All three datasets within a pillar:
- ✅ Use the same CTEs (shared calculations)
- ✅ Evaluate the same metrics
- ✅ Use the same thresholds
- ✅ Use the same percentage-based logic
- ✅ Will always show consistent results

This ensures:
- The overall percentage matches the sum of individual metrics
- Principle percentages match the metrics within them
- No discrepancies between different views
- Summary tab correctly aggregates from individual pillars

---

## 📐 Hierarchical Structure Example (Reliability)

```
total_percentage_r (38%)
│
├── Design for failure (50%)
│   ├── R-01-01: Delta format (85.5%) ✅ Pass
│   ├── R-01-03: DLT usage (25.0%) ❌ Fail
│   ├── R-01-05: Model Serving (15.0%) ❌ Fail
│   └── R-01-06: Serverless/Managed (60.0%) ✅ Pass
│
├── Manage data quality (50%)
│   ├── R-02-03: Unity Catalog (100.0%) ✅ Pass
│   └── R-02-04: DLT for data quality (25.0%) ❌ Fail
│
└── Design for autoscaling (50%)
    ├── R-03-01: Auto-scaling clusters (75.0%) ❌ Fail
    └── R-03-02: Auto-scaling warehouses (90.0%) ✅ Pass
```

**Mathematical Relationship**:
- `total_percentage_r.completion_percent` = Weighted average of `waf_principal_percentage_r.completion_percent`
- Each principle contributes based on number of metrics it contains
- Individual metrics in `waf_controls_r` roll up to principles in `waf_principal_percentage_r`
- Principles roll up to overall in `total_percentage_r`

---

## 🎯 Usage in Dashboard Widgets

### Summary Tab
- **Widget**: "Completion percentage across pillars"
- **Dataset**: `total_percentage_across_pillars`
- **Shows**: Bar chart with all 4 pillar scores

### Pillar Pages (Reliability, Governance, Cost, Performance)

Each pillar page has 3 widgets:

1. **Top Widget**: Overall completion percentage
   - **Dataset**: `total_percentage_[pillar]`
   - **Shows**: Single number or gauge

2. **Middle Widget**: Completion per principle
   - **Dataset**: `waf_principal_percentage_[pillar]`
   - **Shows**: Bar chart grouped by principle

3. **Bottom Widget**: WAF Controls Table
   - **Dataset**: `waf_controls_[pillar]`
   - **Shows**: Table with all metrics, scores, thresholds, and status
   - **Formatting**: Red rows for unmet thresholds

---

## 🔧 Implementation Details

### Percentage-Based Logic

All metrics use **percentage-based calculations** instead of simple EXISTS checks:

**Old Approach (Removed)**:
```sql
CASE WHEN EXISTS (SELECT 1 FROM ...) THEN 100 ELSE 0 END
```

**New Approach (Current)**:
```sql
CASE 
  WHEN total_count > 0 THEN (passing_count * 100.0 / total_count)
  ELSE 0 
END
```

**Example**: Delta format usage
- **Old**: "Do you have ANY Delta tables?" → 100% or 0%
- **New**: "What % of your tables are Delta?" → 0-100% based on actual usage

### Threshold-Based Pass/Fail

Each metric has a threshold:
- **Pass**: `score_percentage >= threshold_percentage`
- **Fail**: `score_percentage < threshold_percentage`

**Example**:
- R-01-01: Delta format ≥80% → Pass
- R-01-03: DLT usage ≥30% → Pass
- R-01-05: Model Serving ≥20% → Pass

### Shared CTEs Pattern

All three datasets in a pillar share the same CTEs to ensure consistency:

```sql
WITH shared_cte_1 AS (...),
     shared_cte_2 AS (...),
     shared_cte_3 AS (...)
SELECT ...
FROM (
  SELECT * FROM VALUES
    ('WAF-ID-1', 'Principle 1', 'Best Practice 1'),
    ('WAF-ID-2', 'Principle 1', 'Best Practice 2'),
    ...
  AS waf(waf_id, principle, best_practice)
)
```

---

## 🐛 Troubleshooting

### Issue: Summary score doesn't match individual pillar

**Check**:
1. Verify `total_percentage_across_pillars` queries each pillar's `total_percentage_[pillar]`
2. Ensure pillar names match exactly ('Reliability', 'Governance', 'Cost', 'Performance')
3. Check for NULL values in completion_percent

### Issue: Principle percentage doesn't match individual metrics

**Check**:
1. Verify `waf_principal_percentage_[pillar]` groups by the same `principle` field
2. Ensure all metrics in `waf_controls_[pillar]` have valid principle values
3. Check that `implemented` logic is consistent (Pass/Fail)

### Issue: Overall percentage doesn't match principle breakdown

**Check**:
1. Verify all three datasets use the same CTEs
2. Ensure threshold logic is identical
3. Check for rounding differences (use ROUND consistently)

### Issue: Dashboard shows old data

**Check**:
1. Verify SQL warehouse is running
2. Check dataset refresh settings
3. Ensure queries are not cached (add timestamp if needed)

---

## 📝 Best Practices

1. **Always update all 3 datasets together** when modifying a pillar
2. **Use shared CTEs** to ensure consistency
3. **Test all 3 datasets** after changes to verify consistency
4. **Document threshold changes** in code comments
5. **Use percentage-based logic** for all metrics (not EXISTS checks)
6. **Maintain consistent naming** across datasets (total_percentage, waf_controls, waf_principal_percentage)
7. **Verify Summary aggregation** after pillar changes

---

## 🔄 Migration Notes

### From Yes/No to Pass/Fail

**Changed**: `implemented` column values
- **Old**: 'Yes' / 'No'
- **New**: 'Pass' / 'Fail'

**Updated in**: All `waf_controls_[pillar]` datasets

### From EXISTS to Percentage-Based

**Changed**: Metric evaluation logic
- **Old**: Simple EXISTS checks (binary 0% or 100%)
- **New**: Percentage-based calculations (0-100% based on actual usage)

**Benefits**:
- More accurate scoring
- Better reflects actual adoption
- Stricter thresholds (e.g., ≥80% instead of "any")

---

## 📚 Related Documentation

- **RELIABILITY_DATASETS_RELATIONSHIP.md** - Detailed Reliability pillar documentation
- **RELIABILITY_METRICS_DOCUMENTATION.md** - Reliability metrics and calculations
- **WAF_DASHBOARD_GUIDE.md** - User-facing guide
- **USER_GUIDE.md** - End-user documentation

---

## 🎓 Summary

The WAF Dashboard uses a **consistent, hierarchical dataset structure**:

1. **13 total datasets**: 3 per pillar (×4) + 1 summary
2. **3-level hierarchy**: Overall → Principles → Individual Metrics
3. **Consistent logic**: Shared CTEs ensure all views are aligned
4. **Percentage-based**: All metrics use actual usage percentages
5. **Threshold-driven**: Clear Pass/Fail criteria for each metric

This architecture ensures:
- ✅ Accurate scoring
- ✅ Consistent views
- ✅ Easy maintenance
- ✅ Clear user experience

---

**Last Updated**: February 2026  
**Dashboard Version**: v1.6  
**Maintained By**: WAF Assessment Team
