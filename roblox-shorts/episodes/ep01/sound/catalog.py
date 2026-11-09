"""EP01 sound catalog: every SFX cue name of ASSETS.md / board.md -> a source (an extracted Epidemic file with in/out,
a procedural design from synth.py, or a stack of both) + sync point + filters + fades + target level, and the
ambience beds (looped, continuous in episode time).

`python3 -I catalog.py` renders every cue once, measures it, writes the computed gains into sfx_map.json (next to
this file) and a preview WAV per cue into <scratch>/cues/. mix.py reads sfx_map.json and calls render_cue()/bed().

Level convention (the approved test's method): a cue's gain makes its loudness hit `target` LUFS, measured either
  - 'win': BS.1770 integrated loudness over [start+a, start+b] of the placed clip (the test's W1/M1/P1/A1 method), or
  - 'mmax' (default): the maximum momentary loudness (400 ms K-weighted window, 10 ms hop) of the clip.
The voice sits at -16 LUFS (dual-mono), so a -28 'mmax' cue is ~15 LU under the voice's own momentary peaks.
Placement: clip start = event time + offset - sync, where `sync` is the sync point inside the trimmed clip
(a transient, a whoosh peak) and `offset` moves it relative to the picture event (e.g. the latch closes 0.1 s after
the gate starts to swing).
"""
import os, sys, json, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pyloudnorm as pyln
from scipy.signal import butter, sosfilt
import synth as S

SR = S.SR
HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = S.SCRATCH
MAP_PATH = os.path.join(HERE, 'sfx_map.json')
F = lambda name: name + ' - Epidemic Sound.mp3'      # extracted file name in <scratch>/sfx/

