variable "aws_region" {
  description = "AWS Region in which the document ingestion infrastructure is deployed."
  type        = string
  default     = "ap-south-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must be a valid AWS Region identifier."
  }
}

variable "environment" {
  description = "Deployment environment used in resource names and tags."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "name_prefix" {
  description = "Optional resource-name prefix. When null, the project name and environment are used."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.name_prefix == null ||
      (
        length(var.name_prefix) >= 3 &&
        length(var.name_prefix) <= 40 &&
        can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.name_prefix))
      )
    )
    error_message = "name_prefix must be 3-40 lowercase alphanumeric characters or hyphens, beginning and ending with an alphanumeric character."
  }
}

variable "documents_bucket_name" {
  description = "Optional globally unique S3 bucket name for uploaded documents. When null, the project derives a name from the project, environment, account, and Region."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.documents_bucket_name == null ||
      (
        length(var.documents_bucket_name) >= 3 &&
        length(var.documents_bucket_name) <= 63 &&
        can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.documents_bucket_name)) &&
        !can(regex("\\.\\.", var.documents_bucket_name)) &&
        !can(regex("\\.-|\\-\\.", var.documents_bucket_name)) &&
        !can(regex("^[0-9]{1,3}(\\.[0-9]{1,3}){3}$", var.documents_bucket_name))
      )
    )
    error_message = "documents_bucket_name must be a valid S3 general-purpose bucket name."
  }
}

variable "documents_upload_prefix" {
  description = "S3 key prefix used by the API for incoming document uploads."
  type        = string
  default     = "incoming"

  validation {
    condition = (
      length(trim(var.documents_upload_prefix, "/")) > 0 &&
      !strcontains(var.documents_upload_prefix, "\\") &&
      alltrue([
        for part in split("/", trim(var.documents_upload_prefix, "/")) :
        part != "" && part != "." && part != ".."
      ])
    )
    error_message = "documents_upload_prefix must contain valid non-empty S3 key-prefix segments."
  }
}

variable "metadata_table_name" {
  description = "Optional DynamoDB table name used by the ingestion Lambda to persist extracted document metadata."
  type        = string
  default     = null
  nullable    = true
}

variable "processing_status_table_name" {
  description = "Optional DynamoDB table name used by the API and processing workflow to track document processing status."
  type        = string
  default     = null
  nullable    = true
}

variable "processing_queue_name" {
  description = "Optional SQS queue name for document-processing events. The Terraform configuration derives a name when null."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.processing_queue_name == null ||
      (
        length(var.processing_queue_name) >= 1 &&
        length(var.processing_queue_name) <= 80 &&
        can(regex("^[A-Za-z0-9_-]+$", var.processing_queue_name))
      )
    )
    error_message = "processing_queue_name must contain only letters, numbers, hyphens, or underscores and be at most 80 characters."
  }
}

variable "processing_dead_letter_queue_name" {
  description = "Optional SQS dead-letter queue name. The Terraform configuration derives a name when null."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.processing_dead_letter_queue_name == null ||
      (
        length(var.processing_dead_letter_queue_name) >= 1 &&
        length(var.processing_dead_letter_queue_name) <= 80 &&
        can(regex("^[A-Za-z0-9_-]+$", var.processing_dead_letter_queue_name))
      )
    )
    error_message = "processing_dead_letter_queue_name must contain only letters, numbers, hyphens, or underscores and be at most 80 characters."
  }
}

variable "lambda_runtime" {
  description = "AWS Lambda runtime used by the ingestion and document-processing functions."
  type        = string
  default     = "python3.12"

  validation {
    condition     = contains(["python3.11", "python3.12", "python3.13"], var.lambda_runtime)
    error_message = "lambda_runtime must be a supported Python runtime selected by this project."
  }
}

variable "lambda_architecture" {
  description = "Instruction-set architecture used by the Lambda functions."
  type        = string
  default     = "arm64"

  validation {
    condition     = contains(["arm64", "x86_64"], var.lambda_architecture)
    error_message = "lambda_architecture must be arm64 or x86_64."
  }
}

variable "ingestion_lambda_timeout_seconds" {
  description = "Maximum execution time for the S3 ingestion Lambda."
  type        = number
  default     = 120

  validation {
    condition     = var.ingestion_lambda_timeout_seconds >= 1 && var.ingestion_lambda_timeout_seconds <= 900
    error_message = "ingestion_lambda_timeout_seconds must be between 1 and 900."
  }
}

variable "processing_lambda_timeout_seconds" {
  description = "Maximum execution time for the document-processing Lambda."
  type        = number
  default     = 300

  validation {
    condition     = var.processing_lambda_timeout_seconds >= 1 && var.processing_lambda_timeout_seconds <= 900
    error_message = "processing_lambda_timeout_seconds must be between 1 and 900."
  }
}

