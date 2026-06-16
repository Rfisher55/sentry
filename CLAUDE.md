# CLAUDE.md — SENTRY project brief

> This file tells Claude Code what this project is and how to work on it.
> When you open this folder in Claude Code, read this first.

## What SENTRY is
A personal counter-surveillance station. It scans the radio / Wi-Fi / Bluetooth
environment, identifies devices that may be watching or tracking the user, and
helps locate them — with a live signal view and AI-style analysis per detection.
Runs on a Windows laptop now; designed to also run on a Raspberry Pi in a
Pelican case. Built as a **learning + demonstration** project.

## Hard rules (do not break)
- **Detect-only.** SENTRY receives and analyzes signals devices openly broadcast,
  and helps find devices in the user's own space. It NEVER jams, replays, clones,
  emulates, or attacks any device, and never decodes private/encrypted content.
- **Be honest about limits.** Surface coverage gaps. A silent device (recording to
  local storage, radio off) emits nothing and can't be found by RF/Wi-Fi/BT —
  say so. Don't oversell; this is not a guarantee against professional surveillance.
- **Graceful degradation.** Any sensor whose hardware is absent reports offline and
  the rest keep working. Never let one sensor crash the system.
- **No fabricated capability.** If something isn't built/real yet, say so plainly.

## Project structure
```
START_SENTRY.bat        one-click Windows launcher (venv + deps + run + open browser)
requirements.txt        Python deps (websockets, numpy; pyrtlsdr/bleak optional)
sentry_backend/
  server.py             runs sensors on a loop, fuses, serves UI (http :8000) + WS (:8765)
  sensor.py             Sensor base class + Detection dataclass (graceful degradation)
  sensors/
    rf.py               RTL-SDR spectrum sweep -> peak detection by band
    wifi.py             Wi-Fi scan (Windows netsh / Linux nmcli) -> camera OUIs, evil-twin
    bluetooth.py        BLE scan (bleak) -> AirTag/Find My, following detection
ui/index.html           the full interface (Scan / Tools / Channels, live signal + AI readout)
docs/
  HARDWARE.md           under-$400 Raspberry Pi + Pelican parts list
  ROADMAP.md            staged build: what's done, what's next
```

## How to run
- One-click: double-click `START_SENTRY.bat`
- CLI: `python -m venv .venv` → `.venv\Scripts\activate` →
  `pip install -r requirements.txt` → `python -m sentry_backend.server`
- Then open http://localhost:8000

## What works where
- **Wi-Fi + Bluetooth**: work on the laptop with built-in hardware (no extra USB).
- **RF spectrum**: needs an RTL-SDR USB dongle (~$45). Plug-and-play — the backend
  re-detects hardware each scan loop, so plugging it in mid-session lights up RF.
- **No hardware at all**: UI runs in demo mode with realistic sample data.

## Current state (honest)
- Interface: complete and audited (all tabs, 18 tools, 12 channels, live signal,
  per-device signal, locate). Runs on simulated data when no sensors are live.
- Backend: real detection code for RF / Wi-Fi / BLE, compiles and runs, degrades
  gracefully. The hard remaining work is noise-vs-signal tuning against real
  hardware (see ROADMAP.md, Stages 2–3).

## Good next tasks (when asked)
- Tune RF peak thresholds once a real RTL-SDR is connected (rf.py).
- Add more camera/IoT OUI prefixes (wifi.py CAMERA_OUIS / IOT_OUIS).
- Wire live sensor status into the Channels tab visuals.
- Stage 4+ sensors: optical (lens), thermal, NFC, acoustic, EMF, GNSS.

## Working style the user likes
- Honest about what's real vs. simulated; no overselling.
- Verify changes actually run (compile + a quick run) before claiming done.
- Check the rendered UI for stray characters, not just that code parses.
- Small, confirmed steps over big risky rewrites.
