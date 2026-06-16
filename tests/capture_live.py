"""Ad-hoc live capture: connect to the running SENTRY backend WS feed, record
what real nearby devices classify as, and track each device's RSSI over several
ticks. Pure diagnostics — read-only, prints a report. Safe to delete."""
import asyncio, json, collections, sys, io
import websockets

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TICKS = 10

async def main():
    seen = {}                       # id -> last device dict
    rssi_hist = collections.defaultdict(list)
    order = []
    async with websockets.connect("ws://localhost:8765") as ws:
        last_ts = None
        got = 0
        while got < TICKS:
            raw = await asyncio.wait_for(ws.recv(), timeout=20)
            msg = json.loads(raw)
            if msg.get("ts") == last_ts:
                continue
            last_ts = msg.get("ts")
            got += 1
            for d in msg.get("devices", []):
                if d["id"] not in seen:
                    order.append(d["id"])
                seen[d["id"]] = d
                if d.get("rssi") is not None:
                    rssi_hist[d["id"]].append(d["rssi"])
            sensors = msg.get("sensors", [])
            online = [s["channel"] for s in sensors if s["online"]]
            print(f"tick {got}: {len(msg.get('devices',[]))} devices · online={online}")

    print("\n==== CLASSIFICATION SUMMARY (live, real nearby devices) ====")
    print(f"{'DEVICE TYPE (main label)':32s} {'VIA (method)':14s} {'MAKER':22s} RSSI")
    for did in order:
        d = seen[did]
        # only the meaningful ones (skip -127 'no reading' sentinel noise)
        r = d.get("rssi")
        tag = "" if (r is not None and r > -127) else "  (no live RSSI)"
        print(f"{(d.get('device_type') or '?'):32.32s} {(d.get('method') or '?'):14.14s} "
              f"{(d.get('maker') or '?'):22.22s} {r}{tag}")

    print("\n==== TWO REAL DEVICES — RSSI OVER TIME (per-device, live) ====")
    # pick the two different devices with the most real (>-127) samples
    real = {k: [x for x in v if x > -127] for k, v in rssi_hist.items()}
    rich = sorted([(k, v) for k, v in real.items() if len(v) >= 3],
                  key=lambda kv: -len(kv[1]))
    for did, hist in rich[:2]:
        d = seen[did]
        label = d.get("device_type") or d.get("kind")
        print(f"\n  {label}  [{did}]  maker={d.get('maker')}")
        print(f"    raw RSSI samples : {hist}")
        print(f"    distinct values  : {sorted(set(hist))}  (identical across devices? compare below)")

asyncio.run(main())
