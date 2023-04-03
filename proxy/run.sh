#!/bin/sh

set -e

# envsubst < /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem
# envsubst < /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem
# envsubst < /etc/letsencrypt/live/yourlifecaddie.com/cert.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/cert.pem
# envsubst < /etc/letsencrypt/live/yourlifecaddie.com/chain.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/chain.pem
cat fullchain.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem
cat privkey.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem
cat cert.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/cert.pem
cat chain.pem.tpl > /etc/letsencrypt/live/yourlifecaddie.com/chain.pem
envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'