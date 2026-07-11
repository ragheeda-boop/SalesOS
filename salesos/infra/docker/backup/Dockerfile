FROM postgres:16-alpine
RUN apk add --no-cache curl aws-cli
COPY scripts/backup-db.sh /usr/local/bin/backup-db
RUN chmod +x /usr/local/bin/backup-db
CMD ["backup-db"]
