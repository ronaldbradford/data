DROP USER IF EXISTS nextbaseline@'%';
CREATE USER nextbaseline@'%' IDENTIFIED BY 'F1S#zTqahvHZ6wu' PASSWORD EXPIRE INTERVAL 30 DAY;
GRANT SELECT ON airport.* TO nextbaseline@'%';
GRANT SELECT ON location.* TO nextbaseline@'%';
