"""Threat Defense — DETECT-ONLY awareness of common attack tools, so SENTRY can
warn you that one may be near or in use against you. Inspired by what tools like
Flipper Zero (RF replay/clone, BadUSB) and autonomous pentest frameworks can do —
but SENTRY only *detects and advises*. It never transmits, replays, clones,
emulates, exploits, or attacks anything (and the RTL-SDR is receive-only).
"""

import json
import subprocess


# A Flipper Zero advertises over BLE; stock firmware names it "Flipper <name>".
def is_flipper(name):
    n = (name or "").lower()
    return "flipper" in n


# Fob / remote / ISM bands a Flipper-class device transmits on (MHz). SENTRY can
# only RECEIVE here — it watches for abnormal repeated bursts (a replay/brute-
# force/jam signature), never sends.
FOB_BANDS = [(300.0, 348.0, "315 MHz remotes/TPMS"),
             (387.0, 464.0, "433 MHz fobs/sensors"),
             (775.0, 928.0, "868/915 MHz remotes/ISM")]


def band_for_freq(mhz):
    for lo, hi, label in FOB_BANDS:
        if lo <= mhz <= hi:
            return label
    return None


def hid_audit():
    """List currently-present HID input devices (keyboards/mice/HID). A BadUSB
    ('rubber ducky') attack appears as a NEWLY-attached keyboard — snapshot this,
    and a new keyboard you didn't plug in is the tell. Read-only enumeration."""
    cmd = ["powershell", "-NoProfile", "-Command",
           "Get-PnpDevice -PresentOnly -Class Keyboard,Mouse,HIDClass "
           "-ErrorAction SilentlyContinue | Select-Object FriendlyName,InstanceId,Class,Status "
           "| ConvertTo-Json -Compress"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                             timeout=15).stdout.strip()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if not out:
        return {"ok": True, "devices": [], "keyboards": 0}
    try:
        data = json.loads(out)
    except Exception:
        return {"ok": False, "error": "could not parse device list"}
    if isinstance(data, dict):
        data = [data]
    devices = []
    for d in data:
        fn = (d.get("FriendlyName") or "").strip()
        if not fn:
            continue
        devices.append({"name": fn, "id": d.get("InstanceId", ""),
                        "class": d.get("Class", ""), "status": d.get("Status", "")})
    keyboards = [d for d in devices if d["class"] == "Keyboard"]
    return {"ok": True, "devices": devices, "keyboards": len(keyboards),
            "note": "A BadUSB attack registers as a new keyboard. If a keyboard appears "
                    "here that you didn't plug in, unplug it and investigate."}
