# 11 — Phases 6, 7 & 8 (Advanced Counter-Surveillance + Home Monitoring)

Build-toward phases beyond the core. 6 and 7 deepen counter-surveillance; 8 turns
SENTRY into an active watch over YOUR OWN home, property, and network.

> Scope stays legal and defensive throughout: detect threats to you, and monitor
> things you own. Receiving/analyzing openly-broadcast signals and monitoring your
> own property is legal. This is not for surveilling other people or intercepting
> others' private communications.

---

# PHASE 6 — ADVANCED COUNTER-SURVEILLANCE SENSORS

Catch what the core build can't, and find threats more precisely.

| # | Item | ~$ | What it catches / adds | Worth it? |
|---|------|----|------------------------|-----------|
| 1 | **IR illuminator detector** (IR photodiode/sensor) | 5 | Night-vision & hidden cameras flood a room with INVISIBLE infrared — this sees it. Catches dark/IR cameras your eyes can't. | ⭐⭐⭐ high value, cheap |
| 2 | **Wideband discone antenna** | 30–50 | Picks up far more of the spectrum than a whip. Often a bigger gain than another receiver. | ⭐⭐⭐ best "see more" upgrade |
| 3 | **Second RTL-SDR** | 45 | Monitor one band continuously while sweeping another — don't miss brief transmissions. | ⭐⭐ solid |
| 4 | **Telescopic tuned antenna set** | 20 | Tune antenna length to a target band for stronger reception. | ⭐⭐ |
| 5 | **Tuned lens-finder (Pi cam + IR ring, optimized)** | (have it) | Find cameras recording LOCALLY with radio OFF — the threat radio can't see. Catches retroreflective lens glint. | ⭐⭐⭐ catches the hardest threat |

**Software to build for Phase 6 (with Claude Code):**
- IR-illuminator detection channel (read the IR sensor, flag IR sources)
- Dual-SDR coordination (one watches, one sweeps)
- Lens-finder glint-detection tuning
- RF baseline/anomaly across wider spectrum (you have the baseline feature)

---

# PHASE 7 — TRUE DIRECTION-FINDING (locate the source)

Solve the "where is it actually coming from" problem properly.

| # | Item | ~$ | What it does | Worth it? |
|---|------|----|--------------|-----------|
| 6 | **Log-periodic directional antenna** | 30 | Manual "point and the signal peaks" — rough but real direction. | ⭐⭐ good cheap start |
| 7 | **KrakenSDR (5 coherent RTL-SDRs)** | ~500 | TRUE automatic bearing to a transmitter — the real "point to the bug" hardware. | ⭐⭐⭐ the real deal (pricey) |
| 8 | **Antenna array mounts/spacing kit** | 30 | Proper element spacing for the Kraken's direction-finding. | needed with Kraken |

**Software to build for Phase 7:**
- KrakenSDR integration → real bearing display (replaces the honest distance-only
  view with actual direction once the hardware supports it)
- Triangulation: take bearings from 2+ spots to pinpoint a source location
- Heat-map a signal's strength as you move (with GPS from earlier phases)

**Honest note:** the directional antenna (#6) is a cheap rough start; the KrakenSDR
(#7) is what actually delivers real direction-finding. Big jump in capability and
cost — only when you're serious about locating.

---

# PHASE 8 — NETWORK MONITORING & ANALYSIS (learn to see your own traffic)

Turn SENTRY into a real network-analysis tool for YOUR OWN network. This is where
you learn to actually "pick things up" — see every device, watch what they talk
to, spot anomalies, and understand normal-vs-suspicious traffic. All on equipment
you own. This is foundational security/networking skill.

> Scope: your own network and your own devices' traffic. If others share your
> network (family/roommates/guests), practice on your own devices and traffic and
> respect their privacy. On your own gear, learn freely.

## 8A — Packet-level visibility (the core skill)
| # | Tool | ~$ | What you learn |
|---|------|----|----------------|
| 1 | **Wireshark** (free software) | 0 | See EVERY packet on your network — what each device talks to, which protocols, when. THE tool for learning to see traffic. |
| 2 | **tshark** (Wireshark CLI) | 0 | Scriptable capture — feed live traffic into SENTRY for analysis |
| 3 | **tcpdump** | 0 | Lightweight packet capture on the Pi |

## 8B — Device & service discovery (you have the start)
| # | Tool | ~$ | What you learn |
|---|------|----|----------------|
| 4 | **nmap** (you already use it) | 0 | Every device, its open ports, OS/service fingerprint |
| 5 | **SENTRY LAN scanner** (built) | 0 | Device discovery + new-device alerts |
| 6 | **arp-scan / netdiscover** | 0 | Fast device enumeration on your subnet |

## 8C — Traffic analysis & "phone home" visibility
| # | Tool | ~$ | What you learn |
|---|------|----|----------------|
| 7 | **ntopng** | 0 | Traffic volume per device, top talkers, where devices connect out |
| 8 | **Pi-hole** | 0 | See (and block) what domains your devices contact — smart devices are chatty |
| 9 | **Your router's traffic logs** | 0 | Underrated: connected devices + traffic right from the router |

## 8D — Features to build into SENTRY (with Claude Code)
- **Live traffic monitor:** capture packets (tshark/tcpdump) and show per-device
  traffic in the SENTRY interface
- **Device "phone home" map:** for each of your devices, show what external
  servers/domains it contacts
- **Traffic baseline + anomaly:** learn each device's normal traffic, flag unusual
  spikes or new destinations (the same baseline idea as RF)
- **New-device + new-connection alerts:** notify when an unknown device joins or a
  device starts talking to something new
- **Protocol breakdown:** show what protocols each device uses (HTTP, RTSP, MQTT,
  etc.) — RTSP/ONVIF = camera tells
- **Bandwidth/uptime tracking** for your own network

## Learning exercises (your own network)
1. Run Wireshark, unplug/replug a device, watch its startup chatter.
2. Watch what your smart devices (TV, bulbs, cameras) talk to while "idle" —
   you'll be surprised how much they phone home.
3. nmap-fingerprint each device, verify against what you know it is.
4. Baseline your network, add a new device, try to spot it in the traffic.
5. Use Pi-hole to see every domain your devices contact over a day.

**This Phase 8 is mostly free software** — the real cost is learning time, and it's
the highest-skill payoff in the whole build. Wireshark + your SENTRY scanner +
traffic baselining teaches you to genuinely "see" a network.

## RUNNING TOTALS (on top of the base box ~$470)
| Phase | ~Added cost | Capability |
|-------|-------------|------------|
| 6 — advanced detection | $100–170 | IR camera detection, wider spectrum, dual-SDR, lens-finder |
| 7 — direction-finding | $30 (manual) or ~$560 (KrakenSDR) | locate signal sources |
| 8 — network monitoring/analysis | $0 (free software) | learn to see your own traffic: Wireshark, traffic baselines, phone-home maps, anomaly alerts |

## RECOMMENDED
- **Phase 6:** the IR detector (#1, ~$5) and a better antenna (#2) are the
  cheap high-value adds. Do these early.
- **Phase 7:** start with the $30 directional antenna; KrakenSDR only if you get
  serious about locating.
- **Phase 8:** free software (Wireshark, ntopng, Pi-hole) + features built into
  SENTRY. Highest skill payoff in the build — this is where you learn to really
  see a network.

Each item: buy/wire it → tell Claude Code what you added → it builds the feature →
test → commit & push.
