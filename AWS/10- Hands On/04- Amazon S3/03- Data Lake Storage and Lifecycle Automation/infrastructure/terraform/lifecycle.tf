resource "aws_s3_bucket_lifecycle_configuration" "raw_data" {
  count = var.enable_lifecycle_configuration ? 1 : 0

  bucket = aws_s3_bucket.raw_data.id

  depends_on = [
    aws_s3_bucket_versioning.raw_data
  ]

  rule {
    id     = "raw-events-storage-transition-and-retention"
    status = "Enabled"

    filter {
      prefix = "${var.raw_data_prefix}/"
    }

    transition {
      days          = var.lifecycle_transition_to_ia_days
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.lifecycle_transition_to_glacier_days
      storage_class = "GLACIER"
    }

    dynamic "expiration" {
      for_each = var.lifecycle_expiration_days > 0 ? [var.lifecycle_expiration_days] : []

      content {
        days = expiration.value
      }
    }

    dynamic "noncurrent_version_expiration" {
      for_each = (
        var.enable_bucket_versioning &&
        var.noncurrent_version_expiration_days > 0
      ) ? [var.noncurrent_version_expiration_days] : []

      content {
        noncurrent_days = noncurrent_version_expiration.value
      }
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = var.abort_incomplete_multipart_upload_days
    }
  }

  lifecycle {
    precondition {
      condition = (
        var.lifecycle_transition_to_glacier_days >
        var.lifecycle_transition_to_ia_days
      )
      error_message = "The Glacier transition must occur after the Standard-IA transition."
    }

    precondition {
      condition = (
        var.lifecycle_expiration_days == 0 ||
        var.lifecycle_expiration_days > var.lifecycle_transition_to_glacier_days
      )
      error_message = "Raw data expiration must occur after the configured Glacier transition, or be set to zero to disable expiration."
    }
  }
}