PHS CALENDAR v6.3 - CONFIGURABLE STANDARDS WATCH + NEWS TICKER

WHAT THIS PATCH ADDS
- Editable/shared NZQA Standards Watch using standards-watch.json
- Rolling official-news ticker along the bottom of the calendar
- Toggle to show/hide the ticker in Settings
- NCEA on TKI RSS as a secondary Technology/assessment source
- Existing NZQA, NCEA Education, Ministry and WorkSafe sources remain
- Editing standards-watch.json triggers the official-updates workflow immediately

UPLOAD / REPLACE
Upload these files to the matching locations in your phscal repo:
- index.html
- service-worker.js
- update_official_updates.py
- updates.json
- standards-watch.json
- phs-shield.webp
- .github/workflows/update-calendar.yml
- .github/workflows/update-official-updates.yml

IMPORTANT
Do NOT delete PHS Calendar.ics. It is still maintained by the KAMAR updater.

HOW TO CHANGE WATCHED STANDARDS
Option 1 - from the calendar Settings panel:
1. Enter the standard numbers you want, comma-separated.
2. Press 'Copy list + open GitHub'.
3. Replace the contents of standards-watch.json with the copied JSON.
4. Commit the change.
The GitHub Action runs automatically and updates the Standards Watch results.

Option 2 - edit standards-watch.json directly in GitHub.
Example:
{
  "standards": ["92012", "92014", "92015", "29655"]
}

ROLLING NEWS
The bottom banner uses the newest/highest-priority official updates, favouring Standards Watch, Technology, Assessment and Safety. Hover or focus it to pause. Users who prefer reduced motion get a non-animated horizontal list.

WORKFLOWS
- Update PHS Calendar: KAMAR calendar sync every 15 minutes.
- Update Official Education Feeds: official update refresh every 6 hours, plus immediately when standards-watch.json changes.

The existing KAMAR secret KAMAR_ICS_URL is still required only by the calendar workflow. No new secret is needed for official updates.
