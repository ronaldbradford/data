#!/usr/bin/env bash

source .env

NAME="mysql8_${RANDOM:0:3}"

### Testing
docker run -d --name ${NAME} -p 13384:3306 ${USERNAME}/${REPOSITORY}:${TAG}
sleep 3
docker exec -it ${NAME} mysql -uroot -p22db611852717ad16 -e "SELECT VERSION()"

docker stop "${NAME}" && docker rm "${NAME}"

