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

import os
import socket
import shutil
import subprocess
import xml.etree.ElementTree as ET
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


def service_note(port, service=""):
    """One-line plain-English note on a service + whether it should be exposed."""
    if port in RISK:
        return RISK[port][1]
    if port in CAMERA_PORTS:
        return CAMERA_PORTS[port] + " — a camera/recorder service; lock it down and isolate it."
    name, enc = PORTS.get(port, (service or "service", False))
    if enc:
        return name + " — encrypted; fine, just keep credentials strong."
    return name + " — usually OK on a trusted LAN; close it if you don't use it."


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


# ============================ nmap integration ==============================
# Professional scanning/enumeration. RECON + ASSESSMENT only — selectable scan
# types, NSE *safe/default* discovery scripts (never brute/intrusion), service &
# version detection, OS fingerprint, host discovery. Own/authorised targets only.
def nmap_tool():
    p = shutil.which("nmap")
    if p:
        return p
    for c in (r"C:\Program Files (x86)\Nmap\nmap.exe", r"C:\Program Files\Nmap\nmap.exe"):
        if os.path.exists(c):
            return c
    return None


def nmap_status():
    tool = nmap_tool()
    if tool:
        ver = ""
        try:
            ver = subprocess.run([tool, "--version"], capture_output=True, text=True,
                                 errors="replace", timeout=8).stdout.splitlines()[0]
        except Exception:
            pass
        return {"available": True, "tool": tool, "version": ver}
    return {"available": False, "tool": None,
            "needs": ["Nmap (winget: Insecure.Nmap, or https://nmap.org/download.html)"],
            "how": ("Install Nmap (it uses the Npcap you already have). winget: "
                    "'winget install Insecure.Nmap'. Then restart SENTRY — the advanced "
                    "scans (service/version, OS, NSE safe scripts, full port + host "
                    "discovery) activate. Until then, SENTRY's built-in pure-Python port "
                    "scan still works.")}


# scan_type -> (nmap args, needs_admin, human label, what-it-does)
NMAP_SCANS = {
    "discovery": (["-sn"], False, "Host discovery (subnet sweep)",
                  "Finds every live host on the subnet (ping/ARP sweep) — a full inventory, no port scan."),
    "quick":     (["-sT", "-F", "-sV", "--version-light"], False, "Quick scan",
                  "Connect-scans the top 100 ports with light service detection — fast overview."),
    "version":   (["-sT", "-sV"], False, "Service / version (-sV)",
                  "Identifies the exact software + version behind each open port."),
    "scripts":   (["-sT", "-sV", "--script", "default,safe"], False, "NSE safe scripts",
                  "Runs nmap's default + safe discovery scripts to enumerate services (no brute/intrusion)."),
    "ports":     (["-sT", "-p-", "--open"], False, "Full port scan (all 65535)",
                  "Connect-scans every TCP port — thorough but slow."),
    "os":        (["-sT", "-O", "-sV"], True, "OS fingerprint (-O)",
                  "Guesses the operating system from network behaviour (needs admin for raw packets)."),
    "aggressive":(["-A"], True, "Aggressive (-A)",
                  "OS + version + default scripts + traceroute in one (needs admin)."),
}


def nmap_scan(target, scan_type="quick", timeout=300):
    """Run nmap on an OWN/authorised target and return structured results
    (hosts, ports, services, versions, OS guesses, NSE script output). Refuses
    non-private targets. Returns needs_install if nmap isn't present."""
    tool = nmap_tool()
    if not tool:
        return {"ok": False, "needs_install": True, "error": "nmap is not installed.",
                "status": nmap_status()}
    target = str(target or "").strip()
    # allow a single private host or a private CIDR (e.g. 192.168.1.0/24)
    host = target.split("/")[0]
    if not _is_private(host):
        return {"ok": False, "error": "Only private/LAN targets (your own network) are "
                                      "allowed — public addresses are refused.", "target": target}
    spec = NMAP_SCANS.get(scan_type, NMAP_SCANS["quick"])
    args, needs_admin, label, what = spec
    cmd = [tool, "-oX", "-", "-T4", "--host-timeout", "120s"] + args + [target]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                              timeout=timeout)
        xml = proc.stdout
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"nmap timed out after {timeout}s — try a smaller "
                                      "scan (Quick) or a single host.", "target": target}
    except Exception as e:
        return {"ok": False, "error": f"nmap failed: {e}", "target": target}
    parsed = _parse_nmap_xml(xml)
    parsed.update({"ok": True, "target": target, "scan_type": scan_type, "label": label,
                   "what": what, "needs_admin": needs_admin})
    if needs_admin and not any(h.get("os") for h in parsed.get("hosts", [])):
        parsed["admin_note"] = ("OS/aggressive detection needs raw-packet (admin) access — "
                                "run SENTRY's server elevated for full results.")
    return parsed


