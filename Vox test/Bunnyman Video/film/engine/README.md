# engine: cheat sheet

A 2.5D layered compositor for the v2 film. You draw in a **1920x1080 design space** with skia. The engine handles
parallax, depth of field, real lenses (doorbell fisheye, peephole), the grade and the HUD, and it scales to the render
size (2560x1440 for the film, 960x540 for tests).

```python
import sys; sys.path.insert(0, '<v2 dir>')
from engine import *                    # core + Cam helpers + Layer/render_frame/Scene + Lens + Grade + hud
set_render_size(960, 540)               # call this before you build anything size-dependent
```

## 1. Layers and depth

```python
def porch(pen, t):                      # draw exactly what the home camera (x=960, y=540, zoom=1) sees
    pen.linear(rect(-600, 0, 3100, 1100), 0, 0, 0, 1100, ['#0b0f1c', '#1b2442'])   # fast vertical gradient
    pen.shape(rect(300, 560, 44, 310), '#4a3a2e', 6)                                # fill + #1d1f26 outline

layers = [
    Layer(40,  sky,     'sky',     cache='porch_sky', bounds=(-1000, -560, 2920, 1640)),   # static: drawn once
    Layer(6,   houses,  'houses',  cache='porch_houses', bounds=...),
    Layer(1.4, porch,   'porch',   cache='porch_floor'),
    Layer(lambda t: 1.0 - 0.55 * ease_in_out(t / 3), officer, 'officer', ref_depth=1.0),  # walks up to the lens
    Layer(0.6, doorframe, 'frame', cache='porch_frame', blur=0),                          # near, never blurred
]
img = render_frame(layers, cam.at(t), t, frame_i, focus=1.0, dof=6.75, lens='doorbell', grade='night_blue',
                   post={'flash': police_flash(t)}, hud=lambda cv, t: hud.caption(cv, line))
```

- **Depth.** 1.0 is the subject plane. Backgrounds sit at 3 to 50 and foregrounds at 0.4 to 0.8. A camera pan of dx
  moves a layer by dx/d. Zoom is a real dolly: near layers grow faster.
- **Approaching the lens.** Animate the depth, for example `depth=f(t)` with `ref_depth` set to the depth you drew at.
  The layer grows by ref_depth/depth about the optical axis, and the fisheye bulges it.
- **`blur`.** `None` uses depth of field only. A number adds extra blur sigma in design px. `0` keeps the layer sharp
  always.
- **Depth of field.** `dof` is the blur sigma in design px when |1/d - 1/focus| = 1. For face close-ups, use
  `focus=1, dof=6.75`: a background at d=3 then gets sigma 4.5 (6 px at 2560), as the spec asks. `focus` can be a layer
  name. Also darken that background with `dim=0.3`.
- **Other Layer parameters.** `alpha`, `dim` (0 to 1) and `tint=('#hex', k)` take values or functions of t.
  `screen=True` locks the layer to the frame but still sends it through the lens.
- **`cache`.** Use `True`, or a string key that layers rebuilt each shot can share. The layer is drawn once at
  `cache_t`, over `bounds`, which defaults to the frame plus 25% on each side. Only non-empty 96 px tiles are blitted.
  If you need extra headroom for big push-ins, set `cache_res=1.3`.
- **Animation over a static set.** Put the static set in a cached layer and the animated parts (moths, flicker, car) in a
  second, uncached layer at the same depth.

## 2. Camera (`engine.camera`)

```python
cam = push_in(t0, t1, x=960, y=500, z0=1.0, rate=0.025)          # 2.5 %/s, reference ease: moving at the cut
cam = drift(t0, t1, 880, 520, 1040, 500, zoom=1.05)
cam = Cam([(0, 960, 540, 1.0), (2.5, 990, 520, 1.08, 0, 'push')], shake=2.5)   # keys: t, x, y, zoom[, roll[, ease]]
cam.hit(1.32, amp=8).snap(2.0, factor=1.25, dur=0.1).post_push(0, 3, 1.0, 1.06)
pan(...), whip(t, x0, x1) (motion blur happens automatically), pull_out(...), snap_zoom(...), hold(...), handheld(cam, 3)
```

- `x, y` is the design point at the centre of the frame (on the depth-1 plane).
- `zoom` is a dolly, so it has parallax.
- `snap` is an optical punch-in with a small overshoot.
- `post_push` zooms into the finished image, after the lens. Use it to push into doorbell footage while the fisheye
  geometry stays fixed.
