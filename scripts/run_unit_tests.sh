#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env}"
LOAD_ENV=1
VERBOSE=0
DRY_RUN=0
QUIET=1

COVERAGE=0
COV_TARGET="${COV_TARGET:-app}"
COV_REPORT="${COV_REPORT:-term-missing}"
COV_BRANCH=0

KEYWORD_EXPR=""
MARKER_EXPR=""
MAXFAIL=""

TARGETS=()
PYTEST_EXTRA_ARGS=()

usage() {
  cat <<'EOF'
Run GAME unit tests in a standardized way.

Usage:
  ./scripts/run_unit_tests.sh [options] [targets...] [-- <extra pytest args>]

Options:
  --env-file <path>       Env file to source (default: .env)
  --no-env                Skip loading env file
  --path <pytest-path>    Path to run (default: tests/unit_tests)
  --file <test-file>      Specific unit test file
  --k <expr>              Pytest -k expression
  --m <expr>              Pytest -m expression
  --maxfail <N>           Stop after N failures
  --fail-fast             Stop after first failure
  --verbose               Run pytest with -vv
  --no-quiet              Disable default -q
  --cov                   Enable coverage (default target: app)
  --cov-target <name>     Coverage target (default: app)
  --cov-report <type>     term-missing|term|html|xml|json|lcov
  --cov-branch            Enable branch coverage
  --dry-run               Print command without executing
  -h, --help              Show this help

Examples:
  ./scripts/run_unit_tests.sh
  ./scripts/run_unit_tests.sh --fail-fast
  ./scripts/run_unit_tests.sh --cov --cov-branch --cov-report html
  ./scripts/run_unit_tests.sh --file tests/unit_tests/services/test_user_points_service.py
  ./scripts/run_unit_tests.sh tests/unit_tests/repository/test_user_repository.py
  ./scripts/run_unit_tests.sh --k "abuse_prevention or points" -- --disable-warnings
EOF
}

log() {
  printf '[UNIT] %s\n' "$*"
}

debug() {
  if [[ "$VERBOSE" == "1" ]]; then
    printf '[UNIT][debug] %s\n' "$*"
  fi
}

warn() {
  printf '[UNIT][warn] %s\n' "$*" >&2
}

fail() {
  printf '[UNIT][error] %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing required command: $cmd"
}

load_env_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    warn "Env file not found ($path). Continuing without sourcing env."
    return
  fi
  log "Loading environment from $path"
  set -a
  # shellcheck source=/dev/null
  source "$path"
  set +a
}

parse_args() {
  while (( "$#" )); do
    case "$1" in
      --env-file)
        shift
        [[ "${1:-}" != "" ]] || fail "--env-file requires a path"
        ENV_FILE="$1"
        ;;
      --no-env)
        LOAD_ENV=0
        ;;
      --path)
        shift
        [[ "${1:-}" != "" ]] || fail "--path requires a value"
        TARGETS+=("$1")
        ;;
      --file)
        shift
        [[ "${1:-}" != "" ]] || fail "--file requires a value"
        TARGETS+=("$1")
        ;;
      --k)
        shift
        [[ "${1:-}" != "" ]] || fail "--k requires an expression"
        KEYWORD_EXPR="$1"
        ;;
      --m)
        shift
        [[ "${1:-}" != "" ]] || fail "--m requires an expression"
        MARKER_EXPR="$1"
        ;;
      --maxfail)
        shift
        [[ "${1:-}" != "" ]] || fail "--maxfail requires a value"
        MAXFAIL="$1"
        ;;
      --fail-fast)
        MAXFAIL="1"
        ;;
      --verbose)
        VERBOSE=1
        ;;
      --no-quiet)
        QUIET=0
        ;;
      --cov)
        COVERAGE=1
        ;;
      --cov-target)
        shift
        [[ "${1:-}" != "" ]] || fail "--cov-target requires a value"
        COV_TARGET="$1"
        ;;
      --cov-report)
        shift
        [[ "${1:-}" != "" ]] || fail "--cov-report requires a value"
        COV_REPORT="$1"
        COVERAGE=1
        ;;
      --cov-branch)
        COV_BRANCH=1
        COVERAGE=1
        ;;
      --dry-run)
        DRY_RUN=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      --)
        shift
        if (( "$#" > 0 )); then
          PYTEST_EXTRA_ARGS+=("$@")
        fi
        break
        ;;
      *)
        if [[ "$1" == -* ]]; then
          fail "Unknown option: $1 (use --help)"
        fi
        TARGETS+=("$1")
        ;;
    esac
    shift
  done
}

build_pytest_command() {
  local -n out_cmd_ref=$1
  local -a built_cmd

  built_cmd=(poetry run pytest)

  if [[ "${#TARGETS[@]}" -eq 0 ]]; then
    TARGETS=("tests/unit_tests")
  fi
  built_cmd+=("${TARGETS[@]}")

  if [[ "$QUIET" == "1" ]]; then
    built_cmd+=(-q)
  fi
  if [[ "$VERBOSE" == "1" ]]; then
    built_cmd+=(-vv)
  fi
  if [[ -n "$KEYWORD_EXPR" ]]; then
    built_cmd+=(-k "$KEYWORD_EXPR")
  fi
  if [[ -n "$MARKER_EXPR" ]]; then
    built_cmd+=(-m "$MARKER_EXPR")
  fi
  if [[ -n "$MAXFAIL" ]]; then
    built_cmd+=(--maxfail "$MAXFAIL")
  fi

  if [[ "$COVERAGE" == "1" ]]; then
    built_cmd+=(--cov="$COV_TARGET" --cov-report "$COV_REPORT")
    if [[ "$COV_BRANCH" == "1" ]]; then
      built_cmd+=(--cov-branch)
    fi
  fi

  if (( ${#PYTEST_EXTRA_ARGS[@]} > 0 )); then
    built_cmd+=("${PYTEST_EXTRA_ARGS[@]}")
  fi

  out_cmd_ref=("${built_cmd[@]}")
}

main() {
  parse_args "$@"

  if [[ "$LOAD_ENV" == "1" ]]; then
    load_env_file "$ENV_FILE"
  else
    log "Skipping env loading (--no-env)."
  fi

  export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"

  require_cmd poetry

  local -a cmd
  build_pytest_command cmd

  debug "Command: ${cmd[*]}"
  log "Running unit tests (targets: ${TARGETS[*]:-tests/unit_tests})"
  if [[ "$COVERAGE" == "1" ]]; then
    log "Coverage enabled: target=$COV_TARGET, report=$COV_REPORT, branch=$COV_BRANCH"
  fi

  if [[ "$DRY_RUN" == "1" ]]; then
    log "Dry-run command: ${cmd[*]}"
    log "Dry-run enabled; pytest not executed."
    return 0
  fi

  "${cmd[@]}"
}

main "$@"
