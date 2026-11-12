terraform {
  required_version = ">= 1.5.0"
}

locals {
  common_tags = merge(
    {
      ManagedBy = "Terraform"
      Component = "s3-security"
    },
    var.tags
  )
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket = var.bucket_id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = var.bucket_id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }

  depends_on = [
    aws_s3_bucket_public_access_block.this
  ]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = var.bucket_id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }

    bucket_key_enabled = var.kms_key_arn != null ? var.bucket_key_enabled : false
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = var.bucket_id
  policy = data.aws_iam_policy_document.this.json

  depends_on = [
    aws_s3_bucket_public_access_block.this
  ]
}

data "aws_iam_policy_document" "this" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:*"
    ]

    resources = [
      var.bucket_arn,
      "${var.bucket_arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }

  dynamic "statement" {
    for_each = var.enforce_encryption_header ? [1] : []

    content {
      sid    = "DenyUnencryptedObjectUploads"
      effect = "Deny"

      principals {
        type        = "*"
        identifiers = ["*"]
      }

      actions = [
        "s3:PutObject"
      ]

      resources = [
        "${var.bucket_arn}/*"
      ]

      condition {
        test     = "Null"
        variable = "s3:x-amz-server-side-encryption"
        values   = ["true"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.enforce_encryption_header && var.kms_key_arn != null ? [1] : []

    content {
      sid    = "DenyIncorrectEncryptionAlgorithm"
      effect = "Deny"

      principals {
        type        = "*"
        identifiers = ["*"]
      }

      actions = [
        "s3:PutObject"
      ]

      resources = [
        "${var.bucket_arn}/*"
      ]

      condition {
        test     = "StringNotEquals"
        variable = "s3:x-amz-server-side-encryption"
        values   = ["aws:kms"]
      }
    }
  }

  dynamic "statement" {
    for_each = var.enforce_encryption_header && var.kms_key_arn != null ? [1] : []

    content {
      sid    = "DenyIncorrectKmsKey"
      effect = "Deny"

      principals {
        type        = "*"
        identifiers = ["*"]
      }

      actions = [
        "s3:PutObject"
      ]

      resources = [
        "${var.bucket_arn}/*"
      ]

      condition {
        test     = "StringNotEquals"
        variable = "s3:x-amz-server-side-encryption-aws-kms-key-id"
        values   = [var.kms_key_arn]
      }
    }
  }

  dynamic "statement" {
    for_each = var.allowed_principal_arns

    content {
      sid    = "AllowConfiguredPrincipal${substr(sha1(statement.value), 0, 12)}"
      effect = "Allow"

      principals {
        type        = "AWS"
        identifiers = [statement.value]
      }

      actions = var.allowed_actions

      resources = concat(
        contains(var.allowed_actions, "s3:ListBucket") ||
        contains(var.allowed_actions, "s3:ListBucketVersions") ||
        contains(var.allowed_actions, "s3:GetBucketLocation") ? [var.bucket_arn] : [],
        contains(var.allowed_actions, "s3:*") ||
        contains(var.allowed_actions, "s3:GetObject") ||
        contains(var.allowed_actions, "s3:GetObjectVersion") ||
        contains(var.allowed_actions, "s3:PutObject") ||
        contains(var.allowed_actions, "s3:DeleteObject") ||
        contains(var.allowed_actions, "s3:DeleteObjectVersion") ? ["${var.bucket_arn}/*"] : []
      )
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "this" {
  count = length(var.cors_rules) > 0 ? 1 : 0

  bucket = var.bucket_id

  dynamic "cors_rule" {
    for_each = var.cors_rules

    content {
      id              = try(cors_rule.value.id, null)
      allowed_headers = try(cors_rule.value.allowed_headers, ["*"])
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = try(cors_rule.value.expose_headers, [])
      max_age_seconds = try(cors_rule.value.max_age_seconds, 3000)
    }
  }
}

resource "aws_s3_bucket_request_payment_configuration" "this" {
  count = var.request_payer_enabled ? 1 : 0

  bucket = var.bucket_id
  payer  = "Requester"
}
