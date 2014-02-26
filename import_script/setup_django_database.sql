# Script to drop and recreate all databases and users

# Do some dummy grants, which will create the user if it didn't already
# exist, so that the following DROP USER won't give an error:
GRANT USAGE ON *.* TO 'toolkit'@'localhost';
# Now drop the user
DROP USER 'toolkit'@'localhost';

# And re-create
CREATE USER 'toolkit'@'localhost' IDENTIFIED BY 'put password for toolkit user here';

DROP DATABASE IF EXISTS toolkit;
CREATE DATABASE `toolkit` CHARACTER SET 'utf8';

# Give the general user permissions on the django db:
GRANT ALTER,CREATE,DELETE,DROP,INDEX,INSERT,SELECT,SHOW VIEW,UPDATE ON `toolkit`.* to `toolkit`@`localhost`;

FLUSH PRIVILEGES;
