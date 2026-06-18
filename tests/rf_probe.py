"""Real RF probe: open the RTL-SDR and report actual power across the tuner's
range right now — the watched surveillance bands plus a few reference points
(so you can see it's genuinely receiving). Read-only diagnostic. Must be run
with the SENTRY server stopped (only one process can own the radio)."""
import sys, io
import numpy as np
from rtlsdr import RtlSdr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# (label, MHz, watched-by-SENTRY?)
PROBES = [
    ("FM broadcast (ref, skipped)",   98.1, False),
    ("Airband (ref, skipped)",        130.0, False),
    ("433 ISM  (WATCHED)",            433.9, True),
    ("700 LTE downlink (ref)",        751.0, False),
    ("868 ISM  (WATCHED)",            868.0, True),
    ("Cellular downlink (ref)",       881.0, False),
    ("915 ISM  (WATCHED)",            915.0, True),
    ("1710 LTE/AWS uplink (WATCHED)", 1730.0, True),
]

sdr = RtlSdr()
sdr.sample_rate = 2.4e6
sdr.gain = "auto"
floors = []
rows = []
for label, mhz, watched in PROBES:
    sdr.center_freq = mhz * 1e6
    s = sdr.read_samples(64 * 1024)
    p = 20 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(s))) + 1e-9)
    n = len(p); c = n // 2; g = max(8, n // 100)          # mask DC spike (±1%)
    edge = np.concatenate([p[:c - g], p[c + g:]])
    floor, peak = float(np.median(p)), float(np.max(edge))
    floors.append(floor)
    rows.append((label, mhz, watched, floor, peak))
sdr.close()

gf = float(np.median(floors))
print(f"tuner: R820T · noise floor ≈ {gf:.1f} dB · threshold = +10 dB over floor\n")
print(f"{'band/freq':32s} {'floor':>7s} {'peak':>7s} {'over':>6s}  signal?")
for label, mhz, watched, floor, peak in rows:
    over = peak - gf
    hit = "◀ SIGNAL" if over >= 10 else ""
    tag = "" if watched else "(not watched)"
    print(f"{label:32s} {floor:7.1f} {peak:7.1f} {over:6.1f}  {hit} {tag}")
print("\nWATCHED bands are what SENTRY reports; references show the radio is live.")
