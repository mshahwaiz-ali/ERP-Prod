# Production Checklist

## Pre-Deploy

- Confirm DNS points the domain/subdomain to the server public IP.
- Confirm security group/firewall allows SSH from trusted IPs and HTTP/HTTPS only.
- Confirm MariaDB and Redis are not public.
- Run `./scripts/ci_local.sh`.
- Run `./deploy/smoke_test.sh --site SITE --offline`.
- Confirm `frappe-bench/`, logs, backups, `.env`, and secret files are ignored.

## Deploy

- Use `./deploy/production_setup.sh` for EC2/public production.
- Install only the selected app on the selected site.
- Use Supervisor and Nginx. Do not use `bench start`.
- Enable scheduler after site setup.
- Run `bench --site SITE migrate`.
- Run `bench build`.
- Reload Supervisor and Nginx.

## Post-Deploy

- Enable HTTPS and verify redirects.
- Run `./deploy/smoke_test.sh --site SITE --online --url https://domain`.
- Change weak or demo Administrator passwords.
- Verify backups are being produced.
- Perform at least one restore rehearsal before relying on backups.
- Verify email/SMS integrations if used.

## FBR Readiness

- Run `bench --site SITE execute ledgix_saas.validation.run_all`.
- Run `bench --site SITE execute ledgix_saas.api.fbr_health.check`.
- Test sandbox validation before production token use.
- Review submission logs after test invoices and returns.
