variable "aws_region" {
  description = "AWS region in which the S3 buckets and regional resources will be created. CloudFront is a global service; ACM certificates used by CloudFront must be provisioned separately in us-east-1."
  type        = string
  default     = "ap-south-1"
  nullable    = false

  validation {
    condition     = length(trimspace(var.aws_region)) > 0
    error_message = "aws_region must not be empty."
  }
}

variable "project_name" {
  description = "Short project identifier used in resource names and default AWS provider tags. Keep it stable to avoid unnecessary resource replacement."
  type        = string
  default     = "static-site"
  nullable    = false

  validation {
    condition = (
      length(trimspace(var.project_name)) >= 2 &&
      length(trimspace(var.project_name)) <= 40
    )
    error_message = "project_name must contain between 2 and 40 characters."
  }

  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9-]*$", var.project_name))
    error_message = "project_name must start with an alphanumeric character and contain only alphanumeric characters and hyphens."
  }
}

variable "environment" {
  description = "Deployment environment identifier used in resource names and default AWS provider tags."
  type        = string
  default     = "dev"
  nullable    = false

  validation {
    condition = (
      length(trimspace(var.environment)) >= 2 &&
      length(trimspace(var.environment)) <= 20 &&
      can(regex("^[a-zA-Z0-9][a-zA-Z0-9-]*$", var.environment))
    )
    error_message = "environment must contain 2 to 20 characters, start with an alphanumeric character, and contain only alphanumeric characters and hyphens."
  }
}

variable "domain_names" {
  description = "Optional custom domain names configured as CloudFront aliases. Leave empty to use the default CloudFront domain name. Every configured domain must be covered by the ACM certificate supplied through acm_certificate_arn."
  type        = list(string)
  default     = []
  nullable    = false

  validation {
    condition     = length(var.domain_names) == length(distinct(var.domain_names))
    error_message = "domain_names must not contain duplicate entries."
  }

  validation {
    condition = alltrue([
      for domain in var.domain_names :
      length(domain) <= 253 &&
      length(split(".", domain)) >= 2 &&
      alltrue([
        for label in split(".", domain) :
        length(label) <= 63 &&
        can(regex("^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$", label))
      ])
    ])
    error_message = "Each domain_names entry must be a valid lowercase DNS name with at least two labels. Wildcard aliases and uppercase characters are not supported."
  }
}

variable "enable_access_logs" {
  description = "Whether to enable CloudFront standard access logging and create the separate S3 logging bucket. The logging bucket uses ACL support because CloudFront standard logging requires it."
  type        = bool
  default     = false
  nullable    = false
}

variable "cloudfront_price_class" {
  description = "CloudFront price class controlling the geographic distribution of edge locations used to serve the website."
  type        = string
  default     = "PriceClass_100"
  nullable    = false

  validation {
    condition = contains(
      [
        "PriceClass_100",
        "PriceClass_200",
        "PriceClass_All"
      ],
      var.cloudfront_price_class
    )
    error_message = "cloudfront_price_class must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate used by CloudFront when custom domain names are configured. The certificate must be issued or imported in us-east-1 and cover every domain in domain_names. Leave null when using the default CloudFront domain."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = (
      length(var.domain_names) == 0 ||
      (
        var.acm_certificate_arn != null &&
        can(regex(
          "^arn:[^:]+:acm:us-east-1:[0-9]{12}:certificate/[0-9a-fA-F-]+$",
          trimspace(var.acm_certificate_arn)
        ))
      )
    )
    error_message = "When domain_names is configured, acm_certificate_arn must be a valid ACM certificate ARN from us-east-1."
  }

  validation {
    condition = (
      var.acm_certificate_arn == null ||
      trimspace(var.acm_certificate_arn) == "" ||
      can(regex(
        "^arn:[^:]+:acm:us-east-1:[0-9]{12}:certificate/[0-9a-fA-F-]+$",
        trimspace(var.acm_certificate_arn)
      ))
    )
    error_message = "acm_certificate_arn must be a valid ACM certificate ARN from us-east-1, or null when no custom certificate is required."
  }
}