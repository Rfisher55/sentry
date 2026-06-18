"""SENTRY backend server — runs the real sensors and streams live detections.

Brings up every sensor (each degrades gracefully if its hardware is absent),
scans on a loop, fuses the results, and serves them to the UI over a local
WebSocket. The UI connects to ws://localhost:8765; if nothing is there, the UI
falls back to its built-in demo data, so it always works.

Run:  python3 -m backend.server
"""

import asyncio
import base64
import json
import time
import os
import re
import threading
import http.server
import socketserver
import webbrowser

try:
    import websockets
except Exception:
    websockets = None

UI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")
HTTP_PORT = 8000


def lan_ip():
    """Best-guess LAN IP (the address other devices on your Wi-Fi use to reach
    this laptop). No packets are sent — connect() just picks the outbound route."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def serve_ui():
    """Serve the UI over HTTP so a browser can load it locally."""
    if not os.path.isdir(UI_DIR):
        return
    # No-store so a phone/laptop browser never serves a STALE cached index.html
    # after we change the UI — otherwise old bugs appear "fixed on laptop but not
    # on phone" simply because the phone cached an older page.
    class _NoCacheHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            super().end_headers()
    handler = lambda *a, **k: _NoCacheHandler(*a, directory=UI_DIR, **k)
    try:
        # Threaded: each connection gets its own thread. A single-threaded server
        # blocks forever on a browser's idle speculative/keep-alive connection,
        # which would hang every page refresh after the first load.
        # 0.0.0.0 = listen on ALL interfaces so other devices on your Wi-Fi
        # (e.g. your phone) can load the UI at http://<laptop-LAN-IP>:8000
        httpd = socketserver.ThreadingTCPServer(("0.0.0.0", HTTP_PORT), handler)
        httpd.daemon_threads = True
        httpd.allow_reuse_address = True
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print(f"  UI:      http://localhost:{HTTP_PORT}   (this laptop)")
        ip = lan_ip()
        if ip:
            print(f"  Phone:   http://{ip}:{HTTP_PORT}   (open this on your phone, same Wi-Fi)")
    except OSError:
        print(f"  (port {HTTP_PORT} busy — open ui/index.html manually)")

from sentry_backend.sensors.rf import RFSensor
from sentry_backend.sensors.wifi import WiFiSensor
from sentry_backend.sensors.bluetooth import BLESensor
from sentry_backend.sensors.network import NetworkSensor
from sentry_backend import identify
from sentry_backend import inspector


def _is_private_ip(ip):
    """Only addresses on a private/LAN range may be scanned — your own network.
    Refuses public/internet addresses outright (legal guardrail)."""
    try:
        parts = [int(x) for x in str(ip).split(".")]
    except Exception:
        return False
    if len(parts) != 4 or any(p < 0 or p > 255 for p in parts):
        return False
    a, b = parts[0], parts[1]
    return (a == 10 or (a == 192 and b == 168) or (a == 172 and 16 <= b <= 31)
            or a == 127)


SENSORS = [RFSensor(), WiFiSensor(), BLESensor(), NetworkSensor()]

# How often we refresh + push the fused state. BLE and the LAN scanner read from
# instant caches, so we tick fast for a live feel; blocking sensors scan less
# often via SENSOR_INTERVAL below.
TICK_INTERVAL = 1.5
# Per-channel minimum seconds between actual scans. 0 = read every tick (the
# sensor self-throttles its own real work in a background thread).
SENSOR_INTERVAL = {"bluetooth": 0.0, "network": 0.0, "wifi": 8.0, "rf": 0.0}

# "New device" baseline: everything present in the first WARMUP seconds is the
# baseline; anything appearing later is flagged NEW (hotel/Airbnb workflow).
WARMUP_SECONDS = 25.0


def _counter_for(category):
    # minimal real counter-guidance (mirrors the UI's intent)
    base = {
        "camera": ["Get out of its line of sight.",
                   "If it's not yours: photograph it in place, don't dismantle, report it.",
                   "If it's your space: cut its power or block the lens."],
        "tracker": ["Separate from the item it may be hidden in (bag, jacket, vehicle).",
                    "Use your phone's tracker-detection to help pinpoint it.",
                    "If you suspect stalking, preserve it and contact authorities."],
        "audio bug": ["Stop sensitive conversations in this space.",
                      "Locate it, then photograph and report rather than destroy.",
                      "Sweep again after removal to confirm it's gone."],
        "wifi attack": ["Do NOT join the duplicate network.",
                        "Verify the real network name/BSSID with the venue.",
                        "Use cellular data or a VPN until clear."],
        "rogue tower": ["Treat calls/texts here as compromised.",
                        "Move away; note where signal strength drops.",
                        "Use encrypted apps; report if persistent."],
    }
    return base.get(category, ["Identify it up close.", "Locate it.", "Document before acting."])


class Fusion:
    """Combine sensor detections into the UI's device list, with STABLE ids.

    The id is derived from channel + MAC so the same physical device keeps the
    same id across scans — this is what lets the UI track one device as it moves
    (radar blip stays put, the open intel drawer keeps updating) instead of the
    list reshuffling every tick.
    """
    def _dedup_key(self, ui):
        """Key for collapsing PROVABLE duplicates. A BLE device that rotates its
        MAC but keeps its advertised NAME (model) is the same device — merge it.
        Trackers and anonymous/rotating beacons (no real advertised name) keep a
        unique key: passive BLE can't link randomized MACs, so we don't pretend
        to — that over-count is a protocol limit, not something to fake away."""
        model = (ui.get("model") or "").strip()
        named = bool(model) and model != "—"
        if ui.get("channel") == "bluetooth" and ui.get("category") != "tracker" and named:
            return ("ble-name", model.lower())
        mac = (ui.get("mac") or "").lower()
        if mac and mac != "—" and not identify.is_random_mac(mac):
            return ("mac", mac)
        return ("id", ui.get("id"))

    def build(self, all_dets):
        devices = []
        for i, d in enumerate(all_dets):
            ui = d.to_ui(i)
            mac = ui.get("mac") or "—"
            if mac and mac != "—":
                ui["id"] = d.channel + "-" + re.sub(r"[^0-9a-z]", "", mac.lower())
            else:
                ui["id"] = f"{d.channel}-idx{i}"
            ui["counter"] = _counter_for(d.category)
            devices.append(ui)

        # Collapse provable duplicates, keeping the strongest-signal instance.
        def sig(x):
            r = x.get("rssi")
            return r if isinstance(r, (int, float)) else -999
        best = {}
        for ui in devices:
            k = self._dedup_key(ui)
            if k not in best or sig(ui) > sig(best[k]):
                best[k] = ui
        deduped = []
        for k, ui in best.items():
            if k[0] == "ble-name":
                # stable id derived from the NAME, so the merged entry doesn't
                # flip ids (and flicker) as the strongest underlying MAC changes.
                ui["id"] = "blename-" + (re.sub(r"[^0-9a-z]", "", k[1]) or "x")
            deduped.append(ui)

        # sort by signal strength: strongest (closest) first; unknown RSSI last
        deduped.sort(key=lambda x: (-sig(x)) if isinstance(x.get("rssi"), (int, float)) else 1e9)
        return deduped


class Station:
    def __init__(self):
        self.fusion = Fusion()
        self.rf = next((s for s in SENSORS if s.channel == "rf"), None)
        self.latest = {"devices": [], "sensors": [], "ts": 0}
        self._cache = {}        # channel -> last list[Detection]
        self._last_scan = {}    # channel -> ts of last actual scan
        self._t0 = time.time()  # session start (for the NEW-device baseline)
        self._baseline = None   # set of device ids present during warmup
        self._seen_warmup = set()

    def bring_up(self):
        print("SENTRY backend — bringing up sensors:")
        for s in SENSORS:
            ok = s.start()
            st = s.status()
            print(f"  [{'ONLINE ' if ok else 'offline'}] {st['name']}"
                  + (f"  ({st['error']})" if st['error'] else ""))
        online = [s for s in SENSORS if s.status()["online"]]
        if not online:
            print("\n  No sensor hardware detected. The UI will use demo data.")
            print("  Plug in an RTL-SDR / Wi-Fi / BLE adapter and re-run to go live.")

    def scan_once(self):
        """One refresh tick. Fast sensors (BLE) scan every tick; slow/blocking
        sensors (Wi-Fi/RF) scan on their own slower interval, their results
        cached in between so the fused feed always stays current and live."""
        now = time.time()
        for s in SENSORS:
            ch = s.channel
            # plug-and-play: re-check offline sensors in case hardware appeared.
            if not s.status()["online"]:
                try:
                    if s.available():
                        s.start()
                except Exception:
                    pass
            if not s.status()["online"]:
                self._cache[ch] = []
                continue
            interval = SENSOR_INTERVAL.get(ch, 8.0)
            if (now - self._last_scan.get(ch, 0.0)) >= interval:
                self._cache[ch] = s.safe_scan()
                self._last_scan[ch] = now

        all_dets = []
        for ch in self._cache:
            all_dets.extend(self._cache[ch])
        devices = self.fusion.build(all_dets)

        # NEW-device baseline: collect everything seen during warmup; after that,
        # flag any id not in the baseline as newly-arrived. We ignore devices with
        # randomized/private MACs (phones, many BLE devices rotate their MAC every
        # ~15 min, so they'd always look "new" — useless for the hotel workflow).
        ids = {d["id"] for d in devices}
        if self._baseline is None:
            self._seen_warmup |= ids
            if (now - self._t0) >= WARMUP_SECONDS:
                self._baseline = set(self._seen_warmup)
        new_count = 0
        for d in devices:
            stable_mac = not identify.is_random_mac(d.get("mac", ""))
            is_new = (self._baseline is not None and d["id"] not in self._baseline
                      and stable_mac)
            d["is_new"] = is_new
            if is_new:
                new_count += 1

        # real RF spectrum (power vs frequency) from the RTL-SDR, for the UI's
        # spectrum/waterfall view — empty unless the SDR is online.
        rf_spectrum = {}
        rf_sensor = next((s for s in SENSORS if s.channel == "rf"), None)
        try:
            if rf_sensor and rf_sensor.status()["online"] and hasattr(rf_sensor, "spectrum"):
                rf_spectrum = rf_sensor.spectrum()
        except Exception:
            rf_spectrum = {}

        self.latest = {
            "devices": devices,
            "sensors": [s.status() for s in SENSORS],
            "new_count": new_count,
            "baseline_ready": self._baseline is not None,
            "rf_spectrum": rf_spectrum,
            "ts": now,
        }
        return self.latest

    def force_rescan(self):
        """Force the throttled sensors (Wi-Fi/RF) to re-scan on the next tick —
        backs the UI's instant REFRESH button."""
        self._last_scan = {}

    def _vendor_for_ip(self, ip):
        for d in self.latest.get("devices", []):
            if d.get("ip") == ip:
                return d.get("maker") or d.get("model") or ""
        return ""

    def scan_device(self, ip):
        """Port-scan + assess ONE device on the LAN (own network only). Blocking —
        the server calls it off the event loop. Refuses non-private addresses."""
        ip = str(ip or "").strip()
        if not _is_private_ip(ip):
            return {"error": "Only private/LAN addresses (your own network) can be "
                             "scanned — public/internet addresses are refused.", "ip": ip}
        vendor = self._vendor_for_ip(ip)
        try:
            ports = inspector.scan_ports(ip)
        except Exception as e:
            return {"error": str(e), "ip": ip}
        return inspector.assess_device(ip, vendor, ports)

    def rf_command(self, cmd):
        """Handle a live RF control message from the UI (tuned view / audio).
        No-ops safely if the RF sensor is offline. Returns a small ack dict."""
        if not self.rf or not self.rf.status()["online"]:
            return {"type": "rf_ack", "ok": False, "reason": "RF offline"}
        c = cmd.get("cmd")
        try:
            if c == "rf_tune":
                self.rf.set_view(center_mhz=cmd.get("center_mhz"),
                                 span_hz=cmd.get("span_hz"),
                                 demod=cmd.get("demod"),
                                 audio=cmd.get("audio"))
            elif c == "rf_sweep":
                self.rf.set_sweep()
            elif c == "rf_scan":
                self.rf.set_scan(band=cmd.get("band"),
                                 kind=cmd.get("kind"),
                                 list_key=cmd.get("list_key"),
                                 auto=cmd.get("auto"),
                                 lo_mhz=cmd.get("lo_mhz"),
                                 hi_mhz=cmd.get("hi_mhz"),
                                 step_khz=cmd.get("step_khz"),
                                 demod=cmd.get("demod"),
                                 squelch_db=cmd.get("squelch_db"))
            elif c == "rf_scan_skip":
                self.rf.scan_skip()
            elif c == "rf_scan_next":
                self.rf.scan_next()
            elif c == "rf_scan_prev":
                self.rf.scan_prev()
            elif c == "rf_scan_auto":
                self.rf.scan_auto(bool(cmd.get("auto", True)))
            elif c == "rf_scan_squelch":
                self.rf.scan_set_squelch(cmd.get("squelch_db", 8.0))
            elif c == "rf_baseline_capture":
                self.rf.capture_rf_baseline()
            elif c == "rf_baseline_clear":
                self.rf.clear_rf_baseline()
            else:
                return {"type": "rf_ack", "ok": False, "reason": "unknown cmd"}
        except Exception as e:
            return {"type": "rf_ack", "ok": False, "reason": str(e)}
        return {"type": "rf_ack", "ok": True, "cmd": c, "meta": self.rf.view_meta()}

    def run_scan_loop(self):
        """Background thread: keep refreshing the fused state forever. Runs off
        the asyncio loop so a blocking sensor scan never stalls the WS feed."""
        while True:
            try:
                self.scan_once()
            except Exception:
                pass
            time.sleep(TICK_INTERVAL)


