No interactive browser is available in this run. Visit the product like this:

1. Fetch every page you would open over HTTP with curl, for example `curl -s http://127.0.0.1:8765/` and `curl -s http://127.0.0.1:8765/pricing.html`. Follow the links a real visitor in your situation would click. Read the CSS (`/styles.css`) when you need to judge size, contrast or layout.
2. Look at the rendered pages: screenshots of every page are in <run>/site-shots/. Files named desktop-<page>.png are 1280 px wide, phone-<page>.png are 390 px wide (pages: index, pricing, signup, privacy). Open the ones that match your device with the Read tool.
3. Forms do not submit anywhere; describe what you would type and where you would stop.

Set "visit_method" to "http". In "evidence", describe actions generically ("opened /pricing at phone width", "read the FAQ") and never mention tool names, file names or local folders.
