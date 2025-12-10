"""
Update catalog and schema references in a Databricks Lakeview dashboard JSON file.
Only update datasets whose displayName starts with "mat_"
This indicates to target datasets that have been materialised.

Single entry point:
    
    from update_dashboard_catalog_schema import update_dashboard_db
    
    update_dashboard_db(
        file_path="/Workspace/dashboards/my_dashboard.lvdash.json",
        new_catalog="prod_catalog",
        new_schema="prod_schema"
    )
"""

import copy
import json
import re
from typing import Optional


def update_dashboard_db(
    file_path: str,
    new_catalog: str,
    new_schema: str,
    old_catalog: Optional[str] = None,
    old_schema: Optional[str] = None,
    verbose: bool = True,
) -> list[str]:
    """
    Update catalog and schema references in a dashboard file (in place).
    
    This is the single entry point. Pass in the file path and new catalog/schema,
    and the file will be updated in place.
    
    Note: Only datasets whose displayName starts with "mat_" will be updated.
    
    Args:
        file_path: Path to the dashboard .lvdash.json file
        new_catalog: The new catalog name to use
        new_schema: The new schema name to use
        old_catalog: (Optional) Only replace this specific catalog.
                     If None, auto-detects from the dashboard.
        old_schema: (Optional) Only replace this specific schema.
                    If None, auto-detects from the dashboard.
        verbose: If True, prints progress information
    
    Returns:
        List of changes made
    
    Example:
        >>> update_dashboard_db(
        ...     "/Workspace/dashboards/my_dashboard.lvdash.json",
        ...     "prod_catalog",
        ...     "prod_schema"
        ... )
    """
    # Load the dashboard
    if verbose:
        print(f"Loading dashboard from: {file_path}")
    
    with open(file_path, "r") as f:
        dashboard = json.load(f)
    
    # Auto-detect old catalog/schema if not provided
    if old_catalog is None or old_schema is None:
        detected = _detect_catalog_schema(dashboard)
        if verbose:
            print(f"Detected catalog.schema: {detected}")
        
        if len(detected) == 1:
            auto_catalog, auto_schema = detected[0]
            old_catalog = old_catalog or auto_catalog
            old_schema = old_schema or auto_schema
            if verbose:
                print(f"Replacing: {old_catalog}.{old_schema} -> {new_catalog}.{new_schema}")
        elif len(detected) > 1 and verbose:
            print("Warning: Multiple catalog.schema found. Specify old_catalog/old_schema to target one.")
    
    # Update the dashboard
    updated_dashboard, changes = _update_dashboard(
        dashboard, new_catalog, new_schema, old_catalog, old_schema
    )
    
    if verbose:
        print(f"\nChanges ({len(changes)}):")
        for c in changes:
            print(f"  - {c}")
    
    # Save back to the same file
    with open(file_path, "w") as f:
        json.dump(updated_dashboard, f, indent=2)
    
    if verbose:
        print(f"\nUpdated: {file_path}")
    
    return changes


# ---- Internal functions below ----

def _detect_catalog_schema(dashboard: dict) -> list[tuple[str, str]]:
    """Detect all catalog.schema combinations in the dashboard."""
    found = set()
    
    for dataset in dashboard.get("datasets", []):
        # From explicit fields
        if "catalog" in dataset and "schema" in dataset:
            found.add((dataset["catalog"], dataset["schema"]))
        
        # From SQL in queryLines
        for line in dataset.get("queryLines", []):
            matches = re.findall(
                r'(?:from|join)\s+(?:`?(\w+)`?\.`?(\w+)`?\.\w+)', 
                line, re.IGNORECASE
            )
            for catalog, schema in matches:
                found.add((catalog, schema))
        
        # From single query field
        if "query" in dataset and isinstance(dataset["query"], str):
            matches = re.findall(
                r'(?:from|join)\s+(?:`?(\w+)`?\.`?(\w+)`?\.\w+)', 
                dataset["query"], re.IGNORECASE
            )
            for catalog, schema in matches:
                found.add((catalog, schema))
    
    return list(found)


def _update_dashboard(
    dashboard: dict,
    new_catalog: str,
    new_schema: str,
    old_catalog: Optional[str],
    old_schema: Optional[str],
) -> tuple[dict, list[str]]:
    """Update catalog and schema references in dashboard dict."""
    dashboard = copy.deepcopy(dashboard)
    changes = []
    
    for dataset in dashboard.get("datasets", []):
        name = dataset.get("displayName", dataset.get("name", "unknown"))
        
        # Only update datasets whose displayName starts with "mat_"
        if not name.startswith("mat_"):
            continue
        
        # Pattern 1: Explicit catalog/schema fields
        if "catalog" in dataset:
            if old_catalog is None or dataset["catalog"] == old_catalog:
                changes.append(f"'{name}': catalog '{dataset['catalog']}' -> '{new_catalog}'")
                dataset["catalog"] = new_catalog
        
        if "schema" in dataset:
            if old_schema is None or dataset["schema"] == old_schema:
                changes.append(f"'{name}': schema '{dataset['schema']}' -> '{new_schema}'")
                dataset["schema"] = new_schema
        
        # Pattern 2: Fully qualified names in queryLines
        if "queryLines" in dataset:
            updated_lines = []
            for line in dataset["queryLines"]:
                updated = _replace_in_sql(line, new_catalog, new_schema, old_catalog, old_schema)
                if updated != line:
                    changes.append(f"'{name}': SQL query updated")
                updated_lines.append(updated)
            dataset["queryLines"] = updated_lines
        
        # Pattern 3: Single 'query' field
        if "query" in dataset and isinstance(dataset["query"], str):
            updated = _replace_in_sql(dataset["query"], new_catalog, new_schema, old_catalog, old_schema)
            if updated != dataset["query"]:
                changes.append(f"'{name}': query updated")
            dataset["query"] = updated
    
    return dashboard, changes


def _replace_in_sql(
    sql: str,
    new_catalog: str,
    new_schema: str,
    old_catalog: Optional[str],
    old_schema: Optional[str],
) -> str:
    """Replace catalog.schema references in SQL text."""
    if old_catalog and old_schema:
        patterns = [
            (rf'\b{re.escape(old_catalog)}\.{re.escape(old_schema)}\.', 
             f'{new_catalog}.{new_schema}.'),
            (rf'`{re.escape(old_catalog)}`\.`{re.escape(old_schema)}`\.', 
             f'`{new_catalog}`.`{new_schema}`.'),
        ]
        for pattern, replacement in patterns:
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
    return sql
