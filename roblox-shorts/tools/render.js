#!/usr/bin/env node
// Frame-accurate offline renderer: headless Chromium (SwiftShader WebGL2) -> JPEG frames -> x264 segments -> mp4.
//
//   node tools/render.js <episode.js | timeline.json> <out.mp4> [key=value ...]
//     from=0 to=<end>      seconds to render (frame range [from*fps, to*fps))
//     workers=2            parallel renderers;  mode=browsers (one Chromium per worker, default) | pages (one browser)
//     chunk=300            frames per x264 segment (frames are deleted once their segment is encoded)
//     quality=final        final (scene 1080x1920 MSAA) | balanced (scene x0.85) | fast (x0.75) | draft (x0.75 FXAA)
//                          | preview (540x960 output);  rs=0.9 overrides the scene render scale
//     jpegq=92 crf=16 preset=medium gop=120
//     times=0.5,1.2        stills mode: render these times (s) to <out>/still_<t>.jpg (out = a directory)
//     sheet=1              also write a contact sheet (<out>.sheet.jpg for videos, <out>/sheet.jpg for stills)
//     bench=120            benchmark: render N frames from `from`, report ms/frame, no encode
//     profile=1            per-stage GPU timings (adds gl.finish() syncs; slower, for diagnostics)
//     keep=1               keep the segment folder after concatenation
// Resumable: re-running the same command skips segments already encoded in <out>.parts/.
// NODE_PATH must contain playwright (e.g. NODE_PATH=/opt/node-tools/node_modules).
const { chromium } = require('playwright');
const http = require('http'), fs = require('fs'), path = require('path'), { spawn, spawnSync } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const GL_ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-vsync', '--disable-frame-rate-limit', '--disable-background-timer-throttling', '--disable-renderer-backgrounding', '--disable-backgrounding-occluded-windows'];
const MIME = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.wasm': 'application/wasm', '.css': 'text/css', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };

function parseArgs(argv) {
  const pos = [], kv = {};
  for (const a of argv) { const m = a.match(/^([a-zA-Z_]+)=(.*)$/); if (m) kv[m[1]] = m[2]; else pos.push(a); }
  return { pos, kv };
}
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);

