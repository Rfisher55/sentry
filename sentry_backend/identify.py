"""SENTRY device identification — turn raw clues into "what is this thing".

Honest by design: every guess carries a confidence and the EVIDENCE it's based
on. We use what's actually observable on built-in hardware:
  - MAC OUI  -> vendor (curated list of common consumer / camera vendors)
  - BLE manufacturer company ID -> vendor
  - BLE advertised name patterns -> device type
  - BLE GATT service UUIDs / appearance -> device type
  - Wi-Fi SSID patterns + vendor -> device type / camera
  - Open TCP ports (network scan) -> camera / printer / etc.

This is NOT a full IEEE OUI database (that's ~35k entries and would need a live
download). It's a curated set covering common home devices; anything unknown is
reported honestly as "Unknown vendor (OUI xx:xx:xx)" rather than guessed.
"""

# ---- OUI -> vendor (first 3 MAC octets, lowercase "xx:xx:xx") --------------
# Curated common consumer / IoT / camera vendors. Extend freely.
OUI_VENDORS = {
    # Apple
    "00:1b:63": "Apple", "ac:bc:32": "Apple", "f0:18:98": "Apple",
    "a4:83:e7": "Apple", "dc:a9:04": "Apple", "f8:ff:c2": "Apple",
    "3c:06:30": "Apple", "a8:66:7f": "Apple", "90:b0:ed": "Apple",
    # Samsung
    "94:e6:ba": "Samsung", "20:15:de": "Samsung", "5c:49:7d": "Samsung",
    "8c:77:12": "Samsung", "00:7c:2d": "Samsung", "e8:50:8b": "Samsung",
    # Google / Nest
    "f4:f5:d8": "Google", "f4:f5:e8": "Google", "1c:f2:9a": "Google",
    "30:fd:38": "Google", "d8:eb:46": "Google", "9c:7b:d2": "Nest (Google)",
    "18:b4:30": "Nest (Google)", "64:16:66": "Nest (Google)",
    # Amazon (Echo / Ring share ranges)
    "fc:a1:83": "Amazon", "44:65:0d": "Amazon", "68:37:e9": "Amazon",
    "ac:63:be": "Amazon", "f0:81:73": "Amazon", "00:bb:3a": "Amazon",
    # Ring (Amazon)
    "00:62:6e": "Ring (Amazon)", "34:3e:a4": "Ring (Amazon)",
    "54:e0:19": "Ring (Amazon)", "b0:09:da": "Ring (Amazon)",
    # Cameras
    "44:19:b6": "Hangzhou Hikvision", "c0:56:e3": "Hangzhou Hikvision",
    "bc:ad:28": "Hangzhou Hikvision", "28:57:be": "Hangzhou Hikvision",
    "3c:ef:8c": "Dahua", "e0:50:8b": "Dahua", "90:02:a9": "Dahua",
    "9c:8e:cd": "Amcrest", "ec:71:db": "Reolink", "b0:c5:54": "D-Link",
    "00:18:0a": "Meraki (Cisco)", "2c:aa:8e": "Wyze", "7c:78:b2": "Wyze",
    "d0:3f:27": "Wyze", "00:1d:c5": "Arlo (Netgear)", "a0:40:a0": "Arlo (Netgear)",
    "00:62:6e": "Dahua/OEM", "00:1a:1e": "Axis Communications",
    "ac:cc:8e": "Axis Communications", "00:0e:8f": "Foscam",
    # Networking / routers
    "a0:55:1f": "Sagemcom (router)", "b8:27:eb": "Raspberry Pi",
    "dc:a6:32": "Raspberry Pi", "e4:5f:01": "Raspberry Pi",
    "50:c7:bf": "TP-Link", "98:da:c4": "TP-Link", "f4:f2:6d": "TP-Link",
    "fc:ec:da": "Ubiquiti", "24:a4:3c": "Ubiquiti", "00:09:b0": "Netgear",
    # Media / IoT
    "b8:27:eb": "Raspberry Pi", "00:0e:58": "Sonos", "5c:aa:fd": "Sonos",
    "94:9f:3e": "Sonos", "b8:e9:37": "Sonos", "dc:56:e7": "Roku",
    "cc:6d:a0": "Roku", "b0:a7:37": "Roku", "00:1e:c0": "LG",
    "10:68:3f": "LG", "c4:36:6c": "LG", "2c:f0:5d": "Intel",
    "3c:9b:d6": "Microsoft", "00:50:f2": "Microsoft", "98:5f:d3": "Microsoft",
    "24:6f:28": "Espressif (ESP32)", "30:ae:a4": "Espressif (ESP32)",
    "7c:9e:bd": "Espressif (ESP32)", "a4:cf:12": "Espressif (ESP8266)",
    "ec:fa:bc": "Espressif (ESP32)", "10:52:1c": "Espressif (ESP32)",
    "44:17:93": "Espressif (ESP32)", "d8:bf:c0": "Govee",
    "00:17:88": "Philips Hue", "ec:b5:fa": "Philips Hue",
}

