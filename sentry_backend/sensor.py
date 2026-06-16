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


def proximity_of(rssi):
    """Turn RSSI into an HONEST, COARSE proximity — a band plus a wide range —
    instead of a falsely-precise single metre value.

    RSSI→distance is genuinely rough indoors (multipath, body-blocking, antenna
    gain), so the real error is easily a factor of ~2. We therefore present a
    range (½× … 2× the point estimate) and a plain-language band, never a hard
    number like "0.4 m". Returns None when RSSI is unknown.
    """
    d = estimate_distance_m(rssi)
    if d is None:
        return None
    lo, hi = d * 0.5, d * 2.0
    band = ("very close" if d < 1.5 else "close" if d < 4 else
            "nearby" if d < 10 else "far" if d < 25 else "very far")

    def r(x):
        return int(round(x)) if x >= 2 else round(x, 1)

    return {"distance": round(d, 1), "lo": r(lo), "hi": r(hi), "band": band,
            "text": f"{band} · approx {r(lo)}–{r(hi)} m"}


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

        prox = proximity_of(self.rssi) if self.distance is None else None
        if self.distance is not None:
            # a real measured distance (rare; e.g. future ranging hardware)
            dist = round(float(self.distance), 1)
            d["distance"] = dist
            d["proximity"] = ""
            d["distance_txt"] = f"approx {dist} m (reported)"
            d["uncertainty"] = round(float(self.uncertainty), 1) if self.uncertainty is not None else 1.0
            d["locnote"] = "Distance reported by the sensor."
        elif prox is not None:
            d["distance"] = prox["distance"]            # point estimate (radar ring only)
            d["proximity"] = prox["band"]
            d["distance_txt"] = prox["text"]
            # uncertainty = half the band width, so the radar ring honestly looks fuzzy
            d["uncertainty"] = round(max(prox["distance"] - prox["lo"],
                                         prox["hi"] - prox["distance"]), 1)
            d["locnote"] = (
                f"Proximity is a ROUGH estimate from signal strength ({self.rssi} dBm) — "
                f"realistically {prox['lo']}–{prox['hi']} m, easily off by 2×. Direction is "
                "NOT measured; devices are shown by distance only. Use Locate and move to home in."
            )
        else:
            # no signal → no distance. Never fake a "0 m" reading.
            d["distance"] = None
            d["proximity"] = "unknown"
            d["distance_txt"] = "no signal — distance unknown"
            d["uncertainty"] = None
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
