#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_DIR="$SCRIPT_DIR/frappe-bench"
APPS_SRC="$SCRIPT_DIR/p_apps"
LOG_DIR="$SCRIPT_DIR/install_logs"
RUN_LOG="$LOG_DIR/site-setup-$(date +%Y%m%d-%H%M%S).log"
BENCH_LOG_DIR="$SCRIPT_DIR/logs"
BENCH_LOG="$BENCH_LOG_DIR/bench-start.log"
ADMIN_PASSWORD="${FRAPPE_ADMIN_PASSWORD:-admin}"

mkdir -p "$LOG_DIR" "$BENCH_LOG_DIR"
exec > >(tee -a "$RUN_LOG") 2>&1

info() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*"; }
err() { printf '[ERROR] %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }

run() {
  info "[RUN] $*"
  "$@"
}

bench_run() {
  [[ -d "$BENCH_DIR" ]] || die "bench directory not found: $BENCH_DIR"
  info "[RUN] bench $*"
  (cd "$BENCH_DIR" && bench "$@")
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

need_sudo() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    SUDO=()
    return 0
  fi
  have_cmd sudo || die "sudo is required for automatic MariaDB site setup"
  sudo -v || die "sudo permission is required"
  SUDO=(sudo)
}

valid_bench() {
  [[ -d "$BENCH_DIR/sites" && -d "$BENCH_DIR/apps/frappe" && -f "$BENCH_DIR/Procfile" ]] || return 1
  (cd "$BENCH_DIR" && bench show-config >/dev/null 2>&1)
}

site_names() {
  [[ -d "$BENCH_DIR/sites" ]] || return 0
  find "$BENCH_DIR/sites" -mindepth 1 -maxdepth 1 -type d \
    ! -name assets ! -name archived ! -name common_site_config.json \
    -exec test -f "{}/site_config.json" \; -printf "%f\n" 2>/dev/null | sort
}

app_name_from_dir() {
  local dir="$1"
  basename "$dir"
}

is_system_app() {
  case "$1" in
    frappe|erpnext|payments|hrms|print_designer) return 0 ;;
    *) return 1 ;;
  esac
}

valid_custom_app_dir() {
  local dir="$1"
  [[ -d "$dir" ]] || return 1
  [[ -f "$dir/hooks.py" ]] || return 1
  [[ -f "$dir/__init__.py" ]] || return 1
  return 0
}

