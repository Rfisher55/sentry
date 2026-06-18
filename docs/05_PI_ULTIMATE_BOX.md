# SENTRY — The Ultimate Pi Box Build (Beginner→Advanced)

Your **step-up build.** Everything the laptop does (RF, Wi-Fi, Bluetooth) PLUS the
physical-sensor world — thermal, optical lens-finder, NFC/RFID, acoustic, EMF —
wired into a Raspberry Pi in a rugged case, with deep tuning and precision. This
manual assumes no prior electronics/terminal experience and explains everything.

> Detect-only. Receiving/analyzing is legal; transmitting on restricted bands is
> not (see the laptop manual's legal section — same rules). This box only
> listens, sees heat/light, and senses fields — it never transmits to interfere.

---

# TABLE OF CONTENTS
1. What this build adds over the laptop
2. The big picture & build order
3. Words you need to know
4. Safety rules
5. The complete shopping list (tiered: ~$390 core → ~$550 ultimate)
6. Understand the Pi & its pins
7. STEP 1 — Flash the SD card
8. STEP 2 — First boot
9. STEP 3 — Connect to the internet
10. STEP 4 — Terminal basics
11. STEP 5 — Install base software
12. STEP 6 — Wire every sensor (diagrams)
13. STEP 7 — Enable interfaces
14. STEP 8 — Test every sensor
15. STEP 9 — Install SENTRY
16. STEP 10 — Auto-start (kiosk)
17. STEP 11 — Build it into the case
18. STEP 12 — Updating, tuning & precision
19. Troubleshooting

---

# 1. WHAT THIS BUILD ADDS OVER THE LAPTOP

The laptop covers the **radio** world. The Pi adds the **physical** world — the
sensors that catch what radio can't, especially **silent devices** (a camera
recording to a card with its radio off emits no radio at all):

| New sensor | Catches | Connects via |
|------------|---------|--------------|
| **Thermal camera (MLX90640)** | heat of any powered hidden electronics | I²C pins |
| **Lens-finder (Pi cam + IR ring)** | camera lenses by glint — even offline cams | camera port + pins |
| **NFC/RFID reader (PN532)** | skimmers, covert readers, card cloning fields | I²C/SPI pins |
| **EMF / magnetic probe** | wired bugs, magnet-mounted trackers, hidden electronics | I²C pins |
| **Acoustic / ultrasonic mic** | ultrasonic tracking beacons, some active mics | USB/I²S |
| **GNSS module** (optional) | GPS jamming/spoofing | USB/UART |

Plus everything the laptop does (RF via SDR, Wi-Fi, Bluetooth) runs here too. This
is the full instrument.

---

# 2. THE BIG PICTURE & BUILD ORDER

Don't build it all at once. **Get each stage working before adding the next** —
that's how real hardware gets built without frustration.

1. **Core boots** (Pi + screen + power + internet) → you see the desktop.
2. **Software runs** (SENTRY on simulated data) → the interface works.
3. **RF + Wi-Fi + BLE live** (plug in the SDR) → real radio detection.
4. **Thermal** wired → real heat detection.
5. **Lens-finder** (camera + IR) → catch offline cameras.
6. **NFC, EMF, acoustic, GNSS** → one at a time, each its own win.
7. **Mount it all in the case** → the finished box.

---

# 3. WORDS YOU NEED TO KNOW

- **Raspberry Pi (the "Pi"):** small full computer, the brain.
- **GPIO pins:** the 40 metal pins on the Pi; sensors connect here.
- **I²C ("eye-squared-see"):** 2-wire way (SDA+SCL) sensors talk to the Pi.
- **SPI:** another sensor connection (a few more wires); some NFC boards use it.
- **SDA/SCL:** the two I²C wires (data / clock).
- **3.3V / 5V / GND:** power pins and ground. Use the exact pin stated.
- **Jumper wires:** push-on wires; "female" end slips over a pin. Use
  **female-to-female.**
- **Ribbon cable:** the flat cable for the camera.
- **SDR (RTL-SDR/HackRF):** USB radio receiver. No pin wiring.
- **Terminal:** the text window where you type commands. We go slow.
- **Kiosk:** Pi boots straight into SENTRY full-screen like an appliance.

---

# 4. SAFETY RULES

1. **Power off and unplug before touching pins or sensors.** Wiring live can fry
   parts.
2. **Double-check every wire before powering on** — reversed power/ground destroys
   parts instantly.
