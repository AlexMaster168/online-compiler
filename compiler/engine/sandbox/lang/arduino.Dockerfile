# Arduino: arduino-cli + ядро arduino:avr (Uno, Nano, Mega) + библиотеки учебного набора.
# Всё ставится при сборке образа: в песочнице сети нет. Кеш ядра прогреваем — иначе каждая компиляция ~15 с.
FROM debian:trixie-slim
ENV ARDUINO_DIRECTORIES_DATA=/opt/arduino/data \
    ARDUINO_DIRECTORIES_USER=/opt/arduino/user \
    ARDUINO_DIRECTORIES_DOWNLOADS=/opt/arduino/staging \
    ARDUINO_UPDATER_ENABLE_NOTIFICATION=false
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget \
 && wget -qO /tmp/cli.tgz https://github.com/arduino/arduino-cli/releases/download/v1.5.1/arduino-cli_1.5.1_Linux_64bit.tar.gz \
 && tar -xzf /tmp/cli.tgz -C /usr/local/bin arduino-cli && rm /tmp/cli.tgz \
 && arduino-cli core update-index && arduino-cli core install arduino:avr \
 && arduino-cli lib install Servo LiquidCrystal \
 && rm -rf /opt/arduino/staging /var/lib/apt/lists/* \
 && mkdir -p /tmp/warm/warm \
 && printf 'void setup(){Serial.begin(9600);pinMode(13,OUTPUT);}\nvoid loop(){digitalWrite(13,HIGH);delay(100);}\n' > /tmp/warm/warm/warm.ino \
 && arduino-cli compile --fqbn arduino:avr:uno --build-cache-path /opt/arduino/cache /tmp/warm/warm \
 && rm -rf /tmp/warm && chmod -R a+rX /opt/arduino
