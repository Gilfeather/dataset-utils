

# Output BigQuery Datasets
resource "google_bigquery_dataset" "outputs" {
  for_each = var.output_datasets_config

  dataset_id    = each.value.dataset_id
  friendly_name = each.value.dataset_id
  description   = each.value.description
  location      = var.region

  # Optional: Set access controls
  access {
    role          = "OWNER"
    user_by_email = data.google_client_openid_userinfo.me.email
  }

  # Optional: Set default table expiration
  default_table_expiration_ms = 3600000 # 1 hour in milliseconds

  labels = merge(
    {
      environment = "terraform-managed"
      purpose     = "filtered-views"
    },
    each.value.labels
  )
}

# Get current user info
data "google_client_openid_userinfo" "me" {}



# Local values for building filter conditions
locals {
  # Flatten source datasets and tables for processing
  all_tables = merge([
    for source_dataset_key, source_dataset_config in var.source_datasets_config : {
      for table_key, table_config in source_dataset_config.tables : "${source_dataset_key}.${table_key}" => merge(table_config, {
        source_dataset_key = source_dataset_key
        source_project_id  = source_dataset_config.source_project_id
        target_dataset_key = source_dataset_config.target_dataset_key
        table_key          = table_key
      })
    }
  ]...)

  # Build filter conditions and date ranges for each table
  table_filters = {
    for table_full_key, table_config in local.all_tables : table_full_key => {
      combined_filter = join(" ", [
        for i, filter in table_config.filter_columns :
        "${i > 0 ? filter.operator : ""} ${filter.column_name} ${filter.condition}"
      ])

      # Get target dataset config for date calculations
      target_dataset_config = var.output_datasets_config[table_config.target_dataset_key]

      start_date_sql = "DATE_SUB(CURRENT_DATE(), INTERVAL ${var.output_datasets_config[table_config.target_dataset_key].months_back} MONTH)"
    }
  }
}

# BigQuery Views for each table
resource "google_bigquery_table" "views" {
  for_each = local.all_tables

  dataset_id = google_bigquery_dataset.outputs[each.value.target_dataset_key].dataset_id
  table_id   = "${var.view_prefix}${each.value.view_name}"

  view {
    query = templatefile("${path.module}/view_template.sql", {
      source_project_id = each.value.source_project_id != null ? each.value.source_project_id : var.project_id
      source_dataset    = each.value.source_dataset_key
      source_table      = each.value.source_table_id
      filter_conditions = local.table_filters[each.key].combined_filter
      additional_where  = each.value.additional_where
      start_date_sql    = local.table_filters[each.key].start_date_sql
    })
    use_legacy_sql = false
  }

  description = each.value.description != "" ? each.value.description : "Filtered view of ${each.value.source_table_id}"

  labels = {
    environment    = "terraform-managed"
    source_dataset = each.value.source_dataset_key
    source_table   = each.value.source_table_id
    target_dataset = each.value.target_dataset_key
    filter_count   = length(each.value.filter_columns)
  }

  depends_on = [google_bigquery_dataset.outputs]
}
