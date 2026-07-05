# Troubleshooting

## Local Site Does Not Open

- Run `./start.sh --status`.
- Confirm `/etc/hosts` maps the site to `127.0.0.1`.
- Confirm port `8000` is owned by this bench.
- Run `./start.sh --smoke --site SITE`.

## App Not Installed

- Run `bench --site SITE list-apps`.
- Confirm `ledgix_saas` appears in `frappe-bench/sites/apps.txt`.
- Run `bench --site SITE install-app ledgix_saas` only for the intended site.
- Run `bench --site SITE migrate`.

## Module Import Errors

- Run `./scripts/validate_repo.sh`.
- Confirm `apps/ledgix_saas/hooks.py`, `pyproject.toml`, and `modules.txt` exist.
- Confirm the app copy exists under `frappe-bench/apps/ledgix_saas`.
- Reinstall editable package with `frappe-bench/env/bin/python -m pip install -e frappe-bench/apps/ledgix_saas`.

## Nginx 502 Or Supervisor FATAL

- Run `./deploy/status.sh`.
- Run `sudo supervisorctl status`.
- Run `sudo nginx -t`.
- Restart Supervisor after build/migrate.
- Check bench logs under `frappe-bench/logs`.

## FBR Submission Errors

- Run `bench --site SITE execute ledgix_saas.api.fbr_health.check`.
- Confirm the active mode has a configured token.
- Confirm seller/buyer tax identity fields.
- Confirm HS code, UOM, tax rate, and invoice total consistency.
- Review `Ledgix FBR Submission Log`; do not paste tokens into tickets or commits.