# OUIs that are camera makers (used to flag likely cameras).
CAMERA_VENDORS = {
    "Hangzhou Hikvision", "Dahua", "Dahua/OEM", "Amcrest", "Reolink",
    "Axis Communications", "Foscam", "Wyze", "Ring (Amazon)", "Nest (Google)",
    "Arlo (Netgear)", "D-Link", "Meraki (Cisco)",
}

# ---- BLE manufacturer "company IDs" -> vendor ------------------------------
BLE_COMPANY_IDS = {
    0x004C: "Apple", 0x0006: "Microsoft", 0x00E0: "Google", 0x0075: "Samsung",
    0x0087: "Garmin", 0x000F: "Broadcom", 0x0157: "Amazfit/Huami", 0x038F: "Xiaomi",
    0x0171: "Amazon", 0x004F: "Logitech", 0x00D2: "Bose", 0x0499: "Ruuvi",
    0x05A7: "Sonos", 0x0059: "Nordic Semi", 0x000D: "Texas Instruments",
    0x0118: "Tile", 0x0822: "Adafruit", 0x07A7: "Fitbit", 0x0131: "Cypress",
    0x02E5: "Espressif", 0x0085: "BlueRadios", 0x004A: "Sony", 0x0078: "Nike",
}

# ---- BLE assigned "appearance" values -> device type (subset) --------------
BLE_APPEARANCE = {
    0x0040: "Phone", 0x0080: "Computer", 0x00C0: "Watch", 0x00C1: "Watch",
    0x0140: "Display", 0x0180: "Remote control", 0x0341: "Keyboard",
    0x03C0: "HID device", 0x03C1: "Keyboard", 0x03C2: "Mouse",
    0x0840: "Heart-rate sensor", 0x0440: "Fitness band/tag", 0x0941: "Speaker",
    0x0942: "Microphone", 0x0944: "Headphones", 0x0945: "Earbuds",
}

# ---- BLE service UUID hints (16-bit assigned numbers) -----------------------
BLE_SERVICE_HINTS = {
    0x180D: "Heart-rate monitor", 0x1812: "HID input device",
    0x1108: "Headset/earbuds", 0x110B: "Audio speaker", 0x180F: "Battery device",
    0xFD5A: "Smart bulb (Govee)", 0xFE9F: "Google device", 0xFE07: "Sonos",
    0xFD6F: "Contact-tracing beacon", 0xFEAA: "Eddystone beacon",
}

