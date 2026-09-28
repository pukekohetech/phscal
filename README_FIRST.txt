PHS Calendar v7.4 - Reader Layout Fix

Replace only these two files in the ROOT of the GitHub repo:
  index.html
  service-worker.js

What this fixes:
- Article content can no longer expand underneath the Updates/RSS column.
- Long links, wide tables, media and long text are constrained to the reader pane.
- Open original stays visible; the toolbar reflows before controls can be pushed off-screen.
- Below 980 px wide, the article switches to full-width reader mode and the feed list is hidden until Back is pressed.
- Reader/table scrollbars remain visually hidden while mouse/touch scrolling still works.

After upload, use Ctrl+F5 once.
No feed, standards or workflow files need changing for this patch.
