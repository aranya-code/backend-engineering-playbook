terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"

  default_tags {
    tags = {
      Environment = "example"
      Project     = "amazon-s3-playbook"
      ManagedBy   = "terraform"
      Purpose     = "secure-s3-bucket-example"
    }
  }
}

module "secure_bucket" {
  source = "../../modules/s3-bucket"

  # Replace this placeholder with a globally unique S3 bucket name.
  bucket_name = "your-org-secure-s3-example-bucket"

  # Prevent accidental deletion of non-empty buckets.
  force_destroy = false

  # Enable versioning to preserve object versions and support recovery.
  versioning_enabled = true

  # Use SSE-S3 by default. Supply a customer-managed KMS key ARN
  # when the workload requires SSE-KMS.
  kms_key_arn        = null
  bucket_key_enabled = true

  # Keep lifecycle management separate when using the dedicated
  # s3-lifecycle module.
  lifecycle_rules = []

  # Server access logging is optional. Configure a separate,
  # pre-existing logging bucket when access logging is required.
  logging_target_bucket = null
  logging_target_prefix = "s3-access-logs/"

  tags = {
    Name        = "secure-s3-example"
    Environment = "example"
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
    DataClass   = "internal"
  }
}
