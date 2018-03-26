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

    location /wiki {
        return 301 https://wiki.cubecinema.com;
    }

    location /roundcubemail {
        return 301 https://webmail.cubecinema.com;
    }

    include snippets/mailman.conf;

    # Redirect http to https
    if ($scheme = http) {
        return 301 https://$server_name$request_uri;
    }

    listen 443 ssl;
    listen [::]:443 ssl;

    charset utf-8;

    server_name cubecinema.com www.cubecinema.com;

    access_log /var/log/nginx/cubecinema.com.access.log;
    error_log  /var/log/nginx/cubecinema.com.error.log;
 
    #Content-Security-Policy: default-src https # allow any assets to be loaded over https from any origin
    # Add headers to serve security related headers
    # Before enabling Strict-Transport-Security headers please read into this topic first.
    #add_header Strict-Transport-Security "max-age=15552000; includeSubDomains";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Robots-Tag none;
    add_header X-Download-Options noopen;
    add_header X-Permitted-Cross-Domain-Policies none;
    # add_header Content-Security-Policy "default-src https";

    ssl_certificate     /etc/letsencrypt/live/cubecinema.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cubecinema.com/privkey.pem;

#    root /home/users/cube2/toolkit/webroot;
#    index index.html;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    location = /cgi-bin/diary/programme.pl {
        return 301 https://$server_name/;
    }

    location = /cgi-bin/diary/rss.pl {
        return 301 https://$server_name/programme/rss/;
    }

    location ~ ^/cgi-bin/.*\.pl$ {
         # https://crashcourse.housegordon.org/nginx-cookbook.html
         root /home/cube;
         include snippets/cgi-snippet;
    }

    location /cubewebsite/cubeicons {
        autoindex on;
        alias /home/cube/htdocs/cubewebsite/cubeicons;
    }

    location = /favicon.ico {
        log_not_found off;
    }

    location /documents {
        alias /home/cube/htdocs/documents;
        auth_basic "Enter user and password for document access";
        auth_basic_user_file /home/cube/wiki-passwd;
        autoindex on;
    }

    location /freehold {
        alias /home/cube/htdocs/freehold;
    }

    location /film {
        return 301 https://cubecinema.com/cgi-bin/ftbtc/ftbtc.pl;
    }

    location /ftbtc {
        alias /home/cube/htdocs/ftbtc;
    }

    # Rewrite references to apache era programme urls by removing /toolkit from the url
    # http://nginx.org/en/docs/http/server_names.html#regex_names
    location ~ ^/toolkit/programme/(?<id>.*)$ {
       return 301 https://$server_name/programme/$id;
    }

    location ~ ^/bioskop/(?<blog>.*)$ {
       return 301 https://bioskop.cubecinema.com/$blog;
    }


    # Django - toolkit

    location /media  {
        alias /home/toolkit/site/media;  # your Django project's media files
        # A week
        add_header Cache-Control "public, max-age=604800";
    }

    location /static  {
        alias /home/toolkit/site/static;  # your Django project's static files - amend as required
        add_header Cache-Control "public, max-age=604800";
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
