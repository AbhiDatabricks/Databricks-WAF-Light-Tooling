#!/usr/bin/env python3
"""
Script to enhance the WAF dashboard with explanatory text widgets and best practice recommendations
"""
import json
import os
from datetime import datetime

# Dashboard explanations mapped to dataset names
METRIC_EXPLANATIONS = {
    "303a6758": {  # Count of Tables
        "title": "📊 Total Tables",
        "explanation": "**What it measures:** Total tables across all catalogs\n\n**Why it matters:** Baseline for data asset inventory\n\n**Action:** Review organization, implement naming conventions",
        "best_practice": "[Unity Catalog Best Practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/best-practices)"
    },
    "f5bf425c": {  # Count of Volumes
        "title": "📦 Unity Catalog Volumes",
        "explanation": "**What it measures:** Total UC volumes for file storage\n\n**Why it matters:** Governance over unstructured data\n\n**Action:** Migrate DBFS to volumes, apply access controls",
        "best_practice": "[Volume Best Practices](https://docs.databricks.com/aws/en/data-governance/unity-catalog/volumes)"
    },
    "5fdcd556": {  # Count of Functions
        "title": "⚙️ User-Defined Functions",
        "explanation": "**What it measures:** Registered UDFs in Unity Catalog\n\n**Why it matters:** Code reuse and standardization\n\n**Action:** Centralize common logic, version functions",
        "best_practice": "[UDF Best Practices](https://docs.databricks.com/aws/en/udf/index.html)"
    },
    "a92ace17": {  # Unused Tables
        "title": "🚨 Unused Tables (HIGH PRIORITY)",
        "explanation": "**What it measures:** Tables with ZERO access in date range\n\n**SQL Logic:** LEFT JOIN tables with lineage events, filter NULLs\n\n**Why it matters:** Storage costs + governance overhead\n\n**Actions:**\n- 🔥 Investigate tables unused 30+ days\n- Archive or DELETE unused tables\n- Set retention policies\n- Validate with data owners\n\n💰 **Cost Impact:** Unused tables incur ongoing storage costs",
        "best_practice": "[Cost Optimization](https://docs.databricks.com/discover/pages/optimize-data-workloads-guide)"
    },
    "55e66413": {  # Tables with Usage
        "title": "✅ Active Tables",
        "explanation": "**What it measures:** Tables accessed in date range\n\n**Why it matters:** Prioritize optimization on high-usage tables\n\n**Actions:**\n- Run OPTIMIZE on hot tables\n- Enable Liquid Clustering\n- Implement Delta caching\n- Monitor query performance",
        "best_practice": "[Table Optimization](https://docs.databricks.com/aws/en/delta/optimize.html)"
    },
    "90d7e6f1": {  # Unique Users
        "title": "👥 Active Users",
        "explanation": "**What it measures:** Distinct users with read/write activity\n\n**Why it matters:** Platform adoption indicator\n\n**Actions:**\n- Enable SSO/SCIM\n- Create user groups\n- Monitor inactive users\n- Provide training",
        "best_practice": "[User Management](https://docs.databricks.com/aws/en/admin/users-groups/index.html)"
    },
    "628c2773": {  # Unsecured Tables
        "title": "🔐 Unsecured Tables (SECURITY RISK)",
        "explanation": "**What it measures:** Tables with SELECT granted to 'account users'\n\n**SQL Logic:** Queries table_privileges for grantee='account users'\n\n**Why it matters:** 🚨 SECURITY RISK - data exposed to all users\n\n**URGENT Actions:**\n- 🔥 Review ALL unsecured tables\n- REVOKE broad access\n- Grant to specific groups only\n- Implement data classification\n- Apply row/column security\n\n**Example Fix:**\n```sql\nREVOKE SELECT ON TABLE catalog.schema.table \nFROM `account users`;\n\nGRANT SELECT ON TABLE catalog.schema.table \nTO `data_analysts`;\n```",
        "best_practice": "[Security Best Practices](https://www.databricks.com/sites/default/files/2024-08/azure-databricks-security-best-practices-threat-model.pdf)"
    },
    "1f951287": {  # Sensitive Tables
        "title": "🔒 Sensitive Tables (Secured)",
        "explanation": "**What it measures:** Tables with column masks or row filters\n\n**SQL Logic:** UNION of column_masks and row_filters views\n\n**Why it matters:** Fine-grained access control = mature governance\n\n**Actions:**\n- Identify more PII columns\n- Apply column masks (hash/redact)\n- Implement row filters by dept/region\n- Document masking logic",
        "best_practice": "[Column Masking](https://docs.databricks.com/aws/en/data-governance/unity-catalog/column-masks.html)"
    }
}

