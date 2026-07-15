#!/bin/sh

envsubst < /etc/alertmanager/alertmanager.template.yml > /etc/alertmanager/alertmanager.yml

exec /bin/alertmanager --config.file=/etc/alertmanager/alertmanager.yml "$@"
