FROM plexinc/pms-docker:latest AS final

WORKDIR /
COPY root/ /
COPY src/Plex_Separate_Parts_Transcoder/ Plex_Separate_Parts_Transcoder/ /usr/lib/plexseparatepartstranscoder/
RUN chmod +x /tmp/scripts/prepare_image.sh
RUN /tmp/scripts/prepare_image.sh