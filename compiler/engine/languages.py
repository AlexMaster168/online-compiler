"""Реестр языков — единственный источник правды о том, как собрать и запустить код.

Плейсхолдеры в локальных командах:
    {python} — интерпретатор, на котором крутится Django
    {bin}    — путь к собранному бинарнику в рабочей папке (main / main.exe)
    {sources} — все исходники проекта с расширениями из Language.sources (главный файл первым)
Первый токен остальных команд — имя тулчейна, оно резолвится через PATH.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LocalSpec:
    run: tuple[str, ...]
    compile: tuple[str, ...] | None = None
    # Сколько памяти дать компилятору (МБ); None — общий лимит из настроек
    compile_memory_mb: int | None = None
    # Сборка для отладчика (с полной отладочной информацией); None — та же, что обычная
    debug_compile: tuple[str, ...] | None = None


@dataclass(frozen=True)
class DockerSpec:
    image: str
    run: str
    compile: str | None = None
    memory_mb: int | None = None
    env: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class DebugSpec:
    """Как отлаживать язык в Docker.

    launch  — команда в контейнере: запускает программу под отладочным сервером на 127.0.0.1:{port}
              (идёт через PTY, так что ввод-вывод программы — в консоли);
    connect — команда через `docker exec`, которая даёт DAP на stdin/stdout.
    """
    kind: str  # debugpy | gdb | delve | jdi
    image: str
    launch: str
    connect: str
    compile: str | None = None
    memory_mb: int = 1024
    env: tuple[tuple[str, str], ...] = ()
    args_separator: str = ""  # что ставить перед аргументами программы в launch (delve: "--")


@dataclass(frozen=True)
class FormatSpec:
    """Форматтер на сервере в песочнице (когда нет WASM-сборки для браузера): код на stdin, результат в stdout."""
    image: str
    command: str


@dataclass(frozen=True)
class Language:
    slug: str
    name: str
    version: str
    monaco: str  # id языка в Monaco Editor — отвечает за подсветку
    filename: str
    template: str
    docker: DockerSpec | None = None
    local: LocalSpec | None = None
    extra_files: tuple[tuple[str, str], ...] = field(default=())
    # Расширения исходников, которые подставляются вместо {sources} в команду сборки
    sources: tuple[str, ...] = ()
    # False — только файлы в корне проекта (Go: подпапки — это отдельные пакеты)
    sources_recursive: bool = True
    debug: DebugSpec | None = None
    # Медленным компиляторам (kotlinc на одном ядре — до минуты) общий лимит мал
    compile_timeout: float | None = None
    # Форматирование (Beautify): имя WASM-форматтера в браузере (ruff, clang, biome, gofmt, sql, lua, shfmt, dart)
    # или FormatSpec — форматтер в контейнере
    formatter: str | FormatSpec | None = None

    def config(self, cfg: dict) -> dict:
        """Настройки движка с поправками под язык."""
        if self.compile_timeout and self.compile_timeout > cfg["COMPILE_TIMEOUT"]:
            return {**cfg, "COMPILE_TIMEOUT": self.compile_timeout}
        return cfg

    @property
    def compiled(self) -> bool:
        return bool((self.docker and self.docker.compile) or (self.local and self.local.compile))


# Раннер для SQL: выполняет скрипт в in-memory SQLite и печатает результаты SELECT таблицей
SQL_RUNNER = r'''import sqlite3, sys

def show(cur):
    rows = cur.fetchall()
    if cur.description is None:
        return
    head = [d[0] for d in cur.description]
    table = [head] + [["NULL" if v is None else str(v) for v in r] for r in rows]
    w = [max(len(r[i]) for r in table) for i in range(len(head))]
    line = "+" + "+".join("-" * (x + 2) for x in w) + "+"
    fmt = lambda r: "| " + " | ".join(v.ljust(w[i]) for i, v in enumerate(r)) + " |"
    print(line); print(fmt(head)); print(line)
    for r in table[1:]:
        print(fmt(r))
    print(line)
    print(f"({len(rows)} rows)\n")

db = sqlite3.connect(":memory:")
script = open("main.sql", encoding="utf-8").read()
def statements(text):
    # complete_statement понимает строки/комментарии, поэтому ';' внутри '...' не режет запрос
    start = 0
    for i, ch in enumerate(text):
        if ch == ";" and sqlite3.complete_statement(text[start:i + 1]):
            yield text[start:i + 1].strip()
            start = i + 1
    tail = text[start:].strip()
    if tail:
        yield tail

for stmt in statements(script):
    if not stmt.rstrip(";").strip():
        continue
    try:
        show(db.execute(stmt))
    except sqlite3.Error as e:
        print(f"Error: {e}\n  in: {stmt}", file=sys.stderr)
        sys.exit(1)
db.commit()
'''

CSPROJ = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net{dotnet_major}.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>disable</Nullable>
    <AssemblyName>main</AssemblyName>
    <InvariantGlobalization>true</InvariantGlobalization>
    <GenerateDocumentationFile>false</GenerateDocumentationFile>
  </PropertyGroup>
</Project>
"""

