# 01 — Quick Start (run SENTRY on a laptop)

Get the working version running with **zero hardware** — built-in Wi-Fi + Bluetooth
do real detection. Works on Windows, Mac, and Linux. ~10 minutes.

> New to all this? This is the friendly step-by-step. The repo's main
> **[README](../README.md)** has the same steps plus a troubleshooting table and the
> hardware tiers — either one gets you running.

---

## What you need
- A laptop (Windows, Mac, or Linux).
- **Python 3** (free) — the engine SENTRY runs on. Installed in Step 1 below.
- That's it. No dongle, no antenna, nothing to buy to start.

---

## Step 1 — Install Python (one time)
1. Go to **https://www.python.org/downloads/** and click the big **Download Python** button.
2. Open the downloaded installer.
3. 🚨 **On the very first screen, tick the box "Add python.exe to PATH"** (it's at the
   bottom), **then** click **Install Now**.
   - If you skip that checkbox, SENTRY can't find Python and won't start. Forgot?
     Just run the installer again and tick it.
4. Click **Close** when it's done.

*(Mac: you can also use `brew install python`. Linux: Python 3 is usually already there.)*

---

## Step 2 — Get SENTRY
**Easy way (no Git needed):**
1. On the GitHub page, click the green **`< > Code`** button → **Download ZIP**.
2. Find `sentry-main.zip` (usually in **Downloads**), **right-click → Extract All → Extract**.
3. Open the extracted folder until you can see the files (you'll spot `START_SENTRY.bat`).

**If you have Git:**
```
git clone https://github.com/Rfisher55/sentry.git
cd sentry
```

---

## Step 3 — Run it

### Windows (easiest)
**Double-click `START_SENTRY.bat`.**
- A black window opens and installs what it needs the first time (about a minute).
- Your browser opens automatically to **http://localhost:8000**.
- If "Windows protected your PC" appears, click **More info → Run anyway** (it's an
  unsigned `.bat`; all the code is right here in the open).

### Mac / Linux (Terminal)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m sentry_backend.server
```
Then open **http://localhost:8000** in your browser.

---

## What you'll see
- The **black window** lists which sensors came online (Wi-Fi, Bluetooth, network).
- The **browser** shows the live SENTRY interface with real detections around you.
- The first Bluetooth scan may pop an **OS permission prompt** — allow it, or BLE
  sees nothing.
- No sensors available at all? It runs in **demo mode** with sample data so you can
  still look around.

## Stop it
Close the black window (or press **Ctrl+C** in the terminal).

---

## Two rules so it behaves
- **Run only ONE copy of SENTRY at a time.** Don't double-click the `.bat` twice.
- If you later add the RTL-SDR radio dongle, **close any other SDR app** (SDR#/HDSDR)
  — the tuner can only belong to one program at once.

## Common snags
| Problem | Fix |
|---------|-----|
| Black window flashes and vanishes / "python not recognized" | Python isn't on PATH — re-run its installer and tick **Add python.exe to PATH**. |
| Browser says it can't reach localhost | Make sure the black window is still open; open **http://localhost:8000** yourself. |
| Everything says **DEMO** | The server (black window) isn't running — start it. |
| Wi-Fi shows nothing (Windows) | Turn **Location** on (Settings → Privacy → Location) — Windows needs it for Wi-Fi scans. |

---

## View it on your phone (same Wi-Fi)
The startup banner in the black window prints a **`Phone: http://<your-ip>:8000`**
line. On your phone (same Wi-Fi), open that address — the laptop does the scanning,
the phone is a live viewer. Allow the firewall prompt the first time.
*(Only do this on your own trusted Wi-Fi.)*

---

## Next steps
- **Add radio (RF) detection** with a ~$45 dongle, and go deeper →
  **[03_LAPTOP_FULL_RF_WIFI_BT.md](03_LAPTOP_FULL_RF_WIFI_BT.md)**
- **Plan the full build-out** (USB add-ons, every feature) →
  **[04_LAPTOP_BUILDOUT_PLAN.md](04_LAPTOP_BUILDOUT_PLAN.md)**
- **Step up to the Raspberry Pi field unit** →
  **[05_PI_ULTIMATE_BOX.md](05_PI_ULTIMATE_BOX.md)**
- Back to the **[full docs index](00_START_HERE.md)**.
