#!/usr/bin/env bash
set -euo pipefail

mkdir -p /opt/keycloak/data/import
envsubst </opt/keycloak/realm-template.json >/opt/keycloak/data/import/realm.json

exec /opt/keycloak/bin/kc.sh start-dev --import-realm