# ------------------------------------------------------------------------------------------------ cues
# fields: kind hit, prio 1 primary (board) / 2 sweetener (standard profile, density-capped) / 3 optional (full only),
# layer_of: counts as part of that cue's event (density), shots, what (picture event), src: {'file', in, out} |
# {'design', args} | {'layers': [...]}, sync (s into the clip), offset (s after the event), fin/fout, hp/lp,
# verb [kind, wet], pan, target {lufs, mode, win}, rule (multi-time placement, see mix.resolve_cues).
CUES = {
    # ---- the approved 5-second test, verbatim (test5_mix_report.json) ----
    'W1': dict(prio=1, shots=['s01'], what='opener snap pull-back from the gnome ECU: airy whoosh, peak 0.12 s',
               src=dict(file=F('ES_Swooshes, Whoosh, Airy, Short'), a=11.21 - 0.12, b=12.55), sync=0.0, offset=0.0,
               fin=0.02, fout=0.25, hp=200, lp=9000, target=dict(lufs=-26.0, mode='win', win=[0.0, 0.5]), approved=True),
    'M1': dict(prio=1, shots=['s04', 's05'], what='transformation shimmer: swell from the cut to s04 (2.10), peak 2.30; '
               'in the episode its sparkle tail fades by 3.95 s (cut to the interior at 3.567)',
               src=dict(file=F('ES_Magic, Shimmer, Christmas, Sparkle, Magic, Shimmer Dust'), a=2.20, b=4.05),
               sync=0.0, offset=2.10 - 2.233333, fin=0.04, fout=0.45, hp=1500, lp=None,
               target=dict(lufs=-28.0, mode='win', win=[0.0, 1.0]), approved=True),
    'P1': dict(prio=1, shots=['s04'], what='the snap: soft poof, pop transient on 2.240 s (frame 134 + 7 ms)',
               src=dict(file=F('ES_Cartoon, Pop, Vanish'), a=0.10, b=0.42), sync=0.135, offset=2.240 - 2.233333,
               fin=0.012, fout=0.05, hp=180, lp=None, target=dict(lufs=-33.0, mode='win', win=[-0.005, 0.395]),
               approved=True, layer_of='M1'),
    # ---- part 1 ----
    'T_GLINT': dict(prio=3, shots=['s08'], what='glasses snap level + star glint on the lens', src=dict(design='t_glint'),
                    sync=0.002, target=dict(lufs=-32.0)),
    'CURTAIN': dict(prio=3, shots=['s11'], what='curtains snap shut on 6 windows, 0.12 s apart', src=dict(design='curtain'),
                    sync=0.08, lp=6000, target=dict(lufs=-33.0)),
    'SQUEAK': dict(prio=2, rank=7, shots=['s12'], what='the dog bites the plastic hat (squash 15 % for 6 frames)',
                   src=dict(design='squeak'), sync=0.0, target=dict(lufs=-27.0)),
    'CHAIN_TUG': dict(prio=3, shots=['s13'], what='lead clink + tug toward the hole', src=dict(design='chain_tug'), sync=0.0,
                      target=dict(lufs=-31.0)),
    'HOPS': dict(prio=3, shots=['s14'], what='the family gnome toddles down its path in small hops (times estimated, '
                 'sync to part1 gate_bonk when built)', src=dict(design='hops'), sync=0.0, target=dict(lufs=-33.0),
                 rule=dict(kind='hops')),
    'BONK': dict(prio=1, shots=['s14'], what='bonk on the invisible line: ripple rings + 12 sparkles + shake',
                 src=dict(design='bonk'), sync=0.0, target=dict(lufs=-24.0)),
    'SHIMMER_S': dict(prio=2, rank=12, shots=['s15', 's32'], what='gold shimmer: the curtain parts / the gold ripple along the line',
                      src=dict(design='shimmer_s'), sync=0.02, target=dict(lufs=-30.0), layer_of={'s32': 'CLINK'}),
    'LATCH': dict(prio=1, shots=['s15'], what='gate leaf swings shut (6 frames) and latches',
                  src=dict(file=F('ES_Doors, Hardware, Latch, Lock'), a=0.27, b=0.74), sync=0.332 - 0.27, offset=0.10,
                  fin=0.003, fout=0.15, hp=150, lp=12000, verb=['night', 0.08], target=dict(lufs=-26.0)),
    'TOK': dict(prio=2, rank=13, shots=['s16'], what='Dad taps the hat (tip wobbles +-6 deg)', src=dict(design='tok'), sync=0.0,
                target=dict(lufs=-30.0)),
    'TIK': dict(prio=1, shots=['s18', 's86'], what='the gnome blinks (2-frame decal swap)', src=dict(design='tik'), sync=0.0,
                target=dict(lufs=-27.0)),
    'CLICK_TORCH': dict(prio=1, shots=['s20', 's61'], what='flashlight on (1 frame) + beam',
                        src=dict(file=F('ES_Mechanical, Click, Button, Switch On, Off'), a=1.135, b=1.30), sync=1.152 - 1.135,
                        fin=0.002, fout=0.06, hp=300, verb=['night', 0.05], target=dict(lufs=-31.0)),
    'STEP_WET': dict(prio=2, rank=11, shots=['s21', 's62', 's64'], what="Grandpa's slipper lands on the wet lawn (s62-s64: his lap, "
                     'steps every 0.44 s until he stops at 71.375 s)', src=dict(design='walk'), sync=0.0, lp=6000,
                     target=dict(lufs=-30.0), rule=dict(kind='steps')),
    'SLAP_STICKER': dict(prio=1, shots=['s25'], what='SOLD sticker slaps on (scale 1.3 -> 1 in 4 frames)', src=dict(design='slap_sticker'),
                         sync=0.0, offset=0.05, target=dict(lufs=-27.0)),
    'TICK_CLOCK': dict(prio=2, rank=4, shots=['s26'], what='minute hand ticks to 12 (2-frame snap + 3-frame wobble)',
                       src=dict(file=F('ES_Clocks, Tick, Old Wall Clock, Ticking'), a=4.49, b=4.95), sync=4.508 - 4.49,
                       fin=0.002, fout=0.2, hp=200, verb=['hall', 0.25], target=dict(lufs=-28.0)),
    # ---- part 2 ----
    'DOOR_BANG': dict(prio=1, shots=['s28'], what='the front door bangs open (heard from the lawn)',
                      src=dict(file=F('ES_Doors, Wood, Slam Shut'), a=0.0, b=0.9), sync=0.032, fin=0.002, fout=0.25, hp=70,
                      verb=['night', 0.12], target=dict(lufs=-23.0)),
    'FEET_WET': dict(prio=2, rank=10, shots=['s28', 's56'], what='bare feet on wet grass: s28 every 0.25 s from 30.483 to the cut; s56 '
                     'feet plant in the bed', src=dict(design='feet_wet'), sync=0.0, target=dict(lufs=-28.0), rule=dict(kind='feet'),
                     layer_of={'s28': 'DOOR_BANG'}),
    'CLINK': dict(prio=1, shots=['s32'], what='he picks Grandpa up: ceramic clink',
                  src=dict(file=F('ES_Food & Drink, Glassware, Mug, Coffee, Down On Table 01'), a=0.19, b=0.55), sync=0.206 - 0.19,
                  fin=0.002, fout=0.12, hp=600, verb=['night', 0.06], target=dict(lufs=-27.0)),
    'CREAK_LANTERN': dict(prio=3, shots=['s33'], what='the lantern wire handle creaks as he lifts it', src=dict(design='creak_lantern'),
                          sync=0.0, target=dict(lufs=-33.0), rule=dict(kind='shot_start', after=0.3)),
    'SUBBOOM': dict(prio=1, shots=['s34', 's35', 's36'], what='"the lawn MOVED": whoosh into a sub-boom, low rumble to 39.5 s',
                    src=dict(layers=[
                        dict(file=F('ES_Swooshes, Whoosh, Airy, Short'), a=1.40, b=2.10, at=-0.32, hp=150, lp=8000, fin=0.05, fout=0.3, g=-9.0),
                        dict(file=F('ES_Designed, Boom, Cinematic Booms, Clean Impact, Sub Bass 05'), a=0.0, b=3.6, at=0.0, fin=0.001, fout=1.2, g=5.0),
                        dict(design='rumble_tail', at=0.02, fin=0.15, fout=0.6, g=-9.0)]),
                    sync=0.32, target=dict(lufs=-15.0, mode='band_peak', band=[25, 110])),
    'CRUMBLE': dict(prio=2, rank=1, shots=['s35', 's51'], what='mounds rise staggered, crumbs popping off their tops',
                    src=dict(design='crumble_rise'), sync=0.0, target=dict(lufs=-29.0), layer_of='SUBBOOM'),
    'PLINK': dict(prio=2, rank=2, shots=['s36'], what='two amber reflector eyes light up (0 -> 1 in 3 frames)', src=dict(design='plink'),
                  sync=0.002, target=dict(lufs=-28.0), layer_of='SUBBOOM'),
    'FLASH': dict(prio=2, rank=2, shots=['s36'], what='"reflectors": the light sweep flashes them (star glint, 0.25 s)',
                  src=dict(design='reflector_flash'), sync=0.0, target=dict(lufs=-30.0), layer_of='SUBBOOM',
                  extra=dict(shot='s36', word='reflectors')),
    'SNIFF': dict(prio=1, shots=['s37', 's53'], what='snout unfurls and tests the air (s37); tulips shake, snouts wriggle (s53)',
                  src=dict(design='sniff'), sync=0.0, target=dict(lufs=-26.0), variants={'s53': 'sniff_wriggle'}),
    'SNIFF_BIG': dict(prio=1, shots=['s37'], what='"BIG ones": the big snout rises with a snort', src=dict(design='sniff_big'), sync=0.0,
                      target=dict(lufs=-25.0), layer_of='SNIFF', extra=dict(shot='s37', word='big')),
    'TINK_WHOOSH': dict(prio=1, shots=['s38'], what="Grandpa's lantern lights: 0 -> 1 in 3 frames, warm pool", src=dict(design='tink_whoosh'),
                        sync=0.12, target=dict(lufs=-23.0)),
    'FIP': dict(prio=2, rank=3, shots=['s39'], what='snouts recoil at the rim of the light (0.15 s spring)', src=dict(design='fip'),
                sync=0.0, target=dict(lufs=-28.0)),
    'TINKS': dict(prio=1, shots=['s40'], what='"Every lantern lit": cascade toward the camera, 0.15-0.3 s apart, the nearest on "lit"',
                  src=dict(design='tinks'), sync=0.12, target=dict(lufs=-23.0), rule=dict(kind='cascade')),
    'CLATTER': dict(prio=2, rank=1, shots=['s41'], what="next door's plastic gnome tips into a hole", src=dict(design='clatter'), sync=0.0,
                    target=dict(lufs=-26.0)),
    'RUMBLE_FAR': dict(prio=3, shots=['s43'], what='mounds prowl outside the fence of light: distant rumble', src=dict(design='rumble_far'),
                       sync=0.0, target=dict(lufs=-34.0), rule=dict(kind='shot_start', after=0.05)),
    # ---- part 3 ----
    'THUD_LOW': dict(prio=2, rank=1, shots=['s46'], what="Theo's window goes dark (1 frame) + the mounds surge", src=dict(design='thud_low'),
                     sync=0.0, target=dict(lufs=-24.0)),
    'RIP': dict(prio=3, shots=['s49'], what='packing tape rips off the box', src=dict(design='rip'), sync=0.0, target=dict(lufs=-28.0)),
    'THUNK_PLASTIC': dict(prio=2, rank=6, shots=['s50'], what="Mom's plastic gnome thunks into the soil", src=dict(design='thunk_plastic'),
                          sync=0.0, target=dict(lufs=-27.0)),
    'GULP': dict(prio=1, shots=['s51'], what='GULP: the turf closes over the plastic gnome like a mouth, seals, burps crumbs',
                 src=dict(design='gulp'), sync=0.0, target=dict(lufs=-21.0)),
    'FLUTTER': dict(prio=3, shots=['s51'], what='the $4.99 price sticker flutters down (0.4 s)', src=dict(design='flutter'), sync=0.0,
                    target=dict(lufs=-34.0)),
    'RUMBLE_ROLL': dict(prio=2, rank=5, shots=['s52'], what='the mounds roll toward the flowerbed (3 studs/s)', src=dict(design='rumble_roll'),
                        sync=0.0, fin=0.15, target=dict(lufs=-26.0)),
    'BRICK': dict(prio=3, shots=['s54'], what='an edging brick tips out (10 deg)', src=dict(design='brick'), sync=0.0, target=dict(lufs=-30.0)),
    'BREATH': dict(prio=2, rank=8, shots=['s55'], what="fog blooms on Theo's pane (0.35 s), heard from inside", src=dict(design='breath'),
                   sync=0.16, target=dict(lufs=-28.0)),
    'TIDE': dict(prio=2, rank=2, shots=['s56'], what='"backed off": the light pushes the mounds back 3 studs in 0.5 s', src=dict(design='tide'),
                 sync=0.0, target=dict(lufs=-25.0)),
    'SNIFF_FAR': dict(prio=3, shots=['s58'], what='distant sniffing at the ring edge', src=dict(design='sniff'), sync=0.0, lp=3000,
                      target=dict(lufs=-34.0), rule=dict(kind='shot_start', after=0.2)),
    'GRIND': dict(prio=1, shots=['s59'], what='the ceramic head grinds round 150 deg in stepped jerks (0.8 s inOutSine)',
                  src=dict(design='grind'), sync=0.0, target=dict(lufs=-23.0)),
    # ---- part 4 ----
    'KNEEL': dict(prio=3, shots=['s73'], what='he kneels in the soil', src=dict(design='kneel'), sync=0.0, target=dict(lufs=-30.0)),
    'TIK_SLOW': dict(prio=1, shots=['s75'], what='slow blink (4 frames), lids settle low: "like he was sorry"', src=dict(design='tik_slow'),
                     sync=0.0, target=dict(lufs=-28.0)),
    'SET_DOWN': dict(prio=2, rank=4, shots=['s76'], what='the gnome touches the soil', src=dict(design='set_down'), sync=0.0,
                     target=dict(lufs=-28.0)),
    # ---- part 5 ----
    'FWOOM': dict(prio=1, shots=['s77', 's78'], what='FWOOM: lantern 8 -> 50 cd in 0.15 s, burst + streaks, grade to magic; '
                  'second pulse on "flared" (+1.06 s)', src=dict(design='fwoom'), sync=0.28, target=dict(lufs=-18.0)),
    'PASS': dict(prio=2, rank=1, shots=['s78'], what='the wall of light passes the lens',
                 src=dict(file=F('ES_Swooshes, Whoosh, Long Reverbs'), a=0.25, b=2.6), sync=1.088 - 0.25, fin=0.1, fout=0.8, hp=180,
                 lp=10000, target=dict(lufs=-26.0), layer_of='FWOOM'),
    'DEFLATE': dict(prio=1, shots=['s79'], what='every mound sinks, staggered 0.15 s, following the ring', src=dict(design='deflate'),
                    sync=0.0, target=dict(lufs=-24.0), rule=dict(kind='deflate', n=6, gap=0.15)),
    'BLIPS': dict(prio=1, shots=['s80'], what='five eye pairs wink out, one blip per pair, each a step lower', src=dict(design='blips'),
                  sync=0.0, target=dict(lufs=-28.0), rule=dict(kind='shot_events')),
    'DOOR_CREAK': dict(prio=2, rank=9, shots=['s82'], what='the front door opens at dawn (14 frames)', src=dict(design='door_creak'),
                       sync=0.0, target=dict(lufs=-29.0)),
    'ENGINE': dict(prio=1, shots=['s87', 's88', 's89'], what='the truck starts off-screen (100.37), pulls away, fades before the pause',
                   src=dict(design='engine'), sync=0.0, target=dict(lufs=-27.5), rule=dict(kind='shot_at')),
    'RATTLE': dict(prio=2, rank=3, shots=['s88'], what='boxes knocking in the truck as it pulls away', src=dict(design='rattle'), sync=0.0,
                   target=dict(lufs=-32.0), layer_of='ENGINE', rule=dict(kind='shot_start', after=0.05)),
    'GRIND_SOFT': dict(prio=1, shots=['s89'], what='far: the head turns back to the window (0.8 s), seen from the truck',
                       src=dict(design='grind_soft'), sync=0.0, target=dict(lufs=-31.0)),
    'DROPS': dict(prio=2, rank=6, shots=['s90'], what='Polaroids drop one by one onto the pile', src=dict(design='drops'), sync=0.04,
                  target=dict(lufs=-31.0), rule=dict(kind='shot_events')),
    'PING': dict(prio=2, rank=5, shots=['s91'], what='message ping, the photo slides up',
                 src=dict(file=F('ES_User Interface, Alert, Notifications, Notification, Ping, Gentle'), a=0.0, b=0.8), sync=0.012,
                 fin=0.001, fout=0.2, target=dict(lufs=-27.0)),
    'SWIPE': dict(prio=3, shots=['s92'], what='swipes to the flowerbed photo, then the window photo (8 frames)',
                  src=dict(file=F('ES_Swooshes, Swish, Stick, Fast Swipe Through Air 01'), a=0.0, b=0.19), sync=0.068, offset=0.06,
                  fin=0.005, fout=0.06, hp=1200, target=dict(lufs=-33.0), rule=dict(kind='shot_events')),
    'POOF_SOFT': dict(prio=1, shots=['s97'], what='the dandelion clock releases its seeds (burst puff 14)', src=dict(design='poof_soft'),
                      sync=0.0, target=dict(lufs=-29.0)),
}

