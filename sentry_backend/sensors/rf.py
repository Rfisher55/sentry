"""Real RF detection + live SDR view via RTL-SDR (Stage 2 — the core sensor).

This module owns the SINGLE RTL-SDR handle and arbitrates the one tuner between
two jobs (a dongle can only be used by ONE app at a time):

  * SWEEP mode (default): sweeps the surveillance-relevant ISM / cellular-uplink
    bands, estimates the noise floor, finds peaks above it, classifies by band.
    This is the genuine "something is transmitting here" capability.

  * TUNED mode (interactive, SDR#-style): the user picks a centre frequency and a
    span; we read REAL IQ at that tune and produce a true power-vs-frequency
    spectrum + waterfall, and (optionally) demodulate WFM/AM/NFM to live audio.
    While tuned, the background surveillance sweep PAUSES — there's only one tuner.

Requires an RTL-SDR (pyrtlsdr); reports offline without one and degrades
gracefully. Everything here is REAL receiver data — no synthesis.

HARDWARE & HONEST COVERAGE (Nooelec NESDR / RTL2832U + R820T tuner):
  * Tunable range ~25 MHz – 1.75 GHz. The sweep WATCHES only the surveillance
    bands in that range (433/868/915 MHz ISM, cellular uplink); the tuned view
    lets you look ANYWHERE in range (e.g. FM broadcast ~100 MHz to prove it works).
  * It CANNOT see 2.4 GHz / 5 GHz Wi-Fi, Bluetooth, or 5.8 GHz analog video — those
    are above the tuner's range and are covered by the Wi-Fi/BLE sensors.
  * It detects/​demodulates ENERGY and OPEN analog modulation (WFM/AM/NFM) only —
    it does NOT decode encrypted/digital content and cannot tune cellular voice.
"""

from sentry_backend.sensor import Sensor, Detection
import collections
import queue
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
    (313, 317, "315 MHz device", "unknown transmitter", "suspect",
     "315 ISM — key fobs, TPMS, garage/gate remotes, sensors (North America). Short "
     "bursts (only while a button is pressed). Detected as ENERGY only — SENTRY never "
     "decodes, stores, clones, or replays it."),
    (430, 435, "433 MHz device", "unknown transmitter", "suspect",
     "433 ISM — key fobs, remotes, weather/IoT sensors, cheap bugs. Often short bursts. "
     "Detected as energy only — never decoded, cloned, or replayed."),
    (860, 870, "868 MHz device", "unknown transmitter", "notable",
     "868 ISM — IoT, alarms, sensors (EU). Energy detected only; not decoded."),
    (902, 928, "915 MHz device", "unknown transmitter", "notable",
     "915 ISM — telemetry, IoT, sensors. Energy detected only; not decoded."),
    (1710, 1750, "Cellular-band transmitter", "unknown transmitter", "notable",
     "Uplink energy (within the R820T's ~1.75 GHz ceiling) — most likely a nearby "
     "phone; a GSM/LTE bug also calls out here. Not a bug on its own — identify up close."),
]

# Span choices for the tuned view. The RTL2832U only accepts sample rates in
# 225001–300000 Hz and 900001–3200000 Hz (the 0.3–0.9 MHz gap is invalid), and
# we keep each span an exact integer multiple of the 48 kHz audio rate so
# demodulation decimates cleanly. (Hz)
VALID_SPANS_HZ = [240000, 1200000, 1920000, 2400000]
AUDIO_RATE = 48000
DEMODS = ("WFM", "AM", "NFM")

# Scanner band presets — sweep a range, stop on activity, listen. Every band is
# inside the R820T's real ~25 MHz–1.75 GHz range and uses a valid sample rate.
# half_bw_hz = how wide around each channel centre we look for a carrier.
SCAN_BANDS = {
    "fm":    {"label": "FM broadcast", "lo": 88.0,  "hi": 108.0,  "step_khz": 200.0, "demod": "WFM", "span_hz": 2400000, "half_bw": 90000},
    "air":   {"label": "Airband (AM)", "lo": 118.0, "hi": 137.0,  "step_khz": 25.0,  "demod": "AM",  "span_hz": 240000,  "half_bw": 6000},
    "wx":    {"label": "Weather",      "lo": 162.4, "hi": 162.55, "step_khz": 25.0,  "demod": "NFM", "span_hz": 240000,  "half_bw": 7000},
    "frs":   {"label": "FRS/GMRS",     "lo": 462.0, "hi": 467.8,  "step_khz": 12.5,  "demod": "NFM", "span_hz": 240000,  "half_bw": 7000},
    "ham2m": {"label": "Ham 2m",       "lo": 144.0, "hi": 148.0,  "step_khz": 12.5,  "demod": "NFM", "span_hz": 240000,  "half_bw": 7000},
    "ham70": {"label": "Ham 70cm",     "lo": 440.0, "hi": 450.0,  "step_khz": 12.5,  "demod": "NFM", "span_hz": 240000,  "half_bw": 7000},
    # ISM fob/remote bands — park here and press a fob/remote to catch the burst.
    # Detection only (a spike + lock); the audio is just the raw OOK click, and
    # SENTRY never decodes, stores, clones, or replays the code.
    "ism315": {"label": "315 ISM (fobs/TPMS)",   "lo": 314.85, "hi": 315.15, "step_khz": 25.0, "demod": "NFM", "span_hz": 240000, "half_bw": 30000},
    "ism433": {"label": "433 ISM (fobs/sensors)", "lo": 433.0,  "hi": 434.8,  "step_khz": 25.0, "demod": "NFM", "span_hz": 240000, "half_bw": 30000},
}


# ---- Known channel plans, so the scanner can "flip" through real channels (like
# a car radio Seek or a police scanner) instead of only stepping raw frequencies.
# Every frequency is inside the R820T's ~25 MHz–1.75 GHz range. Listening is
# legal/analog only; digital/encrypted channels (e.g. marine DSC 70) are omitted.
def _fm_channels():
    out = []
    f = 88.1
    while f <= 107.95:
        out.append((round(f, 1), "FM %.1f" % round(f, 1)))
        f += 0.2
    return out

def _cb_channels():
    # The 40 CB channels (26.965–27.405 MHz, AM) in channel-number order.
    freqs = [26.965, 26.975, 26.985, 27.005, 27.015, 27.025, 27.035, 27.055,
             27.065, 27.075, 27.085, 27.105, 27.115, 27.125, 27.135, 27.155,
             27.165, 27.175, 27.185, 27.205, 27.215, 27.225, 27.255, 27.235,
             27.245, 27.265, 27.275, 27.285, 27.295, 27.305, 27.315, 27.325,
             27.335, 27.345, 27.355, 27.365, 27.375, 27.385, 27.395, 27.405]
    return [(f, "CB %d" % (i + 1)) for i, f in enumerate(freqs)]

def _rail_channels():
    # AAR railroad VHF road band 160.215–161.565 MHz at 15 kHz (NFM). Channel-
    # number assignments vary by railroad, so we label by frequency, honestly.
    out = []
    f = 160.215
    while f <= 161.566:
        out.append((round(f, 4), "Rail %.4f" % round(f, 4)))
        f += 0.015
    return out

