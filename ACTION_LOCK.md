# Verified toolchain lock

Verified on 2026-07-19 against official upstream release repositories.

| Component | Release | Immutable reference |
|---|---:|---|
| actions/checkout | v6.0.2 | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` |
| actions/setup-python | v6.2.0 | `a309ff8b426b58ec0e2a45f0f869d46889d02405` |
| hashicorp/setup-terraform | v4.0.1 | `dfe3c3f87815947d99a8997f908cb6525fc44e9e` |
| aws-actions/configure-aws-credentials | v6.1.1 | `d979d5b3a71173a29b74b5b88418bfda9437d885` |
| Terraform CLI | 1.15.5 | Installed by setup-terraform |

The repository validator rejects mutable action tags, unknown external actions, changed release SHAs, and a different Terraform CLI version. Update the validator and this file together after reviewing an upstream release.
