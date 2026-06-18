# SENTRY — Complete Build Documentation

A personal counter-surveillance station you build yourself, in phases, starting
with a laptop and growing into a full Raspberry Pi field unit in a Pelican case.

> **Detect-only.** SENTRY receives and analyzes signals devices openly broadcast
> and helps you find devices in your own space. It never jams, clones, transmits
> to interfere, or decodes private content. Receiving/analyzing is legal;
> transmitting on restricted bands is not.

---

## What SENTRY does
Scans the Wi-Fi, Bluetooth, network, and (with hardware) radio environment around
you, identifies devices that may be watching or tracking you, and helps locate
them — with a live interface and honest, real-data readings.

## The build journey (in order)
This documentation takes you from nothing to a full field unit, in phases. Do them
in order; each builds on the last.

| Doc | What it covers | When |
|-----|----------------|------|
| **01_QUICKSTART.md** | Get the working laptop version running in minutes | Start here |
| **02_LAPTOP_CLAUDECODE_GITHUB.md** | Develop it with Claude Code + back up to GitHub | Setup |
| **03_LAPTOP_FULL_RF_WIFI_BT.md** | Deep laptop build: RF/Wi-Fi/Bluetooth, hardware tiers, tuning | Core build |
| **04_LAPTOP_BUILDOUT_PLAN.md** | Phased plan: every USB add-on + feature to build toward | Plan/expand |
| **05_PI_ULTIMATE_BOX.md** | The full Raspberry Pi + Pelican case build (thermal, lens, NFC, etc.) | Step-up |
| **06_HARDWARE.md** | Complete parts lists with prices | Reference |
| **07_ROADMAP.md** | What's built, what's staged, the big picture | Reference |
| **08_FULL_FEATURE_CATALOG.md** | Every detection feature, by threat type, to build toward total coverage | Reference/expand |
| **09_SHOPPING_LIST_PI_BOX.md** | Complete parts list for the Pi box build, with links and prices | Shopping |
| **10_SHOPPING_FROM_SCRATCH.md** | Phased buying plan from zero ($0 -> $50 -> full box), with running totals | Shopping |
| **11_PHASES_6_7_8.md** | Advanced phases: deeper detection, true direction-finding, and monitoring your own home/network | Advanced |
| **12_MOVING_GEAR_LAPTOP_TO_PI.md** | How to carry your radio gear from the laptop build into the Pi box (buy once, use in both) | Transfer |

## The fastest path
1. **Run it today:** follow 01_QUICKSTART — works on a laptop with built-in
   Wi-Fi + Bluetooth, nothing to buy.
2. **Make it yours:** 02 connects Claude Code + GitHub so you can build and back up.
3. **Go deeper on the laptop:** 03 + 04 — add an RTL-SDR (~$45) for radio, then
   expand phase by phase.
4. **Build the field unit:** 05 — Raspberry Pi in a Pelican case with physical
   sensors. The "ultimate box."

## What works at each stage (honest)
- **Laptop, no extra hardware:** Wi-Fi + Bluetooth + local-network detection. Real.
- **Laptop + RTL-SDR (~$45):** adds RF spectrum (analog cameras, bugs, remotes).
- **Laptop + HackRF (~$150):** adds 2.4/5.8 GHz (modern Wi-Fi cameras, drones).
- **Laptop + directional antenna:** adds real "walk to it" direction-finding.
- **Raspberry Pi box:** all the above PLUS thermal, lens-finder, NFC, EMF,
  acoustic — the physical-world sensors that catch silent/offline devices.

## The honest limits (true at every stage)
- A device recording to local storage with its radio OFF emits nothing — only the
  Pi's physical sensors (thermal/optical) can catch those.
- Precise direction needs a directional antenna; built-in radios give
  closer/farther only.
- This is a capable learning + personal tool, not a guarantee against
  professional surveillance.

## How to use & contribute
- **Run it:** see 01_QUICKSTART.
- **Build/modify:** open the project in Claude Code (see 02); it reads CLAUDE.md
  and knows the project.
- **Save your work:** commit and push to GitHub after each session.
- **License:** MIT (see LICENSE).