3. **Touch metal first** (static can kill chips). Don't build on carpet/blankets.
4. **Never force a connector.**
5. **Exact voltage pin every time** (this manual tells you).
6. **Don't seal the case airtight** — the Pi needs airflow.
7. **Receive-only.** Don't modify to transmit/jam — illegal.

---

# 5. THE COMPLETE SHOPPING LIST (tiered)

### CORE — required (~$215)
| Part | What | ~$ |
|------|------|----|
| Raspberry Pi 5, 8GB | brain | 80 |
| Active Cooler | prevents overheating | 5 |
| Official 27W USB-C PSU | power (not a phone charger) | 12 |
| 64GB microSD (A2) | storage | 12 |
| Official 7" Touch Display 2 | screen | 60 |
| microSD reader (if laptop lacks one) | flashing | 8 |
| jumper wire kit (F-F, 40pc) | wiring sensors | 7 |
| Pelican-style case + pluck foam | the box | 40 |

### RADIO — the laptop capabilities, on the Pi (~$75)
| Part | What | ~$ |
|------|------|----|
| RTL-SDR Blog V4 + antenna kit | RF spectrum (HF–1.7GHz) | 45 |
| Log-periodic directional antenna 0.85–6.5GHz | locating signals | 30 |
| *(upgrade)* HackRF One | full 1MHz–6GHz incl 2.4/5.8 (RX only) | +150 |

### PHYSICAL SENSORS — the step-up (~$125)
| Part | What | ~$ |
|------|------|----|
| MLX90640 thermal camera (I²C, w/ headers) | heat of hidden electronics | 40 |
| Pi Camera Module 3 | lens-finder camera | 25 |
| IR LED ring light | makes lenses glint | 8 |
| PN532 NFC/RFID module | skimmer/reader detection | 7 |
| Magnetometer (QMC5883L) + EMF coil | magnetic/field probe | 8 |
| USB ultrasonic-capable mic (or I²S MEMS) | ultrasonic beacons | 15 |
| *(optional)* u-blox GNSS USB module | GPS jam/spoof monitor | 15 |

### POWER — go cordless (~$30)
| Part | What | ~$ |
|------|------|----|
| 18650 UPS HAT + 2×18650 cells | run without a wall plug | 30 |

### Budget tiers
- **Core radio box ~$390:** Core + RTL-SDR + directional antenna + thermal +
  lens-finder + battery. (Matches the earlier "Recommended.")
- **Ultimate box ~$550:** add HackRF (full 6 GHz), NFC, EMF, acoustic, GNSS.

### Tools to have
Small Phillips screwdriver, hobby knife (foam + case holes), F-F jumpers, optional
soldering iron (only if a module lacks headers), optional SMA bulkhead connectors
for clean antenna mounting.

---

# 6. UNDERSTAND THE PI & ITS PINS

Hold the Pi with the 40 pins along the top, USB on the right.

```
        ┌──────────── 40 GPIO PINS (top edge) ────────────┐
        │  · · · · · · · · · · · · · · · · · · · ·         │
   ┌────┴───────────────────────────────────────────────┐
   │  [CAMERA + DISPLAY ribbon ports — LEFT edge]  USB-C │ ← power
   │  Raspberry Pi 5                          ┌──┐┌──┐   │
   │  [microSD slot — UNDERSIDE]              │USB││USB│ │ ← blue = USB3 (SDR here)
   │                                  Ethernet└──┘└──┘   │ ← wired internet
   └─────────────────────────────────────────────────────┘
```

GPIO numbering (Pin 1 at the board corner; odd = left column, even = right):
```
   Pin  1 [3.3V ] ● ●  [ 5V   ] Pin  2
   Pin  3 [SDA  ] ● ●  [ 5V   ] Pin  4
   Pin  5 [SCL  ] ● ●  [ GND  ] Pin  6
   Pin  7 [GPIO4] ● ●  [GPIO14] Pin  8
   Pin  9 [GND  ] ● ●  [GPIO15] Pin 10
   Pin 11 [GPIO17]● ●  [GPIO18] Pin 12
```
**Good news about I²C:** the thermal cam, NFC, and EMF sensor can **all share the
same two I²C pins** (SDA=Pin 3, SCL=Pin 5) because each has a different address —
that's how one bus talks to several sensors. They share power and ground pins too.

---

# 7. STEP 1 — FLASH THE SD CARD

