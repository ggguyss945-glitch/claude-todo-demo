// Render scenes to PNG: node tools/render.js scene1 scene2 ...  (t via scene@t)
const { chromium } = require('playwright');
const path = require('path');
const http = require('http');
const fs = require('fs');

const root = path.resolve(__dirname, '..');
const outDir = path.join(root, 'out', 'frames');
fs.mkdirSync(outDir, { recursive: true });

// tiny static server so ES modules load
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); return res.end(); }
    const type = p.endsWith('.js') ? 'text/javascript' : p.endsWith('.html') ? 'text/html' : 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': type }); res.end(data);
  });
});

(async () => {
  await new Promise((r) => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
  for (const arg of process.argv.slice(2)) {
    const [scene, t = '0'] = arg.split('@');
    await page.goto(`http://127.0.0.1:${port}/engine/render.html?scene=${scene}&t=${t}`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
    const file = path.join(outDir, `${scene}${t !== '0' ? '_' + t : ''}.png`);
    await page.locator('#stage').screenshot({ path: file });
    console.log('rendered', file);
  }
  await browser.close(); server.close();
})();
