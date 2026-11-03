// Render one UI/set still to PNG: node tools/render_ui_still.js <module.js> <out.png> [scale=2] [arg]
//   <module.js> is a path relative to engine/ whose default export returns { w, h, svg } (may be async).
//   [arg] is passed to the module's default export as a string (e.g. a variant name).
// The page sizes itself from the module; scale supersamples it (2 = a 1920x1080 design comes out 3840x2160).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const [mod, out, scaleArg, arg] = process.argv.slice(2);
if (!mod || !out) { console.error('usage: node tools/render_ui_still.js <module.js> <out.png> [scale] [arg]'); process.exit(1); }
const types = { '.js': 'text/javascript', '.html': 'text/html', '.ttf': 'font/ttf', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (err, data) => { if (err) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(data); });
});
(async () => {
  await new Promise((r) => server.listen(0, r));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: +(scaleArg || 2) });
  page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.error('console:', m.text()); });
  const q = `ui_still.html?mod=${encodeURIComponent(mod)}${arg ? '&arg=' + encodeURIComponent(arg) : ''}`;
  await page.goto(`http://127.0.0.1:${server.address().port}/engine/${q}`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  const err = await page.evaluate(() => window.__err);
  if (err) { console.error('RENDER ERROR', err); await browser.close(); server.close(); process.exit(2); }
  const box = await page.evaluate(() => { const r = document.getElementById('stage').getBoundingClientRect(); return { width: Math.ceil(r.width), height: Math.ceil(r.height) }; });
  if (box.width > 1920 || box.height > 1080) { await page.setViewportSize(box); await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))); }
  const fonts = await page.evaluate(() => window.__fonts);
  if (fonts && fonts.length) console.error('fonts missing:', fonts.join(', '));
  const ext = path.extname(out).toLowerCase();
  await page.locator('#stage').screenshot({ path: out, type: ext === '.jpg' || ext === '.jpeg' ? 'jpeg' : 'png', ...(ext === '.jpg' || ext === '.jpeg' ? { quality: 92 } : {}) });
  await browser.close(); server.close();
  console.log('wrote', out);
})();
