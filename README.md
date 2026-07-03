# ERP-Prod

ERP-Prod contains the local Frappe installer/control scripts, production EC2 deployment helpers, and custom apps used by this setup.

## What Is Included

- `install.sh` - main launcher for local development setup or production EC2 setup.
- `site_setup.sh` - local site creation, app install, site deletion, and site listing flow.
- `start.sh` - local development bench runner only.
- `deploy/` - production EC2/server setup, update, backup, status, Nginx, Supervisor, and SSL helpers.
- `p_apps/` - custom Frappe apps that the scripts copy into the bench.

The generated Frappe bench folder is intentionally ignored by Git:

```text
frappe-bench/
```

## Local Setup Quickstart

From the project root:

```bash
chmod +x install.sh site_setup.sh start.sh
./install.sh
```

Choose:

```text
1) Local / Development Setup
```

The local menu can install Frappe, run `site_setup.sh`, start `bench start` in the background, stop local bench processes, or show local status.

Local development uses:

- `bench start`
- port `8000`
- local secrets in `secrets.md`
- local logs in `install_logs/` and `logs/`

It does not configure production Nginx, Supervisor, Certbot, or system services.

## Production EC2 Quickstart

Production scripts are intended for a real EC2/server deployment and should be first run on a clean test server.

From the project root on the server:

```bash
chmod +x install.sh deploy/*.sh
./install.sh
```

Choose:

```text
2) Production / EC2 Setup
```

Or run the production script directly:

```bash
deploy/production_setup.sh
```

Default production Git URL:

```text
https://github.com/mshahwaiz-ali/ERP-Prod.git
```

Production uses:

- Supervisor for Frappe processes
- Nginx for HTTP/HTTPS
- ports `80` and `443`
- optional Certbot SSL
- generated strong Administrator passwords by default
- production secrets saved to `deploy/production.secrets.md`

Never use `start.sh` for production.

## Production Helpers

```bash
deploy/production_setup.sh --help
deploy/production_setup.sh --dry-run
deploy/deploy_update.sh
deploy/backup.sh
deploy/status.sh
```

The production menu includes preflight checks, package preparation, bench validation, app sync, site creation, Supervisor/Nginx setup, SSL setup, backups, deploy updates, and status checks.

## DNS And SSL Requirements

Before SSL, point your production domain A record to the EC2 public IP:

```text
erp.example.com -> EC2_PUBLIC_IP
```

The SSL flow asks for a Let's Encrypt email address and validates DNS before running Certbot. If DNS does not match the server public IP, the script stops unless you type the exact confirmation phrase shown on screen.

## Local vs Production

```text
Local:
  runner: bench start
  URL: http://site.local:8000
  services: development processes

Production:
  runner: Supervisor
  web: Nginx
  URL: http://domain or https://domain
  services: system-managed production processes
```

## Secrets

Do not commit secrets. The repo ignores:

```text
secrets.md
deploy/production.secrets.md
deploy/logs/
deploy/backups-index.md
*.sql.gz
*.tar
*.tgz
.env
*.env.local
```

Example environment templates live in:

```text
env/local.example.env
env/production.example.env
```

## Troubleshooting

If you see the Nginx welcome page, the default Nginx site may still be enabled or the Frappe Nginx config may not be loaded. Run:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

If `http://127.0.0.1` returns `404` in multisite mode, test with the Host header:

```bash
curl -I -H "Host: your.domain.com" http://127.0.0.1
```

If SSL fails, verify DNS first:

```bash
dig +short A your.domain.com
curl -fsS https://ifconfig.me
```

Useful production restart/status commands:

```bash
sudo supervisorctl status
sudo supervisorctl restart all
sudo nginx -t
sudo systemctl reload nginx
deploy/status.sh
```
