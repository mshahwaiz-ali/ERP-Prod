#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_DIR="${BENCH_DIR:-$SCRIPT_DIR/frappe-bench}"
LOG_DIR="$SCRIPT_DIR/install_logs"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_DIR/install-$TIMESTAMP.log"
ACTION_LOG="$LOG_DIR/install-$TIMESTAMP.actions"

FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"
DEFAULT_NODE_MAJOR="${NODE_MAJOR:-22}"
NVM_INSTALL_VERSION="${NVM_INSTALL_VERSION:-v0.40.3}"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PIPX_BIN_DIR="$HOME/.local/bin"
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

SUDO=()
BENCH_CREATED_THIS_RUN=0
IS_WSL=0
ENV_MODE="native"
SELECTED_NODE_MAJOR="$DEFAULT_NODE_MAJOR"
YARN_MODE="corepack"

mkdir -p "$LOG_DIR"
touch "$ACTION_LOG"
exec > >(tee -a "$LOG_FILE") 2>&1

info() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*" >&2; }
err() { printf '[ERROR] %s\n' "$*" >&2; }
ok() { printf '[OK] %s\n' "$*"; }
die() { err "$*"; err "Log file: $LOG_FILE"; exit 1; }

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

record_action() {
  printf '%s\n' "$*" >>"$ACTION_LOG"
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

confirm_default_no() {
  local prompt="$1"
  local answer
  read -r -p "$prompt [y/N]: " answer
  [[ "${answer:-}" =~ ^[Yy]$ ]]
}

detect_wsl() {
  IS_WSL=0
  ENV_MODE="native"

  if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null || grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease 2>/dev/null; then
    IS_WSL=1
    ENV_MODE="wsl"
  fi
}

refresh_path() {
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

  if [[ -s "$NVM_DIR/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    . "$NVM_DIR/nvm.sh"
    if [[ -n "${SELECTED_NODE_MAJOR:-}" ]]; then
      nvm use "$SELECTED_NODE_MAJOR" >/dev/null 2>&1 || true
    fi
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
  record_action "INSTALLED_PACKAGE $pkg"
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

service_systemd_usable() {
  have_cmd systemctl || return 1
  systemctl is-system-running >/dev/null 2>&1 || systemctl list-units >/dev/null 2>&1
}

ensure_services() {
  local svc unit

  for svc in mariadb redis-server; do
    unit="$svc.service"

    if service_systemd_usable && systemctl list-unit-files "$unit" >/dev/null 2>&1; then
      if ! systemctl is-enabled "$unit" >/dev/null 2>&1; then
        run "${SUDO[@]}" systemctl enable "$unit" || warn "could not enable $svc"
      fi

      if systemctl is-active "$unit" >/dev/null 2>&1; then
        info "service already running: $svc"
      else
        run "${SUDO[@]}" systemctl start "$unit" || warn "could not start $svc with systemctl"
      fi
    elif have_cmd service; then
      warn "systemctl unavailable/not usable; using service fallback for $svc"
      run "${SUDO[@]}" service "$svc" start || warn "could not start $svc with service"
    else
      warn "could not manage $svc automatically; make sure it is running"
    fi
  done
}

installed_version_or_missing() {
  local label="$1"
  shift

  if have_cmd "$1"; then
    printf '%-18s %s\n' "$label" "$("$@" 2>&1 | sed -n '1p')"
  else
    printf '%-18s missing\n' "$label"
  fi
}

preflight_summary() {
  section "Preflight Summary"
  detect_wsl

  printf 'Repo path:          %s\n' "$SCRIPT_DIR"
  printf 'Bench path:         %s\n' "$BENCH_DIR"
  printf 'Frappe branch:      %s\n' "$FRAPPE_BRANCH"
  printf 'Environment:        %s\n' "$ENV_MODE"
  printf 'Architecture:       %s\n' "$(uname -m)"
  printf 'Kernel:             %s\n' "$(uname -r)"
  printf 'Memory:             %s\n' "$(free -h 2>/dev/null | awk '/Mem:/ {print $2}' || printf unknown)"
  printf '\n'

  installed_version_or_missing "git" git --version
  installed_version_or_missing "curl" curl --version
  installed_version_or_missing "python3" python3 --version
  installed_version_or_missing "node" node -v
  installed_version_or_missing "npm" npm -v
  installed_version_or_missing "yarn" yarn --version
  installed_version_or_missing "mariadb" mariadb --version
  installed_version_or_missing "redis-server" redis-server --version
  installed_version_or_missing "bench" bench --version
  installed_version_or_missing "uv" uv --version
  printf '\n'
}

choose_environment_mode() {
  detect_wsl
  section "Environment Mode"

  if [[ "$IS_WSL" -eq 1 ]]; then
    warn "WSL detected. WSL mode is recommended for Windows laptop/client setups."
    printf '1) WSL / Windows laptop setup [recommended]\n'
    printf '2) Native Linux setup\n'
    read -r -p "Choose [1]: " choice

    case "${choice:-1}" in
      1) ENV_MODE="wsl" ;;
      2) ENV_MODE="native" ;;
      *) warn "invalid choice, using WSL mode"; ENV_MODE="wsl" ;;
    esac
  else
    ENV_MODE="native"
    ok "Native Linux mode selected"
  fi
}

node_major_installed() {
  refresh_path
  have_cmd node || return 1
  node -v | sed -E 's/^v([0-9]+).*/\1/'
}

choose_node_version() {
  section "Node.js Version"
  refresh_path

  local installed_major installed_text recommended choice
  installed_major="$(node_major_installed 2>/dev/null || true)"
  installed_text="missing"

  if [[ -n "$installed_major" ]]; then
    installed_text="$(node -v)"
  fi

  recommended="22"
  if [[ "$DEFAULT_NODE_MAJOR" =~ ^[0-9]+$ ]]; then
    recommended="$DEFAULT_NODE_MAJOR"
  fi

  printf 'Detected Node:      %s\n' "$installed_text"
  printf 'Recommended Node:   %s\n' "$recommended"
  printf '\n'

  if [[ -n "$installed_major" ]]; then
    printf '1) Use installed Node %s [recommended]\n' "$installed_text"
    printf '2) Install/use Node 22 LTS\n'
    printf '3) Install/use Node 24\n'
    printf '4) Manual Node major\n'
    read -r -p "Choose [1]: " choice

    case "${choice:-1}" in
      1) SELECTED_NODE_MAJOR="$installed_major" ;;
      2) SELECTED_NODE_MAJOR="22" ;;
      3) SELECTED_NODE_MAJOR="24" ;;
      4) read -r -p "Enter Node major version: " SELECTED_NODE_MAJOR ;;
      *) warn "invalid choice, using installed Node"; SELECTED_NODE_MAJOR="$installed_major" ;;
    esac
  else
    printf '1) Install/use Node 22 LTS [recommended]\n'
    printf '2) Install/use Node 24\n'
    printf '3) Manual Node major\n'
    read -r -p "Choose [1]: " choice

    case "${choice:-1}" in
      1) SELECTED_NODE_MAJOR="22" ;;
      2) SELECTED_NODE_MAJOR="24" ;;
      3) read -r -p "Enter Node major version: " SELECTED_NODE_MAJOR ;;
      *) warn "invalid choice, using Node 22"; SELECTED_NODE_MAJOR="22" ;;
    esac
  fi

  [[ "$SELECTED_NODE_MAJOR" =~ ^[0-9]+$ ]] || die "invalid Node major version: $SELECTED_NODE_MAJOR"
  ok "selected Node major: $SELECTED_NODE_MAJOR"
}

