import streamlit as st

# Set page config
st.set_page_config(
    page_title="WAF Assessment Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard configuration
INSTANCE_URL = "https://dbc-2a8b378f-7d51.cloud.databricks.com"
DASHBOARD_ID = "01f103607e78117592509ae89bd0d7da"
WORKSPACE_ID = "2a8b378f7d51"
EMBED_URL = f"{INSTANCE_URL}/embed/dashboardsv3/{DASHBOARD_ID}?o={WORKSPACE_ID}"

# Sidebar with explanations
with st.sidebar:
    st.title("📖 WAF Guide")
    
    category = st.selectbox(
        "Select category:",
        [
            "📊 Summary",
            "🔐 Data & AI Governance",
            "💰 Cost Optimization",
            "⚡ Performance Efficiency",
            "🛡️ Reliability"
        ]
    )
    
    st.markdown("---")
    
    if category == "📊 Summary":
        st.markdown("""
        ### WAF Assessment Overview
        
        The dashboard measures your environment across 4 pillars:
        
        **🔐 Data & AI Governance** (25%)
        - Table security & access control
        - Data quality & lineage
        - PII protection
        
        **💰 Cost Optimization** (25%)
        - Compute efficiency
        - Storage optimization
        - Resource utilization
        
        **⚡ Performance Efficiency** (25%)
        - Query optimization
        - Cluster performance
        - Photon adoption
        
        **🛡️ Reliability** (25%)
        - System availability
        - Auto-recovery
        - Production readiness
        
        ### How Overall Score is Calculated
        
        The **Overall WAF Score** is calculated by:
        
        1. **Individual Pillar Scores**: Each pillar calculates its completion percentage
           - Counts how many WAF controls are "Pass" (meet threshold)
           - Formula: `(Passed Controls / Total Controls) × 100`
        
        2. **Summary Aggregation**: Combines all 4 pillar scores
           - Each pillar contributes equally (25% weight)
           - Shows individual pillar scores for comparison
        
        3. **Score Interpretation**:
           - 🎯 **80%+**: Excellent - Production-ready
           - 🟨 **60-80%**: Good - Minor improvements needed
           - 🟧 **40-60%**: Needs improvement - Address gaps
           - 🔴 **<40%**: Critical gaps - Immediate action required
        
        ### Target Scores
        - 🎯 **80%+**: Excellent
        - 🟨 **60-80%**: Good
        - 🟧 **40-60%**: Needs improvement
        - 🔴 **<40%**: Critical gaps
        
        ### Actions
        Select a pillar above to see:
        - How each metric is calculated
        - Thresholds for each control
        - Specific actions if your score is low
        """)
    
    elif category == "🔐 Data & AI Governance":
        metric = st.selectbox("Select metric:", [
            "🚨 Unused Tables",
            "🔐 Unsecured Tables", 
            "🔒 Sensitive Tables",
            "✅ Active Tables",
            "👥 Active Users",
            "📊 Table Lineage",
            "🏷️ Table Tagging"
        ])
        
        if metric == "🚨 Unused Tables":
            st.markdown("""
            ### Unused Tables
            **What**: Tables with zero access in 30 days
            
            **Why**: 💰 Wasted storage costs
            
            **Actions**:
            1. Review unused 30+ days
            2. Archive or DROP tables
            3. Set retention policies
            
            ```sql
            DROP TABLE IF EXISTS catalog.schema.unused_table;
            ```
            
            📚 [Cost Guide](https://docs.databricks.com/discover/pages/optimize-data-workloads-guide)
            """)
        
        elif metric == "🔐 Unsecured Tables":
            st.markdown("""
            ### Unsecured Tables
            **What**: Tables accessible to ALL users
            
            **Why**: 🚨 SECURITY RISK - data exposed
            
            **URGENT Actions**:
            1. Revoke 'account users' access
            2. Grant to specific groups
            
            ```sql
            REVOKE SELECT ON TABLE xxx 
            FROM `account users`;
            
            GRANT SELECT ON TABLE xxx 
            TO `data_analysts`;
            ```
            
            **Goal**: Zero unsecured tables
            
            📚 [Security PDF](https://www.databricks.com/sites/default/files/2024-08/azure-databricks-security-best-practices-threat-model.pdf)
            """)
        
        elif metric == "🔒 Sensitive Tables":
            st.markdown("""
            ### Sensitive Tables
            **What**: Tables with masks/row filters
            
            **Why**: ✅ Proper PII protection
            
            **Actions**:
            1. Identify PII columns
            2. Apply column masks
            3. Add row filters
            
            ```sql
            ALTER TABLE customers 
            ALTER COLUMN email 
            SET MASK mask_email_fn;
            ```
            
            📚 [Masking Docs](https://docs.databricks.com/aws/en/data-governance/unity-catalog/column-masks.html)
            """)
        
        elif metric == "✅ Active Tables":
            st.markdown("""
            ### Active Tables
            **What**: Tables accessed recently
            
            **Why**: Focus optimization here
            
            **Actions**:
            ```sql
            OPTIMIZE catalog.schema.table;
            ANALYZE TABLE catalog.schema.table 
            COMPUTE STATISTICS;
            ```
            
            📚 [Optimization](https://docs.databricks.com/aws/en/delta/optimize.html)
            """)
        
        elif metric == "👥 Active Users":
            st.markdown("""
            ### Active Users
            **What**: Users accessing data
            
            **Why**: Adoption indicator
            
            **Actions**:
            1. Enable SSO/SCIM
            2. Create user groups
            3. Provide training
            
            📚 [User Mgmt](https://docs.databricks.com/aws/en/admin/users-groups/index.html)
            """)
        
        elif metric == "📊 Table Lineage":
            st.markdown("""
            ### Table Lineage
            **What**: Tables with tracked data flow
            
            **Why**: Enables impact analysis
            
            **Actions**:
            1. Use notebooks/workflows (auto-tracked)
            2. Avoid external ETL tools
            3. Enable lineage tracking
            
            📚 [Lineage](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-lineage.html)
            """)
        
        else:  # Table Tagging
            st.markdown("""
            ### Table Tagging
            **What**: Tables with metadata tags
            
            **Why**: Discoverability & governance
            
            **Actions**:
            ```sql
            ALTER TABLE sales.customers 
            SET TAGS ('PII' = 'true', 'Owner' = 'finance');
            ```
            
            **Recommended tags**:
            - Owner, Department
            - Sensitivity (Public/Internal/Confidential)
            - Cost center, Project
            
            📚 [Tags](https://docs.databricks.com/aws/en/data-governance/unity-catalog/tags.html)
            """)
    
    elif category == "💰 Cost Optimization":
        st.markdown("""
        ### 💰 Cost Optimization Pillar - Score Calculation
        
        **How the Score is Calculated**:
        
        The Cost Optimization score uses **9 WAF controls** across **3 principles**:
        
        1. **Choose optimal resources** (5 controls)
        2. **Dynamically allocate resources** (1 control)
        3. **Monitor and control cost** (3 controls)
        
        **Formula**: `(Controls with "Pass" status / Total 9 controls) × 100`
        
        Each control uses **percentage-based thresholds**:
        - Calculates actual usage/optimization percentage
        - Compares against required threshold
        - Status: "Pass" if ≥ threshold, "Fail" if < threshold
        
        **Example**: If 4 out of 9 controls pass → Score = 44.4%
        
        ---
        """)
        
        metric = st.selectbox("Select metric:", [
            "📦 Delta Table Formats (CO-01-01)",
            "🖥️ SQL Warehouse Usage (CO-01-03)",
            "🔄 Up-to-Date Runtimes (CO-01-04)",
            "⚡ Serverless Usage (CO-01-06)",
            "🎯 Photon Usage (CO-01-09)",
            "📊 Compute Policies (CO-02-03)",
            "💰 Cost Monitoring (CO-03-01)",
            "🏷️ Cluster Tagging (CO-03-02)",
            "📈 Cost Observability (CO-03-03)"
        ])
        
        if metric == "📦 Delta Table Formats (CO-01-01)":
            st.markdown("""
            ### Performance Optimized Data Formats (CO-01-01)
            
            **How Score is Calculated**:
            ```
            Score = (Delta/ICEBERG Tables / Total Tables) × 100
            ```
            
            - Counts all tables in Unity Catalog
            - Identifies tables with DELTA or ICEBERG format
            - Calculates percentage of optimized format tables
            
            **Threshold**: ≥80% of tables must use Delta/ICEBERG
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 80%
            - ❌ **Fail** if score < 80%
            
            ---
            
            **Why This Matters**: 
            - **Cost Savings**: Delta reduces storage by 30-50% through compaction
            - **Performance**: 90% faster queries = lower compute costs
            - **Efficiency**: Automatic optimization reduces manual tuning
            
            **Actions if Score is Low (<80%)**:
            
            1. **Identify Non-Delta Tables**:
               ```sql
               SELECT table_catalog, table_schema, table_name, data_source_format
               FROM system.information_schema.tables
               WHERE data_source_format NOT IN ('DELTA', 'ICEBERG')
                 AND table_catalog != 'hive_metastore';
               ```
            
            2. **Convert to Delta**:
               ```sql
               -- Convert existing Parquet/CSV
               CONVERT TO DELTA parquet.`/path/to/data`;
               
               -- Or recreate as Delta
               CREATE TABLE catalog.schema.new_table 
               USING DELTA AS SELECT * FROM old_table;
               ```
            
            3. **Set Default Format**:
               - Configure workspace default to Delta
               - Update table creation templates
               - Train team on Delta benefits
            
            4. **Expected Savings**:
               - 30-50% storage reduction
               - 90% query performance improvement
               - Reduced compute costs
            
            **Goal**: Achieve 80%+ Delta/ICEBERG adoption
            
            📚 [Delta Best Practices](https://docs.databricks.com/aws/en/delta/best-practices.html) | [Convert to Delta](https://docs.databricks.com/aws/en/delta/convert-to-delta.html)
            """)
        
        elif metric == "🔄 Jobs on All-Purpose Clusters":
            st.markdown("""
            ### Jobs on All-Purpose
            **What**: Production jobs running on all-purpose clusters
            
            **Why**: 💰 All-purpose costs 30-40% MORE
            
            **Cost Impact**:
            - All-purpose: $X/DBU
            - Jobs: $0.XX/DBU (70% cheaper)
            
            **Actions**:
            1. Identify production jobs
            2. Switch to Jobs clusters:
            ```python
            # In workflow settings
            cluster_type: "job_cluster"
            ```
            3. Set `new_cluster` in job config
            
            **Savings**: 30-40% on compute costs
            
            📚 [Cluster Types](https://docs.databricks.com/aws/en/compute/configure.html)
            """)
        
        elif metric == "🖥️ SQL vs All-Purpose":
            st.markdown("""
            ### SQL Workloads on All-Purpose
            **What**: BI/Analytics on all-purpose clusters
            
            **Why**: SQL warehouses optimized for queries
            
            **Benefits of SQL Warehouses**:
            - Serverless option (no management)
            - Auto-scaling
            - Query caching
            - Optimized for BI tools
            - Lower cost per query
            
            **Actions**:
            1. Identify SQL workloads
            2. Create SQL warehouse:
            ```sql
            -- Move queries to SQL warehouse
            -- Connect BI tools to SQL endpoint
            ```
            3. Migrate dashboards/reports
            
            📚 [SQL Warehouses](https://docs.databricks.com/aws/en/sql/admin/sql-endpoints.html)
            """)
        
        elif metric == "⚡ Serverless Adoption":
            st.markdown("""
            ### Serverless Adoption
            **What**: % of workloads using serverless
            
            **Why**: No cluster management + auto-scale
            
            **Serverless Benefits**:
            - Zero management overhead
            - Instant startup (<10 sec)
            - Pay per query
            - Auto-scaling
            - Latest runtime
            
            **Available For**:
            - SQL warehouses ✅
            - Notebooks ✅
            - Workflows ✅
            
            **Actions**:
            1. Enable serverless SQL
            2. Use serverless notebooks
            3. Switch workflows to serverless
            
            **Cost**: Often cheaper for bursty workloads
            
            📚 [Serverless](https://docs.databricks.com/aws/en/serverless-compute/index.html)
            """)
        
        elif metric == "🎯 Photon Usage":
            st.markdown("""
            ### Photon Usage
            **What**: % of clusters with Photon enabled
            
            **Why**: 3x faster queries, same cost
            
            **Photon Benefits**:
            - 3x query speedup
            - Lower cost/query
            - Better concurrency
            - Automatic optimization
            
            **Works Best For**:
            - SQL queries
            - Aggregations
            - Joins on large tables
            - Data engineering (ETL)
            
            **Actions**:
            ```python
            # Enable in cluster config
            "runtime_engine": "PHOTON"
            ```
            
            **Goal**: 100% on production workloads
            
            📚 [Photon](https://docs.databricks.com/aws/en/runtime/photon.html)
            """)
        
        elif metric == "📊 Cluster Utilization":
            st.markdown("""
            ### Cluster Utilization
            **What**: CPU/Memory usage % over time
            
            **Why**: Low utilization = wasted money
            
            **Target Ranges**:
            - 🎯 60-80%: Optimal
            - 🟧 <40%: Over-provisioned
            - 🔴 >90%: Under-provisioned
            
            **Actions for Low Utilization**:
            1. Reduce cluster size
            2. Enable auto-scaling
            3. Use spot instances
            4. Consolidate workloads
            
            **Actions for High Utilization**:
            1. Enable auto-scaling
            2. Optimize queries
            3. Add nodes
            
            📚 [Monitoring](https://docs.databricks.com/aws/en/clusters/cluster-metrics.html)
            """)
        
        elif metric == "⏱️ Auto-Termination":
            st.markdown("""
            ### Auto-Termination
            **What**: Clusters auto-stop after inactivity
            
            **Why**: Prevent clusters running idle
            
            **Cost Impact**:
            - Cluster running idle 8 hrs/day = 33% waste
            - Auto-term = automatic savings
            
            **Recommendations**:
            - Interactive: 30-60 min
            - Jobs: Terminate after job
            - SQL: Auto-stop built-in
            
            **Actions**:
            ```python
            # Set in cluster config
            "autotermination_minutes": 30
            ```
            
            **Savings**: 20-40% on compute
            
            📚 [Auto-termination](https://docs.databricks.com/aws/en/clusters/auto-termination.html)
            """)
        
        elif metric == "📈 Auto-Scaling":
            st.markdown("""
            ### Auto-Scaling
            **What**: Clusters scale up/down with load
            
            **Why**: Right-size automatically
            
            **Benefits**:
            - Scale up for heavy workloads
            - Scale down for light workloads
            - Pay only for what you use
            
            **Configuration**:
            ```python
            "autoscale": {
                "min_workers": 2,
                "max_workers": 10
            }
            ```
            
            **Best For**:
            - Variable workloads
            - Multi-user clusters
            - Production jobs with fluctuating data
            
            📚 [Auto-scaling](https://docs.databricks.com/aws/en/clusters/autoscaling.html)
            """)
        
        elif metric == "💵 Spot Instances":
            st.markdown("""
            ### Spot Instance Usage
            **What**: % of clusters using spot/preemptible VMs
            
            **Why**: 60-80% cheaper than on-demand
            
            **Savings**:
            - On-demand: $X/hour
            - Spot: $0.20X/hour (80% off)
            
            **Safe For**:
            - Development ✅
            - Testing ✅
            - ETL jobs with retries ✅
            - Batch processing ✅
            
            **NOT For**:
            - Real-time streaming ❌
            - Interactive analysis (users waiting) ❌
            
            **Actions**:
            ```python
            "aws_attributes": {
                "first_on_demand": 1,
                "availability": "SPOT_WITH_FALLBACK"
            }
            ```
            
            📚 [Spot Instances](https://docs.databricks.com/aws/en/clusters/spot-instances.html)
            """)
        
        elif metric == "🏷️ Cost Tagging":
            st.markdown("""
            ### Cost Tagging
            **What**: % of clusters with cost allocation tags
            
            **Why**: Track spending by team/project
            
            **Recommended Tags**:
            - Team, Department
            - Project, Cost center
            - Environment (prod/dev/test)
            - Owner
            
            **Actions**:
            ```python
            # Add tags to cluster
            "custom_tags": {
                "Team": "DataEngineering",
                "CostCenter": "12345",
                "Project": "ETL",
                "Owner": "john.doe@company.com"
            }
            ```
            
            **Benefits**:
            - Chargeback to teams
            - Identify cost drivers
            - Budget allocation
            
            📚 [Tagging](https://docs.databricks.com/aws/en/admin/account-settings/tag-policies.html)
            """)
        
        else:  # Billing & Chargeback
            st.markdown("""
            ### Billing & Chargeback
            **What**: Cost tracking and allocation
            
            **Why**: Accountability drives efficiency
            
            **Use System Tables**:
            ```sql
            -- Get costs by team
            SELECT 
                usage_metadata.cluster_tags.Team,
                SUM(list_price) as total_cost
            FROM system.billing.usage
            WHERE usage_date >= current_date - 30
            GROUP BY usage_metadata.cluster_tags.Team
            ORDER BY total_cost DESC;
            ```
            
            **Actions**:
            1. Enable system tables
            2. Tag all resources
            3. Create cost dashboards
            4. Implement chargeback
            5. Set team budgets
            
            📚 [System Tables](https://docs.databricks.com/aws/en/admin/system-tables/billing.html)
            """)
    
    elif category == "⚡ Performance Efficiency":
        metric = st.selectbox("Select metric:", [
            "⚡ Photon Workloads",
            "📊 Cluster Performance",
            "🐍 Python UDFs",
            "🚀 Query Optimization",
            "💾 Caching Strategy"
        ])
        
        if metric == "⚡ Photon Workloads":
            st.markdown("""
            ### Photon Workloads
            **What**: % of workloads using Photon
            
            **Why**: 3x faster, same cost
            
            **Performance Gains**:
            - Aggregations: 3-5x faster
            - Joins: 2-4x faster
            - Scans: 2-3x faster
            
            **Enable**:
            ```python
            "runtime_engine": "PHOTON"
            ```
            
            **Goal**: 100% on production
            
            📚 [Photon](https://docs.databricks.com/aws/en/runtime/photon.html)
            """)
        
        elif metric == "📊 Cluster Performance":
            st.markdown("""
            ### Cluster Performance
            **What**: Query execution metrics
            
            **Key Metrics**:
            - Query duration
            - Data scanned
            - Spill to disk
            - Shuffle size
            
            **Optimization Tips**:
            1. Partition pruning
            2. Column pruning (avoid SELECT *)
            3. Predicate pushdown
            4. Broadcast joins for small tables
            
            ```sql
            -- Good: Filters early
            SELECT id, name 
            FROM large_table 
            WHERE date = '2024-01-01'
            
            -- Bad: Scans everything
            SELECT * FROM large_table
            ```
            
            📚 [Query Tuning](https://docs.databricks.com/aws/en/optimizations/index.html)
            """)
        
        elif metric == "🐍 Python UDFs":
            st.markdown("""
            ### Python UDFs
            **What**: Custom Python functions in queries
            
            **Why**: Python UDFs are SLOW
            
            **Performance**:
            - SQL functions: Fast ✅
            - Python UDFs: 10-100x slower ❌
            - Pandas UDFs: Better but still slow
            
            **Actions**:
            1. Replace with SQL functions
            2. Use Pandas UDFs if needed
            3. Vectorize operations
            
            ```python
            # Instead of Python UDF
            @udf
            def slow_func(x):
                return x * 2
            
            # Use SQL
            SELECT col * 2 FROM table
            
            # Or Pandas UDF
            @pandas_udf("int")
            def fast_func(x: pd.Series) -> pd.Series:
                return x * 2
            ```
            
            📚 [UDF Performance](https://docs.databricks.com/aws/en/udf/python.html)
            """)
        
        elif metric == "🚀 Query Optimization":
            st.markdown("""
            ### Query Optimization
            **What**: Query performance best practices
            
            **Top Optimizations**:
            
            1. **OPTIMIZE tables weekly**
            ```sql
            OPTIMIZE catalog.schema.table;
            ```
            
            2. **Update statistics**
            ```sql
            ANALYZE TABLE catalog.schema.table 
            COMPUTE STATISTICS;
            ```
            
            3. **Z-ORDER on filter columns**
            ```sql
            OPTIMIZE table 
            ZORDER BY (customer_id, date);
            ```
            
            4. **Liquid Clustering**
            ```sql
            ALTER TABLE sales 
            CLUSTER BY (region, product);
            ```
            
            5. **Partition correctly**
            - Date-based for time-series
            - Don't over-partition (<1GB per partition)
            
            📚 [Delta Optimization](https://docs.databricks.com/aws/en/delta/optimize.html)
            """)
        
        else:  # Caching
            st.markdown("""
            ### Caching Strategy
            **What**: Delta cache usage
            
            **Why**: 2-5x faster repeated queries
            
            **How It Works**:
            - Caches hot data on local SSD
            - Automatic + intelligent
            - Free (included)
            
            **Best For**:
            - Dashboards
            - BI queries
            - Repeated analysis
            - Small-medium datasets
            
            **Enable**:
            ```python
            # Already enabled by default
            # Use instance types with local SSDs
            "node_type_id": "i3.xlarge"
            ```
            
            📚 [Delta Cache](https://docs.databricks.com/aws/en/optimizations/delta-cache.html)
            """)
    
    else:  # Reliability
        st.markdown("""
        ### 🛡️ Reliability Pillar - Score Calculation
        
        **How the Score is Calculated**:
        
        The Reliability score is calculated using **8 WAF controls** across **3 principles**:
        
        1. **Design for failure** (4 controls)
        2. **Manage data quality** (2 controls)
        3. **Design for autoscaling** (2 controls)
        
        **Formula**: `(Controls with "Pass" status / Total 8 controls) × 100`
        
        Each control uses **percentage-based thresholds**:
        - Calculates actual usage percentage
        - Compares against required threshold
        - Status: "Pass" if ≥ threshold, "Fail" if < threshold
        
        **Example**: If 3 out of 8 controls pass → Score = 37.5%
        
        ---
        """)
        
        metric = st.selectbox("Select metric:", [
            "📦 Delta Table Format (R-01-01)",
            "🔄 DLT Usage (R-01-03)",
            "🤖 Model Serving (R-01-05)",
            "⚡ Serverless/Managed (R-01-06)",
            "🗄️ Unity Catalog (R-02-03)",
            "✅ DLT Data Quality (R-02-04)",
            "📈 Auto-Scaling Clusters (R-03-01)",
            "🏭 Auto-Scaling Warehouses (R-03-02)"
        ])
        
        if metric == "📦 Delta Table Format (R-01-01)":
            st.markdown("""
            ### Delta/ICEBERG Format Adoption (R-01-01)
            
            **How Score is Calculated**:
            ```
            Score = (Delta/ICEBERG Tables / Total Tables) × 100
            ```
            
            - Counts all tables in Unity Catalog
            - Identifies tables with DELTA or ICEBERG format
            - Calculates percentage of Delta/ICEBERG tables
            
            **Threshold**: ≥80% of tables must use Delta/ICEBERG
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 80%
            - ❌ **Fail** if score < 80%
            
            ---
            
            **Why This Matters**: 
            - ACID transactions (no partial writes)
            - Schema enforcement
            - Time travel (data recovery)
            - Audit history
            - Concurrent reads/writes
            
            **Actions if Score is Low (<80%)**:
            
            1. **Identify Non-Delta Tables**:
               ```sql
               SELECT table_catalog, table_schema, table_name, data_source_format
               FROM system.information_schema.tables
               WHERE data_source_format NOT IN ('DELTA', 'ICEBERG')
                 AND table_catalog != 'hive_metastore';
               ```
            
            2. **Convert Parquet/CSV to Delta**:
               ```sql
               -- Convert existing Parquet table
               CONVERT TO DELTA parquet.`/path/to/data`;
               
               -- Or recreate as Delta
               CREATE TABLE catalog.schema.new_table 
               USING DELTA AS 
               SELECT * FROM old_table;
               ```
            
            3. **Set Default Format**:
               - Use Delta for all new tables
               - Configure workspace default to Delta
            
            4. **Migration Plan**:
               - Start with high-value production tables
               - Convert during maintenance windows
               - Test queries after conversion
            
            **Goal**: Achieve 80%+ Delta/ICEBERG adoption
            
            📚 [Delta Lake](https://docs.databricks.com/aws/en/delta/index.html) | [Convert to Delta](https://docs.databricks.com/aws/en/delta/convert-to-delta.html)
            """)
        
        elif metric == "🔄 DLT Usage (R-01-03)":
            st.markdown("""
            ### Delta Live Tables Usage (R-01-03)
            
            **How Score is Calculated**:
            ```
            Score = (DLT Compute Usage / Total Compute Usage) × 100
            ```
            
            - Analyzes last 30 days of compute usage
            - Counts compute usage from DLT pipelines
            - Calculates percentage of DLT vs total compute
            
            **Threshold**: ≥30% of compute usage should be DLT
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 30%
            - ❌ **Fail** if score < 30%
            
            ---
            
            **Why This Matters**: 
            - Automatic data quality checks
            - Declarative pipeline definitions
            - Built-in error handling
            - Schema evolution support
            
            **Actions if Score is Low (<30%)**:
            
            1. **Identify ETL Pipelines to Migrate**:
               - Review existing notebooks/workflows
               - Identify data transformation pipelines
               - Prioritize critical data pipelines
            
            2. **Create DLT Pipeline**:
               ```python
               import dlt
               
               @dlt.table(
                   name="cleaned_data",
                   comment="Cleaned customer data"
               )
               def clean_data():
                   return spark.read.table("raw.customers") \\
                       .filter("status = 'active'")
               ```
            
            3. **Add Data Quality Expectations**:
               ```python
               @dlt.table(
                   name="validated_data"
               )
               @dlt.expect("valid_email", "email LIKE '%@%'")
               @dlt.expect_or_drop("no_nulls", "id IS NOT NULL")
               def validated():
                   return spark.read.table("raw.customers")
               ```
            
            4. **Migrate Incrementally**:
               - Start with one pipeline
               - Test thoroughly
               - Gradually migrate more pipelines
            
            **Goal**: Achieve 30%+ DLT compute usage
            
            📚 [Delta Live Tables](https://docs.databricks.com/aws/en/delta-live-tables/index.html) | [DLT Best Practices](https://docs.databricks.com/aws/en/delta-live-tables/best-practices.html)
            """)
        
        elif metric == "🤖 Model Serving (R-01-05)":
            st.markdown("""
            ### Model Serving Usage (R-01-05)
            
            **How Score is Calculated**:
            ```
            Score = (Model Serving Compute / Total ML Compute) × 100
            ```
            
            - Analyzes last 30 days of ML compute usage
            - Counts Model Serving compute usage
            - Calculates percentage of Model Serving vs total ML compute
            
            **Threshold**: ≥20% of ML compute should be Model Serving
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 20%
            - ❌ **Fail** if score < 20%
            
            ---
            
            **Why This Matters**: 
            - Production-grade model serving
            - Auto-scaling for inference
            - High availability
            - Built-in monitoring
            
            **Actions if Score is Low (<20%)**:
            
            1. **Identify Models to Deploy**:
               - Review MLflow registered models
               - Identify models used in production
               - Check for models deployed via other methods
            
            2. **Enable Model Serving**:
               ```python
               import mlflow
               
               # Register model
               mlflow.register_model(
                   model_uri="runs:/<run_id>/model",
                   name="production_model"
               )
               
               # Enable serving via UI or API
               # Databricks → Models → Enable Serving
               ```
            
            3. **Migrate from Custom Serving**:
               - Replace custom inference endpoints
               - Use Databricks Model Serving for consistency
               - Leverage auto-scaling capabilities
            
            4. **Monitor and Optimize**:
               - Track inference latency
               - Monitor costs
               - Optimize model versions
            
            **Goal**: Achieve 20%+ Model Serving usage
            
            📚 [Model Serving](https://docs.databricks.com/aws/en/machine-learning/model-serving/index.html) | [MLflow Models](https://docs.databricks.com/aws/en/machine-learning/mlflow/index.html)
            """)
        
        elif metric == "⚡ Serverless/Managed (R-01-06)":
            st.markdown("""
            ### Serverless/Managed Compute Usage (R-01-06)
            
            **How Score is Calculated**:
            ```
            Score = (Serverless/Managed Compute / Total Compute) × 100
            ```
            
            - Analyzes last 30 days of compute usage
            - Counts serverless or managed compute usage
            - Calculates percentage vs total compute
            
            **Threshold**: ≥50% of compute should be serverless/managed
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 50%
            - ❌ **Fail** if score < 50%
            
            ---
            
            **Why This Matters**: 
            - Zero infrastructure management
            - Automatic scaling
            - Latest runtimes
            - Reduced operational overhead
            
            **Actions if Score is Low (<50%)**:
            
            1. **Enable Serverless SQL Warehouses**:
               - Convert existing SQL warehouses to serverless
               - Create new serverless SQL warehouses
               - Connect BI tools to serverless endpoints
            
            2. **Use Serverless Notebooks**:
               - Enable serverless for interactive notebooks
               - Use for ad-hoc analysis
               - Leverage for data exploration
            
            3. **Migrate Workflows to Serverless**:
               - Update job configurations
               - Use serverless compute for workflows
               - Test and validate performance
            
            4. **Evaluate Managed Services**:
               - Use Databricks-managed services where available
               - Reduce custom cluster management
               - Leverage auto-scaling features
            
            **Goal**: Achieve 50%+ serverless/managed compute
            
            📚 [Serverless Compute](https://docs.databricks.com/aws/en/serverless-compute/index.html) | [SQL Warehouses](https://docs.databricks.com/aws/en/sql/admin/sql-endpoints.html)
            """)
        
        elif metric == "🗄️ Unity Catalog (R-02-03)":
            st.markdown("""
            ### Unity Catalog Metastore (R-02-03)
            
            **How Score is Calculated**:
            ```
            Score = 100% if Unity Catalog metastore exists, else 0%
            ```
            
            - Checks if Unity Catalog metastore is configured
            - Binary check: exists or doesn't exist
            
            **Threshold**: Unity Catalog metastore must exist (100%)
            
            **Current Status**: 
            - ✅ **Pass** if metastore exists
            - ❌ **Fail** if no metastore
            
            ---
            
            **Why This Matters**: 
            - Centralized data governance
            - Fine-grained access control
            - Data lineage tracking
            - Cross-workspace data sharing
            
            **Actions if Score is Low (No Metastore)**:
            
            1. **Enable Unity Catalog**:
               - Contact Databricks admin
               - Configure metastore in account settings
               - Set up initial catalogs and schemas
            
            2. **Migrate from Hive Metastore**:
               ```sql
               -- Migrate tables to Unity Catalog
               CREATE TABLE catalog.schema.table 
               AS SELECT * FROM hive_metastore.old_schema.old_table;
               ```
            
            3. **Configure Access Controls**:
               - Set up groups and users
               - Grant appropriate permissions
               - Implement data governance policies
            
            4. **Update Applications**:
               - Update table references
               - Modify connection strings
               - Test all data access
            
            **Goal**: Unity Catalog must be enabled (100%)
            
            📚 [Unity Catalog](https://docs.databricks.com/aws/en/data-governance/unity-catalog/index.html) | [Migration Guide](https://docs.databricks.com/aws/en/data-governance/unity-catalog/get-started.html)
            """)
        
        elif metric == "✅ DLT Data Quality (R-02-04)":
            st.markdown("""
            ### DLT for Data Quality (R-02-04)
            
            **How Score is Calculated**:
            ```
            Score = (DLT Compute Usage / Total Compute Usage) × 100
            ```
            
            - Same calculation as R-01-03 (DLT Usage)
            - Analyzes last 30 days of compute usage
            - Focuses on DLT usage for data quality
            
            **Threshold**: ≥30% of compute usage should be DLT
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 30%
            - ❌ **Fail** if score < 30%
            
            ---
            
            **Why This Matters**: 
            - Automatic data validation
            - Data quality expectations
            - Schema enforcement
            - Error handling and recovery
            
            **Actions if Score is Low (<30%)**:
            
            1. **Add Data Quality Expectations**:
               ```python
               @dlt.table(name="validated_customers")
               @dlt.expect("valid_email", "email LIKE '%@%.%'")
               @dlt.expect("valid_phone", "phone RLIKE '^[0-9-]+$'")
               @dlt.expect_or_drop("no_nulls", "id IS NOT NULL AND name IS NOT NULL")
               def validate():
                   return spark.read.table("raw.customers")
               ```
            
            2. **Implement Data Quality Checks**:
               - Add expectations to existing DLT pipelines
               - Use expect_or_fail for critical validations
               - Use expect_or_drop for data cleaning
            
            3. **Monitor Data Quality**:
               - Review DLT pipeline quality metrics
               - Set up alerts for quality failures
               - Track data quality trends
            
            4. **Migrate Manual Checks to DLT**:
               - Replace custom validation code
               - Use DLT's built-in quality features
               - Standardize quality checks
            
            **Goal**: Achieve 30%+ DLT usage for data quality
            
            📚 [DLT Data Quality](https://docs.databricks.com/aws/en/delta-live-tables/expectations.html) | [Data Quality Best Practices](https://docs.databricks.com/aws/en/delta-live-tables/best-practices.html)
            """)
        
        elif metric == "📈 Auto-Scaling Clusters (R-03-01)":
            st.markdown("""
            ### Auto-Scaling Clusters (R-03-01)
            
            **How Score is Calculated**:
            ```
            Score = (Clusters with Auto-Scaling / Total Clusters) × 100
            ```
            
            - Counts all clusters in the workspace
            - Identifies clusters with auto-scaling enabled (max_autoscale_workers > 0)
            - Calculates percentage of auto-scaling clusters
            
            **Threshold**: ≥80% of clusters should have auto-scaling enabled
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 80%
            - ❌ **Fail** if score < 80%
            
            ---
            
            **Why This Matters**: 
            - Handles variable workloads
            - Prevents resource exhaustion
            - Optimizes costs
            - Maintains performance under load
            
            **Actions if Score is Low (<80%)**:
            
            1. **Enable Auto-Scaling on Existing Clusters**:
               ```python
               # In cluster configuration
               {
                   "autoscale": {
                       "min_workers": 2,
                       "max_workers": 20
                   }
               }
               ```
            
            2. **Update Cluster Policies**:
               - Modify cluster policies to include auto-scaling
               - Set appropriate min/max workers
               - Apply to all new clusters
            
            3. **Review Fixed-Size Clusters**:
               - Identify clusters with fixed worker count
               - Evaluate if auto-scaling would help
               - Migrate to auto-scaling configuration
            
            4. **Configure Auto-Scaling Rules**:
               - Set min workers based on baseline load
               - Set max workers based on peak requirements
               - Monitor scaling behavior
            
            **Goal**: Achieve 80%+ clusters with auto-scaling
            
            📚 [Auto-Scaling](https://docs.databricks.com/aws/en/clusters/configure.html#autoscaling) | [Cluster Configuration](https://docs.databricks.com/aws/en/clusters/configure.html)
            """)
        
        elif metric == "🏭 Auto-Scaling Warehouses (R-03-02)":
            st.markdown("""
            ### Auto-Scaling SQL Warehouses (R-03-02)
            
            **How Score is Calculated**:
            ```
            Score = (Warehouses with Auto-Scaling / Total Warehouses) × 100
            ```
            
            - Counts all SQL warehouses in the workspace
            - Identifies warehouses with auto-scaling (max_clusters > min_clusters)
            - Calculates percentage of auto-scaling warehouses
            
            **Threshold**: ≥80% of warehouses should have auto-scaling enabled
            
            **Current Status**: 
            - ✅ **Pass** if score ≥ 80%
            - ❌ **Fail** if score < 80%
            
            ---
            
            **Why This Matters**: 
            - Handles concurrent query spikes
            - Optimizes resource utilization
            - Reduces query wait times
            - Cost-effective scaling
            
            **Actions if Score is Low (<80%)**:
            
            1. **Enable Auto-Scaling on Warehouses**:
               - Open SQL warehouse settings
               - Set "Scaling" to "Auto"
               - Configure min and max clusters
            
            2. **Configure Scaling Parameters**:
               - **Min Clusters**: Baseline for steady load
               - **Max Clusters**: Peak capacity for spikes
               - **Scaling Factor**: How aggressively to scale
            
            3. **Review Fixed-Size Warehouses**:
               - Identify single-cluster warehouses
               - Evaluate concurrent query patterns
               - Enable auto-scaling for variable workloads
            
            4. **Monitor Scaling Behavior**:
               - Track cluster scaling events
               - Review query wait times
               - Optimize min/max settings based on usage
            
            **Goal**: Achieve 80%+ warehouses with auto-scaling
            
            📚 [SQL Warehouse Auto-Scaling](https://docs.databricks.com/aws/en/sql/admin/sql-endpoints.html#configure-auto-scaling) | [Warehouse Configuration](https://docs.databricks.com/aws/en/sql/admin/sql-endpoints.html)
            """)

# Main content
st.title("🔍 WAF Assessment Dashboard")
st.markdown("**💡 Use the sidebar (←) to understand each metric and see recommended actions**")
st.markdown("---")

# Embed the dashboard
st.components.v1.iframe(EMBED_URL, height=800, scrolling=True)

st.markdown("---")
st.caption(f"Dashboard ID: {DASHBOARD_ID} | Workspace: {WORKSPACE_ID}")
