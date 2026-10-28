// Render one piece of channel art to PNG: node tools/render_still.js <item|mod:path.js> <out.png> [scale=2]
//   item draws ITEMS[item] from engine/brand/brand.js; mod:brand/v2/x.js draws that module's default export.
// The page sizes itself from the item; scale supersamples it (2 = a 1920x1080 design comes out 3840x2160).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const [item, out, scaleArg] = process.argv.slice(2);
const types = { '.js': 'text/javascript', '.html': 'text/html' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (err, data) => { if (err) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(data); });
});
(async () => {
  await new Promise((r) => server.listen(0, r));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 4000, height: 2400 }, deviceScaleFactor: +(scaleArg || 2) });
  page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
  const q = item.startsWith('mod:') ? `brand2.html?mod=${encodeURIComponent(item.slice(4))}` : `brand.html?item=${item}`;
  await page.goto(`http://127.0.0.1:${server.address().port}/engine/${q}`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await page.locator('#stage').screenshot({ path: out, type: 'png' });
  await browser.close(); server.close();
  console.log('wrote', out);
})();
