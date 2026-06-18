# 08 — Full Detection Feature Catalog (build toward total coverage)

Every detection capability SENTRY can have, across the laptop and the Pelican-case
Pi build. Organized by threat type so you can build toward full coverage. Each
feature notes what it catches, what hardware it needs, and whether it's
software-only (buildable now) or hardware-gated.

> Detect-only. Receiving/analyzing = legal. Transmitting on restricted bands =
> illegal. Every feature here is receive/sense only.

Legend: 💻 = laptop · 📦 = Pi case · 🆓 = software-only (no new hardware) ·
🔌 = needs hardware

---

## THREAT 1 — HIDDEN CAMERAS

### Wi-Fi / networked cameras
- 💻🆓 **Network camera scan** — ARP-scan your network, flag camera-vendor MACs
  (Hikvision, Dahua, Reolink, Amcrest, Wyze, Ring, Nest, Arlo) — *built*
- 💻🆓 **Open-port fingerprinting** — flag RTSP (554), ONVIF, HTTP (80/8080) =
  camera tells — *built/expandable*
- 💻🆓 **Camera traffic heuristic** — flag devices with steady upstream data
  (streaming-like) — *to build*
- 💻🔌 **Wi-Fi client detection** (monitor-mode adapter) — catch cameras that
  connect out but don't broadcast an AP

### Wireless (non-Wi-Fi) cameras
- 💻🔌 **2.4 GHz camera detection** (HackRF) — common wireless cams
- 💻🔌 **5.8 GHz analog video** (HackRF) — analog FPV/spy cams
- 💻🔌 **900 MHz / 1.2 GHz video** (RTL-SDR/HackRF) — older analog cams

### Offline / radio-silent cameras (the hard ones)
- 📦🔌 **Lens-finder** (Pi camera + IR ring) — catches any lens by retroreflective
  glint, even powered off
- 📦🔌 **Thermal detection** (MLX90640) — heat of a powered camera, even if its
  radio is silent

---

## THREAT 2 — TRACKERS (things following you)

- 💻🆓 **AirTag / Find My detection** (Bluetooth) — *built (now honest, no false
  "following")*
- 💻🆓 **Tile / Chipolo / Samsung SmartTag detection** — expand BLE signatures
- 💻🆓 **"Traveling with you" logic** — only flag a tracker that persists across
  changing locations/signal over time (true following) — *built, conservative*
- 💻🆓 **Cross-session tracker memory** — remember a tag seen across different days/
  places — *to build*
- 💻🔌 **GPS-correlated following** (USB GPS) — confirm a tag is moving WITH you,
  not just present
- 📦🔌 **Magnetic/EMF probe** — find a magnet-mounted tracker on a vehicle/bag

---

## THREAT 3 — LISTENING DEVICES / BUGS

- 💻🔌 **RF bug detection** (RTL-SDR) — 433/315/868/915 MHz transmitters,
  the classic bug bands
- 💻🔌 **GSM/cellular bug presence** (HackRF) — detect a bug's uplink burst
  (presence/behavior only, never content — legal line)
- 💻🆓 **Bluetooth Classic scan** — older audio bugs/headsets not on BLE — *to build*
- 📦🔌 **Acoustic/ultrasonic detection** — ultrasonic beacons, some active mics
- 📦🔌 **EMF probe** — wired/hardwired bugs and hidden powered electronics
- 📦🔌 **Thermal** — heat of a powered recorder, even radio-silent

---

## THREAT 4 — ROGUE NETWORKS / INTERCEPTION

- 💻🆓 **Evil-twin AP detection** — duplicate-SSID networks (MITM lures) — *built*
- 💻🔌 **Deauth / probe-request detection** (monitor-mode adapter) — Wi-Fi attacks
- 💻🔌 **IMSI-catcher / fake-tower hints** (HackRF) — suspicious cell behavior
  (presence/anomaly only)
- 💻🔌 **GPS jamming/spoofing** (USB GPS or Pi GNSS) — detect GPS interference

---

## THREAT 5 — SKIMMERS / DATA THEFT

- 📦🔌 **NFC/RFID reader detection** (PN532) — covert card readers, skimmers
- 💻🆓 **Network anomaly detection** — unexpected devices on your network — *partial*

---

## CROSS-CUTTING FEATURES (make it a real instrument)

### Detection intelligence
- 💻🆓 **Baseline / background subtraction** — capture the normal environment, flag
  only what's NEW (the #1 pro feature)
- 💻🆓 **Sensitivity threshold control** — tune out clutter
- 💻🆓 **Device classification** — what each device IS (phone/TV/bulb/camera) —
  *built, expandable*
- 💻🆓 **Confidence scoring** — honest "how sure" on each detection — *built*

### Locating
- 💻🆓 **Signal-strength proximity** (closer/farther) — *built, honest*
- 💻🔌 **Directional finding** (directional antenna + SDR) — real "walk to it"
- 📦🔌 **Multi-antenna RF array** — true bearing without sweeping

### Workflow
- 💻🆓 **Sweep mode** — baseline a room on arrival, flag new (hotel/Airbnb)
- 💻🆓 **Session recording + history** — save sweeps, compare over time
- 💻🆓 **Alerts** — notify on new/camera-class/tracker detections
- 💻🆓 **Export/report** — save a sweep as PDF/CSV
- 💻🆓 **Location-tagged logging** (with GPS) — heat-map signal as you move

### Presentation
- 💻🆓 **Professional bar-graph signal meter** + optional audio tone
- 💻🆓 **Live spectrum waterfall** (with SDR)
- 💻🆓 **Phone-friendly / touch UI**

---

## NOT REAL — DON'T CHASE
- HDMI-based detection (HDMI is output only — no sensor data in)
- "Through-wall camera detection" gadgets
- Cheap Amazon "bug detector" wands (redundant with this)
- X-ray / see-through-wall imaging (not realistic or legal DIY)
- Decoding others' private communications (illegal — presence/behavior only)

---

## SUGGESTED BUILD ORDER TOWARD FULL COVERAGE
1. **Now (🆓 software):** baseline/sweep mode, new-device alerts, session history,
   camera-traffic heuristic, Bluetooth Classic, expanded tracker signatures
2. **RTL-SDR (~$45):** RF bugs, analog cameras, spectrum waterfall
3. **Directional antenna (~$30):** real direction-finding
4. **HackRF (~$150):** 2.4/5.8 GHz cameras, drones, cellular-presence hints
5. **Monitor-mode Wi-Fi (~$35):** client detection, deauth/probe
6. **USB GPS (~$15):** location logging, GPS-jam detection
7. **Pi case build:** thermal, lens-finder, NFC, EMF, acoustic — the physical
   sensors that catch silent/offline devices

Full coverage = laptop (all radio/network/Wi-Fi/BT) + Pi case (all physical
sensors). The two together cover every threat class above.

Each feature: build with Claude Code, test against real data, commit & push.
