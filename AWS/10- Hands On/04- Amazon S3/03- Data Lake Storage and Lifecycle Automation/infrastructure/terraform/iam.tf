data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  data_lake_bucket_arns = [
    aws_s3_bucket.raw_data.arn,
    aws_s3_bucket.processed_data.arn,
    aws_s3_bucket.analytics.arn
  ]

  raw_data_object_arn       = "${aws_s3_bucket.raw_data.arn}/${trim(var.raw_data_prefix, "/")}/*"
  processed_data_object_arn = "${aws_s3_bucket.processed_data.arn}/${trim(var.processed_data_prefix, "/")}/*"
  analytics_object_arn      = "${aws_s3_bucket.analytics.arn}/${trim(var.analytics_data_prefix, "/")}/*"

  athena_results_object_arn = "${aws_s3_bucket.analytics.arn}/${trim(var.analytics_data_prefix, "/")}/athena-results/*"

  glue_catalog_arn = "arn:${data.aws_partition.current.partition}:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog"
  glue_database_arn = "arn:${data.aws_partition.current.partition}:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${var.glue_database_name}"
  glue_table_arn = "arn:${data.aws_partition.current.partition}:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.glue_database_name}/${var.glue_table_name}"

  athena_workgroup_arn = "arn:${data.aws_partition.current.partition}:athena:${var.aws_region}:${data.aws_caller_identity.current.account_id}:workgroup/${var.athena_workgroup_name}"
}

data "aws_iam_policy_document" "data_lake_access" {
  statement {
    sid    = "ListDataLakeBuckets"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]

    resources = local.data_lake_bucket_arns

    condition {
      test     = "StringLike"
      variable = "s3:prefix"

      values = [
        "${trim(var.raw_data_prefix, "/")}/*",
        "${trim(var.processed_data_prefix, "/")}/*",
        "${trim(var.analytics_data_prefix, "/")}/*"
      ]
    }
  }

  statement {
    sid    = "ReadRawAndProcessedData"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion"
    ]

    resources = [
      local.raw_data_object_arn,
      local.processed_data_object_arn
    ]
  }

  statement {
    sid    = "WriteProcessedData"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts"
    ]

    resources = [
      local.processed_data_object_arn
    ]
  }

  statement {
    sid    = "ReadAndWriteAthenaResults"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:AbortMultipartUpload",
      "s3:ListMultipartUploadParts"
    ]

    resources = [
      local.athena_results_object_arn
    ]
  }

  statement {
    sid    = "ListAthenaResultPrefix"
    effect = "Allow"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.analytics.arn
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"

      values = [
        "${trim(var.analytics_data_prefix, "/")}/athena-results",
        "${trim(var.analytics_data_prefix, "/")}/athena-results/*"
      ]
    }
  }

  statement {
    sid    = "UseDataLakeKmsKey"
    effect = "Allow"

    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey"
    ]

    resources = [
      aws_kms_key.data_lake.arn
    ]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"

      values = [
        "s3.${var.aws_region}.${data.aws_partition.current.dns_suffix}"
      ]
    }
  }

  statement {
    sid    = "ReadGlueCatalog"
    effect = "Allow"

    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetPartition",
      "glue:GetPartitions"
    ]

    resources = [
      local.glue_catalog_arn,
      local.glue_database_arn,
      local.glue_table_arn
    ]
  }

  statement {
    sid    = "ExecuteAthenaQueries"
    effect = "Allow"

    actions = [
      "athena:StartQueryExecution",
      "athena:StopQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:GetWorkGroup"
    ]

    resources = [
      local.athena_workgroup_arn
    ]
  }
}

resource "aws_iam_policy" "data_lake_access" {
  name        = "${local.project_name}-${var.environment}-access"
  description = "Scoped S3, KMS, Glue Catalog, and Athena permissions for data lake application consumers."
  policy      = data.aws_iam_policy_document.data_lake_access.json

  tags = merge(
    local.common_tags,
    var.additional_tags,
    {
      Name        = "${local.project_name}-${var.environment}-access"
      DataPurpose = "data-lake-access"
    }
  )
}

data "aws_iam_policy_document" "athena_query_results" {
  count = var.enable_athena_workgroup ? 1 : 0

  statement {
    sid    = "AllowAthenaServiceToUseResultsKey"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["athena.amazonaws.com"]
    }

    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey"
    ]

    resources = [
      "*"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"

      values = [
        data.aws_caller_identity.current.account_id
      ]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"

      values = [
        local.athena_workgroup_arn
      ]
    }
  }
}

resource "aws_kms_key_policy" "data_lake" {
  key_id = aws_kms_key.data_lake.key_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableAccountIAMPolicies"
        Effect = "Allow"
        Principal = {
          AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowAthenaQueryResultEncryption"
        Effect = "Allow"
        Principal = {
          Service = "athena.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = local.athena_workgroup_arn
          }
        }
      }
    ]
  })

  depends_on = [
    aws_kms_key.data_lake
  ]
}