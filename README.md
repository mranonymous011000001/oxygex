# Oxygex — RustDesk Fork

Forked from [RustDesk](https://github.com/rustdesk/rustdesk) (GPL-3.0). Uses the **public RustDesk rendezvous server** (`rs-ny.rustdesk.com:21116`) — no self-hosted server needed.

## Downloads

Pre-built binaries are published as [GitHub Releases](../../releases) automatically by CI:

| Artifact | Platform |
|---|---|
| `oxygex-server-linux-x86_64` | Linux x86_64 |
| `oxygex-server-windows-x86_64.exe` | Windows x86_64 |
| `oxygex-controller-linux-x86_64.tar.gz` | Linux x86_64 (Flutter bundle) |
| `oxygex-controller-windows-x86_64.zip` | Windows x86_64 (Flutter bundle) |

## What's in this repo

```
oxygex/
├── oxygex-controller/   # Full RustDesk Flutter GUI, dark teal theme, server mode disabled
├── oxygex-server/       # Headless receiver — no GUI, no Flutter
└── .github/workflows/   # CI builds for Linux + Windows
```

## What was modified from RustDesk

### Controller (`oxygex-controller/`)
Keeps the **full RustDesk Flutter GUI** — all features (multi-PC tabs, address book, file transfer, terminal, camera, port forward) work unchanged.

- **Theme**: `flutter/lib/common.dart` — accent `#0071FF` → `#00B4D8` (teal), dark backgrounds → near-black `#0A0C10` / `#14171E`
- **Server mode disabled**: `src/core_main.rs` — `--server`/`--service` exit with error
- **Strings**: "RustDesk" → "Oxygex"
- **Package**: renamed to `oxygex-controller` / `oxygex_controller`

### Server (`oxygex-server/`)
Stripped to a **headless receiver** — no GUI, no tray, no Flutter.

- **Headless main**: `src/main.rs` — calls `start_server(true, false)` directly
- **No Flutter**: feature removed, `cdylib` removed
- **Linux pkg-config**: enabled by default (uses system vpx/yuv/aom)
- **Package**: renamed to `oxygex-server`

## Quick start

### Server (headless receiver)

Download from [Releases](../../releases), or build:
```bash
cd oxygex-server
cargo build --release
./target/release/oxygex-server
```

### Controller (full GUI)

Download from [Releases](../../releases), or build:
```bash
cd oxygex-controller
cargo build --release
cd flutter && flutter pub get
flutter build linux --release  # or: flutter build windows --release
```

## Theme

Dark teal "Oxygex" palette:
- **Accent**: `#00B4D8` (teal/cyan)
- **Canvas**: `#0A0C10` (near-black)
- **Cards**: `#14171E` / `#1E222B`
- **Borders**: `#2D3440`
- **ID text**: `#48CAE4`

## License

GPL-3.0 (inherited from RustDesk).
