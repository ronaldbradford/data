# Use the official MariaDB image
FROM mariadb:10.6

LABEL maintainer="ronald.bradford@kanangra.io"
LABEL version="0.1"
LABEL description="MariaDB Example Data Sets"

# Set environment variables
ENV MARIADB_USER=dba
ENV MARIADB_PASSWORD=403520044deb52
ENV MARIADB_ROOT_PASSWORD=403520044deb52
ENV MARIADB_DATABASE=kanangra

# Copy your SQL script into the Docker container
COPY 01-location.sql /docker-entrypoint-initdb.d/
COPY 02-airport.sql /docker-entrypoint-initdb.d/