# board token -> cue (variants spelled in the timeline's sfx strings)
ALIASES = {'GRIND (soft)': 'GRIND_SOFT', 'SNIFF (distant)': 'SNIFF_FAR', 'distant rumble': 'RUMBLE_FAR', 'A1': None, 'MUSIC': None}
BED_TOKENS = ['A_NIGHT', 'A_ROOM', 'A_DAY', 'A_DUSK', 'A_DAWN']

# ------------------------------------------------------------------------------------------------ beds
CRICKETS = F('ES_Ambience, Suburban, Field With Crickets, Distant Traffic, Night 01')
BIRDS = F('ES_Ambience, Suburban, Neighborhood, Morning, Large Residential Yard, Bird Activity, Summer, Texas, USA')
CLOCK = F('ES_Clocks, Tick, Old Wall Clock, Ticking')
EP_LEN = 113.30
# A_NIGHT period = EP_LEN / 4 so the crickets at the last frame continue seamlessly into frame 0 (the loop);
# phase puts frame 0 on source 32.0 s, exactly the approved test's A1 window (32-37 s).
NIGHT_L = EP_LEN / 4
BEDS = {
    'A_NIGHT': dict(what='crickets, suburban night (the test A1), HPF 250 Hz (no traffic rumble)', loop=dict(file=CRICKETS, a=22.5, L=NIGHT_L, x=2.0),
                    phase=32.0 - 22.5, hp=250, gain_db=None, calib=dict(a=32.0, b=37.0, fin=0.06, fout=0.15, lufs=-33.0)),
    'A_NIGHT_OLD': dict(what='sepia flashback night: A_NIGHT low-passed 6 kHz', base='A_NIGHT', lp=6000, rel_db=-1.5),
    'A_NIGHT_BW': dict(what='1960s B&W: A_NIGHT low-passed 4 kHz', base='A_NIGHT', lp=4000, rel_db=-2.5),
    'A_NIGHT_CAB': dict(what='the night through the closed truck cab: crickets low-passed 2.2 kHz, far', base='A_NIGHT', lp=2200, lp_order=4, lufs=-42.0),
    'A_DAWN': dict(what='light dawn chorus (calm part of the Texas yard take)', loop=dict(file=BIRDS, a=3.0, L=21.0, x=2.0), phase=0.0,
                   hp=200, lp=10000, lufs=-33.0),
    'A_DAY': dict(what='day suburb: busier birds + a distant mower', loop=dict(file=BIRDS, a=62.0, L=19.0, x=2.0), phase=0.0, hp=150,
                  lufs=-32.5, add=[dict(design='mower', rel_db=-15.0)]),
    'A_DUSK': dict(what='evening birds settling (sparser part, low-passed) + the first crickets', loop=dict(file=BIRDS, a=84.0, L=25.0, x=2.0),
                   phase=0.0, hp=200, lp=6500, lufs=-34.0, add=[dict(bed='A_NIGHT', rel_db=-8.0)]),
    'A_ROOM': dict(what='bedroom at night: room tone, a far wall clock, crickets through the glass', synth='room_tone', lufs=-40.0,
                   add=[dict(loop=dict(file=CLOCK, a=10.0, L=40.0, x=0.2), hp=300, lp=2500, rel_db=-12.0),
                        dict(bed='A_NIGHT', lp=1600, rel_db=-6.0)]),
    'A_ROOM_DAY': dict(what="Grandma's room by day: room tone, the clock, birds through the window", synth='room_tone', lufs=-39.0,
                       add=[dict(loop=dict(file=CLOCK, a=10.0, L=40.0, x=0.2), hp=300, lp=2500, rel_db=-12.0),
                            dict(bed='A_DAY', lp=2500, rel_db=-4.0)]),
    'A_ROOM_OLD': dict(what='the room in a flashback: A_ROOM low-passed 5 kHz', base='A_ROOM', lp=5000, rel_db=-1.0),
    'A_HALL': dict(what='the hall at nine: room tone with the wall clock close', synth='room_tone', lufs=-36.0,
                   add=[dict(loop=dict(file=CLOCK, a=10.0, L=40.0, x=0.2), hp=200, rel_db=-3.0, verb=['hall', 0.3])]),
}

