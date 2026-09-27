PHS CALENDAR v6.5 - LARGE LIVE NEWS BAND

WHAT THIS PATCH CHANGES
- Replaces the thin sideways ticker with a large featured-news band across the bottom of the screen.
- The band uses roughly one sixth of the screen height on desktop.
- One official update is featured at a time with source, category, date, headline and short summary.
- Updates advance automatically every 9 seconds with a smooth fade/slide transition.
- A gold progress line shows when the next story will appear.
- Previous/next controls allow manual browsing.
- Hovering or focusing the band pauses auto-advance; leaving it resumes.
- Clicking a story opens it in the existing in-app RSS/article reader.
- The ticker itself has no visible scrollbar.
- The main page scrollbar is visually hidden while wheel/touch scrolling still works if needed.
- Settings and the mobile menu have been moved above the larger news band.

STILL INCLUDED FROM v6.4
- In-app split RSS/article reader.
- Live iframe view plus Reader fallback for sites that block embedding.
- Editable RSS/Atom feeds in Settings.
- Editable NZQA Standards Watch.
- NZQA, NCEA Education, Ministry, WorkSafe and configured TKI feeds.

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

AFTER UPLOADING
1. Hard refresh the calendar once (Ctrl+F5).
2. If the old ticker is still cached, close/reopen the installed PWA or refresh again after a few seconds.
3. The larger band should automatically rotate through the highest-priority official updates.
