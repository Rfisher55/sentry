"""SENTRY backend — sensor base.

Every real sensor inherits from Sensor. The key design rule: a sensor whose
hardware or driver isn't present reports `online=False` and returns no
detections — it never crashes the system. This is what lets you bring the build
up one sensor at a time (RF first, then Wi-Fi, then BLE, ...).
"""

from dataclasses import dataclass, field, asdict
import time


# --- Honest range estimation -------------------------------------------------
# We can estimate DISTANCE from signal strength (RSSI) with a standard
# log-distance path-loss model. We canNOT measure DIRECTION with a single
# omnidirectional antenna, so bearing is never emitted at all — the UI lays
# devices out by distance only (see locnote below).
_TX_POWER_1M = -59.0    # typical RSSI (dBm) at 1 m for 2.4 GHz BLE/Wi-Fi
_PATH_LOSS_N = 2.5      # indoor path-loss exponent (2 = free space, ~3 = walls)


def estimate_distance_m(rssi):
    """Estimate distance in metres from RSSI. Returns None if RSSI is unknown.

    This is an ESTIMATE from signal strength only — multipath, body-blocking
    and antenna differences make it approximate, never a precise fix.
    """
    if rssi is None:
        return None
    dbm = float(rssi)
    # Windows Wi-Fi reports signal as 0..100 %, not dBm — map it roughly.
    if dbm >= 0:
        dbm = dbm / 2.0 - 100.0
    dist = 10 ** ((_TX_POWER_1M - dbm) / (10 * _PATH_LOSS_N))
    return max(0.3, min(dist, 60.0))


@dataclass
class Detection:
    """One real thing a sensor found."""
    kind: str                 # "Wi-Fi IP camera", "BLE tracker", etc.
    channel: str              # "rf" | "wifi" | "bluetooth" | ...
    severity: str             # "alert" | "suspect" | "notable"
    category: str             # "camera" | "tracker" | "audio bug" | ...
    ident: str = ""           # signal identifier ("802.11n · RTSP:554")
    maker: str = "Not announced"
    model: str = "—"
    mac: str = "—"
    bandtxt: str = "—"
    behaviortxt: str = ""
    surveilling: str = ""
    cancapture: str = ""
    capturingnow: str = ""
    confidence: int = 50
    bearing: float | None = None
    distance: float | None = None
    uncertainty: float | None = None
    freq_mhz: float | None = None
    rssi: float | None = None
    ip: str = ""                       # set by the network (LAN) sensor
    device_type: str = ""              # best-guess "what is this" (identify.py)
    method: str = ""                   # HOW it was seen: "Bluetooth LE", "Wi-Fi 5 GHz", "Network (LAN)"
    evidence: list = field(default_factory=list)   # why we think so
    is_new: bool = False               # appeared after the session baseline
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    def to_ui(self, idx):
        d = asdict(self)
        d["id"] = f"dev{idx}"
        # UI expects these names; fill sane defaults
        d.setdefault("name", self.model if self.model != "—" else "Unnamed")

        # Per-device location estimate. Distance comes from this device's own
        # RSSI (so each device differs). DIRECTION is not measured at all — we no
        # longer emit a (previously hash-derived, fake) bearing. The UI arranges
        # devices by distance only; any on-screen angle is layout spacing, not a
        # compass direction.
        d["bearing"] = None

        if self.distance is not None:
            d["distance"] = round(float(self.distance), 1)
            d["uncertainty"] = round(float(self.uncertainty), 1) if self.uncertainty is not None else 1.0
            d["locnote"] = "Distance reported by the sensor."
        else:
            dist = estimate_distance_m(self.rssi)
            if dist is not None:
                unc = max(1.0, 0.35 * dist)   # weaker/farther signal ⇒ less certain
                d["distance"] = round(dist, 1)
                d["uncertainty"] = round(unc, 1)
                d["locnote"] = (
                    f"Distance is estimated from signal strength ({self.rssi} dBm, "
                    f"±{round(unc)} m). Direction is NOT measured — a single antenna "
                    "can't find bearing, so devices are shown by distance only. "
                    "Use Locate and move around to home in by signal strength."
                )
            else:
                d["distance"] = 0
                d["uncertainty"] = 0
                d["locnote"] = (
                    "Signal strength unavailable, so distance can't be estimated, "
                    "and direction isn't measurable with this hardware."
                )
        d["counter"] = []   # fused in later
        return d


class Sensor:
    """Base class. Override channel, name, available(), and scan()."""
    channel = "base"
    name = "Sensor"

    def __init__(self):
        self._online = False
        self._error = ""
        self._note = ""          # honest, non-error coverage caveat for the UI

    def available(self) -> bool:
        """Return True if this sensor's hardware + driver are present."""
        return False

    def start(self):
        try:
            self._online = self.available()
            if self._online:
                self._setup()
        except Exception as e:
            self._online = False
            self._error = str(e)
        return self._online

    def _setup(self):
        """Optional one-time hardware init."""
        pass

    def scan(self) -> list:
        """Return a list[Detection] from one real scan pass. Empty if nothing."""
        return []

    def status(self) -> dict:
        return {"channel": self.channel, "name": self.name,
                "online": self._online, "error": self._error,
                "note": self._note}

    def safe_scan(self) -> list:
        """Never raise — a flaky sensor must not take down the station."""
        if not self._online:
            return []
        try:
            return self.scan() or []
        except Exception as e:
            self._error = str(e)
            return []