meter = pyln.Meter(SR)


# ---------------------------------------------------------------------------------------- processing
def _filt(x, hp=None, lp=None, lp_order=2):
    if hp: x = sosfilt(butter(2, hp, 'hp', fs=SR, output='sos'), x, axis=0)
    if lp: x = sosfilt(butter(lp_order, lp, 'lp', fs=SR, output='sos'), x, axis=0)
    return x


def _fades(x, fin, fout):
    """The approved test's raised-cosine fades (sample counts int(f * SR))."""
    a, b = int((fin or 0) * SR), int((fout or 0) * SR)
    w = lambda n: 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))
    if a: x[:a] *= w(a)[:, None]
    if b: x[-b:] *= w(b)[::-1][:, None]
    return x


def design(name, **kw):
    """Procedural sources (synth.py) incl. the time-dependent multi-hit ones."""
    t = kw.get('times')
    rel = (np.array(t) - t[0]).tolist() if t else None
    if name == 'tinks' and t: return S.lantern_cascade(t)[0]
    if name == 'blips' and t: return S.blips(rel)
    if name == 'drops' and t: return S.photo_drop([x + 0.04 for x in rel])
    if name == 'feet_wet' and t: return S.feet_run(rel)
    if name == 'feet_plant': return S.feet_run([0.0, 0.09], 'plant')
    if name == 'walk' and t: return S.walk(rel)
    if name == 'hops' and t: return S.hops(rel)
    if name == 'deflate': return S.deflate(n=kw.get('n', 6), gap=kw.get('gap', 0.15))
    if name == 'crumble_rise':
        r = S.rng('crumble_rise'); y = np.zeros((S.n_(1.3), 2)); tt = 0.0
        for k in range(7):
            c = S.crumble(0.45, f'cr{k}', dark=2600) * (0.9 ** k)
            S.place(y, c * np.array([0.5 + 0.4 * r.uniform(-1, 1), 0.5 + 0.4 * r.uniform(-1, 1)]), tt); tt += r.uniform(0.05, 0.15)
        return S.norm(y)
    return S.to_st(S.DESIGNS[name]())


