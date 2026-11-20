resource "aws_s3_bucket" "raw_data" {
  bucket = "${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-raw"

  force_destroy = var.force_destroy_buckets

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-raw"
      DataPurpose = "raw-event-ingestion"
    }
  )

  lifecycle {
    precondition {
      condition     = length("${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-raw") <= 63
      error_message = "The generated raw data bucket name must not exceed 63 characters."
    }
  }
}

resource "aws_s3_bucket" "processed_data" {
  bucket = "${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-processed"

  force_destroy = var.force_destroy_buckets

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-processed"
      DataPurpose = "processed-event-data"
    }
  )

  lifecycle {
    precondition {
      condition     = length("${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-processed") <= 63
      error_message = "The generated processed data bucket name must not exceed 63 characters."
    }
  }
}

resource "aws_s3_bucket" "analytics" {
  bucket = "${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-analytics"

  force_destroy = var.force_destroy_buckets

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-analytics"
      DataPurpose = "analytics-and-query-results"
    }
  )

  lifecycle {
    precondition {
      condition     = length("${var.bucket_name_prefix}-${var.environment}-${var.bucket_name_suffix}-analytics") <= 63
      error_message = "The generated analytics bucket name must not exceed 63 characters."
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_ownership_controls" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_ownership_controls" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  versioning_configuration {
    status = var.enable_bucket_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_versioning" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  versioning_configuration {
    status = var.enable_bucket_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_versioning" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  versioning_configuration {
    status = var.enable_bucket_versioning ? "Enabled" : "Suspended"
  }
}