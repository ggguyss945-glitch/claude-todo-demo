// Engine v3 renderer: timeline JSON -> H.264 video (chunked, resumable) or stills.
//
//   node tools/render.js <timeline.json> <out.mp4> [fps=60] [workers=4] [scale=1.3333333] [from=s] [to=s] [chunk=300] [k=v ...]
//   node tools/render.js <timeline.json> <out_dir> times=1.2,3.4|times.json [scale=0.5] [ext=jpg|png]   (stills)
//   node tools/render.js <timeline.json> <cues.json> cues=1                                         (SFX cue list)
//
// Video mode: Playwright workers (one browser context each) draw frames with engine/anim.html and save JPEG q95 into
// <work>/frames_<k>/; as soon as a chunk of `chunk` frames is complete it is encoded to an H.264 segment
// (libx264 crf 15, preset medium, yuv420p, high profile, -g 120, BT.709 tagged) and its frames are deleted, so disk
// use stays at about two chunks of JPEGs. Finished segments (<seg>.ok) are skipped on a re-run (resume), frames already
// on disk inside an unfinished chunk are kept. At the end the segments are joined losslessly (concat, -c copy).
// <work>/progress.json is rewritten every few frames for watchers.
//
// Options (k=v): fps workers scale from to chunk | crf=15 preset=medium pix=yuv420p (yuv420p10le -> high10)
//   quality=95 (JPEG) | work=<dir> (default <out>.parts) | keep=1 keep frames | bake=1 bake static layers (shots opt in
//   with cam.set(set, {bake: ...})), warm=1 bake every shot before frame 0 | audio=<wav> mux into the final file |
//   errors=ignore (a shot error otherwise aborts) | ext=png (stills) | page=engine/anim.html | browsers=1 (share one
//   browser process between workers; default is one per worker) | ahead=1 (chunks of frames allowed beyond the oldest
//   unencoded one)
//   Positional numbers after <out> are read as fps, workers, scale (compatible with the old render_anim.js order).
const path = require('path'), http = require('http'), fs = require('fs'), crypto = require('crypto'), { spawn } = require('child_process');
const { chromium } = require(require.resolve('playwright', { paths: [process.cwd(), '/opt/node-tools/node_modules', __dirname] }));
const root = path.resolve(__dirname, '..');

// ---------- arguments ----------
const argv = process.argv.slice(2);
const pos = argv.filter((a) => !/^[a-z_]+=/.test(a));
const opt = Object.fromEntries(argv.filter((a) => /^[a-z_]+=/.test(a)).map((a) => { const i = a.indexOf('='); return [a.slice(0, i), a.slice(i + 1)]; }));
const [tlPath, outPath] = pos;
if (!tlPath || !outPath) { console.error('usage: node tools/render.js <timeline.json> <out.mp4 | out_dir times=...> [fps=60] [workers=4] [scale=1.3333333] [from=s] [to=s] [chunk=300]'); process.exit(1); }
const fps = +(opt.fps ?? pos[2] ?? 60), workers = +(opt.workers ?? pos[3] ?? 4), scale = +(opt.scale ?? pos[4] ?? 4 / 3);
const T = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
const dur = T.dur ?? Math.max(...(T.shots || []).map((s) => s.end));
const stills = !!opt.times || !!opt.frames;
const quality = +(opt.quality ?? 95), chunkN = +(opt.chunk ?? 300);
const work = path.resolve(opt.work || (stills ? outPath : outPath.replace(/\.[a-z0-9]+$/i, '') + '.parts'));
const bakeDir = path.join(work, 'bake');
if (!opt.cues) fs.mkdirSync(work, { recursive: true });

// ---------- static server: project root + /timeline.json + /bake/* ----------
const types = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json', '.ttf': 'font/ttf', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  let p;
  if (u === '/timeline.json') p = path.resolve(tlPath);
  else if (u.startsWith('/bake/')) p = path.join(bakeDir, path.basename(u));
  else { p = path.join(root, u); if (!p.startsWith(root)) { res.writeHead(403); return res.end(); } }
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'max-age=86400' }); res.end(data);
  });
});

