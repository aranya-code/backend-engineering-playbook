provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "document-ingestion-metadata-pipeline"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}