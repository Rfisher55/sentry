"""Network Inspector + Security Learning Lab — YOUR OWN network only.

Two legitimate, defensive capabilities for the network you're on (and authorised
to test) and the devices on it:

  * SECURITY LAB — a pure-Python TCP connect port/service scan of a device on your
    LAN, with plain-English "what this means", an encrypted-vs-plaintext exposure
    read, camera/IoT tells (RTSP/ONVIF/DVR ports), and risk findings with how-to-fix
    notes. No external tools needed; it actively probes (connects to ports), so it
    is active reconnaissance — only use it on a network you own or are authorised on.

  * NETWORK INSPECTOR (live traffic) — readable packet capture, DNS log, per-device
    "phone-home" map, protocol breakdown, top-talkers. This needs Wireshark/tshark
    (and on Windows, Npcap) installed; if they're absent we say so plainly and tell
    you exactly what to install, rather than faking it.

HONESTY/LEGAL: own network/devices only. This inspects YOUR traffic to learn what
your devices expose — it never decodes or captures other people's private
communications, and it never attacks anything (no exploitation, just observation
and a port knock).
"""

import socket
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor


# Ports worth knocking on a home/IoT LAN: remote-access, web, file, media/IoT,
# camera/DVR, printers, discovery. (service name, is-encrypted)
PORTS = {
    21:   ("FTP", False), 22: ("SSH", True), 23: ("Telnet", False), 25: ("SMTP", False),
    53:   ("DNS", False), 80: ("HTTP", False), 110: ("POP3", False), 143: ("IMAP", False),
    443:  ("HTTPS", True), 445: ("SMB", False), 515: ("Printer (LPD)", False),
    554:  ("RTSP (video)", False), 631: ("IPP (print)", False), 993: ("IMAPS", True),
    1883: ("MQTT", False), 1900: ("SSDP/UPnP", False), 3389: ("RDP", True),
    5000: ("UPnP/HTTP", False), 5353: ("mDNS", False), 8000: ("HTTP-alt", False),
    8080: ("HTTP-alt", False), 8443: ("HTTPS-alt", True), 8554: ("RTSP-alt", False),
    9000: ("HTTP-alt", False), 9100: ("Printer (JetDirect)", False),
    32400: ("Plex", False), 34567: ("DVR (Xiongmai)", False), 37777: ("DVR (Dahua)", False),
    49152: ("UPnP/HTTP", False), 62078: ("iPhone sync", False),
}
DEFAULT_PORTS = sorted(PORTS.keys())

# Camera/DVR tells — an open one of these STRONGLY suggests a camera/recorder.
# (HTTP/8000 alone are NOT here — plenty of non-cameras serve web on those.)
CAMERA_PORTS = {554: "RTSP video stream", 8554: "RTSP video stream",
                37777: "Dahua DVR/NVR", 34567: "Xiongmai/'Sofia' DVR"}

# Risk knowledge: port -> (severity, what it means, how to fix). Educational,
# defensive — it explains the exposure, it does not exploit anything.
RISK = {
    23:   ("high", "Telnet — unencrypted remote login. A classic IoT weakness; "
                   "credentials and everything you type cross the network in clear text.",
                   "Disable Telnet on the device. Use SSH if you need remote access, "
                   "or block port 23 at the router."),
    21:   ("high", "FTP — often anonymous or plaintext; files and logins are exposed.",
                   "Disable FTP or switch to SFTP/FTPS. Don't expose it to the internet."),
    445:  ("high", "SMB file sharing — a frequent ransomware/worm target if exposed "
                   "or unpatched.",
                   "Keep the OS patched, use strong account passwords, never forward "
                   "445 to the internet."),
    3389: ("high", "RDP (Remote Desktop) — a top brute-force/credential-stuffing target.",
                   "Don't expose RDP to the internet; require a VPN, strong passwords, "
                   "and account lockout."),
    3306: ("high", "Database (MySQL) reachable on the network.",
                   "Bind the database to localhost or restrict by firewall; never expose it."),
    1883: ("medium", "MQTT (IoT message bus), often unauthenticated — devices can be "
                     "read or commanded if it's open.",
                     "Enable MQTT auth/TLS, or firewall it to trusted devices only."),
    80:   ("medium", "HTTP web interface — the login page and session are in clear text "
                     "on your LAN.",
                     "Prefer the HTTPS port if the device offers one; change default "
                     "credentials."),
    554:  ("medium", "RTSP video — the stream (and sometimes the login) is unencrypted; "
                     "anyone on the network may be able to view it.",
                     "Set a strong camera password, disable RTSP if unused, and isolate "
                     "cameras on their own VLAN/guest network."),
    1900: ("low", "UPnP/SSDP — device auto-discovery/port-opening. Convenient but a "
                  "known attack surface.",
                  "Disable UPnP on the router unless you need it."),
    9100: ("low", "Raw printing port — printers here can be sent jobs by anyone on the LAN.",
                  "Fine on a trusted home LAN; restrict if on a shared network."),
}

