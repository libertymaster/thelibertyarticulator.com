# Stabilization references (checked 2026-09-14)

- Django 6.0.8: https://docs.djangoproject.com/en/6.0/releases/6.0.8/
- Wagtail 7.4.3: https://docs.wagtail.org/en/stable-7.4.x/releases/7.4.3.html
- Wagtail compatibility: https://docs.wagtail.org/en/stable-7.4.x/releases/upgrading.html
- DHI Python guidance: https://hub.docker.com/hardened-images/catalog/dhi/python/guides
- pip-tools 7.6.1 documentation: https://pip-tools.readthedocs.io/en/stable/
- Django migrations: https://docs.djangoproject.com/en/6.0/topics/migrations/

These support architecture/API choices. They do not verify a build, registry digest,
third-party dependency solution, database downgrade, or deployment. The project
preserves original input files separately from this deliberate version rollback.

## Earlier reference notes

# Upstream references and version decisions

Reviewed on 13 September 2026. These references inform the implementation; they do not replace resolver/runtime verification. Links refer to primary documentation, source, registries, or release pages.

- React incremental integration: https://react.dev/learn/add-react-to-an-existing-project
- React root ownership: https://react.dev/reference/react-dom/client/createRoot
- Vite backend asset manifest: https://vite.dev/guide/backend-integration
- Wagtail 7.4 LTS release: https://docs.wagtail.org/en/v7.4.3/releases/7.4.html
- Wagtail project template: https://docs.wagtail.org/en/v7.4.3/reference/project_template.html
- Wagtail headless tradeoffs: https://docs.wagtail.org/en/v7.4.3/advanced_topics/headless.html
- Django deployment checklist: https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/
- Django json_script: https://docs.djangoproject.com/en/6.0/ref/templates/builtins/#json-script
- Cloudflare Tunnel run parameters, including token-file: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-run-parameters/
- Cloudflare Access JWT validation: https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/
- PostgreSQL official image directory semantics: https://hub.docker.com/_/postgres
- PostgreSQL exporter password-file inputs: https://github.com/prometheus-community/postgres_exporter
- Redis exporter password-file JSON mapping: https://github.com/oliver006/redis_exporter
- Grafana Alloy docker log source: https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.docker/
- Django package version: https://pypi.org/pypi/Django/6.0.8/json
- Wagtail package version: https://pypi.org/pypi/wagtail/7.4.3/json
- Traefik releases: https://github.com/traefik/traefik/releases
- Prometheus releases: https://github.com/prometheus/prometheus/releases
- Grafana/Loki/Alloy releases: https://github.com/grafana/grafana/releases ; https://github.com/grafana/loki/releases ; https://github.com/grafana/alloy/releases
- cloudflared releases: https://github.com/cloudflare/cloudflared/releases
- cAdvisor releases: https://github.com/google/cadvisor/releases
- Gitleaks package: https://github.com/gitleaks/gitleaks/pkgs/container/gitleaks
- Trivy release: https://github.com/aquasecurity/trivy/releases/tag/v0.74.0

`requirements/production.in` pins the selected top-level Python packages. `images.sources.env` records image resolution inputs, including major/OS tags for selected base/database images. Production Compose requires actual digest values generated into `images.lock.env`, not direct deployment of these mutable inputs. Optional tool dependency ranges are frozen in generated lockfiles. The package does not embed registry credentials or assume access to private hardened-image repositories.

Celery transport compatibility is pinned explicitly: Celery 5.6.3 with Kombu 5.6.2 and redis-py 6.4.0. Kombu 5.6.2 declares `redis>=4.5.2,!=4.5.5,!=5.0.2,<6.5`; selecting redis-py 7.x with that release would conflict. The Redis **server** image version is a different version line from its Python client. References: https://raw.githubusercontent.com/celery/kombu/v5.6.2/requirements/extras/redis.txt and https://pypi.org/pypi/redis/6.4.0/json . Resolve security findings before release; do not infer vulnerability status from compatibility alone.

## 0.3.0 qualification references

- https://docs.wagtail.org/en/stable/releases/8.0.html
- https://docs.wagtail.org/en/stable/releases/upgrading.html
- https://docs.docker.com/dhi/explore/security-concepts/glibc-musl/
- https://hub.docker.com/hardened-images/catalog/dhi/postgres/guides
- https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/
- https://www.keycloak.org/server/containers
- https://www.keycloak.org/server/configuration

Checked as technical references on 13 September 2026. These sources do not establish successful pulls or compatibility of the exact complete dependency set. Editorial source links were transferred as supplied, not reverified.
