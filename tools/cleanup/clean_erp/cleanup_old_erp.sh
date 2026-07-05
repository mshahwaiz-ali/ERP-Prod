#!/usr/bin/env bash
# Remove previous local Frappe/ERPNext/MariaDB setup before a fresh install.
set -euo pipefail

echo "[cleanup] Stopping bench/node/python processes..."
pkill -f "bench start" 2>/dev/null || true
pkill -f "honcho start" 2>/dev/null || true
pkill -f "frappe serve" 2>/dev/null || true
pkill -f "frappe worker" 2>/dev/null || true
pkill -f "frappe schedule" 2>/dev/null || true
pkill -f "frappe watch" 2>/dev/null || true
pkill -f "node.*socketio" 2>/dev/null || true

for port in 8000 9000 6787 11000 12000 13000; do
	fuser -k "${port}/tcp" 2>/dev/null || true
done

echo "[cleanup] Stopping services..."
sudo systemctl stop mariadb mysql redis-server nginx supervisor 2>/dev/null || true

echo "[cleanup] Removing local benches and generated files..."
rm -rf \
	"$HOME/frappe-bench" \
	"$HOME/erp-system" \
	"$HOME/erp_next_production/frappe-bench" \
	"/home/alishahwaiz/Projects/erp_products/frappe-bench" \
	"/home/alishahwaiz/Projects/erp_products/config/bench.env" \
	"/home/alishahwaiz/Projects/erp_products/secrets.txt" \
	"/home/alishahwaiz/new/secrets.txt"

echo "[cleanup] Purging MariaDB/MySQL packages and data..."
sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y \
	mariadb-server mariadb-client mariadb-common mariadb-server-core mariadb-client-core \
	mysql-common mysql-server mysql-client mysql-server-core mysql-client-core \
	libmariadb-dev libmariadb3 2>/dev/null || true
sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove -y
sudo rm -rf /var/lib/mysql /var/lib/mariadb /etc/mysql /var/log/mysql /run/mysqld

echo "[cleanup] Clearing old MariaDB reset logs..."
rm -f /tmp/erp-mariadb-init.log /tmp/erp-mariadb-reset.log /tmp/new-installer-mariadb-reset.log

echo "[cleanup] Done. Fresh install can be run with:"
echo "  cd /home/alishahwaiz/new && ./install.sh"
