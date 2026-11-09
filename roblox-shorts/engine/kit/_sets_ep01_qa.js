// QA board for the EP01 sets (sets_ep01.js, interiors.js): one shot per item in story context, rendered as stills.
//   node tools/render.js engine/kit/_sets_ep01_qa.js <outdir> times=0.5,1.5,... quality=final
// Shot i covers [i, i+1); render t = i + 0.5. Cast stand-ins come from the character kit (chars.js), placed on the set
// anchors exactly as the shot builders will. Camera = the set's named view + the default push.
import * as THREE from 'three';
import * as sets from './sets.js';
import * as K from './chars.js';
import * as S from './sets_ep01.js';
import * as I from './interiors.js';

const ST = sets.STUD, DEG = Math.PI / 180;
const V3 = (a) => new THREE.Vector3(...a);
const SPARK = { sharpness: 7, core: 0.75, underlay: 0.55, underlayOpacity: 0.5, brightness: 2.0, px: [55, 95] };
const GALAXY = { ...sets.SKIES.galaxy, nebula: 0.45 };
const GALAXY_LOW = { ...sets.SKIES.galaxy, stops: [[-1, '#000000'], [-0.02, '#1c1650'], [0.12, '#140f3e'], [0.35, '#0b0828'], [0.65, '#06041a'], [1, '#030210']], nebula: 0.6, seed: 21 };
// lay an avatar (metres, feet at origin) on its back: head at `head` (world), body along `dir` (unit, feet -> head)
function lieDown(av, head, dir, up = [0, 1, 0], scale = 1) {
  const y = V3(dir).normalize(), z = V3(up).normalize(), x = new THREE.Vector3().crossVectors(y, z).normalize(); z.crossVectors(x, y);
  av.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z)); const len = 4.7 * ST * scale; av.position.copy(V3(head)).addScaledVector(y, -len).addScaledVector(V3(up), 0.45 * ST * scale); return av;
}
function sleeper(ctx, H, who = 'theo', o = {}) {
  const A = H.ep01.room.sleeper; const yaw = A.yaw; const dir = new THREE.Vector3(-Math.cos(yaw), 0, Math.sin(yaw)); // bed local -X (head end) in world
  const av = K.makeCharacter(who, { face: 'sleeping', ...o }); K.setPose(av, { armLx: 10, armRx: 30 }); lieDown(av, A.head, dir.toArray(), [0, 1, 0], o.scale ?? 1); ctx.add(av); return av;
}
const sparks = (ctx, c, size, n, seed) => { const f = sets.sparkles(ctx, { ...SPARK, center: c, size, count: n, seed }); ctx.add(f); return f; };
const cam = (ctx, v, Z = 0.19) => { ctx.camera.set(v); ctx.camera.push(Z); };

