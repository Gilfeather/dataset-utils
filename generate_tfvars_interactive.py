#!/usr/bin/env python3
"""
Interactive utility to generate terraform.tfvars files for BigQuery dataset configuration.
"""

import sys
from typing import List, Dict, Any, Optional


def get_input(prompt: str, required: bool = True, default: Optional[str] = None) -> str:
    """Get user input with optional default value."""
    if default:
        prompt = f"{prompt} (default: {default}): "
    else:
        prompt = f"{prompt}: "
    
    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return ""
        else:
            print("This field is required. Please enter a value.")


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} ({default_str}): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        elif not response:
            return default
        else:
            print("Please enter 'y' or 'n'.")


def collect_global_filter_values() -> Dict[str, List[str]]:
    """Collect global filter values that will be applied across tables."""
    filter_values = {}
    
    print("\n=== Global Filter Values ===")
    print("These values will be used for filtering across all applicable tables.")
    print("You can specify multiple values separated by commas.")
    print("Leave empty if not needed.\n")
    
    # Define predefined filter columns
    filter_columns = {
        "account_name": "Account name filter",
        "client_id": "Client ID filter", 
        "user_id": "User ID filter",
        "status": "Status filter (e.g., 'active', 'completed')",
        "region": "Region filter"
    }
    
    for column, description in filter_columns.items():
        value = get_input(f"{column} ({description}) - comma separated for multiple", required=False)
        if value:
            # Split by comma and strip whitespace
            values = [v.strip() for v in value.split(',') if v.strip()]
            filter_values[column] = values
    
    return filter_values