// ---------- helpers ----------
const fname = (f) => `f_${String(f).padStart(6, '0')}.${stills && opt.ext === 'png' ? 'png' : 'jpg'}`;
const writeAtomic = (file, buf) => { const tmp = file + '.tmp'; fs.writeFileSync(tmp, buf); fs.renameSync(tmp, file); };
const children = new Set();
function run(cmd, args, label) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { stdio: ['ignore', 'ignore', 'pipe'] });
    children.add(p);
    let err = ''; p.stderr.on('data', (d) => { err += d; });
    p.on('close', (code) => { children.delete(p); code === 0 ? resolve() : reject(new Error(`${label} failed (${code}): ${err.slice(-800)}`)); });
  });
}
// stop cleanly on Ctrl-C / kill: no orphaned encoder keeps writing a segment that the next run (resume) re-encodes
let onStop = () => {};
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) process.on(sig, () => {
  for (const c of children) { try { c.kill('SIGKILL'); } catch (e) { /* gone */ } }
  try { onStop(); } catch (e) { /* best effort */ }
  console.error(`\n${sig}: stopped; re-run the same command to resume`);
  process.exit(130);
});
function encodeArgs(dir, f0, n, out) {
  const pix = opt.pix || 'yuv420p', ten = /10/.test(pix);
  return ['-n', '10', 'ffmpeg', '-y', '-loglevel', 'error', '-framerate', String(fps), '-start_number', String(f0), '-i', path.join(dir, 'f_%06d.jpg'), '-frames:v', String(n),
    '-vf', `scale=in_color_matrix=bt601:out_color_matrix=bt709:in_range=pc:out_range=tv:flags=accurate_rnd+full_chroma_int,format=${pix}`,
    '-c:v', 'libx264', '-preset', opt.preset || 'medium', '-crf', String(opt.crf ?? 15), '-profile:v', ten ? 'high10' : 'high', '-g', String(opt.gop ?? 120), '-bf', '2',
    '-pix_fmt', pix, '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-r', String(fps), '-video_track_timescale', String(fps * 1000), out];
}

// cue export: node tools/render.js <timeline.json> <cues.json> cues=1  (no browser: frame.js runs in node; every shot
// is drawn once with ctx.cue() recording -> [{t, cue, shot, ...}] in global seconds, sorted)
async function exportCues() {
  const { pathToFileURL } = require('url');
  const F = await import(pathToFileURL(path.join(root, 'engine/anim/frame.js')).href);
  await F.loadTimeline(T, (p) => import(pathToFileURL(path.join(root, 'engine', p)).href));
  const cues = F.collectCues(T);
  fs.writeFileSync(outPath, JSON.stringify(cues, null, 1));
  console.log(`wrote ${cues.length} cues to ${outPath}${F.ERRORS.length ? ` (${F.ERRORS.length} shot errors)` : ''}`);
}

