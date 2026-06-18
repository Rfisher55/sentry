"""Local network (LAN) scanner — finds devices actually ON your Wi-Fi network.

This is how real tools find hidden Wi-Fi cameras: enumerate every host on the
subnet you're connected to, get its IP + MAC + vendor, and fingerprint it by the
TCP ports it has open (RTSP 554, ONVIF, web UIs, Dahua/Hik ports).

Pure-Python, no nmap required:
  1. ping-sweep the /24 in parallel to populate the ARP table (ARP resolves even
     if a host drops ICMP),
  2. read the ARP table for IP -> MAC of every live host,
  3. TCP-connect-scan each live host's camera/web/common ports,
  4. identify vendor (MAC OUI) and device type, flagging likely cameras with the
     concrete evidence ("port 554 open + Dahua MAC").

Runs in a background worker so a slow sweep never stalls the live feed.

SCOPE NOTE (honesty): unlike the RF/Wi-Fi/BLE sensors, which passively receive,
this sensor ACTIVELY probes — it pings every host on the /24, opens TCP
connections to common ports, and sends an SSDP query. It still reads nothing
private and attacks nothing, but it is active reconnaissance, so it must only be
used on a network you own or are authorised to test. The UI discloses this in
the sensor status note.
"""

from sentry_backend.sensor import Sensor, Detection
from sentry_backend import identify
import socket
import subprocess
import threading
import time
import re
import shutil
import platform
import concurrent.futures as cf