- `roll` is in degrees. It is applied to the final image, with an automatic zoom to hide the corners, at the cost of one
  extra warp.
- Eases live in `EASES`: `lin`, `in_out`, `out`, `in`, `push`, `back`, `smooth`, `hold`, `step`. There are also
  `spring(t)` and `noise1(t, seed)` for idle motion.

## 3. Lenses (`engine.lens`)

The lens works on the composited scene: a physical rectilinear-to-fisheye remap.

| lens | what it does |
|---|---|
| `None` | flat cartoon (use this for normal shots: it is the fastest) |
| `'lens'` | mild cinematic barrel, k = 0.05 |
| `'doorbell'` | equidistant fisheye with a 150° diagonal (about 130° horizontal), centre magnified 1.15x, a 1920x1080 camera (`res=0.75`), slight colour fringing at the edges, sensor noise, sharpening, JPEG stream blocks (`codec=55`). Corners past 90% of the diagonal fade to black. |
| `'doorbell_ir'` | the same in IR night mode: monochrome, brightness falls off with depth (a near face glows, the street goes dark), more noise. Pair it with `grade='ir_night'`, which is the default. |
| `'peephole'` | disc 0.98 H, pure black outside, brown rim, barrel k1 of about 0.4 at the rim, strong radial falloff |
| `Lens('doorbell', fov=160, zoom=1.0, fps=15, codec=40, ...)` | any setting you choose. `fps` makes the doorbell scene step like a real stream, while post moves stay smooth. |

- **Coverage.** Fisheye views need sets drawn wider than the frame. `get_lens('doorbell').src_rect()` gives about
  x -760..2680, y -430..1510. The peephole needs about x 300..1620, y -120..1200. Add margin for camera moves.
- **Placing HUD on subjects.** `project(x, y, depth, cs, lens, ref_depth)` and `project_box(box, depth, cs, lens)` return
  where a layer point or box lands after the camera, lens and post moves. Use them to pin doorbell motion boxes and tags
  to people.

## 4. Grade and per-frame effects (`engine.post`)

- **Presets.** `Grade(name, **overrides)` takes one of: `night_blue`, `porch_warm`, `interior_dim`, `red_alert`,
  `phone_dark`, `ir_night`, `doorbell_night`, `face_close`, `neutral`. Each preset sets lifted, tinted blacks, a
  vignette (0.34 at r=0.8 on night grades), bloom (1.0 is the reference halo on lamps) and grain of 0.8 to 0.9 levels,
  which only dithers.
- **What blooms.** Only small features brighter than `bloom_thr` (about 236) bloom, so pale faces, eye whites and teeth
  never glow. Draw light cores in `#fff8ee` to `#ffffff`, and keep eye whites and teeth at or below `#f0f0f0`.
- **Changing a grade.** Use `g.with_(exposure=-0.3, vignette=0.3)`. For the climax creeping into red, use
  `g.lerp('red_alert', k)` or `post={'red': k}`.
- **`post={...}` keys.**
  - `exposure`: in stops.
  - `sat`: a multiplier.
  - `fade`: fades to black.
  - `white`: a white flash.
  - `dim`.
  - `red`.
  - `mix`: a pair, `(Grade, k)`.
  - `flash`: the result of `police_flash(t, strength, speed, mode='sweep'|'strobe')`.
  - `static`: a value from 0 to 1, for 2- to 6-frame scare flashes.
  - `glitch`: a value from 0 to 1.
  - `blur`: in design px, for rule-card backgrounds; use `{'blur': 6, 'dim': 0.35}`.
  - `vignette` and `bloom`: override the grade's values.
- **Police light in the scene.** `police_flash(t).light(xf)` returns red and blue intensities at a horizontal frame
  fraction. Use them so sets can light walls.

## 5. HUD (`engine.hud`)

HUD elements are drawn last and stay crisp. Pass `t` as the seconds since the element appeared. Text written `*like
this*` is drawn in the threat red.