(async () => {
  if (opt.cues) return exportCues();
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const base = `http://127.0.0.1:${port}`;
  const page0 = '/' + (opt.page || 'engine/anim.html');
  const bake = opt.bake === '1';
  const launchArgs = { args: ['--disable-gpu', '--force-color-profile=srgb', '--disable-renderer-backgrounding', '--disable-background-timer-throttling'] };
  const browser = await chromium.launch(launchArgs);
  const ownBrowser = opt.browsers !== '1';      // one browser process per worker (screenshot encoding runs in the browser process)
  const OW = Math.round(1920 * scale), OH = Math.round(1080 * scale);
  const t0 = Date.now();

  // ---------- job list ----------
  let jobs;                                   // [{f, t, file, k}]
  let chunks = [];
  if (stills) {
    let ts;
    if (opt.times) ts = fs.existsSync(opt.times) ? JSON.parse(fs.readFileSync(opt.times, 'utf8')) : opt.times.split(',').map(Number);
    else { const [a, b] = opt.frames.split(':').map(Number); ts = Array.from({ length: b - a }, (_, i) => (a + i) / fps); }
    jobs = ts.map((x) => { const t = Array.isArray(x) ? x[1] : x; const f = Array.isArray(x) ? x[0] : Math.round(t * fps); return { f, t, file: path.join(work, fname(f)), k: 0 }; });
    chunks = [{ k: 0, f0: 0, f1: jobs.length, total: jobs.length, left: jobs.length, enc: true }];
  } else {
    const fA = Math.max(0, Math.round((+(opt.from ?? 0)) * fps)), fB = Math.min(Math.round(dur * fps), opt.to !== undefined ? Math.round(+opt.to * fps) : Infinity);
    jobs = [];
    for (let c0 = fA, k = 0; c0 < fB; c0 += chunkN, k++) {
      const c1 = Math.min(fB, c0 + chunkN);
      const seg = path.join(work, `seg_${String(c0).padStart(6, '0')}_${String(c1).padStart(6, '0')}.mp4`);
      const dir = path.join(work, `frames_${String(c0).padStart(6, '0')}`);
      const done = fs.existsSync(seg + '.ok') && fs.existsSync(seg);
      const ch = { k, f0: c0, f1: c1, seg, dir, total: c1 - c0, left: 0, enc: done, encoding: false };
      chunks.push(ch);
      if (done) continue;
      fs.mkdirSync(dir, { recursive: true });
      for (let f = c0; f < c1; f++) {
        const file = path.join(dir, fname(f));
        if (fs.existsSync(file) && fs.statSync(file).size > 0) continue;   // resume inside a chunk
        jobs.push({ f, t: f / fps, file, k }); ch.left++;
      }
    }
  }
  const totalFrames = jobs.length;
  let done = 0, last = '', errors = 0, encoded = chunks.filter((c) => c.enc).length;
  const progressFile = path.join(work, 'progress.json');
  const progress = (phase) => {
    const el = (Date.now() - t0) / 1000, rate = done / Math.max(0.001, el);
    fs.writeFileSync(progressFile, JSON.stringify({ phase, done, total: totalFrames, fps, scale, workers, chunks: chunks.length, chunks_encoded: encoded, last,
      rate_fps: +rate.toFixed(2), ms_per_frame: done ? Math.round((el * 1000) / done) : null, eta_s: rate > 0 ? Math.round((totalFrames - done) / rate) : null, errors,
      out: stills ? work : path.resolve(outPath), started_at: new Date(t0).toISOString(), updated_at: new Date().toISOString() }, null, 1));
  };
  progress('start');
  onStop = () => progress('stopped');
  console.log(`${stills ? 'stills' : 'video'}: ${totalFrames} frames to draw (${chunks.length} chunk(s), ${encoded} already encoded), ${workers} workers, ${Math.round(1920 * scale)}x${Math.round(1080 * scale)}, work ${work}`);

  // ---------- baking (optional) ----------
  const pages = [], baked = new Map(), bakeCtx = new Map();
  let bakeQueue = Promise.resolve();
  async function bakePageFor(px) {
    const k = Math.round(px * 100) / 100;
    if (!bakeCtx.has(k)) {
      const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: k });
      const pg = await ctx.newPage();
      await pg.goto(`${base}/engine/bake.html`);
      await pg.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
      bakeCtx.set(k, pg);
    }
    return bakeCtx.get(k);
  }
  function bakeJob(job) {
    if (baked.has(job.key)) return baked.get(job.key);
    const pr = (bakeQueue = bakeQueue.then(async () => {
      fs.mkdirSync(bakeDir, { recursive: true });
      const hash = crypto.createHash('sha1').update(job.svg + JSON.stringify(job.box) + job.px).digest('hex').slice(0, 20);
      const file = path.join(bakeDir, hash + '.png'), url = `/bake/${hash}.png`;
      if (!fs.existsSync(file)) {
        const pg = await bakePageFor(job.px);
        await pg.setViewportSize({ width: Math.ceil(job.box.w), height: Math.ceil(job.box.h) });
        await pg.evaluate(([s, b]) => window.paint(s, b), [job.svg, job.box]);
        await pg.locator('#stage').screenshot({ path: file, omitBackground: true, type: 'png' });
      }
      await Promise.all(pages.map((p) => p.evaluate(([k, u]) => window.bakeDone && window.bakeDone(k, u), [job.key, url]).catch(() => {})));
      return url;
    }));
    baked.set(job.key, pr);
    return pr;
  }
  async function openPage(own = false) {
    // the frame is drawn at output size by CSS (viewport = output, deviceScaleFactor 1): ~40% faster captures than a
    // deviceScaleFactor and pixel-equivalent to it (mean difference 0.02 levels, antialiasing only)
    const br = own ? await chromium.launch(launchArgs) : browser;
    const ctx = await br.newContext({ viewport: { width: OW, height: OH }, deviceScaleFactor: 1 });
    ctx.__own = own ? br : null;
    const page = await ctx.newPage();
    page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
    page.on('console', (m) => { if (m.type() === 'error') console.error('console:', m.text().slice(0, 400)); });
    await page.goto(`${base}${page0}?timeline=/timeline.json&px=${OW}x${OH}&scale=${scale}${bake ? '&bake=1' : ''}`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    const err = await page.evaluate(() => window.__error);
    if (err) throw new Error('page failed to load:\n' + err);
    const missing = await page.evaluate(() => window.__fontsMissing || []);
    if (missing.length) console.error('fonts missing:', missing.join(', '));
    const cdp = await ctx.newCDPSession(page);
    return { page, ctx, cdp };
  }
  if (bake && opt.warm !== '0' && jobs.length) {
    const { page, ctx } = await openPage();
    const tA = jobs[0].t, tB = jobs[jobs.length - 1].t;
    const probe = [];
    for (const sh of T.shots || []) if (sh.end > tA && sh.start <= tB) probe.push(Math.max(sh.start, tA) + 0.5 / fps, (sh.start + sh.end) / 2);
    for (const t of probe) {
      await page.evaluate((t) => window.renderAt(t), t);
      for (const j of await page.evaluate(() => (window.takeBakeJobs ? window.takeBakeJobs() : []))) bakeJob(j);
    }
    await bakeQueue; await ctx.close();
    console.log(`warm-up: ${baked.size} layers baked in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  }

  // ---------- encoding ----------
  let encChain = Promise.resolve();
  const waiters = [];
  const wakeAll = () => { while (waiters.length) waiters.shift()(); };
  const lowestOpen = () => { const c = chunks.find((c) => !c.enc); return c ? c.k : Infinity; };
  function maybeEncode(ch) {
    if (stills || ch.enc || ch.encoding || ch.left > 0) return;
    ch.encoding = true;
    encChain = encChain.then(async () => {
      const te = Date.now();
      await run('nice', encodeArgs(ch.dir, ch.f0, ch.total, ch.seg), `encode ${path.basename(ch.seg)}`);
      fs.writeFileSync(ch.seg + '.ok', JSON.stringify({ f0: ch.f0, f1: ch.f1, fps, scale, crf: opt.crf ?? 15 }));
      if (opt.keep !== '1') fs.rmSync(ch.dir, { recursive: true, force: true });
      ch.enc = true; encoded++;
      console.log(`segment ${path.basename(ch.seg)} encoded in ${((Date.now() - te) / 1000).toFixed(1)} s (${encoded}/${chunks.length})`);
      progress('render');
      wakeAll();
    }).catch((e) => { console.error(e.message); process.exitCode = 3; ch.failed = true; wakeAll(); });
  }
  for (const ch of chunks) maybeEncode(ch);     // chunks whose frames were all on disk already

  // ---------- workers ----------
  let next = 0;
  const ahead = +(opt.ahead ?? 1);              // chunks of frames allowed on disk beyond the oldest unencoded one
  async function take() {
    for (;;) {
      if (next >= jobs.length) return null;
      const j = jobs[next];
      if (stills || j.k <= lowestOpen() + ahead) { next++; return j; }
      if (chunks.some((c) => c.failed)) return null;
      await new Promise((r) => { waiters.push(r); setTimeout(r, 2000); });
    }
  }
  async function worker(w) {
    const P = await openPage(ownBrowser);
    pages.push(P.page);
    for (const [k, pr] of baked) { const u = await pr; await P.page.evaluate(([kk, uu]) => window.bakeDone && window.bakeDone(kk, uu), [k, u]).catch(() => {}); }
    let j;
    while ((j = await take())) {
      const err = await P.page.evaluate((t) => window.renderAt(t), j.t);
      if (err) {
        errors++; console.error(`frame ${j.f} (t=${j.t.toFixed(3)}): ${err.split('\n')[0]}`);
        if (opt.errors !== 'ignore') { console.error(err); process.exit(4); }
      }
      const png = stills && opt.ext === 'png';
      const shot = await P.cdp.send('Page.captureScreenshot', { format: png ? 'png' : 'jpeg', ...(png ? {} : { quality }), clip: { x: 0, y: 0, width: OW, height: OH, scale: 1 }, captureBeyondViewport: false, optimizeForSpeed: true });
      writeAtomic(j.file, Buffer.from(shot.data, 'base64'));
      if (bake) for (const b of await P.page.evaluate(() => (window.takeBakeJobs ? window.takeBakeJobs() : []))) bakeJob(b);
      last = path.basename(j.file); done++;
      const ch = chunks[j.k]; if (!stills) { ch.left--; maybeEncode(ch); }
      if (done % 20 === 0) progress('render');
      if (done % 120 === 0) console.log(`${done}/${totalFrames} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame (wall, ${workers} workers)`);
    }
    pages.splice(pages.indexOf(P.page), 1);
    await P.ctx.close();
    if (P.ctx.__own) await P.ctx.__own.close();
  }
  await Promise.all(Array.from({ length: Math.max(1, Math.min(workers, jobs.length || 1)) }, (_, i) => worker(i)));
  await bakeQueue;
  const tr = (Date.now() - t0) / 1000;
  console.log(`drew ${done} frames in ${tr.toFixed(1)} s (${(done / Math.max(0.001, tr)).toFixed(2)} fps, ${((tr * 1000) / Math.max(1, done)).toFixed(0)} ms/frame wall)`);
  await encChain;
  await browser.close(); server.close();

  if (!stills) {
    if (chunks.some((c) => !c.enc)) { progress('failed'); console.error('some segments failed to encode; re-run to resume'); process.exit(3); }
    const list = path.join(work, 'segments.txt');
    fs.writeFileSync(list, chunks.map((c) => `file '${c.seg.replace(/'/g, "'\\''")}'`).join('\n') + '\n');
    const args = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
    if (opt.audio) args.push('-i', opt.audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '320k', '-shortest');
    args.push('-c:v', 'copy', '-movflags', '+faststart', path.resolve(outPath));
    await run('ffmpeg', args, 'concat');
    const mb = fs.statSync(outPath).size / 1048576;
    progress('done');
    console.log(`wrote ${outPath} (${mb.toFixed(1)} MB) in ${((Date.now() - t0) / 1000).toFixed(1)} s total`);
  } else { progress('done'); console.log(`wrote ${done} stills to ${work}`); }
})().catch((e) => { console.error(e.stack || e); process.exit(2); });
