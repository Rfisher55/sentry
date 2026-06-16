"""Proof: capture REAL backend RSSI for a strong, a weak, and a no-signal device
over several live ticks, then print exactly what the UI's signal view renders
for each — mirroring the UI's own branch logic (drawSignal/renderDeviceReadout).
Read-only diagnostic."""
import asyncio, json, collections, sys, io
import websockets
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TICKS = 10

def ui_verdict(d):
    """Replicate ui/index.html drawSignal() decision for a device-focused view."""
    rssi = d.get("rssi")
    if rssi is not None:
        return f'REAL TRACE · "{d.get("rssi")} dBm" · ● LIVE (plots this device\'s RSSI history)'
    if d.get("ip") or d.get("channel") == "network":
        return 'NO RADIO SIGNAL panel — "Found by IP/MAC, not a radio reading. Nothing to plot."'
    return 'NO SIGNAL panel — "This device has no measured RSSI."'

async def main():
    hist = collections.defaultdict(list)
    seen = {}
    async with websockets.connect("ws://localhost:8765") as ws:
        last = None; got = 0
        while got < TICKS:
            d = json.loads(await asyncio.wait_for(ws.recv(), timeout=20))
            if d.get("ts") == last: continue
            last = d.get("ts"); got += 1
            for x in d["devices"]:
                seen[x["id"]] = x
                hist[x["id"]].append(x.get("rssi"))

    # pick three real devices by their measured signal
    rssi_now = {i: (v[-1] if v else None) for i, v in hist.items()}
    strong = max((i for i in seen if isinstance(rssi_now[i], (int, float))),
                 key=lambda i: rssi_now[i], default=None)
    weak = min((i for i in seen if isinstance(rssi_now[i], (int, float))),
               key=lambda i: rssi_now[i], default=None)
    nosig = next((i for i in seen if rssi_now[i] is None), None)

    for label, did in [("(a) STRONG signal", strong), ("(b) WEAK signal", weak),
                       ("(c) NO signal", nosig)]:
        print("=" * 70)
        print(label)
        if did is None:
            print("   (none found this run)"); continue
        d = seen[did]
        print(f"   device      : {d.get('device_type') or d.get('kind')}  [{did}]")
        print(f"   raw RSSI/tick: {[v for v in hist[did]]}")
        print(f"   UI renders   : {ui_verdict(d)}")
    print("=" * 70)
    # prove different devices show DIFFERENT data
    if strong and weak and strong != weak:
        print(f"distinct? strong={hist[strong][-3:]}  vs  weak={hist[weak][-3:]}  -> "
              + ("DIFFERENT real data" if hist[strong][-1] != hist[weak][-1] else "same"))

asyncio.run(main())
