"""Deterministic, offline tests for device-type classification (identify.py).

No hardware needed — feeds synthetic BLE beacons / ports and asserts the device
TYPE is correct and is never the radio name. Run: python -m tests.test_identify
Used as an overnight regression guard while improving classification.
"""

from sentry_backend import identify


def _tlv(*pairs):
    """Build an Apple continuity payload from (type, datalen) pairs."""
    out = bytearray()
    for t, n in pairs:
        out.append(t)
        out.append(n)
        out.extend([0] * n)
    return bytes(out)


CASES = [
    # name, kwargs, substring that must appear in type, must_not_be
    ("Apple Find My / AirTag",
     dict(mac="d5:d8:76:36:15:23", ble_manufacturer={0x004C: _tlv((0x12, 2))}),
     "tracker"),
    ("Apple AirPods (earbuds)",
     dict(mac="aa:bb:cc:dd:ee:01", ble_manufacturer={0x004C: _tlv((0x07, 0x19))}),
     "earbud"),
    ("Apple Nearby (iPhone)",
     dict(mac="aa:bb:cc:dd:ee:02", ble_manufacturer={0x004C: _tlv((0x10, 5))}),
     "iphone"),
    ("Apple Handoff (active device)",
     dict(mac="aa:bb:cc:dd:ee:03", ble_manufacturer={0x004C: _tlv((0x0C, 2))}),
     "iphone"),
    ("Apple Watch",
     dict(mac="aa:bb:cc:dd:ee:04", ble_manufacturer={0x004C: _tlv((0x0B, 2))}),
     "watch"),
    ("Apple TV / HomePod",
     dict(mac="aa:bb:cc:dd:ee:05", ble_manufacturer={0x004C: _tlv((0x0A, 2))}),
     "homepod"),
    ("Microsoft CDP Android phone",
     dict(mac="aa:bb:cc:dd:ee:06", ble_manufacturer={0x0006: bytes([0x01, 0x08])}),
     "android"),
    ("Microsoft CDP Windows laptop",
     dict(mac="aa:bb:cc:dd:ee:07", ble_manufacturer={0x0006: bytes([0x01, 0x0F])}),
     "laptop"),
    ("Microsoft CDP Windows desktop",
     dict(mac="aa:bb:cc:dd:ee:08", ble_manufacturer={0x0006: bytes([0x01, 0x09])}),
     "desktop"),
    ("IP camera by RTSP port",
     dict(mac="11:22:33:44:55:66", open_ports=[554, 80]),
     "camera"),
    ("Network printer by 9100",
     dict(mac="11:22:33:44:55:67", open_ports=[9100, 80]),
     "printer"),
    ("Hikvision camera by OUI",
     dict(mac="44:19:b6:00:00:01"),
     "camera"),
    ("Govee bulb by name",
     dict(mac="aa:bb:cc:dd:ee:09", name="Govee_H6181_1383"),
     "light"),
    ("Bose by name",
     dict(mac="aa:bb:cc:dd:ee:0a", name="Bose Flex 2 SoundLink"),
     "bose"),
]

RADIO_WORDS = {"bluetooth device", "bluetooth", "wifi device", "network device",
               "ble device", "bluetooth le"}


def run():
    fails = 0
    for name, kwargs, want in CASES:
        info = identify.identify(seen_via="BLE", **kwargs)
        t = (info["type"] or "").lower()
        ok = want in t and t not in RADIO_WORDS
        if not ok:
            fails += 1
            print(f"  FAIL  {name}: got '{info['type']}' (wanted '*{want}*')")
        else:
            print(f"  ok    {name}: {info['type']}  (conf {info['confidence']})")

    # camera flagging
    cam = identify.identify(mac="11:22:33:44:55:66", open_ports=[554])
    if not cam["is_camera"]:
        fails += 1
        print("  FAIL  RTSP 554 should set is_camera=True")

    # a generic high port alone must NOT be a camera (false-positive guard)
    pc = identify.identify(mac="3c:9b:d6:00:00:01", open_ports=[9000, 8443])
    if pc["is_camera"]:
        fails += 1
        print(f"  FAIL  Microsoft + port 9000/8443 wrongly flagged camera: {pc['type']}")

    print(f"\n{'PASS' if fails == 0 else 'FAIL'}: {len(CASES)+2-fails}/{len(CASES)+2} checks")
    return fails == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
