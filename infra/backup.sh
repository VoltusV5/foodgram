#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/foodgram
umask 077
exec 9>.deploy.lock
flock -n 9 || exit 0
compose() { docker compose -p foodgram --env-file .env --env-file .release.env -f docker-compose.production.yml "$@"; }
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p backups
compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "backups/$stamp.dump"
compose run --rm --no-deps -T backend tar -czf - -C /foodgram/media . > "backups/$stamp-media.tar.gz"
cp .release.env "backups/$stamp-release.env"
# Backups are kept locally; copy them off-host for protection against disk loss.
find /opt/foodgram/backups -maxdepth 1 -type f -mtime +14 \( -name '*.dump' -o -name '*-media.tar.gz' -o -name '*-release.env' \) -delete
