variable "bucket_id" {
  description = "Name or ID of the existing S3 bucket whose lifecycle configuration will be managed."
  type        = string

  validation {
    condition     = length(trimspace(var.bucket_id)) > 0
    error_message = "bucket_id must not be empty."
  }
}

variable "bucket_dependency" {
  description = "Dependency reference to the bucket-owning module or resource. Use this to ensure the bucket exists before applying lifecycle configuration."
  type        = any
  default     = null
}

variable "lifecycle_rules" {
  description = <<-EOT
    Lifecycle rules to apply to the bucket.

    Each rule supports:
    - id: Unique rule identifier.
    - enabled: Whether the rule is enabled.
    - filter: Optional prefix and/or object tags.
    - transitions: Current-version storage-class transitions.
    - expiration: Current-version expiration configuration.
    - noncurrent_version_transitions: Transitions for noncurrent object versions.
    - noncurrent_version_expiration: Expiration for noncurrent object versions.
    - abort_incomplete_multipart_upload_days: Days after which incomplete multipart uploads are aborted.

    A rule should use an appropriate filter to avoid unintentionally affecting unrelated objects.
  EOT

  type = list(object({
    id      = string
    enabled = optional(bool, true)

    filter = optional(object({
      prefix = optional(string)
      tags   = optional(map(string), {})
    }), {})

    transitions = optional(list(object({
      days          = optional(number)
      date          = optional(string)
      storage_class = string
    })), [])

    expiration = optional(object({
      days                         = optional(number)
      date                         = optional(string)
      expired_object_delete_marker = optional(bool)
    }))

    noncurrent_version_transitions = optional(list(object({
      noncurrent_days           = number
      storage_class             = string
      newer_noncurrent_versions = optional(number)
    })), [])

    noncurrent_version_expiration = optional(object({
      noncurrent_days           = number
      newer_noncurrent_versions = optional(number)
    }))

    abort_incomplete_multipart_upload_days = optional(number)
  }))

  default = []

  validation {
    condition = (
      length(var.lifecycle_rules) > 0 &&
      length(distinct([for rule in var.lifecycle_rules : rule.id])) == length(var.lifecycle_rules) &&
      alltrue([
        for rule in var.lifecycle_rules :
        length(trimspace(rule.id)) > 0
      ])
    )

    error_message = "Provide at least one lifecycle rule. Every rule must have a non-empty, unique ID."
  }

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      alltrue([
        for transition in rule.transitions :
        contains(
          [
            "STANDARD_IA",
            "ONEZONE_IA",
            "INTELLIGENT_TIERING",
            "GLACIER",
            "GLACIER_IR",
            "DEEP_ARCHIVE"
          ],
          transition.storage_class
        ) &&
        (
          (transition.days != null && transition.date == null && transition.days >= 0) ||
          (transition.days == null && transition.date != null)
        )
      ])
    ])

    error_message = "Each current-version transition must specify exactly one of days or date, use a non-negative day value when applicable, and use a supported S3 storage class."
  }

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      rule.expiration == null ? true : (
        (
          (rule.expiration.days != null ? 1 : 0) +
          (rule.expiration.date != null ? 1 : 0) +
          (rule.expiration.expired_object_delete_marker != null ? 1 : 0)
        ) == 1 &&
        (rule.expiration.days == null || rule.expiration.days >= 0)
      )
    ])

    error_message = "Each expiration configuration must specify exactly one of days, date, or expired_object_delete_marker. Day values must be non-negative."
  }

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      alltrue([
        for transition in rule.noncurrent_version_transitions :
        transition.noncurrent_days >= 0 &&
        contains(
          [
            "STANDARD_IA",
            "ONEZONE_IA",
            "INTELLIGENT_TIERING",
            "GLACIER",
            "GLACIER_IR",
            "DEEP_ARCHIVE"
          ],
          transition.storage_class
        ) &&
        (
          transition.newer_noncurrent_versions == null ||
          transition.newer_noncurrent_versions >= 0
        )
      ])
    ])

    error_message = "Noncurrent version transitions require non-negative noncurrent_days, a supported storage class, and a non-negative newer_noncurrent_versions value when specified."
  }

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      rule.noncurrent_version_expiration == null ? true : (
        rule.noncurrent_version_expiration.noncurrent_days >= 0 &&
        (
          rule.noncurrent_version_expiration.newer_noncurrent_versions == null ||
          rule.noncurrent_version_expiration.newer_noncurrent_versions >= 0
        )
      )
    ])

    error_message = "Noncurrent version expiration requires non-negative noncurrent_days and a non-negative newer_noncurrent_versions value when specified."
  }

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      rule.abort_incomplete_multipart_upload_days == null ||
      rule.abort_incomplete_multipart_upload_days >= 1
    ])

    error_message = "abort_incomplete_multipart_upload_days must be at least 1 when specified."
  }

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      length(try(rule.filter.tags, {})) == length(distinct(keys(try(rule.filter.tags, {}))))
    ])

    error_message = "Lifecycle filter tag keys must be unique within each rule."
  }
}
