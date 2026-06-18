"""Real Wi-Fi detection — lists every nearby access point.

Scans nearby Wi-Fi APs and reports EACH one with its real SSID, BSSID, vendor
(from the MAC OUI), channel, band and signal. Flags likely cameras (camera
vendor OUI) and evil-twin APs (one SSID on multiple BSSIDs). Listen-only — no
injection, no attacks.

Honest hardware note: on Windows, `netsh` only sees what the OS/driver exposes,
and Windows gates Wi-Fi scan visibility behind Location. It also lists access
points, not connected client stations (that needs monitor mode — RTL-SDR/adapter
upgrade). When few networks are visible we say so plainly rather than pretending.
"""

from sentry_backend.sensor import Sensor, Detection
from sentry_backend import identify
import subprocess
import shutil
import re
import platform
import collections
import time
import ctypes


class WiFiSensor(Sensor):
    channel = "wifi"
    name = "Wi-Fi Scanner"

    def __init__(self):
        super().__init__()
        self._primed = False   # first forced scan needs a moment to populate

    def _trigger_wlan_scan(self):
        """Force a fresh Wi-Fi scan via the native WLAN API.

        Why this matters: Windows' `netsh wlan show networks` only reads a CACHE.
        For a connected, idle adapter that cache frequently holds just the AP
        you're joined to — which made SENTRY nearly blind to the real Wi-Fi
        neighbourhood (1 network instead of ~13). WlanScan asks the driver to do
        a real scan; results land in the cache a few seconds later. Best-effort,
        Windows-only, non-blocking: any failure just falls back to the cache.
        """
        if platform.system() != "Windows":
            return
        try:
            import ctypes.wintypes as wt

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wt.DWORD), ("Data2", wt.WORD),
                            ("Data3", wt.WORD), ("Data4", ctypes.c_ubyte * 8)]

            class IFINFO(ctypes.Structure):
                _fields_ = [("InterfaceGuid", GUID),
                            ("strInterfaceDescription", wt.WCHAR * 256),
                            ("isState", wt.DWORD)]

            class IFLIST(ctypes.Structure):
                _fields_ = [("dwNumberOfItems", wt.DWORD), ("dwIndex", wt.DWORD),
                            ("InterfaceInfo", IFINFO * 1)]

            wlan = ctypes.windll.wlanapi
            neg = wt.DWORD()
            h = wt.HANDLE()
            if wlan.WlanOpenHandle(2, None, ctypes.byref(neg), ctypes.byref(h)) != 0:
                return
            try:
                pl = ctypes.POINTER(IFLIST)()
                if wlan.WlanEnumInterfaces(h, None, ctypes.byref(pl)) == 0 \
                        and pl.contents.dwNumberOfItems:
                    guid = pl.contents.InterfaceInfo[0].InterfaceGuid
                    wlan.WlanScan(h, ctypes.byref(guid), None, None, None)
            finally:
                wlan.WlanCloseHandle(h, None)
        except Exception:
            pass

    def available(self) -> bool:
        if platform.system() == "Windows":
            return shutil.which("netsh") is not None
        return shutil.which("nmcli") is not None or shutil.which("iw") is not None

    # ---- platform scanners: return list of AP dicts ------------------------
    def _scan_netsh(self):
        # errors="replace": an SSID can contain bytes that aren't valid in the
        # console's code page (e.g. 0x81 in cp1252). Without this, the decode
        # raises UnicodeDecodeError inside subprocess's reader thread and the
        # whole scan dies. Replacing bad bytes with � keeps the sensor alive;
        # BSSID/signal/channel are ASCII so parsing is unaffected.
        out = subprocess.run(
            ["netsh", "wlan", "show", "networks", "mode=bssid"],
            capture_output=True, text=True, errors="replace", timeout=15).stdout
        aps = []
        ssid = ""
        cur = None
        for raw in out.splitlines():
            s = raw.strip()
            m = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", s)
            if m:
                ssid = m.group(1).strip()
                continue
            m = re.match(r"^BSSID\s+\d+\s*:\s*([0-9A-Fa-f:]{17})", s)
            if m:
                cur = {"ssid": ssid, "bssid": m.group(1).lower(),
                       "pct": None, "chan": "", "band": "", "radio": ""}
                aps.append(cur)
                continue
            if cur is not None:
                m = re.match(r"^Signal\s*:\s*(\d+)\s*%", s)
                if m:
                    cur["pct"] = int(m.group(1)); continue
                m = re.match(r"^Channel\s*:\s*(\d+)", s)
                if m:
                    cur["chan"] = m.group(1); continue
                m = re.match(r"^Band\s*:\s*(.*)$", s)
                if m:
                    cur["band"] = m.group(1).strip(); continue
                m = re.match(r"^Radio type\s*:\s*(.*)$", s)
                if m:
                    cur["radio"] = m.group(1).strip(); continue
            # colocated radios: "BSSID: aa:bb:.., Band: 5 GHz, Channel: 44"
            m = re.match(r"^BSSID:\s*([0-9A-Fa-f:]{17}),\s*Band:\s*([^,]+),\s*Channel:\s*(\d+)", s)
            if m:
                aps.append({"ssid": ssid, "bssid": m.group(1).lower(),
                            "pct": cur["pct"] if cur else None,
                            "chan": m.group(3), "band": m.group(2).strip(), "radio": ""})
        return aps

    def _scan_nmcli(self):
        out = subprocess.run(
            ["nmcli", "-t", "-f", "BSSID,SSID,CHAN,SIGNAL,FREQ", "device", "wifi",
             "list", "--rescan", "auto"],
            capture_output=True, text=True, errors="replace", timeout=20).stdout
        aps = []
        for line in out.strip().splitlines():
            parts = line.replace("\\:", "§").split(":")
            if len(parts) < 4:
                continue
            bssid = parts[0].replace("§", ":").lower()
            aps.append({"ssid": parts[1].replace("§", ":"), "bssid": bssid,
                        "pct": int(parts[3]) if parts[3].isdigit() else None,
                        "chan": parts[2], "band": "", "radio": ""})
        return aps

    def scan(self):
        try:
            if platform.system() == "Windows":
                # Trigger a real scan, then read the cache. WlanScan is async, so
                # a given read returns the PREVIOUS trigger's results (≤ the scan
                # interval old) — except the very first time, where we wait once
                # for it to populate so the user isn't briefly shown "1 network".
                self._trigger_wlan_scan()
                if not self._primed:
                    time.sleep(4.0)
                    self._primed = True
                aps = self._scan_netsh()
            else:
                aps = self._scan_nmcli()
        except Exception as e:
            self._error = str(e)
            return []

        # evil-twin: same (non-empty) SSID on BSSIDs from DIFFERENT hardware.
        # A normal router exposes several radios (2.4/5/6 GHz) sharing one OUI —
        # that's NOT an evil-twin. Only distinct OUIs (different makers) count.
        by_ssid = collections.defaultdict(set)
        for ap in aps:
            if ap["ssid"]:
                by_ssid[ap["ssid"]].add(":".join(ap["bssid"].split(":")[:3]))

        def is_evil_twin(ssid):
            return bool(ssid) and len(by_ssid.get(ssid, set())) > 1

        # honest coverage note: Windows commonly shows only the connected AP
        distinct_ssids = len({a["ssid"] for a in aps if a["ssid"]})
        if len(aps) <= 1 or distinct_ssids <= 1:
            self._note = ("Only %d Wi-Fi AP(s) visible — Windows limits Wi-Fi scan "
                          "results (enable Location for desktop apps to see neighbors). "
                          "Lists APs only, not client devices." % len(aps))
        else:
            self._note = "Lists access points only (client stations need monitor mode)."

        dets = []
        seen = set()
        for ap in aps:
            bssid = ap["bssid"]
            if bssid in seen:
                continue
            seen.add(bssid)
            pct = ap["pct"]
            rssi = round(pct / 2 - 100) if isinstance(pct, int) else None  # %→approx dBm
            vendor, rand = identify.vendor_for_mac(bssid)
            ssid = ap["ssid"] or "(hidden / no SSID)"
            chan = ap["chan"] or "?"
            band = ap["band"] or "2.4/5 GHz"
            ident_txt = f"ch {chan} · {band}" + (f" · {pct}%" if pct is not None else "")
            band_l = band.lower()
            method = ("Wi-Fi 6 GHz" if "6" in band_l else "Wi-Fi 5 GHz" if "5" in band_l
                      else "Wi-Fi 2.4 GHz" if "2.4" in band_l else "Wi-Fi")
            info = identify.identify(mac=bssid, ssid=ap["ssid"], vendor=vendor, seen_via=method)
            is_evil = is_evil_twin(ap["ssid"])

            if info["is_camera"]:
                sev, cat = "alert", "camera"
                kind = info["type"]
                surveil = "Video of its field of view, plus on-board mic"
                cap = "Video + audio, streamed/recorded over Wi-Fi"
                now = "On Wi-Fi — likely streaming or recording"
            elif is_evil:
                sev, cat = "alert", "wifi attack"
                kind = "Evil-twin access point"
                surveil = "Your traffic — if you connect"
                cap = "Unencrypted traffic, login pages, DNS if joined"
                now = "Waiting for a device to join"
            else:
                sev, cat = "notable", "wifi ap"
                kind = (vendor + " Wi-Fi AP") if vendor else "Wi-Fi access point"
                surveil = "Nothing by itself — it's an access point"
                cap = "Carries traffic for devices that join it"
                now = "Broadcasting a Wi-Fi network"

            ev = list(info["evidence"])
            if is_evil:
                ev.append(f'SSID "{ap["ssid"]}" on {len(by_ssid[ap["ssid"]])} different-vendor BSSIDs (evil-twin)')

            dets.append(Detection(
                kind=kind, channel="wifi", severity=sev, category=cat,
                maker=identify.vendor_label(bssid),
                model=ssid, mac=bssid, ident=ident_txt,
                bandtxt=band,
                behaviortxt=f'SSID "{ssid}" · {band} ch {chan}'
                            + (f' · signal {pct}%' if pct is not None else "")
                            + (" · Windows reports signal as a %, mapped to ~dBm" if pct is not None else ""),
                surveilling=surveil, cancapture=cap, capturingnow=now,
                confidence=info["confidence"], rssi=rssi,
                device_type=kind, method=method, evidence=ev,
            ))
        return dets
