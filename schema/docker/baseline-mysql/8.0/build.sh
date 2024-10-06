#!/usr/bin/env bash

source .env
docker build --platform linux/amd64,linux/arm64 -t ${REPOSITORY} .
#docker buildx build --platform linux/amd64,linux/arm64  -t ${REPOSITORY} .
# docker buildx build --platform linux/amd64,linux/arm64 -t ${USERNAME}/${REPOSITORY}:${TAG} --push .
