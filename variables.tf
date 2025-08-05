# GCP Project Configuration
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

# BigQuery Output Datasets Configuration
variable "output_datasets_config" {
  description = "Configuration for output BigQuery datasets"
  type = map(object({
    dataset_id  = string
    description = optional(string, "Filtered views dataset created by Terraform")
    months_back = optional(number, 18)
    labels      = optional(map(string), {})
  }))
}





# Source Datasets and Tables Configuration
variable "source_datasets_config" {
  description = "Configuration grouped by source datasets"
  type = map(object({
    source_project_id  = optional(string, null) # If null, uses var.project_id
    target_dataset_key = string                 # Key from output_datasets_config
    description        = optional(string, "")
    tables = map(object({
      source_table_id = string
      view_name       = string
      filter_columns = list(object({
        column_name = string
        condition   = string
        operator    = optional(string, "AND") # AND or OR
      }))
      additional_where = optional(string, "")
      description      = optional(string, "")
    }))
  }))
}

variable "view_prefix" {
  description = "Prefix for view names"
  type        = string
  default     = "filtered_"
}
