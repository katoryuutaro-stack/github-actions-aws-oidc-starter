# Migrating to GitHub immutable OIDC subjects

## New format

```text
repo:OWNER@OWNER_ID/REPOSITORY@REPOSITORY_ID:ref:refs/heads/BRANCH
repo:OWNER@OWNER_ID/REPOSITORY@REPOSITORY_ID:environment:ENVIRONMENT
```

## Safe migration sequence

1. Run the `Preview GitHub OIDC subject` workflow and record the actual `sub`.
2. Resolve numeric IDs with `scripts/resolve_github_identity.py`.
3. Set `github_subject_mode = "dual"` and apply Terraform.
4. Opt in to immutable subjects or perform the repository change.
5. Run the AWS OIDC identity workflow and confirm success.
6. Set `github_subject_mode = "immutable"` and apply again.
7. Confirm the legacy subject no longer appears in the IAM trust policy.

Never switch GitHub's token format before AWS trusts the new exact subject. That creates an authentication outage by design.
