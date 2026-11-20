data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    sid     = "AllowLambdaServiceAssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ingestion_lambda" {
  name               = "${local.name_prefix}-ingestion-lambda"
  description        = "Execution role for the document ingestion Lambda."
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-ingestion-lambda"
    Component = "document-ingestion"
  })
}

resource "aws_iam_role" "processing_lambda" {
  name               = "${local.name_prefix}-processing-lambda"
  description        = "Execution role for the document processing Lambda."
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = merge(local.common_tags, {
    Name      = "${local.name_prefix}-processing-lambda"
    Component = "document-processing"
  })
}

resource "aws_iam_role_policy_attachment" "ingestion_lambda_execution" {
  role       = aws_iam_role.ingestion_lambda.name
  policy_arn = "arn:${local.aws_partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "processing_lambda_execution" {
  role       = aws_iam_role.processing_lambda.name
  policy_arn = "arn:${local.aws_partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "ingestion_lambda_access" {
  statement {
    sid    = "ReadUploadedDocuments"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion"
    ]

    resources = [
      "${aws_s3_bucket.documents.arn}/${trimsuffix(var.documents_upload_prefix, "/")}/*"
    ]
  }

  statement {
    sid    = "ReadDocumentBucketConfiguration"
    effect = "Allow"

    actions = [
      "s3:GetBucketLocation"
    ]

    resources = [
      aws_s3_bucket.documents.arn
    ]
  }

  statement {
    sid    = "WriteDocumentMetadata"
    effect = "Allow"

    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem"
    ]

    resources = [
      aws_dynamodb_table.document_metadata.arn
    ]
  }

  statement {
    sid    = "PublishProcessingMessages"
    effect = "Allow"

    actions = [
      "sqs:SendMessage"
    ]

    resources = [
      aws_sqs_queue.processing.arn
    ]
  }

  dynamic "statement" {
    for_each = var.s3_kms_key_arn == null ? [] : [var.s3_kms_key_arn]

    content {
      sid    = "DecryptUploadedDocumentsWithKms"
      effect = "Allow"

      actions = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]

      resources = [
        statement.value
      ]
    }
  }
}

resource "aws_iam_role_policy" "ingestion_lambda_access" {
  name   = "${local.name_prefix}-ingestion-access"
  role   = aws_iam_role.ingestion_lambda.id
  policy = data.aws_iam_policy_document.ingestion_lambda_access.json
}

data "aws_iam_policy_document" "processing_lambda_access" {
  statement {
    sid    = "ReadUploadedDocuments"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion"
    ]

    resources = [
      "${aws_s3_bucket.documents.arn}/*"
    ]
  }

  statement {
    sid    = "ReadDocumentMetadata"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:UpdateItem"
    ]

    resources = [
      aws_dynamodb_table.document_metadata.arn,
      "${aws_dynamodb_table.document_metadata.arn}/index/*"
    ]
  }

  statement {
    sid    = "ManageProcessingStatus"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]

    resources = [
      aws_dynamodb_table.processing_status.arn,
      "${aws_dynamodb_table.processing_status.arn}/index/*"
    ]
  }

  dynamic "statement" {
    for_each = var.s3_kms_key_arn == null ? [] : [var.s3_kms_key_arn]

    content {
      sid    = "DecryptUploadedDocumentsWithKms"
      effect = "Allow"

      actions = [
        "kms:Decrypt",
        "kms:DescribeKey"
      ]

      resources = [
        statement.value
      ]
    }
  }
}

resource "aws_iam_role_policy" "processing_lambda_access" {
  name   = "${local.name_prefix}-processing-access"
  role   = aws_iam_role.processing_lambda.id
  policy = data.aws_iam_policy_document.processing_lambda_access.json
}

data "aws_iam_policy_document" "processing_lambda_sqs_access" {
  statement {
    sid    = "ConsumeProcessingMessages"
    effect = "Allow"

    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]

    resources = [
      aws_sqs_queue.processing.arn
    ]
  }
}

resource "aws_iam_role_policy" "processing_lambda_sqs_access" {
  name   = "${local.name_prefix}-processing-sqs-consumer"
  role   = aws_iam_role.processing_lambda.id
  policy = data.aws_iam_policy_document.processing_lambda_sqs_access.json
}

data "aws_iam_policy_document" "api_document_access" {
  statement {
    sid    = "UploadAndManageDocuments"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:AbortMultipartUpload",
      "s3:GetObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${aws_s3_bucket.documents.arn}/${trimsuffix(var.documents_upload_prefix, "/")}/*"
    ]
  }

  statement {
    sid    = "ReadDocumentBucketConfiguration"
    effect = "Allow"

    actions = [
      "s3:GetBucketLocation"
    ]

    resources = [
      aws_s3_bucket.documents.arn
    ]
  }

  dynamic "statement" {
    for_each = var.s3_kms_key_arn == null ? [] : [var.s3_kms_key_arn]

    content {
      sid    = "UseKmsForDocumentEncryption"
      effect = "Allow"

      actions = [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey"
      ]

      resources = [
        statement.value
      ]
    }
  }
}

data "aws_iam_policy_document" "api_processing_status_access" {
  statement {
    sid    = "ReadProcessingStatus"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query"
    ]

    resources = [
      aws_dynamodb_table.processing_status.arn,
      "${aws_dynamodb_table.processing_status.arn}/index/*"
    ]
  }
}