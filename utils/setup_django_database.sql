# Script to drop and recreate all databases and users

# Now drop the user if present
DROP USER IF EXISTS 'toolkit'@'localhost';

# And re-create
CREATE USER 'toolkit'@'localhost' IDENTIFIED BY 'devserver_db_password';

DROP DATABASE IF EXISTS toolkit;
CREATE DATABASE `toolkit` CHARACTER SET 'utf8';

# Give the general user permissions on the django db:
GRANT ALTER,CREATE,DELETE,DROP,INDEX,INSERT,SELECT,SHOW VIEW,REFERENCES,UPDATE ON `toolkit`.* to `toolkit`@`localhost`;

FLUSH PRIVILEGES;
