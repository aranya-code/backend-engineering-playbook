data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_region" "current" {}

locals {
  project_name = "document-ingestion-metadata-pipeline"

  name_prefix = "${local.project_name}-${var.environment}"

  aws_account_id = data.aws_caller_identity.current.account_id
  aws_partition  = data.aws_partition.current.partition
  aws_region     = data.aws_region.current.name

  common_tags = {
    Project     = local.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}