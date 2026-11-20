resource "aws_athena_workgroup" "data_lake" {
  count = var.enable_athena_workgroup ? 1 : 0

  name        = var.athena_workgroup_name
  description = "Athena workgroup for querying the data lake event datasets."

  state = "ENABLED"

  force_destroy = false

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    bytes_scanned_cutoff_per_query = var.athena_bytes_scanned_cutoff_per_query

    engine_version {
      selected_engine_version = var.athena_engine_version
    }

    result_configuration {
      output_location = "s3://${aws_s3_bucket.analytics.bucket}/${trim(var.analytics_data_prefix, "/")}/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = aws_kms_key.data_lake.arn
      }
    }
  }

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${local.project_name}-${var.environment}-athena"
      DataPurpose = "data-lake-query-execution"
    }
  )

  depends_on = [
    aws_s3_bucket_server_side_encryption_configuration.analytics,
    aws_s3_bucket_public_access_block.analytics
  ]

  lifecycle {
    precondition {
      condition = (
        var.enable_glue_catalog ||
        !var.enable_athena_workgroup
      )
      error_message = "The Athena workgroup requires the Glue catalog to be enabled for this project."
    }

    precondition {
      condition = (
        length(trim(var.analytics_data_prefix, "/")) > 0
      )
      error_message = "The analytics data prefix must not be empty."
    }
  }
}