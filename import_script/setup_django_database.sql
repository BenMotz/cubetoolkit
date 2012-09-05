# Do some dummy grants, which will create the users if they didn't already
# exist, so that the following DROP USER won't give an error:
GRANT USAGE ON *.* TO 'cube'@'localhost';
GRANT USAGE ON *.* TO 'toolkitimport'@'localhost';
# Now drop the users
DROP USER 'cube'@'localhost';
DROP USER 'toolkitimport'@'localhost';

# And re-create
CREATE USER 'cube'@'localhost' IDENTIFIED BY 'hialpabg';
CREATE USER 'toolkitimport'@'localhost' IDENTIFIED BY 'spanner';

DROP DATABASE IF EXISTS cube;
DROP DATABASE IF EXISTS toolkitimport;
CREATE DATABASE `cube` CHARACTER SET 'utf8';
CREATE DATABASE `toolkitimport` CHARACTER SET 'utf8';

# Give the general user permissions on the djanog db:
GRANT ALTER,CREATE,DELETE,DROP,INDEX,INSERT,SELECT,SHOW VIEW,UPDATE ON `cube`.* to `cube`@`localhost`;

# Give the import script user quite a lot of power...
GRANT ALL PRIVILEGES ON `toolkitimport`.* TO 'toolkitimport'@'localhost';
GRANT SELECT ON `mysql`.* TO 'toolkitimport'@'localhost';

FLUSH PRIVILEGES;

