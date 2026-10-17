# pull official base image
# bookworm (Debian 12): bullseye's security pool no longer carries the package
# versions its index advertises, so apt-get fetches 404 mid-build.
FROM python:3.9-bookworm

ARG REQUIREMENTS_FILE

WORKDIR /app
EXPOSE 80
ENV PYTHONUNBUFFERED 1

# libpq-dev is required because requirements pin psycopg2 (source build), not
# psycopg2-binary. These come from Debian's own repo -- the PGDG repo that used
# to be added here was never needed, and the gnupg2/lsb-release/apt-key dance
# that set it up is what was failing (apt-key is also gone in Debian 12).
RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		wget \
		libpq-dev \
		postgresql-client \
		netcat-openbsd; \
	rm -rf /var/lib/apt/lists/*; \
	wget -O /wait-for https://raw.githubusercontent.com/eficode/wait-for/master/wait-for; \
	chmod +x /wait-for

COPY ./docker/ /

COPY ./requirements/ ./requirements
RUN pip install -r ./requirements/prod.txt

COPY . ./

# runserver is Django's development server: single-worker, auto-reloading and
# explicitly not for production. gunicorn is already a dependency and
# WhiteNoise is in MIDDLEWARE, so static files are still served correctly.
# Worker count is deliberately low by default (these workers each load
# numpy/scipy/chempy); raise it with WEB_CONCURRENCY if the instance has room.
CMD python manage.py collectstatic --no-input && \
    python manage.py migrate && \
    gunicorn src.wsgi:application \
        --bind "0.0.0.0:${PORT:-8000}" \
        --workers "${WEB_CONCURRENCY:-2}" \
        --timeout 120 \
        --limit-request-line 6094 \
        --access-logfile -

