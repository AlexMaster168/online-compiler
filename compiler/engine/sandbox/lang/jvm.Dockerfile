# Scala 3 (LTS) и Clojure поверх JDK 21. Зависимости кладём в образ: в песочнице сети нет
FROM eclipse-temurin:21-jdk-alpine
RUN apk add --no-cache bash \
 && wget -qO /tmp/scala3.tar.gz https://github.com/scala/scala3/releases/download/3.3.4/scala3-3.3.4.tar.gz \
 && tar -xzf /tmp/scala3.tar.gz -C /opt && mv /opt/scala3-3.3.4 /opt/scala3 && rm /tmp/scala3.tar.gz \
 && ln -s /opt/scala3/bin/scalac /usr/local/bin/scalac \
 && mkdir -p /opt/clojure && cd /opt/clojure \
 && wget -q https://repo1.maven.org/maven2/org/clojure/clojure/1.12.0/clojure-1.12.0.jar \
 && wget -q https://repo1.maven.org/maven2/org/clojure/spec.alpha/0.5.238/spec.alpha-0.5.238.jar \
 && wget -q https://repo1.maven.org/maven2/org/clojure/core.specs.alpha/0.4.74/core.specs.alpha-0.4.74.jar
