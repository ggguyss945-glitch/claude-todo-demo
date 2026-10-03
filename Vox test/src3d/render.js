// Headless three.js renderer: drives Chromium (SwiftShader WebGL) with Playwright,
// pulls finished frames back over a local HTTP POST, and pipes them to ffmpeg.
//
//   node render.js --version v2 --stills 4.0,9.5 --scale 0.5 --out stills/
//   node render.js --version v2 --video out.mp4 --workers 3 [--from 0 --to 79]
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');

const args = {};
for (let i = 2; i < process.argv.length; i++) {
  const a = process.argv[i];
  if (a.startsWith('--')) {
    const k = a.slice(2);
    const v = process.argv[i + 1] && !process.argv[i + 1].startsWith('--') ? process.argv[++i] : true;
    args[k] = v;
  }
}
const VERSION = args.version || 'v2';
const SCALE = parseFloat(args.scale || '1');
const W = Math.round(1440 * SCALE), H = Math.round(2560 * SCALE);
const FPS = parseInt(args.fps || '30');
const DURATION = 79.0;
const ROOT = __dirname;

const MIME = { '.js': 'text/javascript', '.html': 'text/html', '.ttf': 'font/ttf', '.json': 'application/json',
  '.png': 'image/png' };

// frame sinks: id -> callback(buffer)
const sinks = new Map();

function startServer() {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const url = decodeURIComponent(req.url.split('?')[0]);
      if (req.method === 'POST' && url.startsWith('/frame/')) {
        const id = url.slice(7);
        const parts = [];
        req.on('data', (c) => parts.push(c));
        req.on('end', () => {
          const buf = Buffer.concat(parts);
          parts.length = 0;
          const cb = sinks.get(id);
          res.writeHead(200);
          res.end('ok');
          if (cb) cb(buf);
        });
        return;
      }
      let p = path.join(ROOT, url);
      if (url.startsWith('/transcript/')) p = path.join(ROOT, '..', url);
      fs.readFile(p, (e, d) => {
        if (e) { res.writeHead(404); res.end(); return; }
        res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
        res.end(d);
      });
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv));
  });
}

async function openPage(browser, port, wid) {
  const page = await browser.newPage({ viewport: { width: 360, height: 640 } });
  page.on('console', (m) => { const t = m.text(); if (!t.includes('GPU stall')) console.log(`[w${wid}]`, t); });
  page.on('pageerror', (e) => console.log(`[w${wid}] PAGEERROR`, e.message, e.stack));
  await page.goto(`http://127.0.0.1:${port}/${args.app || 'app'}/index.html?v=${VERSION}&w=${W}&h=${H}&fps=${FPS}&wid=${wid}${args.prof ? '&prof=1' : ''}${args.off ? '&off=' + args.off : ''}${args.sub ? '&sub=' + args.sub : ''}`);
  await page.waitForFunction('window.__ready === true', null, { timeout: 600000 });
  return page;
}

function launch() {
  const gl = args.gl || 'swiftshader';
  const glArgs = gl === 'swiftshader' ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    : gl === 'egl' ? ['--use-gl=angle', '--use-angle=gl-egl'] : gl === 'vulkan' ? ['--use-gl=angle', '--use-angle=vulkan', '--enable-features=Vulkan']
    : ['--use-gl=egl'];
  return chromium.launch({
    env: { ...process.env, GALLIUM_DRIVER: 'llvmpipe', LP_NUM_THREADS: String(args.lpthreads || 4) },
    args: [...glArgs, '--ignore-gpu-blocklist',
      '--disable-gpu-watchdog', '--disable-features=GpuWatchdog', '--js-flags=--max-old-space-size=8192'],
  });
}

async function renderFrameTo(page, id, t) {
  return new Promise(async (resolve, reject) => {
    sinks.set(id, (buf) => { sinks.delete(id); resolve(buf); });
    try {
      await page.evaluate(async ([t, id]) => { await window.__renderAndPost(t, id); }, [t, id]);
    } catch (e) { reject(e); }
  });
}

