# SENTRY — Laptop Build: Full RF / Wi-Fi / Bluetooth Manual

The **laptop version** of SENTRY: everything you can do for counter-surveillance
with a computer and USB gear — deep RF spectrum analysis, Wi-Fi hunting, Bluetooth
tracking, the hardware worth buying, and how to tune it all so it catches the
right devices. The on-screen **AI reading panels explain each signal in plain
language as you go.**

> Detect-only philosophy. You'll see powerful gear here (including transmit-capable
> radios). **Receiving and analyzing is legal; transmitting is not** unless you're
> licensed and on a permitted band — see the legal line in Part 1.

---

# TABLE OF CONTENTS
1. The legal line (read once)
2. What runs on a laptop
3. RF hardware tiers — what to buy
4. Wi-Fi & Bluetooth gear (optional upgrades)
5. Software setup (drivers, install)
6. The RF channel — operate & read the spectrum
7. The Wi-Fi channel — operate & tune
8. The Bluetooth channel — operate & tune
9. Spectrum analysis — what you're looking at
10. Tuning everything (cut false alarms, add devices)
11. Updating
12. Cheat sheet + troubleshooting

---

# 1. THE LEGAL LINE (read once, then build freely)

Simple version for the US:
- ✅ **Receiving, listening, monitoring, spectrum analysis** of radio signals for
  your own awareness — **legal** for general use with the gear here.
- ✅ **Scanning Wi-Fi/Bluetooth** that devices openly broadcast — legal.
- ❌ **Transmitting** on licensed/restricted frequencies without a license — illegal
  (FCC rules).
- ❌ **Jamming** (drowning out signals) — illegal to do, and even to build/sell the
  device.
- ❌ Decoding the **private content** of others' communications, or **attempting to
  decrypt** signals you're not authorized to receive — illegal (ECPA).
- ❌ **Cellular phone bands** are specifically protected — receivers are barred from
  tuning them, and listening to phone calls is illegal. SENTRY detects a cellular
  bug's *presence/behavior* (that something is transmitting), never its content.
- ❌ Using anything you happen to intercept **for your own benefit**, or sharing
  someone's private communication — illegal.

**About HackRF and similar:** they *can* transmit. That capability is legal to
own; **using it to transmit on most bands is not** unless you hold the right
license (e.g. an amateur-radio "ham" license) and stay on a band you're allowed.
**For SENTRY, keep everything receive-only.** You lose nothing for
counter-surveillance — detection is all receiving.

That's the whole rule. Build away.

---

# 2. WHAT RUNS ON A LAPTOP

| Capability | Hardware | On laptop? |
|------------|----------|-----------|
| **Wi-Fi** detection (cameras, rogue APs) | built-in Wi-Fi | ✅ free |
| **Bluetooth/BLE** (AirTags, trackers, bugs) | built-in Bluetooth | ✅ free |
| **RF spectrum** (HF–6 GHz depending on gear) | USB SDR (you buy) | ✅ |
| **Wider/stronger Wi-Fi capture** | USB Wi-Fi adapter w/ monitor mode | ✅ optional |
| Thermal / lens-finder / NFC / EMF | **Pi GPIO sensors** | ❌ that's the Pi box build |

Laptops have USB + HDMI but **no GPIO pins**, so the physical sensors come with the
Pi build. On the laptop you get the full radio side — which is the deepest,
richest part anyway.

---

# 3. RF HARDWARE TIERS — WHAT TO BUY

Pick your level. You can start cheap and upgrade.

### TIER 1 — Entry: RTL-SDR Blog V4  (~$45)
- **Range:** ~500 kHz – 1.766 GHz (HF/VHF/UHF). Receive only.
- **Catches:** analog wireless cameras (some), 315/433/868/915 MHz devices &
  bugs, pagers, lots of telemetry, FM/air/marine, much of the "IoT" spectrum.
- **Why start here:** the most-supported SDR on earth, cheap, the standard
  learning tool. Comes with antennas.
