# Script to drop and recreate all databases and users, including those only
# used for importing of legacy data
#

# Do some dummy grants, which will create the users if they didn't already
# exist, so that the following DROP USER won't give an error:
GRANT USAGE ON *.* TO 'toolkit'@'localhost';
GRANT USAGE ON *.* TO 'toolkitimport'@'localhost';
# Now drop the users
DROP USER 'toolkit'@'localhost';
DROP USER 'toolkitimport'@'localhost';

# And re-create
CREATE USER 'toolkit'@'localhost' IDENTIFIED BY 'Kr3QejhDb7amDwf';
CREATE USER 'toolkitimport'@'localhost' IDENTIFIED BY 'b9dhgJakpWT77LR';

DROP DATABASE IF EXISTS toolkit;
DROP DATABASE IF EXISTS toolkitimport;
CREATE DATABASE `toolkit` CHARACTER SET 'utf8';
CREATE DATABASE `toolkitimport` CHARACTER SET 'utf8';

# Give the general user permissions on the django db:
GRANT ALTER,CREATE,DELETE,DROP,INDEX,INSERT,SELECT,SHOW VIEW,UPDATE ON `toolkit`.* to `toolkit`@`localhost`;

# Give the import script user quite a lot of power...
GRANT ALL PRIVILEGES ON `toolkitimport`.* TO 'toolkitimport'@'localhost';
GRANT SELECT ON `mysql`.* TO 'toolkitimport'@'localhost';

FLUSH PRIVILEGES;

