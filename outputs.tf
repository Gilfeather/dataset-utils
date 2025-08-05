# Output datasets information
output "output_datasets" {
  description = "Information about the output BigQuery datasets"
  value = {
    for k, v in google_bigquery_dataset.outputs : k => {
      dataset_id  = v.dataset_id
      location    = v.location
      project_id  = var.project_id
      months_back = var.output_datasets_config[k].months_back
    }
  }
}

# Views outputs
output "created_views" {
  description = "Information about created views"
  value = {
    for k, v in google_bigquery_table.views : k => {
      table_id       = v.table_id
      dataset_id     = v.dataset_id
      project_id     = var.project_id
      source_dataset = local.all_tables[k].source_dataset_key
      source_table   = local.all_tables[k].source_table_id
      target_dataset = local.all_tables[k].target_dataset_key
      full_table_id  = "${var.project_id}.${v.dataset_id}.${v.table_id}"
    }
  }
}

# Summary by source dataset
output "views_by_source_dataset" {
  description = "Views grouped by source dataset"
  value = {
    for source_dataset_key, source_dataset_config in var.source_datasets_config : source_dataset_key => {
      source_project_id = source_dataset_config.source_project_id != null ? source_dataset_config.source_project_id : var.project_id
      description       = source_dataset_config.description
      table_count       = length(source_dataset_config.tables)
      tables = {
        for table_key, table_config in source_dataset_config.tables : table_key => {
          view_name      = "${var.view_prefix}${table_config.view_name}"
          source_table   = table_config.source_table_id
          target_dataset = source_dataset_config.target_dataset_key
          full_view_id   = "${var.project_id}.${var.output_datasets_config[source_dataset_config.target_dataset_key].dataset_id}.${var.view_prefix}${table_config.view_name}"
        }
      }
    }
  }
}

# Summary by output dataset
output "views_by_output_dataset" {
  description = "Views grouped by output dataset"
  value = {
    for output_dataset_key, output_dataset_config in var.output_datasets_config : output_dataset_key => {
      dataset_id  = output_dataset_config.dataset_id
      description = output_dataset_config.description
      views = {
        for table_full_key, table_config in local.all_tables :
        table_full_key => {
          view_name      = "${var.view_prefix}${table_config.view_name}"
          source_dataset = table_config.source_dataset_key
          source_table   = table_config.source_table_id
          full_view_id   = "${var.project_id}.${output_dataset_config.dataset_id}.${var.view_prefix}${table_config.view_name}"
        }
        if table_config.target_dataset_key == output_dataset_key
      }
      view_count = length([
        for table_config in local.all_tables : table_config
        if table_config.target_dataset_key == output_dataset_key
      ])
    }
  }
}

output "view_count" {
  description = "Number of views created"
  value       = length(google_bigquery_table.views)
}

# Date range information by output dataset
output "date_range_info_by_dataset" {
  description = "Information about the date range used in views by output dataset"
  value = {
    for k, v in var.output_datasets_config : k => {
      dataset_id     = v.dataset_id
      months_back    = v.months_back
      start_date_sql = "DATE_SUB(CURRENT_DATE(), INTERVAL ${v.months_back} MONTH)"
    }
  }
}