# ---- name keyword -> device type -------------------------------------------
NAME_HINTS = [
    ("airpod", "Apple AirPods"), ("airtag", "Apple AirTag"),
    ("iphone", "iPhone"), ("ipad", "iPad"), ("macbook", "MacBook"),
    ("watch", "Smartwatch"), ("galaxy", "Samsung Galaxy device"),
    ("buds", "Wireless earbuds"), ("bose", "Bose audio"),
    ("sony", "Sony audio"), ("jbl", "JBL speaker"), ("soundlink", "Bose speaker"),
    ("tv", "Television"), ("roku", "Roku TV/stick"), ("firetv", "Fire TV"),
    ("chromecast", "Chromecast"), ("nest", "Nest device"),
    ("ring", "Ring device"), ("wyze", "Wyze camera"), ("cam", "Camera"),
    ("printer", "Printer"), ("hp ", "HP printer"), ("epson", "Epson printer"),
    ("hue", "Philips Hue light"), ("govee", "Govee smart light"),
    ("ihoment", "Govee/iHoment smart light"), ("bulb", "Smart bulb"),
    ("plug", "Smart plug"), ("echo", "Amazon Echo"), ("alexa", "Amazon Echo"),
    ("fitbit", "Fitbit tracker"), ("garmin", "Garmin device"),
    ("tile", "Tile tracker"), ("beacon", "BLE beacon"),
    ("peak pro", "Vape/accessory (Puffco)"), ("crystal uhd", "Samsung TV"),
]

# ---- LAN hostname / UPnP-server keyword -> (device type, is_camera) ----------
# Reverse-DNS names ("RingStickUpCam-0a", "BRW4C82...", "amazon-39ef...") and
# SSDP/UPnP 'server' strings are often the richest clue for a wired/Wi-Fi LAN
# device that answers no scanned ports. Matched in order; first hit wins, so the
# most specific tokens come first.
HOST_HINTS = [
    ("ringstickup", "Ring camera", True), ("doorbell", "Video doorbell", True),
    ("nestcam", "Nest camera", True), ("wyzecam", "Wyze camera", True),
    ("wyze", "Wyze device", False), ("ringchime", "Ring chime", False),
    ("ring", "Ring device", False), ("ipcam", "IP camera", True),
    ("ipcamera", "IP camera", True), ("cam", "IP camera", True),
    ("brw", "Brother printer", False), ("epson", "Epson printer", False),
    ("canon", "Canon printer", False), ("officejet", "HP printer", False),
    ("printer", "Network printer", False),
    ("firetv", "Amazon Fire TV", False), ("fire-tv", "Amazon Fire TV", False),
    ("echo", "Amazon Echo", False), ("alexa", "Amazon Echo", False),
    ("amazon", "Amazon device", False), ("roku", "Roku", False),
    ("chromecast", "Chromecast", False), ("googlehome", "Google Home", False),
    ("google-home", "Google Home", False), ("nest", "Nest device", False),
    ("shield", "NVIDIA Shield", False), ("appletv", "Apple TV", False),
    ("apple-tv", "Apple TV", False), ("android", "Android device", False),
    ("iphone", "iPhone", False), ("ipad", "iPad", False),
    ("macbook", "MacBook", False), ("sonos", "Sonos speaker", False),
    ("samsung", "Samsung device", False), ("tidbyt", "Tidbyt display", False),
    ("raspberry", "Raspberry Pi", False), ("synology", "Synology NAS", False),
    ("openwrt", "Router", False),
]


def classify_host(hostname, ssdp=""):
    """Map a reverse-DNS hostname (and/or UPnP server string) to a device type.
    Returns (type, is_camera, matched_text) or (None, False, "")."""
    for src in (hostname or "", ssdp or ""):
        s = src.lower()
        if not s:
            continue
        for kw, typ, cam in HOST_HINTS:
            if kw in s:
                return typ, cam, src
    return None, False, ""

# ---- camera-tell-tale TCP ports --------------------------------------------
# STRONG: these strongly imply a camera/DVR on their own.
CAMERA_PORTS = {
    554: "RTSP (camera stream)", 8554: "RTSP-alt", 37777: "Dahua DVR",
    34567: "DVR (XMeye)",
}
# WEAK: camera-ish only ALONGSIDE a camera vendor (8000/8554 ONVIF, etc.).
# Kept separate so generic services (PCs, NAS, consoles) aren't called cameras.
CAMERA_PORTS_WEAK = {8000: "ONVIF/Hik", 9000: "ONVIF-alt"}
WEB_PORTS = {80: "HTTP", 8080: "HTTP-alt", 443: "HTTPS", 8443: "HTTPS-alt"}
OTHER_PORTS = {9100: "Printer (RAW)", 631: "Printer (IPP)", 22: "SSH",
               23: "Telnet", 445: "SMB", 1883: "MQTT", 5000: "UPnP/HTTP"}
