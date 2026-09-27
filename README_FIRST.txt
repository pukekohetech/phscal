PHS CALENDAR v6.6 - READER FIRST FIX

WHY THIS VERSION
Many NZQA, Ministry, WorkSafe, NCEA and TKI pages block iframe embedding using
browser security headers. That is controlled by the source website and cannot
be overridden by the calendar page.

WHAT CHANGED
- Reader is now the default when an update is opened.
- Live page is optional: use "Try live page" only when a site allows embedding.
- RSS/Atom items now attempt to save a fuller text snapshot from the linked
  article during the GitHub update job.
- If the linked page cannot be fetched, the feed description remains as the
  fallback Reader content.
- Reader scrolling still works but its visual scrollbar is hidden.
- Service worker cache bumped to v22-reader-first.

UPLOAD / REPLACE
- index.html
- service-worker.js
- update_official_updates.py

You may upload the whole patch folder if easier. It deliberately does NOT
contain PHS Calendar.ics, so the working KAMAR calendar is not overwritten.

AFTER UPLOAD
1. GitHub -> Actions -> Update Official Education Feeds -> Run workflow.
2. Wait for a green tick so updates.json is rebuilt with article snapshots.
3. Hard refresh the calendar (Ctrl+F5).
