# Security Policy

## Supported versions

Agentic Project Kit is in early MVP development.

| Version | Supported |
|---|---|
| `main` | yes |
| `0.2.x` | yes |
| `< 0.2.0` | no |

## Reporting a vulnerability

Do not publish secrets, exploit details, private tokens, or sensitive logs in public issues or pull requests.

Preferred reporting path:

1. Use GitHub private vulnerability reporting / Security Advisories if available for this repository.
2. If that is not available, open a minimal issue that says a private security report is needed, without sensitive details.

## Scope

Relevant security issues include:

- accidental token or credential exposure
- unsafe generated repository defaults
- generated workflows that could leak secrets
- command execution paths that use untrusted input unsafely
- log-staging behavior that could commit secrets or broad private logs
- GitHub automation that creates public repositories without a clear warning

## Generated projects

Generated projects may include logging and evidence-staging helpers. These helpers are intended for bounded diagnostics only.

Users must inspect staged evidence before committing it. Agentic Project Kit must not encourage committing broad logs, credentials, private runtime state, `.env` files, or local API-key material.

## GitHub and credentials

The `agentic-kit github-create` command uses the local GitHub CLI (`gh`). It does not ask for or store GitHub tokens itself.

## Dependency updates

GitHub Actions and Python dependencies are checked by CI. Dependabot updates should still be reviewed before merge.
