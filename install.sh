#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_DIR="$SCRIPT_DIR/frappe-bench"
SITE_SETUP="$SCRIPT_DIR/site_setup.sh"
LOG_DIR="$SCRIPT_DIR/install_logs"
LOG_FILE="$LOG_DIR/install-$(date +%Y%m%d-%H%M%S).log"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
NODE_MAJOR="${NODE_MAJOR:-18}"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

info() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
err() { printf '[ERROR] %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }

run() {
  info "[RUN] $*"
  "$@"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

need_sudo() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    SUDO=()
    return 0
  fi
  if ! have_cmd sudo; then
    die "sudo is required for dependency install/service repair"
  fi
  if ! sudo -v; then
    die "sudo permission is required"
  fi
  SUDO=(sudo)
}

apt_has_candidate() {
  local pkg="$1"
  apt-cache policy "$pkg" 2>/dev/null | awk '/Candidate:/ {print $2}' | grep -qxv '(none)'
}

install_apt_if_missing() {
  local pkg="$1"
  if dpkg -s "$pkg" >/dev/null 2>&1; then
    info "skip installed package: $pkg"
    return 0
  fi
  if ! apt_has_candidate "$pkg"; then
    warn "package not available from apt, skipping: $pkg"
    return 0
  fi
  run "${SUDO[@]}" apt-get install -y "$pkg"
}

ensure_node_18() {
  local current_major=""
  if have_cmd node; then
    current_major="$(node -v | sed -E 's/^v([0-9]+).*/\1/')"
    if [[ "$current_major" == "$NODE_MAJOR" ]]; then
      info "Node $NODE_MAJOR already available: $(node -v)"
      return 0
    fi
    warn "node exists but is not Node $NODE_MAJOR: $(node -v)"
  fi

  if apt_has_candidate "nodejs"; then
    install_apt_if_missing nodejs
  else
    warn "nodejs apt package unavailable; install Node $NODE_MAJOR manually if bench setup needs it"
  fi
}

ensure_yarn() {
  if have_cmd yarn; then
    info "yarn already available: $(yarn --version)"
    return 0
  fi
  if have_cmd corepack; then
    run corepack enable || warn "corepack enable failed; trying apt/npm fallback"
  fi
  if have_cmd yarn; then
    info "yarn available after corepack: $(yarn --version)"
    return 0
  fi
  if apt_has_candidate yarnpkg; then
    install_apt_if_missing yarnpkg
    return 0
  fi
  if have_cmd npm; then
    run "${SUDO[@]}" npm install -g yarn || warn "npm yarn install failed"
    return 0
  fi
  warn "yarn is missing and no installer path was available"
}

ensure_services() {
  local svc
  for svc in redis-server mariadb; do
    if ! systemctl list-unit-files "$svc.service" >/dev/null 2>&1; then
      warn "service missing or not systemd-managed: $svc"
      continue
    fi
    if ! systemctl is-enabled "$svc" >/dev/null 2>&1; then
      run "${SUDO[@]}" systemctl enable "$svc" || warn "could not enable $svc"
    fi
    if ! systemctl is-active "$svc" >/dev/null 2>&1; then
      run "${SUDO[@]}" systemctl start "$svc" || warn "could not start $svc"
    else
      info "service already running: $svc"
    fi
  done
}

install_dependencies() {
  need_sudo
  info "Updating apt package index"
  run "${SUDO[@]}" apt-get update
  run "${SUDO[@]}" apt-get --fix-broken install -y

  local packages=(
    git curl ca-certificates gnupg
    python3 python3-dev python3-pip python3-venv python3-setuptools
    build-essential pkg-config
    redis-server mariadb-server mariadb-client
    libffi-dev libssl-dev libmysqlclient-dev
    libjpeg-dev zlib1g-dev libtiff5-dev liblcms2-dev libwebp-dev
    libxrender1 libxext6 fontconfig xfonts-75dpi xfonts-base
    supervisor nginx
  )

  local pkg
  for pkg in "${packages[@]}"; do
    install_apt_if_missing "$pkg"
  done

  if dpkg -s wkhtmltopdf >/dev/null 2>&1; then
    info "wkhtmltopdf already installed"
  elif apt_has_candidate wkhtmltopdf; then
    install_apt_if_missing wkhtmltopdf
  else
    warn "wkhtmltopdf has no apt candidate; continuing without PDF binary"
  fi

  ensure_node_18
  ensure_yarn
  ensure_services
}

ensure_bench_cli() {
  if have_cmd bench; then
    info "bench already available: $(bench --version 2>/dev/null || true)"
    return 0
  fi
  if have_cmd pipx; then
    run pipx install frappe-bench
  else
    install_apt_if_missing pipx || warn "pipx install skipped/failed; using pip fallback if needed"
    if have_cmd pipx; then
      run pipx install frappe-bench
    else
      run python3 -m pip install --user frappe-bench
      export PATH="$HOME/.local/bin:$PATH"
    fi
  fi
  have_cmd bench || die "bench command is still unavailable after install"
}

valid_bench() {
  [[ -d "$BENCH_DIR/sites" && -d "$BENCH_DIR/apps/frappe" && -f "$BENCH_DIR/Procfile" ]] || return 1
  (cd "$BENCH_DIR" && bench show-config >/dev/null 2>&1)
}

site_names() {
  [[ -d "$BENCH_DIR/sites" ]] || return 0
  find "$BENCH_DIR/sites" -mindepth 1 -maxdepth 1 -type d \
    ! -name assets ! -name archived \
    -exec test -f "{}/site_config.json" \; -printf "%f\n" 2>/dev/null | sort
}

ensure_bench() {
  ensure_bench_cli
  if valid_bench; then
    info "valid bench found, reusing: $BENCH_DIR"
    return 0
  fi
  if [[ -e "$BENCH_DIR" ]]; then
    warn "bench path exists but is not a valid bench: $BENCH_DIR"
    warn "not overwriting it; move it aside manually if a fresh bench is needed"
    return 1
  fi
  run bench init --frappe-branch "$FRAPPE_BRANCH" "$BENCH_DIR"
}

run_site_setup() {
  if [[ ! -x "$SITE_SETUP" ]]; then
    die "site setup script missing or not executable: $SITE_SETUP"
  fi
  run "$SITE_SETUP"
}

start_bench() {
  if [[ -x "$SCRIPT_DIR/start.sh" ]]; then
    run "$SCRIPT_DIR/start.sh" --background
    return 0
  fi
  [[ -d "$BENCH_DIR" ]] || die "bench directory not found: $BENCH_DIR"
  mkdir -p "$SCRIPT_DIR/logs" "$BENCH_DIR/.runner"
  if [[ -f "$BENCH_DIR/.runner/bench_start.pid" ]]; then
    local pid
    pid="$(cat "$BENCH_DIR/.runner/bench_start.pid" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
      info "bench already running with PID $pid"
      return 0
    fi
  fi
  info "starting bench in background"
  (cd "$BENCH_DIR" && nohup bench start >>"$SCRIPT_DIR/logs/bench-start.log" 2>&1 & echo "$!" >"$BENCH_DIR/.runner/bench_start.pid")
}

install_flow() {
  install_dependencies
  ensure_bench
  run_site_setup
}

repair_flow() {
  need_sudo
  ensure_services
  run "${SUDO[@]}" apt-get --fix-broken install -y
  if valid_bench; then
    run bash -lc "cd '$BENCH_DIR' && bench setup requirements"
    run bash -lc "cd '$BENCH_DIR' && bench build"
    local site
    while IFS= read -r site; do
      run bash -lc "cd '$BENCH_DIR' && bench --site '$site' migrate"
    done < <(site_names)
  else
    warn "valid bench not found; skipping bench repair commands"
  fi
  start_bench
  run_site_setup
}

main_menu() {
  while true; do
    printf '\n'
    printf '=================================\n'
    printf ' Frappe Installer and Site Setup\n'
    printf '=================================\n'
    printf 'Log: %s\n\n' "$LOG_FILE"
    printf '1) Install / Setup Frappe\n'
    printf '2) Repair Frappe\n'
    printf '3) Start Bench\n'
    printf '4) Site Setup\n'
    printf '5) Exit\n'
    read -r -p "Choose: " choice
    case "${choice:-}" in
      1) install_flow ;;
      2) repair_flow ;;
      3) start_bench ;;
      4) run_site_setup ;;
      5) info "bye"; exit 0 ;;
      *) warn "invalid option" ;;
    esac
  done
}

main_menu "$@"
