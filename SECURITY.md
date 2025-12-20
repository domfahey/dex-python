# Security Guidelines

## API Keys

- **Never commit API keys** to version control
- Store `DEX_API_KEY` in `.env` file (gitignored)
- Use `.env.example` as a template with placeholder values

## Personal Data Protection

This project syncs contact data from Dex CRM. To protect privacy:

- **Database files** (`*.db`, `*.sqlite`) are gitignored
- **Data exports** (`*.json`, `*.csv`) are gitignored
- **Reports with PII** (`*_REPORT.md`) are gitignored
- Never commit files containing real names, emails, or phone numbers

## Pre-commit Checks

Consider using `git-secrets` to prevent accidental commits:

```bash
# Install git-secrets
brew install git-secrets

# Initialize in repo
git secrets --install
git secrets --register-aws
```

## If You Accidentally Commit Secrets

1. **Rotate the exposed key immediately**
2. Remove from history using BFG Repo-Cleaner:
   ```bash
   bfg --delete-files .env
   git push --force
   ```

## Reporting Security Issues

Contact domfahey@gmail.com for security concerns.
