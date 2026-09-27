PHS CALENDAR v6.4 - RSS READER + EDITABLE FEEDS

WHAT THIS PATCH ADDS
- Clicking an official update now opens it inside the calendar in a split reader.
- Desktop: update list stays on the right and the selected page opens on the left.
- Mobile: selecting an update switches to the reader, with a Back button.
- Live page uses an iframe. Some websites block iframe embedding; use Reader mode or Open original when that happens.
- Reader mode shows text captured by the automatic updater, so useful content remains visible even when iframe embedding is blocked.
- RSS/Atom feeds can now be added, edited, disabled or removed from Settings.
- RSS feeds are stored in rss-feeds.json. Publishing changes triggers the updater automatically.
- The rolling bottom ticker now opens articles in the in-app reader instead of immediately leaving the calendar.

DEFAULT RSS SOURCES
- NCEA on TKI
- Technology Online - What's new
- Technology Online - News
- Technology Online - Teaching snapshots

UPLOAD / REPLACE
Upload these files to the repository root:
- index.html
- service-worker.js
- update_official_updates.py
- updates.json
- standards-watch.json
- rss-feeds.json
- phs-shield.webp

Also upload/update:
.github/workflows/update-official-updates.yml
.github/workflows/update-calendar.yml

IMPORTANT
Do NOT replace or delete PHS Calendar.ics. The existing KAMAR workflow continues to manage it.

USING THE RSS EDITOR
1. Open Calendar Settings > Official updates > RSS feeds.
2. Edit existing rows or press Add RSS feed.
3. Give the feed a name, URL and optional comma-separated tags.
4. Turn Tech only on if you want the updater to keep only Technology-relevant entries from a broad feed.
5. Press Publish RSS feeds.
6. The calendar copies rss-feeds.json and opens the GitHub editor.
7. Paste, commit, and the Update Official Education Feeds workflow runs automatically.

VERIFY
- GitHub Actions > Update Official Education Feeds should finish with a green tick.
- Hard refresh the calendar once after uploading this patch.
