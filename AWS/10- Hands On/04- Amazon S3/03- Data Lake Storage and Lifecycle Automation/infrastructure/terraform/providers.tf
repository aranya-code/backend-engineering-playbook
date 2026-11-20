provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "data-lake-storage-lifecycle-automation"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}