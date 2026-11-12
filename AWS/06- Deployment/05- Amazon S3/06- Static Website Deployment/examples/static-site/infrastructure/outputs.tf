output "website_bucket_name" {
  description = "Name of the private S3 bucket used as the CloudFront website origin."
  value       = aws_s3_bucket.website.bucket
}

output "website_bucket_arn" {
  description = "ARN of the private S3 website origin bucket."
  value       = aws_s3_bucket.website.arn
}

output "website_bucket_regional_domain_name" {
  description = "Regional S3 bucket endpoint configured as the CloudFront origin."
  value       = aws_s3_bucket.website.bucket_regional_domain_name
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution serving the static website. Use this value when creating cache invalidations."
  value       = aws_cloudfront_distribution.website.id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution."
  value       = aws_cloudfront_distribution.website.arn
}

output "cloudfront_domain_name" {
  description = "Default CloudFront domain name for accessing the deployed website."
  value       = aws_cloudfront_distribution.website.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront's Route 53 hosted zone ID. Use this as the alias target hosted zone ID when configuring Route 53 records."
  value       = aws_cloudfront_distribution.website.hosted_zone_id
}

output "website_url" {
  description = "HTTPS URL for the website. Uses the first configured custom domain when available; otherwise uses the default CloudFront domain."
  value = (
    length(var.domain_names) > 0
    ? "https://${var.domain_names[0]}"
    : "https://${aws_cloudfront_distribution.website.domain_name}"
  )
}

output "custom_domain_names" {
  description = "Custom domain aliases configured on the CloudFront distribution. Empty when the default CloudFront domain is used."
  value       = aws_cloudfront_distribution.website.aliases
}

output "cloudfront_origin_access_control_id" {
  description = "ID of the Origin Access Control that allows the CloudFront distribution to access the private S3 bucket."
  value       = aws_cloudfront_origin_access_control.website.id
}

output "cloudfront_response_headers_policy_id" {
  description = "ID of the CloudFront response headers policy used to apply website security headers."
  value       = aws_cloudfront_response_headers_policy.security.id
}

output "access_logs_enabled" {
  description = "Indicates whether the optional CloudFront access logging bucket was created."
  value       = var.enable_access_logs
}

output "cloudfront_logs_bucket_name" {
  description = "Name of the optional S3 bucket receiving CloudFront standard access logs. Null when access logging is disabled."
  value       = try(aws_s3_bucket.cloudfront_logs[0].bucket, null)
}

output "cloudfront_logs_bucket_arn" {
  description = "ARN of the optional S3 bucket receiving CloudFront standard access logs. Null when access logging is disabled."
  value       = try(aws_s3_bucket.cloudfront_logs[0].arn, null)
}