- **Verdict:** buy this first no matter what. Best dollar-for-dollar.

### TIER 2 — Wideband: HackRF One  (~$150–200)
- **Range:** 1 MHz – 6 GHz. Half-duplex. **Transmit-capable (keep it OFF — legal
  line, Part 1).**
- **Catches:** everything Tier 1 does PLUS the **2.4 GHz and 5.8 GHz bands** where
  Wi-Fi cameras, video transmitters, drones, and many modern bugs live. This is
  the big jump — full coverage to 6 GHz.
- **Why:** for real counter-surveillance the 2.4/5.8 GHz coverage matters; that's
  where modern wireless cameras sit. The RTL-SDR can't reach there; HackRF can.
- **Verdict:** the serious receive workhorse. The one I'd point you to for "go big."

### TIER 3 — High-performance receive: Airspy / SDRplay RSPdx  (~$200–300)
- **Range:** SDRplay RSPdx ~1 kHz – 2 GHz with excellent sensitivity & dynamic
  range; Airspy R2/Mini superb 24–1800 MHz.
- **Catches:** same bands as their range, but with **cleaner, more sensitive
  reception** — you'll hear weaker signals and resolve them better than HackRF in
  their range. Receive-only by design (no transmit worries).
- **Why:** if you want the best *receive quality* (not the widest range), these
  beat HackRF on signal clarity. Great for serious spectrum analysis under 2 GHz.
- **Verdict:** the "quality over max-frequency" choice. Many pros run a HackRF for
  range + an SDRplay for clean low-band work.

### TIER 4 — The power combo (what I'd build toward)
- **HackRF One** (1 MHz–6 GHz coverage incl. 2.4/5.8 GHz) **+** **RTL-SDR V4** (cheap
  second receiver for monitoring a fixed band while you sweep with the HackRF).
- Add a **wideband discone or log-periodic antenna** for better reception, and a
  **directional antenna** (log-periodic, 0.85–6.5 GHz, ~$30) for **direction-finding
  / walking toward a signal.**
- Total ~$250–300. This covers essentially the whole practical spectrum, receive,
  with the ability to locate.

### Antennas (don't skip — antenna matters as much as the radio)
| Antenna | For | ~Price |
|---------|-----|--------|
| Telescopic/dipole kit (comes w/ RTL-SDR) | general start | incl. |
| **Wideband discone** | broad receive across many bands | $30–50 |
| **Log-periodic directional (0.85–6.5 GHz)** | pointing/locating 2.4/5.8 GHz | $30 |
| Magnetic-mount whip | quick mobile use | $10–15 |

---

# 4. WI-FI & BLUETOOTH GEAR (optional upgrades)

Your built-in radios work. Upgrade only if you want more:
- **USB Wi-Fi adapter with monitor mode** (e.g. Alfa AWUS036ACM, ~$35): captures
  more Wi-Fi detail than built-in cards, better for spotting hidden/odd networks
  and for 5 GHz. Useful but not required.
- **USB Bluetooth 5 adapter** (~$15): a stronger BLE radio than some built-ins,
  slightly better tracker range. Minor upgrade.

For most people: built-in Wi-Fi + built-in Bluetooth + an SDR is the sweet spot.

---

# 5. SOFTWARE SETUP

