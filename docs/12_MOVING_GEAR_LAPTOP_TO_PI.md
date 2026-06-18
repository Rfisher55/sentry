# 12 — Moving Your Gear From the Laptop to the Pi Box

Good news: almost everything you buy for the laptop build moves straight over to
the Raspberry Pi box. You don't buy it twice. This guide explains what transfers,
what doesn't, and how to move each piece — explained simply.

> The idea: build and learn on the laptop first. When you build the Pi box, carry
> your gear over. The laptop becomes your "test bench"; the Pi becomes the
> finished field unit.

---

## What MOVES OVER (buy once, use in both)

| Gear | Laptop | Pi box | How it moves |
|------|--------|--------|--------------|
| **RTL-SDR dongle** (Nooelec Mini) | USB port | USB port | Just unplug from laptop, plug into Pi. Same dongle, same driver concept. |
| **Antennas** (whip, directional, etc.) | screw onto SDR | screw onto SDR | They attach to the SDR, so they go wherever the SDR goes. |
| **MCX-to-SMA adapter** | on the SDR | on the SDR | Stays attached to the dongle. |
| **USB GPS dongle** (if you got one) | USB port | USB port | Unplug, replug. |
| **USB Wi-Fi adapter** (if you got one) | USB port | USB port | Unplug, replug. |
| **HackRF** (if you got one) | USB port | USB port | Unplug, replug. |

**Rule of thumb: anything that plugs into USB or screws onto the SDR moves over
with zero changes.** That's most of your radio gear.

---

## What's NEW for the Pi (laptop didn't need these)

These are Pi-only because they wire to the Pi's GPIO pins, which a laptop doesn't
have:
- Thermal camera (MLX90640)
- Pi Camera + IR ring (lens-finder)
- NFC reader (PN532)
- Magnetometer/EMF probe
- The Pi itself, screen, power, case, battery HAT

So when you build the box, you ADD these — you don't replace anything from the
laptop.

---

## What DOESN'T move (laptop-only)

- **Your laptop's built-in Wi-Fi and Bluetooth** — the Pi has its own built-in
  Wi-Fi and Bluetooth, so you don't move these; the Pi just uses its own. (Same
  capability, different built-in radios.)
- **Zadig/WinUSB driver** — that's a Windows thing. On the Pi (Linux) the SDR uses
  a different driver setup, handled in the Pi build steps. The dongle is the same;
  only the driver install differs by operating system.

---

## How the SOFTWARE moves (the important part)

You do NOT rebuild SENTRY from scratch on the Pi. Because all your code lives on
GitHub:

1. On the Pi, run: `git clone https://github.com/Rfisher55/sentry.git`
2. That downloads your CURRENT, fully-built SENTRY — every fix, every feature you
   built on the laptop — automatically.
3. Install + run it on the Pi (see 05_PI_ULTIMATE_BOX.md).
4. The Pi then runs everything the laptop did, PLUS the new physical sensors you
   wire in.

**So the laptop work is never lost or redone — the Pi inherits all of it via
GitHub.** This is the whole reason we keep pushing to GitHub after each session.

---

## Step-by-step: moving day (laptop -> Pi)

1. **Finish & push on the laptop:** make sure your latest SENTRY is committed and
   pushed to GitHub (`commit and push`, confirm in sync).
2. **Build the Pi base:** flash the SD card, boot, connect internet, install
   SENTRY via `git clone` (05_PI_ULTIMATE_BOX.md).
3. **Move the radio gear:** unplug the SDR (+ its antennas/adapter) from the
   laptop, plug into the Pi's USB. Set up the SDR driver on the Pi (Linux steps in
   the Pi guide).
4. **Test the moved gear on the Pi:** confirm the SDR comes online and you get RF —
   same as it did on the laptop.
5. **Add the Pi-only sensors:** wire in thermal, lens-finder, NFC, EMF one at a
   time (06/05 wiring diagrams), testing each.
6. **You now have the full box** — everything the laptop did + the physical
   sensors, in a portable case.

---

## Quick reference

```
MOVES OVER (USB/screw-on):  SDR dongle, antennas, MCX-SMA adapter, GPS, Wi-Fi
                            adapter, HackRF
PI USES ITS OWN:            built-in Wi-Fi + Bluetooth (don't move laptop's)
NEW FOR PI (GPIO):          thermal, lens-finder, NFC, EMF, + Pi/screen/case/power
SOFTWARE:                   git clone your repo -> Pi gets everything you built
DRIVER:                     same dongle, different driver install per OS (Zadig on
                            Windows, Linux setup on Pi)
```

**Bottom line:** buy your radio gear once. Learn on the laptop. When you build the
box, carry the radio gear over, add the GPIO sensors, and `git clone` the software.
Nothing is wasted, nothing is rebuilt.