def _parse_nmap_xml(xml):
    hosts = []
    try:
        root = ET.fromstring(xml)
    except Exception:
        return {"hosts": [], "summary": "no parseable nmap output"}
    for h in root.findall("host"):
        st = h.find("status")
        if st is not None and st.get("state") != "up":
            continue
        addr = ""
        mac = ""
        vendor = ""
        for a in h.findall("address"):
            if a.get("addrtype") == "ipv4":
                addr = a.get("addr", "")
            elif a.get("addrtype") == "mac":
                mac = a.get("addr", ""); vendor = a.get("vendor", "")
        hn = h.find("hostnames/hostname")
        hostname = hn.get("name", "") if hn is not None else ""
        ports = []
        for p in h.findall("ports/port"):
            state = p.find("state")
            if state is None or state.get("state") != "open":
                continue
            svc = p.find("service")
            sname = svc.get("name", "") if svc is not None else ""
            product = svc.get("product", "") if svc is not None else ""
            version = svc.get("version", "") if svc is not None else ""
            extra = svc.get("extrainfo", "") if svc is not None else ""
            scripts = [{"id": s.get("id", ""), "output": (s.get("output", "") or "").strip()[:400]}
                       for s in p.findall("script")]
            ports.append({
                "port": int(p.get("portid", 0)), "proto": p.get("protocol", "tcp"),
                "service": sname, "product": product, "version": version, "extra": extra,
                "note": service_note(int(p.get("portid", 0)), sname),
                "scripts": scripts,
            })
        osmatch = ""
        osacc = ""
        om = h.find("os/osmatch")
        if om is not None:
            osmatch = om.get("name", ""); osacc = om.get("accuracy", "")
        hscripts = [{"id": s.get("id", ""), "output": (s.get("output", "") or "").strip()[:400]}
                    for s in h.findall("hostscript/script")]
        hosts.append({"ip": addr, "mac": mac, "vendor": vendor, "hostname": hostname,
                      "ports": ports, "os": osmatch, "os_accuracy": osacc,
                      "host_scripts": hscripts})
    rs = root.find("runstats/finished")
    summary = rs.get("summary", "") if rs is not None else ""
    return {"hosts": hosts, "summary": summary, "host_count": len(hosts)}


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


def _lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


def _is_private(ip):
    try:
        a, b = (int(x) for x in ip.split(".")[:2])
    except Exception:
        return False
    return a == 10 or (a == 192 and b == 168) or (a == 172 and 16 <= b <= 31) or a == 127


def capture_interface():
    """The capture interface (friendly name, e.g. 'Wi-Fi') for the LAN adapter —
    the one carrying your default route. None if it can't be determined."""
    lan = _lan_ip()
    if not lan:
        return None
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-NetIPAddress -IPAddress {lan} -ErrorAction SilentlyContinue).InterfaceAlias"],
            capture_output=True, text=True, errors="replace", timeout=10).stdout.strip()
        return out.splitlines()[0].strip() if out else None
    except Exception:
        return None


# Encrypted-transport classification — for "what do my devices expose in the clear".
_ENC_PROTOS = {"TLS", "SSL", "QUIC", "SSH", "TLSV1.2", "TLSV1.3"}
_ENC_PORTS = {443, 8443, 853, 993, 995, 22, 5061, 636, 990}
_PLAINTEXT_PORTS = {80, 8080, 8000, 21, 23, 25, 110, 143, 554, 1883, 5000, 9100}


def _packet_encrypted(proto, dport):
    if proto.upper() in _ENC_PROTOS:
        return True
    if dport in _ENC_PORTS:
        return True
    return False


