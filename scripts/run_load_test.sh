#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env}"
K6_BIN="${K6_BIN:-k6}"
LOAD_SCRIPT="${LOAD_SCRIPT:-tests/load/game_api_loadtest.js}"

VERBOSE=0
DRY_RUN=0

OPT_MODE=""
OPT_TARGET_VUS=""
OPT_BASE_URL=""
OPT_WARMUP=""
OPT_HOLD=""
OPT_RAMP_DOWN=""
OPT_MIX_A=""
OPT_MIX_B=""
OPT_MIX_C=""
OPT_ENFORCE_P95=""
OPT_P95_TARGET_MS=""
OPT_ERROR_RATE_THRESHOLD=""
OPT_WRITE_AUTH_MODE=""
OPT_WRITE_RANDOM_IP=""
OPT_USER_POOL_SIZE=""
OPT_REQUEST_TIMEOUT=""
OPT_MAX_ATTEMPTS=""
OPT_BACKOFF_MS=""
OPT_BACKOFF_FACTOR=""
OPT_RETRYABLE_STATUS_CODES=""
OPT_X_API_KEY=""
OPT_ACCESS_TOKEN=""
OPT_SUMMARY_EXPORT=""

K6_EXTRA_ARGS=()

usage() {
  cat <<'EOF'
Run GAME k6 load test in one command.

Usage:
  ./scripts/run_load_test.sh [options] [-- <extra k6 args>]

Options:
  --env-file <path>             Env file to source (default: .env)
  --mode <100|1000>             Preset load mode (default from env or 100)
  --vus <N>                     Override target VUs (TARGET_VUS)
  --base-url <url>              API base URL (BASE_URL)
  --warmup <dur>                Warmup duration (e.g. 30s)
  --hold <dur>                  Hold duration (e.g. 2m)
  --ramp-down <dur>             Ramp-down duration (e.g. 30s)
  --mix-a <pct>                 Scenario A percentage
  --mix-b <pct>                 Scenario B percentage
  --mix-c <pct>                 Scenario C percentage
  --enforce-p95 <0|1>           Enable/disable p95 threshold
  --p95-target-ms <ms>          p95 latency threshold
  --error-rate-threshold <rate> Error rate threshold (0.01 = 1%)
  --write-auth-mode <mode>      apikey|bearer_preferred|bearer (default: apikey)
  --write-random-ip <0|1>       Randomize IP headers for write requests
  --user-pool-size <N>          Number of externalUserIds in pool
  --request-timeout <dur>       HTTP request timeout (e.g. 30s)
  --max-attempts <N>            Retry attempts
  --backoff-ms <N>              Initial backoff in milliseconds
  --backoff-factor <N>          Exponential backoff factor
  --retryable-status-codes <l>  Comma-separated retryable statuses
  --x-api-key <key>             Force X_API_KEY for /games auth
  --access-token <token>        Force ACCESS_TOKEN (Bearer)
  --summary-export <path>       k6 --summary-export output path
  --dry-run                     Print resolved config and command only
  --verbose                     Print extra debug output
  -h, --help                    Show this help

Examples:
  ./scripts/run_load_test.sh
  ./scripts/run_load_test.sh --mode 1000
  ./scripts/run_load_test.sh --vus 300 --mix-a 60 --mix-b 30 --mix-c 10
  ./scripts/run_load_test.sh --env-file .env.integrated --mode 100 --summary-export /tmp/k6-summary.json
  ./scripts/run_load_test.sh -- --http-debug=full
EOF
}

log() {
  printf '[LOAD] %s\n' "$*"
}

debug() {
  if [[ "$VERBOSE" == "1" ]]; then
    printf '[LOAD][debug] %s\n' "$*"
  fi
}

warn() {
  printf '[LOAD][warn] %s\n' "$*" >&2
}

fail() {
  printf '[LOAD][error] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing required command: $cmd"
}

mask_secret() {
  local value="$1"
  local length="${#value}"
  if (( length <= 10 )); then
    printf '***'
    return
  fi
  printf '%s...%s' "${value:0:6}" "${value:length-4:4}"
}

load_env_file() {
  local path="$1"
  [[ -f "$path" ]] || fail "Env file not found: $path"
  log "Loading environment from $path"

  local -r valid_env_pattern='^[[:space:]]*(#|$|export[[:space:]]+[A-Za-z_][A-Za-z0-9_]*=|[A-Za-z_][A-Za-z0-9_]*=)'
  local invalid_count
  invalid_count="$(grep -Evc "$valid_env_pattern" "$path" || true)"
  if [[ "${invalid_count:-0}" != "0" ]]; then
    warn "Ignoring $invalid_count invalid env line(s) in $path (example: variable names with '-')."
  fi

  set -a
  # shellcheck disable=SC1090
  source <(grep -E "$valid_env_pattern" "$path")
  set +a
}

