#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
BENCH_DIR="$ROOT_DIR/frappe-bench"
P_APPS_DIR="$ROOT_DIR/p_apps"
LOG_DIR="$ROOT_DIR/logs"
BACKGROUND=0
STOP=0
STATUS=0
declare -a SITES=()
declare -a SELECTED_SITES=()

info() { printf '[INFO] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*" >&2; }
err() { printf '[ERROR] %s\n' "$*" >&2; }
die() { err "$*"; exit 1; }
trap 'err "Failed at line $LINENO: $BASH_COMMAND"' ERR

usage() {
  cat <<'EOF'
Usage: ./start.sh [options]

Development/local runner only. This is not production service management.

Options:
  --bench-dir PATH   Bench directory (default: ./frappe-bench)
  --background       Start bench start in background
  --stop             Stop tracked dev process for this bench
  --status           Show bench/site/process status
  --help             Show this help
EOF
}

confirm() { local a d="${2:-n}" s; [[ "$d" == "y" ]] && s="Y/n" || s="y/N"; read -r -p "$1 [$s]: " a; a="${a:-$d}"; [[ "$a" =~ ^[Yy] ]]; }
prompt_default() { local a; read -r -p "$1 [$2]: " a; printf '%s\n' "${a:-$2}"; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"; }
make_log_dir() { mkdir -p "$LOG_DIR"; }
run() { info "Running: $*"; "$@"; }
sudo_run() { run sudo "$@"; }

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --bench-dir) BENCH_DIR="$2"; shift 2 ;;
      --background) BACKGROUND=1; shift ;;
      --stop) STOP=1; shift ;;
      --status) STATUS=1; shift ;;
      --help|-h) usage; exit 0 ;;
      *) die "Unknown option: $1" ;;
    esac
  done
}

verify_bench() {
  [[ -d "$BENCH_DIR/apps" && -d "$BENCH_DIR/sites" && -d "$BENCH_DIR/env" ]] || die "$BENCH_DIR does not look like a Frappe bench."
}

list_sites() {
  local dir
  SITES=()
  while IFS= read -r -d '' dir; do
    SITES+=("$(basename "$dir")")
  done < <(find "$BENCH_DIR/sites" -mindepth 1 -maxdepth 1 -type d -exec test -f '{}/site_config.json' ';' -print0 | sort -z)
  [[ "${#SITES[@]}" -gt 0 ]] || die "No Frappe sites found in $BENCH_DIR/sites. Run ./install.sh first."
}

print_sites() {
  local i
  for i in "${!SITES[@]}"; do printf '  %s) %s\n' "$((i+1))" "${SITES[$i]}"; done
}

parse_selection() {
  local input="$1" part start end i
  SELECTED_SITES=()
  if [[ "$input" == "all" ]]; then SELECTED_SITES=("${SITES[@]}"); return; fi
  IFS=',' read -ra parts <<<"$input"
  for part in "${parts[@]}"; do
    part="${part// /}"
    if [[ "$part" =~ ^([0-9]+)-([0-9]+)$ ]]; then
      start="${BASH_REMATCH[1]}"; end="${BASH_REMATCH[2]}"
      [[ "$start" -le "$end" ]] || die "Invalid range: $part"
      for ((i=start; i<=end; i++)); do
        [[ "$i" -ge 1 && "$i" -le "${#SITES[@]}" ]] || die "Site index out of range: $i"
        SELECTED_SITES+=("${SITES[$((i-1))]}")
      done
    elif [[ "$part" =~ ^[0-9]+$ ]]; then
      [[ "$part" -ge 1 && "$part" -le "${#SITES[@]}" ]] || die "Site index out of range: $part"
      SELECTED_SITES+=("${SITES[$((part-1))]}")
    else
      die "Invalid site selection: $part"
    fi
  done
}

choose_sites() {
  print_sites
  parse_selection "$(prompt_default "Select sites to use/open (1, 1,2, 1-3, all)" "1")"
}

ensure_hosts_entry() {
  local site="$1" line="127.0.0.1 $site # managed-by-frappe-custom-installer"
  grep -Eq "^[[:space:]]*127[.]0[.]0[.]1[[:space:]]+$site([[:space:]]|$)" /etc/hosts && return 0
  confirm "Add $site to /etc/hosts using sudo?" "y" || {
    warn "Skipping /etc/hosts entry for $site. The URL may not resolve until you add it manually."
    return 0
  }
  printf '%s\n' "$line" | sudo tee -a /etc/hosts >/dev/null
}

