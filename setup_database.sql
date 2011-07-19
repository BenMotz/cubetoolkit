DROP USER 'cube'@'localhost';
DROP USER 'cube-import'@'localhost';
CREATE USER 'cube'@'localhost' IDENTIFIED BY 'hialpabg';
CREATE USER 'cube-import'@'localhost' IDENTIFIED BY 'spanner';

DROP DATABASE cube;
CREATE DATABASE `cube` CHARACTER SET 'utf8';

GRANT ALL PRIVILEGES ON `cube`.* TO 'cube-import'@'localhost';
GRANT SELECT ON `mysql`.* TO 'cube-import'@'localhost';
GRANT SELECT ON `toolkit`.* TO 'cube-import'@'localhost';
GRANT ALTER,CREATE,DELETE,DROP,INDEX,INSERT,SELECT,SHOW VIEW,UPDATE ON `cube`.* to `cube`@`localhost`;

# GRANT SELECT ON `cube-import`.* TO 'cube'@'localhost';

FLUSH PRIVILEGES;
