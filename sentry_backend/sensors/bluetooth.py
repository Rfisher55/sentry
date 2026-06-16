"""Real Bluetooth LE detection (Stage 3 — finds actual trackers & BLE bugs).

Runs a PERSISTENT scanner: a background thread owns an asyncio loop and keeps
a BleakScanner running continuously, updating a live table of advertisements
(address -> latest device/adv/RSSI/last-seen). `scan()` just reads that table
instantly, so every server tick gets fresh, real-time RSSI for every device —
this is what makes "warmer/colder" tracking actually live as you move.

Flags AirTag-class trackers (Apple Find My manufacturer data) and surfaces
every other BLE device distinctly by MAC + RSSI. Uses `bleak`; reports offline
without a BLE adapter. Listen-only — no pairing, no attacks.
"""

from sentry_backend.sensor import Sensor, Detection
from sentry_backend import identify
import time
import threading

try:
    import asyncio
    from bleak import BleakScanner
    _HAS_BLE = True
except Exception:
    _HAS_BLE = False

APPLE_COMPANY_ID = 0x004C   # Apple — Find My / AirTag advertisements
_STALE_AFTER = 45.0         # GRACE: keep a device this long after its last advert,
                            # so an intermittently-advertising device doesn't vanish
                            # just because one scan cycle didn't hear it.
_FOLLOWING_AFTER = 30.0     # seen continuously this long ⇒ flag as possibly following


