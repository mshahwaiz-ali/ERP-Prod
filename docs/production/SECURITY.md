# Security Notes

This repository is a local deployment bundle for Frappe v15 and Ledgix. Keep secrets on the machine where the bench runs; do not commit them.

## Secret Handling

- Do not commit FBR tokens, API keys, passwords, private keys, database credentials, `.env` files, site configs, backups, or dumps.
- Use `config/example.env` as a template only.
- Local generated credentials may be written to `secrets.md`; production credentials may be written to `deploy/production.secrets.md`. Both are ignored by Git.
- Run `./scripts/check_secrets.sh` before committing local changes.

## Production Rules

- Use Supervisor and Nginx in production.
- Do not use `bench start` for EC2/public production.
- Keep MariaDB and Redis bound to private/local interfaces only.
- Use HTTPS before production FBR tokens are enabled.
- Restrict SSH with UFW/security groups wherever possible.

## FBR Safety

- FBR health and validation commands must not submit invoices.
- FBR token values must never be printed in logs or smoke-test output.
- Review FBR sandbox behavior before switching any site to production mode.
