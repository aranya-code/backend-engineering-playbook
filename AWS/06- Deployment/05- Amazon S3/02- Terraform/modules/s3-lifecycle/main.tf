terraform {
  required_version = ">= 1.5.0"
}

locals {
  lifecycle_rule_ids = [
    for rule in var.lifecycle_rules : rule.id
  ]

  lifecycle_rule_prefixes = [
    for rule in var.lifecycle_rules : try(rule.filter.prefix, null)
  ]

  lifecycle_rule_tags = [
    for rule in var.lifecycle_rules : try(rule.filter.tags, {})
  ]
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = var.bucket_id

  # Lifecycle configuration requires bucket versioning to be in a
  # compatible state. The bucket-owning module remains responsible
  # for managing versioning.
  depends_on = [
    var.bucket_dependency
  ]

  dynamic "rule" {
    for_each = var.lifecycle_rules

    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      filter {
        prefix = try(rule.value.filter.prefix, null)

        dynamic "tag" {
          for_each = try(rule.value.filter.tags, {})

          content {
            key   = tag.key
            value = tag.value
          }
        }
      }

      dynamic "transition" {
        for_each = try(rule.value.transitions, [])

        content {
          days          = try(transition.value.days, null)
          date          = try(transition.value.date, null)
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = try(rule.value.expiration, null) == null ? [] : [rule.value.expiration]

        content {
          days                         = try(expiration.value.days, null)
          date                         = try(expiration.value.date, null)
          expired_object_delete_marker = try(expiration.value.expired_object_delete_marker, null)
        }
      }

      dynamic "noncurrent_version_transition" {
        for_each = try(rule.value.noncurrent_version_transitions, [])

        content {
          noncurrent_days           = noncurrent_version_transition.value.noncurrent_days
          storage_class             = noncurrent_version_transition.value.storage_class
          newer_noncurrent_versions = try(noncurrent_version_transition.value.newer_noncurrent_versions, null)
        }
      }

      dynamic "noncurrent_version_expiration" {
        for_each = try(rule.value.noncurrent_version_expiration, null) == null ? [] : [rule.value.noncurrent_version_expiration]

        content {
          noncurrent_days           = noncurrent_version_expiration.value.noncurrent_days
          newer_noncurrent_versions = try(noncurrent_version_expiration.value.newer_noncurrent_versions, null)
        }
      }

      dynamic "abort_incomplete_multipart_upload" {
        for_each = try(rule.value.abort_incomplete_multipart_upload_days, null) == null ? [] : [rule.value.abort_incomplete_multipart_upload_days]

        content {
          days_after_initiation = abort_incomplete_multipart_upload.value
        }
      }
    }
  }

  lifecycle {
    precondition {
      condition = length(var.lifecycle_rules) > 0

      error_message = "At least one lifecycle rule must be supplied to create an S3 lifecycle configuration."
    }

    precondition {
      condition = length(local.lifecycle_rule_ids) == length(distinct(local.lifecycle_rule_ids))

      error_message = "Lifecycle rule IDs must be unique within the bucket configuration."
    }
  }
}
