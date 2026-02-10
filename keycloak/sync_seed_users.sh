#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}"
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

required_vars=(
  KEYCLOAK_REALM
  KEYCLOAK_ADMIN
  KEYCLOAK_ADMIN_PASSWORD
  KEYCLOAK_CLIENT_ID
  KEYCLOAK_USER_WITH_ROLE_PASSWORD
  KEYCLOAK_USER_NO_ROLE_PASSWORD
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing ${var_name} in .env"
    exit 1
  fi
done

KEYCLOAK_CONTAINER_NAME="${KEYCLOAK_CONTAINER_NAME:-keycloakgame}"
if ! docker ps --format '{{.Names}}' | grep -qx "${KEYCLOAK_CONTAINER_NAME}"; then
  if docker ps --format '{{.Names}}' | grep -qx "keycloakGame"; then
    KEYCLOAK_CONTAINER_NAME="keycloakGame"
  else
    echo "No running Keycloak container found (expected keycloakgame or keycloakGame)"
    exit 1
  fi
fi

kcadm() {
  docker exec "${KEYCLOAK_CONTAINER_NAME}" /opt/keycloak/bin/kcadm.sh "$@"
}

kcadm config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user "${KEYCLOAK_ADMIN}" \
  --password "${KEYCLOAK_ADMIN_PASSWORD}" >/dev/null

get_client_id() {
  local client_id="$1"
  kcadm get clients -r "${KEYCLOAK_REALM}" -q "clientId=${client_id}" \
    | tr -d '\n' \
    | sed -nE 's/.*"id"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p'
}

ensure_admin_role_exists() {
  CLIENT_UUID="$(get_client_id "${KEYCLOAK_CLIENT_ID}")"
  if [[ -z "${CLIENT_UUID}" ]]; then
    echo "Client ${KEYCLOAK_CLIENT_ID} not found in realm ${KEYCLOAK_REALM}"
    exit 1
  fi

  if ! kcadm get "clients/${CLIENT_UUID}/roles/AdministratorGAME" -r "${KEYCLOAK_REALM}" >/dev/null 2>&1; then
    kcadm create "clients/${CLIENT_UUID}/roles" -r "${KEYCLOAK_REALM}" \
      -s name=AdministratorGAME \
      -s 'description=Can create resources in GAME API' >/dev/null
    echo "Created missing client role: AdministratorGAME"
  fi
}

get_user_id_by_username() {
  local username="$1"
  kcadm get users -r "${KEYCLOAK_REALM}" -q "username=${username}" \
    | tr -d '\n' \
    | sed -nE 's/.*"id"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p'
}

get_user_id_by_email() {
  local email="$1"
  kcadm get users -r "${KEYCLOAK_REALM}" -q "email=${email}" \
    | tr -d '\n' \
    | sed -nE 's/.*"id"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p'
}

upsert_user() {
  local username="$1"
  local email="$2"
  local password="$3"
  local user_id

  user_id="$(get_user_id_by_username "${username}")"
  if [[ -z "${user_id}" ]]; then
    user_id="$(get_user_id_by_email "${email}")"
  fi
  if [[ -z "${user_id}" ]]; then
    user_id="$(kcadm create users -r "${KEYCLOAK_REALM}" \
      -s "username=${username}" \
      -s "email=${email}" \
      -s "enabled=true" \
      -s "emailVerified=true" \
      -i | tr -d '\r\n')"
    echo "Created user: ${username}" >&2
  else
    echo "User exists, updating: ${username}" >&2
  fi

  kcadm update "users/${user_id}" -r "${KEYCLOAK_REALM}" \
    -s "email=${email}" \
    -s "enabled=true" \
    -s "emailVerified=true" >/dev/null

  kcadm set-password -r "${KEYCLOAK_REALM}" \
    --userid "${user_id}" \
    --new-password "${password}" >/dev/null

  echo "${user_id}"
}

ADMIN_USERNAME="game_admin@example.com"
USER_USERNAME="game_user@example.com"
ADMIN_EMAIL="game_admin@example.com"
USER_EMAIL="game_user@example.com"

ADMIN_USER_ID="$(upsert_user "${ADMIN_USERNAME}" "${ADMIN_EMAIL}" "${KEYCLOAK_USER_WITH_ROLE_PASSWORD}")"
upsert_user "${USER_USERNAME}" "${USER_EMAIL}" "${KEYCLOAK_USER_NO_ROLE_PASSWORD}" >/dev/null

# Ensure admin user has AdministratorGAME role in the configured client.
ensure_admin_role_exists

kcadm add-roles -r "${KEYCLOAK_REALM}" \
  --uid "${ADMIN_USER_ID}" \
  --cclientid "${KEYCLOAK_CLIENT_ID}" \
  --rolename "AdministratorGAME" >/dev/null || true

echo "Seed users synchronized in realm ${KEYCLOAK_REALM}:"
kcadm get users -r "${KEYCLOAK_REALM}" -q username="${ADMIN_USERNAME}" --fields username,email,enabled,emailVerified
kcadm get users -r "${KEYCLOAK_REALM}" -q username="${USER_USERNAME}" --fields username,email,enabled,emailVerified
echo "Admin role mappings in client ${KEYCLOAK_CLIENT_ID}:"
kcadm get "users/${ADMIN_USER_ID}/role-mappings/clients/${CLIENT_UUID}" -r "${KEYCLOAK_REALM}" --fields name
