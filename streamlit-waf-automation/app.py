import os
import json as _json
import time as _time
import requests
import streamlit as st

# Set page config
st.set_page_config(
    page_title="WAF Assessment Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "waf_page" not in st.session_state:
    st.session_state.waf_page = "dashboard"
# Open recommendations or progress in new tab when URL has ?page=...
try:
    _qp = st.query_params.get("page")
    if _qp == "recommendations":
        st.session_state.waf_page = "recommendations"
    elif _qp == "progress":
        st.session_state.waf_page = "progress"
except Exception:
    pass

# Dashboard configuration — values replaced at install time by install.ipynb
INSTANCE_URL = "https://dbc-7545f99b-d884.cloud.databricks.com"
DASHBOARD_ID = "01f10cbeacfb108dbae8bc34fb686707"
WORKSPACE_ID = "7474648347311915"
EMBED_URL = f"{INSTANCE_URL}/embed/dashboardsv3/{DASHBOARD_ID}?o={WORKSPACE_ID}"

# Reload job config — injected via app.yaml env vars at deploy time
JOB_ID       = os.environ.get("WAF_JOB_ID", "")
WAREHOUSE_ID = os.environ.get("WAF_WAREHOUSE_ID", "")
GENIE_URL    = os.environ.get("WAF_GENIE_URL", "")


def _get_ws_client():
    """Return a WorkspaceClient auto-configured from the runtime environment."""
    try:
        from databricks.sdk import WorkspaceClient
        return WorkspaceClient()
    except Exception:
        return None


def _load_run_info():
    """Return latest successful run info from _run_log, or {} if unavailable."""
    _cat = os.environ.get("WAF_CATALOG", "useast1")
    if not WAREHOUSE_ID:
        return {}
    _wc = _get_ws_client()
    if _wc:
        try:
            from databricks.sdk.service.sql import StatementState
            _stmt = (
                f"SELECT run_id, triggered_at, finished_at, status, "
                f"tables_succeeded, tables_failed "
                f"FROM `{_cat}`.`waf_cache`.`_run_log` "
                f"WHERE status IN ('success','partial') "
                f"ORDER BY run_id DESC LIMIT 1"
            )
            _r = _wc.statement_execution.execute_statement(
                statement=_stmt,
                warehouse_id=WAREHOUSE_ID,
                wait_timeout="10s",
            )
            if (_r.status and _r.status.state == StatementState.SUCCEEDED
                    and _r.result and _r.result.data_array):
                row = _r.result.data_array[0]
                return {
                    "run_id": row[0], "triggered_at": row[1], "finished_at": row[2],
                    "status": row[3], "tables_succeeded": int(row[4] or 0),
                    "tables_failed": int(row[5] or 0), "catalog": _cat,
                }
        except Exception:
            pass
    try:
        with open("/tmp/waf_run_info.json", encoding="utf-8") as _f:
            return _json.load(_f)
    except Exception:
        return {}


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

# --- Run info (needed for catalog/warehouse on both pages) ---
_run_info = _load_run_info()
_catalog = _run_info.get("catalog") or os.environ.get("WAF_CATALOG", "useast1")
_schema = "waf_cache"

# Main content: Dashboard vs Recommendations vs Progress page
if st.session_state.waf_page == "progress":
    st.title("WAF Assessment Progress")
    st.markdown("Total score over time (average across pillars per run).")
    st.markdown("---")
    if st.button("← Back to Dashboard", type="secondary", key="back_progress"):
        st.session_state.waf_page = "dashboard"
        st.rerun()
    if not WAREHOUSE_ID:
        st.warning("No warehouse configured (WAF_WAREHOUSE_ID). Run install and set app env vars.")
    else:
        _wc = _get_ws_client()
        if not _wc:
            st.error("Databricks SDK could not initialise.")
        else:
            try:
                from databricks.sdk.service.sql import StatementState
                _stmt = (
                    f"SELECT r.run_id, r.triggered_at, ROUND(avg_score.overall_score, 2) AS overall_score "
                    f"FROM `{_catalog}`.`{_schema}`.`_run_log` r "
                    f"INNER JOIN ("
                    f"  SELECT _run_id, AVG(completion_percent) AS overall_score "
                    f"  FROM `{_catalog}`.`{_schema}`.waf_total_percentage_across_pillars_hist "
                    f"  GROUP BY _run_id"
                    f") avg_score ON avg_score._run_id = r.run_id "
                    f"WHERE r.status IN ('success', 'partial') "
                    f"ORDER BY r.run_id"
                )
                _r = _wc.statement_execution.execute_statement(
                    statement=_stmt,
                    warehouse_id=WAREHOUSE_ID,
                    wait_timeout="20s",
                )
                if _r.status and _r.status.state == StatementState.SUCCEEDED and _r.result and _r.result.data_array:
                    rows = _r.result.data_array
                    cols = None
                    for _src in (_r.result, _r):
                        if getattr(_src, "manifest", None) and getattr(_src.manifest, "schema", None) and getattr(_src.manifest.schema, "columns", None):
                            cols = [c.name for c in (_src.manifest.schema.columns or [])]
                            break
                    if not cols and rows:
                        cols = ["run_id", "triggered_at", "overall_score"] if len(rows[0]) == 3 else [f"col{i}" for i in range(len(rows[0]))]
                    import pandas as pd
                    labels = []
                    scores = []
                    for row in (rows or []):
                        run_id, triggered_at_val, score = row[0], row[1], row[2]
                        labels.append(triggered_at_val[:19] if triggered_at_val else str(run_id))
                        scores.append(float(score) if score is not None else 0)
                    if rows:
                        _progress_df = pd.DataFrame({"Run time": labels, "Score (%)": scores})
                        _progress_df["Score (%)"] = _progress_df["Score (%)"].astype(float)
                        _n_runs = len(rows)
                        _latest = scores[-1] if scores else 0
                        _p1, _p2, _p3 = st.columns(3)
                        with _p1:
                            st.metric("Runs", _n_runs)
                        with _p2:
                            st.metric("Latest score", f"{_latest:.1f}%")
                        with _p3:
                            st.metric("Trend", f"{(scores[-1] - scores[0]):.1f}%" if len(scores) > 1 else "—", delta="vs first run" if len(scores) > 1 else None, delta_color="off")
                        st.line_chart(_progress_df.set_index("Run time"), y="Score (%)")
                        st.caption("Overall WAF score (average of 4 pillars) per Reload Data run.")
                    else:
                        st.info("No completed runs yet. Run Reload Data to populate history.")
                else:
                    st.info("No run history with scores. Run Reload Data and ensure waf_total_percentage_across_pillars_hist exists.")
            except Exception as e:
                st.error(f"Failed to load progress: {e}")
    st.stop()

if st.session_state.waf_page == "recommendations":
    st.title("📋 WAF Recommendations (Not Met)")
    st.markdown("Controls that did not meet threshold and their recommended actions.")
    st.markdown("---")
    if st.button("← Back to Dashboard", type="secondary"):
        st.session_state.waf_page = "dashboard"
        st.rerun()
    if not WAREHOUSE_ID:
        st.warning("No warehouse configured (WAF_WAREHOUSE_ID). Run install and set app env vars.")
    else:
        _wc = _get_ws_client()
        if not _wc:
            st.error("Databricks SDK could not initialise.")
        else:
            try:
                from databricks.sdk.service.sql import StatementState
                _stmt = f"SELECT waf_id, pillar_name, principle, best_practice, score_percentage, control_threshold_pct, recommendation_if_not_met FROM `{_catalog}`.`{_schema}`.waf_recommendations_not_met ORDER BY pillar_name, waf_id"
                _r = _wc.statement_execution.execute_statement(
                    statement=_stmt,
                    warehouse_id=WAREHOUSE_ID,
                    wait_timeout="30s",
                )
                if _r.status and _r.status.state == StatementState.SUCCEEDED and _r.result and _r.result.data_array:
                    rows = _r.result.data_array
                    # Column names: manifest may be on result or on response; SDK versions vary
                    cols = None
                    for _src in (_r.result, _r):
                        if getattr(_src, "manifest", None) and getattr(_src.manifest, "schema", None) and getattr(_src.manifest.schema, "columns", None):
                            cols = [c.name for c in (_src.manifest.schema.columns or [])]
                            break
                    if not cols and rows:
                        _n = len(rows[0]) if rows else 0
                        _known = ["waf_id", "pillar_name", "principle", "best_practice", "score_percentage", "control_threshold_pct", "recommendation_if_not_met"]
                        cols = _known if _n == len(_known) else [f"col{i}" for i in range(_n)]
                    import pandas as pd
                    _df = pd.DataFrame(rows, columns=cols) if cols else pd.DataFrame(rows)

                    # ---- Beautiful HTML: one card per waf_id with recommendation text ----
                    import html as _html_mod
                    def _html_esc(s):
                        return _html_mod.escape(str(s)) if s is not None else ""
                    def _strip_platform(s):
                        if s is None:
                            return ""
                        return str(s).replace("AWS | Azure | GCP", "").strip()

                    _card_css = """
                    <style>
                    .waf-rec-card { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-left: 4px solid #0ea5e9; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
                    .waf-rec-card .waf-id { font-size: 1.1rem; font-weight: 700; color: #0f172a; margin-bottom: 0.25rem; }
                    .waf-rec-card .waf-meta { font-size: 0.85rem; color: #64748b; margin-bottom: 0.5rem; }
                    .waf-rec-card .waf-rec-label { font-size: 0.75rem; font-weight: 600; color: #0ea5e9; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.75rem; margin-bottom: 0.35rem; }
                    .waf-rec-card .waf-rec-text { font-size: 0.95rem; line-height: 1.55; color: #334155; white-space: pre-wrap; }
                    .waf-rec-score { display: inline-block; background: #e2e8f0; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; margin-left: 0.5rem; }
                    </style>
                    """
                    _html_parts = [_card_css]
                    for _, row in _df.iterrows():
                        waf_id = _html_esc((str(row.get("waf_id", "")).strip() or "—"))
                        pillar = _html_esc(_strip_platform(row.get("pillar_name")) or "—")
                        principle = _html_esc(_strip_platform(row.get("principle")) or "—")
                        best_practice = _html_esc(_strip_platform(row.get("best_practice")) or "—")
                        rec = _html_esc(_strip_platform(row.get("recommendation_if_not_met")) or "(No recommendation)")
                        score = row.get("score_percentage")
                        thresh = row.get("control_threshold_pct")
                        score_str = ""
                        if score is not None or thresh is not None:
                            score_str = f' <span class="waf-rec-score">Score: {score}% / Threshold: {thresh}%</span>' if thresh is not None else f' <span class="waf-rec-score">Score: {score}%</span>'
                        _html_parts.append(
                            f'<div class="waf-rec-card">'
                            f'<div class="waf-id">{waf_id}{score_str}</div>'
                            f'<div class="waf-meta"><strong>Pillar:</strong> {pillar} &nbsp;|&nbsp; <strong>Principle:</strong> {principle}</div>'
                            f'<div class="waf-meta"><strong>Best practice:</strong> {best_practice}</div>'
                            f'<div class="waf-rec-label">Recommendations</div>'
                            f'<div class="waf-rec-text">{rec}</div>'
                            f'</div>'
                        )
                    st.markdown("\n".join(_html_parts), unsafe_allow_html=True)

                    # Export to PDF: one-click download, dynamic filename, pillar/principle/score in body
                    def _pdf_sanitize(s):
                        if not s:
                            return ""
                        s = str(s)
                        replacements = (
                            ("—", "-"), ("–", "-"), ("\"", '"'), ("\"", '"'), ("'", "'"), ("'", "'"),
                            ("…", "..."), ("\u00a0", " "), ("\u2014", "-"), ("\u2013", "-"),
                        )
                        for a, b in replacements:
                            s = s.replace(a, b)
                        return "".join(c for c in s if ord(c) < 256 or c in " \n\t")

                    def _build_recommendations_pdf(pdf_date):
                        from fpdf import FPDF
                        pdf = FPDF()
                        pdf.set_auto_page_break(True, margin=12)
                        pdf.set_margins(14, 12, 14)
                        pdf.add_page()
                        # Title
                        pdf.set_font("Helvetica", "B", 16)
                        pdf.cell(0, 10, _pdf_sanitize("WAF Assessment - Recommendations (Not Met)"), ln=True)
                        pdf.set_font("Helvetica", "", 9)
                        pdf.cell(0, 6, _pdf_sanitize(f"Workspace: {WORKSPACE_ID}  |  Date: {pdf_date}  |  Catalog: {_catalog}.{_schema}"), ln=True)
                        pdf.ln(2)
                        pdf.set_draw_color(200, 200, 200)
                        pdf.line(14, pdf.get_y(), pdf.w - 14, pdf.get_y())
                        pdf.ln(6)
                        for _, row in _df.iterrows():
                            waf_id = _pdf_sanitize(str(row.get("waf_id", "")))
                            pillar = _pdf_sanitize(_strip_platform(row.get("pillar_name", "")))
                            principle = _pdf_sanitize(_strip_platform(row.get("principle", "")))
                            score = row.get("score_percentage")
                            thresh = row.get("control_threshold_pct")
                            score_txt = "N/A"
                            if score is not None and thresh is not None:
                                score_txt = f"{score}% / {thresh}%"
                            elif score is not None:
                                score_txt = f"{score}%"
                            rec = _pdf_sanitize(_strip_platform(row.get("recommendation_if_not_met", "")))[:2000]
                            # Control header
                            pdf.set_font("Helvetica", "B", 11)
                            pdf.set_fill_color(240, 248, 255)
                            pdf.cell(0, 7, f"  {waf_id}", ln=True, fill=True)
                            pdf.set_font("Helvetica", "", 9)
                            pdf.cell(0, 5, _pdf_sanitize(f"Pillar: {pillar}"), ln=True)
                            pdf.cell(0, 5, _pdf_sanitize(f"Principle: {principle}"), ln=True)
                            pdf.cell(0, 5, _pdf_sanitize(f"Current score / Threshold: {score_txt}"), ln=True)
                            pdf.set_font("Helvetica", "B", 9)
                            pdf.cell(0, 5, "Recommendations:", ln=True)
                            pdf.set_font("Helvetica", "", 9)
                            pdf.multi_cell(0, 5, rec or "(No recommendation)")
                            pdf.ln(4)
                        out = pdf.output()
                        return bytes(out) if not isinstance(out, bytes) else out

                    from datetime import datetime as _dt
                    _pdf_date = _dt.utcnow().strftime("%Y-%m-%d")
                    _pdf_bytes = _build_recommendations_pdf(_pdf_date)
                    _pdf_filename = f"WAF_ASSESSMENT_Recommendation_{WORKSPACE_ID}_{_pdf_date}.pdf"
                    st.download_button("Export to PDF", data=_pdf_bytes, file_name=_pdf_filename, mime="application/pdf", type="primary", use_container_width=False, key="pdf_export")
                else:
                    st.info("No rows returned. Run Reload Data and ensure the view `waf_recommendations_not_met` exists.")
            except Exception as e:
                st.error(f"Failed to load recommendations: {e}")
    st.stop()

# Dashboard page
st.title("🔍 WAF Assessment Dashboard")
st.markdown("**💡 Use the sidebar (←) to understand each metric and see recommended actions**")
st.markdown("---")

# Read-only display of catalog, schema, and latest run
_info_col1, _info_col2, _info_col3, _info_col4 = st.columns(4)
with _info_col1:
    st.metric("Data Catalog", _catalog)
with _info_col2:
    st.metric("Schema", _schema)
with _info_col3:
    if _run_info:
        _ts = _run_info.get("triggered_at", "—")
        st.metric("Last Reload", _ts[:16] if _ts else "—")  # trim seconds
    else:
        st.metric("Last Reload", "No data yet")
with _info_col4:
    if _run_info:
        _rid  = _run_info.get("run_id", "—")
        _ok   = _run_info.get("tables_succeeded", 0)
        _fail = _run_info.get("tables_failed", 0)
        _icon = "✅" if _run_info.get("status") == "success" else "⚠️"
        st.metric("Run", f"{_icon} #{_rid}", delta=f"{_ok}/{_ok+_fail} tables", delta_color="off")
    else:
        st.metric("Run", "—")

st.markdown("---")

# Reload Data button — triggers a Databricks Job via SDK (handles Apps OAuth M2M)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Reload Data", use_container_width=True, type="primary"):
        _catalog = os.environ.get("WAF_CATALOG", "useast1")

        if not JOB_ID:
            st.error("❌ Reload job not configured (WAF_JOB_ID missing). Re-run install.ipynb.")
        else:
            _wc = _get_ws_client()
            if not _wc:
                st.error("❌ Databricks SDK could not initialise. Check app configuration.")
            else:
                try:
                    _resp    = _wc.jobs.run_now(
                        job_id=int(JOB_ID),
                        notebook_params={"catalog": _catalog},
                    )
                    _run_id  = _resp.run_id
                    _run_url = f"{INSTANCE_URL}/?o={WORKSPACE_ID}#job/{JOB_ID}/run/{_run_id}"
                    _status_ph = st.empty()

                    # Poll until terminal state (up to 5 min)
                    _final_state = None
                    for _attempt in range(60):
                        _time.sleep(5)
                        _run     = _wc.jobs.runs.get(run_id=_run_id)
                        _lc      = _run.state.life_cycle_state.value if (
                            _run.state and _run.state.life_cycle_state) else ""
                        _status_ph.info(
                            f"⏳ Reload running ({(_attempt+1)*5}s elapsed) — "
                            f"[View job run ↗]({_run_url})"
                        )
                        if _lc == "TERMINATED":
                            _final_state = _run.state.result_state.value if (
                                _run.state and _run.state.result_state) else "UNKNOWN"
                            break

                    _status_ph.empty()
                    if _final_state == "SUCCESS":
                        st.success(f"✅ Reload complete — [View job run ↗]({_run_url})")
                    elif _final_state is None:
                        st.warning(f"⏳ Reload still running — [Check status ↗]({_run_url})")
                    else:
                        st.error(f"❌ Reload failed ({_final_state}) — [View job run ↗]({_run_url})")
                except Exception as _exc:
                    st.error(f"❌ Failed to trigger reload: {_exc}")

                st.rerun()

st.markdown("---")

# View Recommendations + View Progress (open in new tab)
_rec_col1, _rec_col2, _rec_col3, _rec_col4 = st.columns([1, 2, 2, 1])
_link_style = (
    'display:inline-block;width:100%;padding:0.5rem 1rem;border-radius:0.5rem;'
    'background-color:#f0f2f6;color:#31333f;text-align:center;text-decoration:none;'
    'font-weight:500;border:1px solid rgba(49,51,63,0.2);box-sizing:border-box;'
)
with _rec_col2:
    st.markdown(
        f'<a href="?page=recommendations" target="_blank" rel="noopener noreferrer" style="{_link_style}">'
        '📋 View Recommendations (Not Met)</a>',
        unsafe_allow_html=True,
    )
with _rec_col3:
    st.markdown(
        f'<a href="?page=progress" target="_blank" rel="noopener noreferrer" style="{_link_style}">'
        '📈 View Progress</a>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# Dashboard access — Open Dashboard + Ask Genie (always show both; Genie URL from install)
_dashboard_direct_url = f"{INSTANCE_URL}/sql/dashboardsv3/{DASHBOARD_ID}"
_genie_url = GENIE_URL or f"{INSTANCE_URL}/genie"  # fallback to Genie home if not set by install
_btn_col1, _btn_col2, _btn_col3, _btn_col4 = st.columns([1, 2, 2, 1])
with _btn_col2:
    st.link_button(
        "↗ Open Dashboard in Databricks",
        _dashboard_direct_url,
        use_container_width=True,
    )
with _btn_col3:
    st.link_button(
        "🧞 Ask Genie",
        _genie_url,
        use_container_width=True,
    )
if not GENIE_URL:
    st.caption("💡 **Ask Genie**: Re-run install to link the WAF Genie room; the button above opens Genie.")

st.info(
    "**First time?** The dashboard below may show a Databricks login screen inside the iframe. "
    "Just click **Continue** — it will use your existing Databricks SSO session and sign you in "
    "automatically (no password needed). This is a one-time step per browser session. "
    "If you prefer, use the button above to open the dashboard directly in Databricks.",
    icon="ℹ️",
)

# Embed the dashboard using raw iframe (Databricks recommended format)
st.components.v1.html(
    f'<iframe src="{EMBED_URL}" width="100%" height="800" frameborder="0"></iframe>',
    height=810,
    scrolling=True,
)

st.markdown("---")
st.caption(f"Dashboard ID: {DASHBOARD_ID} | Workspace: {WORKSPACE_ID}")
