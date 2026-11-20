resource "random_id" "documents_bucket_suffix" {
  byte_length = 4
}

locals {
  generated_documents_bucket_name = join("-", [
    "doc-ingest",
    var.environment,
    local.aws_account_id,
    random_id.documents_bucket_suffix.hex
  ])

  documents_bucket_name = (
    var.documents_bucket_name != null
    ? var.documents_bucket_name
    : local.generated_documents_bucket_name
  )
}

resource "aws_s3_bucket" "documents" {
  bucket        = local.documents_bucket_name
  force_destroy = var.force_destroy_documents_bucket

  tags = merge(
    local.common_tags,
    {
      Name        = local.documents_bucket_name
      DataPurpose = "DocumentStorage"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = var.enable_s3_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.s3_kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.s3_kms_key_arn
    }

    bucket_key_enabled = var.s3_kms_key_arn != null
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = var.s3_incomplete_multipart_upload_expiration_days
    }
  }

  dynamic "rule" {
    for_each = (
      var.enable_s3_versioning &&
      var.s3_noncurrent_version_expiration_days != null
    ) ? [var.s3_noncurrent_version_expiration_days] : []

    content {
      id     = "expire-noncurrent-document-versions"
      status = "Enabled"

      filter {}

      noncurrent_version_expiration {
        noncurrent_days = rule.value
      }
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.documents
  ]
}

resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.documents.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyInsecureTransport"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })

  depends_on = [
    aws_s3_bucket_public_access_block.documents,
    aws_s3_bucket_ownership_controls.documents
  ]
}