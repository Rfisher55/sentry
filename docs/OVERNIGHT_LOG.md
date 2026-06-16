# SENTRY — overnight work log

Claude is improving SENTRY autonomously overnight (started 2026-06-15 evening).
Each entry: what changed, why, how it was verified. Newest first.

Ground rules I'm holding to:
- Small, verified steps. After every change: run `python -m tests.test_identify`,
  compile the backend, JS-bracket-check the UI, restart the server, confirm the
  live WebSocket feed still flows.
- Never fake data or capability. Honest about built-in-hardware limits
  (no RTL-SDR, no directional antenna).
- Don't break what works. If a change regresses the self-test or the feed, revert it.

---

## Iteration 1 — regression harness + log (done)
- Added `tests/test_identify.py`: 16 deterministic, offline classification checks
  (Apple Find My/AirPods/iPhone/Watch/TV, Microsoft CDP Android/Windows, camera
  by RTSP port, printer by 9100, Hikvision by OUI, Govee/Bose by name, plus a
  false-positive guard that a generic port must NOT flag a camera).
  Result: **16/16 PASS.**
- Added this log.

## Iteration 2 — per-row signal bar-graph (done)
- Added a 5-segment mini signal-strength bar to each Scan-list row (`miniBar()`),
  green→amber→red, height-stepped — instrument look, at-a-glance proximity.
- Added `tests/jscheck.py` (reusable JS bracket/structure check).
- Verified: jscheck OK, self-test 16/16, backend compiles, server restarted,
  live feed flowing (50 devices, types correct).

## Planned next (no input needed)
- Expand the curated OUI vendor list (more camera + consumer vendors) to identify
  more devices on the LAN scan, incl. Ring/Nest/Wyze/Arlo ranges.
- Per-row mini signal bar-graph in the Scan list (instrument look).
- Sensible default sensitivity gate + show confidence in the list/drawer.
- Wire live per-sensor status into the Channels tab (CLAUDE.md good-next-task).
- More BLE service-UUID and name hints for finer device typing.
- Optional: export detections to JSON/CSV (TSCM evidence trail).
