PHS CALENDAR v6.8 - RELIABLE NEWS READER

Replace these files in the GitHub repo:
- index.html
- service-worker.js
- update_official_updates.py

Do NOT replace:
- PHS Calendar.ics
- rss-feeds.json
- standards-watch.json

What changed
1. News band advances every 5 seconds even if the mouse is resting over it.
2. Reduced-motion settings no longer stop the feed rotation; they only reduce animation.
3. Ticker stories rotate round-robin across different feed sources instead of allowing one busy feed to dominate.
4. Clicking a story opens the saved local Reader view. The app no longer attempts iframe embedding.
5. Open original remains available for the source website.
6. The updater fetches linked RSS/Atom articles and stores a fuller text snapshot in updates.json.
7. The updater now captures additional headings/list text and can fetch up to 10 linked items per configured feed.

After uploading
- Updating update_official_updates.py should automatically trigger the Update Official Education Feeds workflow if the v6.4+ workflow is installed.
- Otherwise run Actions > Update Official Education Feeds > Run workflow once.
- Wait for the green tick.
- Hard refresh the calendar with Ctrl+F5.

The KAMAR calendar updater is unchanged.
