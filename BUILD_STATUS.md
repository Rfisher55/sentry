# SENTRY — Build Status & Audit

> Overnight autonomous build session. Everything below is committed **locally only** —
> nothing has been pushed to GitHub. Read this in the morning, then we decide what to push.
>
> **Your kit:** Nooelec NESDR Mini (RTL2832U/R820T, ~25 MHz–1.7 GHz, receive-only) ·
> built-in Wi-Fi · built-in Bluetooth · Windows laptop.
> **Installed this project:** nmap, Wireshark/tshark, Npcap.

---

## PHASE A — AUDIT (what works, what doesn't, what's buildable)

Live sensor check at audit time: **RF online** (R820T, sweep = 719 spectrum points) ·
**Wi-Fi online** · **Bluetooth online** · **Network online** (10 LAN devices). 121 fused
devices; real BLE RSSI is live/jittery (e.g. −75 → −83 → −76 across samples). Demo sample
devices remain as illustrative entries when a real one of that type isn't present (clearly
the same data the public demo shows).

### ✅ WORKING NOW (real, verified)
| Feature | Where | Notes |
|---|---|---|
| Unified "what's around me" fusion | Overview | RF + Wi-Fi + BLE + network, source-tagged, live RSSI traces |
| RF spectrum sweep | Listening / Overview | Real sweep, 719 points, steps the bands (not parked) |
| RF tuned listen + MHz input + GO | Listening | Tunes any freq in range; verified FM audio earlier |
| WFM / AM / NFM mode buttons | Listening | Really change demodulation (verified live) |
| Scanner: sweep / squelch / dwell / SKIP / activity log | Listening | Auto-seek dwells then resumes; HOLD/PREV/NEXT work |
| RF baseline & anomaly | Listening / Alerts | Capture baseline, flag NEW transmitters (≥8 dB) |
| RF signal characterization | Listening | Bandwidth / strength / continuity / modulation guess — content-free |
| ISM key-fob detection 315 / 433 MHz | RF sweep | Real band defs; catches OOK/FSK bursts |
| Wi-Fi Hunter | Sensors & Toolkit / Overview | netsh scan, camera OUIs, evil-twin/hidden SSID |
| BLE Hunter | Overview / Alerts | AirTag/Find-My + tracker classification |
| Network Inspector | Network | LAN scan, port/service scan, nmap, vuln/CVE awareness, web check, ARP/MITM, IDS, live traffic capture (tshark) |
| Drone detection | Drones (Tools) | Wi-Fi-linked + named-device signatures over Wi-Fi/BT |
| Map: distance rings + range control + distance filter + room-map shell | Map (Overview) | Distance-only, honestly labeled approximate; no fake bearing |
| Alerts: ranked watchers + follow-test + evidence log (CSV/print) | Alerts | Detect-only counter-surveillance |

### 🔨 BUILDABLE NOW (current kit — built/attempted this session, see Phase B)
| Item | Why buildable | Status |
|---|---|---|
| Acoustic / ultrasonic beacon detection | Laptop mic + Web Audio FFT reaches ~20–22 kHz — enough for ~18–20 kHz cross-device tracking beacons + ambient mic level | **BUILT this session (Phase B)** |
| 868 / 915 MHz ISM band presets | In the SDR's range; sweep already covers them, just needed explicit scanner presets | Reviewed in Phase B |
| Honest status when a sensor is busy vs absent | Already shipped earlier today (RF "detected but in use") | Done |
| Tool/channel cards refresh when a sensor comes online | Shipped earlier today | Done |

### 🛰 NEEDS HARDWARE I DON'T HAVE
| Tool | Needs | Note |
|---|---|---|
| Direction Finder (bearing) | Directional antenna / KrakenSDR | SENTRY shows distance-only until then — honest |
| Cellular / IMSI-catcher | HackRF or cellular survey modem | NESDR can't do a real tower survey; weakest channel |
| 2.4/5.8 GHz RF (Wi-Fi-cam RF, analog video, drone video) | HackRF (above 1.7 GHz) | Wi-Fi/BLE sensors cover 2.4 GHz *devices*; RF-level needs HackRF |
| NFC / RFID reader | PN532 module | Pi/USB add-on |
| Infrared Explorer | IR photodiode / IR camera | Phone-cam trick noted in UI |
| EMF / Magnetic probe | Magnetometer + coil probe | Pi sensor |
| Optical Lens Finder | IR LED ring + camera | Webcam-only version is unreliable |
| Thermal Inspection | Thermal camera (MLX90640/Lepton) | Pi sensor |
| GNSS Integrity | GNSS receiver | Pi/USB add-on |
| Mains / Power-line | Isolated power-line coupler | Bench/Pi |
| Offline-Electronics (NLJD) | Dedicated NLJD hardware | Specialist gear |
| GPIO Hardware Lab | Raspberry Pi GPIO | Pi-only |

### 💿 NEEDS A SOFTWARE INSTALL
| Tool | Install | Status |
|---|---|---|
| nmap scanning | nmap | ✅ installed |
| Live packet capture | Wireshark/tshark + Npcap | ✅ installed |
| Deeper web-server audit | nikto (needs Perl) | ⛔ not installed — optional; built-in nikto-lite covers basics |

### 🗑 RECOMMEND REMOVING / SIMPLIFYING (your call — nothing deleted)
- The **Sensors & Toolkit** catalog lists 12 Pi/hardware-only "NOT BUILT YET" tiles
  (NFC, IR, acoustic*, EMF, lens, thermal, GNSS, power, NLJD, GPIO, cellular/IMSI, DF).
  They're honestly badged, but they add length. **Recommendation:** group them under a
  collapsible "Future sensors (need hardware)" section so the working tools stand out.
  (*acoustic now moves to working — see Phase B.)
- **GPIO Hardware Lab**, **Mains/Power-line**, **NLJD** are the most niche/Pi-bench items —
  candidates to hide behind that roadmap toggle first.
- No truly redundant/duplicate features found after the earlier counter-surveillance reorg.

---
