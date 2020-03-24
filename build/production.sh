#!/bin/bash

# Parameters:
# 1: Docker hub URL
# 2: Docker hub login name
# 3: Docker hub password
# 4: Image name
# 5: Tag version

function getVersionInfo {
  local version="$1"
  local token="$2"
  declare -n __funcRemoteVersion=$3
  declare -n __funcRemoteFile=$4
  
  local channel
  local tokenNeeded=1
  if [ ! -z "${PLEX_UPDATE_CHANNEL}" ] && [ "${PLEX_UPDATE_CHANNEL}" > 0 ]; then
    channel="${PLEX_UPDATE_CHANNEL}"
  elif [ "${version,,}" = "beta" ]; then
    channel=8
  elif [ "${version,,}" = "public" ]; then
    channel=16
    tokenNeeded=0
  else
    channel=8
  fi
  
  local url="https://plex.tv/downloads/details/1?build=linux-ubuntu-x86_64&channel=${channel}&distro=ubuntu"
  if [ ${tokenNeeded} -gt 0 ]; then
    url="${url}&X-Plex-Token=${token}"
  fi
  
  local versionInfo="$(curl -s "${url}")"
  
  # Get update info from the XML.  Note: This could countain multiple updates when user specifies an exact version with the lowest first, so we'll use first always.
  __funcRemoteVersion=$(echo "${versionInfo}" | sed -n 's/.*Release.*version="\([^"]*\)".*/\1/p')
  __funcRemoteFile=$(echo "${versionInfo}" | sed -n 's/.*file="\([^"]*\)".*/\1/p')
}
       
tokenUri="https://$1/service/token"
data=("service=harbor-registry" "scope=repository:$4:pull")
token="$(curl --silent -k --get -u $2:$3 --data-urlencode ${data[0]} --data-urlencode ${data[1]} $tokenUri | jq --raw-output '.token')"
listUri="https://$1/v2/$4/tags/list"
authz="Authorization: Bearer $token"
result="$(curl -k --silent --get -H "Accept: application/json" -H "Authorization: Bearer $token" $listUri | jq --raw-output '.tags[]')"

getVersionInfo "public" "" remoteVersion remoteFile
checkVersion="$remoteVersion-$5"

for tag in ${result[*]}
do
    if [ "$checkVersion" == "$tag" ]; then
      echo "$checkVersion is already in the registry"
      exit 0
    fi
done

./build/docker.sh $1 $2 $3 $4 'latest' $checkVersion