// ---------------- static server + frame sink ----------------
function startServer(sink) {
  const srv = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split('?')[0]);
    if (req.method === 'POST' && url.startsWith('/frame/')) {
      const name = url.slice(7); const chunks = [];
      req.on('data', (c) => chunks.push(c));
      req.on('end', () => { try { sink(name, Buffer.concat(chunks)); res.writeHead(200); res.end('ok'); } catch (e) { res.writeHead(500); res.end(String(e)); } });
      return;
    }
    const p = path.join(ROOT, url); if (!p.startsWith(ROOT)) { res.writeHead(403); return res.end(); }
    fs.readFile(p, (e, d) => { if (e) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream', 'Cache-Control': 'no-store' }); res.end(d); });
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

// ---------------- workers ----------------
class Worker {
  constructor(id, opts) { this.id = id; this.o = opts; this.frames = 0; this.ms = 0; this.stages = {}; }
  async start(sharedBrowser) {
    this.browser = sharedBrowser || (await chromium.launch({ args: GL_ARGS }));
    this.owned = !sharedBrowser;
    this.page = await this.browser.newPage({ viewport: { width: 540, height: 960 } });
    this.page.on('pageerror', (e) => log(`[w${this.id}] pageerror`, e.message));
    this.page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') log(`[w${this.id}] console.${m.type()}`, m.text().slice(0, 300)); });
    await this.page.goto(`${this.o.base}/engine/index.html`);
    await this.page.waitForFunction(() => window.__ready, null, { timeout: 120000 });
    await this.page.evaluate(() => { document.getElementById('c').style.display = 'none'; });
    this.info = await this.page.evaluate((o) => window.ENGINE.init(o), { episode: this.o.episode, timeline: this.o.timeline, quality: this.o.quality, profile: this.o.profile, overrides: this.o.overrides });
    return this.info;
  }
  async render(i, upload) {
    const t0 = Date.now();
    const r = await this.page.evaluate(([i, upload, q]) => window.ENGINE.frame(i, { upload, quality: q }), [i, upload, this.o.jpegq / 100]);
    this.frames++; this.ms += Date.now() - t0;
    const tm = r.timings; for (const k of ['build', 'update', 'render', 'encode', 'upload']) this.stages[k] = (this.stages[k] || 0) + (tm[k] || 0);
    if (tm.stages) for (const k in tm.stages) this.stages['gpu_' + k] = (this.stages['gpu_' + k] || 0) + tm.stages[k];
    return tm;
  }
  async stop() { try { await this.page?.close(); } catch {} if (this.owned) try { await this.browser?.close(); } catch {} }
}

function ffmpegEncode(framesDir, a, n, fps, segPath, o) {
  return new Promise((resolve, reject) => {
    const args = ['-y', '-v', 'error', '-framerate', String(fps), '-start_number', String(a), '-i', path.join(framesDir, '%06d.jpg'), '-frames:v', String(n),
      '-vf', 'scale=in_color_matrix=bt601:in_range=full:out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd+full_chroma_int,format=yuv420p',
      '-c:v', 'libx264', '-preset', o.preset, '-crf', String(o.crf), '-g', String(o.gop), '-pix_fmt', 'yuv420p',
      '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-movflags', '+faststart', segPath + '.tmp.mp4'];
    const p = spawn('nice', ['-n', '5', 'ffmpeg', ...args], { stdio: ['ignore', 'ignore', 'pipe'] }); let err = '';
    p.stderr.on('data', (d) => (err += d));
    p.on('close', (code) => { if (code === 0) { fs.renameSync(segPath + '.tmp.mp4', segPath); resolve(); } else reject(new Error('ffmpeg failed: ' + err)); });
  });
}

function contactSheetVideo(video, out, cols = 6, rows = 3) {
  const dur = parseFloat(spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video]).stdout.toString());
  const n = cols * rows; const fpsSel = n / Math.max(0.1, dur);
  spawnSync('ffmpeg', ['-y', '-v', 'error', '-i', video, '-vf', `fps=${fpsSel.toFixed(5)},scale=270:-2:in_color_matrix=bt709:in_range=tv:out_range=pc:flags=bicubic+accurate_rnd+full_chroma_int,format=rgb24,tile=${cols}x${rows}:padding=4:color=0x101014`, '-frames:v', '1', '-q:v', '3', out]);
  return out;
}
function contactSheetImages(files, out, cols = 4) {
  const rows = Math.ceil(files.length / cols); const inputs = files.flatMap((f) => ['-i', f]);
  const filt = files.map((_, i) => `[${i}:v]scale=270:-2[s${i}]`).join(';') + ';' + files.map((_, i) => `[s${i}]`).join('') + `xstack=inputs=${files.length}:layout=` +
    files.map((_, i) => `${(i % cols) * 274}_${Math.floor(i / cols) * 484}`).join('|') + `:fill=0x101014`;
  if (files.length === 1) { spawnSync('ffmpeg', ['-y', '-v', 'error', '-i', files[0], '-vf', 'scale=270:-2', out]); return out; }
  const r = spawnSync('ffmpeg', ['-y', '-v', 'error', ...inputs, '-filter_complex', filt, '-q:v', '3', out]); if (r.status) log('sheet failed', r.stderr.toString().slice(0, 400));
  return out;
}

