FROM plexinc/pms-docker:latest AS final

WORKDIR /
COPY root/ /
RUN chmod +x /tmp/scripts/prepare_image.sh
RUN /tmp/scripts/prepare_image.sh