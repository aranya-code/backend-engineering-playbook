resource "aws_kms_key" "s3_encryption" {
  description             = "KMS key for encrypting secure file upload API objects in S3"
  enable_key_rotation     = true
  deletion_window_in_days = var.kms_key_deletion_window_days
  is_enabled              = true
  key_usage               = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"

  tags = merge(var.tags, {
    Name        = "${var.project_name}-s3-encryption"
    Environment = var.environment
    ManagedBy   = "Terraform"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "s3_encryption" {
  name          = "alias/${var.project_name}-${var.environment}-s3"
  target_key_id = aws_kms_key.s3_encryption.key_id
}