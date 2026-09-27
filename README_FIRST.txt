PHS CALENDAR v6.9 - CORRECT REPOSITORY STRUCTURE
=================================================

This package fixes the GitHub folder-layout problem and includes the v6.8
reliable news reader/ticker build.

CORRECT LAYOUT
--------------
.github/
  workflows/
    update-calendar.yml
    update-official-updates.yml
icons/
  icon-192.png
  icon-512.png
  maskable-512.png
index.html
manifest.webmanifest
phs-shield.webp
rss-feeds.json
service-worker.js
standards-watch.json
update_official_updates.py
updates.json

IMPORTANT
---------
PHS Calendar.ics is deliberately NOT included.
Your working KAMAR workflow owns that file and will keep updating it.

The Python file update_official_updates.py belongs in the REPOSITORY ROOT.
It must NOT be inside .github/workflows/.

The two YAML files belong ONLY in .github/workflows/.

UPLOAD
------
1. Extract this ZIP on your computer.
2. Upload/replace the files in your phscal repository, preserving the folders.
3. Make sure .github/workflows contains BOTH YAML files.
4. Do not delete or replace PHS Calendar.ics.

OLD MISPLACED FILES YOU CAN DELETE FROM GITHUB
----------------------------------------------
These are not needed once this package is installed:
- /update-calendar.yml
- /update-official-updates.yml
- /PASTE_THIS_update-official-updates.yml
- /workflows
- /.github/workflows/update_official_updates.py   (if still present there)

KEEP this root file:
- /update_official_updates.py

CHECK AFTER UPLOAD
------------------
GitHub > Actions should show BOTH:
- Update PHS Calendar
- Update Official Education Feeds

Run "Update Official Education Feeds" once manually.
It should show green steps for:
- Check out repository
- Build official updates
- Commit changes when needed

The official-feed workflow also runs every 6 hours and automatically runs
when rss-feeds.json, standards-watch.json, or update_official_updates.py changes.

The KAMAR workflow remains every 15 minutes.

After the workflows are green, hard-refresh the calendar with Ctrl+F5.
