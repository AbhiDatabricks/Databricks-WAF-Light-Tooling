#!/usr/bin/env python3
"""
Enhance All Metrics in app.py with Calculation Methods and Low-Score Actions
"""

import re

print("📊 Enhancing All Metrics in WAF Guide...")
print("="*70)

# Read current app.py
with open('streamlit-waf-automation/app.py', 'r') as f:
    content = f.read()

# Define enhancements for each metric
enhancements = {
    "🔒 Sensitive Tables": {
        "calculation": """
            **How We Calculate This:**
            ```sql
            SELECT 
              table_catalog,
              table_schema,
              table_name,
              COUNT(DISTINCT column_name) as masked_columns
            FROM system.information_schema.columns c
            JOIN system.data_classification.results dq 
              ON c.table_full_name = dq.table_full_name
            WHERE dq.sensitive_data_class IS NOT NULL
              OR EXISTS (
                SELECT 1 FROM system.information_schema.column_masks m
                WHERE m.table_full_name = c.table_full_name
              )
            GROUP BY table_catalog, table_schema, table_name
            ```
            **Metric**: Tables with column masks or row filters  
            **Target Score**: >80% of sensitive tables protected
            """,
        "low_score": """
            **🔒 Actions if Score is Low (<60%):**
            
            **Security Actions:**
            1. **Identify PII Columns**:
               ```sql
               SELECT table_full_name, column_name, sensitive_data_class
               FROM system.data_classification.results
               WHERE sensitive_data_class IN ('EMAIL', 'SSN', 'CREDIT_CARD', 'PHONE');
               ```
            
            2. **Apply Column Masks**:
               ```sql
               -- Create mask function
               CREATE FUNCTION mask_email(email STRING)
               RETURNS STRING RETURN CONCAT('***', SUBSTRING(email, -4));
               
               -- Apply mask
               ALTER TABLE customers 
               ALTER COLUMN email 
               SET MASK mask_email;
               ```
            
            3. **Add Row Filters**:
               ```sql
               CREATE FUNCTION filter_by_region(region STRING)
               RETURNS BOOLEAN 
               RETURN region = CURRENT_USER();
               
               ALTER TABLE sales_data
               SET ROW FILTER filter_by_region ON (region);
               ```
            
            4. **Verify Protection**:
               - Test as different users
               - Ensure PII is masked
               - Document masking policies
            
            **Expected Impact**: 100% PII protection compliance
            
            📚 [Masking Docs](https://docs.databricks.com/aws/en/data-governance/unity-catalog/column-masks.html)
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
            **Target Score**: >50% serverless adoption
            """,
        "low_score": """
            **⚡ Actions if Score is Low (<50%):**
            
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
              AVG(execution_duration_ms) as avg_duration_ms,
              ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM system.query.history
            WHERE start_time >= CURRENT_DATE - INTERVAL '30' DAY
            GROUP BY photon_enabled
            ```
            **Metric**: Percentage of queries using Photon  
            **Target Score**: >80% Photon adoption
            """,
        "low_score": """
            **⚡ Actions if Score is Low (<60%):**
            
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
            **Target Score**: >90% Delta tables
            """,
        "low_score": """
            **🛡️ Actions if Score is Low (<80%):**
            
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

# Function to enhance a metric section
def enhance_metric(content, metric_name, enhancement):
    # Find the metric section
    pattern = rf'(elif metric == "{re.escape(metric_name)}":\s+st\.markdown\("""\s+###[^"]*?""")'
    
    # Check if calculation already exists
    if "How We Calculate This" in content and metric_name in content:
        print(f"   ℹ️  {metric_name}: Already enhanced, skipping")
        return content
    
    # Find the section and add enhancements
    metric_pattern = rf'(elif metric == "{re.escape(metric_name)}":\s+st\.markdown\("""\s+###[^\n]+\n\s+\*\*What\*\*:[^\n]+\n\s+\*\*Why\*\*:[^\n]+)'
    
    match = re.search(metric_pattern, content, re.MULTILINE)
    if match:
        # Find where to insert (after "Why" section, before "Actions")
        insert_point = match.end()
        
        # Find the "Actions" section
        actions_match = re.search(r'\*\*Actions\*\*:', content[insert_point:insert_point+500])
        if actions_match:
            actions_start = insert_point + actions_match.start()
            
            # Insert calculation before Actions
            new_content = (
                content[:actions_start] +
                "\n\n" + enhancement["calculation"] + "\n\n" +
                enhancement["low_score"] + "\n\n" +
                content[actions_start:]
            )
            
            # Remove old Actions section (we're replacing it)
            # Actually, let's keep old actions and add new section
            return new_content
    
    return content

# Apply enhancements
fixes = 0
for metric_name, enhancement in enhancements.items():
    old_content = content
    content = enhance_metric(content, metric_name, enhancement)
    if content != old_content:
        fixes += 1
        print(f"✅ Enhanced: {metric_name}")

# Save enhanced file
with open('streamlit-waf-automation/app.py', 'w') as f:
    f.write(content)

print(f"\n{'='*70}")
print(f"✅ Enhanced {fixes} metrics")
print(f"💡 Note: Some metrics may need manual enhancement")
print(f"🚀 Ready to deploy!")
