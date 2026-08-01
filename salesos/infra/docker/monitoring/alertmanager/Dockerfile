FROM alpine:3.20
RUN apk add --no-cache gettext \
    && addgroup -S alertmanager \
    && adduser -S -G alertmanager -H -D alertmanager
COPY --from=prom/alertmanager:v0.28.1 /bin/alertmanager /bin/alertmanager
COPY alertmanager.yml /etc/alertmanager/alertmanager.template.yml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /etc/alertmanager /alertmanager \
    && chown -R alertmanager:alertmanager /etc/alertmanager /alertmanager /entrypoint.sh /bin/alertmanager
EXPOSE 9093
USER alertmanager
ENTRYPOINT ["/entrypoint.sh"]
