// Render the animation to JPEG frames with N parallel pages.
// node tools/render_anim.js <timeline.json> <out_dir> [fps=30] [workers=4] [only times: t1,t2,...]
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const [tlPath, outDir, fpsArg, wArg, onlyArg] = process.argv.slice(2);
const fps = +(fpsArg || 30), workers = +(wArg || 4);
fs.mkdirSync(outDir, { recursive: true });
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const p = u === '/timeline.json' ? path.resolve(tlPath) : path.join(root, u);
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/json' }); res.end(data);
  });
});
(async () => {
  await new Promise((r) => server.listen(0, r));
  const port = server.address().port;
  const T = JSON.parse(fs.readFileSync(tlPath));
  const times = onlyArg ? onlyArg.split(',').map(Number) : Array.from({ length: Math.round(T.dur * fps) }, (_, i) => i / fps);
  const browser = await chromium.launch();
  let next = 0, done = 0; const t0 = Date.now();
  async function worker() {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
    await page.goto(`http://127.0.0.1:${port}/engine/anim.html?timeline=/timeline.json`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
    while (next < times.length) {
      const i = next++, t = times[i];
      await page.evaluate((t) => window.renderAt(t), t);
      const name = onlyArg ? `t_${t.toFixed(2)}.jpg` : `f_${String(i).padStart(5, '0')}.jpg`;
      await page.locator('#stage').screenshot({ path: path.join(outDir, name), type: 'jpeg', quality: 93 });
      if (++done % 150 === 0) console.log(`${done}/${times.length} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
    }
    await page.close();
  }
  await Promise.all(Array.from({ length: workers }, worker));
  console.log(`done ${done} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  await browser.close(); server.close();
})();
