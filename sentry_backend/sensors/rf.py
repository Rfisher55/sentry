"""Real RF detection via RTL-SDR (Stage 2 — the core real-detection sensor).

Sweeps the surveillance-relevant ISM / cellular-uplink bands, estimates the
noise floor, finds peaks that rise above it, and classifies them by band. This
is the genuine "something is transmitting here" capability. Requires an RTL-SDR
(pyrtlsdr); reports offline without one.

HARDWARE & HONEST COVERAGE (Nooelec NESDR / RTL2832U + R820T tuner):
  * Tunable range ~25 MHz – 1.75 GHz. We only WATCH the bands within that range
    where bugs/trackers/cheap transmitters live (433/868/915 MHz ISM, cellular
    uplink). We deliberately SKIP normal broadcast (FM/TV/cellular downlink) so
    the station isn't flooded with licensed signals it shouldn't alarm on.
  * It CANNOT see 2.4 GHz / 5 GHz Wi-Fi, Bluetooth, or 5.8 GHz analog video —
    those are above the tuner's range and are covered by the Wi-Fi/BLE sensors.
  * It detects ENERGY only — it does not decode/demodulate private content.

The sweep runs in a background thread, so a slow pass never stalls the live feed
(scan() just returns the latest cached result instantly, like the BLE/LAN sensors).
"""

from sentry_backend.sensor import Sensor, Detection
import threading
import time

try:
    import numpy as np
except Exception:
    np = None

try:
    from rtlsdr import RtlSdr
    _HAS_RTL = True
except Exception:
    _HAS_RTL = False


# Band plan: (low_mhz, high_mhz, kind, category, severity, note)
# IMPORTANT: every band MUST fall within the tuner's real range
# (TUNER_LOW_MHZ..TUNER_HIGH_MHZ). 2.4/5 GHz are above an R820T's reach and are
# deliberately absent — they're covered by the Wi-Fi/BLE sensors instead.
BANDS = [
    (430, 435, "433 MHz device", "unknown transmitter", "suspect",
     "433 ISM — sensors, remotes, cheap bugs"),
    (860, 870, "868 MHz device", "unknown transmitter", "notable",
     "868 ISM — IoT, alarms"),
    (902, 928, "915 MHz device", "unknown transmitter", "notable",
     "915 ISM — telemetry, IoT"),
    (1710, 1750, "Cellular-band transmitter", "unknown transmitter", "notable",
     "Uplink energy (within the R820T's ~1.75 GHz ceiling) — most likely a nearby "
     "phone; a GSM/LTE bug also calls out here. Not a bug on its own — identify up close."),
]


