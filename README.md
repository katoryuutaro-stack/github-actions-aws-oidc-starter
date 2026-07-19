# GitHub Actions AWS OIDC Starter

Version 0.2.1

A security-first starter for authenticating GitHub Actions to AWS without long-lived AWS access keys. It supports both the legacy GitHub OIDC subject and the immutable owner/repository-ID subject introduced for new repositories after 2026-07-15.

[![CI](https://github.com/katoryuutaro-stack/github-actions-aws-oidc-starter/actions/workflows/ci.yml/badge.svg)](https://github.com/katoryuutaro-stack/github-actions-aws-oidc-starter/actions/workflows/ci.yml)

## What this starter gives you

- Terraform-managed GitHub OIDC provider and IAM role
- `legacy`, `immutable`, and controlled `dual` subject modes
- Exact repository + branch or GitHub Environment trust scoping
- GitHub API resolver for immutable owner/repository IDs
- A no-AWS subject-preview workflow that decodes the actual GitHub OIDC claim
- A manual AWS identity workflow that verifies temporary credentials
- Repository scanning that rejects static AWS key patterns
- CI for Python tests, YAML parsing, Terraform formatting, and validation

## Why version 0.2.1 exists

GitHub repositories created after 2026-07-15 use this default subject shape:

```text
repo:OWNER@OWNER_ID/REPOSITORY@REPOSITORY_ID:ref:refs/heads/main
```

Pre-cutoff repositories normally keep the previous name-only shape unless they opt in, are renamed, or are transferred. AWS IAM must match the actual `sub` exactly. This starter therefore never guesses silently: it can resolve IDs through the GitHub API and includes a workflow that prints the real non-secret `sub` claim before AWS is configured.

## Quick start

### 1. Resolve repository identity

For a public repository:

```bash
python scripts/resolve_github_identity.py \
  --repository OWNER/REPOSITORY \
  --ref refs/heads/main \
  --format tfvars
```

For a private repository, export a fine-grained token with repository metadata and Actions read access only for the command:

```bash
GITHUB_TOKEN="$(gh auth token)" python scripts/resolve_github_identity.py \
  --repository OWNER/REPOSITORY \
  --environment production \
  --format tfvars
```

Copy the output into `terraform/terraform.tfvars`. The token is not written or printed.

### 2. Preview the actual subject

Run **Actions → Preview GitHub OIDC subject → Run workflow**. Compare `OIDC_SUBJECT` with:

```bash
terraform -chdir=terraform output -json github_oidc_subjects
```

For custom OIDC claim templates, set `github_oidc_subject_override` to the exact previewed subject.

### 3. Bootstrap the AWS role

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Insert the resolver output.
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
terraform apply
```

### 4. Add GitHub repository variables

- `AWS_ROLE_ARN`: `terraform output -raw github_actions_role_arn`
- `AWS_REGION`: for example `ap-northeast-1`
- `EXPECTED_AWS_ACCOUNT_ID`: the expected 12-digit account ID
- `GITHUB_ENVIRONMENT`: leave undefined for branch mode; set the exact Environment name for environment mode

Do not add static AWS access-key variables.

### 5. Run the AWS identity test

Open **Actions → AWS OIDC identity check → Run workflow**. Expected result:

```text
OIDC_AUTHENTICATION=PASS
```

## Subject modes

| Mode | Use case | Trusted subjects |
|---|---|---|
| `immutable` | New repositories and opted-in repositories | ID-bound subject only |
| `legacy` | Unchanged pre-2026-07-15 repositories | Name-only subject only |
| `dual` | Short migration window | Exact legacy + exact immutable subjects |

Use `dual` temporarily, verify the immutable workflow, then remove legacy trust.

## Local validation

```bash
python -m pip install -e '.[dev]'
python scripts/validate_repo.py .
python -m ruff check scripts tests
python -m pytest -q
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform validate
```

## Security boundary

This starter creates authentication infrastructure only. It deliberately grants only `sts:GetCallerIdentity`. Add narrowly scoped workload permissions after the identity path works.

## Production edition

The paid production kit adds immutable ECR, ECS Fargate execution, S3 audit evidence, Secrets Manager references, CloudWatch logging, deployment receipts, verification scripts, and commercial licensing.

## License

MIT. See [LICENSE](LICENSE).


## Reproducible CI toolchain

Third-party GitHub Actions are pinned to full commit SHAs. See [`ACTION_LOCK.md`](ACTION_LOCK.md). The repository validator rejects mutable tags and unapproved action references.

