# SENTRY — Hardware Build (under $400)

A buildable, professional-grade personal counter-surveillance station on a
Raspberry Pi in a Pelican-style case. Every part below is real, available, and
priced from June 2026 sourcing. The goal: a box you open, power on, and it scans
the RF, Wi-Fi, Bluetooth, cellular, optical, thermal, and acoustic environment
around you, identifies what it finds, and helps you locate it.

Everything here is **receive / detect / analyze** only — nothing transmits to
jam, replay, or defeat another device.

---

## Core platform (~$215)

| Part | Why | ~Price | Source |
|------|-----|--------|--------|
| **Raspberry Pi 5 (8GB)** | The brain — runs the engine + UI, holds RF buffers | $130 | PiShop / CanaKit |
| **Active Cooler** | The SDR + scanning pegs a core; prevents throttling | $5 | PiShop |
| **27W USB-C PSU** | Stable power under load | $12 | PiShop |
| **64GB A2 microSD** | OS + scan logs | $12 | SanDisk/Samsung |
| **7" touchscreen** (official Pi Touch Display 2 or HDMI) | The screen in the lid; touch = glove-friendly | $60 | raspberrypi.com |

## The radio backbone (~$55)

| Part | Why | ~Price | Source |
|------|-----|--------|--------|
| **RTL-SDR Blog V4** | Wideband receiver, ~500 kHz–1.7 GHz: the RF spectrum, analog video, 433/868/915 MHz, pagers, much of cellular survey | $45 | rtl-sdr.com |
| **Wideband antenna set** (telescopic + dipole kit) | Comes with the V4; covers the detect bands | incl. | rtl-sdr.com |
| **Log-periodic directional antenna** (0.85–6.5 GHz) | The direction-finding / "walk to it" antenna for 2.4/5.8 GHz cameras & Wi-Fi | $25–35 | Amazon/eBay |

> The RTL-SDR tops out ~1.7 GHz. For full 2.4/5.8 GHz coverage (Wi-Fi-band
> cameras, video Tx) the Wi-Fi/BT radios below handle those bands directly, and
> the **AD8317 RF power detector** (next section) covers raw field strength up
> to 6 GHz — the same range pro bug-sweepers use.

## Counter-surveillance sensors (~$90)

| Part | Channel it powers | ~Price | Source |
|------|-------------------|--------|--------|
| **AD8317 RF power detector module** (1 MHz–10 GHz log-detector) | Broadband bug/field-strength detection to 6+ GHz — the heart of a real RF sweeper; "warmer/colder" locating | $18 | Amazon/AliExpress |
| **ESP32 (WiFi+BT) module** | Wi-Fi survey (monitor mode), evil-twin/deauth detection, BLE tracker & bug hunting | $8 | Espressif |
| **NRF24L01+ module** | 2.4 GHz channel-by-channel RF energy scan (the waterfall) | $4 | generic |
| **MLX90640 thermal camera** (32×24, I²C) | Thermal inspection — heat of hidden powered electronics | $40 | Adafruit #4407 |
| **Pi Camera + IR-pass + LED ring** | Optical lens-finder (retroreflection) for offline cameras; sees 850 nm IR | $20 | Pi Camera Module 3 |

## Optional / upgrade sensors (~$60)

| Part | Adds | ~Price |
|------|------|--------|
| **PN532 NFC/RFID module** | NFC/RFID read + skimmer detection | $7 |
| **Ultrasonic MEMS mic** (e.g. SPH0641LU) | Acoustic / ultrasonic-beacon detection | $6 |
| **Magnetometer (QMC5883L) + EMF coil** | Magnetic-tracker + wired-bug / offline-electronics probe | $6 |
| **u-blox GPS module** | GNSS-integrity (jam/spoof) monitoring + scan geotagging | $15 |
| **LTE modem hat** (e.g. SIM7600) | Active cellular tower survey for IMSI-catcher detection | $25 |

## Enclosure & power (~$70)

| Part | Why | ~Price |
|------|-----|--------|
| **Pelican-style case w/ foam** (~13×10") | The box: lid screen, base electronics, antennas on shell | $40 |
| **18650 LiPo + UPS HAT** | Cordless grab-and-go operation | $30 |

---

## Budget summary

| Build tier | What you get | Total |
|------------|--------------|-------|
| **Essential** | Pi 5 + screen + RTL-SDR V4 + AD8317 + ESP32 + NRF24 | **~$285** |
| **Recommended** | Essential + thermal + lens-finder + directional antenna + battery | **~$390** |
| **Full** | Recommended + NFC + acoustic + EMF + GPS (drop the LTE hat to stay under) | **~$400 if selective** |

The **Recommended** build lands right at **~$390** and covers the channels that
catch the real-world threats: RF transmitters, Wi-Fi/BLE cameras & trackers,
analog video, thermal-visible hidden electronics, and offline cameras by their
lens. That's a genuinely capable, professional personal TSCM kit for the price
of a single mid-range commercial RF detector — and far more transparent.

## Honest notes

- **Cellular/IMSI detection** is the weakest cheap channel: a passive survey via
  SDR flags anomalies, but full IMSI-catcher detection wants the LTE modem,
  which pushes the budget. Treat cellular as "anomaly hint," not certainty.
- **The silent-device gap stands:** anything recording to local storage with its
  radio off (offline camera, voice recorder) emits nothing — the lens-finder,
  thermal, and EMF probe are how you catch those, not RF.
- This kit **detects and locates**; it never jams or attacks. That keeps it
  legal and on the right side of its purpose: knowing whether you're watched,
  and where it's coming from.
