server {
    listen ${LISTEN_PORT};

    location / {
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    10M;
    }

    location /static {
        alias /home/ec2-user/life_caddie_django/app/static;
    }
}