is_process_in_bench() {
  local pid="$1" cwd cmd
  [[ -d "/proc/$pid" ]] || return 1
  cwd="$(readlink -f "/proc/$pid/cwd" 2>/dev/null || true)"
  cmd="$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null || true)"
  [[ "$cwd" == "$BENCH_DIR"* || "$cmd" == *"$BENCH_DIR"* ]]
}

kill_pid_safely() {
  local pid="$1" pgid
  [[ "$pid" =~ ^[0-9]+$ ]] || return 0
  if is_process_in_bench "$pid"; then
    pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ' || true)"
    if [[ -n "$pgid" ]]; then kill "-$pgid" 2>/dev/null || true; else kill "$pid" 2>/dev/null || true; fi
  fi
}

stop_bench() {
  local pidfile="$BENCH_DIR/.runner/bench_start.pid" pid pfile
  if [[ -f "$pidfile" ]]; then
    pid="$(<"$pidfile")"
    kill_pid_safely "$pid"
    rm -f "$pidfile"
  fi
  if [[ -d "$BENCH_DIR/config/pids" ]]; then
    while IFS= read -r -d '' pfile; do
      pid="$(<"$pfile" 2>/dev/null || true)"
      kill_pid_safely "$pid"
    done < <(find "$BENCH_DIR/config/pids" -type f -print0)
  fi
  sleep 2
  info "Stopped tracked dev processes for $BENCH_DIR where found."
}

show_status() {
  local pidfile="$BENCH_DIR/.runner/bench_start.pid" pid running="no" site
  [[ -f "$pidfile" ]] && pid="$(<"$pidfile")" && is_process_in_bench "$pid" && running="yes (PID $pid)"
  printf 'Bench dir: %s\n' "$BENCH_DIR"
  printf 'Detected sites:\n'; printf '  %s\n' "${SITES[@]}"
  printf 'Tracked bench start running: %s\n' "$running"
  printf 'URLs:\n'; for site in "${SITES[@]}"; do printf '  http://%s:8000\n' "$site"; done
  if command -v ss >/dev/null 2>&1; then ss -ltnp 2>/dev/null || true; fi
}

start_foreground() {
  local site
  info "Stopping existing tracked dev processes for this bench only..."
  stop_bench
  for site in "${SELECTED_SITES[@]}"; do ensure_hosts_entry "$site"; done
  info "bench start runs one bench-level dev process. Selected sites are the URLs to use; code is shared at bench level, while site folders/databases are separate."
  info "Leaving bench default_site untouched so host-header routing can serve multiple sites."
  cd "$BENCH_DIR"
  printf 'URLs:\n'; for site in "${SELECTED_SITES[@]}"; do printf '  http://%s:8000\n' "$site"; done
  exec bench start
}

start_background() {
  local site log_file="$LOG_DIR/bench-start.log" pidfile="$BENCH_DIR/.runner/bench_start.pid"
  make_log_dir
  mkdir -p "$BENCH_DIR/.runner"
  info "Stopping existing tracked dev processes for this bench only..."
  stop_bench
  for site in "${SELECTED_SITES[@]}"; do ensure_hosts_entry "$site"; done
  cd "$BENCH_DIR"
  info "Leaving bench default_site untouched so host-header routing can serve multiple sites."
  setsid bench start >"$log_file" 2>&1 &
  printf '%s\n' "$!" >"$pidfile"
  info "PID: $(<"$pidfile")"
  info "Log: $log_file"
  printf 'URLs:\n'; for site in "${SELECTED_SITES[@]}"; do printf '  http://%s:8000\n' "$site"; done
  info "Stop command: ./start.sh --stop"
}

main() {
  parse_args "$@"
  info "Development/local runner only. Do not use bench start as a production service."
  verify_bench
  list_sites
  if [[ "$STOP" -eq 1 ]]; then stop_bench; exit 0; fi
  if [[ "$STATUS" -eq 1 ]]; then show_status; exit 0; fi
  choose_sites
  if [[ "$BACKGROUND" -eq 1 ]]; then start_background; else start_foreground; fi
}

main "$@"
