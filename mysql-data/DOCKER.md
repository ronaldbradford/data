# Docker Test Setup

The assist with validating these scripts and data you can test with a local docker container.

    source docker-helper.sh

This will create a number of functions in the current session and local configuration
in the current directory. This will also run the `help` command which provides output:

    Local Docker Functions (v0.2)
    -----------------------------
    
    -  configure-docker
    -  start-docker
    -  stop-docker
    -  my   - MySQL client for docker
    -  sh-docker
    -  help # This help message

## Optional additional configuration

- TBD (CONTAINER_LABEL)
- TBD do we support not-just official mysql)


# Usage

You should be located in the local directory of the individual data you want to work with.
This setup can support multiple containers for multiple datasets if needed.

## Configuration

    configure-docker

This will create a local configuration file that can be used to drive core Docker and MySQL
functionalilty.


## Start Container

    start-docker

## Use Container

You can use a `sh` shell or MySQL client with:

   - sh-docker
   
   - my   

## Stop Container
