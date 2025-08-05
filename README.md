# BigQuery Filtered Views Terraform Utility

This Terraform utility creates filtered BigQuery views from multiple source datasets with flexible filtering conditions and configurable time ranges.

## Features

- **Multiple Output Datasets**: Create views in different datasets based on team/purpose
- **Flexible Filtering**: Support for multiple filter columns with AND/OR operators
- **Configurable Time Ranges**: Different data retention periods per output dataset
- **Cross-Project Support**: Source tables can be from different GCP projects
- **Scalable**: Designed to handle 90+ tables efficiently

## Quick Start

### 1. Prerequisites

- Terraform >= 1.0
- GCP credentials configured
- BigQuery API enabled
- GCS bucket for Terraform state (recommended)

### 2. Setup

```bash
# Clone or copy the files
# Update configuration files
cp terraform.tfvars.example terraform.tfvars
cp backend.tfvars.example backend.tfvars

# Edit terraform.tfvars with your settings
# Edit backend.tfvars with your GCS bucket info
```

### 3. Configuration

#### Backend Configuration (backend.tfvars)
```hcl
bucket = "your-terraform-state-bucket"
prefix = "bigquery-filtered-views/terraform.tfstate"
```

#### Main Configuration (terraform.tfvars)
```hcl
project_id = "your-gcp-project-id"
region     = "asia-northeast1"

# Output datasets with different retention periods
output_datasets_config = {
  "analytics" = {
    dataset_id  = "analytics_filtered"
    months_back = 24  # 24 months retention
  }
  "finance" = {
    dataset_id  = "finance_filtered"
    months_back = 12  # 12 months retention
  }
}

# Source datasets and tables
source_datasets_config = {
  "raw_analytics" = {
    target_dataset_key = "analytics"
    tables = {
      "user_events" = {
        source_table_id = "user_events"
        view_name      = "user_behavior"
        filter_columns = [
          {
            column_name = "event_type"
            condition   = "IN ('click', 'view')"
          }
        ]
      }
    }
  }
}
```

### 4. Deploy

```bash
# Initialize Terraform
terraform init -backend-config=backend.tfvars

# Plan the deployment
terraform plan -var-file=terraform.tfvars

# Apply the changes
terraform apply -var-file=terraform.tfvars
```

## Configuration Reference

### Output Datasets

```hcl
output_datasets_config = {
  "dataset_key" = {
    dataset_id  = "actual_dataset_id"
    description = "Dataset description"
    months_back = 18  # Data retention in months
    labels = {
      team = "analytics"
    }
  }
}
```

### Source Datasets

```hcl
source_datasets_config = {
  "source_dataset_name" = {
    source_project_id  = "external-project-id"  # Optional
    target_dataset_key = "output_dataset_key"
    description       = "Source dataset description"
    tables = {
      "table_key" = {
        source_table_id = "actual_table_name"
        view_name      = "filtered_view_name"
        filter_columns = [
          {
            column_name = "status"
            condition   = "= 'active'"
          },
          {
            column_name = "created_at"
            condition   = "IS NOT NULL"
            operator    = "AND"
          }
        ]
        additional_where = "custom_field > 0"
        description     = "Table description"
      }
    }
  }
}
```

### Filter Columns

- **column_name**: Column to filter on
- **condition**: SQL condition (e.g., `= 'value'`, `> 100`, `IN ('a', 'b')`)
- **operator**: `AND` or `OR` (default: `AND`)

### Time Filtering

All views automatically include time-based filtering:
- **Start Date**: `DATE_SUB(CURRENT_DATE(), INTERVAL {months_back} MONTH)`
- **End Date**: `CURRENT_DATE()`
- **Date Column**: `created_at` (configurable in view_template.sql)

## File Structure

```
.
├── main.tf                    # Main BigQuery resources
├── variables.tf               # Variable definitions
├── outputs.tf                 # Output definitions
├── versions.tf                # Terraform and provider versions
├── providers.tf               # Provider configurations
├── backend.tf                 # Backend configuration
├── view_template.sql          # SQL template for views
├── terraform.tfvars.example   # Configuration example
├── backend.tfvars.example     # Backend configuration example
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Outputs

After deployment, Terraform provides:

- **output_datasets**: Information about created datasets
- **created_views**: Details of all created views
- **views_by_source_dataset**: Views grouped by source dataset
- **views_by_output_dataset**: Views grouped by output dataset
- **date_range_info_by_dataset**: Date range information per dataset

## Best Practices

1. **Use descriptive names** for datasets and views
2. **Group related tables** in the same source dataset
3. **Set appropriate retention periods** based on data usage
4. **Use labels** for better resource organization
5. **Test with a small subset** before deploying all 90 tables
6. **Use version control** for configuration files
7. **Set up proper IAM permissions** for cross-project access

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure proper BigQuery and GCS permissions
2. **Table Not Found**: Verify source table names and project IDs
3. **Invalid SQL**: Check filter conditions and additional_where clauses
4. **Backend Issues**: Ensure GCS bucket exists and is accessible

### Validation

```bash
# Validate configuration
terraform validate

# Check plan before applying
terraform plan -var-file=terraform.tfvars

# View current state
terraform show
```

## Contributing

1. Test changes with a small configuration first
2. Update documentation for new features
3. Follow Terraform best practices
4. Ensure backward compatibility

## License

This utility is provided as-is for educational and operational purposes.