### 5.1 Base install (you have this)
SENTRY runs via `START_SENTRY.bat` or:
```powershell
cd C:\Users\YOU\Documents\sentry
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 5.2 RF driver — RTL-SDR (Windows, one time)
Windows needs the generic WinUSB driver via **Zadig**:
1. Plug in the RTL-SDR.
2. Download & run **Zadig** (zadig.akeo.ie).
3. **Options → List All Devices.**
4. Pick **"Bulk-In, Interface (Interface 0)"** (the RTL2832U).
5. Set target driver to **WinUSB** → **Replace Driver.**
6. Then: `pip install pyrtlsdr` (inside the venv).

### 5.3 RF driver — HackRF (if you go Tier 2)
1. Install **HackRF tools** for Windows (the `hackrf` package / `pothosware` SDR
   bundle, or via the SDR# / SDR Console installers which include drivers).
2. Use **Zadig** the same way to bind the HackRF interface to **WinUSB**.
3. Python access: `pip install pyhackrf` (or SENTRY can read it via SoapySDR —
   ask Claude Code to wire the HackRF sensor if you buy one; the RF sensor is
   structured to extend).
4. Verify with `hackrf_info` in a terminal — it should print your HackRF's serial.

### 5.4 A second tool to "see" the spectrum visually (highly recommended)
Install **SDR#** (SDRSharp) or **SDR Console** — free Windows spectrum-analyzer
apps. They give you a gorgeous live waterfall and let you *listen* and explore.
Run these alongside SENTRY to learn what raw spectrum looks like; SENTRY then does
the automatic detection/identification on top. (SENTRY = the watchman; SDR# = the
microscope.)

---

# 6. THE RF CHANNEL — OPERATE & READ

### Get it live
1. Antenna assembled and connected; SDR plugged into USB; driver done (5.2/5.3).
2. Run SENTRY → the window shows `[ONLINE] RF Spectrum`.
3. UI → **Channels → RF Spectrum → See the live signal.**

### What you see (and the AI reads it for you)
- **Left half:** the live spectrum + waterfall — every transmitter as a peak;
  history scrolling below.
- **Right half:** the AI reading — it names the peaks, classifies them
  (camera / bug / unknown), and says what to do. *This is the "tell me what's
  going on" you wanted — it's reading the signal live.*

### Prove it works
Press a **car key fob** (315/433 MHz) near the antenna → a spike appears and the AI
notes a 433 MHz burst. That's your confirmation the whole chain works.

### Find & walk to a signal
Switch to the directional (log-periodic) antenna, tap a device → **Locate**. The
strength trace climbs as you point/move toward it; the AI guides you in.

---

# 7. THE WI-FI CHANNEL — OPERATE & TUNE

### Operate
- Built-in Wi-Fi, no setup. SENTRY scans every AP/device, matches MAC prefixes to
  camera vendors, flags duplicate-SSID **evil-twins**.
- **Scan tab** → camera-flagged devices show maker + signal; tap for full intel.

### Tune
- **Add a camera brand** it doesn't know: `sentry_backend/sensors/wifi.py` →
  `CAMERA_OUIS` → add `"aa:bb:cc": "Brand",` (first 3 MAC pairs, lowercase).
- **Find a MAC's vendor:** search the prefix on an "OUI lookup" site, or ask Claude
  Code.
- An optional **USB monitor-mode adapter** (Part 4) lets a future version capture
  deauth/handshake detail; ask Claude Code to extend wifi.py if you add one.

---

# 8. THE BLUETOOTH CHANNEL — OPERATE & TUNE

### Operate
- Built-in Bluetooth (allow the Windows permission prompt). Finds BLE devices,
  flags **AirTag/Find My** trackers, and escalates to **"following you"** when the
  same tag recurs across scans.
- Walk around with a suspected tag for a minute; the flag should escalate.

### Tune
- **Following sensitivity:** `bluetooth.py` → `following = cnt >= 3` (lower =
  flags sooner; higher = more certain).
- **Flag unnamed chatty devices:** the heuristic for no-name frequent advertisers
  is in `_classify()` — adjust the `cnt >= 4` there.

---

# 9. SPECTRUM ANALYSIS — WHAT YOU'RE LOOKING AT

A quick field guide so the waterfall makes sense (the AI panel says this too, in
context):
- **A tall, steady peak that doesn't move** = a continuous transmitter. In a video
  band (2.4/5.8 GHz) that's camera-like.
- **Short repeating blips** = bursty device — a tracker checking in, a sensor, a
  key fob, or a bug calling out. Note the **interval** (every few sec vs. every
  30–60 sec).
- **A peak that hops around** = frequency-hopping (some Bluetooth, some secure
  links) — harder to pin; the burst-catcher tool watches over time.
- **A wide smear vs. a thin spike** = bandwidth. Video is wide; a simple control
  signal is thin.
- **Noise floor** = the baseline fuzz. A "signal" is anything rising clearly above
  it. Tuning = where you draw that line (Part 10).
- **Where to look for common threats:** 433 MHz (cheap bugs/sensors), 1.8–1.9 GHz
  (GSM bugs calling out), 2.4 GHz (Wi-Fi cameras, BT), 5.8 GHz (analog video
  cameras, drones).

Run **SDR#** next to SENTRY to explore these by ear and eye; it's the fastest way
to build intuition.

---

# 10. TUNING EVERYTHING

### RF false alarms / misses
`sentry_backend/sensors/rf.py` → `PEAK_DB_OVER_FLOOR = 8.0`
- Too many false alarms → raise (12–15).
- Missing weak signals → lower (6).

### Add an RF band to watch
`rf.py` → `BANDS` list → add `(low_MHz, high_MHz, "name", "category", "severity",
"note")`. Example: `(1200, 1300, "1.2 GHz video", "camera", "alert", "1.2 GHz Tx")`.

### Wi-Fi / Bluetooth
See Parts 7 & 8.

### The tuning loop
Run in a room you understand → note false alarms (raise threshold) and misses
(lower it / add the device) → change **one thing** → re-test against a known device
→ commit to GitHub so you can roll back. Hand any of it to Claude Code in plain
English.

---

# 11. UPDATING

```powershell
cd C:\Users\YOU\Documents\sentry
git pull
.venv\Scripts\activate
pip install -r requirements.txt
```
Keep your detection lists current (new camera brands, new bands). Periodically ask
Claude Code: *"add well-known consumer camera MAC prefixes to wifi.py and tell me
what you added."*

---

# 12. CHEAT SHEET + TROUBLESHOOTING

```
BUY FIRST:   RTL-SDR Blog V4 (~$45)         GO BIG: + HackRF One (1MHz–6GHz, RX only)
BEST RECEIVE QUALITY <2GHz: SDRplay RSPdx / Airspy
ANTENNAS:    wideband discone + directional log-periodic
WI-FI/BT:    built-in works; optional Alfa monitor-mode adapter

