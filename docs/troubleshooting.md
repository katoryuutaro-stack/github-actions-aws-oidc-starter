# Troubleshooting

## `Not authorized to perform sts:AssumeRoleWithWebIdentity`

Compare the IAM trust policy `sub` value with the actual workflow identity:

- Branch: `repo:OWNER/REPOSITORY:ref:refs/heads/main`
- Environment: `repo:OWNER/REPOSITORY:environment:production`

Repository names and environment names are case-sensitive in practice. Confirm that `permissions.id-token` is set to `write`.

## Missing OIDC token variables

The workflow must include `id-token: write` at the workflow or job level. Forked pull requests should not be allowed to use a production deployment role.

## Wrong AWS account

Set `EXPECTED_AWS_ACCOUNT_ID`. The credential action's account allowlist makes the workflow fail before deployment if the role resolves to an unexpected account.

## OIDC provider already exists

Set `create_oidc_provider = false` and provide its ARN. Do not create duplicate providers with the same URL.

## Terraform state contains sensitive identifiers

Do not commit state. For production, use an encrypted remote backend and access controls appropriate for your organization.
