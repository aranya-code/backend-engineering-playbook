terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

data "aws_iam_policy_document" "replication_assume_role" {
  statement {
    sid     = "AllowS3ReplicationService"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.source_account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [var.source_bucket_arn]
    }
  }
}

resource "aws_iam_role" "replication" {
  name               = var.replication_role_name
  assume_role_policy = data.aws_iam_policy_document.replication_assume_role.json
  description        = "IAM role assumed by Amazon S3 to replicate objects from the source bucket."

  tags = var.tags
}

data "aws_iam_policy_document" "replication_permissions" {
  statement {
    sid    = "ReadSourceBucketReplicationConfiguration"
    effect = "Allow"

    actions = [
      "s3:GetReplicationConfiguration",
      "s3:ListBucket"
    ]

    resources = [
      var.source_bucket_arn
    ]
  }

  statement {
    sid    = "ReadSourceObjectVersions"
    effect = "Allow"

    actions = [
      "s3:GetObjectVersionForReplication",
      "s3:GetObjectVersionAcl",
      "s3:GetObjectVersionTagging"
    ]

    resources = [
      "${var.source_bucket_arn}/*"
    ]
  }

  statement {
    sid    = "WriteDestinationObjectReplicas"
    effect = "Allow"

    actions = [
      "s3:ReplicateObject",
      "s3:ReplicateDelete",
      "s3:ReplicateTags"
    ]

    resources = [
      "${var.destination_bucket_arn}/*"
    ]
  }

  dynamic "statement" {
    for_each = var.source_kms_key_arn == null ? [] : [var.source_kms_key_arn]

    content {
      sid    = "DecryptSourceObjects"
      effect = "Allow"

      actions = [
        "kms:Decrypt"
      ]

      resources = [
        statement.value
      ]
    }
  }

  dynamic "statement" {
    for_each = var.destination_kms_key_arn == null ? [] : [var.destination_kms_key_arn]

    content {
      sid    = "EncryptDestinationReplicas"
      effect = "Allow"

      actions = [
        "kms:Encrypt",
        "kms:GenerateDataKey"
      ]

      resources = [
        statement.value
      ]
    }
  }
}

resource "aws_iam_role_policy" "replication" {
  name   = "${var.replication_role_name}-permissions"
  role   = aws_iam_role.replication.id
  policy = data.aws_iam_policy_document.replication_permissions.json
}

resource "aws_s3_bucket_replication_configuration" "this" {
  bucket = var.source_bucket_id
  role   = aws_iam_role.replication.arn

  rule {
    id       = var.replication_rule_id
    priority = var.replication_rule_priority
    status   = var.replication_enabled ? "Enabled" : "Disabled"

    filter {
      prefix = var.replication_filter_prefix
    }

    delete_marker_replication {
      status = var.delete_marker_replication_enabled ? "Enabled" : "Disabled"
    }

    destination {
      bucket        = var.destination_bucket_arn
      account       = var.destination_account_id
      storage_class = var.destination_storage_class

      dynamic "encryption_configuration" {
        for_each = var.destination_kms_key_arn == null ? [] : [var.destination_kms_key_arn]

        content {
          replica_kms_key_id = encryption_configuration.value
        }
      }

      dynamic "metrics" {
        for_each = var.metrics_enabled ? [true] : []

        content {
          status = "Enabled"

          event_threshold {
            minutes = var.replication_metrics_event_threshold_minutes
          }
        }
      }

      dynamic "replication_time" {
        for_each = var.replication_time_control_enabled ? [true] : []

        content {
          status = "Enabled"

          time {
            minutes = 15
          }
        }
      }
    }

    dynamic "source_selection_criteria" {
      for_each = var.source_kms_key_arn == null ? [] : [true]

      content {
        sse_kms_encrypted_objects {
          status = "Enabled"
        }
      }
    }
  }

  depends_on = [
    aws_iam_role_policy.replication
  ]

  lifecycle {
    precondition {
      condition = (
        var.source_bucket_id != "" &&
        var.source_bucket_arn != "" &&
        var.destination_bucket_arn != ""
      )

      error_message = "Source bucket ID, source bucket ARN, and destination bucket ARN must be provided."
    }

    precondition {
      condition = (
        !var.replication_time_control_enabled ||
        var.metrics_enabled
      )

      error_message = "S3 Replication Time Control requires replication metrics to be enabled."
    }

    precondition {
      condition = (
        var.source_kms_key_arn == null ||
        var.destination_kms_key_arn != null
      )

      error_message = "When replicating SSE-KMS encrypted source objects, a destination KMS key ARN must also be configured."
    }
  }
}
