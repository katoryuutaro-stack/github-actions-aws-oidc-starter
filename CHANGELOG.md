# Changelog

## 0.2.1 - 2026-07-19

- Corrected Terraform CLI pin from nonexistent 1.15.6 to verified 1.15.5.
- Corrected configure-aws-credentials from nonexistent v6.1.2 to verified v6.1.1.
- Pinned all third-party GitHub Actions to full immutable commit SHAs.
- Added fail-closed validation for mutable or unapproved action references.

## 0.2.0 - 2026-07-19

- Added GitHub immutable OIDC subject support for repositories created after 2026-07-15
- Added legacy, immutable, and controlled dual trust modes
- Added repository/owner ID resolver and actual-token subject preview workflow
- Added exact-subject override for custom OIDC claim templates
- Added migration tests and documentation

## 0.1.0 - 2026-07-19

- Initial Terraform OIDC bootstrap
- Manual AWS identity-check workflow
- Static credential scanner and tests
- CI, Dependabot, quick start, and troubleshooting documentation