export_if_set() {
  local key="$1"
  local value="$2"
  if [[ -n "$value" ]]; then
    export "$key=$value"
  fi
}

validate_mode() {
  local mode="$1"
  [[ "$mode" == "100" || "$mode" == "1000" ]] || fail "--mode must be 100 or 1000"
}

parse_args() {
  while (( "$#" )); do
    case "$1" in
      --env-file)
        shift
        [[ "${1:-}" != "" ]] || fail "--env-file requires a path"
        ENV_FILE="$1"
        ;;
      --mode)
        shift
        [[ "${1:-}" != "" ]] || fail "--mode requires a value"
        OPT_MODE="$1"
        ;;
      --vus)
        shift
        [[ "${1:-}" != "" ]] || fail "--vus requires a value"
        OPT_TARGET_VUS="$1"
        ;;
      --base-url)
        shift
        [[ "${1:-}" != "" ]] || fail "--base-url requires a value"
        OPT_BASE_URL="$1"
        ;;
      --warmup)
        shift
        [[ "${1:-}" != "" ]] || fail "--warmup requires a value"
        OPT_WARMUP="$1"
        ;;
      --hold)
        shift
        [[ "${1:-}" != "" ]] || fail "--hold requires a value"
        OPT_HOLD="$1"
        ;;
      --ramp-down)
        shift
        [[ "${1:-}" != "" ]] || fail "--ramp-down requires a value"
        OPT_RAMP_DOWN="$1"
        ;;
      --mix-a)
        shift
        [[ "${1:-}" != "" ]] || fail "--mix-a requires a value"
        OPT_MIX_A="$1"
        ;;
      --mix-b)
        shift
        [[ "${1:-}" != "" ]] || fail "--mix-b requires a value"
        OPT_MIX_B="$1"
        ;;
      --mix-c)
        shift
        [[ "${1:-}" != "" ]] || fail "--mix-c requires a value"
        OPT_MIX_C="$1"
        ;;
      --enforce-p95)
        shift
        [[ "${1:-}" != "" ]] || fail "--enforce-p95 requires a value"
        OPT_ENFORCE_P95="$1"
        ;;
      --p95-target-ms)
        shift
        [[ "${1:-}" != "" ]] || fail "--p95-target-ms requires a value"
        OPT_P95_TARGET_MS="$1"
        ;;
      --error-rate-threshold)
        shift
        [[ "${1:-}" != "" ]] || fail "--error-rate-threshold requires a value"
        OPT_ERROR_RATE_THRESHOLD="$1"
        ;;
      --write-auth-mode)
        shift
        [[ "${1:-}" != "" ]] || fail "--write-auth-mode requires a value"
        OPT_WRITE_AUTH_MODE="$1"
        ;;
      --write-random-ip)
        shift
        [[ "${1:-}" != "" ]] || fail "--write-random-ip requires a value"
        OPT_WRITE_RANDOM_IP="$1"
        ;;
      --user-pool-size)
        shift
        [[ "${1:-}" != "" ]] || fail "--user-pool-size requires a value"
        OPT_USER_POOL_SIZE="$1"
        ;;
      --request-timeout)
        shift
        [[ "${1:-}" != "" ]] || fail "--request-timeout requires a value"
        OPT_REQUEST_TIMEOUT="$1"
        ;;
      --max-attempts)
        shift
        [[ "${1:-}" != "" ]] || fail "--max-attempts requires a value"
        OPT_MAX_ATTEMPTS="$1"
        ;;
      --backoff-ms)
        shift
        [[ "${1:-}" != "" ]] || fail "--backoff-ms requires a value"
        OPT_BACKOFF_MS="$1"
        ;;
      --backoff-factor)
        shift
        [[ "${1:-}" != "" ]] || fail "--backoff-factor requires a value"
        OPT_BACKOFF_FACTOR="$1"
        ;;
      --retryable-status-codes)
        shift
        [[ "${1:-}" != "" ]] || fail "--retryable-status-codes requires a value"
        OPT_RETRYABLE_STATUS_CODES="$1"
        ;;
      --x-api-key)
        shift
        [[ "${1:-}" != "" ]] || fail "--x-api-key requires a value"
        OPT_X_API_KEY="$1"
        ;;
      --access-token)
        shift
        [[ "${1:-}" != "" ]] || fail "--access-token requires a value"
        OPT_ACCESS_TOKEN="$1"
        ;;
      --summary-export)
        shift
        [[ "${1:-}" != "" ]] || fail "--summary-export requires a path"
        OPT_SUMMARY_EXPORT="$1"
        ;;
      --dry-run)
        DRY_RUN=1
        ;;
      --verbose)
        VERBOSE=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        if (( "$#" > 0 )); then
          K6_EXTRA_ARGS+=("$@")
        fi
        break
        ;;
      *)
        fail "Unknown option: $1 (use --help)"
        ;;
    esac
    shift
  done
}

