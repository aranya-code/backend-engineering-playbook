variable "bucket_id" {
  description = "Name or ID of the existing S3 bucket to secure. The bucket must be managed by the calling configuration or already exist."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.bucket_id)) > 0
    error_message = "bucket_id must be a non-empty S3 bucket name or ID."
  }
}

variable "bucket_arn" {
  description = "ARN of the existing S3 bucket. Used to construct bucket-level and object-level IAM policy resource ARNs."
  type        = string
  nullable    = false

  validation {
    condition = can(regex(
      "^arn:(aws|aws-us-gov|aws-cn):s3:::[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$",
      var.bucket_arn
    ))
    error_message = "bucket_arn must be a valid general-purpose S3 bucket ARN."
  }
}

variable "kms_key_arn" {
  description = "Optional customer-managed AWS KMS key ARN for default SSE-KMS encryption. When null, the module configures SSE-S3 (AES256)."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.kms_key_arn == null ||
      can(regex(
        "^arn:(aws|aws-us-gov|aws-cn):kms:[a-z0-9-]+:[0-9]{12}:key/[A-Za-z0-9-]+$",
        var.kms_key_arn
      ))
    )
    error_message = "kms_key_arn must be null or a valid AWS KMS key ARN."
  }
}

variable "bucket_key_enabled" {
  description = "Whether to enable S3 Bucket Keys when SSE-KMS is configured. Bucket Keys can reduce AWS KMS request costs."
  type        = bool
  default     = true
  nullable    = false
}

variable "enforce_encryption_header" {
  description = "Whether to deny PutObject requests that omit the server-side encryption header. Enable only when upload clients explicitly provide encryption headers; bucket default encryption alone does not satisfy this requirement."
  type        = bool
  default     = false
  nullable    = false
}

variable "allowed_principal_arns" {
  description = "IAM principal ARNs granted the actions in allowed_actions through the bucket policy. Use specific IAM roles rather than broad account-wide principals."
  type        = set(string)
  default     = []
  nullable    = false

  validation {
    condition = alltrue([
      for arn in var.allowed_principal_arns :
      can(regex(
        "^arn:(aws|aws-us-gov|aws-cn):iam::[0-9]{12}:(role|user)/[A-Za-z0-9_+=,.@/-]+$",
        arn
      ))
    ])
    error_message = "Each allowed principal must be an IAM role or IAM user ARN."
  }
}

variable "allowed_actions" {
  description = "S3 IAM actions granted to each configured principal. Use only the permissions required by the workload. Actions must be compatible with the bucket and object resources constructed in main.tf."
  type        = set(string)

  default = [
    "s3:GetObject",
    "s3:PutObject",
    "s3:ListBucket"
  ]

  nullable = false

  validation {
    condition = (
      length(var.allowed_actions) > 0 &&
      alltrue([
        for action in var.allowed_actions :
        contains([
          "s3:ListBucket",
          "s3:ListBucketVersions",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:DeleteObjectVersion"
        ], action)
      ])
    )
    error_message = "allowed_actions must contain at least one supported bucket-level or object-level S3 action."
  }
}

variable "cors_rules" {
  description = "Optional S3 CORS rules for browser-based access. Restrict allowed origins, methods, and headers to the application's actual requirements."
  type = list(object({
    id              = optional(string)
    allowed_headers = optional(list(string), ["*"])
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = optional(list(string), [])
    max_age_seconds = optional(number, 3000)
  }))

  default  = []
  nullable = false

  validation {
    condition = alltrue([
      for rule in var.cors_rules :
      length(rule.allowed_methods) > 0 &&
      length(rule.allowed_origins) > 0 &&
      alltrue([
        for method in rule.allowed_methods :
        contains(["GET", "PUT", "POST", "DELETE", "HEAD"], method)
      ]) &&
      alltrue([
        for origin in rule.allowed_origins :
        length(trimspace(origin)) > 0
      ]) &&
      alltrue([
        for header in rule.allowed_headers :
        length(trimspace(header)) > 0
      ]) &&
      alltrue([
        for header in rule.expose_headers :
        length(trimspace(header)) > 0
      ]) &&
      rule.max_age_seconds >= 0 &&
      rule.max_age_seconds <= 86400
    ])
    error_message = "Each CORS rule must specify valid HTTP methods, non-empty origins and headers, and max_age_seconds between 0 and 86400."
  }

  validation {
    condition = (
      length([
        for rule in var.cors_rules : rule.id
        if rule.id != null
      ]) ==
      length(distinct([
        for rule in var.cors_rules : rule.id
        if rule.id != null
      ]))
    )
    error_message = "CORS rule IDs must be unique when specified."
  }

  validation {
    condition = alltrue([
      for rule in var.cors_rules :
      rule.id == null ? true : length(trimspace(rule.id)) > 0
    ])
    error_message = "A CORS rule ID must not be empty when provided."
  }
}

variable "request_payer_enabled" {
  description = "Whether to configure Requester Pays for the bucket. When enabled, eligible requesters pay applicable request and data transfer charges. This setting is unsuitable for many application-facing buckets."
  type        = bool
  default     = false
  nullable    = false
}

variable "tags" {
  description = "Reserved metadata for the module's common_tags local value. This module does not create or update bucket tags; manage tagging through the bucket-owning Terraform module."
  type        = map(string)
  default     = {}
  nullable    = false

  validation {
    condition = alltrue([
      for key, value in var.tags :
      length(trimspace(key)) > 0 &&
      length(key) <= 128 &&
      length(value) <= 256 &&
      !startswith(lower(key), "aws:")
    ])
    error_message = "Tag keys must be non-empty, at most 128 characters, and must not use the reserved aws: prefix. Tag values must not exceed 256 characters."
  }
}
