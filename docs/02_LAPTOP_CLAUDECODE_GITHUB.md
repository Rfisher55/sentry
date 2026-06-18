# SENTRY — Complete Claude Code + GitHub Manual (Beginner Edition)

**This manual assumes you've never used a terminal, Git, or Claude Code.** It
explains every term and every step, gives you the full daily workflow with real
examples of what to say to Claude Code, and a deep troubleshooting section for
when things break. Copy-paste everything.

> You're setting up so you can **keep building SENTRY on your Windows laptop with
> Claude Code helping you**, with all your work safely backed up on GitHub.

---

# TABLE OF CONTENTS
1. The big picture (what each tool is)
2. Words you need to know
3. STEP 1 — Install the tools (Python, Git, Claude Code)
4. STEP 2 — Put SENTRY on GitHub
5. STEP 3 — Open the project in Claude Code
6. STEP 4 — The daily workflow (with examples)
7. STEP 5 — Real things to ask Claude Code
8. STEP 6 — Saving and updating
9. STEP 7 — Running SENTRY itself
10. Safety + good habits
11. Troubleshooting (deep)
12. Cheat sheet

---

# 1. THE BIG PICTURE

Three separate tools, each with one job:

- **Python** — runs SENTRY (the program is written in Python).
- **Git + GitHub** — saves and backs up your code. *Git* is the tool on your
  laptop; *GitHub* is the website that stores a copy online. Think "save to the
  cloud, with a full history you can roll back."
- **Claude Code** — me, working inside your project folder on your laptop. I can
  read and edit the files, run the program, and fix things, while you talk to me
  in plain English in a terminal window.

**How they fit together:** You open your SENTRY folder in **Claude Code** and we
build/fix things. You **run** it with Python to test. You **save** your work to
**GitHub** so it's backed up and you can undo mistakes.

You do NOT need Claude Code just to *use* SENTRY — only to *keep building* it.

---

# 2. WORDS YOU NEED TO KNOW

- **Terminal / PowerShell:** a text window where you type commands. On Windows we
  use **PowerShell** (built in). Open it: press the Start key, type "PowerShell,"
  press Enter.
- **Command:** a line of text you type and run with **Enter**.
- **Directory / folder:** same thing. `cd` means "change directory" (go into a
  folder).
- **Repository ("repo"):** a project folder that Git tracks. Your SENTRY folder
  becomes a repo.
- **Clone:** download a copy of a repo from GitHub to your laptop.
- **Commit:** a saved snapshot of your changes, with a short message describing
  them.
- **Push:** upload your commits to GitHub. **Pull:** download the latest from
  GitHub.
- **PATH:** a Windows setting that lets you run a tool by name from any folder. If
  a fresh install "isn't recognized," it's usually a PATH issue fixed by opening a
  new window.

---

# 3. STEP 1 — INSTALL THE TOOLS

### 3.1 Install Python
1. Go to **python.org/downloads** → click the big "Download Python 3" button.
2. Run the installer. **CRITICAL:** on the very first screen, check the box
   **"Add Python to PATH"** at the bottom. Then click "Install Now."
3. Verify: open a **new** PowerShell window and type:
   ```powershell
   python --version
   ```
   You should see a version number (e.g. `Python 3.12.x`). If "not recognized,"
   see Troubleshooting 11A.

### 3.2 Install Git
1. Go to **git-scm.com/download/win** → download → run installer → accept all the
   defaults (just keep clicking Next).
2. Verify in a **new** PowerShell window:
   ```powershell
   git --version
   ```

### 3.3 Install Claude Code
> Requires a **Claude Pro plan** or higher. Use **PowerShell, not Git Bash.**
1. In PowerShell, run the official installer:
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
   (Or download from claude.ai/download and run the Windows installer.)
2. **CRITICAL: close PowerShell and open a brand-new window.** The install adds
   Claude to your PATH, but only new windows see it.
3. Verify:
   ```powershell
   claude --version
   ```
   A version number = success. "Not recognized" = you didn't open a new window
   (Troubleshooting 11B).

---

# 4. STEP 2 — PUT SENTRY ON GITHUB

### 4.1 Get the SENTRY folder on your laptop
Download `sentry-repo.zip`, right-click → Extract All, to an easy spot like:
```
C:\Users\YOU\Documents\sentry
```
(Replace `YOU` with your Windows username.)

### 4.2 Make a GitHub account + repo
1. Sign up at github.com (free).
2. Click the **+** (top-right) → **New repository.**
3. Name it `sentry`. Choose **Private.** Do **NOT** check "Add a README" (we have
   one). Click **Create repository.**
