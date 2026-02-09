#!/usr/bin/env python3
"""
Enhance WAF Guide with Calculation Methods and Low-Score Actions
"""

import json
import pandas as pd

print("📊 Enhancing WAF Guide with Calculation Methods & Actions...")
print("="*70)

# Load identifier details from Excel
excel_file = 'DONOTCHECKIN/Well-Architected Framework (WAF) - 22042025.xlsx'
combined_df = pd.read_excel(excel_file, sheet_name='CombinedList')

# Create mapping
identifier_details = {}
for idx, row in combined_df.iterrows():
    identifier = row.get('Identifier', '')
    if pd.notna(identifier):
        identifier_details[identifier] = {
            'practice': str(row.get('Best Practice', '')),
            'capability': str(row.get('Databricks Capabilities', '')),
            'details': str(row.get('Details', ''))[:500] if pd.notna(row.get('Details')) else ''
        }

# Define calculation methods and actions for each metric
metric_enhancements = {
    # Data & AI Governance
    "🚨 Unused Tables": {
        "calculation": """
**How We Calculate This:**
```sql
SELECT 
  table_catalog,
  table_schema,
  table_name,
  DATEDIFF(day, MAX(last_access_time), CURRENT_DATE) as days_unused
FROM system.information_schema.tables t
LEFT JOIN system.access.table_lineage tl 
  ON t.table_full_name = tl.target_table_full_name
WHERE last_access_time < CURRENT_DATE - INTERVAL '30' DAY
  OR last_access_time IS NULL
GROUP BY table_catalog, table_schema, table_name
HAVING days_unused >= 30
```
**Metric**: Count of tables with zero access in last 30 days
**Target**: <5% of total tables
        """,
        "low_score_actions": """
**🚨 If Score is Low (<60%):**

**Immediate Actions:**
1. **Identify unused tables** (30+ days):
   ```sql
   SELECT table_full_name, days_unused 
   FROM unused_tables_view 
   WHERE days_unused >= 30
   ORDER BY days_unused DESC;
   ```

2. **Review and Archive**:
   - Check with data owners before deletion
   - Archive to cold storage if needed
   - Document in data catalog

3. **Set Retention Policies**:
   ```sql
   -- Add retention tag
   ALTER TABLE catalog.schema.table 
   SET TAGS ('retention_days' = '90');
   ```

4. **Automate Cleanup**:
   - Create scheduled job to identify unused tables
   - Send monthly reports to data owners
   - Auto-archive after 90 days

**Expected Impact**: 20-30% storage cost reduction

📚 [Cost Optimization Guide](https://docs.databricks.com/discover/pages/optimize-data-workloads-guide)
        """
    },
    
    "🔐 Unsecured Tables": {
        "calculation": """
**How We Calculate This:**
```sql
SELECT 
  table_catalog,
  table_schema,
  table_name,
  grantee
FROM system.information_schema.table_privileges
WHERE grantee = 'account users'
  AND privilege_type = 'SELECT'
GROUP BY table_catalog, table_schema, table_name, grantee
```
**Metric**: Tables with 'account users' SELECT permission
**Target**: 0 unsecured tables (100% secured)
        """,
        "low_score_actions": """
**🚨 If Score is Low (<80%):**

**URGENT Security Actions:**
1. **Immediate Revocation**:
   ```sql
   -- Revoke public access
   REVOKE SELECT ON TABLE catalog.schema.table 
   FROM `account users`;
   ```

2. **Grant to Specific Groups**:
   ```sql
   -- Grant to data team
   GRANT SELECT ON TABLE catalog.schema.table 
   TO `data_analysts`;
   
   -- Grant to business users
   GRANT SELECT ON TABLE catalog.schema.table 
   TO `business_users`;
   ```

3. **Audit All Tables**:
   ```sql
   SELECT table_full_name, grantee, privilege_type
   FROM system.information_schema.table_privileges
   WHERE grantee = 'account users';
   ```

4. **Set Default Permissions**:
   - Create catalog-level default: NO public access
   - Use groups for access control
   - Document access policies

**Goal**: Zero unsecured tables within 7 days

📚 [Security Best Practices PDF](https://www.databricks.com/sites/default/files/2024-08/azure-databricks-security-best-practices-threat-model.pdf)
        """
    },
    
    "🔄 Jobs on All-Purpose Clusters": {
        "calculation": """
**How We Calculate This:**
```sql
SELECT 
  job_id,
  job_name,
  cluster_type,
  COUNT(*) as run_count
FROM system.lakeflow.jobs j
JOIN system.lakeflow.job_run_timeline jr ON j.job_id = jr.job_id
WHERE cluster_type = 'ALL_PURPOSE'
  AND start_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY job_id, job_name, cluster_type
```
**Metric**: Jobs running on all-purpose clusters
**Target**: <10% of jobs on all-purpose
        """,
        "low_score_actions": """
**💰 If Score is Low (<60%):**

**Cost Optimization Actions:**
1. **Identify Expensive Jobs**:
   ```sql
   SELECT job_name, total_cost, run_count
   FROM expensive_jobs_view
   WHERE cluster_type = 'ALL_PURPOSE'
   ORDER BY total_cost DESC;
   ```

2. **Convert to Job Clusters**:
   - Open job in Databricks UI
   - Settings → Cluster → Change to "Job cluster"
   - Or use API:
   ```python
   jobs.update(job_id, {
       "new_cluster": {
           "cluster_name": "job-cluster",
           "spark_version": "latest"
       }
   })
   ```

3. **Calculate Savings**:
   - All-purpose: ~$0.40/DBU
   - Job clusters: ~$0.15/DBU
   - **Savings: 60-70% per job**

4. **Priority Order**:
   - High-frequency jobs first (daily/hourly)
   - Long-running jobs
   - Production workloads

**Expected Savings**: 30-40% on compute costs

📚 [Cluster Types Guide](https://docs.databricks.com/aws/en/compute/configure.html)
        """
    },
    
    "⚡ Serverless Adoption": {
        "calculation": """
**How We Calculate This:**
```sql
SELECT 
  CASE 
    WHEN usage_type LIKE '%SERVERLESS%' THEN 'Serverless'
    ELSE 'Traditional'
  END as compute_type,
  COUNT(*) as usage_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM system.billing.usage
WHERE usage_start_time >= CURRENT_DATE - INTERVAL '30' DAY
  AND usage_type LIKE '%COMPUTE%'
GROUP BY compute_type
```
**Metric**: Percentage of workloads using serverless
**Target**: >50% serverless adoption
        """,
        "low_score_actions": """
**⚡ If Score is Low (<50%):**

**Performance & Cost Actions:**
1. **Enable Serverless for SQL Warehouses**:
   - SQL → Warehouses → Edit → Enable Serverless
   - Instant startup (no cold start)
   - Auto-scaling included

2. **Use Serverless for Notebooks**:
   - Compute → Create → Serverless
   - No cluster management needed
   - Pay only for compute time

3. **Migrate Jobs to Serverless**:
   ```python
   # In job configuration
   {
       "compute": [{
           "compute_key": "serverless"
       }]
   }
   ```

4. **Benefits**:
   - ⚡ Instant startup (0 seconds vs 2-5 min)
   - 💰 No idle costs
   - 📈 Auto-scaling built-in
   - 🔧 Zero maintenance

**Expected Impact**: 20-30% cost reduction + faster startup

📚 [Serverless Guide](https://docs.databricks.com/aws/en/compute/serverless/index.html)
        """
    },
    
    "🎯 Photon Usage": {
        "calculation": """
**How We Calculate This:**
```sql
SELECT 
  CASE 
    WHEN photon_enabled = true THEN 'Photon'
    ELSE 'Standard'
  END as engine_type,
  COUNT(*) as query_count,
  AVG(execution_duration_ms) as avg_duration_ms
FROM system.query.history
WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY photon_enabled
```
**Metric**: Percentage of queries using Photon
**Target**: >80% Photon adoption
        """,
        "low_score_actions": """
**⚡ If Score is Low (<60%):**

**Performance Optimization Actions:**
1. **Enable Photon on SQL Warehouses**:
   - SQL → Warehouses → Edit → Enable Photon
   - Automatic for new warehouses

2. **Enable Photon on Clusters**:
   ```python
   {
       "photon": true,
       "spark_version": "latest"
   }
   ```

3. **Verify Photon Usage**:
   ```sql
   SELECT query_text, photon_enabled, execution_duration_ms
   FROM system.query.history
   WHERE start_time >= CURRENT_DATE - INTERVAL '7' DAY
   ORDER BY execution_duration_ms DESC
   LIMIT 20;
   ```

4. **Benefits**:
   - ⚡ 3-5x faster queries
   - 💰 Same cost as standard
   - 📊 Better for aggregations, joins, filters

**Expected Impact**: 3-5x query performance improvement

📚 [Photon Guide](https://docs.databricks.com/aws/en/compute/photon.html)
        """
    },
    
    "📦 Delta Table Format": {
        "calculation": """
**How We Calculate This:**
```sql
SELECT 
  table_catalog,
  table_schema,
  COUNT(*) as total_tables,
  SUM(CASE WHEN table_type = 'MANAGED' THEN 1 ELSE 0 END) as delta_tables,
  ROUND(SUM(CASE WHEN table_type = 'MANAGED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as delta_percentage
FROM system.information_schema.tables
WHERE table_catalog != 'hive_metastore'
GROUP BY table_catalog, table_schema
```
**Metric**: Percentage of tables using Delta format
**Target**: >90% Delta tables
        """,
        "low_score_actions": """
**🛡️ If Score is Low (<80%):**

**Reliability & Performance Actions:**
1. **Convert Parquet/CSV to Delta**:
   ```sql
   -- Convert existing Parquet
   CONVERT TO DELTA parquet.`/path/to/data`;
   
   -- Or create new Delta table
   CREATE TABLE catalog.schema.table 
   USING DELTA 
   AS SELECT * FROM old_parquet_table;
   ```

2. **Benefits of Delta**:
   - ✅ ACID transactions (data consistency)
   - ⏰ Time travel (recover from bad writes)
   - 🔒 Schema enforcement
   - ⚡ 90% faster queries
   - 📦 Automatic compaction

3. **Migration Priority**:
   - High-traffic tables first
   - Tables used in ETL pipelines
   - Critical business tables

4. **Verify Conversion**:
   ```sql
   SELECT table_name, table_type, table_format
   FROM system.information_schema.tables
   WHERE table_format != 'DELTA';
   ```

**Expected Impact**: Better reliability + 90% query performance gain

📚 [Delta Best Practices](https://docs.databricks.com/aws/en/delta/best-practices.html)
        """
    }
}

# Save enhancements
with open('DONOTCHECKIN/metric_enhancements.json', 'w') as f:
    json.dump(metric_enhancements, f, indent=2)

print(f"\n✅ Created enhancements for {len(metric_enhancements)} metrics")
print(f"✅ Saved to: DONOTCHECKIN/metric_enhancements.json")
print(f"\n💡 Next: Integrate into app.py")
