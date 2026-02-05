# WAF Assessment Dashboard

## Dashboard Files

- **WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json** - Original dashboard
- **WAF_ASSESSMENTv1.1-DO_NOT_DELETE_ENHANCED_*.lvdash.json** - Enhanced with explanations

## Documentation

See `../WAF_DASHBOARD_GUIDE.md` for:
- Detailed explanation of each metric
- SQL query breakdowns
- Best practice references
- Actionable recommendations
- Priority action matrix

## Deployment

Use `../deploy_complete.py` to automatically deploy with:
- Dashboard publishing
- Warehouse selection
- Embedding configuration
- Databricks App creation

## Metrics Included

### Governance
- Total Tables, Volumes, Functions
- Unsecured Tables 🔐
- Sensitive Tables (with masks/filters) 🔒

### Cost Optimization
- Unused Tables 💰
- Active Tables
- Storage utilization

### Security
- Active Users
- Permission audits
- Data classification

## Best Practice Links

- [Unity Catalog Best Practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices)
- [Cost Optimization Guide](https://docs.databricks.com/discover/pages/optimize-data-workloads-guide)
- [Security Best Practices](https://www.databricks.com/sites/default/files/2024-08/azure-databricks-security-best-practices-threat-model.pdf)
