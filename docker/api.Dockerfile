# Image for the API, the worker and the one-shot migrate job (same code, different command).
# Base image pinned to an exact tag (D67). Runs as a non-root user (threat T26).
FROM python:3.12.15-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

RUN groupadd --system --gid 10001 pramaan \
 && useradd --system --uid 10001 --gid pramaan --home-dir /srv --shell /usr/sbin/nologin pramaan

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

ARG BUILD_COMMIT=unknown
ENV PRAMAAN_BUILD_COMMIT=${BUILD_COMMIT}

USER pramaan
EXPOSE 8000

# Default command runs the API; docker-compose.yml overrides it for the worker and migrate.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