class RFSensor(Sensor):
    channel = "rf"
    name = "RF Spectrum (RTL-SDR R820T)"

    # The R820T tuner (Nooelec NESDR) covers roughly this range.
    TUNER_LOW_MHZ = 25
    TUNER_HIGH_MHZ = 1750
    STEP_MHZ = 2.0            # ~ sample rate per tune (2.4 MHz bw, slight overlap)
    SAMPLE_RATE = 2.4e6
    PEAK_DB_OVER_FLOOR = 10.0  # first-cut threshold; real-world tuning is ongoing
    SCAN_PERIOD = 6.0          # seconds between band sweeps (background thread)

    def __init__(self):
        super().__init__()
        self.sdr = None
        self._dets = []
        self._lock = threading.Lock()
        self._thread = None
        self._started = False

    def available(self) -> bool:
        return _HAS_RTL and np is not None

    def _setup(self):
        if self._started:
            return
        self.sdr = RtlSdr()
        self.sdr.sample_rate = self.SAMPLE_RATE
        self.sdr.gain = "auto"
        self._note = (
            "RTL-SDR R820T online — tuner covers ~%d MHz–%.2f GHz. SENTRY watches the "
            "surveillance ISM/cellular bands in that range (433/868/915 MHz, cellular "
            "uplink) and flags transmitters there; it skips normal broadcast (FM/TV) to "
            "avoid false alarms. It CANNOT see 2.4/5 GHz Wi-Fi/Bluetooth/video (above the "
            "tuner's range — those use the Wi-Fi & BLE sensors) and never decodes content."
            % (self.TUNER_LOW_MHZ, self.TUNER_HIGH_MHZ / 1000.0))
        self._started = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="rf-sweep")
        self._thread.start()

    # ---- background sweeper -------------------------------------------------
    def _run_loop(self):
        while True:
            try:
                dets = self._sweep_bands()
                with self._lock:
                    self._dets = dets
            except Exception as e:               # device unplugged / driver hiccup
                self._error = str(e)
                with self._lock:
                    self._dets = []
            time.sleep(self.SCAN_PERIOD)

    def _power_at(self, center_hz):
        """Read median (noise floor) and max (peak) power, in dB, around a tune.

        The RTL-SDR has a strong DC spike at the centre frequency (an artefact of
        the receiver, NOT a transmitter). We mask a few bins around DC before
        taking the peak, so a quiet band doesn't falsely read as "a signal". This
        is honest first-cut detection; finer real-world threshold tuning remains.
        """
        self.sdr.center_freq = center_hz
        samples = self.sdr.read_samples(64 * 1024)
        spectrum = np.fft.fftshift(np.fft.fft(samples))
        power = 20 * np.log10(np.abs(spectrum) + 1e-9)
        floor = float(np.median(power))
        n = len(power); c = n // 2; g = max(8, n // 100)   # mask ±1% around DC
        edge = np.concatenate([power[:c - g], power[c + g:]])
        peak = float(np.max(edge)) if edge.size else float(np.max(power))
        return floor, peak

    def _sweep_bands(self):
        if not self.sdr:
            return []
        readings = []
        for lo, hi, *_ in BANDS:
            f = lo
            while f <= hi:
                try:
                    floor, peak = self._power_at(f * 1e6)
                    readings.append((f, peak, floor))
                except Exception:
                    pass
                f += self.STEP_MHZ
        if not readings:
            return []
        # noise floor: median of the per-tune medians across the watched bands
        global_floor = float(np.median([r[2] for r in readings]))
        dets = []
        for fmhz, peak, floor in readings:
            over = peak - global_floor
            if over < self.PEAK_DB_OVER_FLOOR:
                continue
            band = self._band_for(fmhz)
            if not band:
                continue
            lo, hi, kind, cat, sev, note = band
            dets.append(Detection(
                kind=kind, channel="rf", severity=sev, category=cat,
                ident=f"{fmhz:.1f} MHz · {over:.0f} dB over floor",
                bandtxt=f"{lo}–{hi} MHz", behaviortxt=note,
                surveilling=self._surv(cat),
                cancapture="Energy detected only — identify it up close (SENTRY can't decode content)",
                capturingnow=f"Transmitting on {fmhz:.1f} MHz now",
                confidence=min(95, 55 + int(over)),
                device_type=kind, method="RF (RTL-SDR)",
                evidence=[f"peak {over:.0f} dB over noise floor at {fmhz:.1f} MHz"],
                freq_mhz=fmhz, rssi=peak,
            ))
        return self._dedupe_by_band(dets)

    def scan(self):
        with self._lock:
            return list(self._dets)

    def _band_for(self, fmhz):
        for b in BANDS:
            if b[0] <= fmhz <= b[1]:
                return b
        return None

    def _surv(self, cat):
        return {"camera": "Visual — its field of view",
                "audio bug": "Audio — room conversations",
                "unknown transmitter": "Unknown — purpose unconfirmed"}.get(cat, "Unknown")

    def _dedupe_by_band(self, dets):
        best = {}
        for d in dets:
            key = d.bandtxt
            if key not in best or (d.rssi or -999) > (best[key].rssi or -999):
                best[key] = d
        return list(best.values())

    def stop(self):
        if self.sdr:
            try:
                self.sdr.close()
            except Exception:
                pass
