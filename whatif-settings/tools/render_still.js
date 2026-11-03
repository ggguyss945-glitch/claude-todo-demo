// Render one still to PNG/JPEG: node tools/render_still.js <module under engine/> <out.png|.jpg> [scale=2] [k=v ...]
//   e.g. node tools/render_still.js sheets/cast_lineup.js renders/cast_lineup.png 2
// The module's default export returns { w, h, svg } in design units (1920x1080); scale supersamples it
// (2 = a 1920x1080 design comes out 3840x2160). Extra k=v pairs are passed to the module as query params.
const { chromium } = require(require.resolve('playwright', { paths: [process.cwd(), '/opt/node-tools/node_modules'] }));
const path = require('path'), http = require('http'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const [mod, out, scaleArg, ...kv] = process.argv.slice(2);
if (!mod || !out) { console.error('usage: render_still.js <module> <out> [scale] [k=v...]'); process.exit(1); }
const types = { '.js': 'text/javascript', '.html': 'text/html', '.ttf': 'font/ttf', '.woff2': 'font/woff2', '.png': 'image/png', '.svg': 'image/svg+xml' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root)) { res.writeHead(403); return res.end(); }
  fs.readFile(p, (err, data) => { if (err) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' }); res.end(data); });
});
(async () => {
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const browser = await chromium.launch();
  const scale = +(scaleArg || 2);
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
  page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') console.error('console:', m.text()); });
  const qs = new URLSearchParams({ mod, ...Object.fromEntries(kv.map((s) => s.split('='))) }).toString();
  await page.goto(`http://127.0.0.1:${server.address().port}/engine/still.html?${qs}`);
  await page.waitForFunction(() => window.__ready === true || window.__error, null, { timeout: 120000 });
  const err = await page.evaluate(() => window.__error);
  if (err) { console.error('MODULE ERROR\n' + err); await browser.close(); server.close(); process.exit(2); }
  const jpg = /\.jpe?g$/i.test(out);
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  await page.locator('#stage').screenshot({ path: out, type: jpg ? 'jpeg' : 'png', ...(jpg ? { quality: 92 } : {}) });
  await browser.close(); server.close();
  console.log('wrote', out, (fs.statSync(out).size / 1024).toFixed(0) + ' KB');
})();
