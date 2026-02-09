#!/usr/bin/env python3
"""
Add Databricks Solutions from Excel to app.py metrics
"""

import json
import re

# Load solutions
with open('DONOTCHECKIN/databricks_solutions_map.json', 'r') as f:
    solutions = json.load(f)

# Map metrics to identifiers (based on best practice matching)
metric_to_identifiers = {
    '🚨 Unused Tables': ['DG-03-01'],  # Data lifecycle
    '🔐 Unsecured Tables': ['DG-02-01', 'DG-02-03'],  # Access control
    '🔒 Sensitive Tables': ['DG-02-02'],  # PII protection
    '✅ Active Tables': ['DG-01-02', 'DG-01-05'],  # Metadata management, discovery
    '👥 Active Users': ['DG-02-01'],  # Access control
    '📊 Table Lineage': ['DG-01-03'],  # Lineage tracking
    '🏷️ Table Tagging': ['DG-01-04'],  # Metadata descriptions
    '📦 Table Formats': ['CO-01-01', 'R-01-01'],  # Delta format
    '🔄 Jobs on All-Purpose Clusters': ['CO-01-02'],  # Workflows
    '🖥️ SQL vs All-Purpose': ['CO-01-03'],  # SQL warehouses
    '⚡ Serverless Adoption': ['CO-01-04'],  # Serverless
    '🎯 Photon Usage': ['CO-01-05', 'P-01-01'],  # Photon
    '📊 Cluster Utilization': ['CO-02-01'],  # Resource utilization
    '⏱️ Auto-Termination': ['CO-02-02'],  # Auto-termination
    '📈 Auto-Scaling': ['CO-02-03'],  # Auto-scaling
    '💵 Spot Instances': ['CO-02-04'],  # Spot instances
    '⚡ Photon Workloads': ['P-01-01'],  # Photon
    '📊 Cluster Performance': ['P-01-02'],  # Query optimization
    '🐍 Python UDFs': ['P-01-03'],  # UDF optimization
    '🚀 Query Optimization': ['P-01-04'],  # Query tuning
    '📦 Delta Table Format': ['R-01-01'],  # Delta format (Reliability)
    '🔄 Auto-Scaling for ETL': ['R-01-02', 'R-01-04'],  # Resilient compute
    '⏱️ Auto-Recovery': ['R-01-03'],  # Auto-recovery
    '🤖 Model Serving': ['R-01-05'],  # ML reliability
}

print("📊 Adding Databricks Solutions to app.py...")
print("="*70)

# Read app.py
with open('streamlit-waf-automation/app.py', 'r') as f:
    content = f.read()

# Function to add solution to a metric
def add_solution_to_metric(content, metric_name, identifiers):
    # Find the metric section - try multiple patterns
    patterns = [
        rf'(elif metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?)(📚 \[)',
        rf'(if metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?)(📚 \[)',
        rf'(elif metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?)(\*\*Expected Impact)',
        rf'(if metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?)(\*\*Expected Impact)',
        rf'(elif metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?)(\*\*Goal)',
        rf'(if metric == "{re.escape(metric_name)}":\s+st\.markdown\("""[^"]*?)(\*\*Goal)',
    ]
    
    match = None
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            break
    
    if not match:
        print(f"   ⚠️  {metric_name}: Section not found")
        return content
    
    # Check if solution already added
    if f"**📋 Databricks Solution" in match.group(1):
        print(f"   ℹ️  {metric_name}: Solution already added")
        return content
    
    # Get solution text from first matching identifier
    solution_text = ""
    solution_ident = ""
    for ident in identifiers:
        if ident in solutions:
            sol = solutions[ident]
            solution_text = sol.get('solution', '').strip()
            solution_ident = ident
            capabilities = sol.get('capabilities', '').strip()
            if solution_text:
                break
    
    if not solution_text:
        print(f"   ⚠️  {metric_name}: No solution found for {identifiers}")
        return content
    
    # Format solution
    solution_section = f"""
            
            **📋 Databricks Solution ({solution_ident}):**
            
            {solution_text}
            """
    
    if capabilities:
        solution_section += f"\n**Capabilities**: {capabilities}\n"
    
    # Insert before the matched pattern (link, Expected Impact, or Goal)
    insert_point = match.end(1)
    
    # Add a newline before if needed
    if not content[insert_point-2:insert_point].strip():
        solution_section = "\n" + solution_section.lstrip()
    
    new_content = content[:insert_point] + solution_section + content[insert_point:]
    
    print(f"   ✅ {metric_name}: Added solution from {solution_ident}")
    return new_content

# Add solutions to all metrics
enhanced = 0
for metric_name, identifiers in metric_to_identifiers.items():
    old_content = content
    content = add_solution_to_metric(content, metric_name, identifiers)
    if content != old_content:
        enhanced += 1

# Save
with open('streamlit-waf-automation/app.py', 'w') as f:
    f.write(content)

print(f"\n{'='*70}")
print(f"✅ Enhanced {enhanced} metrics with Databricks Solutions")
print(f"🚀 Ready to deploy!")
