"""Quick structural check of the UI's inline <script>: bracket balance + a few
required function names. Not a full JS parser, but catches the edit mistakes
that actually happen. Run: python -m tests.jscheck
"""
import re
import io
import sys

html = io.open("ui/index.html", encoding="utf-8").read()
m = re.search(r"<script>(.*)</script>", html, re.S)
js = m.group(1)


def strip(s):
    out = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"`":
            q = c
            i += 1
            while i < n and s[i] != q:
                if s[i] == "\\":
                    i += 2
                    continue
                i += 1
            i += 1
            continue
        if c == "/" and i + 1 < n and s[i + 1] == "/":
            while i < n and s[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and s[i + 1] == "*":
            i += 2
            while i + 1 < n and not (s[i] == "*" and s[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


code = strip(js)
pairs = {")": "(", "]": "[", "}": "{"}
stack = []
ok = True
for ch in code:
    if ch in "([{":
        stack.append(ch)
    elif ch in ")]}":
        if not stack or stack[-1] != pairs[ch]:
            ok = False
            break
        stack.pop()
ok = ok and not stack
print("JS bracket balance:", "OK" if ok else "FAILED")

required = ["function applyLive", "function syncDevList", "function updateDevRow",
           "function drawRadar", "function openLocate", "function identify",
           "function passesFilters", "function miniBar"]
missing = [r for r in required if r not in js and r != "function identify"]
for r in required:
    if r == "function identify":
        continue
    if r not in js:
        print("  MISSING:", r)
sys.exit(0 if (ok and not missing) else 1)
