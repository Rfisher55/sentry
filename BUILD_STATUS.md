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

## PHASE B — BUILD & VERIFY (real data, committed locally)

| Item | Result |
|---|---|
| **Acoustic / Ultrasonic detector** (NEW) | **Built.** Laptop mic + Web Audio FFT, watches 17–22 kHz for tracking-beacon tones, flags a sustained tone as a possible beacon. Detect-only; mic released on close. Verified in headless Edge (fake mic) — flagged a sustained 17.2 kHz tone, mic released, no JS errors. Acoustic tool now **LIVE**. |
| Live Wi-Fi/BLE signal traces | **Verified live** — real BLE RSSI jitters across samples (e.g. −75 → −83 → −76); per-device sparklines move. Not flat. |
| RF sweep / scanner stepping | **Verified stepping** on a clean instance: auto-seek dwells on active stations then advances — 88.1 → 88.3 → 88.5 → 88.7 → 88.9 with real signal strengths. (An earlier "parked at 88.1" reading was a STALE server instance, not a code bug — a clean restart fixed it. Lesson: run only one instance.) |
| MHz input + GO + WFM/AM/NFM modes | Built & verified earlier this session — really tune + change demodulation. |
| ISM/key-fob detection 315/433/868/915 | **Verified** — all four bands present in the detection table; 315/433 flag intermittent OOK/FSK bursts. |
| Unified explorer / Overview | Live fusion, source-tagged, moving signals. |
| Map + distance controls (range, filter, room-map) | Built this session; distance-only, honestly labeled. |
| Drone detection (Wi-Fi-linked + names) | Built this session (in Tools). |
| Network detection (LAN + nmap + tshark) | Live; nmap/tshark/Npcap installed. |

## PHASE C — HONESTY PASS

- Each hardware/install-gated tool now states its **specific** requirement (Requires
  HackRF / directional antenna / PN532 / thermal module / Pi GPIO / install nikto…),
  not a generic "coming soon."
- **Fixed an oversell:** Direction Finder previously read "LIVE" because the RF
  sensor is online — but true bearing needs a directional antenna. It now reads
  **NEEDS ANTENNA** (distance-only still works on the Map).
- Earlier today (same project): RF "detected but in use" vs "no dongle" message;
  tool/channel cards now refresh the moment a sensor comes online (RF stops showing
  "needs a dongle" once it's live).

## SUMMARY (read me first)

**What I built/fixed and verified tonight (all committed LOCALLY — nothing pushed):**
1. NEW **Acoustic/Ultrasonic detector** — real, uses your laptop mic, no extra hardware.
2. **Honesty pass** — every not-yet tool now says exactly what hardware/install it
   needs; Direction Finder no longer oversells "live."
3. **Verified the core mission works on real data:** live Wi-Fi/BLE traces, RF sweep
   actually stepping, ISM 315/433/868/915 detection, unified fusion, map + distance
   controls, drone detection, network detection.

**Now working with your current kit (NESDR Mini + Wi-Fi/BT + Windows):** RF spectrum/
sweep/scanner/listen, RF baseline & anomaly, ISM fob detection, Wi-Fi & BLE hunters,
network inspector (nmap + live capture), drones, map/distance, alerts/follow-test/
evidence, and now acoustic/ultrasonic.

**Still needs hardware you don't have:** Direction-finding bearing (directional
antenna/KrakenSDR), cellular/IMSI + 2.4/5.8 GHz RF + analog-video/drone-video
(HackRF), NFC (PN532), IR, EMF, optical lens, thermal, GNSS, power-line, NLJD, GPIO
(mostly the Pi sensors). All clearly labeled in the UI.

**Needs a software install:** nikto (optional, deeper web audit) — everything else
(nmap, Wireshark/tshark, Npcap) is already installed.

**Recommend (your call, nothing removed):** group the 11 hardware-only "NOT BUILT YET"
tiles under a collapsible "Future sensors (need hardware)" section so the working
tools stand out; the most niche are GPIO Lab, Power-line, NLJD.

**Nothing has been pushed to GitHub.** Local commits are ready; tell me when to push.

---

## SOFTWARE-ONLY OPPORTUNITY RE-AUDIT (current kit — NESDR Mini + Wi-Fi/BT + installed tools)

