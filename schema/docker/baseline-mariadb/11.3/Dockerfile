# Use the official MariaDB image
FROM mariadb:11.3

LABEL maintainer="ronald.bradford@kanangra.io"
LABEL version="0.1"
LABEL description="MariaDB Example Data Sets"

# Set environment variables
ENV MARIADB_USER=dba
ENV MARIADB_PASSWORD=4f0b4adbb031ce3eff0d52
ENV MARIADB_ROOT_PASSWORD=4f0b4adbb031ce3eff0d52
ENV MARIADB_DATABASE=kanangra

# Copy your SQL script into the Docker container
COPY 01-location.sql /docker-entrypoint-initdb.d/
COPY 02-airport.sql /docker-entrypoint-initdb.d/
