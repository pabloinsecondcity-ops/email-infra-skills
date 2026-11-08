---
name: smartscout-scraping
description: >-
  Use when Pablo needs full brand or company tables from SmartScout
  (app.smartscout.com) and Export is locked: run the browser-console AG-Grid
  script to scroll-capture up to 1,000 rows into a CSV.
---
# SmartScout Scraping (no Export plan)

Trigger: "scrape SmartScout", "export SmartScout brands", "SmartScout company names missing", or any request to pull SmartScout data without Enterprise-plan API/Export access.

Built and confirmed 2026-08-05 against `app.smartscout.com/app/brands`.

---

## Why Instant Data Scraper doesn't work here

SmartScout's tables run on AG-Grid (Angular). The **Brand Name column is frozen/pinned left** in its own DOM container (`.ag-pinned-left-cols-container`), separate from the rest of the row (`.ag-center-cols-container`). Generic table scrapers grab one repeating row container and never see the pinned one, so the brand name comes through blank or as the "Dominant Seller" field (often "Amazon.com").

Rows are also virtualized (only rows near the viewport exist), so naive infinite-scroll capture gives blank or duplicate rows.

The fix: read both containers by their shared `row-id` attribute, and scroll with a wait between steps so each batch renders before capture.

---

## Step 1. Get to the right view

Open the SmartScout page/filter you want (e.g. `app.smartscout.com/app/brands` with filters). Confirm the table shows real data first.

## Step 2. Open the console

Chrome Mac: **Cmd+Option+J**. If the console input won't focus (narrow-panel issue seen 2026-08-05): DevTools three-dot menu, "Undock into separate window", click into the console again.

## Step 3. Paste and run

```js
(async function () {
  const COLUMNS = [
    ['double-brand-name', 'Brand Name', 'Brand Score'],
    ['double-brand-categories', 'Main Category', 'Primary Subcategory'],
    ['double-brand-revenue', 'Est Monthly Revenue', 'Trailing 12 Months'],
    ['double-brand-price-volume', 'Avg Price', 'Avg Volume'],
    ['double-brand-seller-counts', 'Avg FBA Sellers', 'Avg Sellers'],
    ['double-brand-dominant-seller', 'Dominant Seller', 'Country / Sales %'],
    ['double-brand-sales-amazon-isr', 'Est Monthly Sales', 'Amazon In-Stock Rate'],
    ['double-brand-reviews', 'Avg Rating', 'Reviews'],
    ['double-brand-growth', '1 Month Growth', 'Growth (secondary)'],
  ];

  const viewport = document.querySelector('.ag-body-viewport');
  const centerContainer = document.querySelector('.ag-center-cols-container');
  if (!viewport || !centerContainer) {
    console.error('Could not find the grid on this page. Make sure you are on the SmartScout table view.');
    return;
  }

  const results = new Map();

  function harvest() {
    document.querySelectorAll('[role="row"][row-id]').forEach((rowEl) => {
      const rowId = rowEl.getAttribute('row-id');
      if (rowId === null) return;
      if (!results.has(rowId)) results.set(rowId, {});
      const rowData = results.get(rowId);
      rowEl.querySelectorAll('[col-id]').forEach((cell) => {
        const colId = cell.getAttribute('col-id');
        const primaryEl = cell.querySelector('.primary-row span');
        const secondaryEls = cell.querySelectorAll('.secondary-row span');
        const primary = primaryEl ? primaryEl.textContent.trim() : '';
        const secondary = Array.from(secondaryEls).map((s) => s.textContent.trim()).filter(Boolean).join(' | ');
        if (primary || secondary) rowData[colId] = { primary, secondary };
      });
    });
  }

  const rowHeight = 65;
  const maxScroll = centerContainer.scrollHeight - viewport.clientHeight;
  const step = rowHeight * 6;

  harvest();
  let pos = 0;
  let iterations = 0;
  while (pos < maxScroll && iterations < 400) {
    pos = Math.min(pos + step, maxScroll);
    viewport.scrollTop = pos;
    await new Promise((r) => setTimeout(r, 350));
    harvest();
    iterations++;
    if (iterations % 10 === 0) console.log(`Scrolled ${pos}/${maxScroll}px, ${results.size} unique rows so far`);
  }
  viewport.scrollTop = maxScroll;
  await new Promise((r) => setTimeout(r, 400));
  harvest();

  console.log(`Done scrolling. Captured ${results.size} rows.`);

  function csvEscape(v) {
    v = v == null ? '' : String(v);
    return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }

  const headers = [];
  COLUMNS.forEach(([, p, s]) => {
    headers.push(p);
    headers.push(s);
  });

  const rowIds = Array.from(results.keys()).sort((a, b) => Number(a) - Number(b));
  const lines = [headers.map(csvEscape).join(',')];
  rowIds.forEach((id) => {
    const rowData = results.get(id);
    const line = [];
    COLUMNS.forEach(([colId]) => {
      const cell = rowData[colId] || { primary: '', secondary: '' };
      line.push(cell.primary, cell.secondary);
    });
    lines.push(line.map(csvEscape).join(','));
  });

  const csv = lines.join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `smartscout_brands_${Date.now()}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  console.log(`CSV downloaded with ${rowIds.length} rows.`);
})();
```

Expect ~15-30 seconds of auto-scrolling with progress logs, then `Done scrolling. Captured N rows.` and a CSV in Downloads, no save dialog.

## Step 4. Repeat per page

Each page holds up to 1,000 rows (footer like `1 to 1,000 of 603,265` / `Page 1 of 604`). Click the ">" next-page arrow, then run the script again. Each run downloads its own timestamped CSV.

## Stopping mid-run

Reload the page. Nothing is saved until the last step, so there's never a partial file.

## Adapting to a different table (Sellers, Products, etc.)

`COLUMNS` maps AG-Grid `col-id` values to header names. To re-derive: save the page ("Webpage, Complete"), search the HTML for `col-id="` to list columns, search for `header-text primary-text` near each to get its label, update `COLUMNS`. The rest of the script stays the same.

---

## Environment adaptation (Grok Bot box)

Added on import from Claude Code (2026-10-22).

- Needs a signed-in SmartScout session. On the box, use the box desktop browser (see `box-desktop` and `sign-in`); Pablo signs in himself.
- On the Linux box the console shortcut is Ctrl+Shift+J. Downloads land in the box's Downloads folder; move CSVs to `/workspace/`.
