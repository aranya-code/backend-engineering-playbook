output "lifecycle_configuration_id" {
  description = "ID of the S3 bucket lifecycle configuration managed by this module."
  value       = aws_s3_bucket_lifecycle_configuration.this.id
}

output "lifecycle_rule_ids" {
  description = "Identifiers of the lifecycle rules configured on the bucket."
  value       = [for rule in var.lifecycle_rules : rule.id]
}

output "lifecycle_rule_count" {
  description = "Number of lifecycle rules supplied to the module."
  value       = length(var.lifecycle_rules)
}

output "enabled_lifecycle_rule_ids" {
  description = "Identifiers of lifecycle rules currently configured as enabled."
  value = [
    for rule in var.lifecycle_rules : rule.id
    if rule.enabled
  ]
}

output "disabled_lifecycle_rule_ids" {
  description = "Identifiers of lifecycle rules currently configured as disabled."
  value = [
    for rule in var.lifecycle_rules : rule.id
    if !rule.enabled
  ]
}

output "lifecycle_transitions" {
  description = "Configured current-version storage-class transitions by lifecycle rule."
  value = {
    for rule in var.lifecycle_rules : rule.id => rule.transitions
  }
}

output "lifecycle_expirations" {
  description = "Configured current-version expiration settings by lifecycle rule."
  value = {
    for rule in var.lifecycle_rules : rule.id => rule.expiration
    if rule.expiration != null
  }
}

output "noncurrent_version_transitions" {
  description = "Configured noncurrent-version storage-class transitions by lifecycle rule."
  value = {
    for rule in var.lifecycle_rules : rule.id => rule.noncurrent_version_transitions
    if length(rule.noncurrent_version_transitions) > 0
  }
}

output "noncurrent_version_expirations" {
  description = "Configured noncurrent-version expiration settings by lifecycle rule."
  value = {
    for rule in var.lifecycle_rules : rule.id => rule.noncurrent_version_expiration
    if rule.noncurrent_version_expiration != null
  }
}

output "multipart_upload_abort_rules" {
  description = "Lifecycle rules that abort incomplete multipart uploads and their configured age thresholds in days."
  value = {
    for rule in var.lifecycle_rules : rule.id => rule.abort_incomplete_multipart_upload_days
    if rule.abort_incomplete_multipart_upload_days != null
  }
}
