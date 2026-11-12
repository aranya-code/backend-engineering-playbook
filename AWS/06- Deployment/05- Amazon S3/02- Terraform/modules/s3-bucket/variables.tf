variable "bucket_name" {
  description = "Globally unique name of the S3 bucket."
  type        = string

  validation {
    condition = (
      length(var.bucket_name) >= 3 &&
      length(var.bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.bucket_name)) &&
      !can(regex("^\\d{1,3}(\\.\\d{1,3}){3}$", var.bucket_name)) &&
      !strcontains(var.bucket_name, "..") &&
      !strcontains(var.bucket_name, ".-") &&
      !strcontains(var.bucket_name, "-.")
    )
    error_message = "bucket_name must be a valid S3 bucket name: 3-63 lowercase letters, numbers, dots, or hyphens; it must not resemble an IPv4 address or contain adjacent periods or invalid dot-hyphen combinations."
  }
}

variable "force_destroy" {
  description = "Allow Terraform to delete a non-empty bucket. Keep false for production buckets."
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Enable S3 bucket versioning. Disabling versioning suspends it but does not remove existing object versions."
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of an existing customer-managed KMS key. Null uses SSE-S3 encryption."
  type        = string
  default     = null
  nullable    = true
}

variable "bucket_key_enabled" {
  description = "Enable S3 Bucket Keys when SSE-KMS is configured."
  type        = bool
  default     = true
}

variable "lifecycle_rules" {
  description = "Lifecycle rules for expiration, noncurrent-version cleanup, and incomplete multipart uploads."

  type = list(object({
    id                                     = string
    enabled                                = optional(bool, true)
    prefix                                 = optional(string)
    expiration_days                       = optional(number)
    noncurrent_version_expiration_days    = optional(number)
    abort_incomplete_multipart_upload_days = optional(number)
  }))

  default = []

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      length(trimspace(rule.id)) > 0 &&
      (
        rule.expiration_days == null ||
        rule.expiration_days >= 1
      ) &&
      (
        rule.noncurrent_version_expiration_days == null ||
        rule.noncurrent_version_expiration_days >= 1
      ) &&
      (
        rule.abort_incomplete_multipart_upload_days == null ||
        rule.abort_incomplete_multipart_upload_days >= 1
      ) &&
      (
        rule.expiration_days != null ||
        rule.noncurrent_version_expiration_days != null ||
        rule.abort_incomplete_multipart_upload_days != null
      )
    ])

    error_message = "Each lifecycle rule must have a non-empty ID and at least one supported action with a positive number of days."
  }

  validation {
    condition = length(distinct([
      for rule in var.lifecycle_rules : rule.id
    ])) == length(var.lifecycle_rules)

    error_message = "Lifecycle rule IDs must be unique within the bucket."
  }
}

variable "logging_target_bucket" {
  description = "Name of an existing bucket that receives S3 server access logs. Set to null to disable access logging."
  type        = string
  default     = null
  nullable    = true
}

variable "logging_target_prefix" {
  description = "Prefix used for S3 server access log objects in the target bucket."
  type        = string
  default     = "s3-access-logs/"
}

variable "tags" {
  description = "Additional tags applied to the S3 bucket."
  type        = map(string)
  default     = {}
}
