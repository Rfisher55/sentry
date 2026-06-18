# 10 — Shopping From Scratch (phased plan, you have nothing)

The complete, beginner-friendly buying plan starting from zero. Buy in phases —
each phase works on its own, so you learn and confirm before spending more. Prices
are approximate (2026); check the links for current.

> The smart path: start with a ~$50 SDR on a laptop you already have, learn the
> whole system, THEN build the dedicated box. Don't buy ~$470 of gear before you
> know you like it.

---

## PHASE 0 — FREE (works today on any laptop)
SENTRY runs on a laptop with built-in Wi-Fi + Bluetooth. No purchase needed for:
- Wi-Fi network/camera detection
- Bluetooth/AirTag/tracker detection
- Local-network scan (finds Wi-Fi cameras like Ring/Nest by vendor + open ports)

**Cost: $0.** Get the software running first (see 01_QUICKSTART.md).

---

## PHASE 1 — ADD RADIO (~$50) ← start spending here
Unlocks the RF spectrum on your laptop: analog wireless cameras, 433/315 MHz
bugs/remotes, two-way radio activity, the live waterfall.

| # | Item | ~$ | Link |
|---|------|----|----|
| 1 | RTL-SDR (Nooelec NESDR Mini, or RTL-SDR Blog V3) | 45 | Nooelec: https://www.amazon.com/dp/B009U7WZCA |
| 2 | MCX-to-SMA adapter (if Nooelec) | 7 | https://www.amazon.com/dp/B07VML6KVR |

**Why start here:** cheapest meaningful upgrade, plugs into a laptop you already
have, teaches you the whole RF side. Install driver via Zadig (WinUSB), then tell
Claude Code "my RTL-SDR is connected."

**Phase 1 total: ~$52**

---

## PHASE 2 — ADD LOCATING (~$30)
Real "walk to it" direction-finding (the thing signal-strength alone can't do).

| # | Item | ~$ | Link |
|---|------|----|----|
| 3 | Log-periodic directional antenna (0.85–6.5 GHz, SMA) | 30 | Search Amazon: "log periodic directional antenna 850MHz-6.5GHz SMA" |

**Phase 2 total: ~$30**

---

## PHASE 3 — THE BOX: core platform (~$205)
Build the dedicated Raspberry Pi unit (runs everything the laptop does, always-on,
portable). Buy from authorized resellers (PiShop, CanaKit, Adafruit).

| # | Item | ~$ | Link |
|---|------|----|----|
| 4 | Raspberry Pi 5 (8GB) | 95 | https://www.pishop.us/product/raspberry-pi-5-8gb/ |
| 5 | Active Cooler | 5 | https://www.raspberrypi.com/products/active-cooler/ |
| 6 | Official 27W USB-C Power Supply | 12 | https://www.raspberrypi.com/products/27w-power-supply/ |
| 7 | 64GB microSD (A2) | 12 | https://www.amazon.com/dp/B09X7DNF3X |
| 8 | Official 7" Touch Display 2 | 60 | https://www.raspberrypi.com/products/raspberry-pi-touch-display-2/ |
| 9 | ⚠️ Pi 5 Display Cable (22-pin) — DON'T SKIP | 1 | https://www.raspberrypi.com/products/display-cable/ |
| 10 | USB microSD card reader (skip if laptop has one) | 8 | https://www.amazon.com/dp/B0779V61XB |

**⚠️ #9 is the most-missed part:** the screen's included cable does NOT fit the
Pi 5. Without this $1 cable the display won't connect.

**Phase 3 total: ~$205**

---

## PHASE 4 — PHYSICAL SENSORS (~$106) — what only the box can do
These catch what radio can't, including silent/offline devices. Add one at a time.

| # | Item | ~$ | Link |
|---|------|----|----|
| 11 | MLX90640 Thermal Camera (I2C, with headers) | 40 | https://www.adafruit.com/product/4407 |
| 12 | Pi Camera Module 3 | 25 | https://www.raspberrypi.com/products/camera-module-3/ |
| 13 | IR LED ring light (850nm) | 8 | Search Amazon: "IR LED ring 850nm" |
| 14 | PN532 NFC/RFID module (I2C mode) | 10 | https://www.adafruit.com/product/364 |
| 15 | QMC5883L magnetometer (EMF/magnetic) | 8 | Search Amazon: "QMC5883L module" |
| 16 | USB ultrasonic-capable microphone | 15 | Search Amazon: "ultrasonic USB microphone" |

**Phase 4 total: ~$106**

---

## PHASE 5 — ENCLOSURE & POWER (~$77) — make it a field unit
| # | Item | ~$ | Link |
|---|------|----|----|
| 17 | Pelican-style case + pluck foam (~13×10") | 40 | Apache 4800 (Harbor Freight) or Pelican 1450 |
| 18 | 18650 UPS HAT + 2 cells (stacking header!) | 30 | Search Amazon: "Raspberry Pi 5 18650 UPS HAT stacking" |
| 19 | Female-to-female jumper wires (40-pack) | 7 | Search Amazon: "female to female dupont jumper 40" |

**Phase 5 total: ~$77**

---

## OPTIONAL ADD-ONS (anytime)
| Item | ~$ | Adds |
|------|----|----|
| u-blox USB GNSS module | 15 | GPS jam/spoof detection + location logging |
| HackRF One | 150 | 2.4/5.8 GHz (modern Wi-Fi cameras, drones) — RX only |
| Alfa AWUS036ACM USB Wi-Fi | 35 | Wi-Fi client-device detection (monitor mode) |
| SMA bulkhead connectors | 10 | Clean antenna mounting through case wall |

---

## TOOLS (basic)
- Small Phillips screwdriver — $5
- Hobby/craft knife (foam + case holes) — $5
- (Only if a module lacks headers) soldering iron — $20

---

## RUNNING TOTALS
| Through phase | Running cost | You can do |
|---------------|--------------|------------|
| Phase 0 | $0 | Wi-Fi + BT + network detection on a laptop |
| + Phase 1 | ~$52 | + RF spectrum (cameras, bugs, radios) |
| + Phase 2 | ~$82 | + real direction-finding |
| + Phase 3 | ~$287 | dedicated always-on Pi box |
| + Phase 4 | ~$393 | + thermal, lens, NFC, EMF, acoustic |
| + Phase 5 | ~$470 | full portable field unit in a case |

---

## RECOMMENDED PATH
1. **Phase 0 now** — get the software running free on your laptop.
2. **Phase 1 (~$52)** — add the SDR, learn the RF side on your laptop.
3. **Decide:** if you love it, move to the box (Phase 3+). If not, you've spent $52.
4. **Phases 3→4→5** — build the box, add sensors one at a time, then the case.

Each phase: buy it → plug in / wire it → tell Claude Code what you added → it builds
that part → test against real data → commit & push to GitHub.

## CRITICAL REMINDERS
- **Pi 5 display cable (#9)** — the #1 missed part; the screen's cable won't fit.
- **Buy the Pi from authorized resellers** — counterfeits exist.
- **"With headers" sensor modules** — no soldering.
- **UPS HAT with stacking header** — so sensors still reach the GPIO pins.
- Prices rose late 2025 (memory costs) — verify current at the links.