apply_overrides() {
  if [[ -n "$OPT_MODE" ]]; then
    validate_mode "$OPT_MODE"
  fi

  # Convenient fallback: reuse E2E_BASE_URL if BASE_URL is not defined.
  if [[ -z "${BASE_URL:-}" && -n "${E2E_BASE_URL:-}" ]]; then
    export BASE_URL="$E2E_BASE_URL"
  fi

  export_if_set "LOAD_MODE" "$OPT_MODE"
  export_if_set "TARGET_VUS" "$OPT_TARGET_VUS"
  export_if_set "BASE_URL" "$OPT_BASE_URL"
  export_if_set "WARMUP_DURATION" "$OPT_WARMUP"
  export_if_set "HOLD_DURATION" "$OPT_HOLD"
  export_if_set "RAMP_DOWN_DURATION" "$OPT_RAMP_DOWN"
  export_if_set "MIX_A" "$OPT_MIX_A"
  export_if_set "MIX_B" "$OPT_MIX_B"
  export_if_set "MIX_C" "$OPT_MIX_C"
  export_if_set "ENFORCE_P95" "$OPT_ENFORCE_P95"
  export_if_set "P95_TARGET_MS" "$OPT_P95_TARGET_MS"
  export_if_set "ERROR_RATE_THRESHOLD" "$OPT_ERROR_RATE_THRESHOLD"
  export_if_set "WRITE_AUTH_MODE" "$OPT_WRITE_AUTH_MODE"
  export_if_set "WRITE_RANDOM_IP" "$OPT_WRITE_RANDOM_IP"
  export_if_set "USER_POOL_SIZE" "$OPT_USER_POOL_SIZE"
  export_if_set "REQUEST_TIMEOUT" "$OPT_REQUEST_TIMEOUT"
  export_if_set "MAX_ATTEMPTS" "$OPT_MAX_ATTEMPTS"
  export_if_set "BACKOFF_MS" "$OPT_BACKOFF_MS"
  export_if_set "BACKOFF_FACTOR" "$OPT_BACKOFF_FACTOR"
  export_if_set "RETRYABLE_STATUS_CODES" "$OPT_RETRYABLE_STATUS_CODES"
  export_if_set "X_API_KEY" "$OPT_X_API_KEY"
  export_if_set "ACCESS_TOKEN" "$OPT_ACCESS_TOKEN"
}

print_effective_config() {
  local effective_base_url effective_mode effective_vus
  effective_base_url="${BASE_URL:-http://localhost:8000/api/v1}"
  effective_mode="${LOAD_MODE:-100}"
  effective_vus="${TARGET_VUS:-auto}"

  log "Load script: $LOAD_SCRIPT"
  log "Base URL: $effective_base_url"
  log "Mode: $effective_mode, TARGET_VUS: $effective_vus"
  log "Durations: warmup=${WARMUP_DURATION:-30s}, hold=${HOLD_DURATION:-2m}, rampDown=${RAMP_DOWN_DURATION:-30s}"
  log "Mix A/B/C: ${MIX_A:-70}/${MIX_B:-25}/${MIX_C:-5}"

  if [[ -n "${X_API_KEY:-}" ]]; then
    log "Auth X_API_KEY: $(mask_secret "$X_API_KEY")"
  fi
  if [[ -n "${ACCESS_TOKEN:-}" ]]; then
    log "Auth ACCESS_TOKEN: $(mask_secret "$ACCESS_TOKEN")"
  fi
}

run_k6() {
  [[ -f "$LOAD_SCRIPT" ]] || fail "Load script not found: $LOAD_SCRIPT"

  local -a cmd
  cmd=("$K6_BIN" run "$LOAD_SCRIPT")
  if [[ -n "$OPT_SUMMARY_EXPORT" ]]; then
    cmd+=(--summary-export "$OPT_SUMMARY_EXPORT")
  fi
  if (( ${#K6_EXTRA_ARGS[@]} > 0 )); then
    cmd+=("${K6_EXTRA_ARGS[@]}")
  fi

  debug "Command: ${cmd[*]}"
  if [[ "$DRY_RUN" == "1" ]]; then
    log "k6 command: ${cmd[*]}"
    log "Dry-run enabled; k6 command not executed."
    return 0
  fi

  require_cmd "$K6_BIN"
  "${cmd[@]}"
}

main() {
  parse_args "$@"
  load_env_file "$ENV_FILE"
  apply_overrides
  print_effective_config
  run_k6
}

main "$@"
