# WAF Assessment Dashboard - Comprehensive Guide

## Overview
This dashboard evaluates your Databricks environment against Well-Architected Framework (WAF) principles using System Tables. Each metric is explained below with SQL logic, significance, and actionable recommendations.

---

## 📊 Metrics & Charts Explained

### 1. **Count of Tables**

**SQL Query:**
```sql
SELECT COUNT(*) FROM system.information_schema.tables;
```

**What It Measures:**
- Total number of tables across all catalogs in Unity Catalog

**Why It Matters:**
- Baseline metric for data asset inventory
- High table counts may indicate sprawl or lack of governance

**Best Practice References:**
- [Unity Catalog Best Practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices)
- [Data Modeling Best Practices](https://docs.databricks.com/aws/en/data-engineering/best-practices)

**Actionable Recommendations:**
- ✅ **Review table organization**: Ensure tables are organized in meaningful catalogs and schemas
- ✅ **Implement naming conventions**: Use consistent naming (e.g., `raw_`, `silver_`, `gold_` prefixes)
- ✅ **Audit unused tables**: Use the "Unused Tables" metric to identify cleanup candidates
- ✅ **Document table purposes**: Add table comments and tags for discoverability

---

### 2. **Count of Volumes**

**SQL Query:**
```sql
SELECT COUNT(*) FROM system.information_schema.volumes;
```

**What It Measures:**
- Total Unity Catalog volumes for managing unstructured data

**Why It Matters:**
- Volumes are Unity Catalog's managed file storage
- Proper volume usage ensures governance over file-based data

**Best Practice References:**
- [Unity Catalog Volumes](https://docs.databricks.com/aws/en/data-governance/unity-catalog/volumes)
- [Storage Best Practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices#storage)

**Actionable Recommendations:**
- ✅ **Use volumes over DBFS**: Migrate DBFS usage to Unity Catalog volumes for governance
- ✅ **Apply access controls**: Set volume-level permissions using GRANT statements
- ✅ **Organize by purpose**: Separate volumes for raw data, models, logs, etc.
- ✅ **Monitor volume usage**: Track storage costs and access patterns

---

### 3. **Count of Functions**

**SQL Query:**
```sql
SELECT COUNT(*) FROM system.information_schema.routines;
```

**What It Measures:**
- Total user-defined functions (UDFs) registered in Unity Catalog

**Why It Matters:**
- Functions enable code reuse and standardization
- Well-managed functions reduce duplication and improve maintainability

**Best Practice References:**
- [SQL UDF Best Practices](https://docs.databricks.com/aws/en/udf/index.html)
- [Unity Catalog Functions](https://docs.databricks.com/aws/en/data-governance/unity-catalog/create-functions.html)

**Actionable Recommendations:**
- ✅ **Centralize common logic**: Create shared UDFs for common transformations
- ✅ **Version your functions**: Document function versions and breaking changes
- ✅ **Grant appropriate permissions**: Use `EXECUTE` privileges to control function usage
- ✅ **Monitor function usage**: Track which functions are actively used vs. abandoned

---

### 4. **Count of Unused Tables** 🚨

**SQL Query:**
```sql
SELECT 
  COUNT(DISTINCT CONCAT(ist.table_catalog, '.', ist.table_schema, '.', ist.table_name)) AS full_name_count
FROM 
  system.information_schema.tables ist
  LEFT JOIN 
    (SELECT 
       tl.source_table_catalog,
       tl.source_table_schema,
       tl.source_table_name
     FROM 
       system.access.table_lineage tl
     WHERE 
       tl.event_time BETWEEN :date_range_start AND :date_range_end
       AND tl.source_type IN ('TABLE', 'STREAMING_TABLE')
    ) tl
    ON 
      tl.source_table_catalog = ist.table_catalog 
      AND tl.source_table_schema = ist.table_schema 
      AND tl.source_table_name = ist.table_name
WHERE
  tl.source_table_catalog IS NULL;
```

**What It Measures:**
- Tables with **ZERO access** in the selected date range (default: last 30 days)
- Uses `system.access.table_lineage` to detect read/write activity

**Why It Matters:**
- Unused tables consume storage costs
- Indicate stale data or abandoned projects
- Create governance overhead

**Best Practice References:**
- [Cost Optimization Guide](https://docs.databricks.com/discover/pages/optimize-data-workloads-guide)
- [Table Lifecycle Management](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices#manage-table-lifecycle)

**Actionable Recommendations:**
- 🔥 **HIGH PRIORITY**: Investigate tables unused for 30+ days
- ✅ **Archive or delete**: Move to cold storage or DROP unused tables
- ✅ **Set retention policies**: Implement automatic cleanup after N days of inactivity
- ✅ **Validate with owners**: Confirm with data owners before deletion
- ✅ **Use shallow clones for testing**: Avoid creating abandoned test tables
- 💰 **Cost Impact**: Unused tables on managed storage incur ongoing costs

**Calculation Logic:**
1. Gets all tables from `information_schema.tables`
2. LEFT JOINs with lineage events (reads/writes) in date range
3. Filters to tables with NULL lineage (no activity)
4. Returns distinct count

---

### 5. **Count of Tables with Usage**

**SQL Query:**
```sql
SELECT 
  COUNT(DISTINCT CONCAT(source_table_catalog, '.', source_table_schema, '.', source_table_name)) AS distinct_tables
FROM 
  system.access.table_lineage
WHERE 
  event_time BETWEEN :date_range_start AND :date_range_end
  AND source_table_full_name IS NOT NULL
  AND source_type IN ('TABLE', 'STREAMING_TABLE');
```

**What It Measures:**
- Tables **actively accessed** (read or written) in the date range

**Why It Matters:**
- Indicates active vs. dormant data assets
- Helps prioritize optimization efforts on high-usage tables

**Best Practice References:**
- [Query Optimization](https://docs.databricks.com/aws/en/optimizations/index.html)
- [Table Optimization](https://docs.databricks.com/aws/en/delta/optimize.html)

**Actionable Recommendations:**
- ✅ **Optimize hot tables**: Run `OPTIMIZE` and `ANALYZE TABLE` on frequently accessed tables
- ✅ **Enable Liquid Clustering**: For high-usage tables with multiple query patterns
- ✅ **Monitor query performance**: Use Query History to identify slow queries
- ✅ **Consider Z-ordering**: For tables with specific filter patterns
- ✅ **Implement Delta caching**: Enable caching on compute for repeated reads

---

### 6. **Count of Unique Users with Table Read/Write Events**

**SQL Query:**
```sql
SELECT 
  COUNT(DISTINCT created_by) AS distinct_users

FROM 
  system.access.table_lineage AS tl

WHERE 
  event_time >= :date_range_start
  AND event_time <= :date_range_end
  AND (source_table_full_name IS NOT NULL);
```

**What It Measures:**
- Number of distinct users actively reading/writing data

**Why It Matters:**
- Indicates platform adoption and active user base
- Low numbers may suggest onboarding issues

**Best Practice References:**
- [User Management](https://docs.databricks.com/aws/en/admin/users-groups/index.html)
- [Unity Catalog Identities](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices#manage-identities)

**Actionable Recommendations:**
- ✅ **Enable SSO**: Use SCIM for automated user provisioning
- ✅ **Create user groups**: Organize users by team/function for easier permission management
- ✅ **Implement least privilege**: Grant minimum required permissions
- ✅ **Monitor user activity**: Track inactive users and remove stale accounts
- ✅ **Provide training**: Ensure users understand Unity Catalog and governance

---

### 7. **Count of Unsecured Tables** 🔐

**SQL Query:**
```sql
SELECT 
    COUNT(DISTINCT CONCAT(TABLE_CATALOG, '.', TABLE_SCHEMA, '.', TABLE_NAME)) AS full_name_count
FROM 
    system.information_schema.table_privileges
WHERE 
    grantee = 'account users' 
    AND privilege_type = 'SELECT';
```

**What It Measures:**
- Tables with `SELECT` privileges granted to **'account users'** (all users)
- Indicates tables accessible to everyone in the account

**Why It Matters:**
- 🚨 **SECURITY RISK**: Sensitive data may be exposed to unauthorized users
- Violates principle of least privilege
- May breach compliance requirements (GDPR, HIPAA, etc.)

**Best Practice References:**
- [Unity Catalog Privilege Model](https://docs.databricks.com/aws/en/data-governance/unity-catalog/manage-privileges/index.html)
- [Security Best Practices](https://www.databricks.com/sites/default/files/2024-08/azure-databricks-security-best-practices-threat-model.pdf)
- [Data Classification](https://docs.databricks.com/aws/en/data-governance/unity-catalog/tags.html)

**Actionable Recommendations:**
- 🔥 **HIGH PRIORITY**: Review all unsecured tables immediately
- ✅ **Revoke broad access**: `REVOKE SELECT ON TABLE <table> FROM 'account users'`
- ✅ **Grant to specific groups**: Use groups instead of 'account users'
- ✅ **Implement data classification**: Tag tables by sensitivity level
- ✅ **Use row/column-level security**: Apply row filters and column masks for sensitive data
- ✅ **Audit permissions regularly**: Set up quarterly access reviews
- ✅ **Create governance policies**: Define who should access different data tiers

**Example Fix:**
```sql
-- Revoke broad access
REVOKE SELECT ON TABLE catalog.schema.sensitive_table FROM `account users`;

-- Grant to specific group
GRANT SELECT ON TABLE catalog.schema.sensitive_table TO `data_analysts`;
```

---

### 8. **Count of Sensitive Tables** 🔒

**SQL Query:**
```sql
SELECT COUNT(DISTINCT CONCAT(table_catalog, '.', table_schema, '.', table_name)) AS distinct_table_count
FROM (
    SELECT 
        table_catalog, table_schema, table_name
    FROM 
        system.information_schema.column_masks
    
    UNION
    
    SELECT 
        table_catalog, table_schema, table_name
    FROM 
        system.information_schema.row_filters
);
```

**What It Measures:**
- Tables with **column masking** or **row-level security** applied
- Indicates active use of fine-grained access controls

**Why It Matters:**
- Shows mature governance implementation
- Protects PII and sensitive data
- Enables compliance (GDPR, CCPA, HIPAA)

**Best Practice References:**
- [Column Masking](https://docs.databricks.com/aws/en/data-governance/unity-catalog/column-masks.html)
- [Row Filters](https://docs.databricks.com/aws/en/data-governance/unity-catalog/row-filters.html)
- [Data Privacy](https://docs.databricks.com/aws/en/security/privacy/index.html)

**Actionable Recommendations:**
- ✅ **Identify sensitive columns**: Scan for PII (email, SSN, credit cards)
- ✅ **Apply column masks**: Hash or redact sensitive fields
- ✅ **Implement row filters**: Restrict data access by department/region
- ✅ **Use Delta Sharing with filters**: Share data externally with built-in security
- ✅ **Document masking logic**: Maintain registry of what's masked and why
- ✅ **Test thoroughly**: Verify masks don't break downstream queries

**Example Implementations:**
```sql
-- Column Mask (redact email domains)
CREATE FUNCTION mask_email(email STRING)
RETURN CONCAT(SUBSTRING(email, 1, 3), '***@', SPLIT(email, '@')[1]);

ALTER TABLE users ALTER COLUMN email 
SET MASK mask_email;

-- Row Filter (region-based access)
CREATE FUNCTION region_filter(region STRING)
RETURN IF(IS_MEMBER('admin_group'), TRUE, region = current_user());

ALTER TABLE sales ADD ROW FILTER region_filter ON (region);
```

---

## 📈 WAF Coverage & Completion

### Completion Percentage Across Pillars

**What It Measures:**
- Overall WAF assessment score across pillars:
  - Data & AI Governance
  - Cost Optimization  
  - Performance Efficiency
  - Reliability

**Calculation:**
- Weighted average of passed checks vs. total checks per pillar

**Best Practice References:**
- [Operational Excellence](https://docs.databricks.com/discover/pages/optimize-data-workloads-guide)
- [Well-Architected Framework](https://docs.databricks.com/aws/en/lakehouse-architecture/index.html)

**Actionable Recommendations:**
- ✅ **Target 80%+ overall**: Aim for high WAF compliance
- ✅ **Prioritize by impact**: Focus on high-impact, low-effort improvements
- ✅ **Review quarterly**: Reassess WAF scores every quarter
- ✅ **Track trends**: Monitor if scores improve over time
- ✅ **Share with stakeholders**: Report WAF scores to leadership

---

## 🎯 Priority Action Matrix

### Immediate (This Week)
1. 🔥 Review **Unsecured Tables** - revoke broad access
2. 🔥 Identify **Sensitive Tables** without masking
3. 💰 Analyze **Unused Tables** - archive top 10 largest

### Short-term (This Month)
4. ✅ Implement row/column-level security on sensitive data
5. ✅ Set up table retention policies
6. ✅ Optimize high-usage tables (OPTIMIZE, ZORDER)
7. ✅ Create user groups and proper GRANT structure

### Long-term (This Quarter)
8. 📊 Implement automated WAF scoring
9. 📊 Set up Unity Catalog governance policies
10. 📊 Migrate DBFS to Unity Catalog volumes
11. 📊 Enable Delta Sharing for external collaboration
12. 📊 Implement CI/CD for data pipelines

---

## 📚 Additional Resources

### Databricks Best Practices Hub
- **Unity Catalog**: https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices
- **Data Engineering**: https://docs.databricks.com/aws/en/data-engineering/best-practices
- **CI/CD Workflows**: https://docs.databricks.com/aws/en/dev-tools/ci-cd/best-practices
- **Cost Optimization**: https://docs.databricks.com/discover/pages/optimize-data-workloads-guide
- **Operational Excellence**: https://docs.databricks.com/discover/pages/optimize-data-workloads-guide

### Comprehensive Guides
- **Optimize Data Workloads Guide**: https://www.databricks.com/discover/pages/optimize-data-workloads-guide
- **Security Best Practices (PDF)**: https://www.databricks.com/sites/default/files/2024-08/azure-databricks-security-best-practices-threat-model.pdf

### SQL/BI Specific
- **Databricks SQL Best Practices**: https://docs.google.com/document/d/182PTAryeOIstrBayix6f2OZqObNAiGEqlZdym2Csyjs
- **Power BI Best Practices (PDF)**: https://www.databricks.com/sites/default/files/2025-04/2025-04-power-bi-on-databricks-best-practices-cheat-sheet.pdf

### Field Materials
- **Databricks Best Practices (Slides)**: https://docs.google.com/presentation/d/1KmAmGWtDPbkxx53tfM92pY-507Yx15LB3AAxZD5dG7U

---

## 🔄 Dashboard Refresh Schedule

**Recommended Frequency:**
- **Daily**: For active production environments
- **Weekly**: For stable environments
- **On-demand**: After major changes (migrations, new projects)

**Set up scheduled refresh:**
1. Open dashboard → Settings
2. Configure "Schedule" → Set daily at off-peak hours
3. Add email notifications for completion

---

## 📞 Support & Questions

For questions about specific metrics or recommendations:
- Review linked Databricks documentation
- Consult with your Databricks Solution Architect
- Post in Databricks Community Forums
- Open GitHub issues for tool bugs/enhancements

---

**Last Updated**: February 2026  
**Dashboard Version**: v1.1  
**Maintained By**: Databricks Field Engineering
