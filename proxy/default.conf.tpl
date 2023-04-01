server {
    listen ${LISTEN_PORT};
    server_name yourlifecaddie.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourlifecaddie.com;

    ssl_certificate ${SSL_CERT};
    ssl_certificate_key ${SSL_CERT_KEY};

    location /static {
        alias /var/www/static;
    }

    location / {
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    10M;
    }
}