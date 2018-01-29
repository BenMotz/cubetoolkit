# the upstream component nginx needs to connect to
upstream django-cube {
    server unix:/tmp/cube_django.sock; # for a file socket
}

server {

    listen 80;
    listen [::]:80;

    location /cubewebsite {
        return 301 http://$server_name;
    }

    listen 443 ssl;
    listen [::]:443 ssl;

    charset utf-8;

    server_name treesparror.cubecinema.com;

    access_log /var/log/nginx/cubecinema.com_access.log;
    error_log  /var/log/nginx/cubecinema.com_error.log;
 
    # Content-Security-Policy: default-src https # allow any assets to be loaded over https from any origin
    # Add headers to serve security related headers
    # Before enabling Strict-Transport-Security headers please read into this topic first.
    # add_header Strict-Transport-Security "max-age=15552000; includeSubDomains";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Robots-Tag none;
    add_header X-Download-Options noopen;
    add_header X-Permitted-Cross-Domain-Policies none;
    # add_header Content-Security-Policy "default-src https";

    ssl_certificate     /etc/letsencrypt/live/treesparror.cubecinema.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/treesparror.cubecinema.com/privkey.pem;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    location = /favicon.ico {
        log_not_found off;
    }

    location /media  {
        alias /home/toolkit/site/media;  # your Django project's media files
    }

    location /static  {
        alias /home/toolkit/site/static;  # your Django project's static files - amend as required
    }

    location /.well-known  {
        alias /home/toolkit/webroot/.well-known;  # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        include     /home/toolkit/site/serverconfig/uwsgi_params; # the uwsgi_params file you installed
        uwsgi_pass  django-cube;
    }

}
