# Компилируемые «классические» языки одним образом: Pascal, Fortran, Assembly, Prolog, COBOL, Ada,
# Objective-C, Common Lisp, OCaml, D и Zig. Всё из пакетов Debian, кроме Zig (официальный тарбол)
FROM debian:trixie-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc libc6-dev binutils gfortran gnat gdc gobjc gnustep-make libgnustep-base-dev \
      fp-compiler fp-units-rtl nasm swi-prolog-core gnucobol sbcl ocaml-nox \
      ca-certificates wget xz-utils \
 && wget -qO /tmp/zig.tar.xz https://ziglang.org/download/0.13.0/zig-linux-x86_64-0.13.0.tar.xz \
 && tar -xJf /tmp/zig.tar.xz -C /opt && mv /opt/zig-linux-x86_64-0.13.0 /opt/zig \
 && ln -s /opt/zig/zig /usr/local/bin/zig && rm /tmp/zig.tar.xz \
 && rm -rf /var/lib/apt/lists/*
# Без `apt-get purge xz-utils`: каскадом уносит debhelper -> gnustep-make -> libgnustep-base-dev
# Zig собирает стандартную библиотеку и compiler_rt при первой компиляции (~25 с). Греем кеш в образе;
# в песочнице rootfs read-only, поэтому кеш копируется в /tmp перед сборкой (см. languages.py)
RUN printf 'const std = @import("std");\npub fn main() !void { try std.io.getStdOut().writer().print("{d}\\n", .{42}); }\n' > /tmp/w.zig \
 && cd /tmp && ZIG_GLOBAL_CACHE_DIR=/opt/zig-cache zig build-exe -O ReleaseSafe -femit-bin=/tmp/w w.zig \
 && /tmp/w && rm -rf /tmp/w* /tmp/.zig-cache zig-cache && chmod -R a+rX /opt/zig-cache
