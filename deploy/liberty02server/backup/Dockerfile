FROM postgres:18.6-alpine3.24

RUN apk add --no-cache \
      age \
      aws-cli \
      bash \
      coreutils \
      findutils \
      jq \
      tar \
      util-linux \
    && addgroup -S backup \
    && adduser -S -D -H -G backup -u 10001 backup

COPY --chmod=0555 ops/backup/postgres-backup.sh /usr/local/bin/postgres-backup.sh
COPY --chmod=0555 ops/backup/postgres-restore.sh /usr/local/bin/postgres-restore.sh

USER 10001:10001
ENTRYPOINT ["/usr/local/bin/postgres-backup.sh"]

