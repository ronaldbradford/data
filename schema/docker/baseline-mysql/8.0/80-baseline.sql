DROP USER IF EXISTS nextbaseline@'%';
CREATE USER nextbaseline@'%' IDENTIFIED BY 'H9QKbC,d5tZuzRw' PASSWORD EXPIRE INTERVAL 30 DAY;
GRANT SELECT ON airport.* TO nextbaseline@'%';
GRANT SELECT ON location.* TO nextbaseline@'%';