async def _serve(station):
    async def handler(ws):
        # push the current state immediately, then push again whenever a new
        # scan tick produces fresh data (detected by its timestamp changing).
        # Separately, when the RF tuned view is active, stream its live spectrum
        # (on each new sweep row) and demodulated audio frames promptly.
        async def reader():
            try:
                async for msg in ws:
                    if not isinstance(msg, str):
                        continue
                    s = msg.strip()
                    if s == "rescan":
                        station.force_rescan()
                        continue
                    if s.startswith("{"):
                        try:
                            cmd = json.loads(s)
                        except Exception:
                            continue
                        if not isinstance(cmd, dict):
                            continue
                        cn = str(cmd.get("cmd", ""))
                        if cn.startswith("rf_"):
                            ack = station.rf_command(cmd)
                            try:
                                await ws.send(json.dumps(ack))
                            except Exception:
                                pass
                        elif cn == "net_capture_status":
                            try:
                                await ws.send(json.dumps({"type": "net_capture",
                                                          "status": inspector.capture_status()}))
                            except Exception:
                                pass
                        elif cn == "net_scan_device":
                            # port scan is blocking (~seconds) — run off the event loop
                            report = await asyncio.to_thread(station.scan_device, cmd.get("ip"))
                            try:
                                await ws.send(json.dumps({"type": "net_scan", "report": report}))
                            except Exception:
                                pass
                        elif cn == "net_capture_start":
                            secs = max(4, min(20, int(cmd.get("seconds", 8))))
                            summary = await asyncio.to_thread(inspector.capture_traffic, secs)
                            try:
                                await ws.send(json.dumps({"type": "net_traffic", "summary": summary}))
                            except Exception:
                                pass
                        elif cn == "net_nmap_status":
                            try:
                                await ws.send(json.dumps({"type": "net_nmap_status",
                                                          "status": inspector.nmap_status()}))
                            except Exception:
                                pass
                        elif cn == "net_nmap_scan":
                            tgt = cmd.get("target")
                            stype = cmd.get("scan_type", "quick")
                            # nmap can run for a while — keep it off the event loop
                            res = await asyncio.to_thread(inspector.nmap_scan, tgt, stype)
                            try:
                                await ws.send(json.dumps({"type": "net_nmap", "result": res}))
                            except Exception:
                                pass
            except Exception:
                pass

        rtask = asyncio.ensure_future(reader())
        try:
            await ws.send(json.dumps(station.latest))
            last_ts = station.latest["ts"]
            last_rf_n = -1
            last_scan_n = -1
            last_audio_seq = 0          # this client's own audio cursor (non-draining)
            while True:
                await asyncio.sleep(0.03)
                # fused device/sensor state (slow tick)
                if station.latest["ts"] != last_ts:
                    await ws.send(json.dumps(station.latest))
                    last_ts = station.latest["ts"]
                # live tuned spectrum + scanner state + audio (fast)
                rf = station.rf
                if rf and rf.status()["online"]:
                    tuned = rf.tuned_state()
                    if tuned and tuned.get("n") != last_rf_n:
                        last_rf_n = tuned["n"]
                        await ws.send(json.dumps({"type": "rf_tuned", "tuned": tuned}))
                    scan = rf.scan_state()
                    if scan and scan.get("n") != last_scan_n:
                        last_scan_n = scan["n"]
                        await ws.send(json.dumps({"type": "rf_scan", "scan": scan}))
                    if rf.audio_active():
                        rate, frames, newest = rf.audio_since(last_audio_seq)
                        last_audio_seq = newest
                        for fr in frames:
                            await ws.send(json.dumps({
                                "type": "rf_audio", "rate": rate,
                                "pcm": base64.b64encode(fr).decode("ascii")}))
        except Exception:
            return
        finally:
            rtask.cancel()

    print(f"  Backend: ws://0.0.0.0:8765 (live sensor feed — reachable on your LAN)")
    # 0.0.0.0 so the phone can reach the WebSocket feed too, not just localhost.
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever


def main():
    station = Station()
    station.bring_up()
    station.scan_once()
    print("\nStarting SENTRY…")
    serve_ui()
    # keep refreshing the fused state in the background (off the asyncio loop).
    threading.Thread(target=station.run_scan_loop, daemon=True,
                     name="scan-loop").start()
    if websockets is None:
        print("\n(websockets not installed — run: pip install -r requirements.txt)")
        print("The UI still runs in demo mode at the URL above.")
        try:
            webbrowser.open(f"http://localhost:{HTTP_PORT}")
        except Exception:
            pass
        # keep the HTTP server alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return
        return
    try:
        webbrowser.open(f"http://localhost:{HTTP_PORT}")
    except Exception:
        pass
    asyncio.run(_serve(station))


if __name__ == "__main__":
    main()
