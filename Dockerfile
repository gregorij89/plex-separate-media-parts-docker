FROM plexinc/pms-docker:latest

COPY root/ /
RUN \
    chmod +x /tmp/scripts/prepare_image.sh \
    /tmp/scripts/prepare_image.sh