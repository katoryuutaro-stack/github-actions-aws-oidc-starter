variable "aws_region" {
  description = "AWS region used by the provider. IAM is global, but a region is still required."
  type        = string
  default     = "ap-northeast-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "aws_region must look like ap-northeast-1 or us-gov-west-1."
  }
}

variable "github_repository" {
  description = "GitHub repository in OWNER/REPOSITORY form."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must use OWNER/REPOSITORY form."
  }
}

variable "github_subject_mode" {
  description = "OIDC subject format: immutable for new/opted-in repositories, legacy for unchanged pre-2026-07-15 repositories, or dual for controlled migration."
  type        = string
  default     = "immutable"

  validation {
    condition     = contains(["legacy", "immutable", "dual"], var.github_subject_mode)
    error_message = "github_subject_mode must be legacy, immutable, or dual."
  }
}

variable "github_repository_owner_id" {
  description = "Immutable numeric GitHub owner ID. Required for immutable or dual mode."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.github_repository_owner_id == null || can(regex("^[0-9]+$", var.github_repository_owner_id))
    error_message = "github_repository_owner_id must contain digits only."
  }
}

variable "github_repository_id" {
  description = "Immutable numeric GitHub repository ID. Required for immutable or dual mode."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.github_repository_id == null || can(regex("^[0-9]+$", var.github_repository_id))
    error_message = "github_repository_id must contain digits only."
  }
}

variable "github_oidc_subject_override" {
  description = "Optional exact subject copied from the subject-preview workflow. Overrides generated legacy/immutable subjects."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.github_oidc_subject_override == null || startswith(var.github_oidc_subject_override, "repo:")
    error_message = "github_oidc_subject_override must begin with repo:."
  }
}

variable "github_ref" {
  description = "Exact Git reference trusted when github_environment is null."
  type        = string
  default     = "refs/heads/main"

  validation {
    condition     = startswith(var.github_ref, "refs/heads/") || startswith(var.github_ref, "refs/tags/")
    error_message = "github_ref must begin with refs/heads/ or refs/tags/."
  }
}

variable "github_environment" {
  description = "Optional GitHub Environment name. When set, environment trust replaces branch trust."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.github_environment == null || trimspace(var.github_environment) != ""
    error_message = "github_environment must be null or a non-empty Environment name."
  }
}

variable "role_name" {
  description = "IAM role assumed by GitHub Actions."
  type        = string
  default     = "github-actions-oidc-starter"
}

variable "create_oidc_provider" {
  description = "Create the GitHub OIDC provider. Set false when the AWS account already has one."
  type        = bool
  default     = true
}

variable "existing_oidc_provider_arn" {
  description = "Existing GitHub OIDC provider ARN when create_oidc_provider is false."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition = var.create_oidc_provider || (
      var.existing_oidc_provider_arn != null &&
      can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:oidc-provider/token\\.actions\\.githubusercontent\\.com$", var.existing_oidc_provider_arn))
    )
    error_message = "Set a valid existing_oidc_provider_arn when create_oidc_provider is false."
  }
}
