"""Read-only assessment: capture the live feed for several ticks and report the
facts needed to judge the build honestly — channel separation, classification,
per-device RSSI distinctness, no-signal handling, over-flagging, and data sanity."""
import asyncio, json, collections, sys, io
import websockets
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TICKS = 12

async def main():
    seen = {}; hist = collections.defaultdict(list); order = []
    sensors = []
    async with websockets.connect("ws://192.168.1.112:8765") as ws:
        last=None; got=0
        while got < TICKS:
            d = json.loads(await asyncio.wait_for(ws.recv(), timeout=25))
            if d.get("ts")==last: continue
            last=d.get("ts"); got+=1
            sensors = d.get("sensors", [])
            for x in d["devices"]:
                if x["id"] not in seen: order.append(x["id"])
                seen[x["id"]]=x
                hist[x["id"]].append(x.get("rssi"))

    devs=list(seen.values())
    print("SENSORS ONLINE:", [s["channel"] for s in sensors if s["online"]],
          "| OFFLINE:", [s["channel"] for s in sensors if not s["online"]])
    for s in sensors:
        if s.get("note"): print("  note["+s["channel"]+"]:", s["note"])

    # 1) channel separation
    bych=collections.Counter(d["channel"] for d in devs)
    print("\n[1] DEVICES PER CHANNEL:", dict(bych), "| total", len(devs))

    # 2) classification breakdown
    print("\n[2] DEVICE_TYPE breakdown:")
    for t,c in collections.Counter(d.get("device_type") or d.get("kind") for d in devs).most_common():
        print(f"    {c:3d}  {t}")

    # 3) severity / over-flagging
    sev=collections.Counter(d["severity"] for d in devs)
    trackers=[d for d in devs if d.get("category")=="tracker"]
    following=[d for d in devs if "following" in (d.get("behaviortxt","").lower())]
    print("\n[3] SEVERITY:", dict(sev))
    print(f"    flagged 'tracker' category : {len(trackers)}")
    print(f"    text says 'following'      : {len(following)}")
    print(f"    alerts                     : {sev.get('alert',0)}")

    # 4) RSSI sanity / no-signal
    nullr=[d for d in devs if d.get("rssi") is None]
    badr=[d for d in devs if isinstance(d.get('rssi'),(int,float)) and d['rssi']<=-127]
    print("\n[4] RSSI SANITY:")
    print(f"    devices with NO rssi (null): {len(nullr)}  (channels: {collections.Counter(d['channel'] for d in nullr)})")
    print(f"    any rssi <= -127 leaking?  : {len(badr)}  (want 0)")
    rv=[d['rssi'] for d in devs if isinstance(d.get('rssi'),(int,float))]
    if rv: print(f"    real rssi range            : {min(rv)}..{max(rv)} dBm")

    # 5) distinct per-device data — show variation across ticks
    print("\n[5] PER-DEVICE DISTINCT DATA (sample of 6 with most samples):")
    rich=sorted(((i,[v for v in hist[i] if v is not None]) for i in order),
                key=lambda kv:-len(kv[1]))
    for i,h in rich[:6]:
        d=seen[i]
        print(f"    {(d.get('device_type') or '?'):30.30s} {d['channel']:9s} samples={h[:10]}")

    # 6) potential duplicates: same vendor+type across channels
    print("\n[6] SAME DEVICE ON MULTIPLE CHANNELS? (vendor/type seen on >1 channel)")
    keymap=collections.defaultdict(set)
    for d in devs:
        keymap[(d.get('maker'),d.get('device_type'))].add(d['channel'])
    multi=[(k,v) for k,v in keymap.items() if len(v)>1]
    for (mk,ty),chs in multi[:8]:
        print(f"    {ty} / {mk}: channels {sorted(chs)}")
    if not multi: print("    (none detected this run)")

    # 7) distance/bearing honesty spot check
    print("\n[7] DISTANCE/BEARING SAMPLE (first 5):")
    for d in devs[:5]:
        print(f"    {(d.get('device_type') or '?'):24.24s} rssi={d.get('rssi')} dist={d.get('distance')} bearing={d.get('bearing')} (bearing is arbitrary)")

asyncio.run(main())
