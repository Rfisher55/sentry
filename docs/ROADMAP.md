# SENTRY — Honest Build Roadmap

**What this is:** a personal counter-surveillance station — a Raspberry Pi in a
Pelican-style case that scans the RF / Wi-Fi / Bluetooth / cellular / optical /
thermal / acoustic environment, identifies what it finds, and helps you locate
it. Built as a **learning + demonstration project**: proof you can design and
build a real multi-sensor instrument end to end.

This document is the honest map of **what's done, what's left, and what "working"
actually means** at each stage — so there are no surprises.

---

## Stage 0 — DONE ✅ (the interface + the plan)

You already have this, finished and audited:

- **The full UI/UX** — 3 tabs (Scan, Tools, Channels), 18 tool screens, 12
  detection channels, the directional map, per-device intel, the live-signal
  views, the locate screen. Every click path works.
- **The detection *logic model*** — how a finding becomes an identity, a
  dossier, a counter-measure, a bearing. The reasoning is real even though the
  data feeding it is simulated.
- **The hardware bill of materials** — a real, buildable, ~$390 parts list.
- **Honest design values** — coverage gaps surfaced, silent-device caveat,
  detect-only (no jamming/attack).

**What "done" means here:** it looks and behaves like the finished instrument,
running on *simulated* signals. Perfect for demonstrating the design. It does
not yet touch a real radio.

---

## Stage 1 — Hardware bring-up (the foundation)

Goal: a Pi in the case, powered, screen working, the UI running as a kiosk.

- [ ] Assemble Pi 5 + cooler + screen + power; flash Raspberry Pi OS
- [ ] Launch the SENTRY HTML in kiosk/full-screen on boot
- [ ] Mount in the Pelican case; cut antenna ports; wire face buttons (optional)
- [ ] Battery/UPS HAT for cordless operation

**"Working" here =** the device powers on and shows the interface on its own
screen. Still simulated data — but now it's a *physical device you built*. This
alone is a strong demonstration milestone.

**Skill you'll learn:** Pi setup, Linux kiosk config, power, enclosure work.

---

## Stage 2 — First real sensor: RF (the big one)

Goal: replace simulated RF with a real RTL-SDR feed. This is where it starts
*actually detecting*.

- [ ] Plug in RTL-SDR Blog V4; install `rtl-sdr` drivers; confirm with `rtl_test`
- [ ] Stream live spectrum (e.g. via `rtl_power` or `soapy`) into a small Python
      service on the Pi
- [ ] Pipe that real spectrum into the live-signal view (replace the fake trace)
- [ ] Detect peaks above the noise floor → real "something is transmitting here"
- [ ] Tune the analog-video band (5.8 GHz needs the Wi-Fi radio / a different
      front-end; RTL-SDR alone tops out ~1.7 GHz)

**"Working" here =** you wave a key fob / turn on a wireless device and the
station *actually sees the signal appear*. That's the magic moment — real
detection. Everything after is adding more senses.

**Skill you'll learn:** SDR, sampling, FFT/spectrum basics, real-time DSP, the
single most valuable RF-engineering skill in the project.

---

## Stage 3 — Wi-Fi + Bluetooth (the highest-value real threats)

Goal: real device enumeration — where most actual hidden cameras and trackers
live.

- [ ] ESP32 (or the Pi's own radio) in monitor mode → list real Wi-Fi APs/clients
- [ ] Match real MAC OUIs to vendors → flag camera-maker devices for real
- [ ] Detect real duplicate-SSID (evil-twin) and deauth frames
- [ ] BLE scan → list real nearby tags; flag AirTag-class advertisements;
      detect one that reappears as you move (following)

**"Working" here =** it finds the *actual* IP camera and the *actual* AirTag in
the room. This is the most practically useful real capability and very
achievable — these protocols announce themselves.

**Skill you'll learn:** 802.11 monitor mode, packet capture, BLE scanning, OUI
lookups — real, employable wireless-security skills.

---

## Stage 4 — The optical + thermal senses (catch the silent ones)

Goal: catch devices that emit no radio — the gap RF can't close.

- [ ] Pi camera + IR-pass filter + LED ring → real lens retroreflection scan
- [ ] MLX90640 thermal → real heat map of surfaces
- [ ] Wire both into their tool screens with real frames

**"Working" here =** you can sweep a room and spot an offline camera's lens
glint or a hidden device's heat. This is what makes it more than an RF toy.

**Skill you'll learn:** camera/IR imaging, I²C sensors, basic computer vision.

---

## Stage 5 — The rest, as you want them

Each is an independent add-on; do them in any order, or stop when satisfied:

- [ ] NFC/RFID (PN532) — real card reads + skimmer-field detection
- [ ] Acoustic/ultrasonic (MEMS mic) — real ~19 kHz beacon detection
- [ ] EMF/magnetic probe — real field-rise over electronics
- [ ] GNSS module — real GPS jam/spoof monitoring
- [ ] Cellular survey (SDR or LTE hat) — *weakest channel; treat as anomaly hint*
- [ ] Direction-finding — directional antenna + signal-strength → real bearing

**"Working" here =** a genuinely multi-sensor instrument. Each sensor you add is
a self-contained win you can demo on its own.

---

## What "real detection" honestly requires (the hard truths)

- **Noise vs. signal is the whole game.** The hard part isn't seeing energy —
  it's deciding *this is a camera, that is your microwave*. Expect to spend most
  of your time on thresholds and false-alarm tuning. This is normal and it's the
  real engineering.
- **Each sensor is its own mini-project.** Don't try to light them all up at
  once. Get RF solid, demo it, then add the next. Stage-by-stage is how this
  actually gets built without drowning.
- **It will never be bug-free, and that's fine.** Real instruments are
  iteratively tuned. "Working" means "reliably catches the common stuff and is
  honest about the rest," not "flawless."
- **The silent-device gap never closes.** A local-storage recorder with its
  radio off is caught only by lens/thermal/EMF/physical search — no amount of
  software fixes that. The device already says so; keep saying so.

---

## Honest milestones to demonstrate "I built this"

You don't need all of it to have an impressive, true demonstration:

1. **Stage 1** → "I built a custom Pi instrument in a field case." ✅ real device
2. **Stage 2** → "It detects live RF transmissions." ✅ real detection
3. **Stage 3** → "It finds real Wi-Fi cameras and Bluetooth trackers." ✅ the
   genuinely useful, genuinely achievable headline capability
4. **Stage 4+** → "It's a true multi-sensor counter-surveillance station." ✅ the
   full vision

**Reaching Stage 3 alone is a legitimately impressive, real, working build** —
and it's the sweet spot of achievable + useful + demonstrable. Everything past
it is bonus capability you can keep adding as you learn.

---

## Bottom line

What you have today: a polished, working **interface and a credible hardware
plan** — a strong Stage 0. The path to a *real* detector is the staged sensor
work above. None of it is beyond a motivated builder; all of it teaches genuinely
valuable skills (SDR, wireless security, embedded sensors, signal processing).

Build it sensor by sensor, demo each win, and be honest about the limits — and
you'll have both a real device *and* the proof that you can design and build one.
