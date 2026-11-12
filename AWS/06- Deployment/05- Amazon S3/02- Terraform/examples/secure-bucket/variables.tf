variable "aws_region" {
  description = "AWS Region in which the secure S3 bucket is created."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS Region identifier."
  }
}

variable "bucket_name" {
  description = "Globally unique name for the S3 bucket. Use a workload- and environment-specific name."
  type        = string

  validation {
    condition = (
      length(var.bucket_name) >= 3 &&
      length(var.bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.bucket_name)) &&
      !can(regex("\\.\\.", var.bucket_name)) &&
      !can(regex("\\.-|\\-\\.", var.bucket_name)) &&
      !can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}$", var.bucket_name))
    )
    error_message = "bucket_name must be a valid S3 general-purpose bucket name: 3-63 characters, lowercase letters, numbers, dots, or hyphens, with no adjacent periods, dot-hyphen combinations, or IP-address format."
  }
}

variable "force_destroy" {
  description = "Allow Terraform to delete a non-empty bucket. Keep false for production and protected data."
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Enable S3 bucket versioning to preserve object versions and support recovery."
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "Optional customer-managed AWS KMS key ARN for SSE-KMS. Null uses the module's default SSE-S3 behavior."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.kms_key_arn == null ||
      can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.kms_key_arn))
    )
    error_message = "kms_key_arn must be null or a valid customer-managed KMS key ARN."
  }
}

variable "bucket_key_enabled" {
  description = "Enable S3 Bucket Keys when SSE-KMS is configured to reduce KMS request costs."
  type        = bool
  default     = true
}

variable "lifecycle_rules" {
  description = "Lifecycle rules passed to the s3-bucket module. Keep empty when lifecycle configuration is managed by the dedicated s3-lifecycle module."
  type        = any
  default     = []
}

variable "logging_target_bucket" {
  description = "Optional name of an existing S3 bucket that receives server access logs."
  type        = string
  default     = null
  nullable    = true
}

variable "logging_target_prefix" {
  description = "Prefix used for server access log objects in the target bucket."
  type        = string
  default     = "s3-access-logs/"
}

variable "tags" {
  description = "Tags applied to the secure S3 bucket and supported resources."
  type        = map(string)
  default = {
    Name        = "secure-s3-example"
    Environment = "example"
    Project     = "amazon-s3-playbook"
    ManagedBy   = "terraform"
    DataClass   = "internal"
  }
}
