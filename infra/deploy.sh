#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/foodgram
umask 077
exec 9>.deploy.lock
flock -n 9 || { echo 'Another Foodgram deployment/backup is running'; exit 1; }

export DOCKER_USERNAME="${1:?Image namespace required}"
export IMAGE_TAG="${2:?Image tag required}"
[[ "$DOCKER_USERNAME" =~ ^[a-z0-9][a-z0-9_-]*$ ]]
[[ "$IMAGE_TAG" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]]
compose() { docker compose -p foodgram --env-file .env -f docker-compose.production.yml "$@"; }
compose config --quiet
if [[ "${3:-}" != '--loaded' ]]; then
    compose pull
fi
compose up -d --wait --wait-timeout 120 db

# Before every migration, preserve the database and uploaded files.
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p backups
compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "backups/$stamp.dump"
if docker volume inspect foodgram_user_files >/dev/null 2>&1; then
    compose run --rm --no-deps -T backend tar -czf - -C /foodgram/media . > "backups/$stamp-media.tar.gz"
fi
if [[ -f .release.env ]]; then cp .release.env "backups/$stamp-release.env"; fi

compose run --rm -T backend python manage.py migrate --noinput
compose run --rm -T backend python manage.py collectstatic --noinput
# Re-run the one-shot frontend even when its image has not changed.
compose up --no-deps --force-recreate --abort-on-container-exit --exit-code-from frontend frontend
compose up -d --no-deps backend gateway
healthy=false
for attempt in $(seq 1 30); do
    if curl -fsS --max-time 5 -H 'Host: foodgram.srv-node.com' http://127.0.0.1:8080/api/recipes/ >/dev/null &&
       curl -fsS --max-time 5 -H 'Host: foodgram.srv-node.com' http://127.0.0.1:8080/ >/dev/null; then
        healthy=true
        break
    fi
    sleep 2
done
if [[ "$healthy" != true ]]; then
    echo 'Foodgram health check failed; backup preserved. Other projects were not changed.' >&2
    exit 1
fi
printf 'DOCKER_USERNAME=%s\nIMAGE_TAG=%s\n' "$DOCKER_USERNAME" "$IMAGE_TAG" > .release.env
echo "Foodgram deployed: $DOCKER_USERNAME / $IMAGE_TAG"