CHANNEL_LISTS = {
    "fm":     {"label": "FM broadcast",     "demod": "WFM", "channels": _fm_channels()},
    "air":    {"label": "Airband (common)", "demod": "AM",  "channels": [
        (121.500, "Guard/Emergency"), (122.700, "Unicom 122.70"), (122.800, "Unicom 122.80"),
        (122.900, "CTAF/Multicom"), (123.000, "Unicom 123.00"), (123.050, "Heli/Unicom"),
        (123.450, "Air-to-air"), (122.750, "Air-to-air priv"), (122.200, "Flight Service"),
        (121.950, "Ground (typ)")]},
    "wx":     {"label": "NOAA Weather",     "demod": "NFM", "channels": [
        (162.400, "WX1"), (162.425, "WX2"), (162.450, "WX3"), (162.475, "WX4"),
        (162.500, "WX5"), (162.525, "WX6"), (162.550, "WX7")]},
    "frs":    {"label": "FRS/GMRS",         "demod": "NFM", "channels": [
        (462.5625, "FRS 1"), (462.5875, "FRS 2"), (462.6125, "FRS 3"), (462.6375, "FRS 4"),
        (462.6625, "FRS 5"), (462.6875, "FRS 6"), (462.7125, "FRS 7"), (467.5625, "FRS 8"),
        (467.5875, "FRS 9"), (467.6125, "FRS 10"), (467.6375, "FRS 11"), (467.6625, "FRS 12"),
        (467.6875, "FRS 13"), (467.7125, "FRS 14"), (462.5500, "GMRS 15"), (462.5750, "GMRS 16"),
        (462.6000, "GMRS 17"), (462.6250, "GMRS 18"), (462.6500, "GMRS 19"), (462.6750, "GMRS 20"),
        (462.7000, "GMRS 21"), (462.7250, "GMRS 22")]},
    "marine": {"label": "Marine VHF",       "demod": "NFM", "channels": [
        (156.300, "Ch 06 Safety"), (156.450, "Ch 09 Hail"), (156.650, "Ch 13 Bridge"),
        (156.800, "Ch 16 Distress"), (157.100, "Ch 22A USCG"), (156.425, "Ch 68"),
        (156.475, "Ch 69"), (156.575, "Ch 71"), (156.625, "Ch 72"), (156.925, "Ch 78A")]},
    "murs":   {"label": "MURS",             "demod": "NFM", "channels": [
        (151.820, "MURS 1"), (151.880, "MURS 2"), (151.940, "MURS 3"),
        (154.570, "MURS 4 Blue"), (154.600, "MURS 5 Green")]},
    "ham2m":  {"label": "Ham 2m simplex",   "demod": "NFM", "channels": [
        (146.520, "2m Call"), (146.550, "Simplex"), (146.580, "Simplex"),
        (147.420, "Simplex"), (147.480, "Simplex"), (147.555, "Simplex")]},
    "ham70":  {"label": "Ham 70cm simplex", "demod": "NFM", "channels": [
        (446.000, "70cm Call"), (446.025, "Simplex"), (446.050, "Simplex"),
        (446.075, "Simplex"), (446.100, "Simplex"), (446.125, "Simplex")]},
    "rail":   {"label": "Railroad (AAR)",   "demod": "NFM", "channels": _rail_channels()},
    "cb":     {"label": "CB radio",         "demod": "AM",  "channels": _cb_channels()},
}


