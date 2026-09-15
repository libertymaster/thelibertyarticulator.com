# Optional Keycloak service, not automatic SSO

The supplied image list includes `dhi.io/keycloak:26.7.3-debian13`. The bundle includes an **opt-in** `compose.keycloak.yaml` overlay using that image as an optimized build base, a dedicated PostgreSQL service, isolated identity data/edge networks, and separate secret files.

No realm, OIDC client, user migration, Wagtail authentication backend, Grafana federation, or Cloudflare Access identity-provider setting is created. Existing editor Access JWT gating and Wagtail login remain unchanged. Do not advertise single sign-on until that independent integration is configured and tested.

## Before enabling

Choose an owned hostname and set `KEYCLOAK_HOST` in .env. Do not use an invented hostname from an example as if DNS is already configured. Set up restricted administrator access and a recovery plan before routing the hostname. Avoid an Access/IdP dependency loop in which the only way to reach Keycloak requires logging into that same unavailable Keycloak instance.

The selected image's Bash and kc.sh capabilities are checked by `ops/check_image_contracts.py`. The image is optimized for PostgreSQL, health and metrics, with local cache for a single instance. Runtime credentials are read from mounted secret files by its Bash entrypoint. They are process environment values inside the Keycloak container, not plaintext Compose values; the Docker host remains trusted.

## Startup after base-stack qualification

```sh
# After setting KEYCLOAK_HOST locally:
python3 ops/render_config.py
export MODE=prod
export COMPOSE_EXTRA_FILES=compose.keycloak.yaml
./ops/dc --profile identity config --quiet
./ops/dc --profile identity build keycloak
./ops/dc --profile identity run --rm --no-deps identity-volume-init
./ops/dc --profile identity up -d --wait keycloak-postgres keycloak
./ops/dc --profile identity up -d traefik
```

The renderer adds a precise-host route only when KEYCLOAK_HOST is set. Dashboard-managed Cloudflare Tunnel should direct that hostname to `http://traefik:8080`. The service listens on its private network; no host port is published. Readiness is checked on Keycloak's private management port 9000. Test HTTPS issuer URLs and forwarded-header behavior through the real tunnel.

Initial admin username is `bootstrap-admin`; its password is in `secrets/keycloak_bootstrap_password`. Retrieve it through a secure local administrative channel. Create durable named administrators, require MFA, test break-glass recovery, then remove the bootstrap administrator and remove bootstrap settings/secrets from the deployment according to Keycloak's operating guidance. Merely changing the bootstrap file does not rotate an existing user.

## Separate identity backup

The base publication backup does **not** include this extra database or custom Keycloak providers/themes. Define identity RPO/RTO and consistent backup rules before relying on it. A reviewed example for the included database is:

```sh
# Use a real age PUBLIC recipient stored in your backup policy; do not place a private key here.
# Run with a protected shell, pipefail, restrictive umask and a verified destination.
set -o pipefail
umask 077
MODE=prod COMPOSE_EXTRA_FILES=compose.keycloak.yaml ./ops/dc exec -T --user 70:70 keycloak-postgres \
  pg_dump -U postgres -d keycloak -Fc --no-owner --no-acl | \
  age -r "$AGE_PUBLIC_RECIPIENT" -o keycloak-backup.dump.age
```

Also back up reviewed configuration, image digests, extensions, themes and required secrets under encryption. Rehearse restore into a separately named identity database and verify users, realm/client configuration, login/logout and token validation. Never point a restored test realm at production consumers by accident.

References: [Keycloak container guide](https://www.keycloak.org/server/containers), [Keycloak configuration](https://www.keycloak.org/server/configuration). No Keycloak container was started in the authoring environment.
