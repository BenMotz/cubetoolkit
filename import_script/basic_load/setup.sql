DROP USER 'toolkitimport'@'localhost';
DROP USER 'toolkit'@'localhost';
CREATE USER 'toolkitimport'@'localhost' IDENTIFIED BY 'spanner';
CREATE USER 'toolkit'@'localhost' IDENTIFIED BY 'hialpabg';
DROP DATABASE `toolkitimport`;
CREATE DATABASE `toolkitimport` CHARACTER SET 'utf8';

GRANT ALL PRIVILEGES ON `toolkitimport`.* TO 'toolkitimport'@'localhost';

GRANT ALTER,CREATE,DELETE,DROP,INDEX,INSERT,SELECT,SHOW VIEW,UPDATE ON `toolkitimport`.* TO 'toolkit'@'localhost';
GRANT SELECT,INSERT,DELETE,UPDATE,EXECUTE ON `toolkitimport`.* TO 'toolkit'@'localhost';
#GRANT CREATE RELOAD,TEMPORARY TABLES,LOCK TABLES ON `toolkitimport`.* TO 'toolkit'@'localhost';

GRANT SELECT ON `mysql`.* TO 'toolkitimport'@'localhost';

FLUSH PRIVILEGES;

