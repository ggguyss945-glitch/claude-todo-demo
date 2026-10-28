// "Too Much Gold": 29 shots timed to the narration (word starts from script/words.json).
import * as THREE from 'three';
import * as PR from './props.js';
import { Hose } from './chars.js';
import { gold, toon, mk } from './toon.js';
import * as TX from './stex.js';
import { V, cam, put, yawTo, faceTo, exprAt, handW, handL, handPt, local, idle, look, walk, cheer, hop, shrug, talk, ride, holdProp, camelWalk,
  clamp, lerp, prog, smooth, easeInOut, easeOut, hash } from './lib.js';
import { DS, VD, CP } from './sets.js';

const PI = Math.PI;
const D0 = DS.origin, V0 = VD.origin, C0 = CP.origin;
const dV = (x, y, z) => V(D0.x + x, y, z);
const vV = (x, y, z) => V(V0.x + x, y, z);
const cV = (x, y, z) => V(C0.x + x, y, z);
const easeOutQ = (x) => 1 - Math.pow(1 - clamp(x), 4);

export function addFilm(S, W) {
  const C = W.cast, A = W.anchors, scene = W.scene;
  const act = (o) => { scene.add(o); o.visible = false; W.actors.push(o); return o; };
  // coin pools (world space)
  const coins = (W.coins = {
    main: new PR.CoinPool(scene, 12000), fly: new PR.CoinPool(scene, 1200), silver: new PR.CoinPool(scene, 40, true),
    big: new PR.CoinPool(scene, 2, false, 2.4), flood: new PR.CoinPool(scene, 7000, false, 1.7), fall: new PR.CoinPool(scene, 900, false, 1.7),
  });
  const pouchA = act(PR.pouch('#8a2a2a')), pouchB = act(PR.pouch('#2a5a8a')), pouchC = act(PR.pouch('#6a3a8a', 0.8));
  const broom = act(PR.broom()), bowl = act(PR.bowl()), bread = act(PR.flatbread(0.12));
  const loaf = act(PR.loaf()); loaf.scale.setScalar(1.15);
  const ropeMat = toon('#a8865a');
  const rope = new Hose(0.012, ropeMat, 18, 5); act(rope.mesh);
  // gold chains for the merchants when they come back rich
  const bling = {};
  for (const k of ['spice', 'cloth', 'jewel', 'changer']) {
    const ch = C[k];
    bling[k] = { set visible(v) { ch.state.bling = v; } };
  }
  const royal = A.desert.camels[2];
  const camels = A.desert.camels;
  const M = A.market;
  const tallyBase = M.tallyBoard.material.map, tally12 = TX.tally(12);
  W.reset = (t) => {
    for (const k in bling) bling[k].visible = false;
    for (const p of Object.values(coins)) p.clear();
    for (const cm of camels) { Object.assign(cm.pose, { walk: null, neck: 0, headPitch: 0, headYaw: 0, chew: 0, lid: 0.55, sit: 0 }); }
    M.tallyBoard.material.map = tallyBase;
    M.balance.userData.set(0);
    A.camp.chest.userData.lid.rotation.x = 0; A.camp.chest.userData.outer.visible = true;
    M.cat.visible = true;
  };
  const people = [...C.town];
  const crowdExpr = ['joy', 'happy', 'surprised', 'laugh', 'grin', 'joy', 'happy', 'dazzled'];

  // ------------------------------------------------------------ S01 hook: gold thrown at the camera
  {
    const t0 = 0, t1 = 1.5;
    const camelP = V(0, 0, -3.3), camelYaw = -0.55;
    // hand points of the rider in world space (camel turned so its head clears the lens)
    const handW0 = (x) => V(x, 2.78, 0.45).applyAxisAngle(V(0, 1, 0), camelYaw).add(camelP);
    // each throw leaves the throwing hand and flies at the lens (camera is front-left of him)
    const throwsL = PR.throwCoins(34, 0.3, handW0(-0.42), V(0.75, 0.16, 1), 7.4, 0.8, 11, 1.6);
    const throwsR = PR.throwCoins(34, 0.86, handW0(0.42), V(0.6, 0.16, 1), 7.4, 0.8, 12, 1.6);
    const rain = PR.throwCoins(60, -0.6, V(0, 3.1, -3.0), V(0, 1, 0.4), 3.2, 3.4, 13, 1.0);
    S.push({ t0, t1, set: 'market', light: 'gold',
      cam: cam([[0, [1.3, 2.62, -0.7], [0.0, 2.72, -3.3], 48], [1.5, [0.95, 2.72, -1.35], [0.0, 2.78, -3.3], 44, easeOutQ]], { ap: 6, focus: [0, 2.8, -3.3], drift: 0.02, seed: 1 }),
      setup(w, t, camera) {
        royal.root.visible = true; royal.root.position.copy(camelP); royal.root.rotation.set(0, camelYaw, 0);
        royal.pose.neck = Math.sin(t * 1.5) * 0.04;
        royal.update(t); const m = C.musa; ride(m, royal);
        m.state.expr = t < 0.62 ? 'grin' : 'joy';
        // two big throws: wind up, fling toward the lens
        const th = (a) => { const k1 = smooth(prog(t, a - 0.28, a - 0.02)), k2 = easeOut(prog(t, a - 0.02, a + 0.14)); return [k1, k2]; };
        const [r1, r2] = th(0.34), [l1, l2] = th(0.9);
        // the arms fling outward and forward, never across his face
        handL(m, 'r', lerp(-0.27, -0.4, r1) - r2 * 0.1, lerp(0.7, 1.4, r1) - r2 * 0.12, lerp(0.05, -0.2, r1) + r2 * 0.75);
        handL(m, 'l', lerp(0.27, 0.4, l1) + l2 * 0.1, lerp(0.7, 1.4, l1) - l2 * 0.12, lerp(0.05, -0.2, l1) + l2 * 0.75);
        m.pose.lean = -0.08 * r1 + 0.12 * r2 - 0.08 * l1 + 0.12 * l2;
        look(m, camera.position, 0.85);
        coins.fly.flight(t, throwsL); coins.fly.flight(t, throwsR); coins.fly.flight(t, rain);
        coins.main.scatter(-2.6, 2.6, -7, 0.5, 260, 0.003, 21);
        // the crowd cheers around the camel
        const spots = [[-1.75, -2.2], [1.85, -2.0], [-2.4, -5.0], [2.2, -5.6], [-0.9, -7.3], [1.3, -7.7], [-2.7, -9.4], [2.6, -9.9]];
        spots.forEach(([x, z], i) => { const c = put(people[i], V(x, 0, z), yawTo(V(x, 0, z), V(0, 0, 1.5)) + (hash(i, 2) - 0.5) * 0.5, crowdExpr[i]); cheer(c, t, 0.8 + 0.2 * hash(i, 1)); idle(c, t); });
        put(C.att1, V(-1.15, 0, -3.8), 0.15, 'happy'); put(C.att2, V(1.2, 0, -4.0), -0.15, 'happy');
        for (const [a, L] of [[C.att1, 'r'], [C.att2, 'l']]) { handL(a, L, L === 'r' ? -0.3 : 0.3, 0.98, 0.18); const st = A.desert.staffs[a === C.att1 ? 0 : 1]; st.visible = true; st.position.copy(handPt(a, L)).add(V(0, -0.98, 0)); }
      } });
  }
  // ------------------------------------------------------------ S02 "that gold became worthless": swept out like dirt
  {
    const t0 = 1.5, t1 = 3.3;
    const mp = V(-2.75, 0, 0.5), yaw = PI / 2 - 0.42;
    const strokes = [[1.52, -2.62], [2.32, -2.12], [3.0, -1.62]];
    const tipAt = (t) => {
      let x = -2.62, y = 0;
      for (const [a, x0] of strokes) {
        if (t >= a) { const push = easeInOut(prog(t, a, a + 0.42)); const back = smooth(prog(t, a + 0.46, a + 0.78)); x = x0 + 0.7 * push - 0.45 * back; y = Math.sin(PI * prog(t, a + 0.46, a + 0.78)) * 0.06; }
      }
      return V(x, y, 0.62 + Math.sin(t * 3) * 0.04);
    };
    const front = (t) => { let f = -2.35; for (const [a, x0] of strokes) if (t >= a) f = Math.max(f, x0 + 0.27 + 0.7 * easeInOut(prog(t, a, a + 0.42))); return f; };
    const slide = [];
    for (const [a] of strokes) for (let i = 0; i < 7; i++) slide.push({ t0: a + 0.12 + i * 0.03, o: V(-2.3, 0.02, 0.6), v: V(1.6 + hash(a, i) * 1.4, 0.7 + hash(i, a) * 0.6, (hash(a + i, 3) - 0.5) * 1.4), r0: 0, spin: V(20 * hash(i, 1), 6, 12), seed: a * 10 + i });
    S.push({ t0, t1, set: 'market', light: 'gold',
      cam: cam([[t0, [-0.75, 1.15, 2.85], [-2.5, 0.88, 0.45], 46], [t1, [-0.95, 1.12, 2.6], [-2.5, 0.88, 0.45], 43]], { ap: 6, focus: [-2.7, 1.0, 0.5], drift: 0.008, seed: 2 }),
      setup(w, t) {
        const m = put(C.spice, mp, yaw, t < 2.45 ? 'bored' : 'unimpressed');
        idle(m, t, 0.6);
        m.pose.lean = 0.16;
        const tip = tipAt(t);
        // a short broom held low: the handle ends at his chest, never across his face
        const hands = local(m, 0.0, 0.86, 0.42);
        const dir = hands.clone().sub(tip).normalize();
        broom.visible = true; broom.scale.set(1, 0.78, 1); broom.position.copy(tip).add(V(0, 0.12, 0)); broom.quaternion.setFromUnitVectors(V(0, 1, 0), dir); broom.updateMatrixWorld(true);
        handW(m, 'l', tip.clone().addScaledVector(dir, 1.0)); handW(m, 'r', tip.clone().addScaledVector(dir, 0.7));
        look(m, tip.clone().add(V(0.3, 0, 0)), 0.6);
        const f = front(t);
        coins.main.heap(V(f + 0.18, 0, 0.62), 0.28, 0.07, 110, 31);
        coins.main.scatter(-2.5, f - 0.05, 0.4, 0.85, 14, 0.003, 32);
        coins.fly.flight(t, slide);
        [[-0.2, -4.5, 0.4], [1.6, -9, -0.3], [-1.4, -12, 0.2]].forEach(([x, z, y], i) => { const c = walk(people[i + 3], V(x, 0, z), V(x + 0.3, 0, z + 2.5), 1.0, 4.2, t); });
      } });
  }
  // ------------------------------------------------------------ caravan (desert)
  const CAR_V = 1.05;
  function caravan(t, dir, x0, tRef, o = {}) {
    const out = [];
    camels.forEach((cm, i) => {
      if (o.camels && !o.camels.includes(i)) return;
      const x = x0 - i * 5.0 * dir + dir * CAR_V * (t - tRef);
      camelWalk(cm, dV(x, 0, 0), dir > 0 ? PI / 2 : -PI / 2, t, CAR_V, i * 0.37);
      out.push(x);
    });
    const walkers = [C.att1, C.att2, C.att3, C.att4, ...C.caravan];
    walkers.forEach((p, k) => {
      if (o.people === false) return;
      const ci = k % 9, side = k % 2 ? 1 : -1;
      const x = x0 - ci * 5.0 * dir + dir * CAR_V * (t - tRef) + dir * (0.6 + (k > 8 ? -2.2 : 0.0));
      const z = side * (1.75 + (k > 8 ? 0.6 : 0));
      put(p, dV(x, 0, z), dir > 0 ? PI / 2 : -PI / 2, k % 3 ? 'neutral' : 'calm');
      const dist = x * dir;
      p.pose.walk = { phase: dist / 0.84 + k * 0.3, stride: 0.23, lift: 0.05 };
      p.pose.bob += Math.abs(Math.sin((dist / 0.84 + k * 0.3) * PI * 2)) * 0.025;
      if (k < 12) {
        const L = side < 0 ? 'l' : 'r';
        handL(p, L, L === 'r' ? -0.3 : 0.3, 0.98, 0.16);
        const st = A.desert.staffs[k]; st.visible = true; st.position.copy(handPt(p, L)).add(V(0, -0.98, 0));
      }
    });
    if (!o.noMusa) { royal.update(t); const m = C.musa; ride(m, royal); m.state.expr = 'proud'; idle(m, t, 0.5); handL(m, 'l', 0.3, 0.98, 0.32); handL(m, 'r', -0.3, 0.95, 0.3); }
    return out;
  }
  // ------------------------------------------------------------ S03 desert wide, the caravan and the pyramids
  S.push({ t0: 3.3, t1: 5.4, set: 'desert', light: 'sunrise', dissolve: 0.3, lightCentre: V(0, 0, 0),
    cam: cam([[3.3, [D0.x - 3, 6.8, 27], [D0.x + 1, 3.8, -40], 40], [5.4, [D0.x + 2, 5.6, 25], [D0.x + 4, 3.4, -40], 40]], { ap: 2, focus: [D0.x, 2, 0], drift: 0.03, seed: 3 }),
    setup(w, t) { caravan(t, 1, 12, 3.3); } });
  // ------------------------------------------------------------ S04 the king under his parasol
  S.push({ t0: 5.4, t1: 7.0, set: 'desert', light: 'sunrise', lightCentre: V(0, 0, 0),
    cam: (t) => { const x = 2 + CAR_V * (t - 3.3); return cam([[5.4, [D0.x + x + 1.7, 3.15, 2.35], [D0.x + x - 0.1, 3.05, -0.1], 38], [7.0, [D0.x + x + 1.3, 3.2, 2.2], [D0.x + x - 0.1, 3.1, -0.1], 36]], { ap: 10, focus: [D0.x + x, 3.1, 0], drift: 0.012, seed: 4 })(t); },
    setup(w, t) { caravan(t, 1, 12, 3.3); const m = C.musa; m.pose.headPitch -= 0.1; m.pose.headYaw += 0.35; m.state.expr = exprAt(t, [[0, 'proud'], [6.2, 'calm']]); m.state.look = [0.5, 0.1]; } });
  // ------------------------------------------------------------ S05 sixty thousand people (long lens down the line)
  S.push({ t0: 7.0, t1: 8.42, set: 'desert', light: 'sunrise', lightCentre: V(-10, 0, 0),
    cam: (t) => { const x = 12 + CAR_V * (t - 3.3); return cam([[7.0, [D0.x + x + 34, 2.6, 4.6], [D0.x + x - 14, 2.1, 0.3], 15], [8.42, [D0.x + x + 33, 2.7, 4.2], [D0.x + x - 14, 2.1, 0.2], 13.5]], { ap: 3, focus: [D0.x + x - 6, 2, 0], drift: 0.02, seed: 5 })(t); },
    setup(w, t) {
      caravan(t, 1, 12, 3.3);
      // more of his people further back, fading into the dust
      people.forEach((p, k) => { const x = 12 - 46 - k * 2.4 + CAR_V * (t - 3.3); const z = (k % 2 ? 1.6 : -1.6) + (k % 3) * 0.5; put(p, dV(x, 0, z), PI / 2); p.pose.walk = { phase: x / 0.84 + k, stride: 0.23, lift: 0.05 }; });
    } });
  // ------------------------------------------------------------ S06 camels carrying gold (tracking on the sacks)
  S.push({ t0: 8.42, t1: 10.12, set: 'desert', light: 'sunrise', lightCentre: V(-6, 0, 0),
    cam: (t) => { const x = 12 - 4 * 5 + CAR_V * (t - 3.3); return cam([[8.42, [D0.x + x + 0.55, 1.55, 7.6], [D0.x + x + 0.25, 1.25, 0], 42], [10.12, [D0.x + x + 0.25, 1.6, 7.1], [D0.x + x + 0.1, 1.27, 0], 40]], { ap: 5, focus: [D0.x + x, 1.3, 0.3], drift: 0.012, seed: 6 })(t); },
    setup(w, t) {
      caravan(t, 1, 12, 3.3, { noMusa: true });
      const x = 12 - 4 * 5 + CAR_V * (t - 3.3);
      // a coin bounces out of the sack on "gold" and drops into the sand
      coins.fly.flight(t, [{ t0: 9.55, o: dV(x + 0.05 + CAR_V * 0, 1.42, 0.62), v: V(CAR_V + 0.3, 1.6, 0.9), r0: 0.3, spin: V(14, 3, 9), seed: 61, s: 1.3 }]);
      coins.main.scatter(D0.x + x - 8, D0.x + x - 2, 0.3, 1.2, 6, 0.01, 62, 1.3);
    } });
  // ------------------------------------------------------------ S07 "doesn't just pay for things": a whole pouch for one roll of cloth
  {
    const mp = V(1.55, 0, 7.5), cp = V(2.45, 0, 7.4);
    S.push({ t0: 10.12, t1: 12.15, set: 'market', light: 'gold',
      cam: cam([[10.12, [2.05, 1.32, 10.7], [2.0, 1.12, 7.45], 46], [12.15, [2.02, 1.34, 10.3], [2.0, 1.14, 7.45], 43]], { ap: 6, focus: [2.0, 1.2, 7.45], seed: 7 }),
      setup(w, t) {
        const m = put(C.musa, mp, yawTo(mp, cp) - 0.75, 'happy'), c = put(C.cloth, cp, yawTo(cp, mp) + 0.75, 'neutral');
        idle(m, t); idle(c, t);
        // the merchant holds out his palm for one coin
        const k = smooth(prog(t, 10.2, 10.6));
        handL(c, 'l', lerp(0.27, 0.12, k), lerp(0.7, 1.0, k), lerp(0.05, 0.42, k));
        // the king puts a whole pouch in it
        const give = smooth(prog(t, 10.75, 11.3));
        const palm = handPt(c, 'l');
        const start = local(m, -0.25, 1.0, 0.3);
        const p = start.clone().lerp(palm.clone().add(V(0, 0.04, 0)), give);
        handW(m, 'r', p);
        pouchA.visible = true; pouchA.position.copy(t < 11.3 ? p : palm).add(V(0, -0.02 - (t > 11.3 ? 0.06 * Math.exp(-(t - 11.3) * 6) * Math.sin((t - 11.3) * 30) : 0), 0));
        if (t > 11.3) { c.pose.hands.l.y -= 0.05 * Math.exp(-(t - 11.3) * 4); handL(m, 'r', -0.27, 0.72, 0.08); }
        c.state.expr = exprAt(t, [[0, 'neutral'], [11.32, 'shocked'], [11.75, 'greedy']]);
        look(c, t < 11.3 ? m.head.getWorldPosition(V()) : palm, 1);
        look(m, c.head.getWorldPosition(V()), 0.8);
        // a few shoppers pass behind
        [[-0.5, 3], [0.8, -2], [-1.6, 0.5]].forEach(([x, z], i) => walk(people[i], V(x, 0, z), V(x + 0.2, 0, z - 3), 9.6, 13, t));
      } });
  }
  // ------------------------------------------------------------ S08 he hands out gold to everyone
  {
    const flights = [];
    for (let i = 0; i < 7; i++) flights.push(...PR.throwCoins(16, 12.2 + i * 0.22, V(0, 2.95, -5.6 + 0.6 * i * 0.22), V(i % 2 ? 1 : -1, 0.9, 0.3), 3.4, 1.1, 80 + i, 1.0));
    S.push({ t0: 12.15, t1: 13.84, set: 'market', light: 'gold', blur: () => 3,
      cam: cam([[12.15, [0.55, 3.5, 0.2], [0.0, 1.8, -6.2], 50], [13.84, [0.45, 3.9, 0.9], [0.0, 1.9, -5.6], 48]], { ap: 4, focus: [0, 2.4, -5.8], drift: 0.025, seed: 8 }),
      setup(w, t) {
        royal.root.visible = true; royal.root.position.set(0, 0, -6.0 + 0.6 * (t - 12.15)); royal.root.rotation.set(0, 0, 0);
        royal.pose.walk = { phase: t * 0.55, stride: 0.5 };
        royal.update(t); const m = C.musa; ride(m, royal); m.state.expr = 'joy';
        const sw = Math.sin(t * 13.8);
        handL(m, 'r', -0.42, 1.25 + 0.25 * Math.max(0, sw), 0.25); handL(m, 'l', 0.42, 1.25 + 0.25 * Math.max(0, -sw), 0.25);
        coins.fly.flight(t, flights);
        coins.main.scatter(-3, 3, -11, -1, 420, 0.003, 81);
        const spots = [[-1.8, -4.2], [1.9, -4.5], [-2.3, -7.0], [2.4, -7.4], [-1.5, -9.2], [1.6, -9.8], [-2.6, -2.6], [2.5, -2.2], [-0.8, -10.8], [0.9, -11.4], [-2.9, -11.8], [2.9, -12.5]];
        spots.forEach(([x, z], i) => { const c = put(people[i], V(x, 0, z), yawTo(V(x, 0, z), m.root.position) + (hash(i, 9) - 0.5) * 0.3, crowdExpr[i % 8]); cheer(c, t + i * 0.3, 1); });
        put(C.att3, V(-1.2, 0, -5.2 + 0.6 * (t - 12.15)), 0, 'happy'); put(C.att4, V(1.2, 0, -5.4 + 0.6 * (t - 12.15)), 0, 'happy');
        for (const a of [C.att3, C.att4]) a.pose.walk = { phase: t * 0.7, stride: 0.2, lift: 0.04 };
      } });
  }
  // ------------------------------------------------------------ S09 "Merchants."
  {
    const sp = V(-2.35, 0, -0.55);
    const toss = [{ t0: 13.5, o: V(0.4, 2.2, 0.6), v: V(-3.6, 2.0, -1.55), r0: 0, spin: V(3, 4, 2), seed: 91 }];
    S.push({ t0: 13.84, t1: 14.6, set: 'market', light: 'gold',
      cam: cam([[13.84, [-1.0, 1.45, 1.55], [-2.35, 1.3, -0.55], 44], [14.6, [-1.12, 1.46, 1.3], [-2.35, 1.32, -0.55], 41, easeOutQ]], { ap: 7, focus: [-2.35, 1.35, -0.55], seed: 9 }),
      setup(w, t) {
        const m = put(C.spice, sp, 0.6, exprAt(t, [[0, 'surprised'], [14.08, 'greedy']]));
        const catchK = smooth(prog(t, 13.84, 14.0));
        handL(m, 'l', 0.12, lerp(0.75, 1.02, catchK), lerp(0.1, 0.42, catchK)); handL(m, 'r', -0.12, lerp(0.75, 1.02, catchK), lerp(0.1, 0.42, catchK));
        const hp = handPt(m, 'l').add(handPt(m, 'r')).multiplyScalar(0.5);
        const k = clamp((t - 13.84) / 0.16);
        const fly = V(0.4, 2.2, 0.6).lerp(hp, easeOut(k)); fly.y += Math.sin(PI * k) * 0.25;
        pouchB.visible = true; pouchB.position.copy(t < 14.0 ? fly : hp.add(V(0, 0.02, 0))); pouchB.rotation.set(0, t * 2, 0.2);
        m.pose.lean = 0.08; idle(m, t);
        look(m, pouchB.position, 0.9);
        coins.main.heap(V(-2.0, 0, 0.3), 0.3, 0.08, 60, 92);
      } });
  }
  // ------------------------------------------------------------ S10 "Beggars."
  {
    const bp = V(2.95, 0, -16.9);
    const drops = [];
    for (let i = 0; i < 70; i++) drops.push({ t0: 14.45 + i * 0.009, o: V(2.62 + (hash(i, 1) - 0.5) * 0.3, 2.4 + hash(i, 2) * 0.6, -16.55 + (hash(i, 3) - 0.5) * 0.3), v: V((hash(i, 4) - 0.5) * 0.6, -1.0, (hash(i, 5) - 0.5) * 0.6), r0: hash(i, 6) * 3, spin: V(12, 5, 9), seed: 100 + i });
    S.push({ t0: 14.6, t1: 15.32, set: 'market', light: 'gold', blur: () => 4,
      cam: cam([[14.6, [1.45, 1.32, -14.85], [2.85, 1.05, -16.75], 44], [15.32, [1.55, 1.33, -15.0], [2.85, 1.07, -16.75], 41]], { ap: 7, focus: [2.85, 1.1, -16.75], seed: 10 }),
      setup(w, t) {
        const b = put(C.beggar, bp, yawTo(bp, V(1.45, 0, -14.85)), exprAt(t, [[0, 'shocked'], [14.95, 'joy']]));
        b.pose.lean = 0.18; idle(b, t, 0.5);
        handL(b, 'l', 0.13, 0.9, 0.36); handL(b, 'r', -0.13, 0.9, 0.36);
        const bw = handPt(b, 'l').add(handPt(b, 'r')).multiplyScalar(0.5).add(V(0, -0.02, 0));
        bowl.visible = true; bowl.position.copy(bw); bowl.rotation.set(0, 0, 0);
        const n = Math.floor(clamp((t - 14.6) / 0.5) * 40);
        coins.main.heap(bw.clone().add(V(0, 0.02, 0)), 0.11, 0.07, 6 + n, 101);
        coins.fly.flight(t, drops, 0);
        look(b, bw.clone().add(V(0, 0.2, 0)), 0.7);
      } });
  }
  // ------------------------------------------------------------ S11 "Kids."
  {
    const rain = [];
    for (let i = 0; i < 90; i++) rain.push({ t0: 14.9 + i * 0.012, o: V((hash(i, 1) - 0.5) * 3, 3.6 + hash(i, 2), -8.3 + (hash(i, 3) - 0.5) * 2), v: V(0, -0.5, 0), r0: hash(i, 4) * 3, spin: V(10, 8, 12), seed: 200 + i });
    S.push({ t0: 15.32, t1: 15.98, set: 'market', light: 'gold', blur: () => 4,
      cam: cam([[15.32, [0.22, 0.85, -5.35], [0.22, 0.8, -8.4], 54], [15.98, [0.24, 0.84, -5.6], [0.22, 0.82, -8.4], 52]], { ap: 6, focus: [0.22, 0.8, -8.3], drift: 0.02, seed: 11 }),
      setup(w, t) {
        [[C.kid1, -0.42, -8.35, 0], [C.kid2, 0.22, -8.05, 0.33], [C.kid3, 0.86, -8.45, 0.66]].forEach(([k, x, z, ph], i) => {
          const c = put(k, V(x, 0, z), (i - 1) * -0.25, i === 1 ? 'joy' : 'laugh'); hop(c, t, 2.6, 0.22, ph); cheer(c, t, 1);
        });
        coins.fly.flight(t, rain);
        coins.main.scatter(-1.6, 1.8, -9.4, -7.2, 120, 0.003, 201);
        [[-2.3, -10], [2.3, -10.5], [-1.2, -12]].forEach(([x, z], i) => { const c = put(people[i + 5], V(x, 0, z), 0.2, crowdExpr[i + 2]); cheer(c, t + i, 0.9); });
      } });
  }
  // ------------------------------------------------------------ S12 "The guy holding his camel."
  {
    const gp = V(0.95, 0, -1.4), cp = V(2.55, 0, -2.4);
    S.push({ t0: 15.98, t1: 17.56, set: 'market', light: 'gold',
      cam: cam([[15.98, [0.45, 1.62, 1.35], [1.45, 1.55, -1.95], 42], [17.56, [0.6, 1.66, 0.95], [1.5, 1.6, -1.95], 39]], { ap: 9, focus: [1.2, 1.6, -1.6], seed: 12 }),
      setup(w, t) {
        royal.root.visible = true; royal.root.position.copy(cp); royal.root.rotation.set(0, -PI / 2 - 0.35, 0);
        royal.pose.chew = 1; royal.pose.lid = 0.62;
        royal.pose.headYaw = lerp(0, 0.85, smooth(prog(t, 16.45, 16.85))); royal.pose.headPitch = 0.1;
        const g = put(C.camelguy, gp, -0.45, exprAt(t, [[0, 'confused'], [16.9, 'dazzled']]));
        idle(g, t);
        // left hand holds one coin up to his eyes, right hand holds the rope
        const k = smooth(prog(t, 16.0, 16.35));
        handL(g, 'l', lerp(0.27, 0.12, k), lerp(0.7, 1.5, k), lerp(0.05, 0.4, k));
        handL(g, 'r', -0.3, 0.88, 0.22);
        const cpos = handPt(g, 'l').add(V(0, 0.07, 0.02));
        coins.big.add(cpos, PI / 2, 0, 0.25 + Math.sin(t * 3) * 0.2, 0.8);
        look(g, cpos, 1);
        royal.update(t);
        const bridle = royal.head.localToWorld(V(0, -0.05, 0.25));
        const rh = handPt(g, 'r');
        const mid = rh.clone().add(bridle).multiplyScalar(0.5); mid.y -= 0.25;
        rope.mesh.visible = true; rope.update(rh, mid, bridle);
        coins.main.scatter(-1.5, 3, -4, 0.5, 120, 0.003, 121);
      } });
  }
  // ------------------------------------------------------------ S13 "Suddenly, Cairo is drowning in gold."
  {
    const rain = [];
    for (let i = 0; i < 260; i++) rain.push({ t0: 17.2 + hash(i, 1) * 2.3, o: V((hash(i, 2) - 0.5) * 6.5, 7 + hash(i, 3) * 3, -22 + hash(i, 4) * 24), v: V(0, -1, 0), r0: hash(i, 5) * 3, spin: V(10, 6, 8), seed: 300 + i });
    S.push({ t0: 17.56, t1: 19.7, set: 'market', light: 'gold', blur: () => 2,
      cam: cam([[17.56, [0.45, 2.0, 2.9], [0.0, 2.1, -10], 50], [19.7, [0.25, 8.6, 3.7], [0.0, 0.6, -12.5], 50]], { ap: 3, focus: [0, 1, -8], drift: 0.03, seed: 13 }),
      setup(w, t) {
        coins.main.scatter(-3.3, 3.3, -30, 3, 6500, 0.004, 301, 1.5);
        for (const [x, z, r] of [[-2.9, 0.4, 0.7], [2.9, -6.2, 0.75], [-2.9, -12.2, 0.8], [3.0, -1.6, 0.6], [3.0, -12.6, 0.7], [-3.0, -6.0, 0.65], [-3.0, -25, 0.8], [2.8, -24, 0.7], [0.3, -18, 0.6]]) coins.main.heap(V(x, 0, z), r, 0.42, 300, x * 7 + z, 1.4);
        coins.fly.flight(t, rain);
        const all = [...people, ...C.caravan.slice(0, 8), C.kid1, C.kid2, C.kid3, C.beggar, C.camelguy, C.baker, C.spice, C.cloth];
        all.forEach((c, i) => {
          const x = (i % 2 ? 1 : -1) * (0.6 + hash(i, 1) * 2.2), z = 3 - i * 1.15 - hash(i, 2) * 0.6;
          put(c, V(x, 0, z), (hash(i, 3) - 0.5) * 2, crowdExpr[i % 8]);
          cheer(c, t + i * 0.37, 0.7 + 0.3 * hash(i, 4));
          if (c.def.scale < 0.7) hop(c, t, 2.4, 0.18, hash(i, 5));
        });
        royal.root.visible = true; royal.root.position.set(0.2, 0, -10); royal.root.rotation.set(0, 0.2, 0);
        royal.update(t); const m = C.musa; ride(m, royal); m.state.expr = 'joy'; cheer(m, t, 0.8);
      } });
  }
  // ------------------------------------------------------------ S14 "Except, the shopkeepers start asking for more gold, for the same bread."
  {
    let drawnKey = '';
    const board = M.priceBoard;
    const coinIcon = (g, x, y) => { g.beginPath(); g.arc(x, y, 18, 0, PI * 2); g.lineWidth = 6; g.stroke(); g.beginPath(); g.arc(x, y, 7, 0, PI * 2); g.fill(); };
    const drawBoard = (strike, three) => {
      const key = strike.toFixed(2) + '|' + three.toFixed(2);
      if (key === drawnKey) return; drawnKey = key;
      board.userData.draw((g) => {
        g.font = 'bold 64px "Lilita One"'; g.textAlign = 'center'; g.fillText('BREAD', 256, 82);
        g.lineWidth = 5; g.beginPath(); g.moveTo(120, 100); g.lineTo(392, 100); g.stroke();
        g.font = '120px "Lilita One"'; g.fillText('1', 175, 230); coinIcon(g, 255, 195);
        if (strike > 0) { g.strokeStyle = '#ff6a5a'; g.lineWidth = 12; g.beginPath(); g.moveTo(130, 230); g.lineTo(130 + 170 * strike, 150 + 0 * strike); g.stroke(); g.strokeStyle = g.fillStyle = '#f4f0e4'; }
        if (three > 0) {
          g.save(); g.beginPath(); g.rect(0, 0, 330 * three + 150, 360); g.clip();
          g.fillStyle = '#ffe07a'; g.strokeStyle = '#ffe07a';
          g.font = '120px "Lilita One"'; g.fillText('3', 340, 320);
          for (let i = 0; i < 3; i++) coinIcon(g, 405 + i * 36, 290);
          g.restore();
        }
      });
    };
    S.push({ t0: 19.7, t1: 22.82, set: 'market', light: 'morning', dissolve: 0.35,
      cam: cam([[19.7, [2.62, 1.48, -7.42], [3.8, 1.45, -7.5], 30], [21.55, [2.55, 1.49, -7.4], [3.8, 1.45, -7.5], 28], [22.6, [1.6, 1.45, -4.2], [4.5, 1.3, -6.65], 46]], { ap: 7, focusFn: (t, p) => (t < 21.6 ? 1.25 : 3.8), seed: 14 }),
      setup(w, t) {
        drawBoard(smooth(prog(t, 20.95, 21.35)), smooth(prog(t, 21.35, 21.85)));
        const b = put(C.baker, V(4.78, 0, -6.35), -PI / 2 - 0.3, 'smug'); idle(b, t);
        const pk = smooth(prog(t, 20.9, 21.3)) * (1 - smooth(prog(t, 21.9, 22.3)));
        handL(b, 'r', lerp(-0.27, -0.2, pk), lerp(0.7, 1.32, pk), lerp(0.05, 0.42, pk));
        [[-1.5, -2], [0.8, -12]].forEach(([x, z], i) => walk(people[i + 6], V(x, 0, z), V(x, 0, z - 3), 19.5, 23, t));
      } });
  }
  // ------------------------------------------------------------ S15 "The baker just shrugs."
  S.push({ t0: 22.82, t1: 24.12, set: 'market', light: 'morning',
    cam: cam([[22.82, [2.2, 1.45, -5.95], [4.7, 1.38, -6.4], 42], [24.12, [2.4, 1.46, -6.0], [4.7, 1.4, -6.4], 39]], { ap: 7, focus: [4.7, 1.4, -6.35], seed: 15 }),
    setup(w, t) {
      const b = put(C.baker, V(4.78, 0, -6.35), -PI / 2 + 0.15, 'shrug'); idle(b, t);
      shrug(b, smooth(prog(t, 23.45, 23.85)) * (1 - 0.3 * smooth(prog(t, 23.95, 24.1))));
    } });
  // ------------------------------------------------------------ S16 baker: "Everyone's got gold now, my friend!"
  S.push({ t0: 24.12, t1: 26.2, set: 'market', light: 'morning',
    cam: cam([[24.12, [2.3, 1.42, -7.05], [4.7, 1.36, -6.4], 42], [26.2, [2.55, 1.43, -6.95], [4.7, 1.38, -6.4], 39]], { ap: 7, focus: [4.7, 1.4, -6.4], seed: 16 }),
    setup(w, t) {
      const b = put(C.baker, V(4.75, 0, -6.35), -PI / 2 - 0.12, 'grin'); idle(b, t, 1.2);
      b.pose.lean = 0.16; talk(b, w, 'baker', t);
      handL(b, 'l', 0.36, 1.15, 0.35);
      const sw = Math.sin(t * 5) * 0.06;
      handL(b, 'r', -0.38, 1.25 + sw, 0.32);
      holdProp(bread, b, 'r', V(0, 0.06, 0), [PI / 2 - 0.3, 0, 0.3]);
    } });
  // ------------------------------------------------------------ S17 "Even the money changers start giving less for every coin."
  {
    const bal = M.balance;
    S.push({ t0: 26.2, t1: 28.98, set: 'market', light: 'morning',
      cam: cam([[26.2, [-1.45, 1.38, -14.75], [-3.95, 1.0, -12.3], 46], [26.8, [-1.62, 1.33, -14.5], [-3.9, 1.0, -12.4], 44], [27.45, [-2.45, 1.3, -13.85], [-4.2, 1.2, -12.49], 44], [27.95, [-2.47, 1.3, -13.87], [-4.2, 1.2, -12.49], 43], [28.7, [-2.5, 1.42, -13.5], [-4.55, 1.38, -12.5], 44]], { ap: 7, focusFn: (t) => (t < 26.9 ? 3.3 : t < 28.0 ? 1.95 : 2.6), seed: 17 }),
      setup(w, t) {
        const c = put(C.changer, V(-4.72, 0, -12.5), PI / 2 - 0.35, exprAt(t, [[0, 'neutral'], [27.75, 'smug']])); idle(c, t, 0.7);
        const cu = put(people[3], V(-2.85, 0, -11.95), -PI / 2 - 0.35, exprAt(t, [[0, 'neutral'], [28.0, 'worried']])); idle(cu, t);
        // how many silver coins on the pan: 3, then the changer takes one back
        const nS = t < 26.85 ? 0 : t < 27.15 ? 1 : t < 27.45 ? 2 : t < 27.85 ? 3 : 2;
        const goldOn = t > 26.45;
        const target = (goldOn ? 1 : 0) * 0.26 - nS * 0.075;
        const ang = target + Math.sin((t - 26) * 9) * 0.02 * Math.exp(-((t - (nS === 2 && t > 27.85 ? 27.85 : 26.45)) * 3));
        bal.userData.set(clamp(ang, -0.3, 0.3));
        bal.updateMatrixWorld(true);
        const [pA, pB] = bal.userData.pans.map((p) => p.pan.getWorldPosition(V()));
        // customer's gold coin (left pan), changer's silver coins (right pan)
        const gk = smooth(prog(t, 26.2, 26.45));
        const gHand = local(cu, -0.05, 1.05, 0.45);
        handW(cu, 'r', gk < 1 ? gHand.clone().lerp(pA.clone().add(V(0, 0.06, 0)), gk) : local(cu, -0.27, 0.72, 0.05));
        coins.main.add(gk < 1 ? gHand.clone().lerp(pA, gk).add(V(0, 0.03, 0)) : pA.clone().add(V(0, 0.006, 0)), 0, 0.3, 0, 1);
        for (let i = 0; i < nS; i++) coins.silver.add(pB.clone().add(V(0, 0.006 + i * 0.0065, 0)), 0, i, 0, 1);
        const putK = (t > 26.55 && t < 27.6) ? Math.abs(Math.sin((t - 26.55) * PI / 0.3)) : 0;
        handW(c, 'l', pB.clone().add(V(0, 0.08 + 0.1 * (1 - putK), 0.0)).lerp(local(c, 0.27, 0.72, 0.05), t > 27.6 && t < 27.8 ? 1 : 0));
        if (t > 27.85) { const tk = smooth(prog(t, 27.85, 28.15)); const hp = pB.clone().add(V(0.0, 0.09, 0)).lerp(local(c, 0.2, 1.0, 0.25), tk); handW(c, 'l', hp); coins.silver.add(hp.clone().add(V(0, 0.02, 0)), 0.3, 0, 0, 1); }
        look(c, t < 28.0 ? pB : V(-2.5, 1.45, -13.5), 0.9);
        look(cu, pA, 0.8);
        if (t > 26.8) cu.root.visible = false; // out of shot once the camera pushes in on the scale
      } });
  }
  // ------------------------------------------------------------ S18 "So how do you ruin a city," (a man sunk to the waist in gold, holding up one loaf)
  {
    const bp = V(0.6, 0, -14.5);
    S.push({ t0: 28.98, t1: 30.34, set: 'market', light: 'morning',
      cam: cam([[28.98, [1.5, 1.05, -12.25], [0.6, 0.78, -14.5], 44], [30.34, [1.35, 1.0, -12.75], [0.6, 0.8, -14.5], 40]], { ap: 6, focus: [0.6, 0.9, -14.5], seed: 18 }),
      setup(w, t, camera) {
        coins.main.heap(bp, 1.15, 0.62, 1100, 181, 1.35);
        coins.main.scatter(-3.2, 3.2, -19.5, -11.0, 700, 0.004, 182, 1.4);
        for (const [x, z] of [[-1.7, -17.2], [2.1, -18.4]]) coins.main.heap(V(x, 0, z), 0.8, 0.5, 450, x * 13 + z, 1.35);
        const m = put(people[3], bp.clone().add(V(0, -0.52, 0)), yawTo(bp, camera.position), exprAt(t, [[0, 'confused'], [29.75, 'worried']]));
        idle(m, t);
        const up = smooth(prog(t, 29.0, 29.35));
        handL(m, 'r', -0.36, lerp(0.95, 1.62, up), 0.18); handL(m, 'l', 0.36, 1.0 + 0.08 * Math.sin(t * 4), 0.2);
        holdProp(loaf, m, 'r', V(0, 0.09, 0), [0.2, 0.4, 0.1]);
        look(m, t < 29.7 ? loaf.position : camera.position, 0.9);
        [[-1.7, -17.2, 'worried'], [2.1, -18.4, 'confused']].forEach(([x, z, e], i) => { const c = put(people[8 + i], V(x, -0.4, z), yawTo(V(x, 0, z), camera.position), e); idle(c, t); shrug(c, 0.6 + 0.4 * Math.sin(t * 2 + i)); });
      } });
  }
  // ------------------------------------------------------------ S19 "by giving it money?" (a coin in the dirt, stepped over)
  S.push({ t0: 30.34, t1: 31.6, set: 'market', light: 'morning',
    cam: cam([[30.34, [0.12, 0.1, -9.62], [0.42, 0.06, -10.55], 52], [31.6, [0.14, 0.11, -9.7], [0.42, 0.06, -10.55], 50]], { ap: 16, focus: [0.42, 0.02, -10.5], drift: 0.004, seed: 19 }),
    setup(w, t) {
      coins.big.add(V(0.42, 0.012, -10.52), 0.08, 0.6, 0.03, 0.75);
      coins.main.scatter(-1.5, 2, -13, -10.8, 40, 0.003, 191);
      const g = walk(C.camelguy, V(-1.6, 0, -10.45), V(2.1, 0, -10.6), 30.25, 31.8, t, { stride: 0.55 }); C.camelguy.state.expr = 'bored';
      walk(people[9], V(2.6, 0, -12.6), V(-1.8, 0, -12.2), 29.8, 32.2, t);
      walk(people[2], V(-2.2, 0, -13.6), V(2.4, 0, -13.9), 29.6, 32.4, t);
    } });
  // ------------------------------------------------------------ S20 "Well, gold is only valuable because it's rare." (one coin on a pedestal)
  S.push({ t0: 31.6, t1: 33.84, set: 'void', dissolve: 0.25, beam: 0.16,
    cam: cam([[31.6, [V0.x + 0.35, 1.72, 3.2], [V0.x, 1.4, 0], 36], [33.84, [V0.x + 0.12, 1.52, 1.55], [V0.x, 1.42, 0], 34]], { ap: 9, focus: [V0.x, 1.42, 0], drift: 0.006, seed: 20 }),
    setup(w, t) { coins.big.add(vV(0, 1.325 + 0.075, 0), PI / 2, 0, t * 0.7, 1); } });
  // ------------------------------------------------------------ S21 "Flood a city with it, and it's just shiny metal."
  {
    const fall = [];
    for (let i = 0; i < 850; i++) {
      const a = hash(i, 1) * PI * 2, r = Math.sqrt(hash(i, 2)) * 2.2;
      fall.push({ t0: 33.72 + hash(i, 3) * 2.0, o: vV(Math.cos(a) * r * 0.6, 6 + hash(i, 4) * 2.5, Math.sin(a) * r * 0.6), v: V(Math.cos(a) * 0.4, -2, Math.sin(a) * 0.4), r0: hash(i, 5) * 3, spin: V(9, 7, 11), seed: 400 + i, s: 1 });
    }
    S.push({ t0: 33.84, t1: 35.86, set: 'void', beam: 0.16, blur: () => 3,
      cam: cam([[33.84, [V0.x + 0.12, 1.52, 1.55], [V0.x, 1.42, 0], 34], [35.86, [V0.x + 1.0, 3.6, 6.8], [V0.x, 0.9, 0], 44, easeInOut]], { ap: 6, focus: [V0.x, 1.2, 0], drift: 0.01, seed: 21 }),
      setup(w, t) {
        const k = smooth(prog(t, 34.0, 35.4));
        const h = 1.55 * k, r = 0.45 + 2.6 * k;
        if (t < 35.1) coins.big.add(vV(0, 1.4 + 0.0, 0), PI / 2, 0, t * 0.7, 1);
        if (k > 0) coins.flood.heap(vV(0, 0, 0), r, h, Math.floor(400 + 6400 * k), 411, 1);
        coins.fall.flight(t, fall, 0);
      } });
  }
  // ------------------------------------------------------------ S22 "Twelve years later, Cairo's gold still hadn't recovered."
  S.push({ t0: 35.86, t1: 38.62, set: 'market', light: 'morning', dissolve: 0.3,
    cam: cam([[35.86, [-2.55, 1.62, -11.55], [-4.62, 1.62, -12.55], 40], [38.62, [-2.85, 1.65, -11.9], [-4.65, 1.65, -12.6], 36]], { ap: 8, focus: [-4.6, 1.65, -12.5], seed: 22 }),
    setup(w, t) {
      M.tallyBoard.material.map = tally12;
      const c = put(C.changerOld, V(-4.72, 0, -12.5), PI / 2 - 0.15, 'unimpressed');
      idle(c, t, 0.5);
      c.pose.headYaw += Math.sin(prog(t, 37.1, 38.3) * PI * 3) * 0.22 * (t > 37.1 && t < 38.3 ? 1 : 0);
      c.pose.squash *= 1 - 0.03 * Math.sin(prog(t, 36.3, 37.0) * PI);
      handL(c, 'l', 0.2, 0.93, 0.42); handL(c, 'r', -0.2, 0.93, 0.42);
      M.balance.userData.set(0.18);
      M.balance.updateMatrixWorld(true);
      const [pA, pB] = M.balance.userData.pans.map((p) => p.pan.getWorldPosition(V()));
      coins.main.add(pA.clone().add(V(0, 0.006, 0)), 0, 0.3, 0, 1);
      for (let i = 0; i < 2; i++) coins.silver.add(pB.clone().add(V(0, 0.006 + i * 0.0065, 0)), 0, i, 0, 1);
    } });
  // ------------------------------------------------------------ S23 "But here's the best part." (sunset, the caravan heads home)
  S.push({ t0: 38.62, t1: 39.94, set: 'desert', light: 'sunset', dissolve: 0.3, lightCentre: V(-8, 0, 0),
    cam: cam([[38.62, [D0.x + 16, 2.6, 7.5], [D0.x - 6, 2.0, -2], 40], [39.94, [D0.x + 15, 2.75, 7.4], [D0.x - 6, 2.1, -2], 38]], { ap: 3, focus: [D0.x + 6, 2, 0], drift: 0.02, seed: 23 }),
    setup(w, t) { caravan(t, -1, 4, 38.62); } });
  // ------------------------------------------------------------ S24 "On the way home, the richest king on Earth," (he opens his treasure chest)
  {
    const chest = A.camp.chest;
    const stand = () => chest.localToWorld(V(0, 0, -0.47));
    S.push({ t0: 39.94, t1: 41.92, set: 'camp', dissolve: 0.3,
      cam: cam([[39.94, [C0.x + 1.4, 1.02, 4.4], [C0.x + 1.0, 1.02, 0.0], 42], [41.92, [C0.x + 1.28, 1.04, 3.7], [C0.x + 1.0, 1.06, 0.0], 40]], { ap: 6, focus: [C0.x + 1.0, 1.1, 0.0], drift: 0.012, seed: 24 }),
      setup(w, t) {
        chest.updateMatrixWorld(true);
        const m = put(C.musa, stand(), chest.rotation.y, exprAt(t, [[0, 'proud'], [40.55, 'grin'], [41.3, 'joy']]));
        idle(m, t, 0.6);
        const lift = smooth(prog(t, 40.55, 41.45));
        chest.userData.lid.rotation.x = -1.3 * lift;
        m.pose.lean = 0.36 - 0.12 * lift;
        chest.updateMatrixWorld(true);
        for (const [L, x] of [['l', 0.36], ['r', -0.36]]) handW(m, L, chest.userData.lid.localToWorld(V(x, 0.03, 0.46)));
        // his people warm their hands at the fire behind him
        put(C.att1, cV(-0.55, 0, -2.45), 0.7, 'happy'); put(C.att2, cV(0.95, 0, -2.7), -0.6, 'calm');
        for (const a of [C.att1, C.att2]) { idle(a, t); handL(a, 'l', 0.14, 0.9, 0.3); handL(a, 'r', -0.14, 0.9, 0.3); }
      } });
  }
  // ------------------------------------------------------------ S25 "runs out of money." (inside the empty chest: a moth flies out)
  {
    const chest = A.camp.chest;
    S.push({ t0: 41.92, t1: 43.2, set: 'camp',
      cam: (t) => { chest.updateMatrixWorld(true); const p = chest.localToWorld(V(0.02, 0.1, 0.06)); const l = chest.localToWorld(V(0, 1.5, -0.1)); const c = cam([[41.92, p.toArray(), l.toArray(), 64], [43.2, p.toArray(), l.clone().add(V(0, 0.05, 0)).toArray(), 60]], { ap: 4, focus: l.toArray(), drift: 0.01, seed: 25 })(t); c.near = 0.02; return c; },
      setup(w, t) {
        chest.userData.lid.rotation.x = -1.3;
        chest.userData.outer.visible = false; // the camera sits inside the box
        chest.updateMatrixWorld(true);
        const m = put(C.musa, chest.localToWorld(V(0, 0, -0.47)), chest.rotation.y, exprAt(t, [[0, 'surprised'], [42.25, 'shocked']]));
        m.pose.lean = 0.42; idle(m, t, 0.4);
        handW(m, 'l', chest.localToWorld(V(0.34, 0.45, -0.12))); handW(m, 'r', chest.localToWorld(V(-0.34, 0.45, -0.12)));
        // the moth flutters up out of the chest, past his nose
        const k = prog(t, 42.0, 43.2);
        const mp = chest.localToWorld(V(Math.sin(k * 9) * 0.12, 0.15 + k * 1.6, 0.05 - k * 0.1 + Math.cos(k * 7) * 0.06));
        A.camp.moth.visible = true; A.camp.moth.position.copy(mp); A.camp.moth.rotation.set(-0.6, k * 4, Math.sin(k * 12) * 0.4); A.camp.moth.userData.flap(t);
        look(m, mp, 1);
      } });
  }
  // ------------------------------------------------------------ S26 "So he goes back to the same merchants he showered with gold,"
  const MERCH = [[C.jewel, V(-2.25, 0, 1.15)], [C.spice, V(-2.0, 0, -0.45)], [C.cloth, V(-1.75, 0, -2.0)], [C.changer, V(-1.95, 0, -3.5)]];
  const merchants = (t, expr, o = {}) => {
    MERCH.forEach(([c, p], i) => {
      put(c, p, yawTo(p, o.lookAt || V(0.4, 0, 0.5)), typeof expr === 'function' ? expr(i, t) : expr);
      bling[c.name].visible = true; idle(c, t);
      handL(c, 'l', 0.1, 0.84, 0.3); handL(c, 'r', -0.1, 0.84, 0.3);
    });
    for (const [x, z, r, h] of [[-3.0, 0.3, 0.55, 0.45], [-2.9, -1.6, 0.6, 0.55], [-2.95, -3.1, 0.5, 0.4], [-3.1, 1.9, 0.5, 0.42]]) coins.main.heap(V(x, 0, z), r, h, 420, x * 11 + z);
  };
  S.push({ t0: 43.2, t1: 45.76, set: 'market', light: 'day', shafts: 0.2, dissolve: 0.25,
    cam: cam([[43.2, [1.75, 1.45, 1.45], [-1.8, 1.1, -1.0], 46], [45.76, [1.6, 1.44, 1.3], [-1.8, 1.1, -1.0], 44]], { ap: 6, focus: [-1.9, 1.2, -1.0], seed: 26 }),
    setup(w, t) {
      merchants(t, 'smug');
      walk(C.musa, V(2.7, 0, 0.15), V(0.45, 0, 0.55), 43.3, 45.4, t, { ease: easeInOut });
      C.musa.state.expr = 'sheepish';
      people.slice(4, 8).forEach((c, i) => walk(c, V(1.6 + i * 0.3, 0, -6 - i * 2), V(1.2, 0, -10 - i * 2), 42.8, 46, t));
    } });
  // ------------------------------------------------------------ S27 Musa: "Hey. Remember me?"
  S.push({ t0: 45.76, t1: 47.08, set: 'market', light: 'day', shafts: 0.2,
    cam: cam([[45.76, [-2.0, 1.38, 0.85], [0.45, 1.22, 0.55], 46], [47.08, [-1.75, 1.39, 0.82], [0.45, 1.24, 0.55], 43]], { ap: 6, focus: [0.45, 1.3, 0.55], seed: 27 }),
    setup(w, t) {
      merchants(t, 'smug');
      const m = put(C.musa, V(0.45, 0, 0.55), yawTo(V(0.45, 0, 0.55), V(-2.0, 0, 0.85)) + 0.12, 'sheepish');
      idle(m, t); talk(m, w, 'musa', t);
      const wave = smooth(prog(t, 45.8, 46.05));
      handL(m, 'r', lerp(-0.27, -0.36, wave) + Math.sin(t * 12) * 0.05 * wave, lerp(0.7, 1.5, wave), lerp(0.05, 0.22, wave));
      handL(m, 'l', 0.22, 0.95, 0.28);
      m.pose.headRoll += 0.1; m.pose.lean = -0.04;
    } });
  // ------------------------------------------------------------ S28 "And they lend it to him."
  S.push({ t0: 47.08, t1: 48.3, set: 'market', light: 'day', shafts: 0.2,
    cam: cam([[47.08, [-0.9, 1.42, 3.35], [-0.95, 1.12, -0.45], 46], [48.3, [-0.92, 1.43, 3.05], [-0.95, 1.14, -0.45], 44]], { ap: 6, focus: [-0.95, 1.25, -0.45], seed: 28 }),
    setup(w, t) {
      merchants(t, (i) => (i === 1 ? 'greedy' : 'smug'));
      C.jewel.root.visible = false;
      const sp = C.spice; put(sp, V(-1.45, 0, -0.4), 1.0, 'greedy');
      const m = put(C.musa, V(-0.45, 0, -0.55), -0.8, exprAt(t, [[0, 'sheepish'], [47.75, 'happy']]));
      idle(m, t);
      const reach = smooth(prog(t, 47.1, 47.5));
      const meet = V(-0.97, 1.05, -0.38);
      handW(sp, 'r', local(sp, -0.2, 0.95, 0.35).lerp(meet, reach * (t < 47.8 ? 1 : 1 - smooth(prog(t, 47.8, 48.1)))));
      handW(m, 'l', local(m, 0.27, 0.72, 0.1).lerp(meet.clone().add(V(0.02, -0.05, 0)), smooth(prog(t, 47.35, 47.7))));
      const owner = t < 47.72 ? [sp, 'r'] : [m, 'l'];
      holdProp(pouchC, owner[0], owner[1], V(0, -0.03, 0));
      look(sp, m.head.getWorldPosition(V()), 1); look(m, pouchC.position, 0.7);
    } });
  // ------------------------------------------------------------ S29 "Because now, they're the ones with all the gold." (and a coin flips into the lens: loop)
  {
    const camEnd = V(1.8, 2.3, 3.5);
    const flip = [{ t0: 50.25, o: V(-1.3, 1.3, -0.6), v: V(4.1, 4.6, 5.4), r0: 0, spin: V(18, 2, 6), seed: 991, s: 1.4 }];
    const GROUP = [[C.spice, V(-1.3, 0, -0.85), 'laugh'], [C.jewel, V(-1.45, 0, 0.05), 'laugh'], [C.cloth, V(-2.05, 0, -0.32), 'laugh'], [C.changer, V(-2.2, 0, -1.1), 'grin']];
    S.push({ t0: 48.3, t1: 51.0, set: 'market', light: 'day', shafts: 0.2, blur: (t) => (t > 50.2 ? 6 : 0),
      cam: cam([[48.3, [1.1, 1.42, -0.2], [-1.8, 1.25, -0.42], 54], [49.7, [1.25, 1.44, -0.12], [-1.8, 1.25, -0.42], 52], [50.3, camEnd.toArray(), [-1.5, 1.15, -0.9], 50], [51.0, [1.85, 2.32, 3.58], [-1.5, 1.18, -0.9], 50]], { ap: 6, focusFn: (t) => (t < 49.9 ? 2.9 : 4.6), drift: 0.015, seed: 29 }),
      setup(w, t, camera) {
        GROUP.forEach(([c, p, e], i) => {
          put(c, p, yawTo(p, V(0.6, 0, -0.3)) + (i % 2 ? -0.1 : 0.1), e);
          bling[c.name].visible = true; idle(c, t, 1.3);
          c.pose.bob += Math.abs(Math.sin(t * 8.5 + i * 1.3)) * 0.035; c.pose.headPitch -= 0.12 + 0.05 * Math.sin(t * 8.5 + i);
          c.pose.lean = -0.06; c.pose.side += Math.sin(t * 4 + i) * 0.04;
          handL(c, 'l', 0.2, 0.86 + 0.05 * Math.sin(t * 8 + i), 0.24); handL(c, 'r', -0.2, 0.86 + 0.05 * Math.sin(t * 8 + i + 1), 0.24);
        });
        for (const [x, z, r, h] of [[-3.0, 0.3, 0.6, 0.5], [-2.95, -1.6, 0.65, 0.6], [-3.05, -3.1, 0.55, 0.45], [-3.1, 1.9, 0.55, 0.45]]) coins.main.heap(V(x, 0, z), r, h, 420, x * 11 + z, 1.3);
        const m = put(C.musa, V(0.15, 0, 1.25), yawTo(V(0.15, 0, 1.25), V(-1.7, 0, -0.5)), 'sheepish');
        idle(m, t); handL(m, 'l', 0.18, 0.9, 0.28);
        holdProp(pouchC, m, 'l', V(0, -0.03, 0));
        coins.fly.flight(t, flip);
        const sp = C.spice; if (t > 50.0) { const k = smooth(prog(t, 50.0, 50.25)); handL(sp, 'r', lerp(-0.2, -0.36, k), lerp(0.86, 1.3, k), lerp(0.24, 0.4, k)); }
      } });
  }
}
