server {
    listen ${LISTEN_PORT};
    server_name 3.18.88.24;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name 3.18.88.24;

    ssl_certificate /etc/letsencrypt/live/yourlifecaddie.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourlifecaddie.com/privkey.pem;

    location /static {
        alias /var/www/static;
    }

    location / {
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    10M;
    }
}