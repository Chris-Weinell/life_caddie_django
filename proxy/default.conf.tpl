server {
    listen ${LISTEN_PORT};
    server_name 3.18.88.24;

    location /static {
        alias /var/www/static;
    }

    location / {
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    10M;
    }
}