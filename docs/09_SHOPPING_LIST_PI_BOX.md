# 09 — Complete Shopping List: SENTRY Pi Box Build (with links)

Everything to build the full Raspberry Pi "ultimate box." Prices are approximate
(2026) and shift — check current at the links. Buy authorized Pi resellers
(PiShop, CanaKit, Adafruit, The Pi Hut, Vilros) for genuine boards.

> Two important notes baked in below: (1) Pi 5 prices rose in late 2025 due to
> memory costs. (2) The Pi 5 needs a DIFFERENT display cable than older Pis — a
> common mistake. Both addressed in the list.

---

## CORE PLATFORM (required)

### 1. Raspberry Pi 5 (8GB) — ~$95
The brain. (Prices rose in late 2025; the 8GB is ~$95 now, was ~$80.)
- Raspberry Pi official: https://www.raspberrypi.com/products/raspberry-pi-5/
- PiShop (US): https://www.pishop.us/product/raspberry-pi-5-8gb/
- CanaKit: https://www.canakit.com/raspberry-pi-5-8gb.html
- Amazon: https://www.amazon.com/dp/B0CK2FCG1K
- Check stock across sellers: https://rpilocator.com

### 2. Active Cooler for Pi 5 — ~$5
Snap-on fan+heatsink. The Pi 5 runs hot; you need this.
- https://www.raspberrypi.com/products/active-cooler/

### 3. Official 27W USB-C Power Supply — ~$12
Don't use a phone charger; the Pi 5 wants the 5V/5A 27W supply.
- https://www.raspberrypi.com/products/27w-power-supply/

### 4. 64GB microSD card (A2) — ~$12
The "hard drive." SanDisk Extreme or Samsung EVO, A2-rated.
- SanDisk Extreme 64GB: https://www.amazon.com/dp/B09X7DNF3X

### 5. Official 7" Touch Display 2 — ~$60
The screen.
- https://www.raspberrypi.com/products/raspberry-pi-touch-display-2/
- (Cheaper 5" version exists for ~$40 if you want smaller.)

### 6. ⚠️ Pi 5 Display Cable (22-pin) — ~$1 — DON'T SKIP
**Critical gotcha:** the Pi 5 uses a different display connector (22-pin) than
the cable that comes with the screen (15-pin). You MUST get the Pi 5 adapter
cable or the screen won't connect.
- https://www.raspberrypi.com/products/display-cable/

### 7. microSD card reader — ~$8 (skip if your laptop has one)
To flash the SD card from your laptop.
- Any USB SD reader, e.g. https://www.amazon.com/dp/B0779V61XB

**Core subtotal: ~$205**

---

## RADIO SENSORS (the laptop capabilities, on the Pi)

### 8. RTL-SDR — you already have the Nooelec NESDR Mini ✓
Works on the Pi too. ~25 MHz–1.7 GHz.
- (Already purchased — plugs into Pi USB)

### 9. MCX-to-SMA adapter — ~$7
Your Nooelec Mini uses MCX; this lets you attach real antennas.
- Nooelec MCX adapters: https://www.amazon.com/dp/B07VML6KVR

### 10. Log-periodic directional antenna (0.85–6.5 GHz) — ~$30
For real direction-finding ("walk to it").
- Search "log periodic directional antenna 850MHz-6.5GHz SMA" on Amazon

**Radio subtotal: ~$37 (you own the SDR)**

---

## PHYSICAL SENSORS (what the box adds over a laptop)

### 11. MLX90640 Thermal Camera (I2C, with headers) — ~$40
Heat of hidden powered electronics. Get the "with headers" version (no
soldering). 55° or 110° FOV both fine.
- Adafruit MLX90640: https://www.adafruit.com/product/4407
- Amazon (various): search "MLX90640 thermal camera I2C"

### 12. Raspberry Pi Camera Module 3 — ~$25
The lens-finder camera.
- https://www.raspberrypi.com/products/camera-module-3/

### 13. IR LED ring light — ~$8
Makes hidden camera lenses glint. Small 850nm IR ring.
- Search "IR LED ring 850nm Raspberry Pi camera" on Amazon

### 14. PN532 NFC/RFID module — ~$10
Detects skimmers / covert readers. Get one with I2C mode (switchable).
- Adafruit PN532: https://www.adafruit.com/product/364
- Amazon (cheaper): search "PN532 NFC module"

### 15. QMC5883L magnetometer (EMF/magnetic) — ~$8 (3-pack)
Magnetic-field probe for wired bugs, magnet-mounted trackers.
- Search "QMC5883L magnetometer module" on Amazon

### 16. USB ultrasonic-capable microphone — ~$15
For ultrasonic tracking-beacon detection.
- Any USB mic; "ultrasonic USB microphone" for higher-frequency capability

### 17. (Optional) u-blox USB GNSS module — ~$15
GPS jamming/spoofing detection + location logging.
- Search "u-blox 7 USB GPS module" on Amazon

**Physical sensors subtotal: ~$120 (or ~$106 without GNSS)**

---

## ENCLOSURE & POWER

### 18. Pelican-style hard case (~13×10") with pluck foam — ~$40
The box. Apache 4800 (Harbor Freight) is a cheap Pelican-equivalent.
- Apache 4800: https://www.harborfreight.com/ (search "Apache 4800")
- Or Pelican 1450: https://www.pelican.com/

### 19. 18650 UPS HAT + 2× 18650 cells — ~$30
Run it cordless. Get one with a STACKING/pass-through header so the GPIO pins
stay reachable for your I2C sensors.
- Search "Raspberry Pi 5 18650 UPS HAT stacking header" on Amazon
- 18650 cells (quality): Samsung/LG, search "18650 button-top 3000mAh"

### 20. Female-to-female jumper wires (40-pack) — ~$7
Connect the I2C sensors to the GPIO pins.
- Search "female to female jumper wires dupont 40 pin"

### 21. (Optional) SMA bulkhead connectors — ~$10
Mount antennas cleanly through the case wall.
- Search "SMA bulkhead panel mount connector"

**Enclosure & power subtotal: ~$87 (or ~$77 without bulkheads)**

---

## TOOLS YOU MIGHT NEED
- Small Phillips screwdriver (~$5)
- Hobby/craft knife for foam + case holes (~$5)
- (Optional) soldering iron — only if a module arrives without headers (~$20)

---

## TOTALS
| Tier | ~Cost |
|------|-------|
| Core platform | $205 |
| Radio (you own the SDR) | $37 |
| Physical sensors | $120 |
| Enclosure & power | $87 |
| **Full ultimate box** | **~$449** |
| Without optional GNSS/bulkheads/tools | **~$415** |

You can phase it: build the **core + your SDR first** (~$242) to get a working
box, then add physical sensors one at a time.

---

## CRITICAL REMINDERS
1. **Get the Pi 5 display cable (#6)** — the screen's included cable does NOT fit
   the Pi 5. Most-missed item.
2. **Buy the Pi from authorized resellers** — counterfeits exist.
3. **Get "with headers" sensor modules** — avoids soldering.
4. **UPS HAT with stacking header** — so I2C sensors still reach the pins.
5. **Your Nooelec Mini works on the Pi** — no need to rebuy an SDR; just get the
   MCX-SMA adapter (#9).
6. Prices rose in late 2025 (memory costs); check current prices at the links.

---

## ORDER TO BUILD (once parts arrive)
Follow **05_PI_ULTIMATE_BOX.md** — flash SD → boot → internet → install SENTRY →
wire sensors one at a time → test each → case build. Don't wire everything at
once; bring up one sensor, confirm it, then the next.
