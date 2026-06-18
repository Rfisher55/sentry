# How to add this documentation to your repo and push it to GitHub

You have the full docs set. Here's how to get it into your project and onto
GitHub so anyone can follow it.

## Step 1 — Put the docs in your project
Copy this entire `sentry-docs` folder into your SENTRY project folder, and rename
it `docs` (replacing or merging with the existing docs folder).

On Windows, you can just drag the folder in via File Explorer, or in PowerShell:
```
Copy-Item -Path "<download-folder>\sentry-docs\*" -Destination "<repo-folder>\docs\" -Recurse -Force
```
(Adjust paths to where you downloaded the docs and where your repo is.)

## Step 2 — Tell Claude Code to organize and push
Open Claude Code in your project folder and paste:

```
I've added a full documentation set to the docs/ folder (files 00_START_HERE through 07, plus HOW_TO_PUBLISH). Please:
1. Make sure they're all in docs/ and well-organized.
2. Update the main README.md so it points new people to docs/00_START_HERE.md as the entry point, with a one-paragraph overview of what SENTRY is and the phased build journey (laptop -> full laptop build-out -> Raspberry Pi Pelican case).
3. Make sure nothing personal to me is in the repo or docs (my home IP, my real device names, my email) - generalize anything personal.
4. Commit everything with a clear message and push to GitHub. Confirm local and remote main are in sync.
```

## Step 3 — (Optional) Make it public so anyone can use it
Only after Step 2 and a privacy check:
1. On GitHub: your repo -> Settings -> scroll to bottom -> Change visibility -> Public.
2. Before that, in Claude Code: "scan the whole repo and git history for any
   personal info (my IP, device names, email) and remove or generalize it before I
   go public."

## Step 4 — (Optional) A live demo page
You can turn on GitHub Pages (Settings -> Pages -> from main, /ui) to host the
interface as a public demo link. Note: the hosted page shows DEMO data only - real
detection always runs locally on the machine with the sensors. The link is for
showing the interface, not live detection.

## Going forward
After any work session, keep GitHub current:
```
Commit and push all changes to GitHub, then confirm local and remote main are in sync.
```