def _source(src, times=None, variant=None, cue_kw=None):
    """One source -> processed stereo clip (before the cue's own filters/fades)."""
    if 'file' in src:
        x = S.LIB.load(src['file'])[int(src['a'] * SR):int(src['b'] * SR)].copy()
    else:
        x = design(variant or src['design'], times=times, **(cue_kw or {}))
    return x


def render_cue(cid, times=None, shot=None):
    """Render cue `cid` (optionally for a list of episode times / a shot variant) -> (clip, sync, spec).
    Gain is NOT applied (mix.py applies sfx_map gain_db)."""
    c = CUES[cid]; src = c['src']
    variant = (c.get('variants') or {}).get(shot)
    rule = c.get('rule') or {}
    kw = {k: rule[k] for k in ('n', 'gap') if k in rule}
    if 'layers' in src:
        sync = c['sync']
        parts = []
        for L in src['layers']:
            x = _source(L, times)
            x = _filt(x, L.get('hp'), L.get('lp'))
            x = _fades(x, L.get('fin'), L.get('fout'))
            parts.append((x * 10 ** (L.get('g', 0.0) / 20), sync + L['at']))
        n = max(int(round(s * SR)) + len(x) for x, s in parts)
        y = np.zeros((n, 2))
        for x, s in parts:
            i = int(round(s * SR)); y[i:i + len(x)] += x
    else:
        y = _source(src, times, variant, kw)
        sync = c.get('sync', 0.0)
    y = _filt(y, c.get('hp'), c.get('lp'))
    y = _fades(y, c.get('fin'), c.get('fout'))
    if c.get('verb'):
        k, w = c['verb']; n0 = len(y)
        y = S.verb(y, k, w, cid)
        y = _fades(y, 0, 0.1) if len(y) > n0 else y
    # trim trailing near-silence (keeps files small; -80 dBFS relative to the peak)
    pk = np.abs(y).max()
    if pk > 0:
        idx = np.where(np.abs(y).max(1) > pk * 1e-4)[0]
        y = y[:idx[-1] + 1] if len(idx) else y
    return y, sync, c


