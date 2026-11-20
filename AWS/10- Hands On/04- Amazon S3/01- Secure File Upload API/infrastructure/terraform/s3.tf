resource "aws_s3_bucket" "uploads" {
  bucket        = local.s3_bucket_name
  force_destroy = false

  tags = merge(local.common_tags, {
    Name = local.s3_bucket_name
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_ownership_controls" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_encryption.arn
    }

    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_object_lock_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    default_retention {
      mode = "GOVERNANCE"
      days = var.object_lock_retention_days
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.uploads
  ]
}

resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = var.abort_incomplete_multipart_upload_days
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {
      prefix = local.s3_upload_prefix
    }

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_expiration_days
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.uploads
  ]
}