data "aws_iam_policy_document" "s3_upload_api_assume_role" {
  statement {
    sid     = "AllowEC2AssumeRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "s3_upload_api" {
  name               = "${var.project_name}-${var.environment}-s3-upload-api"
  assume_role_policy = data.aws_iam_policy_document.s3_upload_api_assume_role.json

  description = "Runtime role for the secure file upload API to access its S3 bucket and encryption key."

  tags = merge(var.tags, {
    Name        = "${var.project_name}-${var.environment}-s3-upload-api"
    Environment = var.environment
    ManagedBy   = "Terraform"
  })
}

data "aws_iam_policy_document" "s3_upload_api_access" {
  statement {
    sid    = "AllowObjectOperationsWithinUploadPrefix"
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:GetObjectTagging",
      "s3:PutObjectTagging"
    ]

    resources = [
      "${aws_s3_bucket.uploads.arn}/${var.s3_upload_prefix}*"
    ]
  }

  statement {
    sid    = "AllowBucketInspection"
    effect = "Allow"

    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.uploads.arn
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        var.s3_upload_prefix,
        "${var.s3_upload_prefix}*"
      ]
    }
  }

  statement {
    sid    = "AllowKMSOperationsForS3Encryption"
    effect = "Allow"

    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey"
    ]

    resources = [
      aws_kms_key.s3_encryption.arn
    ]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values = [
        "s3.${var.aws_region}.amazonaws.com"
      ]
    }
  }
}

resource "aws_iam_policy" "s3_upload_api_access" {
  name        = "${var.project_name}-${var.environment}-s3-upload-api-access"
  description = "Least-privilege S3 and KMS permissions for the secure file upload API."
  policy      = data.aws_iam_policy_document.s3_upload_api_access.json

  tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "Terraform"
  })
}

resource "aws_iam_role_policy_attachment" "s3_upload_api_access" {
  role       = aws_iam_role.s3_upload_api.name
  policy_arn = aws_iam_policy.s3_upload_api_access.arn
}