async function stills() {
  const srv = await startServer();
  const port = srv.address().port;
  const browser = await launch();
  const page = await openPage(browser, port, 0);
  const outDir = args.out || path.join(ROOT, 'stills');
  fs.mkdirSync(outDir, { recursive: true });
  const times = String(args.stills).split(',').map(Number);
  for (const t of times) {
    const t0 = Date.now();
    const buf = await renderFrameTo(page, `s${t}`, t);
    const raw = path.join(outDir, `${VERSION}_${t.toFixed(2)}.rgba`);
    fs.writeFileSync(raw, buf);
    const png = raw.replace('.rgba', '.png');
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-i', raw,
      '-frames:v', '1', png]);
    fs.unlinkSync(raw);
    console.log(png, `${Date.now() - t0}ms`);
  }
  await browser.close();
  srv.close();
}

async function video() {
  const out = path.resolve(args.video);
  const workers = parseInt(args.workers || '3');
  const from = parseFloat(args.from || '0'), to = parseFloat(args.to || String(DURATION));
  const f0 = Math.round(from * FPS), f1 = Math.round(to * FPS);
  const segDir = out.replace(/\.mp4$/, '_seg');
  fs.mkdirSync(segDir, { recursive: true });
  const srv = await startServer();
  const port = srv.address().port;
  const crf = String(args.crf || '12');
  // small resumable chunks pulled from a shared queue
  const CH = parseInt(args.chunk || '60');
  const chunks = [];
  for (let a = f0; a < f1; a += CH) chunks.push([a, Math.min(f1, a + CH)]);
  const segOf = (a) => path.join(segDir, `c${String(a).padStart(6, '0')}.mkv`);
  const todo = chunks.filter(([a]) => !fs.existsSync(segOf(a) + '.done'));
  const total = todo.reduce((n, [a, b]) => n + b - a, 0);
  console.log(`${chunks.length} chunks, ${todo.length} to render (${total} frames)`);
  const startTime = Date.now();
  let done = 0, lastLog = 0, restart = false;
  const jobs = [];
  for (let w = 0; w < Math.min(workers, todo.length); w++) {
    jobs.push((async () => {
      const browser = await launch();
      const page = await openPage(browser, port, w);
      while (todo.length) {
        const [a, b] = todo.shift();
        const seg = segOf(a);
        const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`,
          '-r', String(FPS), '-i', '-', '-c:v', 'libx264rgb', '-qp', '0', '-preset', 'ultrafast', '-threads', '1', seg],
          { stdio: ['pipe', 'inherit', 'inherit'] });
        for (let f = a; f < b; f++) {
          let buf = await renderFrameTo(page, `w${w}f${f}`, f / FPS);
          if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
          buf = null;
          done++;
          if (global.gc && done % 8 === 0) global.gc();
          if (Date.now() - lastLog > 30000) {
            lastLog = Date.now();
            const el = (Date.now() - startTime) / 1000;
            const rate = done / el;
            console.log(`frames ${done}/${total}  ${rate.toFixed(2)} fps  eta ${((total - done) / rate / 60).toFixed(1)} min  rss ${(process.memoryUsage().rss / 1e9).toFixed(2)}GB`);
          }
        }
        ff.stdin.end();
        await new Promise((r) => ff.on('close', r));
        fs.writeFileSync(seg + '.done', 'ok');
        if (process.memoryUsage().rss > (parseFloat(args.maxrss || '3.5') * 1e9)) { restart = true; break; }
        if (restart) break;
      }
      await browser.close();
    })());
  }
  await Promise.all(jobs);
  srv.close();
  if (restart) { console.log('restarting to release memory'); process.exit(75); }
  const list = path.join(segDir, 'list.txt');
  fs.writeFileSync(list, chunks.map(([a]) => `file '${segOf(a)}'`).join('\n') + '\n');
  const cmd = ['-v', 'error', '-stats', '-y', '-f', 'concat', '-safe', '0', '-i', list];
  if (args.audio) cmd.push('-ss', String(from), '-t', String(to - from), '-i', args.audio);
  cmd.push('-map', '0:v:0');
  if (args.audio) cmd.push('-map', '1:a:0', '-c:a', 'aac', '-b:a', '320k');
  const vf = (args.vf ? args.vf + ',' : '') + 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p';
  cmd.push('-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-profile:v', 'high', '-tune', 'film',
    '-x264-params', 'aq-mode=3', '-r', String(FPS),
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-movflags', '+faststart', out);
  if (!args.noencode) execFileSync('ffmpeg', cmd, { stdio: 'inherit' });
  console.log('wrote', out, `in ${((Date.now() - startTime) / 60000).toFixed(1)} min`);
}

(args.stills ? stills() : video()).catch((e) => { console.error(e); process.exit(1); });
