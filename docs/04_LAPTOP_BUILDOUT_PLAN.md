# SENTRY — Full Laptop Build-Out Plan (Phased)

Where you are now and everything to build toward, in phases. Buy hardware when
you're ready for each phase; the software work for each is a Claude Code task.

Detect-only throughout. Receiving/analyzing = legal. Transmitting on restricted
bands = illegal (matters for HackRF — keep it receive-only).

---

## WHERE YOU ARE NOW (Phase 0 — DONE ✅)
Working, honest, on GitHub:
- Wi-Fi network/AP detection (43 networks, real SSID/vendor/channel/signal)
- Bluetooth/BLE detection + accurate device classification
- Local network (LAN) scan — found your Ring cameras
- Honest distance (coarse, labeled approximate), no fake direction
- Resilient live feed (auto-reconnect), demo/offline clearly badged
- No fabricated data or capability

**Gap:** no radio (RF) yet, and no true direction-finding. Both are hardware.

---

## PHASE 1 — RF SPECTRUM + REAL LOCATING  (~$75)
The biggest capability jump. Buy together:
| Buy | ~$ | Unlocks |
|-----|----|---------| 
| RTL-SDR Blog V4 + antenna kit | 45 | RF receive 500kHz–1.7GHz |
| Log-periodic directional antenna (0.85–6.5GHz) | 30 | real direction-finding |

**Features this unlocks (Claude Code builds the backends):**
- Live RF spectrum + waterfall channel (real signals, AI reads the peaks)
- Detect analog wireless cameras, 433/315 MHz bugs, remotes, telemetry
- Real "walk to it" locating — point the directional antenna, signal peaks
- RF baseline/anomaly mode — capture the room's normal spectrum, flag what's NEW

**When it arrives:** plug in USB → Zadig driver (WinUSB) → in Claude Code:
"my RTL-SDR is connected, get the RF channel reading real signals and tune it."

---

## PHASE 2 — FULL-SPECTRUM TO 6 GHz  (~$150)
| Buy | ~$ | Unlocks |
|-----|----|---------| 
| HackRF One | 150 | RF receive 1 MHz – 6 GHz |

**Why:** reaches 2.4 GHz and 5.8 GHz — where modern Wi-Fi cameras, video
transmitters, and drones live. RTL-SDR can't go that high.

**Features:**
- 2.4/5.8 GHz wireless camera detection (the modern threat)
- Video-transmitter and drone-signal detection
- Wide sweep across the whole practical spectrum
- (Receive-only — it can transmit, but don't: illegal on most bands)

**When it arrives:** Zadig driver → in Claude Code: "add the HackRF as an RF
sensor covering 1MHz–6GHz, receive-only, and wire it into the spectrum channel."

---

## PHASE 3 — DEEPER WI-FI  (~$35)
| Buy | ~$ | Unlocks |
|-----|----|---------| 
| USB Wi-Fi adapter w/ monitor mode (Alfa AWUS036ACM) | 35 | see Wi-Fi client devices |

**Features:**
- Detect Wi-Fi *client devices*, not just routers/APs
- Spot hidden cameras that connect out but don't broadcast an AP
- Probe-request / deauth detection (rogue activity)

**When it arrives:** in Claude Code: "I have a monitor-mode Wi-Fi adapter — add a
sensor that captures Wi-Fi client devices and probe requests."

---

## PHASE 4 — LOCATION + LOGGING  (~$15)
| Buy | ~$ | Unlocks |
|-----|----|---------| 
| USB GPS dongle (u-blox) | 15 | location-tag detections |

**Features:**
- Timestamp + GPS-tag every detection
- Map where a signal is strongest as you walk (signal heat-mapping)
- Session history you can review later

---

## PHASE 5 — SOFTWARE-ONLY FEATURES (no hardware, build anytime)
Things Claude Code can add with what you already have:
- **Session recording / history** — save scans, compare over time, "what's new since yesterday"
- **Alerts** — notify when a NEW device or a camera-class device appears
- **Hotel/Airbnb sweep mode** — baseline a room on arrival, flag anything new
- **Export/report** — save a sweep as a PDF/CSV record
- **Camera-traffic heuristic** — flag network devices with steady camera-like upstream data
- **Better device fingerprinting** — expand the vendor/OUI and device-type database
- **Phone-friendly UI** — finish the responsive/touch version (you started this)

---

## HARDWARE THAT DOESN'T HELP (don't waste money)
- **HDMI add-ons** — HDMI outputs video; it can't bring sensor data in. Only use:
  plug into a bigger monitor. No detection value.
- **USB hubs** are fine for adding ports, but add no capability themselves.
- **"Bug detector" cheap Amazon gadgets** — redundant with what you're building.

---

## THE ONLY HARD LIMIT (honest)
Some things need the Raspberry Pi build (physical sensors on GPIO pins):
thermal camera, lens-finder (optical), NFC/RFID, EMF/magnetic, acoustic. These
can't run off a laptop's USB in this build — they're the Pi "ultimate box" step.
Everything radio/Wi-Fi/network is laptop-doable; the physical-world sensors are Pi.

---

## RECOMMENDED ORDER
1. **Now:** field-test current build; add Phase 5 software features you want
2. **Phase 1 (~$75):** RTL-SDR + directional antenna — RF + real locating
3. **Phase 2 (~$150):** HackRF — full 6 GHz, modern camera detection
4. **Phase 3 (~$35):** monitor-mode Wi-Fi — client detection
5. **Phase 4 (~$15):** GPS — location logging
6. **Later:** Raspberry Pi ultimate box for the physical sensors

Total laptop full build ≈ $275 in hardware, phased however you like.
Each phase: buy it → plug in → tell Claude Code what you connected → it builds the
backend → test → commit & push to GitHub.
