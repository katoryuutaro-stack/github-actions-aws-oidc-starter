# Quick Start

## Prerequisites

- Terraform 1.10 or later
- AWS CLI v2
- A non-root AWS identity allowed to create IAM providers and roles
- A GitHub repository

## Bootstrap

1. Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars`.
2. Set the exact `OWNER/REPOSITORY` value.
3. Keep branch trust for the first test, or set a GitHub Environment name.
4. Run `terraform init`, `terraform plan`, and `terraform apply`.
5. Add the repository variables described in the main README. Set `GITHUB_ENVIRONMENT` only when Terraform environment trust is enabled.
6. Manually run the identity-check workflow.

## Existing OIDC provider

An AWS account can reuse one GitHub OIDC provider across repositories. If one already exists:

```hcl
create_oidc_provider      = false
existing_oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
```

## Production state

The included local Terraform state is suitable only for a controlled bootstrap test. Production teams should configure an encrypted remote backend with state locking and restricted access.
