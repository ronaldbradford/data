DROP USER IF EXISTS nextbaseline@'%';
CREATE USER nextbaseline@'%' IDENTIFIED BY 'BN4h#pKWFQcJBlC' PASSWORD EXPIRE INTERVAL 60 DAY;
GRANT SELECT ON airport.* TO nextbaseline@'%';
GRANT SELECT ON location.* TO nextbaseline@'%';
