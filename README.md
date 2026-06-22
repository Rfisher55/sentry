# SENTRY — Personal Counter-Surveillance Station

**SENTRY scans the Wi-Fi, Bluetooth, radio, and network world around you and flags
anything that might be watching, listening to, or tracking you** — hidden cameras,
AirTag-class trackers, rogue Wi-Fi, drones, and unknown transmitters — then helps
you find it. It runs **free on a normal laptop** and grows all the way up to a
portable **Raspberry Pi field unit** in a Pelican case.

> **Detect-only.** SENTRY only *receives and analyzes* signals devices already
> broadcast. It never jams, clones, replays, transmits, attacks, or decodes anyone's
> private content. Receiving/analyzing is legal; transmitting on restricted bands is
> not — SENTRY does not transmit.

It catches the common, real threats people actually face. It is **not** a guarantee
against determined professional surveillance — see [Honest limits](#honest-limits).

---

# 🚀 Just want to try it? (Windows — ~10 minutes, free)

You need **two free downloads**: Python (the engine) and SENTRY (this project).
No hardware required — Wi-Fi and Bluetooth detection work on any laptop.

### Step 1 — Install Python (one-time)
1. Go to **https://www.python.org/downloads/** and click the big **"Download Python"** button.
2. Run the installer. **IMPORTANT:** on the first screen, **tick the box that says
   "Add python.exe to PATH"** (bottom of the window), *then* click **Install Now**.
   - ⚠️ If you skip that checkbox, SENTRY won't start. If you forgot, just run the
     installer again and tick it.
3. When it finishes, click **Close**.

### Step 2 — Download SENTRY
**Option A — the easy way (ZIP):**
1. On this GitHub page, click the green **`< > Code`** button → **Download ZIP**.
2. Find the downloaded `sentry-main.zip` (usually in your **Downloads** folder),
   **right-click → Extract All → Extract**.

**Option B — if you have Git:**
```
git clone https://github.com/Rfisher55/sentry.git
```

### Step 3 — Run it
1. Open the extracted folder until you see the files (you'll see `START_SENTRY.bat`).
2. **Double-click `START_SENTRY.bat`.**
   - A black window opens and sets everything up the first time (takes a minute).
   - Your web browser opens automatically to **http://localhost:8000**.
   - If a blue "Windows protected your PC" box appears, click **More info → Run anyway**
     (it's just an unsigned `.bat`; the code is all here in the open).
3. That's it — you're watching live Wi-Fi + Bluetooth detections.
4. **To stop:** close the black window.

> **Only ever run ONE copy at a time**, and close any other SDR app (SDR#/HDSDR) —
> the radio dongle can only belong to one program at once.

---

# 🍎 Mac / 🐧 Linux

There's no `.bat`, so use the command line (Terminal):
```bash
# 1. get the code
git clone https://github.com/Rfisher55/sentry.git
cd sentry

# 2. make a private environment + install the dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. run it
python3 -m sentry_backend.server
```
Then open **http://localhost:8000** in your browser.
(On Linux, Wi-Fi scanning uses `nmcli`; on macOS some scans need Location/Bluetooth
permission — the app tells you when something's blocked.)

---

# 👀 What you'll see

When it's running, open **http://localhost:8000**. The tabs:

| Tab | What it does |
|-----|--------------|
| **Overview** | The live "what's around me" dashboard — every Wi-Fi / Bluetooth / radio / network device, tagged by source, with a **Radar / Map** view (distance only — see below). |
| **Network** | Scans devices on *your own* network, flags cameras / new / unknown devices and anything "phoning home." (Deeper scans use nmap + Wireshark — optional, see below.) |
| **Alerts** | The ranked "who's watching you" list + a **Hotel/Airbnb sweep mode** (baseline on arrival, flag anything new) + a timestamped evidence log you can export. |
| **Listening** | Tune and listen to legal analog radio (FM / air / weather / ham / FRS) — needs the RTL-SDR dongle. Hobby/learning, not threat detection. |
| **Sensors & Toolkit** | Every sensor/tool, honestly badged **LIVE** / **NEEDS RTL-SDR** / **NEEDS ANTENNA** / **NOT BUILT YET**. The hardware-only ones are tucked in a "Future sensors" group. |
| **Drones / Tools** | Detects drones that broadcast (Wi-Fi-linked + Remote ID names). |

**No sensors at all?** The interface still runs in **demo mode** with realistic
sample data so you can see how it works.

---

# 🧰 Hardware tiers — start free, grow as far as you want

| Tier | Cost | What you add | What it unlocks |
|------|------|--------------|-----------------|
| **1. Laptop only** | **Free** | nothing | Wi-Fi cameras/rogue-APs, Bluetooth trackers (AirTags etc.), own-network scan, acoustic/ultrasonic (laptop mic), drone names |
| **2. + RTL-SDR dongle** | **~$45** | A [Nooelec NESDR / RTL-SDR Blog V4](https://www.rtl-sdr.com/) USB stick | Live radio spectrum 25 MHz–1.7 GHz, RF baseline/anomaly, key-fob/ISM bursts (315/433/868/915 MHz), scanner, listening |
| **3. + optional installs** | Free | [nmap](https://nmap.org/download.html) + [Wireshark/Npcap](https://www.wireshark.org/download.html) | Full Network tab: port/service scans, vulnerability awareness, live traffic capture, phone-home map |
| **4. + directional antenna** | ~$35 | A yagi/log-periodic + monitor-mode Wi-Fi adapter | Direction-finding (bearing), Wi-Fi-airspace recon |
| **5. Raspberry Pi field unit** | <$400 total | Pi + thermal/lens/NFC/EMF sensors, Pelican case | The physical sensors a laptop can't do — see the docs below |

The UI **honestly tells you** what each tool needs — nothing pretends to work when
it can't. Plug the RTL-SDR in mid-session and RF lights up automatically.

---

# 📚 The full build journey — laptop → Raspberry Pi (everything explained)

The **[`docs/`](docs/)** folder is a complete, step-by-step build guide from a free
laptop setup all the way to a portable Pi unit. **New here? Open
[`docs/00_START_HERE.md`](docs/00_START_HERE.md)** — it's the index for everything.

| Stage | Docs |
|-------|------|
| **Run it on a laptop** (free) | [`01_QUICKSTART`](docs/01_QUICKSTART.md) · [`02_LAPTOP_CLAUDECODE_GITHUB`](docs/02_LAPTOP_CLAUDECODE_GITHUB.md) · [`03_LAPTOP_FULL_RF_WIFI_BT`](docs/03_LAPTOP_FULL_RF_WIFI_BT.md) |
| **Build out the laptop** (USB add-ons) | [`04_LAPTOP_BUILDOUT_PLAN`](docs/04_LAPTOP_BUILDOUT_PLAN.md) · [`08_FULL_FEATURE_CATALOG`](docs/08_FULL_FEATURE_CATALOG.md) |
| **Step up to the Pi "ultimate box"** | [`05_PI_ULTIMATE_BOX`](docs/05_PI_ULTIMATE_BOX.md) · [`11_PHASES_6_7_8`](docs/11_PHASES_6_7_8.md) |
| **Reference** (parts, prices, roadmap) | [`06_HARDWARE`](docs/06_HARDWARE.md) · [`09_SHOPPING_LIST_PI_BOX`](docs/09_SHOPPING_LIST_PI_BOX.md) · [`10_SHOPPING_FROM_SCRATCH`](docs/10_SHOPPING_FROM_SCRATCH.md) · [`07_ROADMAP`](docs/07_ROADMAP.md) · [`12_MOVING_GEAR_LAPTOP_TO_PI`](docs/12_MOVING_GEAR_LAPTOP_TO_PI.md) |

Honest throughout: the laptop phases (RF / Wi-Fi / Bluetooth / network) are fully
laptop-doable; the physical sensors (thermal, lens-finder, NFC, EMF) genuinely need
the Pi's GPIO pins and are clearly marked as such.

---

# 🩹 Troubleshooting (the common snags)

| Problem | Fix |
|---------|-----|
| **`START_SENTRY.bat` flashes and closes** / "python not recognized" | Python isn't on PATH. Re-run the Python installer and **tick "Add python.exe to PATH."** |
| **Page won't load / "can't reach localhost"** | Make sure the black window is still open. Open **http://localhost:8000** manually. |
| **RF says "detected but in use" or "needs a dongle"** | The tuner is single-app. Close any other SENTRY window and any SDR app (SDR#/HDSDR), then re-scan. Only run **one** SENTRY. |
| **RF stays offline with the dongle plugged in** | On Windows the RTL-SDR needs the **WinUSB driver** — install it with [Zadig](https://zadig.akeo.ie/) (pick the RTL bulk interface → WinUSB). |
| **Wi-Fi shows nothing on Windows** | Windows requires **Location** turned on for Wi-Fi scanning (Settings → Privacy → Location). |
| **Everything shows "DEMO"** | The backend isn't connected — the page is open but the server (black window) isn't running. Start it. |
| **Want it on your phone** | The black window prints a `http://<your-ip>:8000` link — open that on the same Wi-Fi. (Only on your *own trusted* Wi-Fi.) |

---

# 🔒 Honest limits

- **Silent devices** — a camera/recorder saving to a card with its radio **off**
  transmits nothing, so Wi-Fi/BT/RF can't see it. Those need a physical search, a
  lens-finder, or thermal (the later Pi stages).
- **Cellular / IMSI** is the weakest channel on cheap hardware — treat any cellular
  hint as "investigate," not proof.
- **Direction** isn't shown without a directional antenna — SENTRY honestly gives
  **distance only** (rings), never a fake bearing.
- **Not a professional sweep.** This is a capable learning/hobby instrument. If you
  believe you're under serious targeted surveillance, get a professional TSCM sweep
  and contact authorities.

---

# ⚖️ Legal

Operate within your local laws. SENTRY only **receives and analyzes** signals that
devices openly broadcast, and helps you find devices in your own space. The Network
tab actively probes **your own** network (it says so). It does not decode private
content and does not transmit to interfere with any device. Don't point the network
tools at networks you don't own or aren't authorized to test.

---

*Built as a learning + demonstration project. Detect-only. Be honest about limits.*
