#!/usr/bin/env bash
# Clean previous local Frappe/ERPNext setup for a fresh install in /home/alishahwaiz/production.
set -euo pipefail

ROOT_DIR="/home/alishahwaiz/production"
BENCH_DIR="$ROOT_DIR/frappe-bench"
SECRETS_FILE="$ROOT_DIR/secrets.txt"

log() { echo "[cleanup] $*"; }

log "Stopping bench/node/python processes..."
pkill -f "bench start" 2>/dev/null || true
pkill -f "honcho start" 2>/dev/null || true
pkill -f "frappe serve" 2>/dev/null || true
pkill -f "frappe worker" 2>/dev/null || true
pkill -f "frappe schedule" 2>/dev/null || true
pkill -f "frappe watch" 2>/dev/null || true
pkill -f "node.*socketio" 2>/dev/null || true
pkill -f "redis-server.*frappe" 2>/dev/null || true

for port in 8000 9000 6787 11000 12000 13000; do
	fuser -k "${port}/tcp" 2>/dev/null || true
done

log "Stopping services..."
sudo systemctl stop mariadb mysql redis-server nginx supervisor 2>/dev/null || true

log "Removing generated bench/secrets only..."
rm -rf \
	"$BENCH_DIR" \
	"$SECRETS_FILE" \
	"$HOME/frappe-bench" \
	"$HOME/erp-system" \
	"$HOME/erp_next_production/frappe-bench" \
	"/home/alishahwaiz/Projects/erp_products/frappe-bench" \
	"/home/alishahwaiz/Projects/erp_products/config/bench.env" \
	"/home/alishahwaiz/Projects/erp_products/secrets.txt" \
	"/home/alishahwaiz/new/frappe-bench" \
	"/home/alishahwaiz/new/secrets.txt"

log "Purging MariaDB/MySQL packages and data..."
sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y \
	mariadb-server mariadb-client mariadb-common mariadb-server-core mariadb-client-core \
	mysql-common mysql-server mysql-client mysql-server-core mysql-client-core \
	libmariadb-dev libmariadb3 2>/dev/null || true

log "Purging Redis package and data..."
sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y \
	redis-server redis-tools 2>/dev/null || true

sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove -y || true
sudo rm -rf \
	/var/lib/mysql \
	/var/lib/mariadb \
	/etc/mysql \
	/var/log/mysql \
	/run/mysqld \
	/var/lib/redis \
	/etc/redis

log "Clearing old install logs..."
rm -f \
	/tmp/erp-mariadb-init.log \
	/tmp/erp-mariadb-reset.log \
	/tmp/new-installer-mariadb.log \
	/tmp/new-installer-mariadb-init.log \
	/tmp/new-installer-mariadb-reset.log

log "Done. Fresh install can be run with:"
echo "  cd $ROOT_DIR && ./install.sh"
