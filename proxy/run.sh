#!/bin/sh

set -e

envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
envsubst < /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem
envsubst < /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem
nginx -g 'daemon off;'