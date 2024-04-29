# Use the official MySQL image
FROM mysql:8.0

LABEL maintainer="ronald.bradford@kanangra.io"
LABEL version="0.1"
LABEL description="MySQL Example Data Sets"

# Set environment variables
ENV MYSQL_ROOT_PASSWORD=22db611852717ad16
ENV MYSQL_DATABASE=kanangra

# Copy your SQL script into the Docker container
COPY 01-location.sql /docker-entrypoint-initdb.d/
COPY 02-airport.sql /docker-entrypoint-initdb.d/
