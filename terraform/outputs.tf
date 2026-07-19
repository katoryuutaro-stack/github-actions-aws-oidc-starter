output "github_actions_role_arn" {
  description = "Set this as the GitHub Actions repository variable AWS_ROLE_ARN."
  value       = aws_iam_role.github_actions.arn
}

output "github_oidc_subjects" {
  description = "Exact OIDC subjects trusted by the IAM role."
  value       = local.github_subjects
}

output "github_oidc_primary_subject" {
  description = "Primary subject for display and diagnostics."
  value       = local.github_subjects[0]
}

output "oidc_provider_arn" {
  description = "GitHub OIDC provider ARN used by the role."
  value       = local.oidc_provider_arn
}