def get_table_filter_columns(table_name: str, global_filters: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Generate filter columns for a table based on predefined mappings."""
    
    # Predefined table-to-filter mappings (sample)
    table_filters = {
        "users": ["account_name", "user_id", "status"],
        "transactions": ["client_id", "status", "region"],
        "events": ["account_name", "user_id"],
        "orders": ["client_id", "status"],
        "logs": ["account_name", "region"]
    }
    
    filter_columns = []
    applicable_filters = table_filters.get(table_name, [])
    
    for column_name in applicable_filters:
        if column_name in global_filters and global_filters[column_name]:
            values = global_filters[column_name]
            if len(values) == 1:
                condition = f"= '{values[0]}'"
            else:
                # Multiple values - use IN clause
                formatted_values = "', '".join(values)
                condition = f"IN ('{formatted_values}')"
            
            filter_columns.append({
                "column_name": column_name,
                "condition": condition,
                "operator": "AND"
            })
    
    return filter_columns


def collect_table_info(global_filters: Dict[str, List[str]]) -> Dict[str, Any]:
    """Collect information for a single table."""
    table_info = {}
    
    print("\n--- Table Configuration ---")
    table_info['source_table_id'] = get_input("Source table ID")
    table_info['view_name'] = get_input("View name", default=table_info['source_table_id'])
    table_info['description'] = get_input("Description", required=False)
    
    # Generate filter columns based on table name and global filters
    filter_columns = get_table_filter_columns(table_info['source_table_id'], global_filters)
    
    if filter_columns:
        print(f"\nApplied filters for '{table_info['source_table_id']}':")
        for filter_col in filter_columns:
            print(f"  - {filter_col['column_name']} {filter_col['condition']}")
    else:
        print(f"\nNo applicable filters for '{table_info['source_table_id']}'")
    
    table_info['filter_columns'] = filter_columns
    table_info['additional_where'] = get_input("Additional WHERE clause", required=False)
    
    return table_info


def generate_source_datasets_config(global_filters: Dict[str, List[str]], client_key: str) -> Dict[str, Any]:
    """Generate source datasets configuration from predefined structure."""
    
    # Predefined source datasets and tables structure
    predefined_structure = {
        "raw_lake": {
            "description": "Raw data lake",
            "tables": ["users", "transactions", "events", "orders", "logs"]
        },
        "analytics_raw": {
            "description": "Raw analytics data",
            "tables": ["user_behavior", "conversion_events", "page_tracking"]
        },
        "transaction_raw": {
            "description": "Raw transaction data",
            "tables": ["payments", "refunds", "invoices"]
        }
    }
    
    source_datasets_config = {}
    
    for dataset_name, config in predefined_structure.items():
        dataset_config = {
            "target_dataset_key": client_key,
            "description": config["description"],
            "tables": {}
        }
        
        # Generate tables for this dataset
        for table_name in config["tables"]:
            filter_columns = get_table_filter_columns(table_name, global_filters)
            
            dataset_config["tables"][table_name] = {
                "source_table_id": table_name,
                "view_name": table_name,
                "filter_columns": filter_columns,
                "additional_where": "",
                "description": f"{table_name} filtered view"
            }
        
        source_datasets_config[dataset_name] = dataset_config
    
    return source_datasets_config


def generate_tfvars_content(config: Dict[str, Any]) -> str:
    """Generate terraform.tfvars content from configuration."""
    lines = [
        "# GCP Configuration",
        f'project_id = "{config["project_id"]}"',
        f'region     = "{config.get("region", "asia-northeast1")}"',
        "",
        "# View Configuration", 
        f'view_prefix = "{config.get("view_prefix", "filtered_")}"',
        "",
        "# Output Datasets Configuration",
        "output_datasets_config = {"
    ]
    
    # Output datasets
    for key, dataset in config["output_datasets_config"].items():
        lines.extend([
            f'  "{key}" = {{',
            f'    dataset_id  = "{dataset["dataset_id"]}"',
            f'    description = "{dataset["description"]}"',
            f'    months_back = {dataset["months_back"]}',
            "    labels = {"
        ])
        
        for label_key, label_value in dataset["labels"].items():
            lines.append(f'      {label_key} = "{label_value}"')
        
        lines.extend([
            "    }",
            "  }",
            ""
        ])
    
    lines.extend([
        "}",
        "",
        "# Source Datasets and Tables Configuration",
        "source_datasets_config = {"
    ])
    
    # Source datasets
    for dataset_name, dataset_info in config["source_datasets_config"].items():
        lines.append(f'  "{dataset_name}" = {{')
        lines.append(f'    target_dataset_key = "{dataset_info["target_dataset_key"]}"')
        
        if "source_project_id" in dataset_info:
            lines.append(f'    source_project_id  = "{dataset_info["source_project_id"]}"')
        
        lines.extend([
            f'    description        = "{dataset_info["description"]}"',
            "    tables = {"
        ])
        
        # Tables
        for table_key, table_info in dataset_info["tables"].items():
            lines.extend([
                f'      "{table_key}" = {{',
                f'        source_table_id = "{table_info["source_table_id"]}"',
                f'        view_name      = "{table_info["view_name"]}"',
                "        filter_columns = ["
            ])
            
            # Filter columns
            for filter_col in table_info["filter_columns"]:
                lines.extend([
                    "          {",
                    f'            column_name = "{filter_col["column_name"]}"',
                    f'            condition   = "{filter_col["condition"]}"'
                ])
                if filter_col.get("operator") != "AND":
                    lines.append(f'            operator    = "{filter_col["operator"]}"')
                lines.append("          }")
            
            lines.append("        ]")
            
            if table_info.get("additional_where"):
                lines.append(f'        additional_where = "{table_info["additional_where"]}"')
            
            if table_info.get("description"):
                lines.append(f'        description     = "{table_info["description"]}"')
            
            lines.extend([
                "      }",
                ""
            ])
        
        lines.extend([
            "    }",
            "  }",
            ""
        ])
    
    lines.append("}")
    
    return "\n".join(lines)


def main():
    print("=== Terraform.tfvars Interactive Generator ===\n")
    
    # Basic configuration
    config = {}
    config["project_id"] = get_input("GCP Project ID")
    config["region"] = get_input("Region", default="asia-northeast1")
    config["view_prefix"] = get_input("View prefix", default="filtered_")
    
    # Client name for labeling
    client_name = get_input("Client name")
    
    # Collect global filter values first
    global_filters = collect_global_filter_values()
    
    # Output datasets configuration
    output_datasets_config = {}
    
    print("\n=== Output Dataset Configuration ===")
    print(f"Using client name '{client_name}' as dataset key")
    
    # Use client_name as the default dataset key
    client_key = client_name.lower().replace(" ", "_").replace("-", "_")
    dataset_key = get_input("Dataset key", default=client_key)
    months_back = int(get_input("Months back", default="18"))
    
    output_datasets_config[dataset_key] = {
        "dataset_id": f"{dataset_key}_filtered",
        "description": f"{dataset_key.title()} filtered views for {client_name}",
        "months_back": months_back,
        "labels": {
            "environment": "production",
            "client": client_name.lower().replace(" ", "_"),
            "team": dataset_key
        }
    }
    
    # Ask if they want additional output datasets
    while get_yes_no("Add another output dataset?", default=False):
        dataset_key = get_input("Dataset key (e.g., 'analytics', 'finance')")
        months_back = int(get_input("Months back", default="18"))
        
        output_datasets_config[dataset_key] = {
            "dataset_id": f"{dataset_key}_filtered",
            "description": f"{dataset_key.title()} filtered views for {client_name}",
            "months_back": months_back,
            "labels": {
                "environment": "production",
                "client": client_name.lower().replace(" ", "_"),
                "team": dataset_key
            }
        }
    
    config["output_datasets_config"] = output_datasets_config
    
    # Generate source datasets configuration automatically
    print("\n=== Generating Source Datasets Configuration ===")
    print("Using predefined datasets and tables structure...")
    source_datasets_config = generate_source_datasets_config(global_filters, client_key)
    config["source_datasets_config"] = source_datasets_config
    
    # Generate and save
    content = generate_tfvars_content(config)
    
    output_file = get_input("Output filename", default="terraform.tfvars")
    
    try:
        with open(output_file, 'w') as f:
            f.write(content)
        print(f"\n✅ Generated {output_file} successfully!")
    except Exception as e:
        print(f"❌ Error writing file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()