4. GitHub shows a page with a URL like
   `https://github.com/YOURNAME/sentry.git` — keep that tab open.

### 4.3 Upload your code (first time)
Open PowerShell and run these one at a time:
```powershell
cd C:\Users\YOU\Documents\sentry
```
```powershell
git init
```
```powershell
git add .
```
```powershell
git commit -m "SENTRY initial commit"
```
```powershell
git branch -M main
```
```powershell
git remote add origin https://github.com/YOURNAME/sentry.git
```
```powershell
git push -u origin main
```
What these do, in order: start tracking this folder → stage all files → save a
snapshot → name the main branch → link to your GitHub repo → upload. The push may
pop up a GitHub sign-in — do it once. Your code is now backed up online.

---

# 5. STEP 3 — OPEN THE PROJECT IN CLAUDE CODE

```powershell
cd C:\Users\YOU\Documents\sentry
claude
```
- The first time, it opens your browser to sign in to your Anthropic account.
- Claude Code automatically reads the **CLAUDE.md** file in the folder, so it
  instantly understands what SENTRY is, how it's built, and the rules (detect-only,
  honest about limits).
- You're now in a chat *inside your project*. Type in plain English.

To leave Claude Code, type `/exit` or press Ctrl+C twice.

---

# 6. STEP 4 — THE DAILY WORKFLOW

Here's the loop you'll repeat. Real example, start to finish:

**1. Open a session:**
```powershell
cd C:\Users\YOU\Documents\sentry
claude
```

**2. Tell Claude Code what you want, in plain words.** For example you type:
> *"Run SENTRY and open it in my browser so I can see it works."*

