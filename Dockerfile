# syntax=docker/dockerfile:1.10
ARG PYTHON_BUILDER_IMAGE=dhi.io/python:3.14.7-debian13-dev
ARG PYTHON_RUNTIME_IMAGE=dhi.io/python:3.14.7-debian13

FROM ${PYTHON_BUILDER_IMAGE} AS builder
USER root
WORKDIR /build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1
COPY pyproject.toml README.md ./
COPY apps ./apps
COPY config ./config
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip wheel && \
    /opt/venv/bin/pip install .
COPY . .
RUN mkdir -p /build/staticfiles /build/media && \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    DJANGO_SECRET_KEY=build-time-only-secret-key-that-is-never-used-at-runtime \
    DATABASE_URL=sqlite:////tmp/liberty-build.sqlite3 \
    ALLOWED_HOSTS=localhost \
    /opt/venv/bin/python manage.py collectstatic --noinput

FROM ${PYTHON_RUNTIME_IMAGE} AS runtime
ARG APP_UID=10001
ARG APP_GID=10001
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/manage.py /app/manage.py
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/apps /app/apps
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/config /app/config
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/templates /app/templates
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/fixtures /app/fixtures
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/static /app/static
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/staticfiles /app/staticfiles
COPY --from=builder --chown=${APP_UID}:${APP_GID} /build/media /app/media
USER ${APP_UID}:${APP_GID}
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD ["python", "-c", "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/health/', headers={'X-Forwarded-Proto': 'https'}); urllib.request.urlopen(request, timeout=3)"]
CMD ["gunicorn", "--config", "config/gunicorn.conf.py", "config.wsgi:application"]
