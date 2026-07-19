provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      ManagedBy = "Terraform"
      Project   = "github-actions-aws-oidc-starter"
    }
  }
}
