#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

readonly commit_sha="${1:-${GIT_COMMIT_SHA:-}}"
readonly delivery="${2:-${WEBHOOK_DELIVERY:-manual}}"
readonly compose_file="${COMPOSE_FILE:-/opt/liberty/deploy/liberty01server/compose.yaml}"
readonly compose_env_file="${COMPOSE_ENV_FILE:-/etc/liberty/compose.env}"
readonly app_image_repository="${APP_IMAGE_REPOSITORY:?Set APP_IMAGE_REPOSITORY}"
readonly deployment_state_directory="${DEPLOYMENT_STATE_DIRECTORY:-/var/lib/liberty-deploy}"
readonly health_timeout_seconds="${HEALTH_TIMEOUT_SECONDS:-180}"

log() {
  printf '%s %s\n' "$(date --utc +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

die() {
  log "ERROR: $*" >&2
  exit 1
}

[[ "$commit_sha" =~ ^[0-9a-f]{40}([0-9a-f]{24})?$ ]] || die "Commit SHA is malformed"
[[ "$delivery" =~ ^[A-Za-z0-9._:-]{1,128}$ ]] || die "Delivery identifier is malformed"
[[ -r "$compose_file" ]] || die "Compose file is not readable: $compose_file"
[[ -r "$compose_env_file" ]] || die "Compose environment file is not readable: $compose_env_file"
[[ "$health_timeout_seconds" =~ ^[0-9]+$ ]] || die "HEALTH_TIMEOUT_SECONDS must be an integer"

mkdir -p "$deployment_state_directory"
exec 9>"$deployment_state_directory/deployment.lock"
flock -n 9 || die "Another deployment is already running"

export APP_IMAGE="${app_image_repository}:sha-${commit_sha}"
readonly -a compose=(docker compose --env-file "$compose_env_file" -f "$compose_file")

wait_for_health() {
  local service="$1" container_id deadline status
  container_id="$("${compose[@]}" ps -q "$service")"
  [[ -n "$container_id" ]] || die "$service did not create a container"
  deadline=$((SECONDS + health_timeout_seconds))

  while (( SECONDS < deadline )); do
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id")"
    case "$status" in
      healthy|running)
        log "$service is $status"
        return 0
        ;;
      unhealthy|exited|dead)
        docker logs --tail 100 "$container_id" >&2 || true
        die "$service entered state $status"
        ;;
    esac
    sleep 3
  done

  docker logs --tail 100 "$container_id" >&2 || true
  die "$service did not become healthy before the timeout"
}

log "Validating deployment configuration for $APP_IMAGE"
"${compose[@]}" config --quiet

log "Pulling immutable application image"
"${compose[@]}" pull web_a web_b celery_worker celery_beat

log "Applying backward-compatible database migrations"
"${compose[@]}" run --rm --no-deps web_a python manage.py migrate --noinput

log "Updating web replicas one at a time"
"${compose[@]}" up -d --no-deps web_a
wait_for_health web_a
"${compose[@]}" up -d --no-deps web_b
wait_for_health web_b

log "Updating background workers; celery_beat remains a singleton"
"${compose[@]}" up -d --no-deps celery_worker celery_beat
wait_for_health celery_worker

state_tmp="$(mktemp "$deployment_state_directory/last-successful.tmp.XXXXXX")"
printf 'APP_IMAGE=%s\nCOMMIT_SHA=%s\nDELIVERY=%s\nDEPLOYED_AT=%s\n' \
  "$APP_IMAGE" "$commit_sha" "$delivery" "$(date --utc +'%Y-%m-%dT%H:%M:%SZ')" >"$state_tmp"
mv -f "$state_tmp" "$deployment_state_directory/last-successful.env"

log "Deployment completed successfully"

