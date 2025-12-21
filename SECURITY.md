# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you believe you have found a security vulnerability in this project:

1. **Email:** Contact the project maintainer directly
2. **Include:** Description, steps to reproduce, and potential impact
3. **Response:** Expect acknowledgment within 48 hours

We follow responsible disclosure principles and will:
- Acknowledge receipt of your report
- Provide an estimated timeline for a fix
- Notify you when the vulnerability is resolved
- Credit you in the release notes (unless you prefer anonymity)

## Security Audit

This repository underwent a security audit before public release. See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for details.

**Audit Status:** ✅ Passed (2024-12-21)

## Best Practices for Contributors

### Secret Management

- **Never commit API keys, tokens, or passwords**
- Use `.env` files for local development (template: `.env.example`)
- The `.gitignore` excludes sensitive files - do not force-add them
- Use environment variables: `os.getenv("DEX_API_KEY")`

### Data Privacy

This tool processes personal contact information (PII):

- **Database files (`*.db`, `*.sqlite`)** - Gitignored, never commit
- **Report files (`*_REPORT.md`)** - Gitignored, may contain names/emails
- **Export files (`*.json`, `*.csv`)** - Gitignored, contain contact data
- Use `Faker` library for test data, never real contacts

### Dependency Management

- We use `uv` for dependency management
- Run `uv sync` to install pinned versions
- Regularly audit with `pip-audit` or `safety`

### Testing

- Integration tests run against the live Dex API
- Use a test account when possible
- Never record real API keys in test fixtures
- Use `pytest -m "not integration"` to skip live tests

## Security Controls

### What We Protect

| Data Type | Protection |
|-----------|------------|
| API Keys | Environment variables only |
| Contact Data | Local database, gitignored |
| Reports | Generated locally, gitignored |
| Test Data | Faker-generated synthetic data |

### Gitignore Coverage

```
.env              # Real secrets
*.db, *.sqlite    # Databases with PII
*.json, *.csv     # Data exports
output/*          # Reports directory
*_REPORT.md       # Analysis reports
```

## Automated Security

Consider enabling:

- **GitHub Secret Scanning** - Alerts for exposed secrets
- **Dependabot** - Dependency vulnerability alerts
- **Pre-commit hooks** - Local secret detection

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
```