choose_yarn_mode() {
  section "Yarn Setup"

  printf '1) Corepack/Yarn setup [recommended]\n'
  printf '2) npm global yarn fallback\n'
  printf '3) Use existing yarn if available\n'
  read -r -p "Choose [1]: " choice

  case "${choice:-1}" in
    1) YARN_MODE="corepack" ;;
    2) YARN_MODE="npm-global" ;;
    3) YARN_MODE="existing" ;;
    *) warn "invalid choice, using Corepack"; YARN_MODE="corepack" ;;
  esac
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
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"

  if [[ -s "$NVM_DIR/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    . "$NVM_DIR/nvm.sh"
    return 0
  fi

  have_cmd curl || die "curl is required to install nvm"

  info "Installing nvm into $NVM_DIR"
  run bash -c "curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_INSTALL_VERSION}/install.sh | bash"
  record_action "INSTALLED_NVM $NVM_DIR"

  [[ -s "$NVM_DIR/nvm.sh" ]] || die "nvm install completed but $NVM_DIR/nvm.sh was not found"

  # shellcheck disable=SC1090
  . "$NVM_DIR/nvm.sh"
}

ensure_node() {
  section "Node"
  refresh_path

  local installed_major current_major
  installed_major="$(node_major_installed 2>/dev/null || true)"

  if [[ -n "$installed_major" && "$installed_major" == "$SELECTED_NODE_MAJOR" ]]; then
    ok "using installed node $(node -v)"
    ok "npm $(npm -v)"
    return 0
  fi

  ensure_nvm

  run nvm install "$SELECTED_NODE_MAJOR"
  record_action "INSTALLED_NODE $SELECTED_NODE_MAJOR"
  run nvm alias default "$SELECTED_NODE_MAJOR"
  run nvm use "$SELECTED_NODE_MAJOR"
  hash -r

  have_cmd node || die "node is unavailable after nvm setup"
  have_cmd npm || die "npm is unavailable after nvm setup"

  current_major="$(node -v | sed -E 's/^v([0-9]+).*/\1/')"
  [[ "$current_major" == "$SELECTED_NODE_MAJOR" ]] || die "active node is $(node -v), expected Node $SELECTED_NODE_MAJOR"

  ok "node $(node -v)"
  ok "npm $(npm -v)"
}

ensure_yarn() {
  section "Yarn"
  refresh_path

  if [[ "$YARN_MODE" == "existing" ]]; then
    have_cmd yarn || die "existing yarn selected but yarn is missing"
    ok "yarn $(yarn --version)"
    return 0
  fi

  if [[ "$YARN_MODE" == "corepack" ]]; then
    if have_cmd corepack; then
      run corepack enable || warn "corepack enable failed"
      run corepack prepare yarn@1.22.22 --activate || warn "corepack yarn prepare failed"
      refresh_path
    else
      warn "corepack not available; falling back to npm global yarn"
      YARN_MODE="npm-global"
    fi
  fi

  if ! have_cmd yarn; then
    have_cmd npm || die "npm is required before installing yarn"
    run npm install -g yarn
    record_action "INSTALLED_NPM_GLOBAL yarn"
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
  record_action "ROLLED_BACK_FAILED_BENCH $failed_dir"
}

rollback_prompt() {
  local rc="$1"

  err "Installer failed. Exit code: $rc"
  err "Action log: $ACTION_LOG"

  if [[ "$BENCH_CREATED_THIS_RUN" -eq 1 ]]; then
    rollback_new_failed_bench || true
  fi

  warn "Safe rollback was applied only for incomplete bench created in this run."
  warn "System packages, existing bench, existing sites, and existing databases were not removed."
  err "Log file: $LOG_FILE"
}

on_error() {
  local rc=$?
  err "Failed at line $LINENO: $BASH_COMMAND"
  rollback_prompt "$rc"
  exit "$rc"
}

trap on_error ERR

repair_bench() {
  section "Repair Bench"

  valid_bench || die "cannot repair invalid bench automatically"

  run bash -c "cd '$BENCH_DIR' && ./env/bin/python -m pip install --upgrade pip"
  run bash -c "cd '$BENCH_DIR' && bench setup requirements"

  ok "bench repair completed"
}

recreate_bench() {
  warn "This removes only generated bench folder: $BENCH_DIR"
  read -r -p "Type RECREATE to continue: " confirm

  [[ "$confirm" == "RECREATE" ]] || die "recreate cancelled"

  run rm -rf "$BENCH_DIR"
  record_action "REMOVED_BENCH $BENCH_DIR"
}

bench_choice_for_existing() {
  section "Existing Bench"
  printf 'Existing bench path: %s\n\n' "$BENCH_DIR"

  if valid_bench; then
    printf '1) Reuse existing bench [recommended]\n'
    printf '2) Repair existing bench requirements\n'
    printf '3) Recreate bench\n'
    printf '4) Cancel\n'
    read -r -p "Choose [1]: " choice

    case "${choice:-1}" in
      1) return 0 ;;
      2) repair_bench; return 0 ;;
      3) recreate_bench ;;
      4) die "cancelled" ;;
      *) warn "invalid choice, reusing existing bench"; return 0 ;;
    esac
  else
    warn "Existing frappe-bench is incomplete or invalid."
    printf '1) Move incomplete bench aside and create new bench [recommended]\n'
    printf '2) Cancel\n'
    read -r -p "Choose [1]: " choice

    case "${choice:-1}" in
      1)
        local failed_dir="$SCRIPT_DIR/frappe-bench.incomplete-$TIMESTAMP"
        run mv "$BENCH_DIR" "$failed_dir"
        record_action "MOVED_INCOMPLETE_BENCH $failed_dir"
        ;;
      2) die "cancelled" ;;
      *) die "invalid choice" ;;
    esac
  fi
}

