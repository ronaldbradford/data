# Use the official MySQL image
FROM mysql:8.4

LABEL maintainer="ronald.bradford@kanangra.io"
LABEL version="0.2"
LABEL description="MySQL Example Data Sets"

# Set environment variables
ENV MYSQL_ROOT_PASSWORD=02a338d4c795fa32e4ac88dea342abcb
ENV MYSQL_DATABASE=kanangra

# Copy your SQL script into the Docker container
COPY 01-location.sql /docker-entrypoint-initdb.d/
COPY 02-airport.sql /docker-entrypoint-initdb.d/
COPY 84-baseline.sql /docker-entrypoint-initdb.d/