# A few obvious default-credential devices, by vendor substring → note.
DEFAULT_CRED_HINTS = {
    "hikvision": "Hikvision cameras historically shipped with admin/12345 — make sure "
                 "the default password was changed.",
    "dahua": "Dahua DVRs/cameras had default admin/admin — verify it was changed.",
    "tp-link": "Some TP-Link gear ships admin/admin — verify the admin password.",
}


# ----------------------------- port scanning --------------------------------
def scan_ports(ip, ports=None, timeout=0.4, workers=64):
    """Pure-Python TCP connect scan of one host. Returns the list of OPEN ports.
    A connect scan is a normal TCP handshake — observation, not exploitation."""
    ports = ports or DEFAULT_PORTS
    open_ports = []

    def check(p):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            if s.connect_ex((ip, p)) == 0:
                return p
        except Exception:
            return None
        finally:
            try:
                s.close()
            except Exception:
                pass
        return None

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for r in ex.map(check, ports):
            if r is not None:
                open_ports.append(r)
    return sorted(open_ports)


def assess_device(ip, vendor, open_ports):
    """Turn an open-port list into a readable, educational security report for one
    of YOUR devices: services, plaintext exposure, camera tells, risk findings +
    fixes, and a plain-English 'learn' summary."""
    services = []
    plaintext = []
    encrypted = []
    findings = []
    cam_tells = []
    worst = "info"
    sev_rank = {"info": 0, "low": 1, "medium": 2, "high": 3}

    for p in open_ports:
        name, enc = PORTS.get(p, ("unknown", False))
        services.append({"port": p, "service": name, "encrypted": enc})
        (encrypted if enc else plaintext).append(f"{name} ({p})")
        if p in CAMERA_PORTS:
            cam_tells.append(f"{CAMERA_PORTS[p]} (port {p})")
        if p in RISK:
            sev, what, fix = RISK[p]
            findings.append({"port": p, "service": name, "severity": sev,
                             "what": what, "fix": fix})
            if sev_rank[sev] > sev_rank[worst]:
                worst = sev

    # default-credential awareness by vendor
    vl = (vendor or "").lower()
    for key, note in DEFAULT_CRED_HINTS.items():
        if key in vl and any(p in (80, 443, 554, 8000, 37777, 34567) for p in open_ports):
            findings.append({"port": None, "service": "default credentials",
                             "severity": "high", "what": note,
                             "fix": "Log in and set a strong, unique password if you "
                                    "haven't already."})
            worst = "high"

    likely_camera = bool(cam_tells) or ("camera" in vl) or any(
        k in vl for k in ("hikvision", "dahua", "reolink", "amcrest", "wyze", "ring", "nest"))

    # plain-English learn summary
    if not open_ports:
        learn = ("No open TCP ports responded — this device isn't exposing common "
                 "services on the LAN (or it's filtering the scan). That's generally good.")
    else:
        bits = []
        if plaintext:
            bits.append("exposes " + ", ".join(plaintext) + " in CLEAR TEXT on your "
                        "network (anyone on the LAN could read that traffic)")
        if encrypted:
            bits.append("uses encryption for " + ", ".join(encrypted))
        if likely_camera:
            bits.append("looks like a camera/recorder")
        learn = ("This device " + "; ".join(bits) + ". Open ports are doors — each one "
                 "is a service that's reachable. Close the ones you don't use, and put "
                 "a strong password on the rest.")

    return {
        "ip": ip, "vendor": vendor, "open_ports": open_ports,
        "services": services,
        "plaintext": plaintext, "encrypted": encrypted,
        "camera_tells": cam_tells, "likely_camera": likely_camera,
        "findings": findings, "worst_severity": worst,
        "learn": learn,
        "scanned": True,
    }


# ------------------------- live capture (tshark) ----------------------------
def capture_tool():
    """Return the path to tshark if Wireshark's CLI is installed, else None."""
    p = shutil.which("tshark")
    if p:
        return p
    # common Windows install location
    import os
    for c in (r"C:\Program Files\Wireshark\tshark.exe",
              r"C:\Program Files (x86)\Wireshark\tshark.exe"):
        if os.path.exists(c):
            return c
    return None


def capture_status():
    """Honest report of whether live packet capture is available, and if not,
    exactly what to install to unlock the Network Inspector traffic features."""
    tool = capture_tool()
    if tool:
        return {"available": True, "tool": tool,
                "note": "Wireshark/tshark found — live traffic capture is available "
                        "on networks/devices you own."}
    return {
        "available": False, "tool": None,
        "needs": ["Npcap (packet driver, install with 'WinPcap API-compatible mode')",
                  "Wireshark (includes the tshark command-line capture tool)"],
        "how": ("Install Wireshark from https://www.wireshark.org/download.html and "
                "tick Npcap during setup (Windows). Then restart SENTRY — the live "
                "traffic view, DNS log, per-device phone-home map, protocol breakdown "
                "and top-talkers will activate. Capture only on a network you own/are "
                "authorised on; SENTRY only summarises YOUR traffic and never decodes "
                "other people's private content."),
        "note": "Live packet capture is OFFLINE — Wireshark/tshark (and Npcap) aren't "
                "installed. Port scanning + risk analysis below work without them.",
    }
