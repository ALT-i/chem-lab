# syntax=docker/dockerfile:1
# Release image of the admin dashboard for NOUN.
# The dashboard is built once with placeholder values; the container fills them in
# from the server's .env every time it starts, so NOUN never needs to rebuild it.
# Built by release/build-release.sh from a clean `git archive` of chem_lab_admin_fe.

# --- Stage 1: build the static site with placeholders ---------------------------
FROM node:20 AS build

WORKDIR /app
COPY . .

COPY <<'EOF' .env.production
VITE_PROD_BASE_URL=__CHEMLAB_API_URL__
VITE_SECRET_KEY=__CHEMLAB_COOKIE_KEY__
VITE_COUDINARY_BASE_URL=https://api.cloudinary.com/v1_1
VITE_COUDINARY_PROD_ENV=__CHEMLAB_CLOUDINARY_CLOUD__
VITE_COUDINARY_IMAGE_UPLOAD=/image/upload
VITE_COUDINARY_VIDEO_UPLOAD=/video/upload
VITE_SUBSTANCE_IMAGES=__CHEMLAB_PRESET_SUBSTANCES__
VITE_APPARATUS_IMAGES=__CHEMLAB_PRESET_APPARATUS__
VITE_PROFILE_IMAGES=__CHEMLAB_PRESET_PROFILES__
VITE_LESSON_IMAGES=__CHEMLAB_PRESET_LESSON_IMAGES__
VITE_LESSON_VIDEOS=__CHEMLAB_PRESET_LESSON_VIDEOS__
EOF

# Picture and video links that point at the old Render backend follow the new server
RUN grep -rl "https://chem-lab-backend.onrender.com" src | xargs -r sed -i 's#https://chem-lab-backend.onrender.com#__CHEMLAB_API_ORIGIN__#g' && \
	npm install --no-audit --no-fund && \
	npm run build

# --- Stage 2: serve the built files with nginx ----------------------------------
FROM nginx:stable-alpine

# Pristine copy with placeholders; the start-up script copies it into the web root
COPY --from=build /app/dist /usr/share/nginx/template

COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Every page address loads index.html, so browser refreshes work
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

COPY --chmod=755 <<'EOF' /docker-entrypoint.d/40-chemlab-settings.sh
#!/bin/sh
# Writes this server's settings from .env into the dashboard files.
set -e

if [ -z "$SITE_URL" ]; then
    echo "chemlab: SITE_URL is not set in .env; the dashboard cannot find the backend" >&2
    exit 1
fi
if [ -z "$CLOUDINARY_CLOUD_NAME" ]; then
    echo "chemlab: CLOUDINARY_CLOUD_NAME is not set in .env; uploads will fail" >&2
fi

API_ORIGIN=${SITE_URL%/}
COOKIE_KEY=${ADMIN_COOKIE_KEY:-$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')}

rm -rf /usr/share/nginx/html/*
cp -r /usr/share/nginx/template/. /usr/share/nginx/html/

grep -rl "__CHEMLAB_" /usr/share/nginx/html | while read -r f; do
    sed -i \
        -e "s|__CHEMLAB_API_URL__|$API_ORIGIN/api/v1/|g" \
        -e "s|__CHEMLAB_API_ORIGIN__|$API_ORIGIN|g" \
        -e "s|__CHEMLAB_COOKIE_KEY__|$COOKIE_KEY|g" \
        -e "s|__CHEMLAB_CLOUDINARY_CLOUD__|$CLOUDINARY_CLOUD_NAME|g" \
        -e "s|__CHEMLAB_PRESET_SUBSTANCES__|${CLOUDINARY_PRESET_SUBSTANCES:-chemlab_substances}|g" \
        -e "s|__CHEMLAB_PRESET_APPARATUS__|${CLOUDINARY_PRESET_APPARATUS:-chemlab_apparatus}|g" \
        -e "s|__CHEMLAB_PRESET_PROFILES__|${CLOUDINARY_PRESET_PROFILES:-chemlab_profiles}|g" \
        -e "s|__CHEMLAB_PRESET_LESSON_IMAGES__|${CLOUDINARY_PRESET_LESSON_IMAGES:-chemlab_lesson_images}|g" \
        -e "s|__CHEMLAB_PRESET_LESSON_VIDEOS__|${CLOUDINARY_PRESET_LESSON_VIDEOS:-chemlab_lesson_videos}|g" \
        "$f"
done

echo "chemlab: dashboard configured for $API_ORIGIN"
EOF