On your laptop: install **Raspberry Pi Imager** (raspberrypi.com/software).
1. Insert microSD. In Imager: Device = **Pi 5**; OS = **Raspberry Pi OS (64-bit)**;
   Storage = your card.
2. **Edit Settings:** hostname `sentry`; set username+password (**write down**);
   enter Wi-Fi name/password/country; **Services tab → enable SSH**.
3. **Write.** Remove card when done.

---

# 8. STEP 2 — FIRST BOOT

1. microSD into the Pi (underside).
2. Connect the 7" screen (wide ribbon → DISPLAY port; short power cable).
3. Plug in the 27W USB-C power. Desktop appears in a few minutes (may reboot once).
   Black screen → Troubleshooting 19B.

---

# 9. STEP 3 — CONNECT TO THE INTERNET

**Wi-Fi (desktop):** click the network icon (top-right) → pick your network →
password → Connect.

**Wi-Fi (terminal/SSH):** `sudo raspi-config` → System Options → Wireless LAN →
country, SSID, password.

**Phone hotspot:** turn on your phone's hotspot, connect the Pi to it like normal
Wi-Fi.

**Ethernet (most reliable):** plug a cable from your router into the Pi's Ethernet
port — automatic, no setup. Use this if Wi-Fi gives trouble.

**Check you're online:**
```bash
ping -c 4 raspberrypi.com
```
Replies with times = online ✓. "Packet loss / not known" = not online → recheck
Wi-Fi name/password/country in raspi-config, move closer, or use Ethernet.

---

# 10. STEP 4 — TERMINAL BASICS

Open the terminal (black rectangle icon, top bar). Type a command, press **Enter**.
Paste with **Ctrl+Shift+V**. `sudo` = run as admin (asks your password; typing
shows nothing — normal). The commands here are safe.

---

# 11. STEP 5 — INSTALL BASE SOFTWARE

One block at a time:
```bash
sudo apt update && sudo apt full-upgrade -y
```
```bash
sudo apt install -y git python3-venv python3-pip rtl-sdr i2c-tools python3-numpy chromium-browser libportaudio2
```
```bash
sudo reboot
```

---

# 12. STEP 6 — WIRE EVERY SENSOR

> ⚠️ **POWER OFF FIRST:** `sudo shutdown now`, wait for the LED to stop, **unplug.**

Wire in this order. The I²C sensors (thermal, NFC, EMF) share pins 1/3/5/6.

### 6A — RTL-SDR / HackRF (RF) — USB, no pins
Screw the antenna on; plug into a **blue USB 3.0** port. Done.

### 6B — MLX90640 Thermal Camera — I²C (4 wires)
```
   MLX90640            RASPBERRY PI
   VIN ●──────────────► Pin 1  (3.3V)
   GND ●──────────────► Pin 6  (GND)
   SDA ●──────────────► Pin 3  (SDA)
   SCL ●──────────────► Pin 5  (SCL)
```

### 6C — PN532 NFC/RFID — I²C (shares the bus)
Set the PN532's little switches to **I²C mode** (check its label — usually two DIP
switches). Then:
```
   PN532               RASPBERRY PI
   VCC ●──────────────► Pin 4  (5V)      [PN532 likes 5V]
   GND ●──────────────► Pin 9  (GND)
   SDA ●──────────────► Pin 3  (SDA)     [same SDA as thermal — shared bus]
   SCL ●──────────────► Pin 5  (SCL)     [same SCL — shared bus]
```
> Sharing SDA/SCL with the thermal cam is fine — different I²C addresses. Use a
> small breadboard or wire two jumpers into one pin if needed; or a "Qwiic/STEMMA"
> splitter makes this tidy.

### 6D — Magnetometer/EMF (QMC5883L) — I²C (shares the bus)
```
   QMC5883L            RASPBERRY PI
   VCC ●──────────────► Pin 1  (3.3V)    [shares 3.3V with thermal]
   GND ●──────────────► Pin 6  (GND)     [shares GND]
   SDA ●──────────────► Pin 3  (SDA)     [shared bus]
   SCL ●──────────────► Pin 5  (SCL)     [shared bus]
```

### 6E — Pi Camera Module 3 — ribbon (lens-finder)
Lift the **CAMERA** port clip (left edge), slide ribbon in (metal contacts facing
the correct way — away from the USB side; blue stiffener toward it), press clip
down.

