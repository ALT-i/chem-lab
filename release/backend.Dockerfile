# Release image of the backend for NOUN.
# The application is shipped as compiled bytecode only: no .py sources, no .env.
# Built by release/build-release.sh from a clean `git archive` of the release branch.

# --- Stage 1: compile the application to bytecode -------------------------------
FROM python:3.9-bookworm AS compile

WORKDIR /build
COPY ./src ./src
# -b writes each .pyc next to its module, so Python can import it with the .py removed
RUN python -m compileall -b -q src && \
	find src -name "*.py" -delete && \
	find src -name "__pycache__" -type d -prune -exec rm -rf {} +

# --- Stage 2: the runtime image (only compiled files are copied in) -------------
FROM python:3.9-bookworm

WORKDIR /app
EXPOSE 8000
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
	apt-get install -y --no-install-recommends libpq-dev postgresql-client netcat-openbsd && \
	rm -rf /var/lib/apt/lists/*

COPY ./docker/ /

COPY ./requirements/ ./requirements
RUN pip install --no-cache-dir -r ./requirements/prod.txt

COPY --from=compile /build/src ./src
COPY ./manage.py ./manage.py

# Settings come from the server's .env via docker compose; an empty file here
# stops django-dotenv warning about a missing .env on every command.
ENV PYTHONDONTWRITEBYTECODE 1
RUN touch /app/.env

CMD ["sh", "/entrypoint-web.sh"]
