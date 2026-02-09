# WAF-Based Charts Summary

**Date:** February 5, 2026  
**Based on:** Well-Architected Framework Excel (DONOTCHECKIN folder)

---

## 📊 Overview

Added **11 new charts** mapped directly to WAF identifiers from the Excel file, with Databricks Solutions and recommendations integrated.

---

## 🛡️ RELIABILITY (4 Charts)

### R-01-01: Delta Lake Adoption by Schema
**WAF Identifier:** R-01-01  
**Recommendation:** Use a data format that supports ACID transactions  
**Databricks Solution:** Delta Lake  

**What it measures:**
- Delta table adoption rate per schema
- Percentage of tables using Delta format

**Data Source:** `system.information_schema.tables`

**Why it matters:**
- Delta Lake provides ACID transactions, time travel, and data reliability
- Higher adoption = better data quality and reliability

---

### R-01-04: Job Auto-Retry Configuration
**WAF Identifier:** R-01-04  
**Recommendation:** Configure jobs for automatic retries and termination  
**Databricks Solution:** Databricks Workflows  

**What it measures:**
- Jobs with auto-retry enabled vs disabled
- Resilience configuration status

**Data Source:** `system.lakeflow.jobs`

**Why it matters:**
- Auto-retry prevents transient failures from breaking pipelines
- Reduces manual intervention and improves reliability

---

### R-03-01: Cluster Autoscaling Adoption
**WAF Identifier:** R-03-01  
**Recommendation:** Enable autoscaling for ETL workloads  
**Databricks Solution:** Databricks Autoscaling  

**What it measures:**
- Clusters with autoscaling enabled
- Fixed vs dynamic sizing adoption

**Data Source:** `system.compute.clusters`

**Why it matters:**
- Autoscaling prevents resource exhaustion
- Handles variable workloads without manual intervention

---

### R-04-01: Streaming Job Health
**WAF Identifier:** R-04-01  
**Recommendation:** Recover from Structured Streaming query failures  
**Databricks Solution:** Structured Streaming with Checkpointing  

**What it measures:**
- Streaming job success vs failure rate
- Real-time pipeline health

**Data Source:** `system.compute.clusters`

**Why it matters:**
- Streaming failures can cause data loss
- Monitoring helps maintain SLAs for real-time data

---

## ⚡ PERFORMANCE EFFICIENCY (3 Charts)

### PE-01-01: Serverless Adoption Rate
**WAF Identifier:** PE-01-01  
**Recommendation:** Use serverless architecture  
**Databricks Solution:** Databricks Serverless Compute  

**What it measures:**
- Serverless vs traditional cluster usage
- Modern compute adoption

**Data Source:** `system.compute.clusters`

**Why it matters:**
- Serverless provides instant startup (no cold start)
- Better performance for interactive workloads
- Optimal resource utilization

---

### PE-02-05: Native Spark vs UDF Usage
**WAF Identifier:** PE-02-05  
**Recommendation:** Use native Spark operations  
**Databricks Solution:** Apache Spark  

**What it measures:**
- Queries using Python/Scala UDFs (slower)
- Queries using native Spark operations (faster)

**Data Source:** `system.query.history`

**Why it matters:**
- UDFs can be 10-100x slower than native operations
- Native operations leverage Catalyst optimizer
- Direct impact on query performance and cost

---

### PE-02-08: Delta Cache Hit Rate (30 Days)
**WAF Identifier:** PE-02-08  
**Recommendation:** Use caching  
**Databricks Solution:** Delta Cache  

**What it measures:**
- Cache hit rate percentage over time
- Caching effectiveness trend

**Data Source:** `system.query.history`

**Why it matters:**
- Cache hits provide 10-100x faster query response
- Higher hit rate = better user experience
- Reduces compute costs

---

## 💰 COST OPTIMIZATION (4 Charts)

### CO-01-02: Job vs All-Purpose Cluster Costs
**WAF Identifier:** CO-01-02  
**Recommendation:** Use job clusters  
**Databricks Solution:** Databricks Workflows  

**What it measures:**
- Cost comparison: Job clusters vs All-purpose clusters
- Usage patterns and spend distribution

**Data Source:** `system.billing.usage`

**Why it matters:**
- **Job clusters save 30-40% vs all-purpose clusters**
- All-purpose clusters charge even when idle
- Direct cost optimization opportunity

---

### CO-01-06: Serverless vs Traditional Cost
**WAF Identifier:** CO-01-06  
**Recommendation:** Use Serverless for your workloads  
**Databricks Solution:** Databricks Serverless  