### 6F — IR LED ring — 2–3 wires (around the camera lens)
```
   IR LED RING         RASPBERRY PI
   +    ●──────────────► Pin 2  (5V)
   −    ●──────────────► Pin 14 (GND)    [another ground pin]
   sig  ●──────────────► Pin 11 (GPIO17) [optional on/off]
```

### 6G — Ultrasonic mic — USB (easiest) or I²S
A **USB** ultrasonic-capable mic just plugs into a USB port. (I²S MEMS mics wire to
pins — more involved; start with USB.)

### 6H — GNSS module — USB
Plug the u-blox USB GPS into a USB port. No pin wiring.

### 6I — 18650 UPS HAT — last
Seats on the GPIO pins (covers them). Use a HAT with a **stacking/pass-through
header**, or a **GPIO breakout**, so the I²C sensors still reach pins 1/3/5/6.
Insert cells matching +/−; charge via the HAT's USB-C.

### Final check
Count pins with your finger: thermal VIN→1/GND→6/SDA→3/SCL→5; PN532 VCC→4/GND→9/
shared SDA/SCL; EMF on shared bus; camera ribbon seated; IR ring +→2/−→14; USB
mics/GPS in USB; SDR in blue USB. Power back on.

---

# 13. STEP 7 — ENABLE INTERFACES

```bash
sudo raspi-config
```
- **Interface Options → I2C → Yes**
- **Interface Options → Camera → Yes** (if asked)
- **Interface Options → SPI → Yes** (only if your NFC board uses SPI)
- Finish.

Speed up I²C for the thermal cam:
```bash
sudo nano /boot/firmware/config.txt
```
Make the line read:
```
dtparam=i2c_arm=on,i2c_arm_baudrate=400000
```
Save (Ctrl+O, Enter, Ctrl+X), `sudo reboot`.

---

# 14. STEP 8 — TEST EVERY SENSOR

```bash
rtl_test                       # RF: "Found 1 device" (Ctrl+C to stop)
i2cdetect -y 1                 # I²C: should show numbers for EACH sensor
                               #   thermal ~33, PN532 ~24, QMC5883L ~0d (varies)
libcamera-hello --list-cameras # camera: lists Camera Module 3
arecord -l                     # mic: lists your USB audio device
ls /dev/ttyACM*                # GNSS: shows a device if the USB GPS is seen
```
Each address that appears in `i2cdetect` is one working I²C sensor. If one's
missing, recheck just that sensor's wiring (Troubleshooting 19E).

---

# 15. STEP 9 — INSTALL SENTRY

```bash
cd ~
git clone https://github.com/YOURNAME/sentry.git
cd sentry
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyrtlsdr bleak
```
Run:
```bash
python3 -m sentry_backend.server
```
Open the Pi browser to **http://localhost:8000**. Wi-Fi, Bluetooth, RF go online.
Wave a wireless device → RF reacts; point the thermal at your hand → warm spot.

> The thermal/NFC/EMF/lens *backends* are the build-out stages — the hardware is
> now wired and ready. In Claude Code say: *"my MLX90640 is wired and shows on
> i2cdetect — write the thermal sensor backend and add it to SENTRY."* It extends
> `sentry_backend/sensors/` like the existing ones.

---

# 16. STEP 10 — AUTO-START (KIOSK)

```bash
nano ~/sentry/start.sh
```
Paste (replace `YOURUSER`):
```bash
#!/bin/bash
cd /home/YOURUSER/sentry
source .venv/bin/activate
python3 -m sentry_backend.server &
sleep 6
chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8000
```
```bash
chmod +x ~/sentry/start.sh
mkdir -p ~/.config/autostart
nano ~/.config/autostart/sentry.desktop
```
Paste (replace `YOURUSER`):
```
[Desktop Entry]
Type=Application
Name=SENTRY
Exec=/home/YOURUSER/sentry/start.sh
X-GNOME-Autostart-enabled=true
```
`sudo reboot`. Launches full-screen. Exit kiosk: Ctrl+W or Alt+F4.

---

# 17. STEP 11 — BUILD IT INTO THE CASE

### Layout
```
   LID:                         BASE:
   ┌────────────────┐           ┌──────────────────────┐
   │   7" SCREEN     │          │ [Pi 5 + cooler]       │
   │  (faces user)   │          │ [UPS HAT + batteries] │
   └────────────────┘           │ thermal ─► hole       │
                                │ Pi cam + IR ring ─► hole│
                                │ NFC pad ─► one face    │
                                │ EMF probe (on a lead)  │
                                │ SDR + antennas (bulkhead)│
                                └──────────────────────┘
```

