import streamlit as st

# Set page config
st.set_page_config(
    page_title="WAF Assessment Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dashboard configuration
INSTANCE_URL = "https://dbc-2a8b378f-7d51.cloud.databricks.com"
DASHBOARD_ID = "01f10231411f1016a33e4fe9dd91c42f"
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
        
        ### Target Scores
        - 🎯 **80%+**: Excellent
        - 🟨 **60-80%**: Good
        - 🟧 **40-60%**: Needs improvement
        - 🔴 **<40%**: Critical gaps
        
        ### Actions
        Select a pillar above to see specific recommendations.
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
        metric = st.selectbox("Select metric:", [
            "📦 Table Formats",
            "🔄 Jobs on All-Purpose Clusters",
            "🖥️ SQL vs All-Purpose",
            "⚡ Serverless Adoption",
            "🎯 Photon Usage",
            "📊 Cluster Utilization",
            "⏱️ Auto-Termination",
            "📈 Auto-Scaling",
            "💵 Spot Instances",
            "🏷️ Cost Tagging",
            "💰 Billing & Chargeback"
        ])
        
        if metric == "📦 Table Formats":
            st.markdown("""
            ### Table Formats
            **What**: Distribution of Delta vs Parquet/CSV
            
            **Why**: Delta = better performance + features
            
            **Benefits of Delta**:
            - ACID transactions
            - Time travel
            - Schema enforcement
            - Faster queries (90% improvement)
            - Automatic compaction
            
            **Actions**:
            ```sql
            -- Convert to Delta
            CONVERT TO DELTA parquet.`/path/to/data`;
            
            -- Or create as Delta
            CREATE TABLE catalog.schema.table 
            USING DELTA AS SELECT * FROM old_table;
            ```
            
            **Goal**: 100% Delta tables
            
            📚 [Delta Best Practices](https://docs.databricks.com/aws/en/delta/best-practices.html)
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
        metric = st.selectbox("Select metric:", [
            "📦 Delta Table Format",
            "🔄 Auto-Scaling for ETL",
            "⏱️ Auto-Recovery",
            "🤖 Model Serving",
            "🎯 Production Readiness"
        ])
        
        if metric == "📦 Delta Table Format":
            st.markdown("""
            ### Delta Format Adoption
            **What**: % of tables using Delta
            
            **Why**: ACID transactions + reliability
            
            **Delta Benefits**:
            - Atomic operations (no partial writes)
            - Schema enforcement
            - Time travel (data recovery)
            - Audit history
            - Concurrent reads/writes
            
            **Reliability Features**:
            ```sql
            -- Rollback bad data
            RESTORE TABLE catalog.schema.table 
            TO TIMESTAMP AS OF '2024-01-01';
            
            -- Audit changes
            DESCRIBE HISTORY catalog.schema.table;
            ```
            
            **Goal**: 100% Delta for production
            
            📚 [Delta Lake](https://docs.databricks.com/aws/en/delta/index.html)
            """)
        
        elif metric == "🔄 Auto-Scaling for ETL":
            st.markdown("""
            ### Auto-Scaling ETL
            **What**: Production pipelines with auto-scale
            
            **Why**: Handles data volume spikes
            
            **Benefits**:
            - Adapts to data volume changes
            - Prevents pipeline failures
            - Maintains SLAs
            - Cost-efficient
            
            **Configuration**:
            ```python
            "autoscale": {
                "min_workers": 2,
                "max_workers": 20
            }
            ```
            
            **Best For**:
            - Variable data volumes
            - Business-critical pipelines
            - Multi-step workflows
            
            📚 [ETL Best Practices](https://docs.databricks.com/aws/en/data-engineering/best-practices)
            """)
        
        elif metric == "⏱️ Auto-Recovery":
            st.markdown("""
            ### Auto-Recovery
            **What**: Jobs with retry + failure handling
            
            **Why**: Resilience to transient failures
            
            **Configuration**:
            ```python
            "max_retries": 3,
            "retry_on_timeout": true,
            "timeout_seconds": 3600
            ```
            
            **Best Practices**:
            1. Enable retries (3-5)
            2. Set timeouts
            3. Use idempotent operations
            4. Add alerts on failure
            5. Log errors for debugging
            
            **Monitoring**:
            - Set up alerts
            - Track failure rates
            - Review error logs
            
            📚 [Job Reliability](https://docs.databricks.com/aws/en/workflows/jobs/index.html)
            """)
        
        elif metric == "🤖 Model Serving":
            st.markdown("""
            ### Model Serving
            **What**: ML models deployed for inference
            
            **Why**: Production-ready ML
            
            **Features**:
            - Auto-scaling
            - High availability
            - Version management
            - A/B testing
            - Monitoring
            
            **Deploy**:
            ```python
            # Using MLflow
            import mlflow
            
            mlflow.register_model(
                model_uri,
                "my_model"
            )
            
            # Enable serving
            # UI: Models → Enable Serving
            ```
            
            **Benefits**:
            - Real-time inference
            - Automatic scaling
            - Built-in monitoring
            
            📚 [Model Serving](https://docs.databricks.com/aws/en/machine-learning/model-serving/index.html)
            """)
        
        else:  # Production Readiness
            st.markdown("""
            ### Production Readiness
            **What**: Production best practices checklist
            
            **Checklist**:
            
            ✅ **Data**:
            - Delta format
            - Schema enforcement
            - Data quality checks
            
            ✅ **Compute**:
            - Jobs clusters (not all-purpose)
            - Auto-scaling enabled
            - Auto-termination set
            
            ✅ **Monitoring**:
            - Alerts configured
            - Logging enabled
            - Dashboards for KPIs
            
            ✅ **Reliability**:
            - Retry logic
            - Error handling
            - Backup/recovery plan
            
            ✅ **Security**:
            - Access controls
            - Secrets management
            - Audit logging
            
            📚 [Production Best Practices](https://docs.databricks.com/aws/en/data-engineering/best-practices)
            """)

# Main content
st.title("🔍 WAF Assessment Dashboard")
st.markdown("**💡 Use the sidebar (←) to understand each metric and see recommended actions**")
st.markdown("---")

# Embed the dashboard
st.components.v1.iframe(EMBED_URL, height=800, scrolling=True)

st.markdown("---")
st.caption(f"Dashboard ID: {DASHBOARD_ID} | Workspace: {WORKSPACE_ID}")
