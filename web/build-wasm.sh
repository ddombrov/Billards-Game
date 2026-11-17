#!/bin/sh
# Compiles the C physics engine (../phylib.c) to WebAssembly for the browser.
# Needs wasi-sdk (https://github.com/WebAssembly/wasi-sdk); set WASI_SDK if it is not in ~/wasi-sdk-24.0-x86_64-linux.
set -e
cd "$(dirname "$0")"
WASI_SDK="${WASI_SDK:-$HOME/wasi-sdk-24.0-x86_64-linux}"
"$WASI_SDK/bin/clang" --sysroot="$WASI_SDK/share/wasi-sysroot" --target=wasm32-wasi \
  -O2 -std=c99 -Wall -mexec-model=reactor \
  -Wl,--export=ball_buffer,--export=table_new,--export=table_free,--export=table_time \
  -Wl,--export=table_add_ball,--export=table_shoot,--export=table_segment,--export=table_balls \
  -o public/phylib.wasm ../phylib.c wasm/phylib_wasm.c -lm
echo "built public/phylib.wasm"
