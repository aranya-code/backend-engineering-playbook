variable "project_name" {
  description = "Short project identifier used in AWS resource names. Use lowercase letters, numbers, and hyphens."
  type        = string
  default     = "secure-file-upload-api"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,39}$", var.project_name))
    error_message = "project_name must contain 2-40 lowercase letters, numbers, or hyphens and must start with a letter or number."
  }
}

variable "environment" {
  description = "Deployment environment used for resource naming and tagging."
  type        = string
  default     = "dev"

  validation {
    condition = contains(
      ["dev", "development", "staging", "prod", "production"],
      lower(var.environment)
    )
    error_message = "environment must be one of: dev, development, staging, prod, production."
  }
}

variable "aws_region" {
  description = "AWS Region in which the S3 bucket and KMS key will be provisioned."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-[a-z]+)+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS Region identifier, such as ap-south-1."
  }
}

variable "bucket_name" {
  description = "Optional globally unique S3 bucket name. Leave empty to generate a name from the project, environment, Region, and AWS account ID."
  type        = string
  default     = ""

  validation {
    condition = var.bucket_name == "" || (
      length(var.bucket_name) >= 3 &&
      length(var.bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.bucket_name)) &&
      !strcontains(var.bucket_name, "..") &&
      !can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$", var.bucket_name))
    )
    error_message = "bucket_name must be empty or a valid S3 bucket name containing 3-63 lowercase letters, numbers, periods, or hyphens, without consecutive periods or an IP-address format."
  }
}

variable "s3_upload_prefix" {
  description = "Relative S3 object-key prefix allocated to application uploads. A trailing slash is optional."
  type        = string
  default     = "uploads/"

  validation {
    condition = (
      !startswith(var.s3_upload_prefix, "/") &&
      !strcontains(var.s3_upload_prefix, "..") &&
      !strcontains(var.s3_upload_prefix, "\\") &&
      !strcontains(var.s3_upload_prefix, "//") &&
      !can(regex("[[:cntrl:]]", var.s3_upload_prefix))
    )
    error_message = "s3_upload_prefix must be a relative prefix and must not contain '..', backslashes, consecutive slashes, or control characters."
  }
}

variable "kms_key_deletion_window_days" {
  description = "Waiting period before a scheduled customer-managed KMS key deletion. AWS permits values from 7 to 30 days."
  type        = number
  default     = 30

  validation {
    condition = (
      var.kms_key_deletion_window_days >= 7 &&
      var.kms_key_deletion_window_days <= 30 &&
      floor(var.kms_key_deletion_window_days) == var.kms_key_deletion_window_days
    )
    error_message = "kms_key_deletion_window_days must be a whole number between 7 and 30."
  }
}

variable "object_lock_retention_days" {
  description = "Default S3 Object Lock governance-mode retention period in days. Objects cannot be permanently deleted during this period without an authorized governance-retention bypass."
  type        = number
  default     = 30

  validation {
    condition = (
      var.object_lock_retention_days >= 1 &&
      floor(var.object_lock_retention_days) == var.object_lock_retention_days
    )
    error_message = "object_lock_retention_days must be a positive whole number."
  }
}

variable "abort_incomplete_multipart_upload_days" {
  description = "Number of days after initiation before S3 lifecycle rules abort incomplete multipart uploads."
  type        = number
  default     = 7

  validation {
    condition = (
      var.abort_incomplete_multipart_upload_days >= 1 &&
      floor(var.abort_incomplete_multipart_upload_days) == var.abort_incomplete_multipart_upload_days
    )
    error_message = "abort_incomplete_multipart_upload_days must be a positive whole number."
  }
}

variable "noncurrent_version_expiration_days" {
  description = "Number of days before noncurrent object versions under the configured upload prefix become eligible for lifecycle expiration."
  type        = number
  default     = 90

  validation {
    condition = (
      var.noncurrent_version_expiration_days >= 1 &&
      floor(var.noncurrent_version_expiration_days) == var.noncurrent_version_expiration_days
    )
    error_message = "noncurrent_version_expiration_days must be a positive whole number."
  }
}

variable "tags" {
  description = "Additional tags applied to AWS resources. Project, Environment, and ManagedBy tags are added by the Terraform configuration."
  type        = map(string)
  default = {
    Application = "secure-file-upload-api"
    Component   = "storage"
  }
}