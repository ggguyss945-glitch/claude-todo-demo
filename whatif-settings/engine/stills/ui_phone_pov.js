// Phone POV style frame (S00-L001): Sam's right hand holds the phone, thumb on the Dog size slider; behind it, on the
// street, Kevin's dog Tiny has grown to the size of a house. arg: 'cap' adds the POV caption at 92% H,
// 'v<0..1>' sets the slider (e.g. v0.4), 'night' tries the bedtime glow variant.
import { phone, dogSizeScreen, appScreen, phonePoint, brightnessScreen } from '../ui2.js';
import { street, STREET, wrap } from '../sets.js';
import { toon } from '../cast.js';
import { resetDefs, defsSvg } from '../style.js';
import { caption, CAP_Y } from '../caption.js';
import { sparkles, speedLines } from '../fx.js';
import { contact, Defs, g, rect, f } from '../ui_style.js';
import { tapRing } from '../ui.js';

const W = 1920, H = 1080;
function shot(set, inserts = [], cam = {}) {
  const out = [];
  for (const l of set.layers) {
    out.push(l);
    for (const i of inserts) if (i.after === l.name) out.push({ name: 'ins', depth: i.depth ?? 1, svg: i.svg });
  }
  const z = cam.z ?? 1, cx = cam.x || 0, cy = cam.y || 0;
  return out.map((l) => (l.depth === 0 ? l.svg : `<g transform="translate(960 540) scale(${z}) translate(${-960 - cx * l.depth} ${-540 - cy * l.depth})">${l.svg}</g>`)).join('');
}

export default (arg = '') => {
  const vm = /v([0-9.]+)/.exec(arg || ''), v = vm ? +vm[1] : 0.8;
  resetDefs();
  // background: the street, framed on Kevin's lawn so Tiny sits left of the phone
  const set = street({ split: true, liveTree: 'kevin' });
  const T = { ...STREET.tiny, x: 1090 }, s = T.s0 + (T.s1 - T.s0) * v;
  const dog = contact(T.x, T.y + 4, 120 * s, 14 * s, 0.25) + toon('tiny', { x: T.x, y: T.y, s, lod: s, face: v > 0.5 ? 'excited' : 'happy', pose: { wag: 0.6 } });
  const cam = { x: 600, y: 40, z: 1.22 };
  let bg = shot(set, [{ after: 'yard', depth: 0.75, svg: defsSvg() + dog }], cam);   // the house-size dog stands in front of the yard props
  // growth sparkles round the dog (screen space)
  const dx = 960 + cam.z * (T.x - 960 - cam.x * 0.75), dy = 540 + cam.z * (T.y - 540 - cam.y * 0.75);
  bg += sparkles({ x: dx - 260, y: dy - 420 * s * 0.6, w: 520, h: 360 * s * 0.7, count: 12, seed: 4, t: 0.42, size: 30 });
  // close-up depth: the far street softens a touch (frame-sized filter, outside any <use>)
  const d = new Defs();
  const soft = d.blur(1.8, 0.02);
  let out = d + g(bg, { filter: soft });
  // the phone, right of centre, tilted toward Sam
  const P = { x: 1370, y: 560, s: 0.58, rot: -8 };
  const night = (arg || '').includes('night');
  const scr = night ? brightnessScreen({ v: 0.25, grab: 1, t: 0.3 }) : dogSizeScreen({ v, grab: 1 });
  const [kx, ky] = scr.knob;
  out += phone({ ...P, screen: appScreen({ time: night ? '2:13' : '4:05', crumb: night ? 'Settings › {Display|purple}' : 'Settings › {World|purple} › {Pets|pink}', content: scr.svg }), thumb: { x: kx + 14, y: ky + 26, press: 0.7 }, glow: night ? 0.8 : 0 });
  if ((arg || '').includes('cap')) out += caption('{SETTINGS|cyan} menu?', { y: CAP_Y.pov }, 1);
  return { w: W, h: H, svg: wrap(out) };
};
