#!/usr/bin/env python3
"""
Enhance app.py with actual Databricks Solutions from Excel
"""

import json
import re

# Load solutions from Excel
with open('DONOTCHECKIN/databricks_solutions_map.json', 'r') as f:
    solutions_map = json.load(f)

# Map identifiers to app metrics
# This mapping connects WAF identifiers to the metrics shown in the app
identifier_to_metric = {
    # Data & AI Governance
    'DG-01-02': '✅ Active Tables',  # Metadata management
    'DG-01-03': '📊 Table Lineage',  # Data lineage
    'DG-01-04': '🏷️ Table Tagging',  # Metadata descriptions
    'DG-01-05': '✅ Active Tables',  # Data discovery
    'DG-02-01': '🔐 Unsecured Tables',  # Access control
    'DG-02-02': '🔒 Sensitive Tables',  # PII protection
    'DG-02-03': '🔐 Unsecured Tables',  # Access policies
    'DG-03-01': '🚨 Unused Tables',  # Data lifecycle
    
    # Reliability
    'R-01-01': '📦 Delta Table Format',  # ACID transactions
    'R-01-02': '🔄 Auto-Scaling for ETL',  # Resilient compute
    'R-01-03': '⏱️ Auto-Recovery',  # Auto-recovery
    'R-01-04': '🔄 Auto-Scaling for ETL',  # Workflow reliability
    'R-01-05': '🤖 Model Serving',  # ML reliability
    
    # Cost Optimization
    'CO-01-01': '📦 Table Formats',  # Delta format
    'CO-01-02': '🔄 Jobs on All-Purpose Clusters',  # Workflows
    'CO-01-03': '🖥️ SQL vs All-Purpose',  # SQL warehouses
    'CO-01-04': '⚡ Serverless Adoption',  # Serverless
    'CO-01-05': '🎯 Photon Usage',  # Photon
    'CO-02-01': '📊 Cluster Utilization',  # Resource utilization
    'CO-02-02': '⏱️ Auto-Termination',  # Auto-termination
    'CO-02-03': '📈 Auto-Scaling',  # Auto-scaling
    'CO-02-04': '💵 Spot Instances',  # Spot instances
    
    # Performance
    'P-01-01': '⚡ Photon Workloads',  # Photon
    'P-01-02': '📊 Cluster Performance',  # Query optimization
    'P-01-03': '🐍 Python UDFs',  # UDF optimization
    'P-01-04': '🚀 Query Optimization',  # Query tuning
}

print("📊 Enhancing app.py with Excel solutions...")
print("="*70)

# Read current app.py
with open('streamlit-waf-automation/app.py', 'r') as f:
    app_content = f.read()

# Function to enhance a metric with solution
def enhance_metric_with_solution(content, metric_name, identifier):
    if identifier not in solutions_map:
        return content
    
    solution_data = solutions_map[identifier]
    solution_text = solution_data.get('solution', '')
    capabilities = solution_data.get('capabilities', '')
    
    if not solution_text:
        return content
    
    # Find the metric section
    pattern = rf'(elif metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?""")'
    
    # Check if already enhanced
    if f"**{identifier}**" in content and metric_name in content:
        print(f"   ℹ️  {metric_name}: Already has solution, skipping")
        return content
    
    # Find where to insert (after "Actions if Score is Low" section)
    metric_pattern = rf'(elif metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?\*\*Actions if Score is Low[^"]*?)(📚 \[)'
    
    match = re.search(metric_pattern, content, re.DOTALL)
    if match:
        insert_point = match.end(1)
        
        # Format solution text
        solution_formatted = f"""
            
            **📋 Databricks Solution ({identifier}):**
            
            {solution_text.strip()}
            
            """
        
        if capabilities:
            solution_formatted += f"**Capabilities**: {capabilities}\n\n"
        
        # Insert before the link
        new_content = (
            content[:insert_point] +
            solution_formatted +
            content[insert_point:]
        )
        
        return new_content
    
    return content

# Enhance metrics
enhanced_count = 0
for identifier, metric_name in identifier_to_metric.items():
    old_content = app_content
    app_content = enhance_metric_with_solution(app_content, metric_name, identifier)
    if app_content != old_content:
        enhanced_count += 1
        print(f"✅ Enhanced {metric_name} with {identifier}")

# Save enhanced file
with open('streamlit-waf-automation/app.py', 'w') as f:
    f.write(app_content)

print(f"\n{'='*70}")
print(f"✅ Enhanced {enhanced_count} metrics with Excel solutions")
print(f"💡 Note: Some metrics may need manual mapping")
