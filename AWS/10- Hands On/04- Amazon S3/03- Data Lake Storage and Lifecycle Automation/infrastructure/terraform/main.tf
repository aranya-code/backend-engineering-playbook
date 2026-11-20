locals {
  project_name = "data-lake-storage-lifecycle-automation"

  common_tags = {
    Project     = local.project_name
    ManagedBy   = "Terraform"
    Environment = var.environment
  }
}