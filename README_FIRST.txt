PHS Calendar v7.3 - News Control & Search patch

Replace these repo files:
- index.html
- service-worker.js
- update_official_updates.py
- rss-feeds.json

The workflow file is included in the correct path for reference:
.github/workflows/update-official-updates.yml
(Replace it only if yours is missing or different.)

Then run:
Actions > Update Official Education Feeds > Run workflow

What changed:
- Update/news search box.
- Newest-first / oldest-first sorting.
- Future exam/event dates are no longer treated as publication dates.
- Built-in NZQA, NCEA, Ministry and WorkSafe sources can be turned off.
- Custom RSS feeds can be disabled or removed.
- Disabled/deleted sources are purged from updates.json on the next updater run.
- Source changes hide from the list and ticker immediately in the current browser.
- It is valid to disable every news source; the workflow no longer fails just because none are enabled.

PHS Calendar.ics is intentionally NOT included.
