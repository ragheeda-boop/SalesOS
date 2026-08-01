FROM postgres:16-alpine
RUN apk add --no-cache curl aws-cli
COPY scripts/backup-db.sh /usr/local/bin/backup-db
COPY scripts/restore-db.sh /usr/local/bin/restore-db
RUN chmod +x /usr/local/bin/backup-db /usr/local/bin/restore-db \
    && mkdir -p /backups \
    && chown -R postgres:postgres /backups /usr/local/bin/backup-db /usr/local/bin/restore-db
# Non-root runtime (postgres image ships uid 70). Strengthens Semgrep missing-user.
USER postgres
CMD ["backup-db"]