ALL_SCAN_PORTS = sorted(set(CAMERA_PORTS) | set(CAMERA_PORTS_WEAK)
                        | set(WEB_PORTS) | set(OTHER_PORTS))

# Short, human service names for every port we actually scan — used to print a
# readable fingerprint ("HTTP, SMB") instead of raw numbers ("80, 445").
SERVICE_NAMES = {
    22: "SSH", 23: "Telnet", 80: "HTTP", 443: "HTTPS", 445: "SMB",
    554: "RTSP", 631: "IPP-print", 1883: "MQTT", 5000: "UPnP",
    8000: "HTTP-alt", 8080: "HTTP-alt", 8443: "HTTPS-alt", 8554: "RTSP-alt",
    9000: "HTTP-alt", 9100: "JetDirect-print", 34567: "DVR(XMeye)",
    37777: "Dahua-DVR",
}


def port_fingerprint(open_ports):
    """Honest, PORT-ONLY fingerprint of a LAN host. Returns (services, os_hint,
    role_hint), all strings ('' when nothing applies).

    These are INFERENCES from which TCP ports answered — NOT real OS
    fingerprinting (no TTL/TCP-option probing here). Callers must present them
    as 'likely', never as a measured fact.
    """
    ports = sorted(set(open_ports or []))
    s = set(ports)
    services = ", ".join(SERVICE_NAMES.get(p, str(p)) for p in ports)

    # OS family — only the few honest tells a port scan gives us.
    if 445 in s:
        os_hint = "likely Windows / SMB host"
    elif 23 in s:
        os_hint = "likely embedded / IoT (Telnet open)"
    elif 22 in s and not (s & {9100, 631, 554}):
        os_hint = "likely Linux / Unix-like (SSH)"
    else:
        os_hint = ""

    # Role — strongest service wins.
    if s & {554, 8554, 34567, 37777}:
        role_hint = "camera / DVR"
    elif s & {9100, 631}:
        role_hint = "printer"
    elif 1883 in s:
        role_hint = "IoT device (MQTT)"
    elif s & {80, 443, 8080, 8443, 8000, 9000, 5000}:
        role_hint = "has a web UI"
    else:
        role_hint = ""

    return services, os_hint, role_hint


def norm_mac(mac):
    if not mac:
        return ""
    return mac.replace("-", ":").lower().strip()


def is_random_mac(mac):
    """True if the MAC is locally-administered (randomized for privacy)."""
    m = norm_mac(mac)
    try:
        first = int(m.split(":")[0], 16)
        return bool(first & 0x02)
    except Exception:
        return False


def vendor_for_mac(mac):
    """Return (vendor, is_random). vendor is None if unknown."""
    m = norm_mac(mac)
    if not m or m.count(":") < 2:
        return None, False
    if is_random_mac(m):
        return None, True
    oui = ":".join(m.split(":")[:3])
    return OUI_VENDORS.get(oui), False


def vendor_is_camera(vendor):
    return vendor in CAMERA_VENDORS if vendor else False


def vendor_label(mac):
    """Human label for a MAC's maker: the vendor, a randomized-MAC note, or an
    honest 'Unknown (OUI xx:xx:xx)' that still pins down the hardware prefix."""
    m = norm_mac(mac)
    v, rand = vendor_for_mac(m)
    if v:
        return v
    if rand:
        return "Randomized MAC (private)"
    if m.count(":") >= 2:
        return "Unknown (OUI %s)" % ":".join(m.split(":")[:3])
    return "Unknown vendor"


def _name_type(name):
    n = (name or "").lower()
    for kw, typ in NAME_HINTS:
        if kw in n:
            return typ
    return None


# ---- BLE manufacturer-data parsing: the strongest device-TYPE signal --------
# Microsoft "CDP" beacon device-type byte (Swift Pair / Nearby Share).
MS_CDP_DEVICE_TYPES = {
    1: "Xbox console", 6: "iPhone", 7: "iPad", 8: "Android phone",
    9: "Windows PC (desktop)", 11: "Windows phone", 12: "Linux device",
    14: "Surface Hub", 15: "Windows laptop", 16: "Windows tablet",
}


