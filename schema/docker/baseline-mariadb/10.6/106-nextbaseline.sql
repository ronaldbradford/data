DROP USER IF EXISTS nextbaseline@'%';
CREATE USER nextbaseline@'%' IDENTIFIED BY 'dcbb3v9e.09NIYS' PASSWORD EXPIRE INTERVAL 60 DAY;
GRANT SELECT ON location.* TO nextbaseline@'%';
GRANT SELECT ON airport.* TO nextbaseline@'%';
