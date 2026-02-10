#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REALM_TEMPLATE="${SCRIPT_DIR}/realm-template.json"
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}"
  exit 1
fi

if [[ ! -f "${REALM_TEMPLATE}" ]]; then
  echo "Missing ${REALM_TEMPLATE}"
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

if [[ -z "${KEYCLOAK_REALM:-}" || -z "${KEYCLOAK_ADMIN:-}" || -z "${KEYCLOAK_ADMIN_PASSWORD:-}" ]]; then
  echo "Missing KEYCLOAK_REALM / KEYCLOAK_ADMIN / KEYCLOAK_ADMIN_PASSWORD in .env"
  exit 1
fi

extract_bool_from_template() {
  local key="$1"
  sed -nE "s/^[[:space:]]*\"${key}\"[[:space:]]*:[[:space:]]*(true|false).*/\1/p" "${REALM_TEMPLATE}" | head -n 1
}

REGISTRATION_ALLOWED="$(extract_bool_from_template "registrationAllowed")"
REGISTRATION_EMAIL_AS_USERNAME="$(extract_bool_from_template "registrationEmailAsUsername")"

if [[ -z "${REGISTRATION_ALLOWED}" || -z "${REGISTRATION_EMAIL_AS_USERNAME}" ]]; then
  echo "Could not read registration flags from ${REALM_TEMPLATE}"
  exit 1
fi

KEYCLOAK_CONTAINER_NAME="${KEYCLOAK_CONTAINER_NAME:-keycloakgame}"
if ! docker ps --format '{{.Names}}' | grep -qx "${KEYCLOAK_CONTAINER_NAME}"; then
  if docker ps --format '{{.Names}}' | grep -qx "keycloakGame"; then
    KEYCLOAK_CONTAINER_NAME="keycloakGame"
  else
    echo "No running Keycloak container found (expected keycloakgame or keycloakGame)"
    exit 1
  fi
fi

docker exec "${KEYCLOAK_CONTAINER_NAME}" /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user "${KEYCLOAK_ADMIN}" \
  --password "${KEYCLOAK_ADMIN_PASSWORD}" >/dev/null

docker exec "${KEYCLOAK_CONTAINER_NAME}" /opt/keycloak/bin/kcadm.sh update "realms/${KEYCLOAK_REALM}" \
  -s "registrationAllowed=${REGISTRATION_ALLOWED}" \
  -s "registrationEmailAsUsername=${REGISTRATION_EMAIL_AS_USERNAME}" >/dev/null

echo "Updated realm ${KEYCLOAK_REALM} in ${KEYCLOAK_CONTAINER_NAME}:"
docker exec "${KEYCLOAK_CONTAINER_NAME}" /opt/keycloak/bin/kcadm.sh get "realms/${KEYCLOAK_REALM}" \
  | sed -nE 's/.*"registrationAllowed"[[:space:]]*:[[:space:]]*(true|false).*/registrationAllowed=\1/p; s/.*"registrationEmailAsUsername"[[:space:]]*:[[:space:]]*(true|false).*/registrationEmailAsUsername=\1/p'
