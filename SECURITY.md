# Security: Exposed Secret Remediation

## Summary
A sensitive token was detected and removed from the repository. The file `~/.roboto/config.json` contained an `api_key` which has been removed from version control.

## Immediate Actions (required)
1. **Rotate the exposed token immediately** in the provider dashboard (invalidate the old key and create a new one).
2. Verify audit logs for any misuse of the exposed token.
3. Remove the token from any environment or CI variable that is no longer valid, and replace it with the new token in a secrets manager (e.g., GitHub Secrets).

## Preventative Measures added
- Pre-commit configuration with `detect-secrets` (see `.pre-commit-config.yaml`).
- GitHub Actions workflows:
  - `Secret Scan` using Gitleaks (`.github/workflows/secret-scan.yml`)
  - `Dependency Security Audit` using `pip-audit` (`.github/workflows/pip-audit.yml`)
  - `CodeQL` static analysis (`.github/workflows/codeql-analysis.yml`)
- A recommendation to run `detect-secrets scan` locally and commit a baseline: `detect-secrets scan > .secrets.baseline`.

## Notes
- The token was removed from version control (untracked), but it may still exist in Git history; if required, use `git filter-repo` or BFG to purge it from history and rotate keys.
- Create an incident ticket and rotate the secret immediately.
