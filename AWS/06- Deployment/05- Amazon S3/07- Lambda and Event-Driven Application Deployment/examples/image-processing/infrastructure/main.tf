# ---------------------------------------------------------------------------
# Terraform and Provider Configuration
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.80, < 7.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">= 3.6, < 4.0"
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
      Component   = "S3ImageProcessing"
    }
  }
}

# ---------------------------------------------------------------------------
# Input Variables
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS Region in which the image-processing infrastructure is deployed."
  type        = string

  validation {
    condition     = length(trimspace(var.aws_region)) > 0
    error_message = "aws_region must not be empty."
  }
}

variable "project_name" {
  description = "Project identifier used to construct resource names and tags."
  type        = string
  default     = "s3-image-processing"

  validation {
    condition     = length(trimspace(var.project_name)) >= 3
    error_message = "project_name must contain at least three characters."
  }
}

variable "environment" {
  description = "Deployment environment, such as dev, staging, or production."
  type        = string
  default     = "dev"

  validation {
    condition     = length(trimspace(var.environment)) > 0
    error_message = "environment must not be empty."
  }
}

variable "input_prefix" {
  description = "S3 object-key prefix that identifies original images."
  type        = string
  default     = "uploads/"

  validation {
    condition     = length(trimspace(var.input_prefix)) > 0 && !startswith(var.input_prefix, "/")
    error_message = "input_prefix must be non-empty and must not start with a slash."
  }
}

variable "output_prefix" {
  description = "S3 object-key prefix used for generated thumbnails."
  type        = string
  default     = "thumbnails/"

  validation {
    condition     = length(trimspace(var.output_prefix)) > 0 && !startswith(var.output_prefix, "/")
    error_message = "output_prefix must be non-empty and must not start with a slash."
  }
}

variable "enable_bucket_versioning" {
  description = "Whether versioning is enabled on the input and output buckets."
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days."
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180,
      365, 400, 545, 731, 1096, 1827, 2192, 2557,
      2922, 3288, 3653
    ], var.log_retention_days)
    error_message = "log_retention_days must be a supported CloudWatch Logs retention value."
  }
}

variable "lambda_runtime" {
  description = "AWS Lambda runtime for the image-processing function."
  type        = string
  default     = "python3.12"

  validation {
    condition     = startswith(var.lambda_runtime, "python")
    error_message = "lambda_runtime must specify a Python runtime."
  }
}

variable "lambda_architecture" {
  description = "Instruction-set architecture used by the Lambda deployment package."
  type        = string
  default     = "arm64"

  validation {
    condition     = contains(["arm64", "x86_64"], var.lambda_architecture)
    error_message = "lambda_architecture must be arm64 or x86_64."
  }
}

variable "lambda_package_path" {
  description = "Path to the pre-built Lambda deployment ZIP archive, relative to the Terraform working directory."
  type        = string

  validation {
    condition     = length(trimspace(var.lambda_package_path)) > 0
    error_message = "lambda_package_path must identify the Lambda deployment archive."
  }
}

variable "lambda_timeout" {
  description = "Maximum execution duration of the image-processing Lambda function in seconds."
  type        = number
  default     = 60

  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "lambda_timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_memory_size" {
  description = "Memory allocated to the image-processing Lambda function in MB."
  type        = number
  default     = 1024

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240 && var.lambda_memory_size % 1 == 0
    error_message = "lambda_memory_size must be a whole number between 128 and 10240 MB."
  }
}

variable "lambda_max_retry_attempts" {
  description = "Number of retries for failed asynchronous Lambda invocations."
  type        = number
  default     = 2

  validation {
    condition     = var.lambda_max_retry_attempts >= 0 && var.lambda_max_retry_attempts <= 2 && var.lambda_max_retry_attempts % 1 == 0
    error_message = "lambda_max_retry_attempts must be 0, 1, or 2."
  }
}

variable "failure_queue_retention_seconds" {
  description = "Message retention period for the Lambda asynchronous failure destination queue."
  type        = number
  default     = 1209600

  validation {
    condition     = var.failure_queue_retention_seconds >= 60 && var.failure_queue_retention_seconds <= 1209600
    error_message = "failure_queue_retention_seconds must be between 60 and 1209600 seconds."
  }
}

variable "max_input_size_mb" {
  description = "Maximum accepted input image size in MB."
  type        = number
  default     = 10

  validation {
    condition     = var.max_input_size_mb > 0
    error_message = "max_input_size_mb must be greater than zero."
  }
}

variable "thumbnail_max_width" {
  description = "Maximum generated thumbnail width in pixels."
  type        = number
  default     = 1280

  validation {
    condition     = var.thumbnail_max_width > 0 && var.thumbnail_max_width % 1 == 0
    error_message = "thumbnail_max_width must be a positive whole number."
  }
}

variable "thumbnail_max_height" {
  description = "Maximum generated thumbnail height in pixels."
  type        = number
  default     = 1280

  validation {
    condition     = var.thumbnail_max_height > 0 && var.thumbnail_max_height % 1 == 0
    error_message = "thumbnail_max_height must be a positive whole number."
  }
}

variable "max_image_pixels" {
  description = "Maximum decoded image pixel count accepted by the image transformer."
  type        = number
  default     = 40000000

  validation {
    condition     = var.max_image_pixels > 0 && var.max_image_pixels % 1 == 0
    error_message = "max_image_pixels must be a positive whole number."
  }
}

# ---------------------------------------------------------------------------
# AWS Account and Region Context
#
# These data sources are shared by IAM trust policies and Lambda invocation
# permissions. Each is declared once in the root module.
# ---------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

data "aws_region" "current" {}

# ---------------------------------------------------------------------------
# Shared Resource Naming and Tags
# ---------------------------------------------------------------------------

locals {
  name_prefix = trimsuffix(
    substr(
      trim(
        replace(
          lower("${var.project_name}-${var.environment}"),
          "/[^a-z0-9-]/",
          "-"
        ),
        "-"
      ),
      0,
      40
    ),
    "-"
  )

  input_bucket_name  = "${local.name_prefix}-input"
  output_bucket_name = "${local.name_prefix}-output"

  lambda_function_name = "${local.name_prefix}-image-processor"
  failure_queue_name   = "${local.name_prefix}-lambda-failures"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Component   = "S3ImageProcessing"
  }
}

# ---------------------------------------------------------------------------
# Unique Bucket Suffix
#
# S3 bucket names are globally unique. A random suffix reduces the likelihood
# of collisions between deployments using the same project and environment.
# ---------------------------------------------------------------------------

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# ---------------------------------------------------------------------------
# S3 Input Bucket Notification
#
# S3 invokes Lambda directly for object-created events under the configured
# input prefix. The output bucket is separate, preventing recursive
# processing of generated thumbnails.
#
# The Lambda permission is declared in lambda.tf.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket_notification" "input" {
  bucket = aws_s3_bucket.input.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.image_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = var.input_prefix
  }

  depends_on = [
    aws_lambda_permission.allow_s3_invocation
  ]
}