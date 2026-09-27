PHS Calendar v7.1 - Rich Links Patch

Replace these three files in the ROOT of your GitHub repository:
  index.html
  update_official_updates.py
  service-worker.js

Do not move update_official_updates.py into .github/workflows.
Your existing .github/workflows/update-official-updates.yml should stay where it is.

After committing the three files:
1. GitHub -> Actions -> Update Official Education Feeds -> Run workflow.
2. Wait for a green tick.
3. Open updates.json and search for "readerHtml". You should now see rich HTML entries containing <a href=...> links.
4. Hard refresh the calendar (Ctrl+F5).

Example expected saved content:
<a href="https://...pdf" target="_blank" rel="noopener noreferrer">Download the updated 2026 timetable [PDF, 163 KB]</a>
