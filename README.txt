PHS Calendar Whiteboard - Weather + reliability updates v4

Open index.html through a local web server or a hosted site for live calendar and live weather updates.

Recommended local setup
1. Open a terminal/command prompt in this folder.
2. Run:
   python3 -m http.server 8080
3. Open:
   http://localhost:8080

On Windows, if python3 is not recognised, try:
   py -m http.server 8080

Main changes in v4:
- Service worker install is more fault-tolerant, so one missing icon will not break the whole offline install.
- Service worker registration errors now show as a visible notice instead of being silently hidden.
- Calendar and weather requests now use a timeout so weak Wi-Fi does not leave refreshes hanging.
- Notices and errors use ARIA live regions for better accessibility.
- The header now shows a simple last-updated status for calendar and weather.
- Settings saving is wrapped in a safe try/catch to avoid crashing if browser storage is full.
- The parser explicitly recognises Pacific/Auckland calendar times from the PHS feed and keeps them as school wall-clock times.

Existing v3 improvements kept:
- Teacher-friendly wording: online calendar, imported calendar file, saved backup, linked calendar file.
- Weather chips show plain labels such as Fine, Rain likely, Showers possible, Windy, or Cold.
- Weather chips hide automatically when a date is outside the available forecast range.
- School timetable uses simple editable rows instead of visible JSON.
- Advanced troubleshooting keeps backup timetable data hidden under More calendar options.

If opening by double-clicking index.html, browser security may block the online calendar. In that case, use Settings > School calendar > Import selected file and choose PHS Calendar.ics.

Future larger improvements to consider:
- Split index.html into separate CSS and JS files.
- Move large saved calendar backups from localStorage to IndexedDB.
- Add full RECURRENCE-ID support with a dedicated iCalendar parser such as ical.js.
