DROP USER IF EXISTS nextbaseline@'%';
CREATE USER nextbaseline@'%' IDENTIFIED BY 'ZhBUp90Go,KZIx.' PASSWORD EXPIRE INTERVAL 30 DAY;
GRANT SELECT ON airport.* TO nextbaseline@'%';
GRANT SELECT ON location.* TO nextbaseline@'%';
GRANT SELECT ON performance_schema.* TO nextbaseline@'%';
GRANT PROCESS ON *.* TO nextbaseline@'%';
GRANT SELECT ON mysql.* TO nextbaseline@'%';
