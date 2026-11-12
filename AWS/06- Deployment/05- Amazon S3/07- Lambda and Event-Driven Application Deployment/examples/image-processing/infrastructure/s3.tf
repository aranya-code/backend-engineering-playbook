# ---------------------------------------------------------------------------
# S3 Input Bucket
#
# Stores original images uploaded by clients.
# Only objects created under var.input_prefix generate Lambda events.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "input" {
  bucket        = "${local.input_bucket_name}-${random_id.bucket_suffix.hex}"
  force_destroy = false

  tags = merge(local.common_tags, {
    Name      = "${local.input_bucket_name}-${random_id.bucket_suffix.hex}"
    Purpose   = "image-input"
    Component = "image-processing"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "input" {
  bucket = aws_s3_bucket.input.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "input" {
  bucket = aws_s3_bucket.input.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "input" {
  bucket = aws_s3_bucket.input.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_versioning" "input" {
  bucket = aws_s3_bucket.input.id

  versioning_configuration {
    status = var.enable_bucket_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "input" {
  bucket = aws_s3_bucket.input.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.input
  ]
}

data "aws_iam_policy_document" "input_bucket" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.input.arn,
      "${aws_s3_bucket.input.arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "input" {
  bucket = aws_s3_bucket.input.id
  policy = data.aws_iam_policy_document.input_bucket.json

  depends_on = [
    aws_s3_bucket_public_access_block.input
  ]
}

# ---------------------------------------------------------------------------
# S3 Output Bucket
#
# Stores generated thumbnails. Keeping the output bucket separate from the
# input bucket prevents the Lambda function from recursively processing
# objects that it creates.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "output" {
  bucket        = "${local.output_bucket_name}-${random_id.bucket_suffix.hex}"
  force_destroy = false

  tags = merge(local.common_tags, {
    Name      = "${local.output_bucket_name}-${random_id.bucket_suffix.hex}"
    Purpose   = "image-output"
    Component = "image-processing"
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "output" {
  bucket = aws_s3_bucket.output.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_versioning" "output" {
  bucket = aws_s3_bucket.output.id

  versioning_configuration {
    status = var.enable_bucket_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.output
  ]
}

data "aws_iam_policy_document" "output_bucket" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.output.arn,
      "${aws_s3_bucket.output.arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "output" {
  bucket = aws_s3_bucket.output.id
  policy = data.aws_iam_policy_document.output_bucket.json

  depends_on = [
    aws_s3_bucket_public_access_block.output
  ]
}