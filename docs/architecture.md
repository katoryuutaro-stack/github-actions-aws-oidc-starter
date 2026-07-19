# Architecture and Threat Model

## Assets protected

- AWS role assumption path
- Repository identity and branch or environment boundary
- Temporary AWS credentials
- Terraform state

## Primary threats

1. A different repository attempts to assume the role.
2. An untrusted branch or pull request attempts to assume the role.
3. Long-lived AWS keys are committed to GitHub.
4. A workflow assumes a role in the wrong AWS account.

## Controls

- Exact `aud` and `sub` trust-policy conditions
- `id-token: write` only on the manual identity workflow
- Account allowlisting in `configure-aws-credentials`
- Static credential scanner
- No deployment permissions in the free starter
- GitHub Environment mode for production approvals and branch policies
