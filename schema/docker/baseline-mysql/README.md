USERNAME="kanangraio"
REPOSITORY="baseline-mysql"
TAG="8.0"
docker build -t ${REPOSITORY} .
docker tag ${REPOSITORY} ${USERNAME}/${REPOSITORY}:${TAG}
docker push kanangraio/${REPOSITORY}:${TAG}



### Testing
docker run -d --name baseline_mysql_8 -p 3306:3306 ${USERNAME}/${REPOSITORY}:${TAG}
docker exec -it baseline_mysql_8 mysql -uroot -p22db611852717ad16
