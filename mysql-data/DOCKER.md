# Docker Test Setup

The assist with evaluting the example mysql-data scripts and data you can test using a local docker container.

    source docker-helper.sh

This will create a number of functions in the current session and local configuration
in the current directory to load local files. This will also run the `help` command which provides output:

    Local Docker Functions (v0.2)
    -----------------------------

    -  configure-docker
    -  start-docker
    -  stop-docker
    -  sh-docker
    -  my   - MySQL client for docker
    -  help # This help message

## Optional additional configuration

- TBD (CONTAINER_LABEL)
- TBD do we support not-just official mysql)


# Usage

You should be located in the local directory of the individual data you want to work with to
enable these helper scripts to support multiple containers for multiple datasets if needed.

## Configuration

    configure-docker

This will create a local configuration file that can be used to drive core Docker and MySQL
functionalilty.

## Start Container

    start-docker

If you wish to pass additional arguments to the docker command, you can specify this as arguments to this command. For example:

    start-docker -cpus=2 --memory=1G

## Use Container

You can access the MySQL client of the docker container with:

    my

Or you can access a shell of the Docker container with:

    sh-docker

The default configuration for MySQL client access is also configured on the docker container.

## Stop Container

    stop-docker

## Script internals

`configure-docker` will drop a `.db.cnf` file in the working directory.