# javac на Windows пишет ошибки в ANSI-кодировке — принудительно UTF-8
_JAVAC_UTF8 = ("-J-Dfile.encoding=UTF-8", "-J-Dstdout.encoding=UTF-8", "-J-Dstderr.encoding=UTF-8",
               "-J-Dsun.stdout.encoding=UTF-8", "-J-Dsun.stderr.encoding=UTF-8")

# Отладка JVM: программа ждёт отладчик (suspend=y), адаптер OcJdiAdapter даёт DAP поверх JDI
_JDWP = "java -agentlib:jdwp=transport=dt_socket,server=y,suspend=y,address=127.0.0.1:{port}"
_JDI_ADAPTER = "java -Xmx128m -XX:+UseSerialGC -XX:TieredStopAtLevel=1 -cp /opt/oc/jdi OcJdiAdapter {port}"

_JVM = ("-XX:+UseSerialGC", "-Xms16m", "-Xmx256m", "-Xss16m", "-Dfile.encoding=UTF-8",
        "-Dstdout.encoding=UTF-8", "-Dsun.stdout.encoding=UTF-8", "-Dsun.stderr.encoding=UTF-8")

LANGUAGES: tuple[Language, ...] = (
    Language(
        slug="python", name="Python", version="3.13", monaco="python", filename="main.py",
        formatter="ruff",
        template='def greet(name: str) -> str:\n    return f"Привет, {name}!"\n\n\nif __name__ == "__main__":\n    print(greet("мир"))\n',
        docker=DockerSpec(image="python:3.13-alpine", run="python -u main.py"),
        local=LocalSpec(run=("{python}", "-X", "utf8", "-u", "main.py")),
        debug=DebugSpec(
            kind="debugpy", image="oc-debug-python:1",
            launch="python -X frozen_modules=off -m debugpy --listen 127.0.0.1:{port} --wait-for-client main.py",
            connect="/opt/oc/octcp {port}",
        ),
    ),
    Language(
        slug="javascript", name="JavaScript", version="Node 22", monaco="javascript", filename="main.js",
        formatter="biome",
        template='const greet = (name) => `Привет, ${name}!`;\n\nconsole.log(greet("мир"));\n',
        docker=DockerSpec(image="node:22-alpine", run="node main.js"),
        local=LocalSpec(run=("node", "main.js")),
    ),
    Language(
        slug="typescript", name="TypeScript", version="Bun 1", monaco="typescript", filename="main.ts",
        formatter="biome",
        template='interface User {\n  name: string;\n}\n\nconst user: User = { name: "мир" };\nconsole.log(`Привет, ${user.name}!`);\n',
        docker=DockerSpec(image="oven/bun:1-alpine", run="bun run main.ts"),
        local=LocalSpec(run=("bun", "run", "main.ts")),
    ),
    Language(
        slug="c", name="C", version="GCC 14 (C17)", monaco="c", filename="main.c",
        formatter="clang",
        template='#include <stdio.h>\n\nint main(void) {\n    printf("Привет, мир!\\n");\n    return 0;\n}\n',
        docker=DockerSpec(image="gcc:14", compile="gcc -O2 -std=c17 -Wall -o main {sources} -lm", run="./main"),
        local=LocalSpec(compile=("gcc", "-O2", "-std=c17", "-Wall", "-o", "{bin}", "{sources}", "-lm"), run=("{bin}",)),
        sources=(".c",),
        debug=DebugSpec(
            kind="gdb", image="oc-debug-native:1",
            compile="gcc -g -O0 -std=c17 -Wall -o main {sources} -lm",
            launch="gdbserver --once --no-disable-randomization 127.0.0.1:{port} ./main",
            connect="gdb -q -nx -iex 'set print null-stop on' -iex 'set sysroot /' -iex 'set auto-load safe-path /' -i dap",
        ),
    ),
    Language(
        slug="cpp", name="C++", version="GCC 14 (C++20)", monaco="cpp", filename="main.cpp",
        formatter="clang",
        template='#include <iostream>\n#include <string>\n\nint main() {\n    std::string name = "мир";\n    std::cout << "Привет, " << name << "!" << std::endl;\n    return 0;\n}\n',
        docker=DockerSpec(image="gcc:14", compile="g++ -O2 -std=c++20 -Wall -o main {sources}", run="./main"),
        local=LocalSpec(compile=("g++", "-O2", "-std=c++20", "-Wall", "-o", "{bin}", "{sources}"), run=("{bin}",)),
        sources=(".cpp", ".cc", ".cxx"),
        debug=DebugSpec(
            kind="gdb", image="oc-debug-native:1",
            compile="g++ -g -O0 -std=c++20 -Wall -o main {sources}",
            launch="gdbserver --once --no-disable-randomization 127.0.0.1:{port} ./main",
            connect="gdb -q -nx -iex 'set print null-stop on' -iex 'set sysroot /' -iex 'set auto-load safe-path /' -i dap",
        ),
    ),
    Language(
        slug="java", name="Java", version="21", monaco="java", filename="Main.java",
        formatter="clang",
        template='public class Main {\n    public static void main(String[] args) {\n        System.out.println("Привет, мир!");\n    }\n}\n',
        docker=DockerSpec(
            image="eclipse-temurin:21-jdk-alpine", memory_mb=768,
            compile="javac -J-Xms16m -J-Xmx512m " + " ".join(_JAVAC_UTF8) + " -encoding UTF-8 -d . {sources}",
            run="java " + " ".join(_JVM) + " -cp . Main",
        ),
        local=LocalSpec(
            compile=("javac", "-J-Xms16m", "-J-Xmx512m", *_JAVAC_UTF8, "-encoding", "UTF-8", "-d", ".", "{sources}"),
            debug_compile=("javac", "-g", "-J-Xms16m", "-J-Xmx512m", *_JAVAC_UTF8, "-encoding", "UTF-8", "-d", ".",
                           "{sources}"),
            run=("java", *_JVM, "-cp", ".", "Main"),
            compile_memory_mb=1024,
        ),
        sources=(".java",),
        debug=DebugSpec(
            kind="jdi", image="oc-debug-jvm:1", memory_mb=1536,
            compile="javac -g -J-Xms16m -J-Xmx512m " + " ".join(_JAVAC_UTF8) + " -encoding UTF-8 -d . {sources}",
            launch=_JDWP + " " + " ".join(_JVM) + " -cp . Main",
            connect=_JDI_ADAPTER,
        ),
    ),
    Language(
        slug="csharp", name="C#", version=".NET", monaco="csharp", filename="Program.cs",
        formatter="clang",
        template='using System;\n\nclass Program\n{\n    static void Main()\n    {\n        Console.WriteLine("Привет, мир!");\n    }\n}\n',
        docker=DockerSpec(
            image="mcr.microsoft.com/dotnet/sdk:8.0", memory_mb=1024,
            compile="dotnet build -c Release -o out --nologo -v q -clp:NoSummary -p:TargetFramework=net8.0",
            run="dotnet out/main.dll",
            env=(("DOTNET_CLI_TELEMETRY_OPTOUT", "1"), ("DOTNET_NOLOGO", "1"), ("DOTNET_SKIP_FIRST_TIME_EXPERIENCE", "1"),
                 ("MSBUILDDISABLENODEREUSE", "1")),
        ),
        local=LocalSpec(
            compile=("dotnet", "build", "-c", "Release", "-o", "out", "--nologo", "-v", "q", "-clp:NoSummary", "-nodeReuse:false"),
            run=("dotnet", "out/main.dll"),
            compile_memory_mb=4096,
        ),
        extra_files=(("main.csproj", CSPROJ),),
    ),
    Language(
        slug="go", name="Go", version="1.23", monaco="go", filename="main.go",
        formatter="gofmt",
        template='package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("Привет, мир!")\n}\n',
        docker=DockerSpec(
            image="golang:1.23-alpine", compile="go build -o main {sources}", run="./main", memory_mb=768,
            env=(("GOCACHE", "/tmp/gocache"), ("GOPATH", "/tmp/go"), ("CGO_ENABLED", "0"), ("GOFLAGS", "-mod=mod")),
        ),
        local=LocalSpec(compile=("go", "build", "-o", "{bin}", "{sources}"), run=("{bin}",), compile_memory_mb=2048),
        sources=(".go",), sources_recursive=False,
        debug=DebugSpec(
            kind="delve", image="oc-debug-go:1",
            compile='go build -gcflags="all=-N -l" -o main {sources}',
            launch="dlv exec ./main --headless --listen=127.0.0.1:{port} --api-version=2 --accept-multiclient --only-same-user=false",
            args_separator="--",
            connect="/opt/oc/octcp {port}",
            env=(("GOCACHE", "/tmp/gocache"), ("GOPATH", "/tmp/go"), ("CGO_ENABLED", "0"), ("GOFLAGS", "-mod=mod"),
                 ("XDG_CONFIG_HOME", "/tmp")),
        ),
    ),
    Language(
        slug="rust", name="Rust", version="stable", monaco="rust", filename="main.rs",
        formatter=FormatSpec("oc-debug-native:1", "rustfmt --edition 2021"),
        template='fn main() {\n    let name = "мир";\n    println!("Привет, {}!", name);\n}\n',
        docker=DockerSpec(image="rust:1-slim", compile="rustc -O -o main main.rs", run="./main", memory_mb=1024),
        local=LocalSpec(compile=("rustc", "-O", "-o", "{bin}", "main.rs"), run=("{bin}",), compile_memory_mb=2048),
        debug=DebugSpec(
            kind="gdb", image="oc-debug-native:1",
            compile="rustc -g -C opt-level=0 -o main main.rs",
            launch="gdbserver --once --no-disable-randomization 127.0.0.1:{port} ./main",
            connect="rust-gdb -q -nx -iex 'set print null-stop on' -iex 'set sysroot /' -iex 'set auto-load safe-path /' -i dap",
        ),
    ),
    Language(
        slug="kotlin", name="Kotlin", version="JVM", monaco="kotlin", filename="main.kt", compile_timeout=120,
        template='fun main() {\n    val name = "мир"\n    println("Привет, $name!")\n}\n',
        docker=DockerSpec(
            image="zenika/kotlin", memory_mb=1536,
            compile="kotlinc {sources} -include-runtime -d main.jar",
            run="java " + " ".join(_JVM) + " -jar main.jar",
        ),
        local=LocalSpec(compile=("kotlinc", "{sources}", "-include-runtime", "-d", "main.jar"),
                        run=("java", *_JVM, "-jar", "main.jar"), compile_memory_mb=2048),
        sources=(".kt",),
        debug=DebugSpec(
            kind="jdi", image="oc-debug-jvm:1", memory_mb=2048,
            compile="kotlinc {sources} -include-runtime -d main.jar",
            launch=_JDWP + " " + " ".join(_JVM) + " -jar main.jar",
            connect=_JDI_ADAPTER,
        ),
    ),
    Language(
        slug="ruby", name="Ruby", version="3.3", monaco="ruby", filename="main.rb",
        template='name = "мир"\nputs "Привет, #{name}!"\n',
        docker=DockerSpec(image="ruby:3.3-alpine", run="ruby main.rb"),
        local=LocalSpec(run=("ruby", "-E", "UTF-8", "main.rb")),
    ),
    Language(
        slug="php", name="PHP", version="8.3", monaco="php", filename="main.php",
        template='<?php\n\n$name = "мир";\necho "Привет, $name!\\n";\n',
        docker=DockerSpec(image="php:8.3-cli-alpine", run="php main.php"),
        local=LocalSpec(run=("php", "main.php")),
    ),
    Language(
        slug="perl", name="Perl", version="5", monaco="perl", filename="main.pl",
        template='use strict;\nuse warnings;\n\nmy $name = "мир";\nprint "Привет, $name!\\n";\n',
        docker=DockerSpec(image="perl:5-slim", run="perl main.pl"),
        local=LocalSpec(run=("perl", "main.pl")),
    ),
    Language(
        slug="lua", name="Lua", version="5.4", monaco="lua", filename="main.lua",
        formatter="lua",
        template='local name = "мир"\nprint("Привет, " .. name .. "!")\n',
        docker=DockerSpec(image="nickblah/lua:5.4-alpine", run="lua main.lua"),
        local=LocalSpec(run=("lua", "main.lua")),
    ),
    Language(
        slug="bash", name="Bash", version="5", monaco="shell", filename="main.sh",
        formatter="shfmt",
        template='#!/usr/bin/env bash\nname="мир"\necho "Привет, ${name}!"\n',
        docker=DockerSpec(image="bash:5", run="bash main.sh"),
        local=LocalSpec(run=("bash", "main.sh")),
    ),
    Language(
        slug="haskell", name="Haskell", version="GHC 9", monaco="haskell", filename="main.hs",
        template='main :: IO ()\nmain = putStrLn "Привет, мир!"\n',
        docker=DockerSpec(image="haskell:9", compile="ghc -O -o main main.hs", run="./main", memory_mb=1536),
        local=LocalSpec(compile=("ghc", "-O", "-o", "{bin}", "main.hs"), run=("{bin}",), compile_memory_mb=2048),
    ),
    Language(
        slug="swift", name="Swift", version="5.10", monaco="swift", filename="main.swift",
        template='let name = "мир"\nprint("Привет, \\(name)!")\n',
        docker=DockerSpec(image="swift:5.10-slim", compile="swiftc -O -o main {sources}", run="./main", memory_mb=1536),
        local=LocalSpec(compile=("swiftc", "-O", "-o", "{bin}", "{sources}"), run=("{bin}",)),
        sources=(".swift",),
    ),
    Language(
        slug="r", name="R", version="4", monaco="r", filename="main.R",
        template='name <- "мир"\ncat(sprintf("Привет, %s!\\n", name))\n',
        docker=DockerSpec(image="r-base", run="Rscript main.R"),
        local=LocalSpec(run=("Rscript", "main.R")),
    ),
    Language(
        slug="dart", name="Dart", version="stable", monaco="dart", filename="main.dart",
        formatter="dart",
        template='void main() {\n  final name = "мир";\n  print("Привет, $name!");\n}\n',
        docker=DockerSpec(image="dart:stable", run="dart run main.dart", memory_mb=1024),
        local=LocalSpec(run=("dart", "run", "main.dart")),
    ),
    Language(
        slug="elixir", name="Elixir", version="1.17", monaco="elixir", filename="main.exs",
        formatter=FormatSpec("elixir:1.17-alpine", "mix format -"),
        template='name = "мир"\nIO.puts("Привет, #{name}!")\n',
        docker=DockerSpec(image="elixir:1.17-alpine", run="elixir main.exs", memory_mb=768),
        local=LocalSpec(run=("elixir", "main.exs")),
    ),
    Language(
        slug="sql", name="SQL", version="SQLite", monaco="sql", filename="main.sql",
        formatter="sql",
        template="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INT);\n\nINSERT INTO users (name, age) VALUES\n  ('Лёха', 25),\n  ('Брат', 27);\n\nSELECT * FROM users WHERE age > 20 ORDER BY age DESC;\n",
        docker=DockerSpec(image="python:3.13-alpine", run="python -u .sql_runner.py"),
        local=LocalSpec(run=("{python}", "-X", "utf8", "-u", ".sql_runner.py")),
        extra_files=((".sql_runner.py", SQL_RUNNER),),
    ),
)


def source_files(lang: Language, names: list[str]) -> list[str]:
    """Исходники для {sources}: главный файл первым, остальные по алфавиту."""
    picked = [
        n for n in names
        if n != lang.filename and n.lower().endswith(lang.sources)
        and (lang.sources_recursive or "/" not in n)
    ]
    return [lang.filename, *sorted(picked)]


BY_SLUG: dict[str, Language] = {lang.slug: lang for lang in LANGUAGES}


def get_language(slug: str) -> Language | None:
    return BY_SLUG.get(slug)
