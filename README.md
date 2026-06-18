# SENTRY — Personal Counter-Surveillance Station

A multi-sensor counter-surveillance station you can run on a Windows laptop (or a
Raspberry Pi in a Pelican case). It scans the radio, Wi-Fi, and Bluetooth
environment around you, identifies devices that may be watching or tracking you,
and helps you locate them — with a live signal view and AI-style analysis for
each detection.

**Built as a learning + demonstration project.** It detects the common, real
threats people actually face (Wi-Fi cameras, AirTag-class trackers, rogue
networks). It is **not** a guarantee against determined, professional
surveillance — see *Honest limits* below.

> Detect-only. SENTRY never jams, replays, clones, or attacks any device. It
> finds, identifies, and locates — nothing more.

---

## 📚 Full build documentation → start at [`docs/00_START_HERE.md`](docs/00_START_HERE.md)

The `docs/` folder is a complete, staged build journey — from running it free on a
laptop all the way to a portable Raspberry Pi unit in a Pelican case. New here?
Open **[`docs/00_START_HERE.md`](docs/00_START_HERE.md)** — it's the entry point and
index for everything below.

The journey, in order:

1. **Run it on a laptop** (free) — Wi-Fi + Bluetooth + network detection today;
   add a ~$45 RTL-SDR dongle for live RF. → `01_QUICKSTART`, `02_LAPTOP_CLAUDECODE_GITHUB`, `03_LAPTOP_FULL_RF_WIFI_BT`
2. **Build out the laptop** — phased USB add-ons (SDR, directional antenna,
   monitor-mode Wi-Fi, GPS) and every feature to grow toward. → `04_LAPTOP_BUILDOUT_PLAN`, `08_FULL_FEATURE_CATALOG`
3. **Step up to the Pi "ultimate box"** — the physical sensors a laptop can't do
   (thermal, lens-finder, NFC, EMF, acoustic), full wiring diagrams, the Pelican
   case build. → `05_PI_ULTIMATE_BOX`, `11_PHASES_6_7_8`
4. **Reference** — parts/prices, shopping lists, roadmap, and moving gear from
   laptop to Pi. → `06_HARDWARE`, `09_SHOPPING_LIST_PI_BOX`, `10_SHOPPING_FROM_SCRATCH`, `07_ROADMAP`, `12_MOVING_GEAR_LAPTOP_TO_PI`

Honest throughout: the laptop phases (RF / Wi-Fi / Bluetooth / network) are fully
laptop-doable; the physical sensors (thermal, lens, NFC, EMF) genuinely need the
Pi's GPIO pins and are clearly marked as such.

---

## Quick start (Windows)

1. **Install Python 3** from https://python.org — during install, tick
   **"Add Python to PATH."**
2. **Clone or download this repo:**
   ```
   git clone https://github.com/YOUR_USERNAME/sentry.git
   cd sentry
   ```
   (Or download the ZIP from GitHub and extract it.)
3. **Double-click `START_SENTRY.bat`.**
   It sets up everything on first run and opens the station in your browser.

That's it. To stop, close the black window.

### Prefer the command line?
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m sentry_backend.server
```
Then open http://localhost:8000

---

## What works on your laptop right now

| Sensor | Needs | Works on a laptop? |
|--------|-------|--------------------|
| **Wi-Fi** (finds IP cameras, evil-twins) | built-in Wi-Fi | ✅ yes, no extra hardware |
| **Bluetooth** (finds AirTags & BLE trackers/bugs) | built-in Bluetooth | ✅ yes, no extra hardware |
| **RF spectrum** (any transmitter, analog video) | **RTL-SDR USB dongle (~$45)** | ➕ plug it in to go live |

With **zero extra hardware**, the Wi-Fi and Bluetooth sensors run for real.
Add a [RTL-SDR Blog V4](https://www.rtl-sdr.com/) USB dongle and the RF channel
goes live too — that's the "antenna through your laptop."

Any sensor whose hardware isn't present simply shows **offline** — the rest keep
working. If no sensors are available at all, the interface runs in **demo mode**
with realistic sample data, so it always works for showing people.

---

## How it works

```
  your laptop's Wi-Fi / Bluetooth  (+ optional RTL-SDR)
        -> sentry_backend  (real Python sensors: scan, identify, locate)
        -> WebSocket :8765  (live detections)
        -> the browser UI  (Scan / Tools / Channels, live signal + AI readout)
```

- **`sentry_backend/`** — the real detection code. Each sensor degrades
  gracefully when its hardware is absent.
- **`ui/index.html`** — the full interface (self-contained; also works standalone
  in demo mode if you just open it).
- **`docs/`** — the hardware bill of materials and the staged build roadmap.

---

## Run the interface only (no Python)

Just open `ui/index.html` in your browser. It runs in demo mode with sample data
— perfect for showing the design. For **real detection**, run the backend
(above) so the UI gets a live feed.

### Host the demo on GitHub Pages
Enable Pages on this repo (Settings → Pages → from `main`, `/ui` or root). You'll
get a public URL anyone can open. Note: a public Pages site can only show **demo
mode** — browsers block a public page from reaching the backend on your laptop.
Real detection always runs locally.

---

## Honest limits (read this)

- **Silent devices:** a camera or recorder saving to a local card with its radio
  **off** transmits nothing — Wi-Fi/BT/RF can't see it. Those are caught only by
  physical search, a lens-finder, or thermal (see the roadmap's later stages).
- **Cellular/IMSI** detection is the weakest channel on cheap hardware; treat any
  cellular hint as "investigate," not proof.
- **Not a professional sweep.** This is a capable hobby/learning instrument. If
  you believe you're under serious, targeted surveillance, get a professional
  TSCM sweep and, as appropriate, contact authorities.
- **It will never be perfectly bug-free** — real instruments are tuned over time.
  "Working" means it reliably catches the common stuff and is honest about the
  rest.

See **`docs/ROADMAP.md`** for the staged build (what's done, what's next) and
**`docs/HARDWARE.md`** for the full under-$400 parts list for the Pelican-case
Raspberry Pi build.

---

## Legal

Operate within your local laws. SENTRY only **receives and analyzes** signals
that devices openly broadcast, and helps you find devices in your own space. It
does not decode private content, and it does not transmit to interfere with any
device.
