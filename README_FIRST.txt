PHS CALENDAR v6.2 - OFFICIAL UPDATES PATCH
==========================================

WHAT THIS ADDS
- Minimal Official Updates bell in the calendar header.
- Updates drawer for NZQA, NCEA, Ministry of Education and WorkSafe.
- Filters for Technology, Assessment, Curriculum, Safety and Standards Watch.
- Standards Watch for 92012, 92014, 92015 and 29655.
- Compact Term / Week indicator derived from the school calendar.
- Network-first caching for updates.json so fresh updates appear without breaking offline use.
- GitHub Actions checkout upgraded to v7 to avoid the old Node 20 warning.

IMPORTANT
This patch deliberately does NOT contain PHS Calendar.ics.
Do not delete your live PHS Calendar.ics. Your existing KAMAR updater continues to maintain it.
No new GitHub secret is required. Keep your existing KAMAR_ICS_URL secret unchanged.

UPLOAD / REPLACE THESE FILES IN THE REPOSITORY ROOT
- index.html
- service-worker.js
- updates.json
- update_official_updates.py
- phs-shield.webp (safe to replace; it is the existing shield)

GITHUB WORKFLOW FILES
These must be at these exact paths:
- .github/workflows/update-official-updates.yml
- .github/workflows/update-calendar.yml

The update-calendar workflow is your existing KAMAR updater with actions/checkout updated to v7.
The new update-official-updates workflow needs no secret.

IF THE .github FOLDER IS AWKWARD TO UPLOAD
1. In GitHub choose Add file > Create new file.
2. Enter this exact filename:
   .github/workflows/update-official-updates.yml
3. Paste the contents of PASTE_THIS_update-official-updates.yml from this patch.
4. Commit the file.

FIRST TEST
1. Open GitHub > Actions.
2. Open "Update Official Education Feeds".
3. Choose Run workflow.
4. A green run means the official-source updater is working.
5. If new information was found, GitHub will create a commit called:
   Update official education feeds
6. Open the calendar and use the bell icon to see the updates.

AUTOMATIC SCHEDULES
- KAMAR calendar: every 15 minutes (existing workflow).
- Official education/safety updates: every 6 hours.

OFFICIAL SOURCES CHECKED
- NZQA Assessment Matters
- NCEA What's New
- Ministry of Education Te Poutahu Curriculum Centre school updates
- WorkSafe New Zealand news and media, filtered for relevant safety/technology items

STANDARDS WATCHED
- AS 92012
- AS 92014
- AS 92015
- US 29655

NOTES
- The app keeps the main calendar uncluttered. Updates live behind the bell.
- If one official website is temporarily unavailable, existing data is retained.
- If all official sources fail, the GitHub Action fails visibly rather than pretending the refresh succeeded.
