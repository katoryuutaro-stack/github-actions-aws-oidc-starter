data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

locals {
  repository_parts = split("/", var.github_repository)
  owner_name       = local.repository_parts[0]
  repository_name  = local.repository_parts[1]

  context_suffix = var.github_environment != null ? (
    "environment:${var.github_environment}"
  ) : "ref:${var.github_ref}"

  legacy_subject = "repo:${var.github_repository}:${local.context_suffix}"
  immutable_subject = format(
    "repo:%s@%s/%s@%s:%s",
    local.owner_name,
    coalesce(var.github_repository_owner_id, "MISSING"),
    local.repository_name,
    coalesce(var.github_repository_id, "MISSING"),
    local.context_suffix,
  )

  github_subjects = var.github_oidc_subject_override != null ? [var.github_oidc_subject_override] : (
    var.github_subject_mode == "legacy" ? [local.legacy_subject] : (
      var.github_subject_mode == "immutable" ? [local.immutable_subject] : [
        local.legacy_subject,
        local.immutable_subject,
      ]
    )
  )

  oidc_provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : var.existing_oidc_provider_arn
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    sid     = "GitHubActionsOidc"
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.github_subjects
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name                 = var.role_name
  assume_role_policy   = data.aws_iam_policy_document.github_trust.json
  max_session_duration = 3600

  lifecycle {
    precondition {
      condition = var.github_oidc_subject_override != null || var.github_subject_mode == "legacy" || (
        var.github_repository_owner_id != null &&
        var.github_repository_id != null
      )
      error_message = "Immutable or dual subject mode requires numeric owner and repository IDs. Run the GitHub identity resolver first."
    }
  }

  tags = {
    GitHubRepository  = var.github_repository
    GitHubSubjectMode = var.github_oidc_subject_override != null ? "override" : var.github_subject_mode
  }
}

data "aws_iam_policy_document" "identity_only" {
  statement {
    sid       = "ReadOwnCallerIdentity"
    effect    = "Allow"
    actions   = ["sts:GetCallerIdentity"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "identity_only" {
  name   = "identity-check-only"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.identity_only.json
}
