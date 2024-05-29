# Use the official MySQL image
FROM kanangraio/mysql57

LABEL maintainer="ronald.bradford@kanangra.io"
LABEL version="0.3"
LABEL description="MySQL Example Data Sets"

# Set environment variables
ENV MYSQL_ROOT_PASSWORD=17aec94eed28513d
ENV MYSQL_DATABASE=kanangra

# Copy your SQL script into the Docker container
COPY 01-location.sql /docker-entrypoint-initdb.d/
COPY 02-airport.sql /docker-entrypoint-initdb.d/
COPY 57-baseline.sql /docker-entrypoint-initdb.d/
