const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..');
const srv = http.createServer((q, s) => { const p = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { s.writeHead(404); return s.end(); } s.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : 'text/html' }); s.end(d); }); });
srv.listen(0, async () => {
  const port = srv.address().port; const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } }); p.on('console', m => console.log('console:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto(`http://127.0.0.1:${port}/engine/gltest.html`); await p.waitForFunction(() => window.__ready, null, { timeout: 60000 });
  console.log(await p.evaluate(() => JSON.stringify(window.__info)));
  const out = process.argv[2]; const t0 = Date.now();
  for (let i = 0; i < 5; i++) { await p.evaluate((t) => window.renderAt(t), i * 0.1); await p.screenshot({ path: `${out}/f${i}.jpg`, type: 'jpeg', quality: 92 }); }
  console.log('ms/frame incl. capture', (Date.now() - t0) / 5);
  const t1 = Date.now(); for (let i = 0; i < 5; i++) await p.evaluate((t) => window.renderAt(t), i * 0.1); console.log('ms/frame render only', (Date.now() - t1) / 5);
  await b.close(); srv.close();
});
