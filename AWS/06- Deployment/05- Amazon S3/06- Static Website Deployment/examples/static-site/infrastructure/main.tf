terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.80, < 7.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Component   = "StaticWebsite"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_canonical_user_id" "current" {}

locals {
  bucket_name = substr(
    replace(
      lower("${var.project_name}-${var.environment}-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}"),
      "/[^a-z0-9-]/",
      "-"
    ),
    0,
    63
  )

  origin_id = "s3-${local.bucket_name}"

  cloudfront_aliases = var.domain_names

  has_custom_domain = length(local.cloudfront_aliases) > 0

  logging_bucket_name = substr(
    replace(
      lower("${var.project_name}-${var.environment}-cloudfront-logs-${data.aws_caller_identity.current.account_id}-${data.aws_region.current.name}"),
      "/[^a-z0-9-]/",
      "-"
    ),
    0,
    63
  )
}

# ---------------------------------------------------------------------------
# Private S3 origin
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "website" {
  bucket = local.bucket_name

  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_ownership_controls" "website" {
  bucket = aws_s3_bucket.website.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "website" {
  bucket = aws_s3_bucket.website.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }

    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id

  policy = data.aws_iam_policy_document.website_bucket.json

  depends_on = [
    aws_s3_bucket_public_access_block.website,
    aws_s3_bucket_ownership_controls.website
  ]
}

data "aws_iam_policy_document" "website_bucket" {
  statement {
    sid    = "AllowCloudFrontReadOnlyAccess"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.website.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"

      values = [
        aws_cloudfront_distribution.website.arn
      ]
    }
  }

  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:*"
    ]

    resources = [
      aws_s3_bucket.website.arn,
      "${aws_s3_bucket.website.arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"

      values = [
        "false"
      ]
    }
  }
}

# ---------------------------------------------------------------------------
# CloudFront Origin Access Control
# ---------------------------------------------------------------------------

resource "aws_cloudfront_origin_access_control" "website" {
  name                              = "${var.project_name}-${var.environment}-s3-oac"
  description                       = "Restrict S3 origin access to the website CloudFront distribution"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ---------------------------------------------------------------------------
# Optional CloudFront access logging bucket
#
# CloudFront legacy standard logging requires ACL support. The website bucket
# remains BucketOwnerEnforced; ACLs are enabled only on this separate bucket.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  bucket = local.logging_bucket_name

  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_ownership_controls" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  bucket = aws_s3_bucket.cloudfront_logs[0].id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  bucket = aws_s3_bucket.cloudfront_logs[0].id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  bucket = aws_s3_bucket.cloudfront_logs[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  bucket = aws_s3_bucket.cloudfront_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_acl" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  bucket = aws_s3_bucket.cloudfront_logs[0].id

  access_control_policy {
    owner {
      id = data.aws_canonical_user_id.current.id
    }

    grant {
      grantee {
        type = "CanonicalUser"
        id   = data.aws_cloudfront_log_delivery_canonical_user_id.current.id
      }

      permission = "FULL_CONTROL"
    }

    grant {
      grantee {
        type = "Group"
        uri  = "http://acs.amazonaws.com/groups/s3/LogDelivery"
      }

      permission = "WRITE"
    }

    grant {
      grantee {
        type = "Group"
        uri  = "http://acs.amazonaws.com/groups/s3/LogDelivery"
      }

      permission = "READ_ACP"
    }
  }

  depends_on = [
    aws_s3_bucket_ownership_controls.cloudfront_logs,
    aws_s3_bucket_public_access_block.cloudfront_logs
  ]
}

data "aws_cloudfront_log_delivery_canonical_user_id" "current" {
  count = var.enable_access_logs ? 1 : 0
}

resource "aws_s3_bucket_policy" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  bucket = aws_s3_bucket.cloudfront_logs[0].id

  policy = data.aws_iam_policy_document.cloudfront_logs[0].json

  depends_on = [
    aws_s3_bucket_public_access_block.cloudfront_logs,
    aws_s3_bucket_acl.cloudfront_logs
  ]
}

data "aws_iam_policy_document" "cloudfront_logs" {
  count = var.enable_access_logs ? 1 : 0

  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:*"
    ]

    resources = [
      aws_s3_bucket.cloudfront_logs[0].arn,
      "${aws_s3_bucket.cloudfront_logs[0].arn}/*"
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"

      values = [
        "false"
      ]
    }
  }
}

# ---------------------------------------------------------------------------
# CloudFront security response headers
# ---------------------------------------------------------------------------

resource "aws_cloudfront_response_headers_policy" "security" {
  name    = "${var.project_name}-${var.environment}-security-headers"
  comment = "Security headers for the static website"

  security_headers_config {
    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }

    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = false
      override                   = true
    }

    xss_protection {
      mode_block = true
      protection = true
      override   = true
    }
  }

  custom_headers_config {
    items {
      header   = "Permissions-Policy"
      value    = "camera=(), microphone=(), geolocation=()"
      override = true
    }
  }
}

# ---------------------------------------------------------------------------
# CloudFront distribution
# ---------------------------------------------------------------------------

resource "aws_cloudfront_distribution" "website" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name} ${var.environment} static website"
  default_root_object = "index.html"
  price_class         = var.cloudfront_price_class

  aliases = local.cloudfront_aliases

  origin {
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_id                = local.origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.website.id
  }

  default_cache_behavior {
    target_origin_id       = local.origin_id
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = [
      "GET",
      "HEAD",
      "OPTIONS"
    ]

    cached_methods = [
      "GET",
      "HEAD",
      "OPTIONS"
    ]

    # AWS managed CachingOptimized policy.
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"

    response_headers_policy_id = aws_cloudfront_response_headers_policy.security.id

    compress = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = !local.has_custom_domain

    acm_certificate_arn = local.has_custom_domain ? var.acm_certificate_arn : null

    ssl_support_method       = local.has_custom_domain ? "sni-only" : null
    minimum_protocol_version = local.has_custom_domain ? "TLSv1.2_2021" : null
  }

  dynamic "logging_config" {
    for_each = var.enable_access_logs ? [1] : []

    content {
      bucket          = aws_s3_bucket.cloudfront_logs[0].bucket_domain_name
      prefix          = "cloudfront/"
      include_cookies = false
    }
  }

  # The S3 bucket policy references this distribution's ARN to restrict
  # CloudFront access to this distribution. Do not make the distribution
  # depend on that policy; doing so would create a dependency cycle.
  #
  # The logging ACL is independent of the website bucket policy and remains
  # an explicit prerequisite when access logging is enabled.
  depends_on = [
    aws_s3_bucket_acl.cloudfront_logs
  ]

  lifecycle {
    prevent_destroy = true

    precondition {
      condition = (
        !local.has_custom_domain ||
        (
          var.acm_certificate_arn != null &&
          trimspace(var.acm_certificate_arn) != ""
        )
      )

      error_message = "A valid ACM certificate ARN in us-east-1 is required when custom domain names are configured."
    }
  }
}