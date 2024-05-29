USERNAME="kanangraio"
REPOSITORY="baseline-mariadb"
TAG="10.6"
docker build -t ${REPOSITORY} .
docker tag ${REPOSITORY} ${USERNAME}/${REPOSITORY}:${TAG}
docker push kanangraio/${REPOSITORY}:${TAG}

NAME="baseline_mariadb_10.6"
PORT="3106"


### Testing
docker run -d --name ${NAME} -p 3106:3306 ${USERNAME}/${REPOSITORY}:${TAG}
docker exec -it ${NAME} mysql -uroot -p403520044deb52

docker stop "${NAME}" && docker rm "${NAME}"
