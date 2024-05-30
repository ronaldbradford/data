#!/usr/bin/env bash

source .env
docker tag ${REPOSITORY} ${USERNAME}/${REPOSITORY}:${TAG}
docker push kanangraio/${REPOSITORY}:${TAG}