# ---------------------------------------------------------------------------------------- loudness
_K = (np.array([[1.53512485958697, -2.69169618940638, 1.19839281085285, 1.0, -1.69065929318241, 0.73248077421585],
                [1.0, -2.0, 1.0, 1.0, -1.99004745483398, 0.99007225036621]]))


def kweight(x):
    return sosfilt(_K, x, axis=0)


def momentary(x, win=0.4, hop=0.01):
    """K-weighted, ungated loudness over sliding windows (LUFS per hop) for a stereo array."""
    z = (kweight(x) ** 2).sum(1)
    c = np.concatenate([[0], np.cumsum(z)])
    w = int(win * SR); h = int(hop * SR)
    if len(z) < w: z2 = np.pad(z, (0, w - len(z))); c = np.concatenate([[0], np.cumsum(z2)])
    idx = np.arange(0, max(1, len(c) - 1 - w + 1), h)
    ms = (c[idx + w] - c[idx]) / w
    return -0.691 + 10 * np.log10(ms + 1e-20), idx / SR


def win_lufs(clip, start, a, b):
    """The test's measure: place clip at `start` on a silent bus and take BS.1770 integrated loudness of [start+a, start+b]."""
    t0 = min(0.0, a); n = int(round((max(b, len(clip) / SR) - t0 + 0.01) * SR))
    bus = np.zeros((n, 2)); i = int(round(-t0 * SR)); bus[i:i + len(clip)] += clip
    return meter.integrated_loudness(bus[int((a - t0) * SR):int((b - t0) * SR)])


