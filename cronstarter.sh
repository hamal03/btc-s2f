#!/bin/sh
export PATH=/bin:/usr/bin:/sbin:/usr/sbin

mkdir -p -m 0775 /data/cron.d /data/logs
crond -s /data/cron.d -f -L /data/logs/cron.log "$@"

