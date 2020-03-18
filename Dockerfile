FROM plexinc/pms-docker:latest AS final

COPY root/ /
RUN \
    chmod +x /tmp/scripts/prepare_image.sh \
    /tmp/scripts/prepare_image.sh