ensure_bench() {
  section "Bench"
  refresh_path

  ensure_bench_cli
  ensure_uv
  ensure_node
  ensure_yarn
  refresh_path

  if [[ -e "$BENCH_DIR" ]]; then
    bench_choice_for_existing
  fi

  if valid_bench; then
    ok "valid bench found, reusing: $BENCH_DIR"
    return 0
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

  record_action "CREATED_BENCH $BENCH_DIR"
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

wsl_final_notes() {
  [[ "$ENV_MODE" == "wsl" ]] || return 0

  section "WSL Notes"
  warn "For Windows browser access, localhost usually works:"
  printf '  http://localhost:8000\n\n'
  warn "For custom site domains, add this to Windows hosts as Administrator:"
  printf '  127.0.0.1 yoursite.local\n\n'
  printf 'PowerShell example:\n'
  printf "  Start-Process powershell -Verb runAs -ArgumentList \"Add-Content -Path C:\\Windows\\System32\\drivers\\etc\\hosts -Value '127.0.0.1 yoursite.local'\"\n"
}

final_summary() {
  section "Final Summary"
  environment_summary

  if valid_bench; then
    ok "Bench validation passed: $BENCH_DIR"
    ok "Local installer completed."
    info "Log file: $LOG_FILE"
    info "Action log: $ACTION_LOG"
    wsl_final_notes

    if [[ -f "$SCRIPT_DIR/site_setup.sh" ]]; then
      printf '\n'
      printf 'Next step:\n'
      printf '1) Run site setup now\n'
      printf '2) Exit\n'
      read -r -p "Choose [2]: " choice

      case "${choice:-2}" in
        1)
          chmod +x "$SCRIPT_DIR/site_setup.sh" 2>/dev/null || true
          run "$SCRIPT_DIR/site_setup.sh"
          ;;
        *) ok "exit. Run ./site_setup.sh later to create/manage sites." ;;
      esac
    else
      warn "site_setup.sh not found. Create/manage sites manually."
    fi
  else
    die "Install finished but bench validation failed"
  fi
}

