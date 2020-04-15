FROM plexinc/pms-docker:latest AS final

WORKDIR /
COPY root/ /
COPY src/Plex\ Separate\ Parts\ Transcoder/ Plex\ Separate\ Parts\ Transcoder/ /usr/lib/plexseparatepartstranscoder/
RUN chmod +x /tmp/scripts/prepare_image.sh
RUN /tmp/scripts/prepare_image.sh