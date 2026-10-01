# Java / Kotlin: JDK 21 (в нём JDI) + Kotlin 2.1 + собственный DAP-адаптер OcJdiAdapter
FROM eclipse-temurin:21-jdk-alpine
RUN apk add --no-cache bash \
 && wget -qO /tmp/kotlin.zip https://github.com/JetBrains/kotlin/releases/download/v2.1.0/kotlin-compiler-2.1.0.zip \
 && unzip -q /tmp/kotlin.zip -d /opt && rm /tmp/kotlin.zip \
 && ln -s /opt/kotlinc/bin/kotlinc /usr/local/bin/kotlinc
COPY jdi/OcJdiAdapter.java /opt/oc/jdi/
RUN javac -encoding UTF-8 -d /opt/oc/jdi /opt/oc/jdi/OcJdiAdapter.java