Found by walking the whole app. Everything here is buildable with the current kit
(no HackRF / antenna / Pi sensors). Items needing absent hardware are NOT listed
(they stay honestly labeled in the UI). Build order = top to bottom.

| # | Opportunity | Why it's software-only | Plan |
|---|---|---|---|
| 1 | **Deeper BLE tracker detection** — today only Apple Find My is flagged. Add Tile, Samsung Galaxy SmartTag, Chipolo, Pebblebee (service-UUID + name signatures). | Pure advert parsing of data devices already broadcast | BUILD |
| 2 | **More camera / IoT vendor IDs** — extend the OUI/vendor + name classifier (Reolink, Amcrest, Eufy, Blink, Lorex, Annke, Tapo, SwitchBot…) for richer Wi-Fi/LAN device ID. | Curated lookup tables | BUILD |
| 3 | **Acoustic detector enrichment** — adjustable sensitivity, peak-hold trace, and an event log of detected ultrasonic tones. | Browser Web Audio only | BUILD |
| 4 | **Hotel / Airbnb sweep mode** — a guided workflow: capture an arrival baseline, then watch for NEW devices/cameras and review them. Orchestrates existing detection. | UX over existing baseline + new-device data | BUILD |
| 5 | Cross-channel "what's new since baseline" already exists via the CAPTURE BASELINE + NEW/CHANGED filter; #4 surfaces it better. | — | Folded into #4 |
| 6 | Network depth (DNS log, phone-home map, top-talkers, new-port change-tracking) already built with tshark/nmap. | — | Already done |
| 7 | UX/theme consistency pass on any new UI. | — | As built |

**Explicitly NOT building (needs hardware — stays labeled):** direction-finding
bearing (antenna/KrakenSDR), cellular/IMSI + 2.4/5.8 GHz RF (HackRF), NFC (PN532),
IR, EMF, optical lens, thermal, GNSS, power-line, NLJD, GPIO.

---

## SOFTWARE-ONLY BUILD SESSION 2 — RESULTS (committed locally, NOT pushed)

| # | Built | Verified |
|---|---|---|
| 1 | **Non-Apple BLE tracker detection** — Tile, Samsung Galaxy SmartTag, Chipolo, Pebblebee (svc-UUID + name). Same honest "can't confirm following from a stationary scan" handling as Apple. | Tile/Samsung/Chipolo/Pebblebee → tracker; "Reptile"/"Versatile"/"Bose" NOT flagged (no false positives). |
| 2 | **Many more camera/IoT brands** in the classifier — Reolink, Eufy, Blink, TP-Link Tapo, Ezviz, Lorex, Annke, Amcrest, Hikvision, Dahua, Foscam, Arlo, Nanit + SwitchBot/Shelly/Sonoff/LIFX/Kasa/SmartThings/Meross. A name/SSID that resolves to a camera type now sets is_camera. Curated name/hostname strings only — no fabricated OUIs. | Existing suite still 16/16; Reolink/EufyCam/Tapo/Ezviz flagged as cameras across name/SSID/hostname; Shelly/SwitchBot/MacBook NOT cameras. |
| 3 | **Acoustic detector enrichment** — sensitivity slider (8–30 dB), peak-hold trace (+RESET), timestamped detected-tone log. | Fake-mic: slider set threshold, peak-hold built, a sustained 17.2 kHz tone logged with timestamp/freq/dB, mic released on close. |
| 4 | **Hotel/Airbnb sweep mode** (Alerts tab) — capture arrival baseline, flag anything NEW since arrival (watchers in red, one-tap evidence log), + physical-search checklist for offline cameras. | START captured a 100-device baseline; an injected camera flagged "1 new since arrival (1 watcher)"; STOP resets. |

**Honesty confirmed:** nothing requiring absent hardware was built or faked. The
hardware-only tools stay in the collapsed "Future sensors (need hardware)" group
with their specific requirement (HackRF / antenna / PN532 / thermal / Pi…). No
fabricated OUIs were added (camera-brand detection uses the device's own advertised
name/hostname, which is real data it broadcasts).

**Status:** 6 commits from this session are LOCAL only (4 builds + 2 audit/summary).
Combined with the prior overnight batch, nothing is on GitHub since you last pushed.
**Waiting for your OK to push** (push is re-blocked until you say so).
