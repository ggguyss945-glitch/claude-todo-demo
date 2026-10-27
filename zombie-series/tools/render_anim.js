// Render an animation to JPEG frames with N parallel pages.
// node tools/render_anim.js <timeline.json> <out_dir> [fps=30] [workers=4] [only times: t1,t2,...|-] [scale=1] [key=value ...]
//   scale renders the 1920x1080 stage at a higher pixel density (4/3 -> 2560x1440).
//   page=engine/anim.html  which page draws the frames (it must expose renderAt and may install a baker)
//   frames=a:b             render only frame indices a..b-1 (chunked renders); progress.json counts this range
//   bake=0                 draw static layers inline instead of baking them into bitmaps
const { chromium } = require('playwright');
const path = require('path'), http = require('http'), fs = require('fs'), crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const pos = process.argv.slice(2).filter((a) => !/^[a-z]+=/.test(a));
const opt = Object.fromEntries(process.argv.slice(2).filter((a) => /^[a-z]+=/.test(a)).map((a) => a.split(/=(.*)/s).slice(0, 2)));
const [tlPath, outDir, fpsArg, wArg, onlyRaw, scaleArg] = pos;
const fps = +(fpsArg || 30), workers = +(wArg || 4), scale = +(scaleArg || 1);
const onlyArg = onlyRaw && onlyRaw !== '-' ? onlyRaw : '';
const pageUrl = '/' + (opt.page || 'engine/anim.html');
const cacheDir = path.resolve(outDir, '..', 'bake_cache');
fs.mkdirSync(outDir, { recursive: true }); fs.mkdirSync(cacheDir, { recursive: true });
const types = { '.js': 'text/javascript', '.html': 'text/html', '.png': 'image/png', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const p = u === '/timeline.json' ? path.resolve(tlPath) : u.startsWith('/cache/') ? path.join(cacheDir, path.basename(u)) : path.join(root, u);
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'max-age=86400' }); res.end(data);
  });
});
(async () => {
  await new Promise((r) => server.listen(0, r));
  const port = server.address().port;
  const T = JSON.parse(fs.readFileSync(tlPath));
  const all = Math.round(T.dur * fps);
  const [f0, f1] = (opt.frames || `0:${all}`).split(':').map(Number);
  const times = onlyArg ? onlyArg.split(',').map(Number) : Array.from({ length: Math.min(f1, all) - f0 }, (_, i) => (f0 + i) / fps);
  const browser = await chromium.launch();
  let next = 0, done = 0, last = ''; const t0 = Date.now();
  // progress.json lets a watcher (the live render page) follow the job without parsing logs.
  const progress = (finished) => fs.writeFileSync(path.join(outDir, 'progress.json'), JSON.stringify({
    done, total: times.length, fps, last, finished, first: f0, started_at: new Date(t0).toISOString(),
    updated_at: new Date().toISOString(), rate: +(done / Math.max(0.001, (Date.now() - t0) / 1000)).toFixed(2) }));
  progress(false);

  // ---- layer baking: one shared page rasterizes each static layer once; every worker then uses the PNG ----
  const pages = [], baked = new Map(); let bakeQueue = Promise.resolve(), bakePage = null;
  const over = 1.25;   // headroom for slow camera pushes
  function bake(job, defs) {
    if (baked.has(job.key)) return baked.get(job.key);
    const pr = (bakeQueue = bakeQueue.then(async () => {
      const hash = crypto.createHash('sha1').update(defs + job.svg + JSON.stringify(job.box) + scale).digest('hex').slice(0, 20);
      const file = path.join(cacheDir, hash + '.png'), url = `/cache/${hash}.png`;
      if (!fs.existsSync(file)) {
        if (!bakePage) {
          bakePage = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale * over });
          await bakePage.goto(`http://127.0.0.1:${port}/engine/bake.html`);
          await bakePage.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
        }
        await bakePage.setViewportSize({ width: Math.ceil(job.box.w), height: Math.ceil(job.box.h) });
        await bakePage.evaluate(([d, s, b]) => window.paint(d, s, b), [defs, job.svg, job.box]);
        await bakePage.locator('#stage').screenshot({ path: file, omitBackground: true, type: 'png' });
      }
      await Promise.all(pages.map((p) => p.evaluate(([k, u]) => window.bakeDone && window.bakeDone(k, u), [job.key, url]).catch(() => {})));
      return url;
    }));
    baked.set(job.key, pr);
    return pr;
  }

  async function worker() {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
    page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
    await page.goto(`http://127.0.0.1:${port}${pageUrl}?timeline=/timeline.json${opt.bake === '0' ? '&bake=0' : ''}`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    pages.push(page);
    for (const [k, pr] of baked) pr.then((u) => page.evaluate(([kk, uu]) => window.bakeDone && window.bakeDone(kk, uu), [k, u]).catch(() => {}));
    const defs = await page.evaluate(() => window.bakeDefs || '');
    while (next < times.length) {
      const i = next++, t = times[i];
      await page.evaluate((t) => window.renderAt(t), t);
      const name = onlyArg ? `t_${t.toFixed(2)}.jpg` : `f_${String(f0 + i).padStart(5, '0')}.jpg`;
      await page.locator('#stage').screenshot({ path: path.join(outDir, name), type: 'jpeg', quality: 95 });
      const jobs = await page.evaluate(() => (window.takeBakeJobs ? window.takeBakeJobs() : []));
      for (const j of jobs) bake(j, defs);
      last = name;
      if (++done % 30 === 0) progress(false);
      if (done % 150 === 0) console.log(`${done}/${times.length} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
    }
    pages.splice(pages.indexOf(page), 1);
    await page.close();
  }
  await Promise.all(Array.from({ length: workers }, worker));
  await bakeQueue;
  progress(true);
  console.log(`done ${done} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s, ${baked.size} layers baked`);
  await browser.close(); server.close();
})();
