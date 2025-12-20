# Security Guidelines

## API Keys

- **Never commit API keys** to version control
- Store `DEX_API_KEY` in `.env` file (gitignored)
- Use `.env.example` as a template with placeholder values

## Personal Data Protection

This project syncs contact data from Dex CRM. To protect privacy:

- **All artifacts go to `output/`** directory (gitignored)
- **Database files** (`*.db`, `*.sqlite`) are gitignored
- **Data exports** (`*.json`, `*.csv`) are gitignored
- **Reports with PII** (`*_REPORT.md`) are gitignored
- Never commit files containing real names, emails, or phone numbers

## Pre-commit Hooks (Enforced)

This repo uses pre-commit hooks for automated secret scanning:

```bash
# Install pre-commit
pip install pre-commit  # or: brew install pre-commit

# Install hooks (runs gitleaks on every commit)
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

The `.pre-commit-config.yaml` includes:
- **gitleaks** - Scans for secrets, API keys, credentials
- **ruff** - Linting and formatting
- **standard hooks** - Trailing whitespace, YAML validation

## If You Accidentally Commit Secrets

1. **Rotate the exposed key immediately**
2. Remove from history using BFG Repo-Cleaner:
   ```bash
   bfg --delete-files .env
   git push --force
   ```

## Reporting Security Issues

Contact domfahey@gmail.com for security concerns.