class BLESensor(Sensor):
    channel = "bluetooth"
    name = "Bluetooth LE Scanner"

    def __init__(self, stale_after=_STALE_AFTER):
        super().__init__()
        self.stale_after = stale_after
        self._adv = {}                 # address -> {device, adv, rssi, last_seen, first_seen, count}
        self._lock = threading.Lock()
        self._thread = None
        self._started = False
        self._failed = False           # scanner thread died (no adapter) — stay offline

    def available(self) -> bool:
        # bleak present AND we haven't already failed to bring up a scanner
        return _HAS_BLE and not self._failed

    def _setup(self):
        """Start the persistent background scanner exactly once."""
        if self._started:
            return
        self._started = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="ble-scanner")
        self._thread.start()

    # ---- background scanner thread -----------------------------------------
    def _run_loop(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._scan_forever())
        except Exception as e:          # no adapter / driver error — degrade
            self._failed = True
            self._online = False
            self._error = str(e)

    async def _scan_forever(self):
        def on_advert(device, adv):
            now = time.time()
            with self._lock:
                prev = self._adv.get(device.address)
                # MERGE, don't overwrite: BLE sends the name in a scan-response
                # that isn't in every packet, so keep the best-known name and
                # accumulate manufacturer data across adverts.
                name = (adv.local_name or "").strip()
                if not name and prev:
                    name = prev.get("name", "")
                mfr = dict(prev["mfr"]) if prev else {}
                if adv.manufacturer_data:
                    mfr.update(adv.manufacturer_data)
                svcs = set(prev["svcs"]) if prev else set()
                if adv.service_uuids:
                    svcs.update(adv.service_uuids)
                self._adv[device.address] = {
                    "device": device, "adv": adv, "rssi": adv.rssi,
                    "name": name, "mfr": mfr, "svcs": svcs,
                    "last_seen": now,
                    "first_seen": prev["first_seen"] if prev else now,
                    "count": (prev["count"] + 1) if prev else 1,
                }

        scanner = BleakScanner(detection_callback=on_advert)
        await scanner.start()
        try:
            while True:
                await asyncio.sleep(1.0)
                cutoff = time.time() - self.stale_after
                with self._lock:
                    for addr in [a for a, r in self._adv.items()
                                 if r["last_seen"] < cutoff]:
                        del self._adv[addr]
        finally:
            try:
                await scanner.stop()
            except Exception:
                pass

    # ---- read the live snapshot (instant — no blocking) --------------------
    def scan(self):
        if not _HAS_BLE or self._failed:
            return []
        now = time.time()
        with self._lock:
            snapshot = list(self._adv.values())
        dets = []
        for rec in snapshot:
            d = self._classify(rec, now)
            if d:
                dets.append(d)
        return dets

    def _classify(self, rec, now):
        dev = rec["device"]
        addr = dev.address
        rssi = rec["rssi"]
        # bleak/Windows reports -127 dBm (BLE spec 0x7F) when no RSSI is actually
        # available for an advert. That's "no reading", NOT a real, very-weak
        # signal — surfacing it would fake a distance (~60 m) and a meter level.
        # Treat it honestly as unknown so the UI says "signal unavailable".
        if rssi is not None and rssi <= -127:
            rssi = None
        name = rec.get("name", "")
        mfr = rec.get("mfr", {})
        svcs = rec.get("svcs", set())
        age = now - rec["first_seen"]
        following = age >= _FOLLOWING_AFTER

        # 16-bit assigned numbers from the advertised 128-bit service UUIDs
        svc16 = []
        for u in svcs:
            try:
                svc16.append(int(str(u)[4:8], 16))
            except Exception:
                pass

        # identify the DEVICE TYPE (what it is) from manufacturer beacons,
        # service UUIDs, name and vendor. "Bluetooth LE" is the METHOD, not type.
        METHOD = "Bluetooth LE"
        info = identify.identify(mac=addr, name=name,
                                 ble_manufacturer=mfr, ble_services=svc16,
                                 seen_via=METHOD)
        vendor = info["vendor"]
        dtype = info["type"]
        # the device's own advertised name is the friendliest label when present
        label = name if name else dtype

        def det(**kw):
            kw.setdefault("first_seen", rec["first_seen"])
            kw.setdefault("last_seen", rec["last_seen"])
            kw.setdefault("method", METHOD)
            kw.setdefault("device_type", dtype)
            kw.setdefault("evidence", list(info["evidence"]))
            return Detection(**kw)

        # AirTag / Find My: Apple manufacturer data with the Find My type byte
        if APPLE_COMPANY_ID in mfr:
            payload = mfr[APPLE_COMPANY_ID]
            if payload and payload[0] in (0x12, 0x07) and "tracker" in dtype.lower():
                sev = "alert" if following else "suspect"
                return det(
                    kind="Item tracker (Apple Find My)", channel="bluetooth",
                    severity=sev, category="tracker",
                    maker="Apple", model=name or "AirTag / Find My", mac=addr,
                    ident="Apple Find My beacon", bandtxt="2.4 GHz",
                    device_type="Item tracker (Apple Find My)",
                    behaviortxt=(f"Seen continuously for {int(age)}s — consistent with "
                                 "traveling with you" if following
                                 else "Find My tracker advertising nearby"),
                    surveilling="Your location, continuously",
                    cancapture="Position via the Find My network",
                    capturingnow="Reporting location through nearby Apple devices",
                    confidence=88 if following else max(70, info["confidence"]), rssi=rssi,
                )

        # Everything else: primary label is the DEVICE TYPE / its real name.
        return det(
            kind=label, channel="bluetooth", severity="notable",
            category="bluetooth device", mac=addr,
            maker=vendor or ("randomized MAC" if identify.is_random_mac(addr) else "Unknown vendor"),
            model=name or "—",
            ident=(f'"{name}"' if name else dtype),
            bandtxt="2.4 GHz",
            behaviortxt=(f"{dtype}, seen {rec['count']}× over {int(age)}s via {METHOD}."
                         + (" Identified from: " + "; ".join(info["evidence"]) + "." if info["evidence"] else "")
                         + (" Has been near you a while." if following else "")),
            surveilling="Depends on the device type",
            cancapture="Depends on the device",
            capturingnow="Advertising on BLE",
            confidence=info["confidence"], rssi=rssi,
        )
