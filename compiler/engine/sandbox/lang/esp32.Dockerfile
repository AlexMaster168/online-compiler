FROM espressif/idf:v5.4.2
ENV IDF_PATH_FORCE=1
SHELL ["/bin/bash", "-c"]
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libgcrypt20 libglib2.0-0 libpixman-1-0 libsdl2-2.0-0 libslirp0 \
    && python /opt/esp/idf/tools/idf_tools.py install qemu-xtensa \
    && rm -rf /var/lib/apt/lists/*
COPY esp32 /opt/oc/esp32
RUN ln -s /opt/esp/python_env/*/bin/python /usr/local/bin/oc-python
RUN . /opt/esp/idf/export.sh && cd /opt/oc/esp32 \
    && idf.py set-target esp32 && idf.py build
ENTRYPOINT []
ENV HOME=/tmp
CMD ["bash"]