class NetworkSensor(Sensor):
    channel = "network"
    name = "Local Network Scanner"

    SCAN_PERIOD = 30.0          # seconds between full LAN sweeps

    def __init__(self):
        super().__init__()
        self._dets = []
        self._lock = threading.Lock()
        self._thread = None
        self._started = False
        self._subnet = None
        self._self_ip = None

    # ---- availability: we need a real (non-loopback) IPv4 ------------------
    def _local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))   # no packets sent; just picks the route
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass
        return None

    def available(self) -> bool:
        ip = self._local_ip()
        if ip:
            self._self_ip = ip
            self._subnet = ip.rsplit(".", 1)[0]   # /24 assumption (home networks)
            return True
        return False

    def _setup(self):
        if self._started:
            return
        self._started = True
        self._note = ("ACTIVE scan of %s.0/24 every %ds — pings every host, makes TCP "
                      "connections to common ports, and sends an SSDP query. This is "
                      "active probing, not passive listening. Use only on a network you "
                      "own or are authorised to test." % (self._subnet, int(self.SCAN_PERIOD)))
        self._thread = threading.Thread(target=self._run_loop, daemon=True,
                                        name="lan-scanner")
        self._thread.start()

    def _run_loop(self):
        while True:
            try:
                dets = self._full_scan()
                with self._lock:
                    self._dets = dets
            except Exception as e:
                self._error = str(e)
            time.sleep(self.SCAN_PERIOD)

    # ---- the actual scan ---------------------------------------------------
    def _ping(self, ip):
        # one quick ping to provoke ARP resolution; we ignore the result
        if platform.system() == "Windows":
            cmd = ["ping", "-n", "1", "-w", "350", ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", ip]
        try:
            subprocess.run(cmd, capture_output=True, timeout=2)
        except Exception:
            pass

    def _arp_table(self):
        """Return {ip: mac} for hosts on our subnet from the OS ARP cache."""
        out = ""
        try:
            # errors="replace": guard against non-ASCII bytes in the ARP table
            # (e.g. an interface/host label) that aren't valid in the console code
            # page — without it the decode crashes the scan thread.
            out = subprocess.run(["arp", "-a"], capture_output=True,
                                 text=True, errors="replace", timeout=8).stdout
        except Exception:
            return {}
        table = {}
        for line in out.splitlines():
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5})", line)
            if not m:
                continue
            ip, mac = m.group(1), identify.norm_mac(m.group(2))
            if not ip.startswith(self._subnet + "."):
                continue
            last = ip.rsplit(".", 1)[1]
            if last in ("0", "255") or mac in ("ff:ff:ff:ff:ff:ff",) or mac.startswith("01:00:5e"):
                continue
            table[ip] = mac
        return table

    def _scan_ports(self, ip, ports, timeout=0.4):
        open_ports = []
        for p in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                if s.connect_ex((ip, p)) == 0:
                    open_ports.append(p)
                s.close()
            except Exception:
                pass
        return open_ports

    def _reverse_dns(self, ip):
        """Reverse-DNS hostname for a LAN IP — often the single richest clue
        ('RingStickUpCam-0a', 'BRW4C82...', 'amazon-39ef...'). '' if none."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""

    def _ssdp_probe(self, timeout=2.5):
        """One SSDP/UPnP M-SEARCH; collect {ip: server-string} from responders
        (media renderers, smart TVs, some cameras). Listen-only, best-effort."""
        res = {}
        try:
            msg = ("M-SEARCH * HTTP/1.1\r\nHOST:239.255.255.250:1900\r\n"
                   'MAN:"ssdp:discover"\r\nMX:2\r\nST:ssdp:all\r\n\r\n').encode()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(timeout)
            s.sendto(msg, ("239.255.255.250", 1900))
            end = time.time() + timeout
            while time.time() < end:
                try:
                    data, addr = s.recvfrom(2048)
                except Exception:
                    break
                srv = ""
                for ln in data.decode("latin1").split("\r\n"):
                    if ln.lower().startswith("server:"):
                        srv = ln[7:].strip()
                if srv:
                    res.setdefault(addr[0], srv)
            s.close()
        except Exception:
            pass
        return res

    def _full_scan(self):
        if not self._subnet:
            return []
        # 1) ping-sweep to populate ARP (parallel)
        targets = [f"{self._subnet}.{i}" for i in range(1, 255)]
        with cf.ThreadPoolExecutor(max_workers=80) as ex:
            list(ex.map(self._ping, targets))
        # 2) read ARP for live hosts
        table = self._arp_table()
        # 2b) one SSDP/UPnP sweep for richer identification of port-silent hosts
        ssdp = self._ssdp_probe()
        # 3) port-scan + reverse-DNS each live host (parallel across hosts)
        def fingerprint(item):
            ip, mac = item
            ports = self._scan_ports(ip, identify.ALL_SCAN_PORTS)
            host = self._reverse_dns(ip)
            return ip, mac, ports, host
        results = []
        if table:
            with cf.ThreadPoolExecutor(max_workers=40) as ex:
                results = list(ex.map(fingerprint, table.items()))

        self._note = ("Found %d device(s) on %s.0/24 by ACTIVE probing (pings + TCP "
                      "port connects + SSDP) — not passive. Use only on a network you "
                      "own/are authorised on." % (len(results), self._subnet))

        dets = []
        for ip, mac, ports, host in results:
            vendor, rand = identify.vendor_for_mac(mac)
            srv = ssdp.get(ip, "")
            info = identify.identify(mac=mac, vendor=vendor, open_ports=ports,
                                     hostname=host, ssdp=srv, seen_via="Network (LAN)")
            host_disp = host.split(".")[0] if host else ""   # drop .lan/.local suffix
            is_self = (ip == self._self_ip)
            # port-only fingerprint: readable service names + hedged OS/role
            # inferences (NOT real OS fingerprinting — see identify.port_fingerprint)
            services, os_hint, role_hint = identify.port_fingerprint(ports)
            svc_txt = services or "no common ports open"

            if info["is_camera"]:
                sev, cat = "alert", "camera"
                kind = info["type"]
                surveil = "Video (and likely audio) of its field of view"
                cap = "Streams/records over your network — check who can reach it"
                now = "On your network — a likely camera"
            elif is_self:
                sev, cat = "notable", "self"
                kind = "This computer (SENTRY)"
                surveil = "—"; cap = "—"; now = "Running SENTRY"
            else:
                sev, cat = "notable", "network device"
                kind = info["type"]
                # promote a port-based role onto an otherwise-vague label so LAN
                # hosts read specifically — e.g. "Network host — printer" beats
                # the generic "Networked device (web UI)". It's a port inference,
                # so it stays hedged ("— <role>"), never asserted as certain.
                if role_hint and ("Networked device" in kind or kind.startswith("Unknown device")):
                    kind = "Network host — " + role_hint
                surveil = "Depends on the device"
                cap = "Whatever it's designed to do on the network"
                now = "Connected to your Wi-Fi network"

            ev = list(info["evidence"])
            ev.append(f"IP {ip}")
            if host:
                ev.append(f"hostname {host}")
            if srv:
                ev.append("UPnP: " + srv[:48])
            if services:
                ev.append("services: " + services)
            if os_hint:
                ev.append("fingerprint: " + os_hint + " (from open ports only)")

            behavior = f"On your network at {ip}. " + (
                "Open services: " + services + "." if services
                else "No common ports answered.")
            if os_hint and not is_self:
                behavior += " Port fingerprint: " + os_hint + "."

            dets.append(Detection(
                kind=kind, channel="network", severity=sev, category=cat,
                maker=identify.vendor_label(mac),
                model=host_disp or info["type"], mac=mac, ip=ip,
                ident=f"{ip} · {svc_txt}", bandtxt="LAN (Wi-Fi)",
                behaviortxt=behavior,
                surveilling=surveil, cancapture=cap, capturingnow=now,
                confidence=info["confidence"], device_type=kind,
                method="Network (LAN)", evidence=ev,
            ))
        return dets

    def scan(self):
        with self._lock:
            return list(self._dets)
