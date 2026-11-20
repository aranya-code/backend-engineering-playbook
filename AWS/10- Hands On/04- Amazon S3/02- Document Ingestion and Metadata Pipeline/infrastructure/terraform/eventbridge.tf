resource "aws_cloudwatch_event_rule" "document_ingestion" {
  name        = "${local.name_prefix}-document-ingestion"
  description = "Matches S3 object-created events for the document ingestion pipeline."

  event_pattern = jsonencode({
    source = [
      "aws.s3"
    ]

    detail-type = [
      "Object Created"
    ]

    detail = {
      bucket = {
        name = [
          aws_s3_bucket.documents.bucket
        ]
      }

      object = {
        key = [
          {
            prefix = var.documents_upload_prefix
          }
        ]
      }
    }
  })

  state = var.enable_s3_event_notifications ? "ENABLED" : "DISABLED"

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-document-ingestion"
    Component = "document-ingestion"
    Purpose   = "S3ObjectCreatedEventRouting"
  })
}

resource "aws_cloudwatch_event_archive" "document_ingestion" {
  name             = "${local.name_prefix}-document-ingestion-archive"
  event_source_arn = "arn:${local.aws_partition}:events:${local.aws_region}:${local.aws_account_id}:event-bus/default"
  description      = "Retains matching document-ingestion events for investigation and replay."

  event_pattern = aws_cloudwatch_event_rule.document_ingestion.event_pattern

  retention_days = 7
}