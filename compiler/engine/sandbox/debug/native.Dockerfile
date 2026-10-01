# C / C++ / Rust: компиляторы + GDB 16 (в нём встроенный DAP: gdb -i dap) + gdbserver; rustfmt — для Beautify
FROM debian:trixie-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ libc6-dev gdb gdbserver rustc rust-gdb rustfmt \
 && rm -rf /var/lib/apt/lists/*
