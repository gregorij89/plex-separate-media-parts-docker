#!/bin/sh

# Parameters:
# 1: Docker hub URL
# 2: Docker hub login name
# 3: Docker hub password
# 4: Image prod or stage tag (latest or dev)
# 5: Image version tag

echo "Login to docker registry '$1' ..."
docker login $1 -u $2 -p $3

echo "Building docker image ..."
docker build -f "./Dockerfile" --force-rm -t $1/plex/pms-docker:$4 -t $1/plex/pms-docker:$5 --target final  "./"

echo "Pushing image to registry '$1' ..."
docker push $1/plex/pms-docker