const SHOTS = [
  // 0 s45: Theo's window from outside at night: the room lit softly, Theo asleep inside, the empty ring below, the hero with the lit gnome
  ['lot_theo_window_night', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', bed: 'empty' }); ctx.add(H); const sp = H.ep01.spots;
    sleeper(ctx, H, 'theo');
    const hero = K.makeCharacter('heroBarefoot', { face: 'sad' }); K.setPose(hero, { ...K.POSES.hug, neckY: -25 }); hero.position.copy(V3(sp.bed0)).add(new THREE.Vector3(-2.2 * ST, -0.35 * ST, 2.4 * ST)); hero.rotation.y = Math.PI - 0.5; ctx.add(hero);
    const g = K.makeGnome('grandpa', { lantern: 1, lanternLight: 2.2 }); g.position.copy(hero.position).add(new THREE.Vector3(Math.sin(hero.rotation.y) * 1.1 * ST, 2.0 * ST, Math.cos(hero.rotation.y) * 1.1 * ST)); g.rotation.y = hero.rotation.y; ctx.add(g);
    cam(ctx, H.ep01.views.theoWindowOut); S.heroLight(ctx, H, { skyPreset: GALAXY_LOW, skyOpts: { intensity: 1.6 } });
    ctx.shared.fx = sparks(ctx, V3(sp.theoWindow).add(new THREE.Vector3(0, -0.3, 1.2)).toArray(), [3, 1.6, 1.6], 8, 'q0');
  }],
  // 1 s10: day, the agent board by the path, two family gnomes either side, Grandpa small behind under the window
  ['lot_board_day', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'day', gnomes: ['lawn1', 'lawn3', 'bedFront1'] }); ctx.add(H); const sp = H.ep01.spots; const b = V3(sp.board);
    [[-1.4, 1], [3.4, 3]].forEach(([dx, v]) => { const f = K.makeFamilyGnome(v); f.position.set(b.x + dx * ST, 0, b.z + 0.8 * ST); f.rotation.y = 0.35 * Math.sign(-dx); ctx.add(f); });
    cam(ctx, H.ep01.views.boardMS, 0.26); S.heroLight(ctx, H); },
  ],
  // 2 s25: dusk from the street: SOLD on the board, the truck at the kerb (open back, BALCONY GNOME box), Theo at the fence
  ['lot_sold_truck_dusk', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'dusk', sold: -1, truck: 'open' }); ctx.add(H); const sp = H.ep01.spots;
    const theo = K.makeCharacter('theo', { face: 'wonder' }); K.setPose(theo, K.POSES.hug); theo.position.set(sp.gate[0] - 2.6 * ST, 0, sp.gate[2] + 1.1 * ST); theo.rotation.y = Math.PI - 0.3; ctx.add(theo);
    cam(ctx, H.ep01.views.streetWS, 0.15); S.heroLight(ctx, H);
  }],
  // 3 s27: the empty ring under his old window (lit, curtains half drawn), two boot dents
  ['lot_empty_spot', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', bed: 'empty' }); ctx.add(H); cam(ctx, H.ep01.views.emptySpot, 0.2);
    S.heroLight(ctx, H, { window: { n: 1, cd: 2.4, maxD: 10 } }); ctx.shared.fx = sparks(ctx, V3(H.ep01.spots.bed0).add(new THREE.Vector3(0, 0.5, 0.4)).toArray(), [1.6, 0.8, 1.0], 7, 'q3');
  }],
  // 4 s29: Grandpa at the gate staring up at the truck's open back (dome light on, BALCONY GNOME box)
  ['lot_gate_truck', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', bed: 'empty', truck: 'open', gate: 1.5, gnomes: ['lawn0', 'lawn2', 'lawn3'] }); ctx.add(H); const sp = H.ep01.spots;
    const g = K.makeGnome('grandpa', { lantern: 0 }); g.position.set(sp.gate[0] - 0.2 * ST, 0, sp.gate[2] + 0.2 * ST); g.lookAt(V3(sp.truckBack).setY(0)); ctx.add(g); K.setGnomeGaze(g, 0, 18);
    cam(ctx, H.ep01.views.gateTruck, 0.22);
    sets.nightStreet(ctx, { set: H, lamp: { n: 3 } });
  }],
  // 5 s44 / s55: inside the half-empty room: Theo on the mattress, boxes THEO, star projections, the window behind
  ['room_theo_inside', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', bed: 'grandpa', lantern: 0.6 }); ctx.add(H); sleeper(ctx, H, 'theo');
    cam(ctx, H.ep01.views.room_toWindow, 0.19); I.bedroomNight(ctx, { set: H, lamp: 3.5, nightlight: 2.5, lanternOutside: true });
    ctx.shared.fx = sparks(ctx, V3(H.ep01.room.sleeper.body).add(new THREE.Vector3(0, 0.8, 0.6)).toArray(), [3, 1.6, 2.2], 14, 'q5');
  }],
  // 6 s66: 2010s sepia: the hero at 5 asleep in the small rocket bed; Grandpa's face at the glass with his flashlight
  ['room_hero5_sepia', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', era: '2010s' }); ctx.add(H); sleeper(ctx, H, 'hero', { scale: 0.75 });
    const gp = K.makeCharacter('grandpa', { face: 'heartfelt' }); const w = V3(H.ep01.spots.theoWindow); gp.position.set(w.x - 0.1, 0, w.z + 0.75); gp.rotation.y = Math.PI; K.setPose(gp, { armRx: 120, armRz: -10 }); ctx.add(gp);
    cam(ctx, H.ep01.views.room_toWindow, 0.19); I.bedroomNight(ctx, { set: H, lamp: 3, lanternOutside: { cd: 2 } }); ctx.post.set(sets.postPreset('sepia'));
  }],
  // 7 s67: the same in black and white, 1960s: iron bed, rose stripe, a younger Grandpa at the window
  ['room_dad60s_bw', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', era: '1960s' }); ctx.add(H); sleeper(ctx, H, 'dad', { scale: 0.75 });
    const gp = K.makeCharacter('grandpa', { face: 'heartfelt', accessories: [{ type: 'hair', style: 'short', color: '#2a2018' }, { type: 'moustache', color: '#2a2018' }] }); const w = V3(H.ep01.spots.theoWindow); gp.position.set(w.x - 0.1, 0, w.z + 0.75); gp.rotation.y = Math.PI; K.setPose(gp, { armRx: 120, armRz: -10 }); ctx.add(gp);
    cam(ctx, H.ep01.views.room_toWindow, 0.19); I.bedroomNight(ctx, { set: H, lamp: 3, lanternOutside: { cd: 2 } }); ctx.post.set(sets.postPreset('bw'));
  }],
  // 8 s68: outside the same window in the 1990s (sepia): yellow floral wallpaper, a girl asleep in the top bunk
  ['lot_1990s_window', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', era: '1990s', theoRoom: { era: 'cousin90s', lit: true, curtains: 'open' } }); ctx.add(H); sleeper(ctx, H, 'theo', { scale: 0.75 });
    cam(ctx, H.ep01.views.theoWindowOut); S.heroLight(ctx, H, { skyPreset: GALAXY_LOW }); ctx.post.set(sets.postPreset('sepia'));
  }],
  // 9 s17: the hero's own room (11): OTS at the window, Grandpa gnome below in the window spill
  ['room_hero11_ots', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', theoRoom: { era: 'hero11', lit: true, curtains: 'open' } }); ctx.add(H);
    const hero = K.makeCharacter('hero', { face: 'grin' }); const w = V3(H.ep01.spots.theoWindow); hero.position.set(w.x + 0.12, 0.32, w.z - 1.3 * ST); hero.rotation.y = 0; K.setPose(hero, K.POSES.wave); ctx.add(hero);
    const v = H.ep01.views.room_otsWindow; cam(ctx, v, 0.15); I.bedroomNight(ctx, { set: H, lamp: 4 });
  }],
  // 10 s12: next door by day: three glossy plastic gnomes facing the street, the REX kennel, hose reel, the lead + hole
  ['nextdoor_day', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'day' }); ctx.add(H); cam(ctx, H.ep01.views.nextDoorMS, 0.19); S.heroLight(ctx, H);
  }],
  // 11 s13: top-down over the lead, from the empty kennel toward the hole
  ['kennel_top', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'day' }); ctx.add(H); const a = H.ep01.views.kennelTop, b = H.ep01.views.holeTop;
    const mid = (x, y) => x.map((v, i) => v * 0.4 + y[i] * 0.6); ctx.camera.set({ pos: mid(a.pos, b.pos), target: mid(a.target, b.target), fov: 50 }); S.heroLight(ctx, H, { sun: { el: 30 } });
  }],
  // 12 s41: next door at night: plastic gnomes with black lanterns, the hole, our side lit past the fence
  ['nextdoor_night', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', lanterns: 1 }); ctx.add(H); cam(ctx, H.ep01.views.nextDoorNight); sets.nightStreet(ctx, { set: H, postOpts: { grade: { temperature: -24 } } });
  }],
  // 13 s06: Grandma in her rose wingback armchair (day interior)
  ['grandma_room', (ctx) => {
    const R = I.grandmaRoom(ctx); ctx.add(R); const A = R.userData.anchors; const gm = K.makeCharacter('grandma', { face: 'content' }); K.setPose(gm, { ...K.POSES.sit, armLx: 40, armRx: 40, armLz: -12, armRz: -12 }); gm.position.set(A.seat[0], A.seat[1] - 1.5 * ST, A.seat[2]); ctx.add(gm);
    cam(ctx, R.userData.views.armchairMS, 0.18); I.interiorDay(ctx, { room: R });
  }],
  // 14 s26: the hall at 9:00: clock, rolled sleeping bag, THEO boxes by the front door
  ['hall_clock', (ctx) => {
    const R = I.hall(ctx); ctx.add(R); R.ep01.setClock(9, 0, 0); cam(ctx, R.userData.views.clockINS, 0.15); I.bedroomNight(ctx, { room: R, lamp: 3 });
    const lp = R.userData.anchors.lamp; ctx.add(ctx.lights.point({ color: '#ffe6c0', intensity: 3, pos: lp, decay: 2 }));
  }],
  // 15 s48: truck cab: red LED 11:52, sticky note LEAVE 6 AM on the wheel, the night street through the windscreen
  ['truck_cab', (ctx) => { const R = I.truckCab(ctx); ctx.add(R); R.ep01.update(0); cam(ctx, R.userData.views.clockINS, 0.15); I.cabNight(ctx, { cab: R }); }],
  // 16 s88: rear POV from the leaving truck at dawn: box edges frame the street, Theo small beside Grandpa
  ['truck_pov_dawn', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'dawn', bed: 'grandpa', board: false, truck: 'leaving', truckOpts: { t0: 0, balconyBox: false }, lanterns: 0.4 }); ctx.add(H);
    const theo = K.makeCharacter('theo', { face: 'content' }); theo.position.copy(V3(H.ep01.spots.bed0)).add(new THREE.Vector3(1.6 * ST, -0.35 * ST, 1.4 * ST)); theo.rotation.y = 0.4; ctx.add(theo);
    const pov = H.ep01.truck.ep01.povCamera({}); ctx.camera.set({ pos: (t, o) => pov.pos(t + 4.5, o), target: (t, o) => pov.target(t + 4.5, o), fov: pov.fov }); S.heroLight(ctx, H, { sun: { az: 200, el: 9 } });
    ctx.shared.upd = (t) => H.ep01.update(t + 4.5);
  }],
  // 17 s95: the back garden at dusk: the narrator on the bench, his granddaughter beside him
  ['back_garden_bench', (ctx) => {
    const G = S.backGarden(ctx, { tod: 'dusk' }); ctx.add(G); const A = G.userData.anchors;
    const old = K.makeCharacter('heroOld', { face: 'content' }); K.setPose(old, K.POSES.sit); old.position.set(A.benchSeatL[0], A.benchSeatL[1] - 1.5 * ST, A.benchSeatL[2]); old.rotation.y = Math.PI; ctx.add(old);
    const girl = K.makeCharacter('theo', { face: 'angry', scale: 0.75 }); girl.position.set(A.benchSeatR[0] - 0.1, 0, A.benchSeatR[2] - 0.35); girl.rotation.y = Math.PI + 0.9; K.setPose(girl, { armLz: 40, armRz: 40, armLx: -10, armRx: -10 }); ctx.add(girl);
    cam(ctx, G.userData.views.benchMS, 0.18); G.ep01.light(ctx);
  }],
  // 18 s97: reverse angle from the granddaughter's lit window: the narrator in the striped deck chair, the TF moon
  ['back_garden_window_night', (ctx) => {
    const G = S.backGarden(ctx, { tod: 'night' }); ctx.add(G); const A = G.userData.anchors;
    const old = K.makeCharacter('heroOld', { face: 'content' }); K.setPose(old, { ...K.POSES.sit, bodyX: -18 }); old.position.set(A.chairSeat[0], A.chairSeat[1] - 1.75 * ST, A.chairSeat[2]); old.rotation.y = Math.PI; ctx.add(old);
    cam(ctx, G.userData.views.windowReverse, 0.25); G.ep01.light(ctx, { tod: 'night', preset: { skyPreset: GALAXY, moon: { az: 160, el: 22, size: 8, style: 'tf' } } });
    ctx.shared.fx = sparks(ctx, V3(A.chairSeat).add(new THREE.Vector3(0, 0.6, -0.8)).toArray(), [2.5, 1.4, 1.6], 8, 'q18');
  }],
  // 19 s90: top-down on the garden table at dusk: the Polaroid pile (photos rendered from the 3D set)
  ['polaroid_stack', (ctx) => {
    const G = S.backGarden(ctx, { tod: 'dusk' }); ctx.add(G); const A = G.userData.anchors;
    const st = S.polaroidStack(ctx, [1, 10, 25, 40], { at: A.pile }); ctx.add(st);
    cam(ctx, G.userData.views.tableTop, 0.15); G.ep01.light(ctx);
  }],
  // 20 s91: the phone in an old freckled hand, Theo's newest photo on the screen
  ['phone_ecu', (ctx) => {
    const G = S.backGarden(ctx, { tod: 'dusk' }); ctx.add(G); const A = G.userData.anchors;
    const ph = S.phone(ctx, { photos: [52, 60] }); ph.position.copy(V3(A.benchSeatL)).add(new THREE.Vector3(0, 1.3 * ST, -1.2 * ST)); ph.rotation.set(-0.35, Math.PI, 0); ctx.add(ph); ph.ep01.swipe(0.5, [0.45]);
    const v = { pos: V3(ph.position.toArray()).add(new THREE.Vector3(0.05, 0.25, -0.9)).toArray(), target: ph.position.toArray(), fov: 50 }; cam(ctx, v, 0.1); G.ep01.light(ctx);
  }],
  // 21 s93: the newest photo full frame (Grandpa mid-blink, Theo at 66, the girl waving at the window)
  ['photo_full', (ctx) => {
    const ph = S.photoTexture(ctx, 60, { blink: 0.55, girl: true }); const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: ph.texture })); ctx.add(m);
    ctx.camera.set({ pos: [0, 0, 1.6], target: [0, 0, 0], fov: 50 }); ctx.camera.push(0.08); ctx.post.set(sets.postPreset('day', { exposure: 1.0, toneMapping: 'linear' }));
  }],
  // 22 s22: top-down sepia over our lawn (the lap)
  ['lot_lap_top', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', era: '2010s' }); ctx.add(H); cam(ctx, H.ep01.views.lapTop, 0.15); S.heroLight(ctx, H); ctx.post.set(sets.postPreset('sepia'));
  }],
  // 23 60 years later, spring day, the photo framing in the episode renderer (repaint, grown tree, mossy Grandpa, Theo 66)
  ['lot_year60_day', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'day', year: 60, board: false, keepOff: false, gnomes: ['lawn0', 'lawn1', 'bedFront1'] }); ctx.add(H);
    const t66 = S.theoAtFallback(66); t66.position.copy(V3(H.ep01.spots.bed0)).add(new THREE.Vector3(3.0 * ST, -0.35 * ST, 1.2 * ST)); t66.rotation.y = -0.15; ctx.add(t66); K.setGnomeHead(H.ep01.gnomes.grandpa, 150, 4, 0);
    cam(ctx, { ...H.ep01.views.photo, fov: 60 }, 0.1); S.heroLight(ctx, H);
  }],
  // 24 s73 / s54: night, the hole the plastic gnome left, $4.99 sticker, the brick edging under the lit window
  ['lot_hole_bricks', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', bed: 'hole' }); ctx.add(H); cam(ctx, H.ep01.views.bricksCU, 0.2);
    S.heroLight(ctx, H, { skyPreset: GALAXY_LOW });
  }],
  // 25 s82: pink dawn over our house, the door, Grandpa in his bed, the family gnomes, lanterns dimmed
  ['lot_dawn', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'dawn', bed: 'grandpa', board: false, lanterns: 0.4 }); ctx.add(H); cam(ctx, H.ep01.views.dawnLow, 0.19); S.heroLight(ctx, H);
    ctx.shared.fx = sparks(ctx, V3(H.ep01.spots.steps).add(new THREE.Vector3(0, 0.5, 2)).toArray(), [4, 1, 3], 5, 'q25');
  }],
  // 26 s70: the s09 framing again (part1 lawn_stare camera block) on heroLot: lanterns lit, Theo's real room behind the glass
  ['lot_lawn_stare_lit', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', bed: 'grandpa', lantern: 1, lanterns: 1, shiftBedFront0: false }); ctx.add(H); sleeper(ctx, H, 'theo');
    const id = 'A1'; const sl = sets.slot(H, id + '.bed0'); const fwd = new THREE.Vector3(Math.sin(sl.yaw), 0, Math.cos(sl.yaw)); const side = new THREE.Vector3(-fwd.z, 0, fwd.x);
    const base = V3(sl.pos); const near = V3(sets.slot(H, id + '.bedFront0').pos);
    const pos = near.clone().addScaledVector(fwd, -3.0 * ST).addScaledVector(side, -1.6 * ST); pos.y = 1.4 * ST; const tgt = base.clone(); tgt.y = 3.0 * ST;
    ctx.camera.set({ pos: pos.toArray(), target: tgt.toArray(), fov: 70 }); const camYaw = Math.atan2(tgt.x - pos.x, -(tgt.z - pos.z)) / DEG;
    sets.nightLawn(ctx, { set: H, window: { n: 2, cd: 2.4, color: '#ffd9a0', maxD: 14 }, hemiIntensity: 1.05, moon: { az: camYaw - 8, el: 30, size: 9, style: 'tf' }, skyPreset: GALAXY_LOW, skyOpts: { intensity: 1.6 }, postOpts: { exposure: 1.1, grade: { temperature: -10, tint: 6 } } });
    ctx.camera.pull(0.1); ctx.shared.fx = sparks(ctx, pos.clone().lerp(base, 0.35).setY(0.7).toArray(), [3.5, 1.4, 2.5], 8, 's06');
  }],
  // 27 s40: our street at night, every lawn's gnome with its lantern lit (next door's plastic ones stay dark)
  ['street_lanterns', (ctx) => {
    const T = S.ep01Street(ctx, { lanterns: 1 }); ctx.add(T); cam(ctx, T.ep01.views.alongLawns, 0.15);
    sets.nightStreet(ctx, { set: T, skyPreset: GALAXY, lamp: { n: 4 } }); ctx.shared.fx = sparks(ctx, T.ep01.views.alongLawns.target, [8, 2, 6], 10, 'q27');
  }],
  // 28 s43: our street from high above
  ['street_aerial', (ctx) => {
    const T = S.ep01Street(ctx, { lanterns: 1, truck: 'open' }); ctx.add(T); cam(ctx, T.ep01.views.aerial, 0.12); sets.nightStreet(ctx, { set: T, skyPreset: GALAXY, lamp: { n: 4 } });
  }],
  // 29 the hero's room at 11 (s17 era): carved bed, magenta duvet, posters, shelf, rug, glow stars, lamp (wide, back wall)
  ['room_hero11_wide', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', theoRoom: { era: 'hero11', lit: true, curtains: 'open' } }); ctx.add(H); const w = V3(H.ep01.spots.theoWindow);
    cam(ctx, { pos: [w.x + 0.6, 1.95, w.z - 0.35], target: [w.x + 0.2, 0.95, w.z - 3.6], fov: 70 }, 0.15); I.bedroomNight(ctx, { set: H, lamp: 4 });
    ctx.shared.fx = sparks(ctx, [w.x + 0.3, 1.5, w.z - 2.2], [2.6, 1.4, 2.0], 12, 'q29');
  }],
  // 30 the 1990s room from inside: yellow floral wallpaper, the bunk bed
  ['room_cousin90s_wide', (ctx) => {
    const H = S.heroLot(ctx, { tod: 'night', era: '1990s', theoRoom: { era: 'cousin90s', lit: true, curtains: 'open' } }); ctx.add(H); const w = V3(H.ep01.spots.theoWindow);
    cam(ctx, { pos: [w.x + 0.6, 1.9, w.z - 0.35], target: [w.x + 0.3, 1.2, w.z - 3.6], fov: 70 }, 0.15); I.bedroomNight(ctx, { set: H, lamp: 4 }); ctx.post.set(sets.postPreset('sepia'));
  }],
];

export const QA_NAMES = SHOTS.map((s) => s[0]);
export default {
  name: 'sets_ep01_qa', fps: 60, width: 1080, height: 1920, seed: 'ep01', quality: { shadows: 'pcfsoft' },
  post: sets.postPreset('night'),
  shots: SHOTS.map(([name, build], i) => ({ name, start: i, end: i + 1,
    build(ctx) { ctx.shared.fx = null; ctx.shared.upd = null; build(ctx); },
    update(ctx, t) { if (ctx.shared.fx) ctx.shared.fx.update(t); if (ctx.shared.upd) ctx.shared.upd(t); } })),
};
