# Missing WAF Identifier Charts - Added to Dashboard

**Date:** February 5, 2026  
**Compliance:** All charts map to MISSING WAF identifiers from Excel  
**Data Source:** System Tables (real data, not Excel status)

---

## ✅ **Charts Added: 12 New Charts for Reliability**

### **Principle 1: Design for Failure**

#### R-01-02: Spark/Photon Workload Distribution
**WAF Identifier:** R-01-02  
**Practice:** Use a resilient distributed data engine for all workloads  
**Databricks Solution:** Apache Spark; Photon  
**System Table:** `system.compute.clusters`  
**Chart Type:** Pie Chart  
**Measures:** Percentage of workloads using Photon vs Standard Spark  
**Why:** Photon provides better resilience and performance

---

#### R-01-03: Delta Live Tables Pipeline Health
**WAF Identifier:** R-01-03  
**Practice:** Automatically rescue invalid or nonconforming data  
**Databricks Solution:** Delta Live Tables  
**System Table:** `system.lakeflow.pipeline_update_timeline`  
**Chart Type:** Bar Chart  
**Measures:** Pipeline success rate, failed updates  
**Why:** DLT automatically handles data quality issues

---

#### R-01-06: Serverless vs Managed Compute Usage
**WAF Identifier:** R-01-06  
**Practice:** Use managed services for your workloads  
**Databricks Solution:** Databricks Platform  
**System Table:** `system.compute.clusters`  
**Chart Type:** Pie Chart  
**Measures:** Adoption of managed services (Serverless, Job clusters)  
**Why:** Managed services reduce operational overhead

---

### **Principle 2: Data Integrity**

#### R-02-01: Table Distribution by Layer (Bronze/Silver/Gold)
**WAF Identifier:** R-02-01  
**Practice:** Use a layered storage architecture  
**Databricks Solution:** Databricks Lakehouse Architecture  
**System Table:** `system.information_schema.tables`  
**Chart Type:** Pie Chart  
**Measures:** Tables distributed across Bronze/Silver/Gold layers  
**Why:** Layered architecture improves data quality as it moves up

---

#### R-02-02: Table Duplication Analysis
**WAF Identifier:** R-02-02  
**Practice:** Improve data integrity by reducing data redundancy  
**Databricks Solution:** Databricks Platform  
**System Table:** `system.information_schema.tables`  
**Chart Type:** Bar Chart  
**Measures:** Tables with same name across multiple schemas (redundancy)  
**Why:** Reduces data inconsistency and storage costs

---

#### R-02-03: Schema Management - Tables per Schema
**WAF Identifier:** R-02-03  
**Practice:** Actively manage schemas  
**Databricks Solution:** Unity Catalog  
**System Table:** `system.information_schema.tables`  
**Chart Type:** Bar Chart  
**Measures:** Table count per schema, schema organization  
**Why:** Active schema management prevents data chaos

---

#### R-02-04: Data Quality Check Results
**WAF Identifier:** R-02-04  
**Practice:** Use constraints and data expectations  
**Databricks Solution:** Delta Live Tables  
**System Table:** `system.data_quality_monitoring.table_results`  
**Chart Type:** Bar Chart  
**Measures:** Failed data quality checks by table  
**Why:** Constraints ensure data integrity

---

#### R-02-05: MLflow Experiment Activity
**WAF Identifier:** R-02-05  
**Practice:** Take a data-centric approach to machine learning  
**Databricks Solution:** Databricks Platform  
**System Table:** `system.mlflow.experiments_latest`  
**Chart Type:** Line Chart  
**Measures:** ML experiment count over time  
**Why:** Data-centric ML improves model reliability

---

### **Principle 4: Recovery**

#### R-04-02: Delta Table Versions (Time Travel Capability)
**WAF Identifier:** R-04-02  
**Practice:** Recover ETL jobs using data time travel capabilities  
**Databricks Solution:** Delta Lake - Delta Time Travel  
**System Table:** `system.information_schema.tables`  
**Chart Type:** Bar Chart  
**Measures:** Delta table adoption by schema (enables time travel)  
**Why:** Time travel allows recovery from bad ETL runs

---

#### R-04-03: Job Run Success Rate with Auto-Recovery
**WAF Identifier:** R-04-03  
**Practice:** Leverage a job automation framework with built-in recovery  
**Databricks Solution:** Databricks Workflows  
**System Table:** `system.lakeflow.job_run_timeline`  
**Chart Type:** Line Chart  
**Measures:** Daily job success rate trend  
**Why:** Auto-recovery reduces manual intervention

---

### **Principle 5: Monitoring**

#### R-05-01: Data Platform Event Monitoring
**WAF Identifier:** R-05-01  
**Practice:** Monitor data platform events  
**Databricks Solution:** System Tables / Audit Logs  
**System Table:** `system.access.audit`  
**Chart Type:** Bar Chart  
**Measures:** Event counts by type (table operations, jobs)  
**Why:** Monitoring enables proactive issue detection

---

#### R-05-02: Cloud Resource Usage Monitoring
**WAF Identifier:** R-05-02  
**Practice:** Monitor cloud events  
**Databricks Solution:** System Tables / Cloud Integration  
**System Table:** `system.billing.usage`  
**Chart Type:** Line Chart  
**Measures:** Daily resource usage trends  
**Why:** Cloud monitoring ensures cost control and capacity planning

---

## 📊 **Summary**

| Category | Charts Added | Status |
|----------|-------------|--------|
| **Reliability** | 12 charts | ✅ Added |
| **Performance Efficiency** | 0 charts | ⏳ Pending |
| **Cost Optimization** | 0 charts | ⏳ Pending |
| **Governance** | 0 charts | ⏳ Pending |
| **Security** | 0 charts | ⏳ Pending |
| **Total** | **12 charts** | |

---

## 🎯 **Key Features**

✅ **100% Compliance** - All charts map to missing WAF identifiers  
✅ **Real Data** - All use system tables (not Excel status)  
✅ **Measurable** - Actual metrics, not subjective status  
✅ **Actionable** - Shows what needs improvement  
✅ **Automated** - No manual data entry required  

---

## 📈 **Impact**

### Before:
- **Reliability Coverage:** 4 identifiers (R-01-01, R-01-04, R-03-01, R-04-01)
- **Missing:** 13 identifiers

### After:
- **Reliability Coverage:** 16 identifiers (added 12 new)
- **Missing:** 1 identifier (R-04-04 - Disaster Recovery - no system table data)

---

## 🔄 **Next Steps**

1. ✅ **Reliability:** 12 charts added (92% coverage)
2. ⏳ **Performance Efficiency:** Analyze missing identifiers
3. ⏳ **Cost Optimization:** Analyze missing identifiers
4. ⏳ **Governance:** Analyze missing identifiers
5. ⏳ **Security:** Analyze missing identifiers

---

## 📚 **References**

- WAF Excel: `DONOTCHECKIN/Well-Architected Framework (WAF) - 22042025.xlsx`
- System Tables Docs: https://docs.databricks.com/aws/en/admin/system-tables/
- Chart Definitions: `DONOTCHECKIN/missing_identifier_charts.json`

---

*Generated: February 5, 2026*