// ---------------- main ----------------
async function main() {
  const { pos, kv } = parseArgs(process.argv.slice(2));
  if (pos.length < 2) { console.log(fs.readFileSync(__filename, 'utf8').split('\n').slice(1, 17).join('\n')); process.exit(1); }
  const input = path.resolve(pos[0]); const out = path.resolve(pos[1]);
  if (!input.startsWith(ROOT)) throw new Error('episode/timeline must live under ' + ROOT);
  const rel = '/' + path.relative(ROOT, input).split(path.sep).join('/');
  const isTimeline = input.endsWith('.json');
  const o = {
    episode: isTimeline ? null : rel, timeline: isTimeline ? rel : null, quality: kv.quality || 'final', profile: kv.profile === '1',
    overrides: kv.rs ? { renderScale: +kv.rs } : {},
    jpegq: +(kv.jpegq || 92), crf: +(kv.crf || 16), preset: kv.preset || 'medium', gop: +(kv.gop || 120),
  };
  const W = +(kv.workers || 2), chunk = +(kv.chunk || 300), mode = kv.mode || 'browsers';
  const stills = kv.times ? kv.times.split(',').map(Number) : null;
  const bench = kv.bench ? +kv.bench : 0;

  // frame sink: name is "<dir-key>/<file>" resolved against registered dirs
  const sinks = {};
  const srv = await startServer((name, buf) => { const [key, file] = name.split('/'); const dir = sinks[key]; if (!dir) throw new Error('no sink ' + key); const f = path.join(dir, file); fs.writeFileSync(f + '.part', buf); fs.renameSync(f + '.part', f); });
  o.base = `http://127.0.0.1:${srv.address().port}`;

  const t0 = Date.now();
  const shared = mode === 'pages' ? await chromium.launch({ args: GL_ARGS }) : null;
  const workers = Array.from({ length: Math.max(1, W) }, (_, k) => new Worker(k, o));
  const infos = await Promise.all(workers.map((w) => w.start(shared)));
  const info = infos[0]; const fps = info.fps;
  log(`episode "${info.name}" ${info.width}x${info.height}@${fps} ${info.duration}s (${info.frames} frames), ${info.shots.length} shots, gpu: ${info.gpu}, workers=${W} (${mode}), init ${((Date.now() - t0) / 1000).toFixed(1)}s`);

  const finish = async () => { await Promise.all(workers.map((w) => w.stop())); if (shared) await shared.close(); srv.close(); };
  const summary = (frames, ms) => {
    const st = {}; let n = 0; for (const w of workers) { n += w.frames; for (const k in w.stages) st[k] = (st[k] || 0) + w.stages[k]; }
    for (const k in st) st[k] = +(st[k] / Math.max(1, n)).toFixed(1);
    return { frames, wall_s: +(ms / 1000).toFixed(1), ms_per_frame_wall: +(ms / Math.max(1, frames)).toFixed(1), fps: +(frames / (ms / 1000)).toFixed(3), per_worker_ms_per_frame: workers.map((w) => +(w.ms / Math.max(1, w.frames)).toFixed(0)), stage_ms_avg: st };
  };

  // ---- stills ----
  if (stills) {
    fs.mkdirSync(out, { recursive: true }); sinks.s = out; const files = [];
    let k = 0; const queue = stills.slice();
    await Promise.all(workers.map(async (w) => { while (queue.length) { const t = queue.shift(); const i = Math.min(info.frames - 1, Math.round(t * fps)); const f = `still_${t.toFixed(2)}.jpg`; await w.render(i, `/frame/s/${f}`); files.push(path.join(out, f)); k++; } }));
    files.sort(); log(`stills: ${files.length} -> ${out}`);
    if (kv.sheet === '1') log('sheet', contactSheetImages(files, path.join(out, 'sheet.jpg')));
    console.log(JSON.stringify(summary(k, Date.now() - t0)));
    return finish();
  }

  const fromF = Math.max(0, Math.round(+(kv.from || 0) * fps)); const toF = Math.min(info.frames, kv.to ? Math.round(+kv.to * fps) : info.frames);

  // ---- benchmark ----
  if (bench) {
    const tmp = fs.mkdtempSync(path.join(path.dirname(out), '.bench_')); sinks.b = tmp;
    const N = Math.min(bench, toF - fromF); let next = fromF;
    // warm-up: one frame per worker (shader compile + shot build), not counted
    await Promise.all(workers.map((w, k) => w.render(fromF + k, `/frame/b/warm_${k}.jpg`)));
    for (const w of workers) { w.frames = 0; w.ms = 0; w.stages = {}; }
    const tb = Date.now();
    await Promise.all(workers.map(async (w) => { while (next < fromF + N) { const i = next++; await w.render(i, `/frame/b/${String(i).padStart(6, '0')}.jpg`); } }));
    const res = summary(N, Date.now() - tb); res.workers = W; res.mode = mode; res.quality = o.quality;
    res.avg_jpeg_kb = +(fs.readdirSync(tmp).filter((f) => !f.startsWith('warm')).reduce((s, f) => s + fs.statSync(path.join(tmp, f)).size, 0) / N / 1024).toFixed(0);
    fs.rmSync(tmp, { recursive: true, force: true });
    console.log(JSON.stringify(res));
    return finish();
  }

  // ---- video ----
  const parts = out + '.parts'; const framesDir = path.join(parts, 'frames'); fs.mkdirSync(framesDir, { recursive: true }); sinks.f = framesDir;
  const chunks = []; for (let a = fromF; a < toF; a += chunk) { const b = Math.min(toF, a + chunk); chunks.push({ a, b, seg: path.join(parts, `seg_${String(a).padStart(6, '0')}_${String(b).padStart(6, '0')}.mp4`), left: b - a }); }
  const todo = chunks.filter((c) => !fs.existsSync(c.seg));
  log(`frames ${fromF}-${toF} (${toF - fromF}), ${chunks.length} segments, ${chunks.length - todo.length} already done`);
  const totalTodo = todo.reduce((s, c) => s + (c.b - c.a), 0); let done = 0; const tr = Date.now();
  // frames already on disk from an interrupted run count as done
  const have = new Set(fs.readdirSync(framesDir));
  const queue = []; for (const c of todo) for (let i = c.a; i < c.b; i++) { if (have.has(String(i).padStart(6, '0') + '.jpg')) { c.left--; done++; } else queue.push(i); }
  const chunkOf = (i) => todo.find((c) => i >= c.a && i < c.b);
  const encQ = []; let encoding = Promise.resolve(); let pendingEnc = 0;
  const enqueueEncode = (c) => {
    pendingEnc++;
    encoding = encoding.then(async () => {
      const te = Date.now(); await ffmpegEncode(framesDir, c.a, c.b - c.a, fps, c.seg, o);
      for (let i = c.a; i < c.b; i++) fs.rmSync(path.join(framesDir, String(i).padStart(6, '0') + '.jpg'), { force: true });
      pendingEnc--; log(`segment ${path.basename(c.seg)} encoded in ${((Date.now() - te) / 1000).toFixed(1)}s`);
    });
  };
  for (const c of todo) if (c.left === 0) enqueueEncode(c);
  const writeProgress = () => {
    const el = (Date.now() - tr) / 1000; const rendered = workers.reduce((s, w) => s + w.frames, 0); const f = rendered / Math.max(0.001, el);
    const p = { out, from: fromF, to: toF, total: totalTodo, done, elapsed_s: +el.toFixed(0), fps: +f.toFixed(3), eta_s: +((totalTodo - done) / Math.max(1e-3, f)).toFixed(0), segments_done: chunks.filter((c) => fs.existsSync(c.seg)).length, segments: chunks.length, pending_encodes: pendingEnc, workers: workers.map((w) => ({ frames: w.frames, ms_per_frame: +(w.ms / Math.max(1, w.frames)).toFixed(0) })) };
    fs.writeFileSync(path.join(parts, 'progress.json'), JSON.stringify(p, null, 1)); return p;
  };
  let lastLog = 0;
  await Promise.all(workers.map(async (w) => {
    while (queue.length) {
      while (pendingEnc > 2) await new Promise((r) => setTimeout(r, 200)); // back-pressure keeps disk small
      const i = queue.shift(); let tries = 0;
      for (;;) {
        try { await w.render(i, `/frame/f/${String(i).padStart(6, '0')}.jpg`); break; }
        catch (e) { if (++tries > 2) throw e; log(`[w${w.id}] frame ${i} failed (${e.message.slice(0, 200)}), restarting worker`); await w.stop(); await w.start(shared); }
      }
      done++; const c = chunkOf(i); if (--c.left === 0) enqueueEncode(c);
      if (Date.now() - lastLog > 10000) { lastLog = Date.now(); const p = writeProgress(); log(`${done}/${totalTodo} frames, ${p.fps} fps, eta ${p.eta_s}s`); }
    }
  }));
  await encoding; writeProgress();
  const stats = summary(workers.reduce((s, w) => s + w.frames, 0), Date.now() - tr);
  await finish();
  // concat
  const list = path.join(parts, 'list.txt'); fs.writeFileSync(list, chunks.map((c) => `file '${c.seg.replace(/'/g, "'\\''")}'`).join('\n'));
  const r = spawnSync('ffmpeg', ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', out]);
  if (r.status) throw new Error('concat failed ' + r.stderr);
  log(`wrote ${out} (${(fs.statSync(out).size / 1e6).toFixed(1)} MB)`);
  if (kv.sheet === '1') log('sheet', contactSheetVideo(out, out.replace(/\.mp4$/, '') + '.sheet.jpg'));
  if (kv.keep !== '1') fs.rmSync(parts, { recursive: true, force: true });
  console.log(JSON.stringify(stats));
}

main().catch((e) => { console.error(e); process.exit(1); });
