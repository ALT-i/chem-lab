#!/bin/sh
# Builds the NOUN release bundle: backend and admin dashboard images (no source code),
# docker-compose.yml, settings template, backup script and checksums.
#
# Usage (from the backend repo root, Git Bash or Linux):
#   release/build-release.sh 1.0.0
#
# Optional settings:
#   BACKEND_REF=origin/master          branch or tag of this repo to build (run git fetch first)
#   ADMIN_REPO=../chem_lab_admin_fe    path to the admin dashboard repo
#   ADMIN_REF=origin/prod              branch or tag of the dashboard to build (git fetch there too)
#   MEDIA_DIR=/path/to/media           folder of media files to ship as media.tar.gz
#   DATA_SQL=/path/to/export.sql       database export to ship as chemlab-data.sql
set -e

VERSION=${1:?Usage: release/build-release.sh <version>, e.g. 1.0.0}
BACKEND_REF=${BACKEND_REF:-origin/master}
ADMIN_REPO=${ADMIN_REPO:-../chem_lab_admin_fe}
ADMIN_REF=${ADMIN_REF:-origin/prod}
OUT="release-dist/chemlab-release-$VERSION"
WORK="release-dist/.build-$VERSION"

echo "==> Exporting clean sources: backend $BACKEND_REF, dashboard $ADMIN_REF"
rm -rf "$WORK" "$OUT"
mkdir -p "$WORK/backend" "$WORK/admin" "$OUT"
git archive "$BACKEND_REF" | tar -x -C "$WORK/backend"
git -C "$ADMIN_REPO" archive "$ADMIN_REF" | tar -x -C "$WORK/admin"

echo "==> Building chemlab-backend:$VERSION"
docker build -f release/backend.Dockerfile -t "chemlab-backend:$VERSION" "$WORK/backend"

echo "==> Building chemlab-admin:$VERSION"
docker build -f release/admin.Dockerfile -t "chemlab-admin:$VERSION" "$WORK/admin"

echo "==> Checking the backend image holds no source code or settings"
PY_COUNT=$(docker run --rm --entrypoint sh "chemlab-backend:$VERSION" -c 'find /app -name "*.py" ! -name manage.py | wc -l')
ENV_SIZE=$(docker run --rm --entrypoint sh "chemlab-backend:$VERSION" -c 'wc -c < /app/.env')
if [ "$PY_COUNT" -ne 0 ] || [ "$ENV_SIZE" -ne 0 ]; then
    echo "STOP: image contains $PY_COUNT .py files and a $ENV_SIZE-byte .env" >&2
    exit 1
fi

echo "==> Saving images (this takes a few minutes)"
docker save "chemlab-backend:$VERSION" "chemlab-admin:$VERSION" | gzip > "$OUT/chemlab-images-$VERSION.tar.gz"

cp release/docker-compose.yml "$OUT/docker-compose.yml"
sed "s/__VERSION__/$VERSION/" release/env.template > "$OUT/env.template"
cp release/backup.sh "$OUT/backup.sh"
if [ -n "$MEDIA_DIR" ]; then
    tar -czf "$OUT/media.tar.gz" -C "$MEDIA_DIR" .
fi
if [ -n "$DATA_SQL" ]; then
    cp "$DATA_SQL" "$OUT/chemlab-data.sql"
fi

(cd "$OUT" && sha256sum -- * > SHA256SUMS)
rm -rf "$WORK"

echo "==> Done: $OUT"
ls -lh "$OUT"
