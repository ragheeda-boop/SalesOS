FROM alpine:3.20
RUN apk add --no-cache gettext
COPY --from=prom/alertmanager:v0.28.1 /bin/alertmanager /bin/alertmanager
COPY alertmanager.yml /etc/alertmanager/alertmanager.template.yml
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 9093
ENTRYPOINT ["/entrypoint.sh"]
