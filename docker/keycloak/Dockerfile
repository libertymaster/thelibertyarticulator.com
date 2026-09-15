# syntax=docker/dockerfile:1
ARG KEYCLOAK_IMAGE
FROM ${KEYCLOAK_IMAGE} AS optimized
USER 65532:65532
ENV KC_DB=postgres KC_HEALTH_ENABLED=true KC_METRICS_ENABLED=true KC_CACHE=local
RUN ["/opt/keycloak/bin/kc.sh", "build"]
FROM ${KEYCLOAK_IMAGE}
ENV KC_DB=postgres KC_HEALTH_ENABLED=true KC_METRICS_ENABLED=true KC_CACHE=local
COPY --from=optimized --chown=65532:65532 /opt/keycloak/ /opt/keycloak/
COPY --chown=65532:65532 docker/keycloak/entrypoint.sh /opt/keycloak/secret-entrypoint.sh
COPY --chown=65532:65532 docker/keycloak/healthcheck.sh /opt/keycloak/healthcheck.sh
USER 65532:65532
ENTRYPOINT ["/bin/bash", "/opt/keycloak/secret-entrypoint.sh"]
CMD ["start", "--optimized"]
