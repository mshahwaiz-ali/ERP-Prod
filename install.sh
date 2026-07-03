#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_DIR="$SCRIPT_DIR/frappe-bench"
LOG_DIR="$SCRIPT_DIR/install_logs"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_DIR/install-$TIMESTAMP.log"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
NODE_MAJOR="${NODE_MAJOR:-24}"
NVM_INSTALL_VERSION="${NVM_INSTALL_VERSION:-v0.40.3}"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PIPX_BIN_DIR="$HOME/.local/bin"

SUDO=()
BENCH_CREATED_THIS_RUN=0

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

info() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
err() { printf '[ERROR] %s\n' "$*" >&2; }
ok() { printf '[OK] %s\n' "$*"; }
die() { err "$*"; exit 1; }

trap 'err "Failed at line $LINENO: $BASH_COMMAND"' ERR

section() {
  printf '\n'
  printf '==================================================\n'
  printf ' %s\n' "$*"
  printf '==================================================\n'
}

run() {
  info "[RUN] $*"
  "$@"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

refresh_path() {
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if [[ -n "${NVM_DIR:-}" && -s "$NVM_DIR/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    . "$NVM_DIR/nvm.sh"
  elif [[ -s "$HOME/.nvm/nvm.sh" ]]; then
    export NVM_DIR="$HOME/.nvm"
    # shellcheck disable=SC1091
    . "$NVM_DIR/nvm.sh"
  fi
}

need_sudo() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    SUDO=()
    return 0
  fi
  have_cmd sudo || die "sudo is required for dependency installation"
  sudo -v || die "sudo permission is required"
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
    warn "package has no apt candidate, skipping: $pkg"
    return 0
  fi
  run "${SUDO[@]}" apt-get install -y "$pkg"
}

install_tiff_dependency() {
  if dpkg -s libtiff-dev >/dev/null 2>&1 || dpkg -s libtiff5-dev >/dev/null 2>&1; then
    info "skip installed package: libtiff-dev/libtiff5-dev"
  elif apt_has_candidate libtiff-dev; then
    install_apt_if_missing libtiff-dev
  elif apt_has_candidate libtiff5-dev; then
    install_apt_if_missing libtiff5-dev
  else
    warn "no libtiff development package candidate found"
  fi
}

ensure_services() {
  local svc unit
  for svc in mariadb redis-server; do
    unit="$svc.service"
    if have_cmd systemctl && systemctl list-unit-files "$unit" >/dev/null 2>&1; then
      if ! systemctl is-enabled "$unit" >/dev/null 2>&1; then
        run "${SUDO[@]}" systemctl enable "$unit" || warn "could not enable $svc"
      fi
      if systemctl is-active "$unit" >/dev/null 2>&1; then
        info "service already running: $svc"
      elif ! run "${SUDO[@]}" systemctl start "$unit"; then
        warn "could not start $svc with systemctl"
      fi
    elif have_cmd service; then
      warn "systemctl unavailable or service not systemd-managed: $svc"
      run "${SUDO[@]}" service "$svc" start || warn "could not start $svc with service"
    else
      warn "could not manage $svc automatically; make sure it is running"
    fi
  done
}

install_dependencies() {
  section "System Dependencies"
  need_sudo
  run "${SUDO[@]}" apt-get update
  run "${SUDO[@]}" apt-get --fix-broken install -y

  local packages=(
    git curl ca-certificates gnupg
    build-essential pkg-config
    python3 python3-dev python3-pip python3-venv python3-setuptools pipx
    redis-server mariadb-server mariadb-client
    libffi-dev libssl-dev libmysqlclient-dev
    libjpeg-dev zlib1g-dev liblcms2-dev libwebp-dev
    libxrender1 libxext6 fontconfig xfonts-75dpi xfonts-base
    cron
  )

  local pkg
  for pkg in "${packages[@]}"; do
    install_apt_if_missing "$pkg"
  done
  install_tiff_dependency

  if dpkg -s wkhtmltopdf >/dev/null 2>&1; then
    info "wkhtmltopdf already installed"
  elif apt_has_candidate wkhtmltopdf; then
    install_apt_if_missing wkhtmltopdf
  else
    warn "wkhtmltopdf has no apt candidate; PDF generation may need manual setup"
  fi

  ensure_services
}

ensure_nvm() {
  export NVM_DIR="$HOME/.nvm"
  if [[ -s "$NVM_DIR/nvm.sh" ]]; then
    # shellcheck disable=SC1091
    . "$NVM_DIR/nvm.sh"
    return 0
  fi

  have_cmd curl || die "curl is required to install nvm"
  info "Installing nvm into $NVM_DIR"
  run bash -c "curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_INSTALL_VERSION}/install.sh | bash"
  [[ -s "$NVM_DIR/nvm.sh" ]] || die "nvm install completed but $NVM_DIR/nvm.sh was not found"
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh"
}

ensure_node() {
  section "Node"
  refresh_path
  if have_cmd node; then
    local existing_major
    existing_major="$(node -v | sed -E 's/^v([0-9]+).*/\1/')"
    if [[ "$existing_major" != "$NODE_MAJOR" ]]; then
      warn "node exists but is not Node $NODE_MAJOR: $(node -v)"
      warn "using nvm Node $NODE_MAJOR for this script session"
    fi
  fi
  ensure_nvm
  run nvm install "$NODE_MAJOR"
  run nvm alias default "$NODE_MAJOR"
  run nvm use "$NODE_MAJOR"
  hash -r

  have_cmd node || die "node is unavailable after nvm setup"
  have_cmd npm || die "npm is unavailable after nvm setup"

  local current_major
  current_major="$(node -v | sed -E 's/^v([0-9]+).*/\1/')"
  [[ "$current_major" == "$NODE_MAJOR" ]] || die "active node is $(node -v), expected Node $NODE_MAJOR"

  ok "node $(node -v)"
  ok "npm $(npm -v)"
}

ensure_yarn() {
  section "Yarn"
  refresh_path
  have_cmd npm || die "npm is required before installing yarn"
  if ! have_cmd yarn; then
    run npm install -g yarn
    refresh_path
  fi
  have_cmd yarn || die "yarn command is unavailable after install"
  ok "yarn $(yarn --version)"
}

ensure_pipx() {
  refresh_path
  if have_cmd pipx; then
    info "pipx available: $(pipx --version 2>/dev/null || true)"
    run pipx ensurepath || true
    refresh_path
    return 0
  fi

  need_sudo
  install_apt_if_missing pipx
  refresh_path

  if have_cmd pipx; then
    run pipx ensurepath || true
    refresh_path
    return 0
  fi

  return 1
}

pip_user_install() {
  local package="$1"
  run python3 -m pip install --user "$package" || run python3 -m pip install --user --break-system-packages "$package"
  refresh_path
}

ensure_uv() {
  section "uv"
  refresh_path
  if have_cmd uv; then
    ok "$(uv --version 2>/dev/null || true)"
    return 0
  fi

  if ensure_pipx; then
    run pipx install uv || run pipx upgrade uv || warn "pipx could not install/upgrade uv"
    refresh_path
  fi

  if ! have_cmd uv; then
    warn "falling back to user-level pip install for uv"
    pip_user_install uv
  fi

  have_cmd uv || die "uv command is unavailable after install"
  ok "$(uv --version 2>/dev/null || true)"
}

ensure_bench_cli() {
  section "Bench CLI"
  refresh_path
  if have_cmd bench; then
    ok "$(bench --version 2>/dev/null || true)"
    return 0
  fi

  if ensure_pipx; then
    run pipx install frappe-bench || run pipx upgrade frappe-bench || warn "pipx could not install/upgrade frappe-bench"
    refresh_path
  fi

  if ! have_cmd bench; then
    warn "falling back to user-level pip install for frappe-bench"
    pip_user_install frappe-bench
  fi

  have_cmd bench || die "bench command is unavailable after install"
  ok "$(bench --version 2>/dev/null || true)"
}

valid_bench() {
  [[ -d "$BENCH_DIR/apps/frappe" ]] || return 1
  [[ -d "$BENCH_DIR/sites" ]] || return 1
  [[ -x "$BENCH_DIR/env/bin/python" ]] || return 1
  [[ -f "$BENCH_DIR/Procfile" ]] || return 1
  [[ -f "$BENCH_DIR/sites/common_site_config.json" ]] || return 1
  [[ -f "$BENCH_DIR/sites/apps.txt" ]] || return 1
  return 0
}

rollback_new_failed_bench() {
  [[ "$BENCH_CREATED_THIS_RUN" -eq 1 ]] || return 0
  [[ -e "$BENCH_DIR" ]] || return 0
  valid_bench && return 0

  local failed_dir="$SCRIPT_DIR/frappe-bench.failed-$TIMESTAMP"
  if [[ -e "$failed_dir" ]]; then
    failed_dir="$failed_dir.$$"
  fi
  warn "bench init did not complete; moving incomplete bench to: $failed_dir"
  run mv "$BENCH_DIR" "$failed_dir"
}

ensure_bench() {
  section "Bench"
  refresh_path
  ensure_bench_cli
  ensure_uv
  ensure_node
  ensure_yarn
  refresh_path

  if valid_bench; then
    ok "valid bench found, reusing: $BENCH_DIR"
    return 0
  fi

  if [[ -e "$BENCH_DIR" ]]; then
    err "Existing frappe-bench is incomplete. Move it manually or delete it, then rerun installer."
    err "Path: $BENCH_DIR"
    exit 1
  fi

  BENCH_CREATED_THIS_RUN=1
  info "initializing Frappe bench: $BENCH_DIR"
  if ! run bench init --frappe-branch "$FRAPPE_BRANCH" "$BENCH_DIR"; then
    rollback_new_failed_bench
    die "bench init failed; no site was created"
  fi

  if ! valid_bench; then
    rollback_new_failed_bench
    die "bench init finished but validation failed"
  fi

  ok "bench initialized: $BENCH_DIR"
}

print_cmd_version() {
  local label="$1"
  shift
  local cmd="$1"
  if have_cmd "$cmd"; then
    info "$label: $("$@" 2>&1 | sed -n '1p')"
  else
    warn "$label: missing"
  fi
}

environment_summary() {
  section "Environment Summary"
  refresh_path
  print_cmd_version "node" node -v
  print_cmd_version "npm" npm -v
  print_cmd_version "yarn" yarn --version
  print_cmd_version "uv" uv --version
  print_cmd_version "bench" bench --version
  print_cmd_version "python3" python3 --version
  print_cmd_version "mariadb" mariadb --version
  print_cmd_version "redis-server" redis-server --version
}

final_summary() {
  section "Final Summary"
  environment_summary
  if valid_bench; then
    ok "Bench validation passed: $BENCH_DIR"
    ok "Install completed. Next run ./site_setup.sh to create sites."
    ok "Credentials created during site setup will be saved to ./secrets.md"
  else
    die "Install finished but bench validation failed"
  fi
  info "Log file: $LOG_FILE"
}

install_flow() {
  section "Frappe v15 Local Installer"
  install_dependencies
  ensure_bench
  final_summary
}

run_local_script() {
  local script="$1"
  shift || true
  [[ -f "$script" ]] || die "required local script is missing: $script"
  if [[ ! -x "$script" ]]; then
    run chmod +x "$script"
  fi
  run "$script" "$@"
}

local_development_menu() {
  while true; do
    printf '\n'
    printf '=================================\n'
    printf ' Local / Development Setup\n'
    printf '=================================\n'
    printf 'Bench: %s\n' "$BENCH_DIR"
    printf 'Log:   %s\n\n' "$LOG_FILE"
    printf '1) Install / Setup Frappe\n'
    printf '2) Site Setup\n'
    printf '3) Start Bench\n'
    printf '4) Stop Bench\n'
    printf '5) Status\n'
    printf '6) Back\n'
    read -r -p "Choose: " choice
    case "${choice:-}" in
      1) install_flow ;;
      2) run_local_script "$SCRIPT_DIR/site_setup.sh" ;;
      3) run_local_script "$SCRIPT_DIR/start.sh" --background ;;
      4) run_local_script "$SCRIPT_DIR/start.sh" --stop ;;
      5) run_local_script "$SCRIPT_DIR/start.sh" --status ;;
      6) return 0 ;;
      *) warn "invalid option" ;;
    esac
  done
}

production_setup_flow() {
  local production_script="$SCRIPT_DIR/deploy/production_setup.sh"
  section "Production / EC2 Setup"
  warn "Production mode is for real EC2/server deployment and uses nginx/supervisor."
  warn "This path does not run bench start or use start.sh."
  if [[ ! -f "$production_script" ]]; then
    die "production setup script is missing: $production_script"
  fi
  if [[ ! -x "$production_script" ]]; then
    run chmod +x "$production_script"
  fi
  run "$production_script"
}

main_menu() {
  while true; do
    printf '\n'
    printf '=================================\n'
    printf ' Frappe Installer\n'
    printf '=================================\n'
    printf 'Bench: %s\n' "$BENCH_DIR"
    printf 'Log:   %s\n\n' "$LOG_FILE"
    printf '1) Local / Development Setup\n'
    printf '2) Production / EC2 Setup\n'
    printf '3) Exit\n'
    read -r -p "Choose: " choice
    case "${choice:-}" in
      1) local_development_menu ;;
      2) production_setup_flow ;;
      3) info "bye"; exit 0 ;;
      *) warn "invalid option" ;;
    esac
  done
}

main_menu "$@"
