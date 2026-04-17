# Safety

## Safety Principles

This project is designed for practical engineering workflows, but it should not be deployed as an unrestricted root agent.

The minimum safety model is:

- least privilege
- explicit allowlists
- auditability
- rollback readiness
- conservative failure handling

## Tool Safety

### Allowed roots

Restrict file operations to explicit roots such as:

- a repository workspace
- a small set of reviewed config directories

Every requested path should be resolved to an absolute path and checked to ensure it stays inside one of the allowed roots after symlink and `..` normalization.

### Allowed commands

Use an allowlist, not a denylist.

Typical safe commands include:

- `pwd`
- `ls`
- `cat`
- `head`
- `tail`
- `grep`
- `find`
- `stat`
- `python3`
- `pytest`
- `git`

High-risk commands should not be available by default.

In the public reference implementation, command execution should also reject shell metacharacters such as:

- `;`
- `&&`
- `||`
- `>`
- `<`
- `` ` ``

This does not make command execution universally safe, but it removes a large class of trivial command injection mistakes from the reference path.

## Agent Rollout Model

### Stage 1: Read-only expert

Allow:

- read files
- search code
- search docs
- inspect logs
- inspect status

### Stage 2: Constrained execution

Allow:

- repository-local file edits
- test runs
- non-destructive allowlisted commands

### Stage 3: High-risk operations with approval

Require human review for:

- service restarts
- network changes
- daemon changes
- `/etc` modifications

## Open-Source Publishing Safety

Before publishing this project:

- remove real API keys
- remove hostnames and SSH targets
- remove real usernames
- remove local absolute paths
- remove private corpora
- scan generated files and caches

Also review:

- `.env.example`
- sample payloads
- test scripts
- screenshots
- copied logs
