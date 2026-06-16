"""Real RF detection via RTL-SDR (Stage 2 — the core real-detection sensor).

Sweeps the spectrum, estimates the noise floor, finds peaks that rise above it,
and classifies them by band. This is the genuine "something is transmitting
here" capability. Requires an RTL-SDR (pyrtlsdr); reports offline without one.
"""

from sentry_backend.sensor import Sensor, Detection

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
# IMPORTANT: every band here MUST fall within the actual sweep range
# (SWEEP_START_MHZ..SWEEP_STOP_MHZ). A standard RTL-SDR tops out around 1.7 GHz,
# so 2.4 GHz and 5.8 GHz are physically OUT OF RANGE for this hardware and are
# deliberately NOT listed — they'd be dead entries that can never fire. Those
# bands are instead covered by the Wi-Fi and Bluetooth sensors (2.4/5 GHz). A
# wideband SDR (e.g. HackRF) would be needed to add them here.
BANDS = [
    (430, 435, "433 MHz device", "unknown transmitter", "suspect",
     "433 ISM — sensors, remotes, cheap bugs"),
    (860, 870, "868 MHz device", "unknown transmitter", "notable",
     "868 ISM — IoT, alarms"),
    (900, 930, "915 MHz device", "unknown transmitter", "notable",
     "915 ISM — telemetry, IoT"),
    (1700, 1766, "Cellular uplink burst", "audio bug", "suspect",
     "GSM/LTE uplink (up to the RTL-SDR's ~1.7 GHz ceiling) — possible GSM bug"),
]


class RFSensor(Sensor):
    channel = "rf"
    name = "RF Spectrum (RTL-SDR)"

    # sweep config
    SWEEP_START_MHZ = 24      # RTL-SDR practical low end
    SWEEP_STOP_MHZ = 1766     # RTL-SDR practical high end (~1.7 GHz)
    STEP_MHZ = 2.4            # ~ sample rate per tune
    SAMPLE_RATE = 2.4e6
    PEAK_DB_OVER_FLOOR = 8.0  # how far above noise floor counts as a signal

    def __init__(self):
        super().__init__()
        self.sdr = None

    def available(self) -> bool:
        return _HAS_RTL and np is not None

    def _setup(self):
        self.sdr = RtlSdr()
        self.sdr.sample_rate = self.SAMPLE_RATE
        self.sdr.gain = "auto"

    def _power_at(self, center_hz):
        """Read average power (dB) in the band around a center frequency."""
        self.sdr.center_freq = center_hz
        samples = self.sdr.read_samples(64 * 1024)
        spectrum = np.fft.fftshift(np.fft.fft(samples))
        power = 20 * np.log10(np.abs(spectrum) + 1e-9)
        return float(np.median(power)), float(np.max(power))

    def scan(self):
        if not self.sdr:
            return []
        # 1) sweep, collecting (freq_mhz, peak_db, floor_db)
        readings = []
        f = self.SWEEP_START_MHZ
        while f <= self.SWEEP_STOP_MHZ:
            try:
                floor, peak = self._power_at(f * 1e6)
                readings.append((f, peak, floor))
            except Exception:
                pass
            f += self.STEP_MHZ

        if not readings:
            return []

        # 2) global noise floor estimate (median of all medians)
        global_floor = float(np.median([r[2] for r in readings]))

        # 3) keep peaks that rise clearly above the floor
        dets = []
        for fmhz, peak, floor in readings:
            if peak - global_floor < self.PEAK_DB_OVER_FLOOR:
                continue
            band = self._band_for(fmhz)
            if not band:
                continue
            lo, hi, kind, cat, sev, note = band
            dets.append(Detection(
                kind=kind, channel="rf", severity=sev, category=cat,
                ident=f"{fmhz:.1f} MHz · {peak - global_floor:.0f} dB over floor",
                bandtxt=f"{lo}–{hi} MHz",
                behaviortxt=note,
                surveilling=self._surv(cat),
                cancapture="Determined on closer inspection",
                capturingnow=f"Transmitting on {fmhz:.1f} MHz now",
                confidence=min(95, 55 + int(peak - global_floor)),
                freq_mhz=fmhz, rssi=peak,
            ))
        # 4) collapse adjacent detections in the same band to one
        return self._dedupe_by_band(dets)

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
