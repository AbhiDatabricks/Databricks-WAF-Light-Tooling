# WAF Dashboard - User Guide

## 📖 How to Read This Dashboard

Each metric on the WAF dashboard tells you something important about your Databricks environment. 
This guide explains what each number means and what actions you should take.

---

## 🚨 Unused Tables - Cost Optimization Opportunity

### What This Shows
Tables that haven't been accessed in the selected time period (default: last 30 days).

### How It's Calculated
- Compares all your data tables against access logs
- Finds tables with zero reads or writes in the time window
- Counts tables that appear inactive

### Why This Matters
💰 **Direct Cost Impact**: Each unused table consumes storage that you're paying for
- Managed tables: Charged for cloud storage (S3/ADLS/GCS)
- External tables: Still tracked and managed (compute overhead)

### Actionable Steps
1. **Review the list**: Identify tables unused for 30+ days
2. **Investigate with owners**: Confirm if tables are truly obsolete
3. **Archive cold data**: Move to cheaper storage tiers
4. **Delete obsolete tables**: Use `DROP TABLE` for confirmed unused tables
5. **Set retention policies**: Implement automatic cleanup after N days inactivity

### Best Practices
- **Quarterly cleanup**: Review unused tables every quarter
- **Tagging strategy**: Tag tables with owner and purpose for easier cleanup decisions
- **Monitoring**: Set alerts when table count grows unexpectedly

