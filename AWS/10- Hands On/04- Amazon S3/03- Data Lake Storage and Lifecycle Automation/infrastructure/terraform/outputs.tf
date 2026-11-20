output "aws_region" {
  description = "AWS Region where the data lake infrastructure is deployed."
  value       = var.aws_region
}

output "environment" {
  description = "Deployment environment associated with the data lake."
  value       = var.environment
}

output "project_name" {
  description = "Logical project identifier used for resource tagging."
  value       = local.project_name
}

output "raw_data_prefix" {
  description = "S3 prefix used for raw event datasets."
  value       = var.raw_data_prefix
}

output "processed_data_prefix" {
  description = "S3 prefix reserved for processed event datasets."
  value       = var.processed_data_prefix
}

output "analytics_data_prefix" {
  description = "S3 prefix used for analytics artifacts and Athena query results."
  value       = var.analytics_data_prefix
}

output "glue_database_name" {
  description = "AWS Glue database name configured for the data lake."
  value       = var.glue_database_name
}

output "glue_table_name" {
  description = "AWS Glue table name configured for event analytics."
  value       = var.glue_table_name
}

output "athena_workgroup_name" {
  description = "Athena workgroup name configured for data lake queries."
  value       = var.athena_workgroup_name
}

output "bucket_versioning_enabled" {
  description = "Whether S3 bucket versioning is enabled by configuration."
  value       = var.enable_bucket_versioning
}

output "lifecycle_configuration_enabled" {
  description = "Whether S3 lifecycle configuration is enabled by configuration."
  value       = var.enable_lifecycle_configuration
}

output "glue_catalog_enabled" {
  description = "Whether Glue catalog resources are enabled by configuration."
  value       = var.enable_glue_catalog
}

output "athena_workgroup_enabled" {
  description = "Whether the Athena workgroup is enabled by configuration."
  value       = var.enable_athena_workgroup
}