DRIVERS:     Zadig → WinUSB for the SDR ; pip install pyrtlsdr (or pyhackrf)
EXPLORE:     run SDR# / SDR Console next to SENTRY for a visual waterfall

RUN:         START_SENTRY.bat  → http://localhost:8000
PROVE RF:    press a key fob near the antenna, watch the spike + AI note it

TUNE RF:     rf.py PEAK_DB_OVER_FLOOR (8→12 less sensitive, 8→6 more)
ADD CAMERA:  wifi.py CAMERA_OUIS "aa:bb:cc":"Brand"
ADD BAND:    rf.py BANDS (low,high,"name","category","severity","note")
TRACKER:     bluetooth.py following = cnt >= 3  (lower = sooner)

UPDATE:      git pull ; pip install -r requirements.txt
SAVE:        git add . && git commit -m "msg" && git push
```

### Troubleshooting
- **RF offline** → redo Zadig/WinUSB; confirm `pip install pyrtlsdr` in the venv;
  try another USB port.
- **HackRF not found** → `hackrf_info` in a terminal; if blank, redo Zadig for the
  HackRF interface; reinstall HackRF tools.
- **RF online but flat** → reposition antenna away from the laptop; extend it;
  trigger a strong source; lower the threshold.
- **Bluetooth nothing** → BT on in Windows; allow the permission prompt; scans take
  seconds.
- **Wi-Fi nothing** → Wi-Fi on; built-in `netsh` is used; run again.
- **Want thermal/lens/NFC** → that's the Pi box build (next manual).
