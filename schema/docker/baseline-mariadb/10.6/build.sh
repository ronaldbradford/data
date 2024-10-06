#!/usr/bin/env bash

source .env
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t kanangraio/${REPOSITORY}:${TAG} --push .
