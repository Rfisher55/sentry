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

        # --- scanner (sweep/stop-on-activity/listen) state ---
        self._scan_cfg = dict(SCAN_BANDS["fm"], band="fm", squelch_db=8.0)
        self._scan_epoch = 0
        self._scan_pos = None       # current sweep frequency (Hz)
        self._scan_locked = False   # parked on an active signal (listening)
        self._scan_log = []         # recent hits [{mhz, over, t}]
        self._scan_n = 0            # state counter (bumps on update)
        self._scan_cur = None       # latest scan-state dict for the UI

    def available(self) -> bool:
        return _HAS_RTL and np is not None

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
        # detections: peaks rising above the floor AND inside a watched band only
        dets = []
        for fmhz, peak in spec:
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
        dets = self._dedupe_by_band(dets)
        with self._lock:
            self._spectrum = spec
            self._floor = round(global_floor, 1)
            self._dets = dets
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

    # ====================== SCANNER MODE (sweep + listen) ====================
    def set_scan(self, band=None, lo_mhz=None, hi_mhz=None, step_khz=None,
                 demod=None, squelch_db=None):
        """Enter scanner mode. Either pick a preset band, or pass a custom
        lo/hi/step/demod. The worker sweeps the range, stops when a channel rises
        above squelch, and listens; scan_skip() resumes the sweep."""
        with self._lock:
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
            cfg.setdefault("span_hz", 240000)
            cfg.setdefault("half_bw", 7000)
            cfg["squelch_db"] = float(squelch_db) if squelch_db is not None else self._scan_cfg.get("squelch_db", 8.0)
            self._scan_cfg = cfg
            self._scan_epoch += 1
            self._scan_pos = None
            self._scan_locked = False
            self._scan_log = []
            self._mode = "scan"
            self._audio_buf.clear()

    def scan_skip(self):
        """Resume sweeping from a locked/parked signal (find the next one)."""
        with self._lock:
            if self._scan_locked:
                self._scan_locked = False
                step = int(self._scan_cfg["step_khz"] * 1000)
                if self._scan_pos is not None:
                    self._scan_pos += step
                self._audio_buf.clear()

    def scan_set_squelch(self, squelch_db):
        with self._lock:
            self._scan_cfg["squelch_db"] = float(squelch_db)

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
        """Sweep the configured band. While unlocked, step channel-by-channel
        measuring power and stop when one rises above squelch. While locked, read
        audio blocks at the parked frequency and feed them to the DSP pipeline so
        the spectrum + audio stream exactly like the tuned listener."""
        if not self.sdr:
            return
        with self._lock:
            cfg = dict(self._scan_cfg)
            epoch = self._scan_epoch
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
                locked = self._scan_locked
                pos = self._scan_pos
                squelch = self._scan_cfg["squelch_db"]
            if locked:
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
                self._set_scan_state(cfg, pos, None, True)
            else:
                try:
                    over = self._channel_active(pos, sr, half_bw)
                except Exception as e:
                    self._error = str(e); over = -999.0; time.sleep(0.05)
                self._set_scan_state(cfg, pos, over, False)
                if over >= squelch:
                    with self._lock:
                        self._scan_locked = True
                        self._scan_log.insert(0, {"mhz": round(pos / 1e6, 4),
                                                  "over": round(float(over), 1),
                                                  "t": self._scan_n})
                        self._scan_log = self._scan_log[:30]
                else:
                    pos += step
                    if pos > hi:
                        pos = lo
                    with self._lock:
                        self._scan_pos = pos

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

    def _set_scan_state(self, cfg, pos, over, locked):
        with self._lock:
            self._scan_n += 1
            self._scan_cur = {
                "n": self._scan_n, "band": cfg.get("band", "custom"),
                "label": cfg.get("label", "Custom"),
                "lo_mhz": round(cfg["lo"], 4), "hi_mhz": round(cfg["hi"], 4),
                "step_khz": cfg["step_khz"], "demod": cfg["demod"],
                "squelch_db": self._scan_cfg["squelch_db"],
                "freq_mhz": round(pos / 1e6, 4),
                "over_db": (None if over is None else round(float(over), 1)),
                "locked": bool(locked),
                "log": list(self._scan_log),
                "audio_rate": self._audio_rate,
            }

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
                    "points": list(self._spectrum)}

    def tuned_state(self):
        """Latest live spectrum for the UI — from the tuned listener, or from the
        scanner when it's parked on a signal (so the scanner shows a real spectrum
        at the locked frequency). None otherwise."""
        with self._lock:
            live = (self._mode == "tuned"
                    or (self._mode == "scan" and self._scan_locked))
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
        the tuned listener with audio on, or the scanner parked on a signal."""
        with self._lock:
            if self._mode == "tuned":
                return bool(self._req["audio"])
            if self._mode == "scan":
                return bool(self._scan_locked)
            return False

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
        return {"spans": VALID_SPANS_HZ, "demods": list(DEMODS),
                "low_mhz": self.TUNER_LOW_MHZ, "high_mhz": self.TUNER_HIGH_MHZ,
                "audio_rate": AUDIO_RATE, "scan_bands": bands}

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
