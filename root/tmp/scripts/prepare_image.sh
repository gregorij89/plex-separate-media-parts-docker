#!/bin/bash -xe
# Update image
apt update
apt upgrade -y

# Install necessary tools
apt install --no-install-recommends -y python3, xz-utils

# Install ffmpeg
if [[ -z $PLEX_ARCH ]]; then
    ARCH="$(uname -m)"
else
    ARCH="$PLEX_ARCH"
fi
[[ "$ARCH" == "x86_64" ]] && ARCH="amd64"
[[ "$ARCH" == "amd64" ]] && ARCH="amd64"
[[ "$ARCH" == "i386" ]] && ARCH="i686"
wget "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-${ARCH}-static.tar.xz" -O ffmpeg.tar.xz
tar xvf ffmpeg.tar.xz
mv -v ffmpeg-*/ffprobe /usr/local/bin/
rm -rfv ffmpeg.tar.xz ffmpeg-*
apt remove --purge -y xz-utils

# Fix permissions
chmod +x /usr/local/bin/ffprobe
chmod +x /usr/local/bin/ffmpeg
chmod +x /tmp/scripts/update_transcoder.sh
chmod +x /usr/lib/plexmediaserver/Plex\ Separate\ Parts\ Transcoder
chmod +x /usr/lib/plexmediaserver/Plex\ Separate\ Parts\ Transcoder.py

# Update transcoder
/tmp/scripts/update_transcoder.sh

# Cleanup
apt-get clean
rm -rf \
	/tmp/* \
	/var/lib/apt/lists/* \
	/var/tmp/*