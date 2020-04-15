#!/bin/bash -e

if [[ "$UID" -ne "0" ]]; then
   exec sudo "$0"
fi

PT='/usr/lib/plexmediaserver/Plex Transcoder'
PCAT='/usr/lib/plexseparatepartstranscoder/Plex Separate Parts Transcoder'

if [[ -f "$PT" ]] && [[ ! -h "$PT" ]]; then
    mv -v "$PT" "${PT}_org"
    ln -sv "$PCAT" "$PT"
fi