resource "aws_kms_key" "data_lake" {
  description             = "Customer-managed KMS key for the data lake S3 buckets."
  deletion_window_in_days = var.kms_key_deletion_window_in_days
  enable_key_rotation     = var.kms_key_rotation_enabled
  is_enabled              = true
  key_usage               = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${local.project_name}-${var.environment}-s3-encryption"
      DataPurpose = "data-lake-s3-encryption"
    }
  )

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "data_lake" {
  name          = "alias/${local.project_name}-${var.environment}"
  target_key_id = aws_kms_key.data_lake.key_id
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data_lake.arn
    }

    bucket_key_enabled = var.enable_bucket_key && var.enable_s3_bucket_keys
  }

  depends_on = [
    aws_s3_bucket_public_access_block.raw_data
  ]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed_data" {
  bucket = aws_s3_bucket.processed_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data_lake.arn
    }

    bucket_key_enabled = var.enable_bucket_key && var.enable_s3_bucket_keys
  }

  depends_on = [
    aws_s3_bucket_public_access_block.processed_data
  ]
}

resource "aws_s3_bucket_server_side_encryption_configuration" "analytics" {
  bucket = aws_s3_bucket.analytics.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.data_lake.arn
    }

    bucket_key_enabled = var.enable_bucket_key && var.enable_s3_bucket_keys
  }

  depends_on = [
    aws_s3_bucket_public_access_block.analytics
  ]
}