discover_source_apps() {
  [[ -d "$APPS_SRC" ]] || return 0
  local dir name
  for dir in "$APPS_SRC"/*; do
    [[ -d "$dir" ]] || continue
    name="$(app_name_from_dir "$dir")"
    is_system_app "$name" && continue
    valid_custom_app_dir "$dir" || {
      warn "skip invalid app: $name"
      continue
    }
    printf '%s\n' "$name"
  done | sort
}

discover_bench_custom_apps() {
  [[ -d "$BENCH_DIR/apps" ]] || return 0
  local dir name
  for dir in "$BENCH_DIR/apps"/*; do
    [[ -d "$dir" ]] || continue
    name="$(app_name_from_dir "$dir")"
    is_system_app "$name" && continue
    valid_custom_app_dir "$dir" || continue
    printf '%s\n' "$name"
  done | sort
}

copy_custom_apps() {
  [[ -d "$APPS_SRC" ]] || {
    warn "apps source folder missing: $APPS_SRC"
    return 0
  }
  valid_bench || die "valid bench not found: $BENCH_DIR"

  local app src dest
  while IFS= read -r app; do
    [[ -n "$app" ]] || continue
    src="$APPS_SRC/$app"
    dest="$BENCH_DIR/apps/$app"
    if [[ -e "$dest" ]]; then
      warn "skip existing app, no overwrite: $app"
    else
      info "copying app: $app"
      run cp -a "$src" "$dest"
    fi
  done < <(discover_source_apps)
}

prepare_app_imports() {
  valid_bench || die "valid bench not found: $BENCH_DIR"
  local app app_dir
  while IFS= read -r app; do
    [[ -n "$app" ]] || continue
    app_dir="$BENCH_DIR/apps/$app"
    [[ -d "$app_dir" ]] || continue
    info "preparing python import for app: $app"
    if [[ -f "$app_dir/pyproject.toml" || -f "$app_dir/setup.py" || -f "$app_dir/setup.cfg" ]]; then
      (cd "$BENCH_DIR" && ./env/bin/python -m pip install -e "apps/$app") || warn "editable install failed for $app"
    else
      warn "no python package metadata found for $app; skipping editable install"
    fi
  done < <(discover_bench_custom_apps)
}

ensure_custom_app_assets() {
  valid_bench || die "valid bench not found: $BENCH_DIR"
  mkdir -p "$BENCH_DIR/sites/assets"

  local app public_dir asset_link
  while IFS= read -r app; do
    [[ -n "$app" ]] || continue
    public_dir="$BENCH_DIR/apps/$app/public"
    asset_link="$BENCH_DIR/sites/assets/$app"
    [[ -d "$public_dir" ]] || continue
    if [[ -L "$asset_link" ]]; then
      local target
      target="$(readlink "$asset_link")"
      if [[ "$target" == "$public_dir" ]]; then
        info "asset link ok: $app"
      else
        warn "asset link points elsewhere, replacing: $app"
        run rm -f "$asset_link"
        run ln -s "$public_dir" "$asset_link"
      fi
    elif [[ -e "$asset_link" ]]; then
      warn "asset path exists and is not a symlink, leaving untouched: $asset_link"
    else
      run ln -s "$public_dir" "$asset_link"
    fi
  done < <(discover_bench_custom_apps)
}

sync_custom_apps() {
  copy_custom_apps
  prepare_app_imports
  ensure_custom_app_assets
}

bench_pid_running() {
  local pid_file="$BENCH_DIR/.runner/bench_start.pid"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" >/dev/null 2>&1
}

bench_process_for_dir_running() {
  pgrep -af "bench start" 2>/dev/null | grep -F "$BENCH_DIR" >/dev/null 2>&1
}

start_bench_background() {
  valid_bench || die "valid bench not found: $BENCH_DIR"
  mkdir -p "$BENCH_DIR/.runner" "$BENCH_LOG_DIR"

  if bench_pid_running || bench_process_for_dir_running; then
    info "bench already appears to be running"
    return 0
  fi

  info "starting bench in background"
  (
    cd "$BENCH_DIR"
    nohup bench start >>"$BENCH_LOG" 2>&1 &
    printf '%s\n' "$!" >"$BENCH_DIR/.runner/bench_start.pid"
  )
  sleep 2
  if bench_pid_running || bench_process_for_dir_running; then
    info "bench started; log: $BENCH_LOG"
  else
    warn "bench did not stay running; check log: $BENCH_LOG"
  fi
}

random_hex() {
  if have_cmd openssl; then
    openssl rand -hex "$1"
  else
    date +%s%N | sha256sum | cut -c "1-$(("$1" * 2))"
  fi
}

make_db_name() {
  printf '_%s' "$(random_hex 8)"
}

make_db_password() {
  random_hex 18
}

sql_quote() {
  printf "%s" "$1" | sed "s/'/''/g"
}

create_database_and_user() {
  local db_name="$1"
  local db_password="$2"
  need_sudo

  local quoted_pass
  quoted_pass="$(sql_quote "$db_password")"
  info "creating MariaDB database/user automatically via sudo socket auth"
  "${SUDO[@]}" mariadb <<SQL
CREATE DATABASE IF NOT EXISTS \`$db_name\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$db_name'@'localhost' IDENTIFIED BY '$quoted_pass';
ALTER USER '$db_name'@'localhost' IDENTIFIED BY '$quoted_pass';
GRANT ALL PRIVILEGES ON \`$db_name\`.* TO '$db_name'@'localhost';
FLUSH PRIVILEGES;
SQL
}

select_apps() {
  local -n _out="$1"
  mapfile -t available < <(discover_bench_custom_apps)
  _out=()

  if [[ "${#available[@]}" -eq 0 ]]; then
    warn "no custom apps available"
    return 0
  fi

  printf '\nSelect app(s) for this site:\n'
  local i
  for i in "${!available[@]}"; do
    printf '  %d) %s\n' "$((i + 1))" "${available[$i]}"
  done
  printf '  all) Install all\n'

  local choice part idx
  while true; do
    read -r -p "Choose apps (example 1,2 or all): " choice
    choice="${choice//[[:space:]]/}"
    if [[ "$choice" == "all" ]]; then
      _out=("${available[@]}")
      return 0
    fi
    if [[ -z "$choice" ]]; then
      warn "please choose at least one app"
      continue
    fi
    IFS=',' read -ra parts <<<"$choice"
    _out=()
    local ok=1
    for part in "${parts[@]}"; do
      if [[ ! "$part" =~ ^[0-9]+$ ]]; then
        ok=0
        break
      fi
      idx=$((part - 1))
      if (( idx < 0 || idx >= ${#available[@]} )); then
        ok=0
        break
      fi
      _out+=("${available[$idx]}")
    done
    if (( ok == 1 && ${#_out[@]} > 0 )); then
      return 0
    fi
    warn "invalid app selection"
  done
}

print_site_summary() {
  local site="$1"
  printf '\nSite ready: http://%s:8000\n' "$site"
  if bench_run --site "$site" list-apps; then
    true
  else
    warn "could not read installed apps for $site"
  fi
}

create_site_once() {
  sync_custom_apps
  start_bench_background

  local site
  while true; do
    read -r -p "Site name (example xyz.local): " site
    site="${site//[[:space:]]/}"
    [[ -n "$site" ]] || {
      warn "site name is required"
      continue
    }
    [[ "$site" == *.* ]] || warn "site name usually includes a domain suffix, example xyz.local"
    if [[ -d "$BENCH_DIR/sites/$site" ]]; then
      warn "site already exists: $site"
      continue
    fi
    break
  done

  local selected_apps=()
  select_apps selected_apps

  local db_name db_password
  db_name="$(make_db_name)"
  db_password="$(make_db_password)"
  create_database_and_user "$db_name" "$db_password"

  info "creating site: $site"
  bench_run new-site "$site" \
    --admin-password "$ADMIN_PASSWORD" \
    --db-name "$db_name" \
    --db-password "$db_password" \
    --no-setup-db

  local app failed=0
  for app in "${selected_apps[@]}"; do
    info "installing app on $site: $app"
    if bench_run --site "$site" install-app "$app"; then
      info "app installed: $app"
    else
      err "app install failed: $app"
      failed=1
    fi
  done

  info "running migrate for $site"
  bench_run --site "$site" migrate || failed=1
  print_site_summary "$site"

  if (( failed == 1 )); then
    warn "site completed with one or more errors; check log: $RUN_LOG"
  fi
}

new_site_flow() {
  while true; do
    create_site_once
    local again
    read -r -p "Create another site? y/N: " again
    case "${again:-}" in
      y|Y|yes|YES) continue ;;
      *) break ;;
    esac
  done
}

select_site() {
  local -n _selected="$1"
  mapfile -t sites < <(site_names)
  _selected=""
  if [[ "${#sites[@]}" -eq 0 ]]; then
    warn "no valid sites found"
    return 1
  fi

  printf '\nAvailable sites:\n'
  local i
  for i in "${!sites[@]}"; do
    printf '  %d) %s\n' "$((i + 1))" "${sites[$i]}"
  done

  local choice idx
  while true; do
    read -r -p "Choose site: " choice
    choice="${choice//[[:space:]]/}"
    [[ "$choice" =~ ^[0-9]+$ ]] || {
      warn "invalid site selection"
      continue
    }
    idx=$((choice - 1))
    if (( idx >= 0 && idx < ${#sites[@]} )); then
      _selected="${sites[$idx]}"
      return 0
    fi
    warn "invalid site selection"
  done
}

drop_site_no_backup_supported() {
  (cd "$BENCH_DIR" && bench drop-site --help 2>/dev/null | grep -q -- '--no-backup')
}

delete_site_flow() {
  valid_bench || die "valid bench not found: $BENCH_DIR"
  local site
  select_site site || return 0
  [[ -n "$site" ]] || return 0

  warn "this will delete site: $site"
  local confirm
  read -r -p "Type the site name to delete: " confirm
  if [[ "$confirm" != "$site" ]]; then
    warn "delete cancelled"
    return 0
  fi

  if drop_site_no_backup_supported; then
    bench_run drop-site "$site" --force --no-backup
  else
    warn "bench does not support --no-backup; using compatible drop-site command"
    bench_run drop-site "$site" --force
  fi
}

list_sites_and_apps() {
  valid_bench || die "valid bench not found: $BENCH_DIR"
  local sites site
  mapfile -t sites < <(site_names)
  if [[ "${#sites[@]}" -eq 0 ]]; then
    warn "no valid sites found"
    return 0
  fi

  printf '\nSites and apps:\n'
  for site in "${sites[@]}"; do
    printf '\n- %s\n' "$site"
    if ! bench_run --site "$site" list-apps; then
      warn "could not list apps for $site"
    fi
  done
}

site_menu() {
  valid_bench || die "valid bench not found: $BENCH_DIR"
  sync_custom_apps
  start_bench_background

  while true; do
    printf '\n'
    printf '====================\n'
    printf ' Site Setup Manager\n'
    printf '====================\n'
    printf 'Log: %s\n\n' "$RUN_LOG"
    printf '1) New Site\n'
    printf '2) Delete Site\n'
    printf '3) List Sites and Apps\n'
    printf '4) Exit\n'
    read -r -p "Choose: " choice
    case "${choice:-}" in
      1) new_site_flow ;;
      2) delete_site_flow ;;
      3) list_sites_and_apps ;;
      4) info "bye"; exit 0 ;;
      *) warn "invalid option" ;;
    esac
  done
}

site_menu "$@"