📚 [Cost Optimization Guide](https://docs.databricks.com/discover/pages/optimize-data-workloads-guide)


---

## 🔐 Unsecured Tables - SECURITY RISK

### What This Shows
Tables accessible to **ALL users** in your Databricks account.

### How It's Calculated
- Checks permission settings for each table
- Identifies tables with SELECT access granted to 'account users'
- These tables have no access restrictions

### Why This Is Critical
🚨 **SECURITY & COMPLIANCE RISK**:
- **Data exposure**: Sensitive data visible to everyone
- **Compliance violations**: May breach GDPR, HIPAA, SOX requirements
- **Audit failures**: Fails least-privilege principle
- **Insider risk**: Increases unauthorized data access potential

### Immediate Actions Required
1. **Audit NOW**: Review every unsecured table immediately
2. **Classify data**: Determine sensitivity level of exposed data
3. **Revoke broad access**: Remove 'account users' permission
4. **Grant to specific groups**: Use role-based access (e.g., `data_analysts`, `finance_team`)
5. **Implement row/column security**: Apply masks and filters for sensitive fields

### Implementation Example
```sql
-- Remove public access
REVOKE SELECT ON TABLE sales.customer_data FROM `account users`;

-- Grant to specific team
GRANT SELECT ON TABLE sales.customer_data TO `sales_analysts`;

-- Apply column masking for PII
ALTER TABLE sales.customer_data 
ALTER COLUMN email SET MASK mask_email_function;
```

### Best Practices
- **Zero public tables**: Goal should be 0 unsecured tables
- **Regular audits**: Review permissions monthly
- **Data classification**: Tag tables by sensitivity (Public/Internal/Confidential/Restricted)
- **Approval workflow**: Require approval for broad grants

📚 [Security Best Practices (PDF)](https://www.databricks.com/sites/default/files/2024-08/azure-databricks-security-best-practices-threat-model.pdf)


---

## 🔒 Sensitive Tables - Protected Data

### What This Shows
Tables with fine-grained access controls applied (column masking or row-level security).

### How It's Calculated
- Counts tables with column masks (data redaction/hashing)
- Plus tables with row filters (restrict which rows users see)
- Indicates mature data governance implementation

### Why This Matters
✅ **Mature Governance Indicator**:
- Shows proper PII protection
- Enables compliance (GDPR "right to be forgotten", HIPAA, CCPA)
- Allows data sharing while protecting sensitive fields
- Reduces over-permissioning risks

### Actionable Steps to Increase This Number
1. **Identify PII columns**: Scan for email, SSN, phone, credit cards, addresses
2. **Apply column masks**:
   - Hash sensitive IDs
   - Redact email domains
   - Mask credit card numbers
   - Partial SSN masking
3. **Implement row filters**:
   - Department-based access (users see only their dept data)
   - Region-based restrictions
   - Time-based access (only current period data)
4. **Test thoroughly**: Verify masks don't break downstream queries
5. **Document policies**: Maintain registry of what's masked and why

### Implementation Patterns

**Column Masking Example**:
```sql
-- Create masking function
CREATE FUNCTION mask_email(email STRING)
RETURN CONCAT(LEFT(email, 3), '***@', SPLIT(email, '@')[1]);

-- Apply to column
ALTER TABLE customers 
ALTER COLUMN email SET MASK mask_email;
```

**Row Filter Example**:
```sql
-- Create filter function
CREATE FUNCTION region_filter(region STRING)
RETURN IF(IS_MEMBER('admin_group'), TRUE, 
          region = current_user_metadata('region'));

-- Apply to table
ALTER TABLE sales 
ADD ROW FILTER region_filter ON (region);
```

### Best Practices
- **Start with highest risk data**: Prioritize customer PII, financial data, health records
- **Use built-in functions**: Databricks provides standard masks (redact, hash, etc.)
- **Test with real users**: Verify business users can still do their jobs
- **Audit access**: Track who accesses masked data
- **Version control**: Document masking rules in code/git

📚 [Column Masking](https://docs.databricks.com/aws/en/data-governance/unity-catalog/column-masks.html) | [Row Filters](https://docs.databricks.com/aws/en/data-governance/unity-catalog/row-filters.html)


---

## ✅ Active Tables - Optimization Targets

### What This Shows
Tables that have been accessed (read or written) in the selected time period.

### How It's Calculated
- Tracks all table access events in the time window
- Includes reads, writes, and queries
- Shows which data assets are actively used

### Why This Matters
🎯 **Optimization Priority List**:
- High-usage tables = biggest performance impact
- Focus optimization efforts where they matter most
- Identify "hot" tables for special treatment

### Actionable Steps
1. **Optimize hot tables**:
   ```sql
   -- Compact small files
   OPTIMIZE catalog.schema.hot_table;
   
   -- Update statistics
   ANALYZE TABLE catalog.schema.hot_table COMPUTE STATISTICS;
   ```

2. **Enable Liquid Clustering** (for tables with multiple query patterns):
   ```sql
   ALTER TABLE catalog.schema.fact_sales 
   CLUSTER BY (region, product_category, date);
   ```

3. **Implement Z-Ordering** (for specific filter columns):
   ```sql
   OPTIMIZE catalog.schema.fact_sales 
   ZORDER BY (customer_id, order_date);
   ```

4. **Enable Delta Caching**:
   - Use compute with caching enabled
   - Benefits tables queried repeatedly
   - Speeds up dashboards and BI tools

5. **Monitor query patterns**:
   - Use Query History to find slow queries
   - Identify missing indexes or poor predicates
   - Optimize join strategies

### Performance Best Practices
- **Partition pruning**: Ensure queries filter on partition columns
- **Column pruning**: SELECT only needed columns (not SELECT *)
- **Predicate pushdown**: Apply filters early in query
- **File sizes**: Target 128MB-1GB per file (use OPTIMIZE)
- **Statistics**: Keep table stats current for query optimizer

### When to Use What
- **OPTIMIZE**: Always - run weekly on active tables
- **Z-ORDER**: Tables with 2-4 high-cardinality filter columns
- **Liquid Clustering**: Tables with diverse query patterns (multiple GROUP BY combinations)
- **Partitioning**: Time-series data, clear partition key, queries always filter on it

📚 [Table Optimization](https://docs.databricks.com/aws/en/delta/optimize.html) | [Liquid Clustering](https://docs.databricks.com/aws/en/delta/clustering.html)


---

## 👥 Active Users - Platform Adoption

### What This Shows
Number of distinct users who accessed data in the time period.

### How It's Calculated
- Counts unique users with table read/write activity
- Tracks actual data access, not just logins
- Indicates platform engagement

### Why This Matters
📊 **Adoption & Governance Indicator**:
- Low number = poor onboarding or access issues
- Growing number = successful rollout
- Helps justify platform investment
- Identifies training needs

### Actionable Steps to Increase Adoption
1. **Remove access barriers**:
   - Enable SSO/SCIM for easy login
   - Simplify permission requests
   - Create self-service data catalogs

2. **Organize users properly**:
   ```sql
   -- Create functional groups
   CREATE GROUP data_analysts;
   CREATE GROUP data_engineers;
   CREATE GROUP business_users;
   
   -- Grant appropriate access
   GRANT SELECT ON CATALOG gold TO `business_users`;
   GRANT ALL PRIVILEGES ON CATALOG dev TO `data_engineers`;
   ```

3. **Improve discoverability**:
   - Add table comments and descriptions
   - Use tags for categorization
   - Maintain data catalog
   - Publish data dictionary

4. **Provide training**:
   - Unity Catalog basics
   - SQL workshop for business users
   - Best practices sessions
   - Office hours for questions

5. **Monitor inactive users**:
   - Identify users who haven't accessed data in 90+ days
   - Follow up or remove access
   - Keep permission lists clean

### Best Practices
- **Just-in-time access**: Grant permissions when needed, not proactively
- **Group-based management**: Manage permissions via groups, not individuals
- **Regular audits**: Review user list quarterly
- **Onboarding checklist**: Standard process for new users
- **Feedback loop**: Survey users about pain points

📚 [User Management](https://docs.databricks.com/aws/en/admin/users-groups/index.html) | [Unity Catalog Identities](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices#manage-identities)


---


## 🎯 Priority Action Matrix

### This Week (Immediate)
1. 🔥 **Review Unsecured Tables** - Security risk, must address NOW
2. 🔥 **Audit who has access to what** - Remove unnecessary permissions
3. 💰 **Identify top 10 largest unused tables** - Quick cost savings

### This Month (High Priority)
4. ✅ Implement row/column security on sensitive tables
5. ✅ Set up automated cleanup policies for unused tables
6. ✅ Optimize top 5 most-queried tables
7. ✅ Create user groups for better permission management

### This Quarter (Strategic)
8. 📊 Achieve 100% classified data (all tables tagged by sensitivity)
9. 📊 Zero unsecured tables (everything has proper access control)
10. 📊 Implement data catalog with full documentation
11. 📊 Set up automated WAF scoring and tracking
12. 📊 Create self-service data access portal for business users

---

## 📞 Need Help?

- **Documentation**: See full guide at `WAF_DASHBOARD_GUIDE.md`
- **Best Practices**: All metrics link to official Databricks documentation
- **Questions**: Contact your Databricks Solution Architect or post in Community Forums

---

**Dashboard Version**: v1.1  
**Last Updated**: February 2026