install_flow() {
  section "Local / Development Installer"

  preflight_summary
  choose_environment_mode
  choose_node_version
  choose_yarn_mode

  printf '\n'
  warn "Installer will skip compatible installed packages and reuse existing bench unless you choose otherwise."
  confirm_default_no "Continue local install?" || die "cancelled"

  install_dependencies
  ensure_bench
  final_summary
}

production_setup_flow() {
  local production_script="$SCRIPT_DIR/deploy/production_setup.sh"

  section "Production / Server Setup"
  warn "Production mode is for real server deployment and uses deploy/production_setup.sh."

  if [[ ! -f "$production_script" ]]; then
    die "production setup script is missing: $production_script"
  fi

  chmod +x "$production_script" 2>/dev/null || true
  run "$production_script"
}

main_menu() {
  preflight_summary

  while true; do
    printf '\n'
    printf '=================================\n'
    printf ' ERP Prod Installer\n'
    printf '=================================\n'
    printf '1) Local / Development Install\n'
    printf '2) Production / Server Install\n'
    printf '3) Exit\n'
    read -r -p "Choose: " choice

    case "${choice:-}" in
      1) install_flow ;;
      2) production_setup_flow ;;
      3) info "bye"; exit 0 ;;
      *) warn "invalid option" ;;
    esac
  done
}

main_menu "$@"
