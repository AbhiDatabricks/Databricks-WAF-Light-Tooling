# Reliability Datasets Relationship Analysis

## Overview

The Reliability pillar uses **3 related datasets** that work together to provide different views of the same underlying data:

1. **`total_percentage_r`** - Overall completion percentage
2. **`waf_controls_r`** - Individual metrics with scores
3. **`waf_principal_percentage_r`** - Completion per principle

---

## 1️⃣ total_percentage_r (Overall Summary)

**Purpose**: Calculate the overall Reliability completion percentage

**Output** (1 row):
```
total_controls | implemented_controls | completion_percent
      8        |          3           |        38
```

**Logic**:
- Evaluates all 8 metrics
- Counts how many have `implemented = 'Yes'`
- Calculates: `(implemented_controls / total_controls) × 100`

**Used For**: 
- Main completion percentage display
- Summary view at the top of Reliability page

---

## 2️⃣ waf_controls_r (Detailed Metrics Table)

**Purpose**: Show detailed breakdown of each individual metric

**Output** (8 rows - one per metric):
```
waf_id  | principle              | best_practice                                    | score_percentage | implemented | threshold_percentage
--------|------------------------|-------------------------------------------------|------------------|-------------|--------------------
R-01-01 | Design for failure     | Use a data format that supports ACID...        | 85.5             | Yes         | 80
R-01-03 | Design for failure     | Automatically rescue invalid or nonconforming  | 25.0             | No          | 30
R-01-05 | Design for failure     | Use a scalable and production-grade...        | 15.0             | No          | 20
R-01-06 | Design for failure     | Use managed services for your workloads        | 60.0             | Yes         | 50
R-02-03 | Manage data quality    | Actively manage schemas                         | 100.0            | Yes         | 100
R-02-04 | Manage data quality    | Use constraints and data expectations          | 25.0             | No          | 30
R-03-01 | Design for autoscaling | Enable autoscaling for ETL workloads           | 75.0             | No          | 80
R-03-02 | Design for autoscaling | Use autoscaling for SQL Warehouses              | 90.0             | Yes         | 80
```

**Logic**:
- Shows all 8 metrics individually
- Calculates actual percentage for each metric
- Compares against threshold to determine `implemented` (Yes/No)
- Provides threshold reference for each metric

**Used For**:
- Detailed table showing each metric's status
- WAF Control Table chart
- Users can see which specific metrics need improvement

---

## 3️⃣ waf_principal_percentage_r (Per-Principle Breakdown)

**Purpose**: Calculate completion percentage grouped by principle

**Output** (3 rows - one per principle):
```
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

**Principle Breakdown**:
- **Design for failure**: 4 metrics (R-01-01, R-01-03, R-01-05, R-01-06)
- **Manage data quality**: 2 metrics (R-02-03, R-02-04)
- **Design for autoscaling**: 2 metrics (R-03-01, R-03-02)

**Used For**:
- "Completion percentage of implemented controls per principle" chart
- Shows which principles need more attention
- Helps prioritize improvement efforts

---

## 🔗 Relationship Diagram

```
                    ┌─────────────────────────┐
                    │  total_percentage_r     │
                    │  (Overall: 38%)         │
                    │  1 row                  │
                    └───────────┬─────────────┘
                                │
                    Aggregates all 8 metrics
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│ waf_controls_r│      │waf_principal_perc_r   │      │  (Same base data)    │
│               │      │                       │      │                      │
│ 8 rows        │      │ 3 rows               │      │  Shared CTEs:        │
│ (one per      │      │ (one per principle)  │      │  - delta_usage       │
│  metric)      │      │                       │      │  - dlt_usage         │
│               │      │ Groups by principle   │      │  - model_serving_... │
│ Individual    │      │                       │      │  - serverless_usage  │
│ scores        │      │ Principle-level       │      │  - autoscale_clusters│
│               │      │ completion            │      │  - autoscale_ware... │
└───────────────┘      └──────────────────────┘      └──────────────────────┘
```

---

## 📊 Data Flow

### Step 1: Shared Base Calculations
All 3 datasets use **identical CTEs** (Common Table Expressions):
- `delta_usage` - Delta/ICEBERG table percentage
- `dlt_usage` - DLT compute usage percentage
- `model_serving_usage` - Model Serving usage percentage
- `serverless_usage` - Serverless compute percentage
- `autoscale_clusters` - Auto-scaling clusters percentage
- `autoscale_warehouses` - Auto-scaling warehouses percentage

### Step 2: Individual Metric Evaluation
Each dataset evaluates the same 8 metrics using the same logic:
- R-01-01: Delta format (≥80%)
- R-01-03: DLT usage (≥30%)
- R-01-05: Model Serving (≥20%)
- R-01-06: Serverless/Managed (≥50%)
- R-02-03: Unity Catalog (exists)
- R-02-04: DLT for data quality (≥30%)
- R-03-01: Auto-scaling clusters (≥80%)
- R-03-02: Auto-scaling warehouses (≥80%)

### Step 3: Different Aggregations

**waf_controls_r**:
- Keeps all 8 rows separate
- Shows individual scores and status
- No aggregation

**waf_principal_percentage_r**:
- Groups by principle
- Aggregates: `GROUP BY principle`
- Calculates completion per principle

**total_percentage_r**:
- Aggregates all metrics
- No grouping
- Single row with overall completion

---

## ✅ Key Relationships

1. **Same Base Data**: All 3 use identical calculation logic for consistency
2. **Different Granularity**: 
   - `waf_controls_r` = Most detailed (8 rows)
   - `waf_principal_percentage_r` = Medium detail (3 rows)
   - `total_percentage_r` = Summary (1 row)
3. **Hierarchical Structure**:
   ```
   total_percentage_r (38%)
   ├── Design for failure (50%)
   │   ├── R-01-01: 85.5% ✅
   │   ├── R-01-03: 25.0% ❌
   │   ├── R-01-05: 15.0% ❌
   │   └── R-01-06: 60.0% ✅
   ├── Manage data quality (50%)
   │   ├── R-02-03: 100.0% ✅
   │   └── R-02-04: 25.0% ❌
   └── Design for autoscaling (50%)
       ├── R-03-01: 75.0% ❌
       └── R-03-02: 90.0% ✅
   ```

4. **Mathematical Relationship**:
   - `total_percentage_r.completion_percent` = Weighted average of `waf_principal_percentage_r.completion_percent`
   - Each principle contributes based on number of metrics it contains

---

## 🎯 Usage in Dashboard

1. **Summary Page**: Uses `total_percentage_r` for overall Reliability score
2. **Reliability Page - Top Chart**: Uses `total_percentage_r` for completion percentage
3. **Reliability Page - Middle Chart**: Uses `waf_principal_percentage_r` for per-principle breakdown
4. **Reliability Page - Bottom Table**: Uses `waf_controls_r` for detailed metric table

---

## 🔄 Consistency Guarantee

All three datasets:
- ✅ Use the same CTEs (shared calculations)
- ✅ Evaluate the same 8 metrics
- ✅ Use the same thresholds
- ✅ Use the same percentage-based logic
- ✅ Will always show consistent results

This ensures that:
- The overall percentage matches the sum of individual metrics
- Principle percentages match the metrics within them
- No discrepancies between different views
