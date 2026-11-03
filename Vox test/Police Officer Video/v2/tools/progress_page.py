"""Live progress page for v2, in counts rather than percentages (the owner asked for "N of M frames, X fps").
    python3 progress_page.py <work dir> <out.html>
Reads <work dir>/status.json:
  {updated, steps_done, steps_total, stages[{name, status, detail, count?}], previews[{file, caption}],
   audio[{file, caption}], notes[]}
and, when a render is running, <work dir>/picture/progress_*.json ({done, total, fps} per worker), shown as a frame
counter with speed and time left.
"""
import base64, glob, html, json, os, sys

WD, OUT = sys.argv[1], sys.argv[2]
st = json.load(open(os.path.join(WD, 'status.json')))
PILL = {'done': ('Done', 'ok'), 'running': ('Working', 'run'), 'waiting': ('Next', 'wait'), 'blocked': ('Blocked', 'bad')}


def data_uri(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def esc(s): return html.escape(str(s))


render = ''
P = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(WD, 'picture', 'progress_*.json')))]
if P:
    done, total = sum(p['done'] for p in P), sum(p['total'] for p in P)
    fps = sum(p.get('fps', 0) for p in P if p['done'] < p['total'])
    left = max(((p['total'] - p['done']) / p['fps'] for p in P if p.get('fps') and p['done'] < p['total']), default=0) / 60
    render = (f'<section class="render"><h2>Render</h2><div class="big">{done:,} <span>of {total:,} frames</span></div>'
              f'<div class="facts"><span>{fps:.1f} frames per second</span><span>{len(P)} workers</span>'
              f'<span>{"finished" if done >= total else f"about {left:.0f} min left"}</span></div></section>')
stages = ''.join(
    f'<li class="stage {PILL[s["status"]][1]}"><div class="row"><span class="name">{esc(s["name"])}</span>'
    f'<span class="pill">{PILL[s["status"]][0]}</span></div>'
    + (f'<div class="count">{esc(s["count"])}</div>' if s.get('count') else '')
    + f'<p>{esc(s.get("detail", ""))}</p></li>' for s in st['stages'])
prev = ''.join(f'<figure><img src="{data_uri(os.path.join(WD, p["file"]), "image/jpeg")}" alt="{esc(p["caption"])}">'
               f'<figcaption>{esc(p["caption"])}</figcaption></figure>'
               for p in st.get('previews', []) if os.path.exists(os.path.join(WD, p['file'])))
aud = ''.join(f'<div class="clip"><span>{esc(a["caption"])}</span><audio controls preload="none" '
              f'src="{data_uri(os.path.join(WD, a["file"]), "audio/mpeg")}"></audio></div>'
              for a in st.get('audio', []) if os.path.exists(os.path.join(WD, a['file'])))
notes = ''.join(f'<li>{esc(n)}</li>' for n in st.get('notes', []))

page = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(st.get("title", "The Other Resident"))}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;800&display=swap">
<style>
/* one dark column like the film itself: header, step counter, render counter, stages, previews, notes */
:root{{--bg:#0d0f14;--panel:#151922;--line:#262c39;--fg:#e8eaf0;--muted:#8c93a3;--red:#e3202a;--ok:#3fbf73;--run:#f2b84a;
--display:"Montserrat",system-ui,sans-serif;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font-family:var(--display);font-size:15px;line-height:1.55}}
main{{max-width:980px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:30px}}
.eyebrow{{font-size:12px;letter-spacing:.24em;color:var(--muted);text-transform:uppercase;margin:0}}
h1{{font-weight:800;font-size:clamp(30px,6vw,48px);line-height:1.05;margin:6px 0 0;letter-spacing:.01em;text-wrap:balance}}
h1 b{{color:var(--red)}}
.sub{{color:var(--muted);margin:8px 0 0}}
.steps{{display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}} .steps b{{font-size:28px;font-weight:800}}
.steps span{{color:var(--muted)}} .updated{{font-size:12px;color:var(--muted)}}
.render{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
.render .big{{font-size:clamp(28px,7vw,44px);font-weight:800;font-variant-numeric:tabular-nums}} .render .big span{{font-size:16px;color:var(--muted);font-weight:600}}
.render .facts{{display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-variant-numeric:tabular-nums}}
h2{{font-size:13px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin:0 0 12px;font-weight:600}}
ol{{list-style:none;margin:0;padding:0;display:grid;gap:10px}}
.stage{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.stage .row{{display:flex;justify-content:space-between;gap:12px;align-items:center}} .stage .name{{font-weight:600}}
.stage .count{{font-weight:600;font-variant-numeric:tabular-nums;margin-top:2px}}
.stage p{{margin:4px 0 0;color:var(--muted);font-size:14px}}
.pill{{font-size:12px;font-weight:600;padding:2px 10px;border-radius:99px;white-space:nowrap;border:1px solid currentColor}}
.ok .pill{{color:var(--ok)}} .run .pill{{color:var(--run)}} .wait .pill{{color:var(--muted)}} .bad .pill{{color:var(--red)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}
figure{{margin:0}} figure img{{width:100%;border-radius:8px;border:1px solid var(--line);display:block}}
figcaption{{font-size:13px;color:var(--muted);margin-top:6px}}
.clip{{display:grid;gap:6px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px}} .clip audio{{width:100%}}
.notes li{{color:var(--muted);margin-bottom:6px}} .notes{{padding-left:18px;margin:0}}
</style>
<main>
<header><p class="eyebrow">{esc(st.get("eyebrow", "House rules · rule-format horror · v2 rebuild"))}</p>
<h1>{esc(st.get("h1", "If a police officer knocks…"))} <b>{esc(st.get("h1b", "don't prove you live there"))}</b></h1>
<p class="sub">{esc(st.get("sub", "Script: The Other Resident · 11:37 · 2560×1440, 60 fps · about 41,860 frames"))}</p></header>
<section class="steps"><b>{st.get("steps_done", 0)} of {st.get("steps_total", 0)}</b><span>{esc(st.get("steps_label", "build steps done"))}</span>
<span class="updated">Updated {esc(st["updated"])}</span></section>
{render}
<section><h2>Stages</h2><ol>{stages}</ol></section>
{f'<section><h2>Latest frames</h2><div class="grid">{prev}</div></section>' if prev else ''}
{f'<section><h2>Listen</h2><div class="grid">{aud}</div></section>' if aud else ''}
<section><h2>Notes</h2><ul class="notes">{notes}</ul></section>
</main>'''
open(OUT, 'w').write(page)
print(f'{os.path.getsize(OUT) // 1024} KB, {st.get("steps_done", 0)} of {st.get("steps_total", 0)} steps')