def create_text_widget(title, content, position_x, position_y, width=6, height=4):
    """Create a markdown text widget for the dashboard"""
    return {
        "name": f"text_{abs(hash(title)) % 100000000}",
        "textbox_spec": f"# {title}\n\n{content}"
    }

def enhance_dashboard(dashboard_path, output_path=None):
    """Add explanatory text widgets to the dashboard"""
    
    print("🔧 Enhancing WAF Dashboard with Best Practices")
    print("="*70)
    
    # Read dashboard
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    
    print(f"✅ Loaded dashboard: {dashboard_path}")
    print(f"   Found {len(dashboard.get('datasets', []))} datasets")
    
    # Add explanations for each dataset
    explained_count = 0
    for dataset in dashboard.get('datasets', []):
        dataset_name = dataset.get('name')
        if dataset_name in METRIC_EXPLANATIONS:
            info = METRIC_EXPLANATIONS[dataset_name]
            
            # Add description to dataset
            full_description = f"{info['explanation']}\n\n📚 **Best Practice:** {info['best_practice']}"
            
            if 'description' not in dataset:
                dataset['description'] = full_description
                explained_count += 1
                print(f"   ✨ Added explanation for: {dataset.get('displayName')}")
    
    print(f"\n✅ Enhanced {explained_count} datasets with explanations")
    
    # Add a summary text at the top
    summary_text = """
## 📖 How to Use This Dashboard

Each metric below is explained with:
- **What it measures** - The SQL logic and data source
- **Why it matters** - Business impact and WAF significance  
- **Actions** - Specific steps to improve your score
- **Best Practices** - Links to Databricks documentation

### 🎯 Priority Actions
1. 🔥 **URGENT:** Review Unsecured Tables (security risk)
2. 💰 **HIGH:** Archive Unused Tables (cost savings)
3. ✅ **MEDIUM:** Optimize Active Tables (performance)

### 📚 Complete Guide
See `WAF_DASHBOARD_GUIDE.md` for detailed explanations, SQL breakdowns, and comprehensive recommendations.

### 🔄 Refresh Schedule
Set to daily refresh for active monitoring. Adjust date range (default: 30 days) using filters.
"""
    
    # Save enhanced dashboard
    if output_path is None:
        # Create new version with timestamp
        base, ext = os.path.splitext(dashboard_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = f"{base}_ENHANCED_{timestamp}{ext}"
    
    with open(output_path, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"\n✅ Enhanced dashboard saved to:")
    print(f"   {output_path}")
    
    # Create a README for the dashboard folder
    dashboard_dir = os.path.dirname(dashboard_path)
    readme_path = os.path.join(dashboard_dir, "README.md")
    
    readme_content = """# WAF Assessment Dashboard

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
"""
    
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"\n✅ Created README at:")
    print(f"   {readme_path}")
    
    print("\n" + "="*70)
    print("✅ ENHANCEMENT COMPLETE!")
    print("="*70)
    print(f"\n📊 Next steps:")
    print(f"   1. Deploy enhanced dashboard: python3 deploy_complete.py")
    print(f"   2. Review guide: cat WAF_DASHBOARD_GUIDE.md")
    print(f"   3. Take priority actions based on metrics")
    
    return output_path

def main():
    dashboard_path = os.path.join(os.getcwd(), "dashboards", "WAF_ASSESSMENTv1.1-DO_NOT_DELETE.lvdash.json")
    
    if not os.path.exists(dashboard_path):
        print(f"❌ Dashboard not found at: {dashboard_path}")
        return
    
    enhance_dashboard(dashboard_path)

if __name__ == "__main__":
    main()