**What it measures:**
- Average cost per workload: Serverless vs Traditional
- Cost efficiency comparison

**Data Source:** `system.billing.usage`

**Why it matters:**
- Serverless eliminates idle costs
- Pay only for actual compute time
- Better cost predictability

---

### CO-01-09: Photon Performance & Cost
**WAF Identifier:** CO-01-09  
**Recommendation:** Evaluate performance optimized query engines  
**Databricks Solution:** Photon Engine  

**What it measures:**
- Query duration: Photon vs Standard
- Performance improvement with Photon

**Data Source:** `system.query.history` + `system.billing.usage`

**Why it matters:**
- **Photon provides 3-5x faster queries**
- Same cost, better performance = better ROI
- Reduced time to insights

---

### CO-02-01: Auto-Termination Effectiveness
**WAF Identifier:** CO-02-01  
**Recommendation:** Leverage auto-termination to reduce idle costs  
**Databricks Solution:** Cluster Auto-Termination  

**What it measures:**
- Clusters with auto-termination enabled
- Percentage of idle clusters
- Potential savings from termination

**Data Source:** `system.compute.clusters`

**Why it matters:**
- **Auto-termination saves 20-40% on compute costs**
- Prevents paying for idle resources
- Automatic cost control without manual intervention

---

## 📈 Dashboard Structure

### Pages Enhanced:
1. **Summary** - Clean, only completion percentage
2. **Analytics & Insights** - 7 general analytics charts
3. **Data And AI Governance** - Original metrics
4. **Cost Optimisation** - Original + 4 WAF charts
5. **Performance Efficiency** - Original + 3 WAF charts
6. **Reliability** - Original + 4 WAF charts

---

## 🎯 WAF Mapping

All charts are mapped to official WAF identifiers from the Excel file:

| Pillar | WAF IDs | Count |
|--------|---------|-------|
| Reliability | R-01-01, R-01-04, R-03-01, R-04-01 | 4 |
| Performance | PE-01-01, PE-02-05, PE-02-08 | 3 |
| Cost | CO-01-02, CO-01-06, CO-01-09, CO-02-01 | 4 |
| **Total** | | **11** |

---

## 📚 Databricks Solutions Referenced

Each chart includes the recommended Databricks solution from the WAF Excel:

- **Delta Lake** - ACID transactions, reliability
- **Databricks Workflows** - Job automation, retries
- **Databricks Autoscaling** - Dynamic resource allocation
- **Structured Streaming** - Real-time data processing
- **Databricks Serverless** - Instant startup, no idle costs
- **Apache Spark** - Distributed computing engine
- **Delta Cache** - Query acceleration
- **Photon Engine** - 3-5x query performance

---

## 🔗 Data Sources

All charts use Databricks System Tables:

- `system.information_schema.tables` - Table metadata
- `system.lakeflow.jobs` - Job configurations
- `system.compute.clusters` - Cluster usage
- `system.query.history` - Query performance
- `system.billing.usage` - Cost and usage data

---

## ✅ Benefits

### For Users:
1. **Direct WAF Alignment** - Charts map to specific WAF identifiers
2. **Actionable Insights** - Each chart shows specific areas to improve
3. **Cost Visibility** - Quantified savings opportunities (20-40%)
4. **Performance Metrics** - Measurable improvements (3-5x faster)
5. **Best Practices** - Databricks solution recommendations included

### For Assessment:
1. **Comprehensive Coverage** - 11 new metrics across 3 pillars
2. **Real-Time Data** - All charts use live system tables
3. **Trend Analysis** - Time-based views show progress over time
4. **Prioritization** - Clear impact percentages help prioritize fixes

---

## 🚀 Deployment Status

✅ **Dashboard ID:** 01f10255b09413e1ac5306cc454d51c3  
✅ **Dashboard URL:** https://dbc-2a8b378f-7d51.cloud.databricks.com/sql/dashboardsv3/01f10255b09413e1ac5306cc454d51c3  
✅ **App URL:** https://waf-automation-tool-7474657119815190.aws.databricksapps.com  
✅ **Warehouse:** Configured (43faffa03985771c)  
✅ **Published:** Yes  
✅ **Embedding:** Enabled for *.databricksapps.com  

---

## 📝 Notes

- WAF Excel file location: `DONOTCHECKIN/Well-Architected Framework (WAF) - 22042025.xlsx`
- Charts added to existing pillar pages (not Analytics & Insights tab)
- Summary page kept clean with only completion percentage
- All charts follow WAF recommendations and use Databricks Solutions column
- Queries optimized for performance with appropriate time windows

---

*Generated from WAF Excel file - February 5, 2026*
