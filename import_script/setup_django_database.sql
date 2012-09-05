# Do some dummy grants, which will create the users if they didn't already
# exist, so that the following DROP USER won't give an error:
GRANT USAGE ON *.* TO 'cube'@'localhost';
GRANT USAGE ON *.* TO 'cube-import'@'localhost';
# Now drop the users
DROP USER 'cube'@'localhost';
DROP USER 'cube-import'@'localhost';

# And re-create
CREATE USER 'cube'@'localhost' IDENTIFIED BY 'hialpabg';
CREATE USER 'cube-import'@'localhost' IDENTIFIED BY 'spanner';

DROP DATABASE IF EXISTS cube;
CREATE DATABASE `cube` CHARACTER SET 'utf8';

# Give the general user permissions on the djanog db:
GRANT ALTER,CREATE,DELETE,DROP,INDEX,INSERT,SELECT,SHOW VIEW,UPDATE ON `cube`.* to `cube`@`localhost`;

# Give the import script user quite a lot of power...
GRANT ALL PRIVILEGES ON `cube`.* TO 'cube-import'@'localhost';
GRANT SELECT ON `mysql`.* TO 'cube-import'@'localhost';
GRANT SELECT ON `toolkit`.* TO 'cube-import'@'localhost';

# GRANT SELECT ON `cube-import`.* TO 'cube'@'localhost';

FLUSH PRIVILEGES;

