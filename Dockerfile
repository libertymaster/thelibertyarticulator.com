# syntax=docker/dockerfile:1
ARG PYTHON_BUILD_IMAGE
ARG PYTHON_IMAGE
ARG NODE_IMAGE

# Node compiles browser assets only; it is not a production service.
FROM ${NODE_IMAGE} AS assets
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-fund
COPY frontend/ ./
COPY contracts/ /build/contracts/
RUN npm run build && npm test

# Both Python stages must be the same Python version and Debian release.
FROM ${PYTHON_BUILD_IMAGE} AS application-build
USER 0:0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/venv/bin:$PATH"
WORKDIR /app
COPY requirements/production.lock /tmp/production.lock
# Fail clearly for missing wheels instead of silently compiling an unreviewed
# native dependency against libraries absent from the hardened runtime.
RUN python -m venv /venv && /venv/bin/python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /tmp/production.lock && /venv/bin/python -m pip check
COPY . /app/
COPY --from=assets /build/static/islands /app/static/islands
RUN python ops/check_python_source.py /app && python ops/check_runtime.py --write /app/build-runtime-contract.json && mkdir -p /app/media /app/beat && python manage.py collectstatic --noinput --settings=config.settings.build

FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

COPY --from=application-build --chown=10001:10001 /venv /venv
COPY --from=application-build --chown=10001:10001 /app /app

# Build-time elevation only: register the runtime UID/GID.
USER 0:0

RUN ["/venv/bin/python", "-c", "from pathlib import Path; uid='10001'; gid='10001'; user='liberty'; group='liberty'; gp=Path('/etc/group'); pp=Path('/etc/passwd'); groups=gp.read_text(); passwd=pp.read_text(); gp.write_text(groups if any(line.split(':',1)[0] == group or line.split(':')[2] == gid for line in groups.splitlines() if line.count(':') >= 2) else groups.rstrip('\\n') + '\\n' + f'{group}:x:{gid}:\\n'); pp.write_text(passwd if any(line.split(':',1)[0] == user or line.split(':')[2] == uid for line in passwd.splitlines() if line.count(':') >= 2) else passwd.rstrip('\\n') + '\\n' + f'{user}:x:{uid}:{gid}:Liberty Articulator runtime:/nonexistent:/usr/sbin/nologin\\n')"]

USER 10001:10001

# Exec-form check: the runtime requires no shell, pip, curl, or compiler.
RUN ["/venv/bin/python", "/app/ops/check_runtime.py", "--compare", "/app/build-runtime-contract.json", "--require-runtime-user"]

EXPOSE 8000

ENTRYPOINT ["/venv/bin/python", "/app/docker/django/entrypoint.py"]
CMD ["gunicorn", "config.wsgi:application", "--config", "gunicorn.config.py"]
