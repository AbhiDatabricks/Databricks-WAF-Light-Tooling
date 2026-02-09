# New Charts Opportunities Based on System Tables

**Analysis Date:** February 5, 2026  
**Source:** [Databricks System Tables Documentation](https://docs.databricks.com/aws/en/admin/system-tables/)

---

## 📊 Current State

### ✅ **Currently Using (6 tables):**
- `system.billing.usage` - Cost analysis
- `system.compute.clusters` - Cluster metrics
- `system.information_schema.tables` - Table metadata
- `system.access.audit` - Access patterns
- `system.lakeflow.jobs` - Job configurations
- `system.query.history` - Query performance

### ❌ **NOT Using (22 tables):**
Many valuable system tables are available but not utilized!

---

## 🎯 **HIGH-PRIORITY NEW CHARTS**

### 🛡️ **RELIABILITY (8 New Charts)**

#### 1. **Job Run Success Rate Over Time**
**Table:** `system.lakeflow.job_run_timeline`  
**WAF Mapping:** R-04-03 (Job automation framework)  
**Query:**
```sql
SELECT 
  DATE_TRUNC('day', start_time) as date,
  COUNT(*) as total_runs,
  SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) as succeeded,
  SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) as failed,
  ROUND(SUM(CASE WHEN state = 'SUCCEEDED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM system.lakeflow.job_run_timeline
WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC
```
**Chart Type:** Line chart (success rate trend)  
**Value:** Track reliability improvements over time

---

#### 2. **Failed Job Analysis**
**Table:** `system.lakeflow.job_run_timeline`  
**WAF Mapping:** R-04-01 (Recover from failures)  
**Query:**
```sql
SELECT 
  job_id,
  job_name,
  COUNT(*) as failure_count,
  AVG(DATEDIFF(SECOND, start_time, end_time)) as avg_duration_seconds,
  MAX(end_time) as last_failure
FROM system.lakeflow.job_run_timeline
WHERE state = 'FAILED'
  AND start_time >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY job_id, job_name
ORDER BY failure_count DESC
LIMIT 20
```
**Chart Type:** Bar chart (top failing jobs)  
**Value:** Identify jobs needing attention

---

#### 3. **Pipeline Update Success Rate**
**Table:** `system.lakeflow.pipeline_update_timeline`  
**WAF Mapping:** R-04-03 (Job automation)  
**Query:**
```sql
SELECT 
  CASE 
    WHEN update_state = 'COMPLETED' THEN 'Success'
    WHEN update_state = 'FAILED' THEN 'Failed'
    ELSE 'Other'
  END as status,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM system.lakeflow.pipeline_update_timeline
WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY status
```
**Chart Type:** Pie chart  
**Value:** Pipeline reliability tracking

---

#### 4. **Model Serving Endpoint Utilization**
**Table:** `system.serving.endpoint_usage`  
**WAF Mapping:** R-01-05 (Production-grade model serving)  
**Query:**
```sql
SELECT 
  endpoint_name,
  DATE_TRUNC('day', timestamp) as date,
  COUNT(*) as request_count,
  SUM(input_tokens + output_tokens) as total_tokens,
  AVG(latency_ms) as avg_latency_ms
FROM system.serving.endpoint_usage
WHERE timestamp >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY endpoint_name, date
ORDER BY date DESC, request_count DESC
```
**Chart Type:** Line chart (usage trends)  
**Value:** Monitor model serving health

---

#### 5. **MLflow Experiment Activity**
**Table:** `system.mlflow.experiments_latest`  
**WAF Mapping:** R-02-05 (Data-centric ML)  
**Query:**
```sql
SELECT 
  DATE_TRUNC('month', creation_time) as month,
  COUNT(*) as experiment_count,
  COUNT(DISTINCT user_id) as unique_users
FROM system.mlflow.experiments_latest
WHERE creation_time >= CURRENT_DATE - INTERVAL '12' MONTH
GROUP BY month
ORDER BY month DESC
```
**Chart Type:** Bar chart  
**Value:** Track ML adoption and activity

---

#### 6. **Model Training Run Duration**
**Table:** `system.mlflow.runs_latest`  
**WAF Mapping:** R-02-05 (Data-centric ML)  
**Query:**
```sql
SELECT 
  CASE 
    WHEN status = 'FINISHED' THEN 'Success'
    WHEN status = 'FAILED' THEN 'Failed'
    ELSE 'Other'
  END as run_status,
  COUNT(*) as run_count,
  AVG(DATEDIFF(SECOND, start_time, end_time) / 3600.0) as avg_duration_hours
FROM system.mlflow.runs_latest
WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY run_status
```
**Chart Type:** Bar chart  
**Value:** ML training efficiency

---

### ⚡ **PERFORMANCE EFFICIENCY (2 New Charts)**

#### 7. **Node CPU/Memory Utilization**
**Table:** `system.compute.node_timeline`  
**WAF Mapping:** PE-02-07 (Understand hardware/workload)  
**Query:**
```sql
SELECT 
  DATE_TRUNC('hour', timestamp) as hour,
  AVG(cpu_utilization_percent) as avg_cpu,
  AVG(memory_utilization_percent) as avg_memory,
  AVG(disk_utilization_percent) as avg_disk
FROM system.compute.node_timeline
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
GROUP BY hour
ORDER BY hour DESC
LIMIT 168  -- Last 7 days hourly
```
**Chart Type:** Line chart (multi-series)  
**Value:** Right-sizing recommendations, identify underutilized nodes

---

#### 8. **SQL Warehouse Auto-Scaling Events**
**Table:** `system.compute.warehouse_events`  
**WAF Mapping:** PE-01-01 (Serverless capabilities)  
**Query:**
```sql
SELECT 
  warehouse_id,
  event_type,
  COUNT(*) as event_count,
  DATE_TRUNC('day', timestamp) as date
FROM system.compute.warehouse_events
WHERE timestamp >= CURRENT_DATE - INTERVAL '30' DAY
  AND event_type IN ('SCALED_UP', 'SCALED_DOWN', 'STARTED', 'STOPPED')
GROUP BY warehouse_id, event_type, date
ORDER BY date DESC, event_count DESC
```
**Chart Type:** Bar chart  
**Value:** Warehouse efficiency, auto-scaling effectiveness

---

### 💰 **COST OPTIMIZATION (1 New Chart)**

#### 9. **SKU Price Change History**
**Table:** `system.billing.list_prices`  
**WAF Mapping:** CO-01-04 (Up-to-date runtimes)  
**Query:**
```sql
SELECT 
  sku_name,
  effective_date,
  price_per_unit,
  LAG(price_per_unit) OVER (PARTITION BY sku_name ORDER BY effective_date) as previous_price,
  ROUND((price_per_unit - LAG(price_per_unit) OVER (PARTITION BY sku_name ORDER BY effective_date)) * 100.0 / LAG(price_per_unit) OVER (PARTITION BY sku_name ORDER BY effective_date), 2) as price_change_percent
FROM system.billing.list_prices
WHERE effective_date >= CURRENT_DATE - INTERVAL '12' MONTH
ORDER BY effective_date DESC, sku_name
```
**Chart Type:** Line chart  
**Value:** Track pricing changes, cost planning

---

### 🔐 **DATA & AI GOVERNANCE (5 New Charts)**

#### 10. **Data Lineage - Most Connected Tables**
**Table:** `system.access.table_lineage`  
**WAF Mapping:** DG-02-01 (Data lineage)  
**Query:**
```sql
SELECT 
  target_table_full_name as table_name,
  COUNT(DISTINCT source_table_full_name) as upstream_tables,
  COUNT(DISTINCT downstream_table_full_name) as downstream_tables,
  COUNT(*) as total_connections
FROM system.access.table_lineage
WHERE event_time >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY target_table_full_name
ORDER BY total_connections DESC
LIMIT 50
```
**Chart Type:** Bar chart  
**Value:** Identify critical data assets, impact analysis

---

#### 11. **Sensitive Data Classification Coverage**
**Table:** `system.data_classification.results`  
**WAF Mapping:** DG-01-03 (Data classification)  
**Query:**
```sql
SELECT 
  table_schema,
  COUNT(DISTINCT table_name) as tables_classified,
  COUNT(DISTINCT column_name) as columns_classified,
  COUNT(DISTINCT CASE WHEN sensitive_data_class IS NOT NULL THEN column_name END) as sensitive_columns
FROM system.data_classification.results
GROUP BY table_schema
ORDER BY tables_classified DESC
```
**Chart Type:** Bar chart  
**Value:** Track data classification progress, compliance

---

#### 12. **Data Quality Monitoring - Failed Checks**
**Table:** `system.data_quality_monitoring.table_results`  
**WAF Mapping:** R-02-04 (Constraints and expectations)  
**Query:**
```sql
SELECT 
  table_full_name,
  DATE_TRUNC('day', check_time) as date,
  COUNT(*) as total_checks,
  SUM(CASE WHEN check_status = 'FAILED' THEN 1 ELSE 0 END) as failed_checks,
  ROUND(SUM(CASE WHEN check_status = 'FAILED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as failure_rate
FROM system.data_quality_monitoring.table_results
WHERE check_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY table_full_name, date
HAVING failed_checks > 0
ORDER BY failed_checks DESC
LIMIT 50
```
**Chart Type:** Bar chart  
**Value:** Data quality issues, prioritize fixes

---

#### 13. **Table Freshness Monitoring**
**Table:** `system.data_quality_monitoring.table_results`  
**WAF Mapping:** R-02-01 (Layered storage)  
**Query:**
```sql
SELECT 
  table_full_name,
  freshness_check_result,
  freshness_value_hours,
  CASE 
    WHEN freshness_value_hours < 24 THEN 'Fresh (< 1 day)'
    WHEN freshness_value_hours < 168 THEN 'Stale (1-7 days)'
    ELSE 'Very Stale (> 7 days)'
  END as freshness_category
FROM system.data_quality_monitoring.table_results
WHERE freshness_check_result IS NOT NULL
  AND check_time >= CURRENT_DATE - INTERVAL '7' DAY
ORDER BY freshness_value_hours DESC
LIMIT 50
```
**Chart Type:** Bar chart  
**Value:** Identify stale data, freshness compliance

---

#### 14. **Column-Level Lineage for Sensitive Data**
**Table:** `system.access.column_lineage`  
**WAF Mapping:** DG-01-03 (Sensitive data tracking)  
**Query:**
```sql
SELECT 
  target_column_full_name,
  COUNT(DISTINCT source_column_full_name) as source_columns,
  COUNT(DISTINCT downstream_column_full_name) as downstream_columns,
  COUNT(*) as lineage_events
FROM system.access.column_lineage
WHERE event_time >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY target_column_full_name
HAVING COUNT(*) > 10  -- Active columns
ORDER BY lineage_events DESC
LIMIT 50
```
**Chart Type:** Table  
**Value:** Track sensitive data flow, compliance

---

### 🔒 **SECURITY (3 New Charts)**

#### 15. **Network Security Policy Violations**
**Table:** `system.access.inbound_network` + `system.access.outbound_network`  
**WAF Mapping:** SC-01-01 (Network security)  
**Query:**
```sql
SELECT 
  'Inbound' as direction,
  COUNT(*) as denied_attempts,
  COUNT(DISTINCT source_ip) as unique_ips,
  DATE_TRUNC('day', timestamp) as date
FROM system.access.inbound_network
WHERE timestamp >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date

UNION ALL

SELECT 
  'Outbound' as direction,
  COUNT(*) as denied_attempts,
  COUNT(DISTINCT destination_ip) as unique_ips,
  DATE_TRUNC('day', timestamp) as date
FROM system.access.outbound_network
WHERE timestamp >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date

ORDER BY date DESC, direction
```
**Chart Type:** Bar chart (grouped)  
**Value:** Security monitoring, policy effectiveness

---

#### 16. **User Activity Patterns (Security Audit)**
**Table:** `system.access.audit`  
**WAF Mapping:** SC-02-01 (Access monitoring)  
**Query:**
```sql
SELECT 
  user_identity.email as user_email,
  action_name,
  COUNT(*) as action_count,
  COUNT(DISTINCT DATE_TRUNC('day', event_time)) as active_days,
  MAX(event_time) as last_activity
FROM system.access.audit
WHERE event_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND action_name IN ('getTable', 'createTable', 'deleteTable', 'updateTable')
GROUP BY user_email, action_name
ORDER BY action_count DESC
LIMIT 100
```
**Chart Type:** Table  
**Value:** User behavior analysis, anomaly detection

---

#### 17. **Workspace Distribution & Configuration**
**Table:** `system.access.workspaces_latest`  
**WAF Mapping:** SC-03-01 (Multi-workspace governance)  
**Query:**
```sql
SELECT 
  deployment_name,
  workspace_status,
  COUNT(*) as workspace_count,
  SUM(CASE WHEN unity_catalog_enabled = true THEN 1 ELSE 0 END) as uc_enabled_count
FROM system.access.workspaces_latest
GROUP BY deployment_name, workspace_status
ORDER BY workspace_count DESC
```
**Chart Type:** Bar chart  
**Value:** Multi-workspace visibility, UC adoption

---

## 📊 **Summary**

| Pillar | New Charts | Priority |
|--------|-----------|----------|
| **Reliability** | 6 charts | 🔴 High |
| **Performance** | 2 charts | 🟡 Medium |
| **Cost** | 1 chart | 🟡 Medium |
| **Governance** | 5 charts | 🔴 High |
| **Security** | 3 charts | 🔴 High |
| **Total** | **17 charts** | |

---

## 🎯 **Recommended Implementation Order**

### Phase 1: Reliability (Critical)
1. Job Run Success Rate Over Time
2. Failed Job Analysis
3. Pipeline Update Success Rate

### Phase 2: Governance (Compliance)
4. Data Lineage - Most Connected Tables
5. Sensitive Data Classification Coverage
6. Data Quality Monitoring - Failed Checks

### Phase 3: Performance & Security
7. Node CPU/Memory Utilization
8. Network Security Policy Violations
9. User Activity Patterns

### Phase 4: Advanced
10. Model Serving Endpoint Utilization
11. MLflow Experiment Activity
12. Column-Level Lineage

---

## 💡 **Key Benefits**

✅ **Real Data** - All from system tables (no Excel status needed)  
✅ **Actionable** - Direct insights for improvement  
✅ **WAF-Aligned** - Maps to WAF identifiers  
✅ **Automated** - No manual data entry  
✅ **Historical** - Trend analysis over time  

---

## 📚 **References**

- [Databricks System Tables Documentation](https://docs.databricks.com/aws/en/admin/system-tables/)
- System Tables Relationships Diagram (DONOTCHECKIN/SystemTables.png)
- WAF Excel File (DONOTCHECKIN/Well-Architected Framework (WAF) - 22042025.xlsx)

---

*Generated: February 5, 2026*