```python
hud.caption(cv, text); hud.header(cv, 'RULE 2 OF 7', '12:36 AM')                  # v1 look and metrics
hud.rule_card(cv, 5, 'If you hear someone *calling* from the car, *do not answer*.', t)   # pop 0.07 s, types ~3 s
hud.rule_times(text)  # -> {'pop', 'line', 'type0', 'type1', 'end'}: ui_pop / typing SFX times
hud.tag(cv, 'NEVER OPEN UP', 960, 150, 'alert')         # 58 % W red box, hard cut (hold ~1.2 s)
hud.tag(cv, 'MICROPHONE', x, y, 'red', t)  # also 'white' (pop) and 'pill' / 'dark' (fade in 1 s)
hud.speech_bubble(cv, ["You haven't gotten", '*yours yet, have you?*'], x, y, t)
hud.waveform_panel(cv, x, y, w, h, 'SHOULDER RADIO', [{'label': 'PLAY 1', 'color': 'blue', 'seed': 1, 'progress': 0.6}], t, playhead=0.6)
hud.dispatch_panel(cv, x, y, 'DISPATCH  -  CALL 24-1187', ['Address: 144 Elm St'], t)
hud.phone(cv, 'calling'|'busy'|'incoming'|'connected'|'voicemail'|'emergency', t, name='MUM', x=760, y=560, scale=1.0)
hud.doorbell_hud(cv, t, name='FRONT DOOR', clock=(0, 36, 7), motion=project_box(...), ir=False, talk=False)
hud.bodycam_hud(cv, t, unit='UNIT 24-07', badge='4471')
```

## 6. Drawing (`engine.core`)

- **Kept from v1.** `col`, `mix`, `Pen` (`fill`, `line`, `shape`, `shade`, `glow`, `grad`, `wash`), `text`, `wrap`,
  `typeface`, `smooth`, `poly`, `rect`, `rrect`, `oval`, `inter`, `union`, `minus`.
- **Pen additions.**
  - `pen.linear(path, x0, y0, x1, y1, stops)` and `pen.radial(path, cx, cy, r, stops, sy=)`. Stops are `['#hex', ...]`
    or `[(pos, '#hex', alpha), ...]`.
  - `pen.texture(path, 'grunge'|'fabric'|'plaster'|'wood'|'asphalt'|'paper'|'skin', alpha, 'overlay'|'multiply'|...)`.
  - `pen.shadow(path, dx, dy, blur)`, `pen.rim(path, lx, ly, w, c, a)`, `pen.cone(x, y, w0, w1, h, c, a)`,
    `pen.dashed(path)` and `pen.ellipse_glow(...)`.
- **Other helpers.** `moved(path, dx, dy)`, `scaled(path, s)`, `ring`, `text_width`, `hud.rich_text` and `noise1`.
  `hash01` is deterministic randomness.
- **Style constants.** `LINE = '#1d1f26'` is the measured outline colour. Outlines are 7.5 to 9 design px on close-ups
  and 3 to 4.5 on wide shots. `SKIN` holds the pale palette and `SKIN_SHADE` its shadow.

## 7. Speed rules (measured at 2560x1440, one process)

**The spec scene.** Six layers, two DOF-blurred, plus the grade, police flash and HUD. Seconds per frame with OpenCV
using 4 threads, then 1 thread:

| lens | 4 threads | 1 thread |
|---|---|---|
| none | 0.12 | 0.15 |
| lens | 0.11 | 0.20 |
| doorbell | 0.16 | 0.23 |
| doorbell_ir | 0.19 | 0.24 |
| peephole | 0.11 | 0.14 |

The placeholder officer accounts for 9 to 23 ms of each figure. A full-frame cached layer costs about 20 ms at 2560 (35 ms
on the larger doorbell source). The doorbell HUD costs about 10 ms.

**What is fast.**
- Solid fills.
- `pen.linear` and `pen.radial` on an unrotated canvas: they are stretched-image blits, about 2 ms full frame. (A skia
  gradient shader takes 20 to 60 ms per full frame.)
- Cached layers: about 5 ns per covered pixel.

**What is slow; avoid it in uncached layers.**
- Big blurred shapes (`fill(blur=)` or `shadow` on a large path): about 90 ms per full frame.
- Non-normal blend modes (`screen`, `add`, `overlay` textures) over large areas: 25 to 80 ms.
- Rotated gradients and rotated image draws.
- Skia colour filters: the engine bakes `dim`, `tint` and IR gains for you.

Put anything static in a cached layer.

## 8. Render and test

```
python3 render.py --stills 12.5,40 --size 960x540
python3 render.py --clip 30 36 --size 960x540 [--audio mix_en.wav]
python3 render.py --workers 3 [--audio mix_en.wav]                 # full 2560x1440/60, slices -> picture.mp4 / film.mp4
python3 -m engine.demo --sheets --hud --clip --bench               # tests -> $S/pov2/tests/engine/
```

`render.py` uses `film.Film(timeline).frame(t, i)` when `film.py` exists, and `engine.demo.DemoFilm` until then. It
writes `progress_NN.json` for `tools/progress_page.py`, and finished slices resume.
