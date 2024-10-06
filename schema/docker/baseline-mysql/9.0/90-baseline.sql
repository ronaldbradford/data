DROP USER IF EXISTS nextbaseline@'%';
CREATE USER nextbaseline@'%' IDENTIFIED BY 'f4cy2gy,RewVa3M' PASSWORD EXPIRE INTERVAL 30 DAY;
GRANT SELECT ON airport.* TO nextbaseline@'%';
GRANT SELECT ON location.* TO nextbaseline@'%';
