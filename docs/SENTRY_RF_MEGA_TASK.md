# SENTRY — Four-Task RF + Detection Build (paste into Claude Code)

Paste this whole thing into Claude Code. It's four tasks; do them in order, each as
separate verified commits, real data only — no fake/generated spectrum, audio, or
signals. Hardware: Nooelec NESDR Mini (RTL2832U/R820T, real range ~25MHz–1.7GHz),
plus the laptop's built-in Wi-Fi and Bluetooth.

---

```
SENTRY four-task build. Do them in order, each as its own verified commit. REAL
DATA ONLY - never fake, generate, or simulate spectrum, audio, or signal values.
My hardware: Nooelec NESDR Mini (RTL2832U/R820T, ~25MHz-1.7GHz), built-in Wi-Fi,
built-in Bluetooth. Be honest in the UI about what each can and can't do.

========================================================================
TASK 1 - FIX ALL SIGNAL DISPLAYS (they show flat static bars)
========================================================================
Every signal reading across ALL channels shows a flat, static bar instead of live
data. Wi-Fi shows "50 dBm" as a straight bar with no movement; Bluetooth shows
"85 dBm" flat across, totally static. Real RSSI fluctuates constantly - a flat
line means it's not reading live.
- Go through EVERY signal display (Wi-Fi, Bluetooth, RF, network, every channel
  and per-device view). Confirm each value is the REAL current signal from the
  actual scan, updating as new readings arrive.
- Show the signal changing over time (a live trace/history), not one frozen number
  drawn flat.
- Trace each value (sensor -> Detection -> UI); fix every place a single static
  value is drawn as a flat bar.
- Also fix the RF spectrum flat-line: it must plot the REAL live spectrum from the
  dongle.
- PROVE IT: show one device's signal changing across several consecutive scans and
  confirm the UI moves with it. (Real RSSI is jittery - that's correct.)

========================================================================
TASK 2 - FULL SPECTRUM/WATERFALL + LISTENING (everything the tuner can hear)
========================================================================
Build a real SDR receiver into SENTRY for everything within the tuner's range:
- Live SPECTRUM + scrolling WATERFALL like SDR#, real signal strength across the
  tuned range; let me set center frequency and span anywhere in ~25MHz-1.7GHz.
- LISTENING: tune any in-range frequency and HEAR demodulated audio, with a mode
  selector (WFM, NFM, AM, and LSB/USB if feasible) for FM broadcast, air band,
  ham, FRS/GMRS, weather, and any analog signal in range.
- Frequency input + quick presets (FM 88-108 WFM, air 118-137 AM, weather 162 NFM,
  FRS/GMRS 462/467 NFM, ham 144/440 NFM).
- TEST with FM ~100 MHz to confirm real audio.
HONEST LIMITS in the UI: tunes ~25MHz-1.7GHz only - CANNOT receive above 1.7GHz
(no 2.4GHz Wi-Fi/Bluetooth audio - needs a HackRF); CANNOT decode encrypted or
digital (DMR/P25); must NOT tune cellular bands. Analog/unencrypted only.

========================================================================
TASK 3 - "SCANNER" TAB (sweep and discover what's out there)
========================================================================
Add a new Scanner tab - a classic radio-scanner sweep experience:
- SWEEP MODE: automatically step through a frequency range, stopping when it
  detects activity (signal above a squelch threshold), so I can discover active
  signals without knowing the frequency. Resume sweeping (manually or auto after a
  few seconds) to find the next.
- BAND PRESETS: quick-scan buttons - FM, air, weather, FRS/GMRS, ham 2m, ham 70cm,
  and a full-range sweep. Each sets the right range + mode automatically.
- LISTEN ON STOP: when it stops on activity, play the live audio, show frequency +
  signal strength, let me lock on or skip to keep scanning.
- ACTIVITY LOG: list active frequencies found during a sweep, with strength + time.
- ADJUSTABLE SQUELCH: control for how strong a signal must be to stop the sweep.
- TEST by sweeping the FM band and confirming it stops on and plays real stations.
Note: a single dongle steps through frequencies sequentially (not simultaneous) -
that's normal scanner behavior; make the stepping fast and smooth.

========================================================================
TASK 4 - UNIFIED "SEE EVERYTHING" EXPLORER + decode the short-range stuff
========================================================================
I want one place to read and look at EVERYTHING around me across all my sensors,
and to decode the common short-range signals where it's legal and feasible.
- UNIFIED EXPLORER VIEW: a single screen that shows, live and together, everything
  detected across ALL sources - RF signals (from the dongle), Wi-Fi networks/
  devices, Bluetooth/BLE devices, and network/LAN devices - each clearly tagged by
  source, with its real signal, identity/classification, and live updating. One
  "what's around me right now" dashboard.
- KEY FOBS / ISM DEVICES: many key fobs, doorbells, TPMS, remotes, and cheap
  sensors transmit on 315/433/868/915 MHz - within the dongle's range. Detect and
  display these bursts in the RF view: show frequency, signal, timing, and label
  the likely type (e.g. "315/433 MHz remote/fob burst"). DETECT and CHARACTERIZE
  only - do NOT decode, store, replay, or clone any access-control/rolling code or
  any signal that could be used to operate someone's device. Presence/timing/
  frequency only.
- BLE DEEP READ: for Bluetooth devices, surface everything they openly advertise -
  device type, services/appearance, vendor, RSSI - to identify what each thing is
  (phone, watch, earbuds, tag, TV, etc.).
- WI-FI DEEP READ: surface everything Wi-Fi openly broadcasts - SSID, BSSID,
  vendor, channel, band, signal, and (if a monitor-mode adapter is ever added)
  client devices. For now use what built-in Wi-Fi can see.
- DURING THIS TASK also fix the unrelated cp1252 UnicodeDecodeError in the Wi-Fi/
  network sensor's subprocess reader (decode output safely so an unusual network
  name can't crash it).
HONEST LIMITS in the UI: receive/observe/identify only. No decoding encrypted or
rolling-code signals, no replay/clone/transmit, no cellular. Anything above 1.7GHz
(2.4GHz Wi-Fi/BT radio-level, drones) needs a HackRF and is out of range for now -
label it as such, don't fake it.

========================================================================
WHEN ALL FOUR ARE DONE
========================================================================
Summarize what you built per task. Verify with real signals: show the FM peak +
audio, a live-changing Wi-Fi/BLE signal, the scanner stopping on a real station,
and the unified explorer showing real RF + Wi-Fi + BLE + network together. Then
commit and push everything to GitHub and confirm local and remote main are in sync.
```

---

## Notes
- **Task 4 is the "see everything" dashboard** you described - one screen pulling
  RF + Wi-Fi + Bluetooth + network together, plus detecting key-fob/ISM bursts
  (315/433 MHz) which ARE in your dongle's range.
- **Important honest line baked in:** it DETECTS and characterizes key fobs (that
  one's transmitting, on this frequency, this type) but does NOT decode, clone, or
  replay them. Capturing/replaying a fob's rolling code to operate a car/garage is
  illegal and I won't have it build that. Presence and analysis only - which is the
  legitimate counter-surveillance use.
- **The 1.7GHz ceiling is real:** "everything" = everything analog/unencrypted from
  ~25MHz to 1.7GHz, plus all your Wi-Fi/BT/network. The 2.4/5.8GHz world (modern
  Wi-Fi cameras, BT audio at radio level, drones) needs a HackRF - that's the next
  hardware step when you want to truly cover "everything."
- This is a big build - let it run, approve prompts, keep SDR# closed while it
  tests, and confirm each task with real signals before trusting it.
