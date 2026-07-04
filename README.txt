PHS Calendar Whiteboard - simplified settings revision

Files:
- index.html: updated calendar app with daily weather chips and a simpler settings layout.
- service-worker.js: updated cache name and offline shell caching.
- manifest.webmanifest: installable PWA manifest.
- PHS Calendar.ics: copy of the supplied calendar file for local import if needed.

Simple use:
1. Open index.html through a local server or HTTPS for live calendar/weather fetching.
2. Open Settings -> School calendar.
3. Click Use school live calendar for the normal setup.
4. If the live calendar is blocked because the app is opened as a local file, choose PHS Calendar.ics and click Import selected file.
5. Use Settings -> Daily weather to show/hide weather or change the location.

Notes:
- Default weather location is Pukekohe, New Zealand.
- Weather uses the Open-Meteo forecast/geocoding APIs in the browser.
- Advanced calendar options are hidden under More calendar options.
