locals {
  document_metadata_table_name = "${local.name_prefix}-document-metadata"
  processing_status_table_name = "${local.name_prefix}-processing-status"
}

resource "aws_dynamodb_table" "document_metadata" {
  name         = local.document_metadata_table_name
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "object_id"

  attribute {
    name = "object_id"
    type = "S"
  }

  attribute {
    name = "bucket_name"
    type = "S"
  }

  attribute {
    name = "object_key"
    type = "S"
  }

  global_secondary_index {
    name            = "bucket-object-key-index"
    hash_key        = "bucket_name"
    range_key       = "object_key"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  deletion_protection_enabled = var.enable_deletion_protection

  tags = merge(local.common_tags, {
    Name      = local.document_metadata_table_name
    Component = "document-ingestion"
    Purpose   = "DocumentMetadata"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_dynamodb_table" "processing_status" {
  name         = local.processing_status_table_name
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "object_id"
  range_key = "created_at"

  attribute {
    name = "object_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  attribute {
    name = "processing_status"
    type = "S"
  }

  global_secondary_index {
    name            = "processing-status-index"
    hash_key        = "processing_status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  deletion_protection_enabled = var.enable_deletion_protection

  tags = merge(local.common_tags, {
    Name      = local.processing_status_table_name
    Component = "document-processing"
    Purpose   = "ProcessingStatus"
  })

  lifecycle {
    prevent_destroy = true
  }
}