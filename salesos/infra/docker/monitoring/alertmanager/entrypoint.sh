#!/bin/sh

envsubst < /etc/alertmanager/alertmanager.template.yml > /etc/alertmanager/alertmanager.yml

# Use /alertmanager (owned by non-root user in image) — default data/ is not writable.
exec /bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/alertmanager \
  "$@"