### Steps
1. **Dry-fit** everything in the pluck foam before cutting; trace and pluck snug
   pockets.
2. **Antenna ports:** mount SMA bulkhead connectors through the case wall; antennas
   outside, short cables to the SDR inside. (Shortcut: route cables out a notch.)
3. **Sensor windows:** cut small holes so the thermal cam and Pi camera see out;
   the IR ring mounts around the camera lens facing out.
4. **NFC pad** near an exterior face so you can present cards to it; **EMF probe**
   on a short flexible lead so you can sweep surfaces.
5. **Cooling:** vent holes near the cooler; never airtight.
6. **Strain-relief** the screen ribbon and all jumpers (zip ties / dab of hot
   glue) so the lid doesn't tug them.
7. **Charge port:** route the UPS HAT's USB-C to a case edge.

---

# 18. STEP 12 — UPDATING, TUNING & PRECISION

### Update code
```bash
cd ~/sentry
git pull
source .venv/bin/activate
pip install -r requirements.txt
```

### Update system (monthly)
```bash
sudo apt update && sudo apt full-upgrade -y && sudo reboot
```

### Confirm it catches the right devices (after any change)
- Wi-Fi: names a known camera correctly?
- Bluetooth: AirTag flags as tracker → "following" after a minute?
- RF: key fob makes a spike in the right band?
- Thermal: warm hand shows a warm spot?
- NFC: a card near the pad reads its type?

### Precision tuning (one change at a time, re-test, commit)
- **RF sensitivity:** `sensors/rf.py` → `PEAK_DB_OVER_FLOOR` (raise = fewer false
  alarms; lower = catch weaker).
- **Add RF band:** `rf.py` → `BANDS` → `(low, high, "name", "category",
  "severity", "note")`.
- **Add camera brand:** `sensors/wifi.py` → `CAMERA_OUIS` → `"aa:bb:cc":"Brand"`.
- **Tracker trigger:** `sensors/bluetooth.py` → `following = cnt >= 3`.
- **Thermal threshold / NFC sensitivity / EMF baseline:** in their sensor files
  once built — ask Claude Code to expose a tunable constant like the RF one.

### Let Claude Code do precision work
On the Pi or laptop, in the project: `claude`, then e.g. *"the thermal sensor
flags sunlit windows as threats — add a tunable temperature-over-ambient
threshold and default it to +3°C,"* or *"add Ring, Wyze, Nest, Arlo camera MAC
prefixes to wifi.py."*

### Save every good change
```bash
git add . && git commit -m "what changed" && git push
```

---

# 19. TROUBLESHOOTING

**19A — Pi won't power:** use the official 27W supply; reseat USB-C; try another
outlet.
**19B — Black screen:** reseat display ribbon both ends; check screen power; reboot.
**19C — No internet:** Section 9 — recheck Wi-Fi name/password/country, or use
Ethernet; `ping` to confirm.
**19D — RF "usb_claim_interface error":**
```bash
echo 'blacklist dvb_usb_rtl28xxu' | sudo tee /etc/modprobe.d/blacklist-rtl.conf
sudo reboot
```
**19E — A sensor missing from `i2cdetect`:** recheck that sensor's SDA/SCL (most
common: swapped) and power/ground; confirm I²C enabled + rebooted; reseat jumpers.
If two I²C sensors conflict, they may share an address — ask Claude Code to set one
to its alternate address.
**19F — Camera "no cameras":** ribbon orientation/seating; enable Camera in
raspi-config; reboot.
**19G — Mic not listed by `arecord -l`:** try another USB port; some mics need
`libportaudio2` (installed in Step 5).
**19H — SENTRY won't start:** read the last error line; usually a missing package →
`pip install -r requirements.txt` in the active venv. Paste the error to Claude
Code.
**19I — Kiosk didn't start:** replace `YOURUSER` in both files; `chmod +x start.sh`.
**19J — A part gets hot/smells:** unplug immediately — usually reversed
power/ground. Recheck against diagrams. Parts are cheap to replace.

---

## When this box is done
It scans radio, Wi-Fi, and Bluetooth like the laptop — and adds heat, lenses, NFC,
and fields to catch what radio can't, including silent recording devices. Build it
one sensor at a time, test each, tune with Claude Code, and commit your wins to
GitHub. That's a real, serious instrument you built and understand end to end.