def band_peak(clip, lo, hi, w=0.1):
    """Max 100 ms RMS (dBFS, channel mean) of the clip in [lo, hi] Hz (used for the sub-boom: its K-weighted loudness
    says little about how hard the sub hits)."""
    y = sosfilt(butter(4, [lo, hi], 'bandpass', fs=SR, output='sos'), clip.mean(1))
    k = int(w * SR)
    return max(20 * np.log10(np.sqrt((y[i:i + k] ** 2).mean()) + 1e-12) for i in range(0, max(1, len(y) - k), k // 2))


def measure(clip, target):
    if target.get('mode') == 'win':
        return win_lufs(clip, 0.0, *target['win'])
    if target.get('mode') == 'band_peak':
        return band_peak(clip, *target['band'])
    m, _ = momentary(clip)
    return float(m.max())


# --------------------------------------------------------------------------------------------- beds
_loops = {}


def loop_buffer(spec):
    """Seamless loop of file[a, a+L] (equal-power crossfade of the x seconds after a+L into the head), filtered
    circularly (two periods, keep the second) so the wrap has no filter transient."""
    key = json.dumps(spec, sort_keys=True)
    if key in _loops: return _loops[key]
    x = S.LIB.load(spec['file']); a, L, X = spec['a'], spec['L'], spec['x']
    n, nx = int(round(L * SR)), int(round(X * SR))
    i0 = int(round(a * SR))
    P = x[i0:i0 + n].copy()
    w = np.linspace(0, 1, nx)[:, None]
    P[:nx] = x[i0:i0 + nx] * np.sin(w * np.pi / 2) + x[i0 + n:i0 + n + nx] * np.cos(w * np.pi / 2)
    _loops[key] = P
    return P


def _loop_slice(P, phase, t0, t1):
    n = len(P); i0 = int(round((t0 + phase) * SR)); m = int(round((t1 - t0) * SR))
    idx = (i0 + np.arange(m)) % n
    return P[idx]


def _circ_filter(P, hp=None, lp=None, lp_order=2):
    if not hp and not lp: return P
    y = _filt(np.concatenate([P, P]), hp, lp, lp_order)
    return y[len(P):]


_bed_gain, _layer_k = {}, {}


def _main_raw(b, t0, t1):
    if 'loop' in b:
        P = _circ_filter(loop_buffer(b['loop']), b.get('hp'), b.get('lp'))
        return _loop_slice(P, b.get('phase', 0.0), t0, t1)
    key = 'synth:' + b['synth']            # synthetic room tone: one fixed 20 s seeded render, looped
    if key not in _loops: _loops[key] = S.room_tone(20.0, 'ep01room')
    return _loop_slice(_loops[key], 0.0, t0, t1)


def _layer_raw(L, t0, t1):
    if 'bed' in L:
        z = bed_raw(L['bed'], t0, t1)
    elif 'loop' in L:
        z = _loop_slice(_circ_filter(loop_buffer(L['loop']), L.get('hp'), None), 0.0, t0, t1)
    else:
        key = 'design:' + L['design']
        if key not in _loops: _loops[key] = getattr(S, L['design'])(20.0, 'ep01' + L['design'])
        z = _loop_slice(_loops[key], 0.0, t0, t1)
    z = _filt(z, None, L.get('lp'))
    if L.get('verb'): z = S.verb(z, L['verb'][0], L['verb'][1], 'bedverb')[:len(z)]
    return z


def bed_raw(name, t0, t1):
    """Bed before its level gain: main layer + added layers at fixed levels relative to the main layer (rel_db is
    the layer's RMS relative to the main layer's RMS, both measured once on episode seconds 0-10)."""
    b = BEDS[name]
    if 'base' in b:
        pre = min(0.5, t0)
        y = bed_raw(b['base'], t0 - pre, t1)
        return _filt(y, b.get('hp'), b.get('lp'), b.get('lp_order', 2))[int(round(pre * SR)):]
    y = _main_raw(b, t0, t1)
    for i, L in enumerate(b.get('add', [])):
        key = (name, i)
        if key not in _layer_k:
            ref = np.sqrt((_main_raw(b, 0.0, 10.0) ** 2).mean()); zr = np.sqrt((_layer_raw(L, 0.0, 10.0) ** 2).mean())
            _layer_k[key] = ref / (zr + 1e-12) * 10 ** (L.get('rel_db', 0.0) / 20)
        y = y + _layer_k[key] * _layer_raw(L, t0, t1)
    return y


def bed(name, t0, t1):
    """Bed `name` for episode time [t0, t1) as a stereo array at its level. Continuous in t: any slice of a bed lines
    up sample-exactly with any other slice of it (looped sources indexed by absolute episode time)."""
    return bed_raw(name, t0, t1) * bed_gain(name)


def bed_gain(name):
    """Linear gain bringing bed `name` to its target (A_NIGHT: the approved test's A1 calibration, -2.09 dB;
    variants with `base`: the base's gain x rel_db)."""
    if name in _bed_gain: return _bed_gain[name]
    b = BEDS[name]
    if 'base' in b and 'lufs' not in b:
        g = 20 * np.log10(bed_gain(b['base'])) + b.get('rel_db', 0.0)
    elif 'calib' in b:   # the test's exact method: file segment a..b, HPF, fades, integrated loudness
        c = b['calib']
        seg = S.LIB.load(b['loop']['file'])[int(c['a'] * SR):int(c['b'] * SR)].copy()
        seg = _fades(_filt(seg, b.get('hp')), c['fin'], c['fout'])
        g = c['lufs'] - meter.integrated_loudness(seg)
    else:
        g = b['lufs'] - meter.integrated_loudness(bed_raw(name, 0.0, 12.0))
    _bed_gain[name] = 10 ** (g / 20)
    return _bed_gain[name]


# --------------------------------------------------------------------------------------------- build
def build(write_previews=True):
    import soundfile as sf
    out = {'version': 1, 'sr': SR, 'note': __doc__.strip().split('\n')[0],
           'roots': {'sfx': os.path.join(SCRATCH, 'sfx'), 'previews': os.path.join(SCRATCH, 'cues')},
           'level_modes': {'win': 'BS.1770 integrated over [start+a, start+b] of the placed clip (approved test method)',
                           'mmax': 'max momentary loudness (400 ms K-weighted, 10 ms hop) of the clip',
                           'band_peak': 'max 100 ms RMS in a band, dBFS (the sub-boom: 25-110 Hz)'},
           'cues': {}, 'beds': {}, 'aliases': ALIASES}
    pdir = os.path.join(SCRATCH, 'cues'); os.makedirs(pdir, exist_ok=True)
    for cid, c in CUES.items():
        times = None
        if (c.get('rule') or {}).get('kind') in ('cascade',): times = [44.63, 44.83, 45.02, 45.22]
        if (c.get('rule') or {}).get('kind') in ('shot_events',) and cid == 'BLIPS': times = [91.29, 91.67, 91.848, 92.083, 92.233]
        if cid == 'DROPS': times = [103.83, 104.23, 104.468, 104.75]
        if cid == 'SWIPE': times = None
        if cid == 'FEET_WET': times = [30.483, 30.733, 30.983, 31.233]
        if cid == 'STEP_WET': times = [69.623, 70.063, 70.503, 70.943, 71.375]
        if cid == 'HOPS': times = [15.25, 15.47, 15.69, 15.91, 16.13]
        y, sync, _ = render_cue(cid, times)
        tgt = dict(mode='mmax', **c['target']) if 'mode' not in c['target'] else c['target']
        L = measure(y, tgt)
        g = tgt['lufs'] - L
        src = c['src']
        if 'file' in src: sdesc = dict(type='file', file=src['file'], **{'in': src['a'], 'out': src['b']})
        elif 'design' in src: sdesc = dict(type='synth', design=src['design'], fn='synth.py')
        else: sdesc = dict(type='layers', layers=[({'file': L2['file'], 'in': L2['a'], 'out': L2['b']} if 'file' in L2 else {'design': L2['design']})
                                                  | {'at': L2['at'], 'gain_db': L2.get('g', 0.0), 'hp': L2.get('hp'), 'lp': L2.get('lp')}
                                                  for L2 in src['layers']])
        e = dict(kind='hit', prio=c['prio'], primary=c['prio'] == 1, layer_of=c.get('layer_of'), shots=c['shots'], what=c['what'],
                 source=sdesc, sync=c.get('sync', 0.0), offset=c.get('offset', 0.0), fin=c.get('fin'), fout=c.get('fout'),
                 hp=c.get('hp'), lp=c.get('lp'), verb=c.get('verb'), target=tgt, measured_lufs=round(L, 2), gain_db=round(g, 2),
                 clip_s=round(len(y) / SR, 3), peak_after_gain_dbfs=round(20 * np.log10(np.abs(y).max() * 10 ** (g / 20) + 1e-12), 1),
                 rule=c.get('rule'), variants=c.get('variants'), extra_event=c.get('extra'), rank=c.get('rank'),
                 approved_test=bool(c.get('approved')))
        out['cues'][cid] = e
        if write_previews:
            sf.write(os.path.join(pdir, cid + '.wav'), (y * 10 ** (g / 20)).astype(np.float32), SR, subtype='PCM_24')
        print(f'{cid:14s} p{c["prio"]} {e["clip_s"]:5.2f}s  measured {L:6.1f} -> target {tgt["lufs"]:6.1f}  gain {g:6.2f} dB  peak {e["peak_after_gain_dbfs"]:6.1f}')
    for name, b in BEDS.items():
        g = 20 * np.log10(bed_gain(name))
        y = bed(name, 0.0, 10.0)
        e = dict(kind='bed', what=b['what'], gain_db=round(g, 2), lufs_10s=round(meter.integrated_loudness(y), 2))
        if 'loop' in b: e['loop'] = dict(file=b['loop']['file'], **{'in': b['loop']['a'], 'period_s': round(b['loop']['L'], 4), 'xfade_s': b['loop']['x']}, phase_s=b.get('phase', 0.0))
        if 'base' in b: e['base'] = b['base']
        for k in ('hp', 'lp', 'synth', 'add', 'calib', 'lufs'):
            if k in b: e[k] = b[k]
        out['beds'][name] = e
        print(f'bed {name:12s} gain {g:6.2f} dB  10 s loudness {e["lufs_10s"]:6.1f} LUFS')
    json.dump(out, open(MAP_PATH, 'w'), indent=1)
    print('wrote', MAP_PATH)
    return out


if __name__ == '__main__':
    build()