Claude Code will run the program and tell you the address (http://localhost:8000).
It may ask permission before running commands — say yes.

**3. Ask for a change.** For example:
> *"Add the Wyze and Reolink camera brands to the Wi-Fi detector so it flags
> those cameras too."*

Claude Code finds the right file (`sentry_backend/sensors/wifi.py`), makes the
edit, and shows you what it changed. If it's in "ask mode," it shows the change
and waits for you to approve.

**4. Test it.** You type:
> *"Run it again and confirm there are no errors."*

**5. Save your work to GitHub.** You can just say:
> *"Commit and push my changes with a message describing what we did."*

Or do it yourself in PowerShell:
```powershell
git add .
git commit -m "added Wyze and Reolink to camera detection"
git push
```

**6. Done for now?** Type `/exit`.

That's the whole rhythm: **open → ask → test → save.** Small steps, tested and
saved as you go, so you can always undo.

---

# 7. STEP 5 — REAL THINGS TO ASK CLAUDE CODE

Copy these, or adapt them. Plain English works:

**Getting oriented**
- "Explain what each file in this project does."
- "Walk me through how a detection goes from a sensor to the screen."

**When hardware arrives**
- "My RTL-SDR is plugged in. Confirm the RF sensor comes online and help me tune
  the detection thresholds."
- "My MLX90640 thermal camera is wired up. Write the thermal sensor backend and
  wire it into the interface."
- "The Pi camera is connected. Build the lens-finder sensor that flags
  retroreflections."

**Improving detection**
- "Add more known camera MAC prefixes to wifi.py."
- "Make the Bluetooth scanner better at spotting a tracker that's following me."
- "Show live sensor online/offline status on the Channels tab."

**Fixing things**
- "SENTRY won't start — here's the error." (paste the red text)
- "The RF channel shows nothing even with the dongle in — help me debug."

**Housekeeping**
- "Commit and push my changes."
- "Undo the last change — it broke something."

---

# 8. STEP 6 — SAVING AND UPDATING

### Save your work (do this often)
```powershell
git add .
git commit -m "short description of what changed"
git push
```
Or tell Claude Code: *"commit and push my changes."*

### Get the latest (if you edit on another machine, like the Pi)
```powershell
git pull
```

### If you accidentally break something
Git keeps history. Tell Claude Code *"undo the last commit"* or, to throw away
unsaved edits and return to the last save:
```powershell
git restore .
```

### Update Claude Code itself
```powershell
claude update
```

### Update Python packages (after requirements.txt changes)
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

---

# 9. STEP 7 — RUNNING SENTRY ITSELF

You don't need Claude Code to run it. Two ways:

**Easiest:** double-click **START_SENTRY.bat** in the folder. It sets up
everything the first time and opens the station in your browser.

**From PowerShell:**
```powershell
cd C:\Users\YOU\Documents\sentry
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m sentry_backend.server
```
Then open **http://localhost:8000**. Wi-Fi and Bluetooth detection work with your
laptop's built-in radios; plug in an RTL-SDR for the RF channel. Close the window
to stop.

---

# 10. SAFETY + GOOD HABITS

- **Start Claude Code in "ask mode"** (it asks before changing files) until you
  trust the flow. You can let it run more freely later.
- **Only open the `sentry` folder** with Claude Code — never your whole drive or
  system folders like `C:\Windows`.
- **Commit often** with clear messages. Small saved steps are easy to undo; giant
  unsaved changes are not.
- **Claude Code shares your usage limits with regular Claude chats**, measured in a
  rolling window. If you've been chatting a lot, your coding quota is lower — pace
  big sessions.
- **Read what it's about to do** before approving, especially anything that
  deletes files or installs system-wide.

---

# 11. TROUBLESHOOTING (DEEP)

**11A — `python` not recognized:**
You didn't tick "Add Python to PATH," or didn't open a new window. Fix: re-run the
Python installer → choose **Modify** → ensure "Add to PATH" is on → finish → open
a **new** PowerShell window. Test `python --version`.

**11B — `claude` not recognized:**
Almost always the new-window step. Close every PowerShell window, open a fresh one,
try `claude --version`. If still failing, reboot the laptop (forces PATH refresh),
then retry. If still failing, re-run the installer from Section 3.3.

**11C — "Raw mode is not supported" when starting Claude Code:**
You're running it inside **Git Bash**, which doesn't support what Claude Code's
interface needs. Use **PowerShell** instead (Start → "PowerShell").

**11D — `git push` rejected / "updates were rejected":**
The GitHub copy has changes your laptop doesn't. Pull first, then push:
```powershell
git pull --rebase
git push
```
If it mentions a merge conflict, ask Claude Code: *"help me resolve this git
conflict."*

**11E — Git asks for a username/password every time, or push fails to
authenticate:**
Modern GitHub wants a token, not your account password. Easiest fix: when the
sign-in browser window pops up on first push, log in there. If you're stuck, in
GitHub go to **Settings → Developer settings → Personal access tokens → Tokens
(classic) → Generate**, give it "repo" scope, copy the token, and use it as the
password when prompted. (Ask Claude Code to walk you through it.)

**11F — "fatal: not a git repository":**
You're not inside the SENTRY folder. Run `cd C:\Users\YOU\Documents\sentry` first.
If you truly haven't initialized it, run `git init` (Section 4.3).

**11G — Claude Code can't find or edit a file:**
Make sure you launched `claude` from **inside** the sentry folder (`cd` there
first). If you opened it from your home directory, exit and relaunch from the
project folder.

**11H — SENTRY won't start (red error text):**
Copy the **last few lines** of the error and paste them to Claude Code with "fix
this." Most common cause: a package didn't install — run, inside the activated
venv, `pip install -r requirements.txt`.

**11I — "running low on usage" / Claude Code stops mid-task:**
You've hit the rolling usage limit shared with Claude chats. Wait for the window to
reset, or do lighter work. Plan big build sessions for when you haven't been
chatting heavily.

**11J — I want to start over on a file I messed up:**
If you haven't committed: `git restore path\to\file`. If you committed it, ask
Claude Code to *"revert the last commit."* Your history protects you.

---

# 12. CHEAT SHEET

```
INSTALL (once):
  python.org  (tick "Add to PATH")   git-scm.com   irm https://claude.ai/install.ps1 | iex
  (open a NEW PowerShell window after each)

PUT ON GITHUB (once, in the sentry folder):
  git init
  git add .
  git commit -m "SENTRY initial commit"
  git branch -M main
  git remote add origin https://github.com/YOURNAME/sentry.git
  git push -u origin main

DAILY:
  cd C:\Users\YOU\Documents\sentry
  claude                         # build/fix with Claude Code
  ...ask, test...
  git add . && git commit -m "msg" && git push      # save to GitHub

RUN SENTRY:
  double-click START_SENTRY.bat        (or)   python -m sentry_backend.server
  open http://localhost:8000

UPDATE:
  git pull                       # latest code
  claude update                  # update Claude Code
  pip install -r requirements.txt    # after dependency changes  (venv active)

UNDO:
  git restore .                  # discard unsaved edits
  (ask Claude Code: "revert the last commit")
```

---

When your RTL-SDR or other hardware arrives, the fastest path is: plug it in, open
Claude Code in the project, and say *"my [device] is connected — help me get it
working and tune it."* It knows the project from CLAUDE.md and will pick up right
where we left off.
