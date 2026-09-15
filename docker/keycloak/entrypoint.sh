#!/bin/bash
# The selected Keycloak DHI explicitly includes bash; the Python runtime does not.
set -euo pipefail
KC_DB_PASSWORD=$(</run/secrets/keycloak_database_password)
KC_BOOTSTRAP_ADMIN_PASSWORD=$(</run/secrets/keycloak_bootstrap_password)
[[ -n "$KC_DB_PASSWORD" && -n "$KC_BOOTSTRAP_ADMIN_PASSWORD" ]] || { echo 'Required Keycloak secret file is empty.' >&2; exit 1; }
export KC_DB_PASSWORD KC_BOOTSTRAP_ADMIN_PASSWORD
exec /opt/keycloak/bin/kc.sh "$@"