class RFSensor(Sensor):
    channel = "rf"
    name = "RF Spectrum (RTL-SDR R820T)"

    # The R820T tuner (Nooelec NESDR) covers roughly this range.
    TUNER_LOW_MHZ = 25
    TUNER_HIGH_MHZ = 1750
    STEP_MHZ = 2.4             # tune step across the FULL range (≈ the 2.4 MHz bw)
    SAMPLE_RATE = 2.4e6        # sweep sample rate
    READ_SAMPLES = 16 * 1024   # per tune; smaller keeps a full sweep fast (~10 s)
    PEAK_DB_OVER_FLOOR = 10.0  # first-cut threshold; real-world tuning is ongoing
    ANOMALY_DB = 8.0           # how much stronger than baseline counts as "new"
    SCAN_PERIOD = 0.5          # brief pause between full sweeps (background thread)

    TUNED_GAIN_DB = 30.0       # fixed manual gain for a stable, honest tuned spectrum
    NFFT = 2048                # FFT size for the tuned periodogram
    SPEC_BINS = 512            # display points (peak-held down from NFFT)

    def __init__(self):
        super().__init__()
        self.sdr = None
        self._dets = []
        self._spectrum = []     # [(freq_mhz, peak_db), ...] — the REAL swept spectrum
        self._floor = None      # estimated noise floor (dB)
        self._sweep_n = 0       # increments each completed sweep (waterfall row id)
        self._lock = threading.Lock()
        self._thread = None
        self._started = False

        # --- tuned (SDR#-style) view state ---
        self._mode = "sweep"            # "sweep" | "tuned" | "closing"
        self._epoch = 0                 # bumps when tuned center/span/gain changes
        self._tuned_applied_epoch = -1  # last epoch the tuned radio was configured to
        self._sweep_configured = False  # is the radio currently in sweep config?
        self._req = {                   # current tuned request
            "center_hz": 98_000_000,
            "span_hz": 2_400_000,
            "demod": "WFM",
            "audio": False,
        }
        self._tuned = None              # latest tuned spectrum dict for the UI
        self._tuned_n = 0               # tuned row counter (waterfall)
        # Audio is published as a sequence-numbered ring buffer (NOT a drain queue)
        # so multiple WS clients can each read independently — one client popping
        # frames must not starve another (e.g. the browser + a phone both listening).
        self._audio_buf = collections.deque(maxlen=48)   # (seq, bytes) int16 PCM
        self._audio_seq = 0
        self._audio_rate = AUDIO_RATE
        # IQ pipeline: the worker reads the dongle back-to-back (the USB read is
        # ~97% real-time on its own) and hands raw IQ blocks to a separate DSP
        # thread, so demod/FFT cost never stalls the read → gapless live audio.
        self._iq_q = queue.Queue(maxsize=4)
        self._dsp_thread = None

        # --- scanner (sweep/channel-flip/auto-seek/listen) state ---
        self._scan_cfg = dict(SCAN_BANDS["fm"], band="fm", kind="sweep",
                              squelch_db=8.0, dwell_s=3.0)
        self._scan_epoch = 0
        self._scan_pos = None       # current sweep frequency (Hz), sweep mode
        self._scan_channels = []    # active channel list [{mhz,name,demod,band}]
        self._scan_idx = 0          # current channel index, channels mode
        self._scan_auto = True      # True = auto-seek/flip; False = manual park+listen
        self._scan_locked = False   # dwelling on an active signal (auto mode)
        self._scan_lock_t = 0.0     # time we locked (for the dwell timeout)
        self._scan_active_t = 0.0   # last time the locked signal was above squelch
        self._scan_log = []         # recent hits [{mhz, name, over, t}]
        self._scan_n = 0            # state counter (bumps on update)
        self._scan_cur = None       # latest scan-state dict for the UI

        # --- RF signal characterization (content-free) + baseline/anomaly ---
        self._char_center = None    # centre the over-history belongs to
        self._char_hist = collections.deque(maxlen=24)  # recent over-floor dB (continuity)
        self._rf_baseline = None    # captured sweep spectrum {mhz: db} for anomaly flagging
        self._rf_baseline_n = 0
        self._baseline_req = False  # capture the baseline on the next sweep
        self._rf_anomalies = []     # latest [{mhz, db, delta}] new-vs-baseline

    def available(self) -> bool:
        return _HAS_RTL and np is not None

    def status(self) -> dict:
        """Honest status. When offline, distinguish 'no dongle' from 'dongle is
        plugged in but couldn't be opened' (almost always: another app or a second
        SENTRY instance is holding the single-app tuner)."""
        st = super().status()
        if not st.get("online") and not st.get("note"):
            st["note"] = self._offline_reason()
        return st

    def _offline_reason(self) -> str:
        if not (_HAS_RTL and np is not None):
            return ("RTL-SDR support isn't installed — run 'pip install pyrtlsdr numpy' "
                    "and install the RTL-SDR USB driver, then re-scan.")
        n = -1
        try:
            from rtlsdr import librtlsdr
            n = librtlsdr.rtlsdr_get_device_count()
        except Exception:
            n = -1
        if isinstance(n, int) and n > 0:
            return ("RTL-SDR DETECTED but it couldn't be opened — the tuner is single-app, so "
                    "another program or a second SENTRY instance is using it. Close the other one "
                    "(SDR#/HDSDR, or an extra SENTRY window) and re-scan; it will come online.")
        if n == 0:
            return "No RTL-SDR found on USB — plug one in (~$45) and RF lights up automatically."
        return "RTL-SDR is offline."

    def _setup(self):
        if self._started:
            return
        self.sdr = RtlSdr()
        self.sdr.sample_rate = self.SAMPLE_RATE
        self.sdr.gain = "auto"
        self._note = (
            "RTL-SDR R820T online — tuner covers ~%d MHz–%.2f GHz. SWEEP watches the "
            "surveillance ISM/cellular bands (315/433/868/915 MHz key-fob/sensor + cellular "
            "uplink); the live "
            "TUNED view lets you inspect & listen anywhere in range (try FM ~100 MHz). "
            "Only one tuner: tuning/listening pauses the background sweep. It CANNOT see "
            "2.4/5 GHz Wi-Fi/Bluetooth/video (above range — use the Wi-Fi & BLE sensors), "
            "cannot tune cellular voice, and never decodes encrypted/digital content."
            % (self.TUNER_LOW_MHZ, self.TUNER_HIGH_MHZ / 1000.0))
        self._started = True
        self._dsp_thread = threading.Thread(target=self._dsp_loop, daemon=True, name="rf-dsp")
        self._dsp_thread.start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="rf-sweep")
        self._thread.start()

    # ---- background worker (single owner of the tuner) ----------------------
    def _run_loop(self):
        while True:
            if self._mode == "closing":
                return
            try:
                if self._mode == "scan":
                    self._run_scan()                 # sweep → stop on activity → listen
                elif self._mode == "tuned":
                    with self._lock:
                        audio = self._req["audio"]
                    if audio:
                        self._run_audio_sync()       # pipelined sync read → DSP thread
                    else:
                        self._tuned_cycle()          # snappy sync spectrum-only
                else:
                    self._sweep_full()
                    time.sleep(self.SCAN_PERIOD)
            except Exception as e:               # device unplugged / driver hiccup
                self._error = str(e)
                with self._lock:
                    self._dets = []
                    self._spectrum = []
                time.sleep(0.3)

    # ====================== SWEEP MODE (surveillance) ========================
    def _power_at(self, center_hz, nsamp=None):
        """Read median (noise floor) and max (peak) power, in dB, around a tune.

        The RTL-SDR has a strong DC spike at the centre frequency (an artefact of
        the receiver, NOT a transmitter). We mask a few bins around DC before
        taking the peak, so a quiet band doesn't falsely read as "a signal". This
        is honest first-cut detection; finer real-world threshold tuning remains.
        """
        self.sdr.center_freq = center_hz
        samples = self.sdr.read_samples(nsamp or (64 * 1024))
        spectrum = np.fft.fftshift(np.fft.fft(samples))
        power = 20 * np.log10(np.abs(spectrum) + 1e-9)
        floor = float(np.median(power))
        n = len(power); c = n // 2; g = max(8, n // 100)   # mask ±1% around DC
        edge = np.concatenate([power[:c - g], power[c + g:]])
        peak = float(np.max(edge)) if edge.size else float(np.max(power))
        return floor, peak

    def _sweep_full(self):
        """Sweep the WHOLE tuner range once. Produces a real power-vs-frequency
        spectrum (for the UI display/waterfall) AND derives band detections from
        the same genuine RTL-SDR reads. Updates _spectrum/_floor/_dets atomically."""
        if not self.sdr:
            return
        # make sure the radio is in sweep config (it may have been left in a tuned
        # sample rate / fixed gain by a previous TUNED session)
        if not self._sweep_configured:
            try:
                self.sdr.sample_rate = self.SAMPLE_RATE
                self.sdr.gain = "auto"
            except Exception:
                pass
            self._sweep_configured = True
        spec = []        # (freq_mhz, peak_db) — peak power per tune, DC-spike masked
        floors = []
        f = self.TUNER_LOW_MHZ
        while f <= self.TUNER_HIGH_MHZ:
            if self._mode != "sweep":            # user jumped to the tuned view
                return
            try:
                floor, peak = self._power_at(f * 1e6, self.READ_SAMPLES)
                spec.append((round(float(f), 1), round(peak, 1)))
                floors.append(floor)
            except Exception:
                pass
            f += self.STEP_MHZ
        if not spec:
            return
        global_floor = float(np.median(floors))

        # RF baseline + anomaly: capture the room's normal RF, then flag anything
        # NEW — the core counter-surveillance "did something just appear?" workflow.
        with self._lock:
            if self._baseline_req:
                self._rf_baseline = {fmhz: peak for fmhz, peak in spec}
                self._rf_baseline_n += 1
                self._baseline_req = False
            baseline = dict(self._rf_baseline) if self._rf_baseline else None
        anomaly_freqs = {}     # fmhz -> delta dB vs baseline (NEW / much stronger)
        if baseline:
            for fmhz, peak in spec:
                over = peak - global_floor
                base = baseline.get(fmhz)
                if over >= self.PEAK_DB_OVER_FLOOR and (
                        base is None or (peak - base) >= self.ANOMALY_DB):
                    anomaly_freqs[fmhz] = round(peak - (base if base is not None else global_floor), 1)

        # detections: peaks rising above the floor inside a watched band, plus any
        # NEW-vs-baseline signal anywhere in range.
        dets = []
        for fmhz, peak in spec:
            over = peak - global_floor
            if over < self.PEAK_DB_OVER_FLOOR:
                continue
            band = self._band_for(fmhz)
            if not band:
                continue
            lo, hi, kind, cat, sev, note = band
            is_new = fmhz in anomaly_freqs
            dets.append(Detection(
                kind=kind, channel="rf", severity=("alert" if is_new else sev), category=cat,
                ident=f"{fmhz:.1f} MHz · {over:.0f} dB over floor"
                      + (f" · NEW (+{anomaly_freqs[fmhz]:.0f} dB vs baseline)" if is_new else ""),
                bandtxt=f"{lo}–{hi} MHz",
                behaviortxt=(("Appeared since the RF baseline was captured. " if is_new else "") + note),
                surveilling=self._surv(cat),
                cancapture="Energy detected only — identify it up close (SENTRY can't decode content)",
                capturingnow=f"Transmitting on {fmhz:.1f} MHz now",
                confidence=min(95, 55 + int(over)),
                device_type=kind, method="RF (RTL-SDR)",
                evidence=[f"peak {over:.0f} dB over noise floor at {fmhz:.1f} MHz"],
                freq_mhz=fmhz, rssi=peak, is_new=is_new,
            ))
        # anomalies OUTSIDE the watched bands — "something new is transmitting here"
        for fmhz in [f for f in anomaly_freqs if not self._band_for(f)][:10]:
            delta = anomaly_freqs[fmhz]
            peak = next((p for m, p in spec if m == fmhz), global_floor)
            dets.append(Detection(
                kind="Unidentified transmitter (new)", channel="rf",
                severity="suspect", category="unknown transmitter",
                ident=f"{fmhz:.1f} MHz · NEW (+{delta:.0f} dB vs baseline)",
                bandtxt=f"{fmhz:.1f} MHz",
                behaviortxt="Not present (or far weaker) when the RF baseline was captured — appeared since.",
                surveilling="Unknown — newly appeared",
                cancapture="Energy detected only — not decoded",
                capturingnow=f"Transmitting on {fmhz:.1f} MHz (new vs baseline)",
                confidence=min(90, 60 + int(delta)),
                device_type="Unidentified transmitter", method="RF (RTL-SDR) · baseline anomaly",
                evidence=[f"+{delta:.0f} dB vs baseline at {fmhz:.1f} MHz"],
                freq_mhz=fmhz, rssi=peak, is_new=True,
            ))
        dets = self._dedupe_by_band(dets)
        with self._lock:
            self._spectrum = spec
            self._floor = round(global_floor, 1)
            self._dets = dets
            self._rf_anomalies = [{"mhz": f, "delta": anomaly_freqs[f]} for f in anomaly_freqs]
            self._sweep_n += 1

    # ====================== TUNED MODE (live SDR view) =======================
    def set_view(self, center_mhz=None, span_hz=None, demod=None, audio=None):
        """Enter/refresh the live tuned view. Clamps to the tuner's real range and
        to a valid span. Switching center/span/gain bumps an epoch so the worker
        reconfigures the radio on its next cycle."""
        with self._lock:
            r = dict(self._req)
            if center_mhz is not None:
                c = max(self.TUNER_LOW_MHZ, min(self.TUNER_HIGH_MHZ, float(center_mhz)))
                r["center_hz"] = int(round(c * 1e6))
            if span_hz is not None:
                r["span_hz"] = min(VALID_SPANS_HZ, key=lambda s: abs(s - int(span_hz)))
            if demod is not None and str(demod).upper() in DEMODS:
                r["demod"] = str(demod).upper()
            if audio is not None:
                r["audio"] = bool(audio)
            changed = (r["center_hz"] != self._req["center_hz"]
                       or r["span_hz"] != self._req["span_hz"])
            self._req = r
            if changed or self._mode != "tuned":
                self._epoch += 1
            self._mode = "tuned"
            if not r["audio"]:
                self._audio_buf.clear()
        # The worker's read loop checks this state between blocks (≤ one block,
        # ~0.25 s) and reconfigures — no async cancel needed (that crashes the
        # device on this Windows/librtlsdr build), so switching is always clean.

    def set_sweep(self):
        """Return to the surveillance sweep (resumes background detection)."""
        with self._lock:
            self._mode = "sweep"
            self._tuned = None
            self._audio_buf.clear()
        self._tuned_applied_epoch = -1   # force a tuned reconfigure next time

    # ============== SCANNER MODE (sweep / channel-flip / auto-seek) ==========
    def _build_channels(self, list_key):
        """Expand a channel-list key (or 'all') into in-range channel dicts."""
        keys = list(CHANNEL_LISTS.keys()) if list_key == "all" else [list_key]
        out = []
        for k in keys:
            spec = CHANNEL_LISTS.get(k)
            if not spec:
                continue
            for mhz, name in spec["channels"]:
                if self.TUNER_LOW_MHZ <= mhz <= self.TUNER_HIGH_MHZ:
                    out.append({"mhz": float(mhz), "name": name,
                                "demod": spec["demod"], "band": spec["label"]})
        return out

    def set_scan(self, band=None, kind=None, list_key=None, auto=None,
                 lo_mhz=None, hi_mhz=None, step_khz=None, demod=None, squelch_db=None):
        """Enter scanner mode.

        Two kinds:
          * SWEEP   — step raw frequencies across lo..hi (preset band or custom),
            auto-stop on activity. (kind='sweep')
          * CHANNELS — flip through a known channel plan (FM, FRS/GMRS, marine…)
            like a car radio. 'auto' True = auto-seek (pause on activity); False =
            manual park+listen (use scan_next/scan_prev). 'all' = every plan.
        """
        sq = float(squelch_db) if squelch_db is not None else self._scan_cfg.get("squelch_db", 8.0)
        if kind is None:
            kind = "channels" if list_key else ("sweep" if (band in SCAN_BANDS) else
                                                self._scan_cfg.get("kind", "sweep"))
        with self._lock:
            if kind == "channels":
                lk = list_key or self._scan_cfg.get("list_key") or "fm"
                chans = self._build_channels(lk)
                if not chans:
                    chans = self._build_channels("fm"); lk = "fm"
                fmin = min(c["mhz"] for c in chans); fmax = max(c["mhz"] for c in chans)
                cfg = {"kind": "channels", "list_key": lk,
                       "label": ("All bands" if lk == "all"
                                 else CHANNEL_LISTS.get(lk, {}).get("label", lk)),
                       "lo": fmin, "hi": fmax, "squelch_db": sq,
                       "dwell_s": self._scan_cfg.get("dwell_s", 3.0)}
                self._scan_channels = chans
                self._scan_idx = 0
                self._scan_auto = True if auto is None else bool(auto)
            else:
                if band and band in SCAN_BANDS:
                    cfg = dict(SCAN_BANDS[band], band=band)
                else:
                    cfg = dict(self._scan_cfg)
                if lo_mhz is not None:
                    cfg["lo"] = max(self.TUNER_LOW_MHZ, min(self.TUNER_HIGH_MHZ, float(lo_mhz))); cfg["band"] = "custom"
                if hi_mhz is not None:
                    cfg["hi"] = max(self.TUNER_LOW_MHZ, min(self.TUNER_HIGH_MHZ, float(hi_mhz))); cfg["band"] = "custom"
                if step_khz is not None:
                    cfg["step_khz"] = max(1.0, float(step_khz))
                if demod is not None and str(demod).upper() in DEMODS:
                    cfg["demod"] = str(demod).upper()
                cfg["kind"] = "sweep"
                cfg.setdefault("span_hz", 240000); cfg.setdefault("half_bw", 7000)
                cfg["squelch_db"] = sq
                cfg["dwell_s"] = self._scan_cfg.get("dwell_s", 3.0)
                self._scan_pos = None
                self._scan_auto = True
            self._scan_cfg = cfg
            self._scan_epoch += 1
            self._scan_locked = False
            self._scan_log = []
            self._mode = "scan"
            self._audio_buf.clear()

    def scan_skip(self):
        """Resume seeking from a locked/parked signal (find the next one)."""
        with self._lock:
            if not self._scan_locked:
                return
            self._scan_locked = False
            if self._scan_cfg.get("kind") == "channels" and self._scan_channels:
                self._scan_idx = (self._scan_idx + 1) % len(self._scan_channels)
            elif self._scan_pos is not None:
                self._scan_pos += int(self._scan_cfg.get("step_khz", 25) * 1000)
            self._audio_buf.clear()

    def scan_next(self):
        """Flip to the next channel/step (manual)."""
        self._scan_step(+1)

    def scan_prev(self):
        """Flip to the previous channel/step (manual)."""
        self._scan_step(-1)

    def _scan_step(self, d):
        with self._lock:
            if self._scan_cfg.get("kind") == "channels" and self._scan_channels:
                self._scan_idx = (self._scan_idx + d) % len(self._scan_channels)
            elif self._scan_pos is not None:
                self._scan_pos += d * int(self._scan_cfg.get("step_khz", 25) * 1000)
            self._scan_locked = False
            self._audio_buf.clear()

    def scan_auto(self, on):
        """Toggle auto-seek (True = scan with dwell) vs manual HOLD (False = stay
        on the current channel/frequency and keep listening)."""
        with self._lock:
            self._scan_auto = bool(on)
            self._scan_locked = False          # neither dwell-locked now
            self._scan_lock_t = 0.0
            self._audio_buf.clear()

    def scan_set_squelch(self, squelch_db):
        with self._lock:
            self._scan_cfg["squelch_db"] = float(squelch_db)

    def _half_bw_for(self, demod):
        return 90000 if demod == "WFM" else 7000

    def _apply_tuned_config(self, req):
        """Put the radio into the requested tuned config (rate/centre/fixed gain)."""
        self.sdr.sample_rate = req["span_hz"]
        self.sdr.center_freq = req["center_hz"]
        self.sdr.gain = self._nearest_gain(self.TUNED_GAIN_DB)
        self._sweep_configured = False   # sweep will need to reconfigure later

    def _tuned_cycle(self):
        """One synchronous read at the tuned centre → real spectrum (audio OFF).
        Snappy: a small block for a responsive analyzer/waterfall."""
        if not self.sdr:
            return
        with self._lock:
            req = dict(self._req)
            epoch = self._epoch
        if epoch != self._tuned_applied_epoch:
            try:
                self._apply_tuned_config(req)
            except Exception as e:
                self._error = str(e); time.sleep(0.2); return
            self._tuned_applied_epoch = epoch
        fs = float(req["span_hz"])
        try:
            x = self.sdr.read_samples(self.NFFT * 16)
        except Exception as e:
            self._error = str(e); time.sleep(0.1); return
        self._emit_block(x, req, fs, audio=False)

    def _run_audio_sync(self):
        """LISTEN: read the dongle synchronously, back-to-back, in ~0.25 s blocks
        and hand each raw IQ block to the DSP thread. Back-to-back synchronous
        reads are ~97% real-time on their own (the per-call USB overhead amortises
        over a big block), and moving demod/FFT to the DSP thread keeps that cost
        off the read path — so audio stays gapless WITHOUT the async reader, whose
        cancel corrupts the device on this Windows/librtlsdr build. The loop
        re-checks the requested view each block, so retune/demod/stop switch
        cleanly within one block."""
        if not self.sdr:
            return
        with self._lock:
            req = dict(self._req)
            epoch = self._epoch
        try:
            self._apply_tuned_config(req)
        except Exception as e:
            self._error = str(e); time.sleep(0.2); return
        self._tuned_applied_epoch = epoch
        fs = float(req["span_hz"])
        k = self._audio_decim(fs, req["demod"])
        nsamp = max(k, int(round(fs * 0.25 / k)) * k)   # ~0.25 s, decimates cleanly
        while (self._mode == "tuned" and self._epoch == epoch
               and self._req["audio"]):
            try:
                x = self.sdr.read_samples(nsamp)
            except Exception as e:
                self._error = str(e); time.sleep(0.1); return
            try:
                self._iq_q.put_nowait((x, req, fs))
            except queue.Full:
                pass                                  # DSP behind (rare): drop this block

    def _dsp_loop(self):
        """Consume IQ blocks from the read pipeline and turn each into a real
        spectrum + demodulated audio. Runs parallel to the USB read so reads
        never wait on DSP."""
        while True:
            try:
                x, req, fs = self._iq_q.get(timeout=0.5)
            except queue.Empty:
                continue
            if self._mode == "closing":
                return
            try:
                self._emit_block(x, req, fs, audio=True)
            except Exception as e:                    # one bad block ≠ dead stream
                self._error = str(e)

    def _emit_block(self, x, req, fs, audio):
        """Build the real spectrum from one IQ block and (optionally) demodulate
        audio, publishing both atomically for the UI/clients."""
        spec = self._periodogram(x, req["center_hz"], fs)
        spec["analysis"] = self._characterize(spec, fs)   # content-free signal id
        pcm = None
        if audio:
            pcm, arate = self._demodulate(x, fs, req["demod"])
        with self._lock:
            self._tuned_n += 1
            spec["n"] = self._tuned_n
            self._tuned = spec
            if pcm is not None:
                self._audio_rate = arate
                self._audio_seq += 1
                self._audio_buf.append((self._audio_seq, pcm))

    # ---- scanner worker ----------------------------------------------------
    def _run_scan(self):
        """Dispatch to the raw-frequency sweep or the channel-flip scanner."""
        if not self.sdr:
            return
        with self._lock:
            cfg = dict(self._scan_cfg)
            epoch = self._scan_epoch
        if cfg.get("kind") == "channels":
            self._run_scan_channels(cfg, epoch)
        else:
            self._run_scan_sweep(cfg, epoch)

    def _run_scan_channels(self, cfg, epoch):
        """Flip through a known channel plan. In AUTO mode, step channel-by-channel
        and lock+listen on activity above squelch (Seek). In MANUAL mode, park on
        the current channel and listen continuously; scan_next/prev move it."""
        chans = list(self._scan_channels)
        if not chans:
            time.sleep(0.2); return
        cur_sr = None
        while self._mode == "scan" and self._scan_epoch == epoch:
            with self._lock:
                idx = self._scan_idx % len(chans)
                self._scan_idx = idx
                auto = self._scan_auto
                locked = self._scan_locked
                squelch = self._scan_cfg["squelch_db"]
            ch = chans[idx]
            center = int(round(ch["mhz"] * 1e6)); demod = ch["demod"]
            sr = 2400000 if demod == "WFM" else 240000
            half_bw = self._half_bw_for(demod)
            if sr != cur_sr:
                try:
                    self.sdr.sample_rate = sr
                    self.sdr.gain = self._nearest_gain(self.TUNED_GAIN_DB)
                except Exception as e:
                    self._error = str(e); time.sleep(0.2); continue
                cur_sr = sr; self._sweep_configured = False
            if (not auto) or locked:
                # listen on this channel (manual HOLD, or auto dwell on a hit)
                k = self._audio_decim(sr, demod)
                nsamp = max(k, int(round(sr * 0.25 / k)) * k)
                try:
                    self.sdr.center_freq = center
                    x = self.sdr.read_samples(nsamp)
                except Exception as e:
                    self._error = str(e); time.sleep(0.1); continue
                req = {"center_hz": center, "span_hz": sr, "demod": demod, "audio": True}
                try:
                    self._iq_q.put_nowait((x, req, float(sr)))
                except queue.Full:
                    pass
                over = self._block_over(x, sr, half_bw)
                self._set_scan_state_ch(cfg, chans, idx, over, locked=(auto and locked), auto=auto)
                if auto and locked and self._scan_resume_due(over, squelch, cfg):
                    with self._lock:
                        self._scan_locked = False
                        self._scan_idx = (idx + 1) % len(chans)   # dwell over → next
                    self._audio_buf.clear()
            else:
                # auto-seek: measure this channel, lock if active else advance
                try:
                    over = self._channel_active(center, sr, half_bw)
                except Exception as e:
                    self._error = str(e); over = -999.0; time.sleep(0.04)
                self._set_scan_state_ch(cfg, chans, idx, over, locked=False, auto=True)
                if over >= squelch:
                    self._scan_lock(round(center / 1e6, 4), over, ch["name"])
                else:
                    with self._lock:
                        self._scan_idx = (idx + 1) % len(chans)

    def _run_scan_sweep(self, cfg, epoch):
        """Raw-frequency sweep across lo..hi. While unlocked, step by step_khz
        measuring power and stop when one rises above squelch. While locked, read
        audio blocks at the parked frequency and feed them to the DSP pipeline so
        the spectrum + audio stream exactly like the tuned listener."""
        sr = int(cfg["span_hz"]); demod = cfg["demod"]
        lo = int(round(cfg["lo"] * 1e6)); hi = int(round(cfg["hi"] * 1e6))
        step = int(round(cfg["step_khz"] * 1000)); half_bw = int(cfg["half_bw"])
        try:
            self.sdr.sample_rate = sr
            self.sdr.gain = self._nearest_gain(self.TUNED_GAIN_DB)
        except Exception as e:
            self._error = str(e); time.sleep(0.2); return
        self._sweep_configured = False
        with self._lock:
            if self._scan_pos is None or not (lo <= self._scan_pos <= hi):
                self._scan_pos = lo

        while self._mode == "scan" and self._scan_epoch == epoch:
            with self._lock:
                auto = self._scan_auto
                locked = self._scan_locked
                pos = self._scan_pos
                squelch = self._scan_cfg["squelch_db"]
            if (not auto) or locked:
                # listen at pos (manual HOLD, or auto dwell on a hit)
                k = self._audio_decim(sr, demod)
                nsamp = max(k, int(round(sr * 0.25 / k)) * k)
                try:
                    self.sdr.center_freq = pos
                    x = self.sdr.read_samples(nsamp)
                except Exception as e:
                    self._error = str(e); time.sleep(0.1); continue
                req = {"center_hz": pos, "span_hz": sr, "demod": demod, "audio": True}
                try:
                    self._iq_q.put_nowait((x, req, float(sr)))
                except queue.Full:
                    pass
                over = self._block_over(x, sr, half_bw)
                self._set_scan_state(cfg, pos, over, locked=(auto and locked), auto=auto)
                if auto and locked and self._scan_resume_due(over, squelch, cfg):
                    npos = pos + step
                    if npos > hi:
                        npos = lo
                    with self._lock:
                        self._scan_locked = False
                        self._scan_pos = npos                 # dwell over → next
                    self._audio_buf.clear()
            else:
                try:
                    over = self._channel_active(pos, sr, half_bw)
                except Exception as e:
                    self._error = str(e); over = -999.0; time.sleep(0.05)
                self._set_scan_state(cfg, pos, over, locked=False, auto=True)
                if over >= squelch:
                    self._scan_lock(round(pos / 1e6, 4), over, None)
                else:
                    npos = pos + step
                    if npos > hi:
                        npos = lo
                    with self._lock:
                        self._scan_pos = npos

    def _scan_lock(self, mhz, over, name):
        """Lock (dwell) on an active signal during auto-seek, log the hit."""
        now = time.time()
        with self._lock:
            self._scan_locked = True
            self._scan_lock_t = now
            self._scan_active_t = now
            entry = {"mhz": mhz, "over": round(float(over), 1), "t": self._scan_n}
            if name:
                entry["name"] = name
            self._scan_log.insert(0, entry)
            self._scan_log = self._scan_log[:30]

    def _scan_resume_due(self, over, squelch, cfg):
        """In auto mode, decide whether the dwell on a locked signal is over and
        we should resume seeking — after the max dwell time, OR once the signal
        has gone quiet for ~1 s (so brief transmissions release quickly while a
        constant carrier like an FM station is held for the full dwell)."""
        now = time.time()
        if over >= squelch:
            self._scan_active_t = now
        dwell = cfg.get("dwell_s", 3.0)
        return (now - self._scan_lock_t) > dwell or (now - self._scan_active_t) > 1.0

    def _channel_active(self, center_hz, sr, half_bw):
        """Return dB of the strongest carrier within ±half_bw of a channel centre,
        above the local noise floor (DC spike masked). Used to decide squelch."""
        self.sdr.center_freq = center_hz
        N = self.NFFT
        x = self.sdr.read_samples(N * 4)
        win = np.hanning(N)
        acc = np.zeros(N)
        for k in range(4):
            seg = x[k * N:(k + 1) * N] * win
            acc += np.abs(np.fft.fftshift(np.fft.fft(seg))) ** 2
        pdb = 10.0 * np.log10(acc / 4.0 + 1e-12)
        floor = float(np.median(pdb))
        binhz = sr / float(N)
        c = N // 2
        bw = max(2, int(half_bw / binhz))
        g = max(2, int(3000 / binhz))                 # mask ±3 kHz DC spike
        lo_i = max(0, c - bw); hi_i = min(N, c + bw)
        window = np.concatenate([pdb[lo_i:c - g], pdb[c + g:hi_i]])
        peak = float(np.max(window)) if window.size else float(np.max(pdb))
        return peak - floor

    def _block_over(self, x, sr, half_bw):
        """Same carrier-over-floor measure as _channel_active, but from an IQ
        block we already read — used for the live activity indicator while
        listening, with no extra tune/read."""
        N = self.NFFT
        nseg = max(1, min(4, len(x) // N))
        if nseg < 1 or len(x) < N:
            return 0.0
        win = np.hanning(N)
        acc = np.zeros(N)
        for k in range(nseg):
            seg = x[k * N:(k + 1) * N] * win
            acc += np.abs(np.fft.fftshift(np.fft.fft(seg))) ** 2
        pdb = 10.0 * np.log10(acc / nseg + 1e-12)
        floor = float(np.median(pdb))
        binhz = sr / float(N); c = N // 2
        bw = max(2, int(half_bw / binhz)); g = max(2, int(3000 / binhz))
        window = np.concatenate([pdb[max(0, c - bw):c - g], pdb[c + g:min(N, c + bw)]])
        peak = float(np.max(window)) if window.size else float(np.max(pdb))
        return peak - floor

    def _set_scan_state(self, cfg, pos, over, locked, auto=True):
        with self._lock:
            self._scan_n += 1
            self._scan_cur = {
                "n": self._scan_n, "kind": "sweep", "band": cfg.get("band", "custom"),
                "label": cfg.get("label", "Custom"),
                "lo_mhz": round(cfg["lo"], 4), "hi_mhz": round(cfg["hi"], 4),
                "step_khz": cfg["step_khz"], "demod": cfg["demod"],
                "squelch_db": self._scan_cfg["squelch_db"],
                "freq_mhz": round(pos / 1e6, 4),
                "over_db": (None if over is None else round(float(over), 1)),
                "locked": bool(locked), "auto": bool(auto),
                "ch_name": None, "idx": None, "total": None,
                "log": list(self._scan_log),
                "audio_rate": self._audio_rate,
            }

    def _set_scan_state_ch(self, cfg, chans, idx, over, locked, auto):
        ch = chans[idx]
        with self._lock:
            self._scan_n += 1
            self._scan_cur = {
                "n": self._scan_n, "kind": "channels", "list_key": cfg.get("list_key"),
                "label": cfg.get("label", "Channels"),
                "lo_mhz": round(cfg["lo"], 4), "hi_mhz": round(cfg["hi"], 4),
                "demod": ch["demod"], "squelch_db": self._scan_cfg["squelch_db"],
                "freq_mhz": round(ch["mhz"], 4), "ch_name": ch["name"],
                "ch_band": ch.get("band", ""), "idx": idx, "total": len(chans),
                "over_db": (None if over is None else round(float(over), 1)),
                "locked": bool(locked), "auto": bool(auto),
                "log": list(self._scan_log),
                "audio_rate": self._audio_rate,
            }

    def _characterize(self, spec, fs):
        """Content-free RF characterization of the tuned signal: occupied
        bandwidth (−10 dB), strength over the noise floor, continuity (continuous
        vs bursting, from recent frames), and a HONEST modulation/type GUESS from
        the spectral SHAPE + band. It describes 'something is transmitting here,
        like this' — it never decodes or reveals content."""
        pts = spec.get("points") or []
        pk = spec.get("peak"); floor = spec.get("floor")
        if not pts or pk is None or floor is None:
            return None
        dbs = [p[1] for p in pts]
        n = len(dbs)
        pk_db = pk["db"]; over = round(pk_db - floor, 1)
        # find the peak bin, then the contiguous OCCUPIED span around it. Use a
        # threshold relative to the noise floor (floor + 6 dB), capped to peak-25 dB
        # — this captures the real occupied bandwidth (e.g. FM's wide sidebands)
        # rather than just the narrow tip at the carrier.
        pk_i = max(range(n), key=lambda i: dbs[i])
        thr = max(floor + 6.0, pk_db - 25.0)
        lo = pk_i
        while lo > 0 and dbs[lo - 1] > thr:
            lo -= 1
        hi = pk_i
        while hi < n - 1 and dbs[hi + 1] > thr:
            hi += 1
        bin_hz = fs / float(n)
        bw_hz = (hi - lo + 1) * bin_hz
        bw_khz = round(bw_hz / 1000.0, 1)
        center = spec.get("center_mhz")
        # continuity from recent over-floor history at this centre
        if self._char_center != center:
            self._char_center = center; self._char_hist.clear()
        self._char_hist.append(over)
        h = list(self._char_hist)
        present = sum(1 for v in h if v >= 6.0)
        duty = present / len(h) if h else 0.0
        if len(h) < 4:
            continuity = "measuring…"
        elif duty >= 0.85:
            continuity = "continuous carrier"
        elif duty <= 0.15:
            continuity = "quiet (no steady signal)"
        else:
            continuity = "intermittent / bursting"
        # modulation/type GUESS from bandwidth + band + strength (clearly a guess)
        if over < 6:
            guess = "no clear signal above the noise"
        elif bw_khz < 3:
            guess = "narrow carrier / CW / beacon / tone"
        elif bw_khz < 20:
            guess = "narrowband — NFM voice or data burst (ham/FRS/GMRS/business)"
        elif bw_khz < 60:
            guess = "narrow data / paging-class signal"
        elif bw_khz < 300:
            guess = "wideband FM — broadcast or wideband voice"
        else:
            guess = "very wide — analog video or wideband data"
        # band context sharpens the guess
        if center is not None:
            if 87.5 <= center <= 108 and bw_khz >= 80:
                guess = "broadcast FM (WFM) — wide audio"
            elif 118 <= center <= 137:
                guess = "AM voice (aviation/air band)" if over >= 6 else guess
            elif (313 <= center <= 317 or 433 <= center <= 435) and continuity.startswith("interm"):
                guess = "ISM burst — likely a key-fob/remote/sensor (OOK/FSK)"
        return {"bw_khz": bw_khz, "over_db": over, "continuity": continuity,
                "guess": guess,
                "note": "Guess from RF shape only — content is NOT decoded or revealed."}

    def _periodogram(self, x, center_hz, fs):
        """Real averaged power spectrum across the tuned span, peak-held down to
        SPEC_BINS display points so narrow carriers stay visible."""
        N = self.NFFT
        # cap averaging at a few segments: enough to smooth the trace, but cheap
        # so a wide span never starves the real-time audio throughput.
        nseg = max(1, min(8, len(x) // N))
        win = np.hanning(N)
        acc = np.zeros(N)
        for i in range(nseg):
            seg = x[i * N:(i + 1) * N] * win
            acc += np.abs(np.fft.fftshift(np.fft.fft(seg))) ** 2
        acc /= nseg
        pdb = 10.0 * np.log10(acc + 1e-12)
        # peak-hold bin down to SPEC_BINS
        bins = min(self.SPEC_BINS, N)
        step = N // bins
        pdb = pdb[:bins * step].reshape(bins, step).max(axis=1)
        f0 = center_hz - fs / 2.0
        df = fs / N * step
        pts = [[round((f0 + (i + 0.5) * df) / 1e6, 4), round(float(pdb[i]), 1)]
               for i in range(bins)]
        floor = float(np.median(pdb))
        pk_i = int(np.argmax(pdb))
        return {
            "center_mhz": round(center_hz / 1e6, 4),
            "span_hz": int(fs),
            "low_mhz": round(f0 / 1e6, 4),
            "high_mhz": round((center_hz + fs / 2.0) / 1e6, 4),
            "floor": round(floor, 1),
            "peak": {"mhz": pts[pk_i][0], "db": pts[pk_i][1]},
            "demod": self._req["demod"],
            "audio": bool(self._req["audio"]),
            "audio_rate": self._audio_rate,
            "gain_db": self.TUNED_GAIN_DB,
            "points": pts,
        }

    # ---- demodulation (REAL analog WFM/AM/NFM only) -------------------------
    @staticmethod
    def _boxdec(sig, k):
        """Boxcar decimate by integer k (cheap anti-alias low-pass + downsample)."""
        if k <= 1:
            return sig
        t = (len(sig) // k) * k
        return sig[:t].reshape(-1, k).mean(axis=1)

    def _audio_decim(self, fs, demod):
        """Total integer decimation from span fs down to the ~48 kHz audio rate."""
        if demod == "WFM":
            k1 = max(1, int(round(fs / 240000)))      # isolate the ~200 kHz FM channel
            return k1 * max(1, int(round((fs / k1) / AUDIO_RATE)))
        # AM / NFM: take the envelope/discriminator at fs then decimate to audio
        return max(1, int(round(fs / AUDIO_RATE)))

    def _demodulate(self, x, fs, demod):
        """Demodulate REAL IQ to mono int16 PCM. WFM/AM/NFM only — open analog
        modulation. Returns (bytes, rate) or (None, rate)."""
        if demod == "WFM":
            k1 = max(1, int(round(fs / 240000)))
            ch = self._boxdec(x, k1)                  # complex IF ~240 kHz
            if_rate = fs / k1
            disc = np.angle(ch[1:] * np.conj(ch[:-1]))
            k2 = max(1, int(round(if_rate / AUDIO_RATE)))
            audio = self._boxdec(disc, k2)
            arate = if_rate / k2
            audio = self._deemphasis(audio, arate)
            gain = 9000.0
        elif demod == "NFM":
            disc = np.angle(x[1:] * np.conj(x[:-1]))
            k = max(1, int(round(fs / AUDIO_RATE)))
            audio = self._boxdec(disc, k)
            arate = fs / k
            gain = 16000.0                            # narrow deviation → more gain
        elif demod == "AM":
            env = np.abs(x)
            k = max(1, int(round(fs / AUDIO_RATE)))
            audio = self._boxdec(env, k)
            arate = fs / k
            audio = audio - np.mean(audio)            # drop the DC carrier term
            rms = float(np.sqrt(np.mean(audio ** 2))) or 1.0
            gain = 0.2 * 32767.0 / max(rms, 1e-6)     # AM amplitude varies → normalise
        else:
            return None, AUDIO_RATE
        samples = np.clip(audio * gain, -32767, 32767).astype('<i2')
        return samples.tobytes(), int(round(arate))

    @staticmethod
    def _deemphasis(a, fs, tau=75e-6):
        """75 µs FM de-emphasis — tames bright treble hiss. Implemented as a short
        FIR approximation of the one-pole IIR so it's a single vectorised convolve
        (no per-sample Python loop), which keeps each audio cycle near real-time."""
        alpha = 1.0 - np.exp(-1.0 / (fs * tau))
        b = 1.0 - alpha
        K = int(min(64, max(4, np.log(0.01) / np.log(b)))) if b < 1 else 4
        h = alpha * (b ** np.arange(K))
        h /= h.sum()                      # unity DC gain (preserve level)
        return np.convolve(a, h, mode="same")

    def _nearest_gain(self, db):
        try:
            gains = self.sdr.valid_gains_db
            return min(gains, key=lambda g: abs(g - db))
        except Exception:
            return db

    # ---- getters for the server/UI -----------------------------------------
    def spectrum(self):
        """The latest real swept spectrum for the UI (sweep mode, power vs freq)."""
        with self._lock:
            return {"n": self._sweep_n, "floor": self._floor,
                    "low_mhz": self.TUNER_LOW_MHZ, "high_mhz": self.TUNER_HIGH_MHZ,
                    "bands": [[b[0], b[1]] for b in BANDS],
                    "points": list(self._spectrum),
                    "baseline_n": self._rf_baseline_n,
                    "baseline_set": self._rf_baseline is not None,
                    "anomalies": list(self._rf_anomalies)}

    def capture_rf_baseline(self):
        """Snapshot the current full-range RF spectrum as the baseline; later
        sweeps flag anything NEW or much stronger than it."""
        with self._lock:
            self._baseline_req = True

    def clear_rf_baseline(self):
        with self._lock:
            self._rf_baseline = None
            self._rf_anomalies = []

    def _scan_listening(self):
        """True when the scanner is producing audio: manual HOLD (always listens,
        sweep or channels), or auto mode while dwelling on a locked signal."""
        if self._mode != "scan":
            return False
        if not self._scan_auto:
            return True
        return bool(self._scan_locked)

    def tuned_state(self):
        """Latest live spectrum for the UI — from the tuned listener, or from the
        scanner while it's listening (parked/locked) so the scanner shows a real
        spectrum at the current frequency. None otherwise."""
        with self._lock:
            live = (self._mode == "tuned") or self._scan_listening()
            if not live or self._tuned is None:
                return None
            return dict(self._tuned)

    def scan_state(self):
        """Latest scanner state (sweep position, lock, activity log). None unless
        in scanner mode."""
        with self._lock:
            if self._mode != "scan" or self._scan_cur is None:
                return None
            return dict(self._scan_cur)

    def audio_active(self):
        """True when SENTRY should be producing/streaming audio right now —
        the tuned listener with audio on, or the scanner parked/locked."""
        with self._lock:
            if self._mode == "tuned":
                return bool(self._req["audio"])
            return self._scan_listening()

    def audio_since(self, after_seq):
        """Return PCM frames newer than after_seq WITHOUT consuming them, so every
        client reads independently. Returns (rate, [bytes], newest_seq). A client
        that falls further behind than the ring buffer (48 frames ≈ 5 s) simply
        resyncs to the newest — a brief gap, never a crash."""
        with self._lock:
            frames = [b for (s, b) in self._audio_buf if s > after_seq]
            return self._audio_rate, frames, self._audio_seq

    def view_meta(self):
        """Static info the UI needs to build the tuned + scanner controls."""
        bands = [{"key": k, "label": v["label"], "lo": v["lo"], "hi": v["hi"],
                  "demod": v["demod"]} for k, v in SCAN_BANDS.items()]
        chan_lists = [{"key": k, "label": v["label"], "demod": v["demod"],
                       "count": len(v["channels"])} for k, v in CHANNEL_LISTS.items()]
        return {"spans": VALID_SPANS_HZ, "demods": list(DEMODS),
                "low_mhz": self.TUNER_LOW_MHZ, "high_mhz": self.TUNER_HIGH_MHZ,
                "audio_rate": AUDIO_RATE, "scan_bands": bands,
                "channel_lists": chan_lists}

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
        # signal the read loop to exit (it checks mode between blocks), let the
        # in-flight synchronous read finish, then release the device.
        self._mode = "closing"
        if self.sdr:
            time.sleep(0.35)            # > one read block, so no read is in flight
            try:
                self.sdr.close()
            except Exception:
                pass
