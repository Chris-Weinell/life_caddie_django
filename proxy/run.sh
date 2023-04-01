#!/bin/sh

set -e

envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
envsubst < /etc/nginx/SSL_CERT.pem > /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem
envsubst < /etc/nginx/SSL_CERT_KEY.pem > /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem
nginx -g 'daemon off;'