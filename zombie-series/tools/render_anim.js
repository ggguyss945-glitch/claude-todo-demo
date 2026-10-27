// Render the animation to JPEG frames with N parallel pages.
// node tools/render_anim.js <timeline.json> <out_dir> [fps=30] [workers=4] [only times: t1,t2,...|-] [scale=1]
// scale renders the 1920x1080 stage at a higher pixel density (4/3 -> 2560x1440).
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs');
const root = path.resolve(__dirname, '..');
const [tlPath, outDir, fpsArg, wArg, onlyRaw, scaleArg] = process.argv.slice(2);
const fps = +(fpsArg || 30), workers = +(wArg || 4), scale = +(scaleArg || 1);
const onlyArg = onlyRaw && onlyRaw !== '-' ? onlyRaw : '';
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
  let next = 0, done = 0, last = ''; const t0 = Date.now();
  // progress.json lets a watcher (the live render page) follow the job without parsing logs.
  const progress = (finished) => fs.writeFileSync(path.join(outDir, 'progress.json'), JSON.stringify({
    done, total: times.length, fps, last, finished, started_at: new Date(t0).toISOString(),
    updated_at: new Date().toISOString(), rate: +(done / Math.max(0.001, (Date.now() - t0) / 1000)).toFixed(2) }));
  progress(false);
  async function worker() {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
    page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
    await page.goto(`http://127.0.0.1:${port}/engine/anim.html?timeline=/timeline.json`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
    while (next < times.length) {
      const i = next++, t = times[i];
      await page.evaluate((t) => window.renderAt(t), t);
      const name = onlyArg ? `t_${t.toFixed(2)}.jpg` : `f_${String(i).padStart(5, '0')}.jpg`;
      await page.locator('#stage').screenshot({ path: path.join(outDir, name), type: 'jpeg', quality: 95 });
      last = name;
      if (++done % 30 === 0) progress(false);
      if (done % 150 === 0) console.log(`${done}/${times.length} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
    }
    await page.close();
  }
  await Promise.all(Array.from({ length: workers }, worker));
  progress(true);
  console.log(`done ${done} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  await browser.close(); server.close();
})();