def _apple_segments(payload):
    """Apple continuity adverts are TLV segments; return the set of type bytes."""
    segs = set()
    i, n = 0, len(payload)
    while i + 1 < n:
        t = payload[i]
        ln = payload[i + 1]
        segs.add(t)
        i += 2 + ln
    if not segs and n >= 1:
        segs.add(payload[0])
    return segs


def classify_ble_manufacturer(mfr):
    """Infer DEVICE TYPE from BLE manufacturer data. Returns (type, conf, evidence).

    This is method-independent: it says WHAT the device is (phone, earbuds, …),
    never how it was seen. The big wins are Apple continuity beacons (iPhone vs
    AirPods vs Watch vs Find My) and Microsoft CDP beacons (Android phone vs
    Windows laptop vs Xbox).
    """
    mfr = mfr or {}
    if 0x004C in mfr:                       # Apple
        segs = _apple_segments(mfr[0x004C])
        if 0x12 in segs:
            return "Item tracker (Apple Find My)", 80, ["Apple Find My beacon (type 0x12)"]
        if 0x07 in segs:
            return "Wireless earbuds (AirPods/Beats)", 72, ["Apple proximity-pairing (type 0x07)"]
        if 0x06 in segs or 0x0B in segs:
            return "Apple Watch", 64, ["Apple Watch beacon"]
        if 0x09 in segs or 0x0A in segs:
            return "Apple TV / HomePod", 60, ["Apple AirPlay beacon"]
        if segs & {0x10, 0x0C, 0x05, 0x0F}:
            return "iPhone / iPad (Apple)", 66, ["Apple Nearby/Handoff beacon (active device)"]
        return "Apple device", 42, ["Apple manufacturer data"]
    if 0x0006 in mfr:                       # Microsoft CDP / Swift Pair
        p = mfr[0x0006]
        if len(p) >= 2 and p[0] == 0x01:
            name = MS_CDP_DEVICE_TYPES.get(p[1] & 0x3F)
            if name:
                return name, 62, [f"Microsoft CDP beacon → {name}"]
        return "Windows / Microsoft device", 42, ["Microsoft beacon"]
    if 0x0075 in mfr:
        return "Samsung device (phone/watch/buds)", 40, ["Samsung manufacturer data"]
    if 0x00E0 in mfr:
        return "Google / Android device", 42, ["Google manufacturer data"]
    return None, 0, []


