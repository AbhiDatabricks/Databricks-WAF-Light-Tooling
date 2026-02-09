# Reliability Metrics Calculation Documentation

This document explains how each Reliability metric is calculated in the WAF Assessment Dashboard.

## Overview

The Reliability pillar uses **8 metrics** across **3 principles**:
- **Design for failure**: 4 metrics
- **Manage data quality**: 2 metrics  
- **Design for autoscaling**: 2 metrics

## Metrics and Calculation Methods

### R-01-01: Delta/ICEBERG Format Adoption
**Principle**: Design for failure  
**Best Practice**: Use a data format that supports ACID transactions  
**Threshold**: ≥80% of tables use Delta or ICEBERG format

**Calculation**:
```sql
WITH delta_usage AS (
  SELECT 
    COUNT(*) as total_tables,
    SUM(CASE WHEN data_source_format IN ('DELTA', 'ICEBERG') THEN 1 ELSE 0 END) as delta_tables
  FROM system.information_schema.tables
  WHERE table_catalog != 'hive_metastore'
)
SELECT 
  CASE WHEN total_tables > 0 
    THEN (delta_tables * 100.0 / total_tables) 
    ELSE 0 
  END as percentage
FROM delta_usage
```

**Status**: ✅ Implemented if percentage ≥ 80%

---

### R-01-03: Delta Live Tables Usage
**Principle**: Design for failure  
**Best Practice**: Automatically rescue invalid or nonconforming data  
**Threshold**: ≥30% of compute usage is DLT

**Calculation**:
```sql
WITH dlt_usage AS (
  SELECT 
    COUNT(*) as total_compute_usage,
    SUM(CASE WHEN billing_origin_product = 'DLT' THEN 1 ELSE 0 END) as dlt_compute_usage
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
)
SELECT 
  CASE WHEN total_compute_usage > 0 
    THEN (dlt_compute_usage * 100.0 / total_compute_usage) 
    ELSE 0 
  END as percentage
FROM dlt_usage
```

**Status**: ✅ Implemented if percentage ≥ 30%

---

### R-01-05: Model Serving Usage
**Principle**: Design for failure  
**Best Practice**: Use a scalable and production-grade model serving infrastructure  
**Threshold**: ≥20% of ML compute usage is Model Serving

**Calculation**:
```sql
WITH model_serving_usage AS (
  SELECT 
    COUNT(*) as total_ml_compute,
    SUM(CASE WHEN billing_origin_product = 'MODEL_SERVING' THEN 1 ELSE 0 END) as serving_compute
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND (usage_type LIKE '%COMPUTE%' OR billing_origin_product = 'MODEL_SERVING')
)
SELECT 
  CASE WHEN total_ml_compute > 0 
    THEN (serving_compute * 100.0 / total_ml_compute) 
    ELSE 0 
  END as percentage
FROM model_serving_usage
```

**Status**: ✅ Implemented if percentage ≥ 20%

---

### R-01-06: Serverless/Managed Compute Usage
**Principle**: Design for failure  
**Best Practice**: Use managed services for your workloads  
**Threshold**: ≥50% of compute is serverless or managed

**Calculation**:
```sql
WITH serverless_usage AS (
  SELECT 
    COUNT(*) as total_compute,
    SUM(CASE WHEN usage_type LIKE '%SERVERLESS%' OR sku_name LIKE '%SERVERLESS%' THEN 1 ELSE 0 END) as serverless_count
  FROM system.billing.usage
  WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
    AND usage_type LIKE '%COMPUTE%'
)
SELECT 
  CASE WHEN total_compute > 0 
    THEN (serverless_count * 100.0 / total_compute) 
    ELSE 0 
  END as percentage
FROM serverless_usage
```

**Status**: ✅ Implemented if percentage ≥ 50%

---

### R-02-03: Unity Catalog Metastore
**Principle**: Manage data quality  
**Best Practice**: Actively manage schemas  
**Threshold**: Unity Catalog metastore exists

**Calculation**:
```sql
SELECT EXISTS (
  SELECT 1 FROM system.information_schema.metastores LIMIT 1
) as has_metastore
```

**Status**: ✅ Implemented if metastore exists

---

### R-02-04: Delta Live Tables for Data Quality
**Principle**: Manage data quality  
**Best Practice**: Use constraints and data expectations  
**Threshold**: ≥30% of compute usage is DLT

**Calculation**: Same as R-01-03 (DLT usage)

**Status**: ✅ Implemented if percentage ≥ 30%

---

### R-03-01: Auto-Scaling Clusters
**Principle**: Design for autoscaling  
**Best Practice**: Enable autoscaling for ETL workloads  
**Threshold**: ≥80% of clusters have auto-scaling enabled

**Calculation**:
```sql
WITH autoscale_clusters AS (
  SELECT 
    COUNT(*) as total_clusters,
    SUM(CASE WHEN ifnull(max_autoscale_Workers, 0) > 0 THEN 1 ELSE 0 END) as autoscale_clusters
  FROM system.compute.clusters
)
SELECT 
  CASE WHEN total_clusters > 0 
    THEN (autoscale_clusters * 100.0 / total_clusters) 
    ELSE 0 
  END as percentage
FROM autoscale_clusters
```

**Status**: ✅ Implemented if percentage ≥ 80%

---

### R-03-02: Auto-Scaling Warehouses
**Principle**: Design for autoscaling  
**Best Practice**: Use autoscaling for SQL Warehouses  
**Threshold**: ≥80% of warehouses have auto-scaling enabled

**Calculation**:
```sql
WITH autoscale_warehouses AS (
  SELECT 
    COUNT(*) as total_warehouses,
    SUM(CASE WHEN max_clusters - min_clusters > 0 THEN 1 ELSE 0 END) as autoscale_warehouses
  FROM system.compute.warehouses
)
SELECT 
  CASE WHEN total_warehouses > 0 
    THEN (autoscale_warehouses * 100.0 / total_warehouses) 
    ELSE 0 
  END as percentage
FROM autoscale_warehouses
```

**Status**: ✅ Implemented if percentage ≥ 80%

---

## Overall Completion Calculation

The Reliability completion percentage is calculated as:

```
Completion % = (Number of Implemented Metrics / Total Metrics) × 100
```

Where:
- **Total Metrics**: 8
- **Implemented Metrics**: Count of metrics with status = 'Yes'

## Principles Breakdown

### Design for failure (4 metrics)
- R-01-01: Delta/ICEBERG format
- R-01-03: DLT usage
- R-01-05: Model Serving
- R-01-06: Serverless/Managed compute

### Manage data quality (2 metrics)
- R-02-03: Unity Catalog metastore
- R-02-04: DLT for data quality

### Design for autoscaling (2 metrics)
- R-03-01: Auto-scaling clusters
- R-03-02: Auto-scaling warehouses

## Notes

- **R-01-02** (Apache Spark/Photon) was removed from calculation as Apache Spark is always available in Databricks
- All percentage-based checks use a 30-day lookback period for usage metrics
- Thresholds are based on Databricks best practices and WAF recommendations
