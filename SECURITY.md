# Security Policy

We take the security of GAME seriously. Thank you for helping keep the project
and its users safe.

## Supported Versions

GAME is developed primarily on the `main` branch, and security fixes are applied
there first and then to the most recent tagged release.

| Version                 | Supported          |
| ----------------------- | ------------------ |
| `main` (latest)         | :white_check_mark: |
| Latest tagged release   | :white_check_mark: |
| Older tags              | :x:                |

If you depend on an older release, please upgrade to the latest tag before
reporting an issue, as the vulnerability may already be fixed.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Instead, use one of these private channels:

1. **GitHub Security Advisories (preferred).** Open a private report via the
   repository's [**Security → Report a vulnerability**](https://github.com/fvergaracl/GAME/security/advisories/new)
   page. This keeps the discussion confidential until a fix is ready.
2. **Email.** If you cannot use GitHub Security Advisories, email
   **felipe.vergara@deusto.es** with the subject line `SECURITY: GAME`.

To help us triage quickly, please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce, or a proof-of-concept, if available.
- Affected version, commit, or endpoint.
- Any relevant logs, payloads, or configuration (with secrets redacted).

## What to Expect

This is a research-driven, maintainer-led project, so timelines are best-effort:

- **Acknowledgement** of your report within **5 business days**.
- An initial **assessment and severity estimate** shortly after.
- Regular updates on remediation progress until the issue is resolved.
- **Coordinated disclosure**: we will agree on a public disclosure date with you
  and credit you in the advisory (unless you prefer to remain anonymous).

Please give us a reasonable opportunity to address the issue before any public
disclosure.

## Scope & Hardening Notes

The following are in scope for a security report:

- Authentication and authorization flaws (API keys, Keycloak OAuth2 / OIDC).
- Injection, data exposure, or privilege-escalation issues in the API.
- Vulnerable dependencies not already flagged by automated tooling.

GAME already ships with several privacy- and security-conscious defaults:

- Sentry defaults are privacy-conservative
  (`SENTRY_SEND_DEFAULT_PII=false`, reduced trace sampling, profiling off).
- CORS is restricted to an explicit allow-list and rejects `*` in
  `prod`/`stage`.
- Data retention and GDPR posture for the audit `logs` table are documented in
  [docs/DATA_RETENTION.md](docs/DATA_RETENTION.md).
- Dependency and code scanning run in CI (`pip-audit`, CodeQL, Dependabot).

For the full security model, see the
[Security chapter of the documentation](docs/source/security.rst).

Thank you for contributing to the security of GAME.
