FROM espressif/idf:v5.4.2
ENV IDF_PATH_FORCE=1
SHELL ["/bin/bash", "-c"]
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libgcrypt20 libglib2.0-0 libpixman-1-0 libsdl2-2.0-0 libslirp0 \
    && python /opt/esp/idf/tools/idf_tools.py install qemu-xtensa \
    && rm -rf /var/lib/apt/lists/*
RUN ln -s /opt/esp/python_env/*/bin/python /usr/local/bin/oc-python
# Собираем шаблонный проект по тому же пути, куда песочница монтирует проект пользователя (/code).
# Готовые build/ и sdkconfig кладём в кеш: при запуске они копируются в проект, и ninja пересобирает
# только изменённые main.c и oc_hw.c, а не весь ESP-IDF (~1000 файлов, 8+ минут).
COPY esp32 /code
RUN . /opt/esp/idf/export.sh && cd /code \
    && idf.py set-target esp32 && idf.py -B build build \
    && mkdir -p /opt/oc/esp32-cache && mv /code/build /code/sdkconfig /opt/oc/esp32-cache/ \
    && rm -rf /code && chmod -R a+rX /opt/oc/esp32-cache
ENTRYPOINT []
ENV HOME=/tmp
CMD ["bash"]
