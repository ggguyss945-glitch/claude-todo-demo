"""Builds the live progress page from status.json (stages, notes) and the preview images/audio in the same folder.
    python3 progress.py <work dir> <out.html>
"""
import base64, html, json, os, sys

WD, OUT = sys.argv[1], sys.argv[2]
st = json.load(open(os.path.join(WD, 'status.json')))
PILL = {'done': ('Done', 'ok'), 'running': ('In progress', 'run'), 'waiting': ('Waiting', 'wait'), 'blocked': ('Blocked', 'bad')}


def data_uri(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


stages = ''.join(
    f'<li class="stage {PILL[s["status"]][1]}"><div class="row"><span class="name">{html.escape(s["name"])}</span>'
    f'<span class="pill">{PILL[s["status"]][0]}</span></div><p>{html.escape(s.get("detail", ""))}</p>'
    + (f'<div class="bar"><i style="width:{s["pct"]:.0f}%"></i></div>' if 'pct' in s else '') + '</li>'
    for s in st['stages'])
done = sum(1 for s in st['stages'] if s['status'] == 'done') + sum(s.get('pct', 0) / 100 for s in st['stages'] if s['status'] == 'running')
overall = 100 * done / len(st['stages'])
prev = ''
for p in st.get('previews', []):
    f = os.path.join(WD, p['file'])
    if os.path.exists(f):
        prev += f'<figure><img src="{data_uri(f, "image/jpeg")}" alt="{html.escape(p["caption"])}"><figcaption>{html.escape(p["caption"])}</figcaption></figure>'
aud = ''
for a in st.get('audio', []):
    f = os.path.join(WD, a['file'])
    if os.path.exists(f):
        aud += f'<div class="clip"><span>{html.escape(a["caption"])}</span><audio controls preload="none" src="{data_uri(f, "audio/mpeg")}"></audio></div>'
notes = ''.join(f'<li>{html.escape(n)}</li>' for n in st.get('notes', []))

page = f'''<title>The Other Resident</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;800&display=swap">
<style>
/* one dark column like the film itself: a header, the overall bar, stages, previews, notes */
:root{{--bg:#0d0f14;--panel:#151922;--line:#262c39;--fg:#e8eaf0;--muted:#8c93a3;--red:#e3202a;--ok:#3fbf73;--run:#f2b84a;
--display:"Montserrat",system-ui,sans-serif;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:var(--display);font-size:15px;line-height:1.55}}
main{{max-width:980px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:30px}}
.eyebrow{{font-size:12px;letter-spacing:.24em;color:var(--muted);text-transform:uppercase;margin:0}}
h1{{font-weight:800;font-size:clamp(30px,6vw,48px);line-height:1.05;margin:6px 0 0;letter-spacing:.01em;text-wrap:balance}}
h1 b{{color:var(--red)}}
.sub{{color:var(--muted);margin:8px 0 0}}
.overall{{display:grid;gap:8px}} .overall .bar{{height:10px}}
.bar{{height:6px;background:var(--line);border-radius:6px;overflow:hidden}} .bar i{{display:block;height:100%;background:var(--red)}}
h2{{font-size:13px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin:0 0 12px;font-weight:600}}
ol{{list-style:none;margin:0;padding:0;display:grid;gap:10px}}
.stage{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.stage .row{{display:flex;justify-content:space-between;gap:12px;align-items:center}} .stage .name{{font-weight:600}}
.stage p{{margin:4px 0 0;color:var(--muted);font-size:14px}} .stage .bar{{margin-top:10px}}
.pill{{font-size:12px;font-weight:600;padding:2px 10px;border-radius:99px;white-space:nowrap;border:1px solid currentColor}}
.ok .pill{{color:var(--ok)}} .run .pill{{color:var(--run)}} .wait .pill{{color:var(--muted)}} .bad .pill{{color:var(--red)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}
figure{{margin:0}} figure img{{width:100%;border-radius:8px;border:1px solid var(--line);display:block}}
figcaption{{font-size:13px;color:var(--muted);margin-top:6px}}
.clip{{display:grid;gap:6px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px}} .clip audio{{width:100%}}
.notes li{{color:var(--muted);margin-bottom:6px}} .notes{{padding-left:18px;margin:0}}
.updated{{font-size:12px;color:var(--muted)}}
</style>
<main>
<header><p class="eyebrow">House rules · rule-format horror · EN + RU</p>
<h1>If a police officer knocks… <b>don't prove you live there</b></h1>
<p class="sub">Script: "The Other Resident" · about 12 minutes · 2560×1440, 60 fps</p></header>
<section class="overall"><div class="row" style="display:flex;justify-content:space-between"><span>Overall</span><span>{overall:.0f}%</span></div>
<div class="bar"><i style="width:{overall:.0f}%"></i></div><span class="updated">Updated {html.escape(st["updated"])}</span></section>
<section><h2>Stages</h2><ol>{stages}</ol></section>
{f'<section><h2>Latest frames</h2><div class="grid">{prev}</div></section>' if prev else ''}
{f'<section><h2>Voice samples</h2><div class="grid">{aud}</div></section>' if aud else ''}
<section><h2>Notes</h2><ul class="notes">{notes}</ul></section>
</main>'''
open(OUT, 'w').write(page)
print(f'{os.path.getsize(OUT) // 1024} KB, overall {overall:.0f}%')
