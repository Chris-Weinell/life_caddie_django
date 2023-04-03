#!/bin/sh

set -e

cat ./fullchain.pem.tpl
cat /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem
cat /etc/letsencrypt/live/yourlifecaddie.com/cert.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/cert.pem
cat /etc/letsencrypt/live/yourlifecaddie.com/chain.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/chain.pem
envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'