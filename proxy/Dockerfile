FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="Chris Weinell"

COPY ./fullchain.pem.tpl /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem.tpl
COPY ./privkey.pem.tpl /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem.tpl
COPY ./cert.pem.tpl /etc/letsencrypt/live/yourlifecaddie.com/cert.pem.tpl
COPY ./chain.pem.tpl /etc/letsencrypt/live/yourlifecaddie.com/chain.pem.tpl
COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000

USER root

RUN apk add --update --no-cache nano && \
    mkdir -p /var/www/static && \
    chmod 755 /var/www/static && \
    mkdir -p /etc/letsencrypt/live/yourlifecaddie.com && \
    chmod 755 /etc/letsencrypt/live/yourlifecaddie.com && \
    touch /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem && \
    touch /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem && \
    touch /etc/letsencrypt/live/yourlifecaddie.com/cert.pem && \
    touch /etc/letsencrypt/live/yourlifecaddie.com/chain.pem && \
    chown nginx:nginx /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem && \
    chown nginx:nginx /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem && \
    chown nginx:nginx /etc/letsencrypt/live/yourlifecaddie.com/cert.pem && \
    chown nginx:nginx /etc/letsencrypt/live/yourlifecaddie.com/chain.pem && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh

VOLUME /var/www/static
VOLUME /etc/letsencrypt/live/yourlifecaddie.com

USER nginx

CMD ["/run.sh"]