variable "ingestion_lambda_memory_mb" {
  description = "Memory allocation in MB for the ingestion Lambda."
  type        = number
  default     = 512

  validation {
    condition     = var.ingestion_lambda_memory_mb >= 128 && var.ingestion_lambda_memory_mb <= 10240
    error_message = "ingestion_lambda_memory_mb must be between 128 and 10240 MB."
  }
}

variable "processing_lambda_memory_mb" {
  description = "Memory allocation in MB for the document-processing Lambda."
  type        = number
  default     = 1024

  validation {
    condition     = var.processing_lambda_memory_mb >= 128 && var.processing_lambda_memory_mb <= 10240
    error_message = "processing_lambda_memory_mb must be between 128 and 10240 MB."
  }
}

variable "lambda_log_retention_days" {
  description = "CloudWatch Logs retention period for Lambda log groups."
  type        = number
  default     = 30

  validation {
    condition = contains(
      [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653],
      var.lambda_log_retention_days
    )
    error_message = "lambda_log_retention_days must be a supported CloudWatch Logs retention value."
  }
}

variable "processing_queue_visibility_timeout_seconds" {
  description = "Visibility timeout for the document-processing SQS queue. It should exceed the processing Lambda timeout."
  type        = number
  default     = 360

  validation {
    condition     = var.processing_queue_visibility_timeout_seconds >= 1 && var.processing_queue_visibility_timeout_seconds <= 43200
    error_message = "processing_queue_visibility_timeout_seconds must be between 1 and 43200."
  }
}

variable "processing_queue_message_retention_seconds" {
  description = "Retention period for messages in the document-processing SQS queue."
  type        = number
  default     = 345600

  validation {
    condition     = var.processing_queue_message_retention_seconds >= 60 && var.processing_queue_message_retention_seconds <= 1209600
    error_message = "processing_queue_message_retention_seconds must be between 60 and 1209600."
  }
}

variable "processing_queue_max_receive_count" {
  description = "Maximum number of receives before SQS moves a message to the dead-letter queue."
  type        = number
  default     = 5

  validation {
    condition     = var.processing_queue_max_receive_count >= 1 && var.processing_queue_max_receive_count <= 1000
    error_message = "processing_queue_max_receive_count must be between 1 and 1000."
  }
}

variable "enable_s3_versioning" {
  description = "Enable S3 bucket versioning to support recovery from accidental overwrites and deletions."
  type        = bool
  default     = true
}

variable "enable_s3_event_notifications" {
  description = "Enable S3 ObjectCreated notifications for the ingestion Lambda."
  type        = bool
  default     = true
}

variable "enable_s3_server_access_logging" {
  description = "Enable S3 server access logging when a dedicated logging destination is configured."
  type        = bool
  default     = false
}

variable "s3_noncurrent_version_expiration_days" {
  description = "Number of days before noncurrent document versions become eligible for lifecycle expiration. Null disables this lifecycle setting."
  type        = number
  default     = null
  nullable    = true

  validation {
    condition = (
      var.s3_noncurrent_version_expiration_days == null ||
      var.s3_noncurrent_version_expiration_days >= 1
    )
    error_message = "s3_noncurrent_version_expiration_days must be null or at least 1."
  }
}

variable "s3_incomplete_multipart_upload_expiration_days" {
  description = "Number of days after which incomplete multipart uploads are aborted."
  type        = number
  default     = 7

  validation {
    condition     = var.s3_incomplete_multipart_upload_expiration_days >= 1
    error_message = "s3_incomplete_multipart_upload_expiration_days must be at least 1."
  }
}

variable "s3_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN for SSE-KMS encryption. When null, S3-managed encryption is used."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      var.s3_kms_key_arn == null ||
      can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/.+$", var.s3_kms_key_arn))
    )
    error_message = "s3_kms_key_arn must be a valid customer-managed KMS key ARN or null."
  }
}

variable "api_allowed_origins" {
  description = "Explicit browser origins allowed by the FastAPI CORS configuration. Keep empty when browser-based cross-origin access is not required."
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for origin in var.api_allowed_origins :
      can(regex("^https?://[^/]+$", origin))
    ])
    error_message = "Each api_allowed_origins entry must be an HTTP or HTTPS origin without a path."
  }
}

variable "api_log_level" {
  description = "Application log level passed to the API runtime."
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], upper(var.api_log_level))
    error_message = "api_log_level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL."
  }
}

variable "enable_deletion_protection" {
  description = "Enable resource deletion protection where supported by the configured infrastructure resources."
  type        = bool
  default     = true
}

variable "force_destroy_documents_bucket" {
  description = "Allow Terraform to delete a non-empty documents bucket, including object versions. Keep false for production environments."
  type        = bool
  default     = false
}