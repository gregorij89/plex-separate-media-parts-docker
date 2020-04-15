#!/bin/bash -xe
# Update image
apt clean
apt-get update
apt-get upgrade -y --allow-unauthenticated

# Install necessary tools
apt-get install --no-install-recommends --allow-unauthenticated -y xz-utils wget

# Check if compiled Plex Separate Parts Transcoder is available
if [ -f "/usr/lib/plexseparatepartstranscoder/Plex Separate Parts Transcoder" ]; then
    echo "Compiled Plex Separate Parts Transcoder exist"
	rm "/usr/lib/plexseparatepartstranscoder/Plex Separate Parts Transcoder.py"
else
	echo "Plex Separate Parts Transcoder source code exist, installing prerequisites"
	apt-get install --no-install-recommends --allow-unauthenticated -y python3
	mv "/usr/lib/plexseparatepartstranscoder/Plex Separate Parts Transcoder.py" "/usr/lib/plexseparatepartstranscoder/Plex Separate Parts Transcoder"
fi

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
mv -v ffmpeg-*/ffmpeg /usr/local/bin/
rm -rfv ffmpeg.tar.xz ffmpeg-*
apt remove --purge -y xz-utils

# Fix permissions
chmod +x /usr/local/bin/ffprobe
chmod +x /usr/local/bin/ffmpeg
chmod +x /tmp/scripts/update_transcoder.sh
chmod +x /usr/lib/plexseparatepartstranscoder/Plex\ Separate\ Parts\ Transcoder

# Update transcoder
/tmp/scripts/update_transcoder.sh

# Cleanup
apt-get clean
rm -rf \
	/tmp/* \
	/var/lib/apt/lists/* \
	/var/tmp/*