def capture_traffic(seconds=8, max_rows=120):
    """Capture live traffic on YOUR network for a few seconds with tshark and
    summarise it — readable rows, protocol breakdown, encrypted-vs-plaintext,
    a DNS query log, a per-device phone-home map (which external hosts each of
    your devices contacts), and top-talkers. It summarises metadata (who talked
    to whom, how much, what protocol) — it never stores or decodes message
    CONTENT. Authorised-network use only."""
    tool = capture_tool()
    if not tool:
        return {"ok": False, "error": "Wireshark/tshark not installed."}
    iface = capture_interface()
    if not iface:
        return {"ok": False, "error": "Could not determine the LAN capture interface."}
    fields = ["frame.time_epoch", "ip.src", "ip.dst", "_ws.col.Protocol",
              "tcp.dstport", "udp.dstport", "frame.len",
              "dns.qry.name", "dns.a", "tls.handshake.extensions_server_name", "http.host"]
    cmd = [tool, "-i", iface, "-a", f"duration:{int(seconds)}", "-n", "-l",
           "-T", "fields", "-E", "separator=\t", "-E", "occurrence=f"]
    for f in fields:
        cmd += ["-e", f]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                             timeout=seconds + 20).stdout
    except Exception as e:
        return {"ok": False, "error": f"capture failed: {e}", "interface": iface}

    name_for_ip = {}            # external IP -> hostname (from DNS answers)
    proto_pkts = {}; proto_bytes = {}
    talkers = {}                # local ip -> bytes
    phone_home = {}             # local ip -> {host/ip: count}
    dns_log = []                # {device, query}
    enc = 0; unenc = 0
    camera_tells = []
    rows = []
    total = 0

    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 11:
            parts += [""] * (11 - len(parts))
        t, src, dst, proto, tdp, udp, ln, dq, da, sni, host = parts[:11]
        if not src and not dst:
            continue
        total += 1
        try:
            size = int(ln) if ln else 0
        except Exception:
            size = 0
        dport = 0
        try:
            dport = int(tdp) if tdp else (int(udp) if udp else 0)
        except Exception:
            dport = 0
        proto = proto or "?"
        proto_pkts[proto] = proto_pkts.get(proto, 0) + 1
        proto_bytes[proto] = proto_bytes.get(proto, 0) + size
        # DNS answer → name map (enriches the phone-home view)
        if dq and da:
            for ip in da.split(","):
                ip = ip.strip()
                if ip:
                    name_for_ip[ip] = dq
        # DNS query log: which of MY devices looked up what
        if dq and _is_private(src):
            dns_log.append({"device": src, "query": dq})
        # encrypted vs plaintext
        if proto.upper() in ("TLS", "SSL", "QUIC") or dport in _ENC_PORTS:
            enc += 1
        elif proto.upper() in ("HTTP", "DNS", "FTP", "TELNET") or dport in _PLAINTEXT_PORTS:
            unenc += 1
        # camera tell
        if proto.upper().startswith("RTSP") or dport in (554, 8554):
            camera_tells.append({"src": src, "dst": dst})
        # phone-home: local device -> external destination
        if _is_private(src) and dst and not _is_private(dst):
            talkers[src] = talkers.get(src, 0) + size
            label = sni or host or name_for_ip.get(dst) or dst
            ph = phone_home.setdefault(src, {})
            ph[label] = ph.get(label, 0) + 1
        elif _is_private(src):
            talkers[src] = talkers.get(src, 0) + size
        # readable row
        if len(rows) < max_rows:
            rows.append({"t": (t.split(".")[0][-6:] if t else ""), "src": src, "dst": dst,
                         "proto": proto, "port": dport, "size": size,
                         "enc": _packet_encrypted(proto, dport)})

    protocols = sorted(
        [{"proto": p, "packets": proto_pkts[p], "bytes": proto_bytes.get(p, 0)} for p in proto_pkts],
        key=lambda x: -x["packets"])
    top_talkers = sorted(
        [{"ip": ip, "bytes": b, "name": name_for_ip.get(ip, "")} for ip, b in talkers.items()],
        key=lambda x: -x["bytes"])[:10]
    phone = []
    for ip, hosts in phone_home.items():
        top = sorted(hosts.items(), key=lambda x: -x[1])[:8]
        phone.append({"device": ip, "contacts": [{"host": h, "count": c} for h, c in top]})
    phone.sort(key=lambda x: -sum(c["count"] for c in x["contacts"]))
    # dedupe DNS log keeping counts
    dns_counts = {}
    for d in dns_log:
        k = (d["device"], d["query"])
        dns_counts[k] = dns_counts.get(k, 0) + 1
    dns_top = sorted([{"device": k[0], "query": k[1], "count": v} for k, v in dns_counts.items()],
                     key=lambda x: -x["count"])[:30]

    return {
        "ok": True, "interface": iface, "seconds": int(seconds), "packets": total,
        "protocols": protocols[:14],
        "encrypted": enc, "plaintext": unenc,
        "dns": dns_top, "phone_home": phone[:12], "top_talkers": top_talkers,
        "camera_tells": camera_tells[:6],
        "rows": rows,
        "note": "Metadata only — who talked to whom, how much, what protocol. "
                "Message CONTENT is never stored or decoded.",
    }


def capture_status():
    """Honest report of whether live packet capture is available, and if not,
    exactly what to install to unlock the Network Inspector traffic features."""
    tool = capture_tool()
    if tool:
        return {"available": True, "tool": tool, "interface": capture_interface(),
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
