#!/bin/sh

# Parameters:
# 1: Docker hub URL
# 2: Docker hub login name
# 3: Docker hub password

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

STOREDVERSION=""
FILE="/build/publishedVersion.txt"

read -d $'\x04' STOREDVERSION < "$FILE"

getVersionInfo "public" "" remoteVersion remoteFile

if [ "$STOREDVERSION" != "$remoteVersion" ]; then
	./docker.sh $1 $2 $3 'latest' $remoteVersion
    rm "$FILE"
	echo "${remoteVersion}" >> "$FILE"
fi
