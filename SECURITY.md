# Security Policy

## Reporting

Do not open public issues containing credentials, account IDs tied to private systems, or exploit details. Use GitHub private vulnerability reporting when enabled.

## Credential policy

This repository must never contain long-lived AWS credentials. The validation script rejects common AWS access-key and private-key patterns. Treat generated Terraform state as sensitive and store it in an encrypted remote backend for production use.

## Supported versions

Only the latest release is supported.
