# Commands

## Local Development

```bash
./install.sh
./site_setup.sh
./start.sh --background
./start.sh --status
./start.sh --smoke --site ledgix.local
./start.sh --stop
```

## Validation

```bash
./scripts/validate_repo.sh
./scripts/check_secrets.sh
./scripts/ci_local.sh
```

## Site/App Checks

```bash
cd frappe-bench
bench --site ledgix.local list-apps
bench --site ledgix.local migrate
bench --site ledgix.local execute ledgix_saas.validation.run_all
bench --site ledgix.local execute ledgix_saas.api.fbr_health.check
```

## Production

```bash
./deploy/production_setup.sh
./deploy/status.sh
./deploy/backup.sh
./deploy/deploy_update.sh
./deploy/smoke_test.sh --site ledgix.local --offline
./deploy/smoke_test.sh --site ledgix.local --online --url https://domain.example
```

Production uses Supervisor and Nginx. Do not use `bench start` for public/EC2 production.
