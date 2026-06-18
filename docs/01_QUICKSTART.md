# 01 — Quick Start (Run SENTRY on a laptop in minutes)

Get the working version running. Works on Windows, Mac, or Linux with built-in
Wi-Fi + Bluetooth — nothing to buy.

## You need
- A laptop (Windows/Mac/Linux)
- Python 3 — from https://python.org (during install, tick "Add Python to PATH")

## Get the code
Download/clone the repo and open its folder:
```
git clone https://github.com/Rfisher55/sentry.git
cd sentry
```
(Or download the ZIP from GitHub and extract it.)

## Run it

**Windows — easiest:** double-click `START_SENTRY.bat`. It sets up everything the
first time and opens the station in your browser.

**Any OS — command line:**
```
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m sentry_backend.server
```
Then open **http://localhost:8000**.

## What you'll see
- The black window shows which sensors came online (Wi-Fi, Bluetooth, network).
- The browser shows the SENTRY interface with live detections.
- On first Bluetooth scan, allow the OS permission prompt or BLE sees nothing.

## Stop it
Close the window (or Ctrl+C in the terminal).

## View it on your phone (same Wi-Fi)
The server listens on your network. Find your laptop's local IP (the startup
banner prints a `Phone:` URL), then on your phone (same Wi-Fi) open
`http://<that-ip>:8000`. The laptop does the scanning; the phone is a live viewer.
Allow the firewall prompt the first time.

## Next
- Develop it + back up to GitHub → **02_LAPTOP_CLAUDECODE_GITHUB.md**
- Add radio (RF) and go deeper → **03_LAPTOP_FULL_RF_WIFI_BT.md**