def identify(*, mac="", name="", vendor=None, ble_manufacturer=None,
             ble_services=None, ble_appearance=None, ssid=None, open_ports=None,
             hostname="", ssdp="", seen_via=""):
    """Best-guess DEVICE TYPE (what it is) from whatever clues are available.

    The returned `type` is always a real device type (iPhone, earbuds, printer,
    Wi-Fi AP, …) or an honest "Unknown device" — NEVER the radio it was seen on.
    `seen_via` (the detection method) is carried through separately, untouched.

    Returns: {type, vendor, confidence, evidence:[...], is_camera, seen_via}.
    """
    ble_manufacturer = ble_manufacturer or {}
    ble_company_ids = list(ble_manufacturer.keys())
    ble_services = ble_services or []
    open_ports = open_ports or []
    evidence = []
    conf = 0
    dtype = None
    is_camera = False

    # vendor: MAC OUI first, then BLE company id
    rand = is_random_mac(mac) if mac else False
    if vendor is None:
        vendor, _ = vendor_for_mac(mac)
    if vendor:
        evidence.append(f"vendor {vendor} (MAC OUI)")
        conf += 18
    for cid in ble_company_ids:
        v = BLE_COMPANY_IDS.get(cid)
        if v and not vendor:
            vendor = v
            evidence.append(f"vendor {v} (BLE company ID 0x{cid:04X})")
            conf += 12

    # (A) STRONGEST device-type signal: BLE manufacturer beacons (Apple/MS/…)
    bt, bconf, bev = classify_ble_manufacturer(ble_manufacturer)
    if bt:
        dtype = bt
        conf += bconf
        evidence.extend(bev)
        if "tracker" in bt.lower():
            pass

    # (B) cameras by port / vendor (network scan) — overrides generic types
    cam_ports = [p for p in open_ports if p in CAMERA_PORTS]
    weak_ports = [p for p in open_ports if p in CAMERA_PORTS_WEAK]
    if cam_ports:
        is_camera = True
        dtype = (vendor + " IP camera") if vendor_is_camera(vendor) else "IP camera"
        conf += 40
        evidence.append("open " + ", ".join(f"{p} ({CAMERA_PORTS[p]})" for p in cam_ports))
    elif vendor_is_camera(vendor):
        is_camera = True
        dtype = f"{vendor} camera"
        conf += 35
        evidence.append("known camera vendor")
    elif weak_ports and vendor_is_camera(vendor):
        is_camera = True
        dtype = dtype or f"{vendor} camera"
        conf += 25
        evidence.append("ONVIF-ish port + camera vendor")
    if 9100 in open_ports or 631 in open_ports:
        dtype = dtype or "Network printer"
        conf += 30
        evidence.append("printer port open")
    web = [p for p in open_ports if p in WEB_PORTS]
    if web and not dtype:
        dtype = "Networked device (web UI)"
        conf += 10
        evidence.append("web port " + ", ".join(str(p) for p in web))

    # (C) BLE appearance / service UUIDs
    if ble_appearance in BLE_APPEARANCE:
        dtype = dtype or BLE_APPEARANCE[ble_appearance]
        conf += 25
        evidence.append(f"BLE appearance: {BLE_APPEARANCE[ble_appearance]}")
    for s in ble_services:
        s16 = (s & 0xFFFF) if isinstance(s, int) else None
        if s16 in BLE_SERVICE_HINTS:
            dtype = dtype or BLE_SERVICE_HINTS[s16]
            conf += 18
            evidence.append(f"BLE service: {BLE_SERVICE_HINTS[s16]}")

    # (D) advertised name (often the most human-meaningful)
    nt = _name_type(name)
    if nt:
        dtype = nt if (dtype is None or dtype in ("Apple device", "Windows / Microsoft device")) else dtype
        conf += 22
        evidence.append(f'advertised name "{name}"')
    elif name:
        evidence.append(f'name "{name}"')
        conf += 5

    # (E) SSID (Wi-Fi)
    if ssid:
        st = _name_type(ssid)
        if st:
            dtype = dtype or st
            conf += 12
            evidence.append(f'SSID "{ssid}"')

    # (E2) LAN hostname / UPnP server string — often the best clue for a wired/
    # Wi-Fi device that answers no ports (e.g. "RingStickUpCam-0a" → Ring camera).
    ht, hcam, hsrc = classify_host(hostname, ssdp)
    _generic = (dtype is None or dtype.startswith("Unknown")
                or "Networked device" in (dtype or "") or (dtype or "").endswith(" device"))
    if ht and _generic:
        dtype = ht
        conf += 28
        evidence.append(f'hostname/UPnP "{hsrc}"')
        if hcam:
            is_camera = True
    elif ht and hcam and not is_camera:
        # a camera hint is important even if a (non-camera) type was already set
        is_camera = True
        evidence.append(f'camera hostname "{hsrc}"')

    if rand and not vendor:
        evidence.append("randomized/private MAC (vendor hidden)")

    # final fallback — NEVER the radio name; honest "Unknown" + vendor if any
    if not dtype:
        if vendor:
            dtype = f"{vendor} device"
            conf = max(conf, 25)
        else:
            via = f" (seen via {seen_via})" if seen_via else ""
            dtype = "Unknown device" + via
            conf = max(conf, 8)

    return {
        "type": dtype,
        "vendor": vendor,
        "seen_via": seen_via,
        "confidence": max(5, min(95, conf)),
        "evidence": evidence,
        "is_camera": is_camera,
    }
