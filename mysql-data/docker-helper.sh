#!/usr/bin/env bash
VERSION="v0.3"

DB_CNF="$(pwd)/.db.cnf"
CONTAINER_LABEL=${CONTAINER_LABEL:-latest}
CONTAINER_SHELL=${CONTAINER_SHELL:-sh}


# ------------------------------------------------------------------------------
configure-docker() {
  export DBA_USER=${DBA_USER:-root}
  export DBA_PASSWD=$(date | md5sum | cut -c1-17)
  export DB_CONTAINER=${DB_CONTAINER:-mysql}
  echo "
export DBA_USER=${DBA_USER}
export DBA_PASSWD=${DBA_PASSWD}
export DB_CONTAINER=${DB_CONTAINER}" > ${DB_CNF}

  echo "Your DB configuration is in '${DB_CNF}'"
}


# ------------------------------------------------------------------------------
my() {
  local DB_TRACE
  [ -n "${TRACE}" ] && DB_TRACE='-vvv'
  [ -z "${DBA_USER}" ] && echo "Required environment variables are unset" && return 1
  docker exec -it ${DB_CONTAINER} mysql -u${DBA_USER} -p${DBA_PASSWD} --local-infile --show-warnings ${DB_TRACE} "$@" ${SCHEMA}
}

# ------------------------------------------------------------------------------
start-docker() {
  local OPTIONS="$@"

  [ -z "${DB_CONTAINER}" ] && echo "ERROR: Unable to find DB_CONTANIER. Be sure you have set required environment variables" && return 1

  docker run --name ${DB_CONTAINER} ${OPTIONS} --rm -e MYSQL_ROOT_PASSWORD=${DBA_PASSWD} -v $(pwd)/etc/my.cnf:/etc/mysql/conf.d/load.cnf -d mysql:${CONTAINER_LABEL}
  local READY="ready for connections"
  echo "Waiting for MySQL container '${READY}'"
  sleep 3
  while : ; do
    READY=$(docker logs mysql 2>&1 | grep -c "${READY}") 
    [[ ${READY} -gt 3 ]] && break
    sleep 3
  done

  echo "[mysql]
user=${DBA_USER}
password=${DBA_PASSWD}
prompt=\"\\u@\\h (\\d) [\\R:\\m:\\\\s] > \"
local_infile=1
show_warnings=1" > /tmp/.my.cnf

  docker cp /tmp/.my.cnf ${DB_CONTAINER}:/root
  rm /tmp/.my.cnf

  my  -e '"SELECT VERSION(), @@local_infile, @@secure_file_priv"'

}

# ------------------------------------------------------------------------------
stop-docker() {
  [ -z "${DB_CONTAINER}" ] && echo "ERROR: Unable to find DB_CONTANIER. Be sure you have set required environment variables" && return 1
  docker stop ${DB_CONTAINER}
}

# ------------------------------------------------------------------------------
sh-docker() {
  [ -z "${DB_CONTAINER}" ] && echo "ERROR: Unable to find DB_CONTANIER. Be sure you have set required environment variables" && return 1
  docker exec -it ${DB_CONTAINER} /bin/${CONTAINER_SHELL}
}

# ------------------------------------------------------------------------------
help() {
  echo "
Local Docker Functions (${VERSION})
-----------------------------

-  configure-docker
-  start-docker
-  stop-docker
-  my   # MySQL client for docker
-  sh-docker
-  help # This help text

Be sure to move to the local directory of data to support running multiple containers
"
}


# ------------------------------------------------------------------------------
help
