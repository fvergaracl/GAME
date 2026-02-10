#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env}"
RUN_REAL="${RUN_REAL_E2E:-0}"
AUTO_TOKEN=1
VERBOSE=0

PYTEST_ARGS=()

usage() {
  cat <<'EOF'
Run GAME E2E tests in one command.

Usage:
  ./scripts/run_e2e.sh [options] [-- <extra pytest args>]

Options:
  --env-file <path>   Env file to source (default: .env)
  --real              Include real HTTP/PostgreSQL E2E tests
  --controlled-only   Run only controlled E2E tests (default)
  --no-token          Skip automatic ACCESS_TOKEN fetch
  --verbose           Print extra debug output
  -h, --help          Show this help

Examples:
  ./scripts/run_e2e.sh
  ./scripts/run_e2e.sh --real
  ./scripts/run_e2e.sh --env-file .env.integrated --real -- -k apikey_create
EOF
}

log() {
  printf '[E2E] %s\n' "$*"
}

debug() {
  if [[ "$VERBOSE" == "1" ]]; then
    printf '[E2E][debug] %s\n' "$*"
  fi
}

warn() {
  printf '[E2E][warn] %s\n' "$*" >&2
}

fail() {
  printf '[E2E][error] %s\n' "$*" >&2
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

first_non_empty() {
  local value=""
  for value in "$@"; do
    if [[ -n "${value:-}" ]]; then
      printf '%s' "$value"
      return
    fi
  done
  printf ''
}

ensure_access_token() {
  if [[ "$AUTO_TOKEN" != "1" ]]; then
    log "Skipping token resolution (--no-token)."
    return
  fi

  if [[ -n "${ACCESS_TOKEN:-}" ]]; then
    log "ACCESS_TOKEN already present in environment."
    export ADMIN_BEARER_TOKEN="${ADMIN_BEARER_TOKEN:-$ACCESS_TOKEN}"
    return
  fi

  require_cmd curl
  require_cmd jq

  local keycloak_url realm client_id client_secret username password token_url
  keycloak_url="$(first_non_empty "${E2E_KEYCLOAK_URL:-}" "${KEYCLOAK_URL:-}")"
  realm="$(first_non_empty "${E2E_KEYCLOAK_REALM:-}" "${KEYCLOAK_REALM:-}")"
  client_id="$(first_non_empty "${E2E_KEYCLOAK_CLIENT_ID:-}" "${KEYCLOAK_CLIENT_ID:-}")"
  client_secret="$(first_non_empty "${E2E_KEYCLOAK_CLIENT_SECRET:-}" "${KEYCLOAK_CLIENT_SECRET:-}")"
  username="$(first_non_empty "${E2E_KEYCLOAK_ADMIN_USERNAME:-}" "${KEYCLOAK_USER_WITH_ROLE_USERNAME:-}" "${KEYCLOAK_ADMIN_USERNAME:-}" "${ADMIN_USERNAME:-}")"
  password="$(first_non_empty "${E2E_KEYCLOAK_ADMIN_PASSWORD:-}" "${KEYCLOAK_USER_WITH_ROLE_PASSWORD:-}" "${KEYCLOAK_ADMIN_PASSWORD:-}" "${ADMIN_PASSWORD:-}")"
  token_url="${KEYCLOAK_TOKEN_URL:-}"

  if [[ -z "$token_url" ]]; then
    [[ -n "$keycloak_url" ]] || fail "KEYCLOAK_URL/E2E_KEYCLOAK_URL is required for token resolution."
    [[ -n "$realm" ]] || fail "KEYCLOAK_REALM/E2E_KEYCLOAK_REALM is required for token resolution."
    token_url="${keycloak_url%/}/realms/${realm}/protocol/openid-connect/token"
  fi

  [[ -n "$client_id" ]] || fail "KEYCLOAK_CLIENT_ID/E2E_KEYCLOAK_CLIENT_ID is required for token resolution."
  [[ -n "$username" ]] || fail "Admin username is missing (E2E_KEYCLOAK_ADMIN_USERNAME / KEYCLOAK_USER_WITH_ROLE_USERNAME / KEYCLOAK_ADMIN_USERNAME / ADMIN_USERNAME)."
  [[ -n "$password" ]] || fail "Admin password is missing (E2E_KEYCLOAK_ADMIN_PASSWORD / KEYCLOAK_USER_WITH_ROLE_PASSWORD / KEYCLOAK_ADMIN_PASSWORD / ADMIN_PASSWORD)."

  log "Requesting Keycloak token for user '$username'..."
  debug "Using token endpoint: $token_url"
  ACCESS_TOKEN="$(
    curl -sS -X POST "$token_url" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "client_id=$client_id" \
      -d "client_secret=$client_secret" \
      -d "grant_type=password" \
      -d "username=$username" \
      -d "password=$password" | jq -er '.access_token'
  )" || fail "Unable to fetch ACCESS_TOKEN from Keycloak."

  export ACCESS_TOKEN
  export ADMIN_BEARER_TOKEN="$ACCESS_TOKEN"
  log "ACCESS_TOKEN resolved: $(mask_secret "$ACCESS_TOKEN")"
}

run_pytest() {
  require_cmd poetry

  local marker_expr
  local -a cmd

  if [[ "$RUN_REAL" == "1" ]]; then
    export RUN_REAL_E2E=1
    marker_expr=""
    log "Running controlled + real-infrastructure E2E tests."
  else
    export RUN_REAL_E2E=0
    marker_expr="not e2e_real_http"
    log "Running controlled E2E tests only."
  fi

  cmd=(poetry run pytest tests/e2e -q)
  if [[ -n "$marker_expr" ]]; then
    cmd+=(-m "$marker_expr")
  fi
  if (( ${#PYTEST_ARGS[@]} > 0 )); then
    cmd+=("${PYTEST_ARGS[@]}")
  fi

  debug "Executing: ${cmd[*]}"
  "${cmd[@]}"
}

parse_args() {
  while (( "$#" )); do
    case "$1" in
      --env-file)
        shift
        [[ "${1:-}" != "" ]] || fail "--env-file requires a path"
        ENV_FILE="$1"
        ;;
      --real)
        RUN_REAL=1
        ;;
      --controlled-only)
        RUN_REAL=0
        ;;
      --no-token)
        AUTO_TOKEN=0
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
          PYTEST_ARGS+=("$@")
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

main() {
  parse_args "$@"
  load_env_file "$ENV_FILE"

  if [[ "$RUN_REAL" == "1" ]]; then
    ensure_access_token
  fi

  run_pytest
}

main "$@"
