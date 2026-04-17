# Security

## Scope

This repository is a public reference implementation for `GhostFabric`. Treat all execution features as examples that must be reviewed and narrowed for a real deployment.

## Default Safety Model

The recommended baseline is:

- no unrestricted shell
- no unrestricted filesystem writes
- explicit path allowlists
- explicit command allowlists
- bounded tool loops
- auditable writes
- human approval for high-risk changes

## Publishing Checklist

Before making any repository public:

1. remove real API keys and tokens
2. remove real IPs, domains, SSH endpoints, and usernames
3. remove SSH keys, PEM files, and certificates
4. remove private corpora and customer data
5. remove absolute local paths unless clearly synthetic
6. remove build caches and generated artifacts
7. run `scripts/secret_scan.ps1`
8. manually inspect the staged diff

## Runtime Checklist

For a real agent deployment:

1. isolate a dedicated workspace
2. mount only approved directories
3. use a command allowlist, not a denylist
4. block shell chaining and redirection by default
5. keep `/etc`, network config, and service control behind approval
6. log every write action and command result
7. create rollback points before edits

## Disclosure

If you adapt this repository for production, document your own threat model and incident response process. This public repository does not include a full production hardening profile.
