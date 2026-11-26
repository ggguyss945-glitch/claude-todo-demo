"""Sound effects for "If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME" (THIS film's names
are OBSESSION_NAMES in audio/sfx_obsession.py, executed last: Evie's chalk, the song's pings, the clank, this film's
foley and beds; DEFAULT_GAIN gives the cast's levels to cues without gain_db). Before it: "If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET" (THIS film's names are
BUTTONS_NAMES in audio/sfx_buttons.py, executed last: tik, ping, this film's foley and beds). Before it: "If Your Little
Brother Says Someone Lives In The Walls... DON'T LAUGH" (WALLS_NAMES in audio/sfx_walls.py, executed after
sfx_ice.py). Before that: "If The Ice Cream Truck Plays Its Song In
Winter... DON'T GO OUTSIDE" (the police film's v2 SFX
engine, as the delivery, dummy, Bunnyman, Doctor and Bus films extended it; THIS film's names are ICE_NAMES in
audio/sfx_ice.py, executed here just before RECIPES; the Bus film's BUS_NAMES and every earlier name stay available): recorded, layered, perspective-processed, 48 kHz stereo float.

Every sound is built from the recorded library (the owner's Epidemic files first, then the free CC0/CC-BY library in
catalog.json via library.py), cut into single events ("grains") automatically, layered 2-3 deep (e.g. a knock =
recorded knuckle/door hit + modal door-body thump + hallway convolution), varied by seed and never repeating the same
grain back to back. Synthesis is used only to fill gaps or add a layer (door-body modes, sub booms, sirens with
doppler, ring-back tones, CRT power-off, squelch tails).

Public API
    render(name, seed=0, space=None, level=0.0, **params) -> np.ndarray float32 [n, 2] at 48 kHz
    render_event(name, seed=0, space=None, level=0.0, **params) -> (audio, pre_s)
        pre_s = seconds of audio that come BEFORE the cue time t, so mix.py places the audio at t - pre_s:
        a riser ends at t, a whoosh / car_pass / siren pass peaks at t, a hit's transient lands on t.
    NAMES       POLICE_NAMES (the 42 police names) + DELIVERY_NAMES (the delivery film) + DUMMY_NAMES (the dummy film)
                + BUNNY_NAMES (this film, see the end of this docstring)
    SPACES      'close', 'inside', 'outside', 'doorbell_mic' (+ 'street', 'phone', 'radio', 'car', 'dry', and for this
                film 'porch' (on the porch, exterior shots), 'window' (outdoors heard through an open window), 'upstairs'
                (through the ceiling / far up the stairs), 'box' (inside the cardboard box), 'app' (the doorbell camera's
                live audio played by the phone)). SPACE_ALIAS maps loose words ('hall', 'camera', 'van', ...); any other
                space falls back to the name's DEFAULT_SPACE with a warning.
    resolve(name, params) -> (name, params, note)   aliases ('ding_dong', 'keys_bowl', 'eye_flash', 'sob', ...) and a
                keyword guess for unknown names ('box_rattle' -> 'box_creak'); (None, params, note) when nothing fits.
                render_event() resolves first and raises KeyError only for a name nothing fits (mix.py skips those with
                a warning; see mix.py for the retry/skip policy).
    TIMED       names whose recipe needs the cue's absolute film time (mix.py passes cue_t): hazard_ticks
    LEVEL_LU    house level of each name in LU relative to the narration's integrated loudness
    BEDS        continuous names (take dur; calibrated by integrated loudness; mix.py ducks them with the music)
    HITS        names mix.py treats as hits (bed dips just before them, never ducked)
    DEFAULT_SPACE  per-name default perspective
    space(y, kind, seed=0, wet=None) -> stereo      perspective processing on any audio
    ir(name) -> [n, 2]    unit-energy IRs: recorded OpenAIR 'live', 'hall', 'recital', 'church', 'reactor', 'forest';
                          synthetic (image-source early reflections + per-band exponential tail) 'hallway', 'living',
                          'porch', 'street', 'car'
    reset()     clears the recent-pick memory (mix.py calls it before rendering a cue sheet, so renders are repeatable)
    helpers reused by mix.py: lufs_int, mom_max, kw, follow, compress, eq, hp, lp, bp, st, mono, fade, pan

Calibration: output loudness is absolute for a mix whose voice sits at -14 LUFS integrated. One-shots: momentary
(400 ms) maximum = -14 + LEVEL_LU[name] + SPACE_LU[space] + level (+ a force/intensity term); beds: integrated
loudness the same way. gain_db = 0 in sfx_cues.json therefore gives the house level.

Parameters (all optional; unknown keys are ignored; every name accepts seed, space, level, dur where it makes sense)
    knock_door      n=3, spacing=0.32, force=0.7 (0..1) or strength (Acting: 1.0..1.4 -> force 0.7..1.0),
                    accel=0 (0..0.3 speeds up), material='wood'|'glass', door=1
    doorbell_chime  -                                footsteps_porch / footsteps_wood_inside  n or dur, rate=1.8
                                                     steps/s, approach=0 (+1 nearer, -1 away), creak=0.3, weight=0.7
    car_pass        dist=1 (x reference distance), direction=1|-1, dur=None (window around the pass)
    car_idle        dur=8              car_door_open / car_door_close  -      siren_far  dur=12, dist=1, synth=False,
                                                     mode='wail'|'yelp', speed=0 (m/s, >0 = drive-by with doppler)
    police_radio_squelch  kind='key'|'unkey'|'burst'  radio_click  -   radio_static  dur=3, amount=0.6
    bodycam_beep    n=2                phone_ring  dur=None or n=2, kind='ring'|'ringback'   phone_busy  dur=3
    phone_vibrate   n=2                phone_pickup -    mail_slot  paper=False    paper  dur=1.2
    pen_click       n=1                key_in_lock  -    lock_turn  -              chain_lock  action='lock'|'unlock'
    door_creak      dur=None (stretch), slow=1.0         breath  kind='nervous'|'panic'|'panting'|'gasp'|'held', dur=3
    heartbeat       bpm=70, bpm_end=None, dur=6          whoosh  kind='soft'|'hard'
    riser           dur=6              braam  key='d'    impact_hit  size=1.0 (0.5..1.5)   sub_drop  -   stinger  -
    glitch          dur=0.6, amount=0.7                  ui_pop  -   typing  dur=3, cps=7   tinnitus  dur=4, freq=None
    ambience_night  dur=30, dog=0.5, wind=0.5, buzz=0.5  room_tone  dur=10       clock_tick  dur=6, bpm=60
    countdown_tick  n=1, spacing=1.0, rise=0 (semitones per tick)                tv_off  -
    crowd_whisper   dur=4, density=6 (voices per second)

Delivery film names (built from the owner's Epidemic files first: the new delivery set, then the police and mirror
sets; free library and synthesis only as extra layers). Default space in brackets.
    doorbell_dingdong  kind='house'|'old', n=1, spacing=None (re-rings) [inside]   the house chime, recorded ding-dong
                       + a chime-box knock; doorbell_chime now defaults to kind='ding_dong' (= this recipe; 'reception'
                       gives the police chime)
    doorbell_cam_chime -  [close]   the smart-doorbell app chime on your phone: a recorded ding-dong up 5 semitones
                       through a phone-speaker EQ + a soft UI ping
    phone_notify    kind='app'|'text', vibrate=True [close]    the app notification (3:07, the delivery photos)
    box_knock       n=1 | pattern=[2, 1] or '2-1' (two, a pause, one), gap=0.3, pause=0.72, strength=1.0 (0.5..1.4)
                    or force (0..1.2) [outside]   a knuckle on cardboard from INSIDE the box: cardboard impact (top end
                    soaked up), muffled wood knock, box-panel modes 58-320 Hz, a low sub thump, a flap rattle.
                    characters.BoxActing emits one event per knock (n_in_pattern, group, strength): n=1 default.
                    Tuned to read on a phone speaker: 5-10 dB of its loudness stays above 300 Hz in every space (the
                    police door knock: 8-10 dB); the transient of the first knock lands on the cue time.
    box_tap         n=1, spacing=0.22 [doorbell_mic]   fingertip / nail on the label      box_creak  dur=0.6  [doorbell_mic]
    box_drop        -  [doorbell_mic]  set down on the mat     box_scrape  dur=0.8, surface='mat'|'concrete' [doorbell_mic]
    box_open        keys=False (rusted keys rattle inside) [close]      box_voice  dur=4 (BED under the box's lines:
                    dark air, cardboard creaks, a breath inside) [box]
    tape_rip        kind='rip'|'cut'|'peel', dur=None [close]  (cut: a blade through parcel tape, fibres ticking)
    hazard_ticks    dur=10, rate=1.25, duty=0.48, t_on=None, t_off=None (film s; sets.hazard() defaults) [street]
                    BED: relay tick on / tock off, phase-locked to sets.hazard() through cue_t (mix.py passes it)
    van_door_slide  action='close'|'open' [street]  close: the slam lands on t; open: the roll starts at t
    van_idle        dur=8 (BED) [street]           van_pull_away  dur=7 (idle -> rev -> drives off) [street]
    van_step        -  [doorbell_mic]  boot on the van's step + body creak
    keys_drop       surface='bowl'|'wood'|'carpet', rust=False [inside]   bowl: keys + ceramic ring + settle rattle
    window_slide    action='open'|'close', speed=1.0 [close]      curtain_flutter  dur=4, wind=0.6 [close]
    cloth_rustle    kind='rustle'|'grab' [close]     touch_tap  n=1, spacing=0.25 [close]
    stylus_scribble dur=0.8 [close]  rubber stylus squeaks on glass   camera_shutter  kind='tablet'|'camera' [doorbell_mic]
    footsteps_stairs direction='up'|'down', n or dur, rate=1.5, weight=0.6 [inside]
    footsteps_hall  n or dur, rate=1.7, approach=0 (socks / bare feet on wood) [inside]
    mom_breath      kind='shaky'|'gasp'|'held'|'sniff', dur=3 [close]     mom_sob  dur=3, intensity=0.7 [close]
                    (breath kind='sob' / 'shaky' / 'sniff' route here too)
    ambience_suburb dur=30, dog=0.25, wind=0.4, buzz=0.3, traffic=0.4 (BED) [outside]
    ambience_dawn   dur=30, birds=0.6 (BED; birdsong windows chosen away from the roosters) [outside]
    room_tone_house dur=10, hum=0.3, clock=0.0 (BED) [inside]
    hazard_tick     kind='on'|'off' [street]   ONE relay click (film.py cues every tick from sets.hazard_ticks());
                    mix.py puts it on the bed bus (BED_BUS) so the music's foley dip does not pump at 1.25 Hz
    window_latch    - [close]   a hand tries a locked window: latch clack + frame thud, twice (rule 7 montage)
    stinger         kind='eye_flash': short glassy flash for the driver's eyes on the doorbell camera
    knock_door      soft=True: a light palm / single soft knock
    Small-speaker presence (measured: loudness left above 300 Hz): box sounds heard through the door ('outside') get
    _door_presence (the knuckle / carton attack through the door gap), bare-foot stairs and hall steps _foot_presence;
    footsteps_porch 'outside' gets _door_presence too. Layers of keys_drop (bowl ring), van_step and box_drop land on
    the recorded impact, not on the grain start.
    Params film.py uses on police names: memory=True on ANY name (21 years ago: duller, tape wow, more room);
    car_pass kind='away' (= van_pull_away, starts at t) | 'arrive' (draws up and stops, starts at t);
    car_idle kind='diesel' (= van_idle); chain_lock kind='rattle'; cloth_rustle kind='curtain' (= curtain_flutter),
    dur; footsteps_wood_inside stairs=True (direction), run=True, slippers=True, foot='L'|'R'; footsteps_porch foot;
    keys_drop bowl=True, jingle=True, lift=True; tape_rip soft=True (peel); ui_pop kind='speaker' (the doorbell's
    two-way speaker opening); van_door_slide kind='open'|'close'; box_knock on='porch'|'door'|'vent', small=True.

Dummy film names (DUMMY_NAMES; the owner's dummy set W/samples/epidemic first: wooden pole / blocks / box lid / woody
click, spoon and mug, studio laughter, the old hifi and the VHS deck, the boy's and the men's laughs, the female screams,
the heart monitor; then the delivery, police and mirror sets and the free library). Default space in brackets; levels
in LEVEL_LU (gain_db 0 = the house level; the cast's own gains, CAST.md, ride on top).
    dummy_clack     kind='snap' (deliberate: "Clack.") | 'slow' (after a slow close) | 'speech' (one per word while he
                    talks, -1 dB, the cast sends -14..-8) [tight]   dry hardwood click, the hollow head's 410-2650 Hz
                    modes, a contact click, the hinge's low thock; the transient lands on the cue
    dummy_jaw       kind='drop' [tight]   the jaw bottoming out: a dull wooden knock + the bounce (2 tiny rattles)
    eyelid_click    kind='shut' | 'open' (a tone lower, -5 dB) | 'wink' [tight]   a doll's wooden lid: a tiny click, the
                    glass eye's ring, the lid settling ("Click, click.")
    wood_creak      kind='tick' (dur 0.08-0.3: a finger, an elbow) | 'grind' (the 180-degree head turn, dur default 3:
                    a long groan fitted to dur, pitched down, the neck's ratchet ticking under it, +2 dB) | 'creak' [tight]
    wood_knock      n, spacing, size [close]   his wooden body on a chair / table / stair
    tiny_steps      n or dur, rate=3.0 (steps/s), approach [inside]   a knee-high wooden figure walking (heel + toe)
                    (footsteps_wood_inside kind='tiny' routes here, +4 dB)
    glove_lift      [close]   a small cotton glove lifting off the table (cloth_rustle kind='glove' routes here, +10 dB)
    hand_slot       dur=1.0 [tight]   a hand through the slot in his back: fabric, the slot's wooden edge, the hollow
                    answering (cloth_rustle kind='slot' routes here, +6 dB)
    hand_squeeze    [tight]   one soft squeeze: fabric, two hands' skin creaking, a faint pressure thump
    case_latch      kind='pop' | 'close' [close]   a brass latch of the leather case: latch, brass ring, case body
    case_lid        action='open' (the squeaky hinge, the lid back on the table) | 'close' [close]
    velvet          dur=0.8 [tight]   fingers in the red velvet lining
    spoon_stir      dur=3.0, clink=False [close]   a teaspoon going round a ceramic mug (use space 'next_room' for the
                    spoon heard from the kitchen)
    spoon_clink     n=3, spacing=0.62 | times=[offsets s] [close]   "Clink. Clink. Clink.": recorded clink + the mug's
                    ceramic ring + the spoon's ring; the first transient on the cue
    mug_set         kind='down' | 'pickup' [close]      sip  [close]   a careful slurp, a swallow, a breath out
    dummy_thud      kind='rug' | 'floor' [close]   face down on the rug: padded body, torso, the head a beat later, limbs
    tv_on           [close]   the old console TV on by itself: switch clunk, degauss thoom, static crackle, flyback whine
    vcr             action='play' | 'insert' | 'rewind' (dur) | 'stop' [close]   Grandpa's old VCR (Into VHS, rewinds)
    tape_hiss       dur (BED) [tv]   the tape running: hiss with flutter, 30 Hz head buzz, mains hum
    studio_laugh    size='short' | 'medium' | 'huge' (three takes layered into one roaring wave, +1.5 dB), dur, swell
                    (fade-in s: a wave rising), align='start' | 'peak' (the crest on the cue) [tv]; on the bed bus
    applause        dur=4 [tv]
    lamp_flicker    dur=1.2, times=[edge offsets s], buzz=0.6 [close]   filament ticks and arcs on every edge, the
                    120 Hz buzz while lit
    lamp_out        kind='out' (tink, pop, the buzz cut, a low whump; pre = 0.25 s, the pop on the cue) | 'on' [close]
    flashlight_click kind='on' | 'off' [close]      flashlight_hum  dur (BED) [dry]
    heart_monitor   dur, bpm=62, bpm_end, flatline_at (s) (DUR bed) [hospital]   the recorded 488 Hz beep
    monitor_flatline dur=4, beeps=2, bpm=38 [hospital]
    mom_scream      kind='mid' | 'short' | 'falling', breath=True (a gasp first; pre = 0.3) [close]
    snort           [close]   Owen's stifled laugh through the nose      owen_giggle  dur [close]
    owen_cry        kind='cry' | 'whimper' (dur, DUR bed) | 'shriek' [close]
    winks_laugh     kind='giggle' (a man's laugh up 6 semitones, boxed in the head, a jaw tick per syllable) | 'dark'
                    [tight]   (not in the script: for the director, sparingly)
    goodnight_hit   swell=0.9 [dry] HIT   "Goodnight, Owen." in near silence: a reversed air swell into a deep soft sub
                    thump and a low D-A fifth, the washed braam under it; pre = swell (the thump on the cue)
    old_clock       dur, bpm=60 (BED) [dry]      hospital_tone / museum_tone  dur (BED) [dry]
    house_creaks    dur, density=0.12 (BED) [dry]   the old house settling: sparse distant timber creaks
    tape_glitch     kind='stop' (the tape drags to a halt) | 'tracking' | 'warble', dur [tv]
    keys_jangle     [close]   (keys_drop kind='jangle' routes here)
    paper_slide     dur=0.8 [tight]   the P.S. sliding out of the slot (paper kind='slide' routes here, +5 dB)
    Spaces added: 'tight' (dry, close: the jaw, the eyelids, on a lap), 'next_room' (through the doorway: the kitchen),
    'tv' (the old console TV's speaker), 'tape' (the 1974 tape's own sound, full-frame), 'hospital', 'museum',
    'behind_glass' (the display case), 'memory' (close + memory_fx). Aliases: kitchen / doorway -> next_room,
    television / screen -> tv, studio -> tape, ward -> hospital, gallery -> museum, glass / display -> behind_glass.
    The cast's names (CAST.md "Sound events the cast emits") are all recipes or route by kind: dummy_clack, dummy_jaw,
    eyelid_click, wood_creak, flashlight_click, dummy_thud, case_latch, hand_squeeze, snort, sip, paper (kind 'slide'),
    cloth_rustle (kind 'grab' / 'glove' / 'slot'), breath ('sniff' +10, 'gasp' +3, 'sob' +2 dB: the cast sends them at
    -8..-12), keys_drop (kind 'jangle'), footsteps_wood_inside (kind 'tiny'), whoosh.

Bunnyman film names (BUNNY_NAMES; the owner's bunny set W/samples/epidemic first: every file judged in
W/mix/sfx_review.md (use / process / reject); then the dummy, delivery, police and mirror sets and the free library;
synthesis for the egg's plastic shell, the ring, the brass flap, the barrel's steel, the bulb, the zipper, the curtain
rings, the VHS pause; the real Laurie's crying is her own voice through audio/voicesynth.py). Default space in
brackets; levels in LEVEL_LU (one-shots momentary max, beds integrated, LU rel the voice at gain_db 0).
    ambience_woods  dur, crickets=0.6, owl=0.5, wind=0.5, frogs=0.25, dog=0 (BED) [window]   the night at the treeline:
                    field crickets (the close single cricket kept back), frogs, wind in bare branches, the tawny owl
    owl_hoot        [woods]   one owl call        dogs_search  dur, n_dogs (DUR) [woods]   1987: the search dogs
    crowd_parade    dur, cheer, drums, applause, swell_at (BED) [dry]   the 1987 parade (kids close, adults far)
    hospital_corridor dur, busy (BED) [dry]      hospital_room  dur, hum (BED) [dry]
    burn_barrel     dur, ignite=False, size (BED) [porch]   embers, a low flame body, the steel ticking; ignite: whoomp
    plastic_melt    dur (DUR) [porch]   the egg melting: sizzle, bubbles, sagging crackle
    egg_tap         [inside]  "one soft tap on the front door"      egg_set  surface='mat'|'wood' [porch]
    egg_rattle      dur, strength [outside]   the egg rocking on the mat, the ring loose inside
    egg_open        ring=True [close]   the old halves pop apart, the shell rings, the ring clinks
    ring_roll       dur [close]   the ring rolling round the plastic half       ring_drop  surface='hand'|'egg'|'floor'
    ring_hand       kind='take'|'pocket' [close]     oven_mitt  dur [close]
    knock_family    beat=0.476, groups=[s, s, s], force, soft, door [inside]   THE family knock 2-3-2 on the jingle's
                    beat (knocks on beats 0, 1 | 3, 3.5, 4 | 6, 7); groups move each group into the narration's gaps
                    (spacing inside a group stays on the beat); soft=True: Grandma on the kitchen table (memory=True)
    slot_flap       action='open'|'hold' (dur)|'close'|'snap' [inside]   the brass mail slot: the spring hinge creak,
                    held open (faint strain), let down, snapped shut
    girl_cry        dur, intensity, seed_voice, sobs (DUR) [slot]   the real Laurie crying (her own voice, voicesynth.cry;
                    sobs: the picture's sob catches, s from the cue)
    jingle          version ('speaker' | 'vhs' | 'parade' | 'musicbox' | 'hum' | 'hum_x' | 'girl' | 'knocks' |
                    'climax' | 'count' | 'outro' | 'studio'), dur, stop ('fade'|'cut'|'drag'), + jingle.render keys
                    (DUR) [dry]   the Pemberton's jingle as a sound in the scene (the score plays it as 'jingle' events)
    attic_door      action='open'|'close' [inside]     bulb  kind='chain'|'buzz' (dur) [attic]
    chest_lid       action='open'|'close' [attic]      page_flip  n, rate [attic]     diary_lock [attic]
    window_smash    [next_room] HIT   the kitchen window explodes (glass x2, the frame, shards, a low thump)
    door_crash      [next_room] HIT   the back door kicked in, into the wall, splinters
    wet_drag        dur, wet [next_room]   something heavy, wet, dragging on the kitchen boards
    hatchet_step    n, rate=0.75, weight [door]   a slow heavy tread, then 0.3 s later the hatchet head knocking the
                    step ("Thunk."): the k-th Thunk lands at t + k / rate + 0.3
    doorknob        kind='turn'|'rattle' [bathroom]      paper_under_door  dur [bathroom]
    struggle        kind='wall'|'shake'|'slam'|'crack'|'full' (dur) [door]   the fight in the hall, from the bathroom:
                    restrained (no library screams: the voiceover carries them); 'slam' pre = 0.25 s (the hit on t)
    key_outside     [bathroom]   the key in the bathroom lock from the hall side; pre = 0.75 (the bolt on the cue)
    sirens_arrive   dur, n_cars [street]   police cars pulling up at dawn
    vhs_pause       kind='pause' (dur: the paused deck's hum and tracking noise) | 'play' [dry]   the comment prompt
    light_switch    kind='wall'|'porch'|'porch_off' [close]     music_box_wind  dur [close]
    flash_pop       [close]   the 1987 newspaper camera (shutter, flash, winder)
    bathtub         kind='settle'|'squeak' [bathroom]   body_fall_stairs  n [door]   zipper  dur [close]
    fridge_paper    [close]   the rules go up      curtain_close  dur [close]   (rings on the rod)    peephole [close]
    Spaces added: 'woods' (deep in the trees, -12), 'door' (the hall heard from inside the shut bathroom: panel boom,
    the crack under the door, the tiled room, -6), 'bathroom' (inside it), 'slot' (through the brass mail slot, -4),
    'vhs' (the 1987 camcorder tape: audio/jingle.camcorder), 'attic'. IRs added: 'bathroom', 'attic' (image-source).
    Aliases (ALIASES) and keyword guesses (KEYWORDS, bunny words first): woods, owl, parade, fire, barrel, egg, ring,
    family_knock, secret_knock, mail_flap, crying, song / pembertons / hum / music_box (-> jingle), attic, bulb_chain,
    chest, pages, smash, kick_in, drag, hatchet, thunk, knob, fight, slam, crack, sirens, pause, porch_light, zip...
"""
import os, sys, json, math, hashlib
from collections import OrderedDict, defaultdict, deque
import numpy as np, soundfile as sf
from scipy import signal
import soxr
from numba import njit

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import library as LIB

SR = 48000
REF = -14.0
W = os.path.normpath(os.path.join(HERE, '..', '_work'))   # this film's work dir (never the police project's)
S = W
CACHE = os.path.join(W, 'cache', 'sfx')

POLICE_NAMES = ('knock_door', 'doorbell_chime', 'footsteps_porch', 'footsteps_wood_inside', 'car_pass', 'car_idle',
         'car_door_open', 'car_door_close', 'siren_far', 'police_radio_squelch', 'radio_click', 'radio_static',
         'bodycam_beep', 'phone_ring', 'phone_busy', 'phone_vibrate', 'phone_pickup', 'mail_slot', 'paper',
         'pen_click', 'key_in_lock', 'lock_turn', 'chain_lock', 'door_creak', 'breath', 'heartbeat', 'whoosh',
         'riser', 'braam', 'impact_hit', 'sub_drop', 'stinger', 'glitch', 'ui_pop', 'typing', 'tinnitus',
         'ambience_night', 'room_tone', 'clock_tick', 'countdown_tick', 'tv_off', 'crowd_whisper')
DELIVERY_NAMES = ('doorbell_dingdong', 'doorbell_cam_chime', 'phone_notify', 'box_knock', 'box_tap', 'box_creak',
                  'box_drop', 'box_scrape', 'box_open', 'box_voice', 'tape_rip', 'hazard_ticks', 'van_door_slide',
                  'van_idle', 'van_pull_away', 'van_step', 'keys_drop', 'window_slide', 'curtain_flutter',
                  'cloth_rustle', 'touch_tap', 'stylus_scribble', 'camera_shutter', 'footsteps_stairs', 'footsteps_hall',
                  'mom_breath', 'mom_sob', 'ambience_suburb', 'ambience_dawn', 'room_tone_house', 'hazard_tick',
                  'window_latch')
DUMMY_NAMES = ('dummy_clack', 'dummy_jaw', 'eyelid_click', 'wood_creak', 'wood_knock', 'tiny_steps', 'glove_lift',
               'hand_slot', 'hand_squeeze', 'case_latch', 'case_lid', 'velvet', 'spoon_stir', 'spoon_clink', 'mug_set',
               'sip', 'dummy_thud', 'tv_on', 'vcr', 'tape_hiss', 'studio_laugh', 'applause', 'lamp_flicker', 'lamp_out',
               'flashlight_click', 'flashlight_hum', 'heart_monitor', 'monitor_flatline', 'mom_scream', 'snort',
               'owen_giggle', 'owen_cry', 'winks_laugh', 'goodnight_hit', 'old_clock', 'hospital_tone', 'museum_tone',
               'house_creaks', 'tape_glitch', 'keys_jangle', 'paper_slide', 'clock_chime', 'tv_voice', 'rule_lie')
BUNNY_NAMES = ('ambience_woods', 'owl_hoot', 'crowd_parade', 'hospital_corridor', 'hospital_room', 'burn_barrel',
               'plastic_melt', 'egg_tap', 'egg_set', 'egg_rattle', 'egg_open', 'ring_roll', 'ring_drop', 'ring_hand',
               'oven_mitt', 'knock_family', 'slot_flap', 'girl_cry', 'jingle', 'attic_door', 'bulb', 'chest_lid',
               'page_flip', 'diary_lock', 'window_smash', 'door_crash', 'wet_drag', 'hatchet_step', 'doorknob',
               'paper_under_door', 'struggle', 'key_outside', 'sirens_arrive', 'vhs_pause', 'light_switch',
               'music_box_wind', 'flash_pop', 'dogs_search', 'bathtub', 'body_fall_stairs', 'zipper', 'fridge_paper',
               'curtain_close', 'peephole')
# the final mix: film.py's picture names the recipes above did not cover (sfx_plan.PICTURE maps them)
FINAL_NAMES = ('footsteps_grass', 'wind_gust', 'police_radio', 'swap', 'marker_strike', 'water_tap', 'creek',
               'magnet_click', 'magic_sparkle')
NAMES = POLICE_NAMES + DELIVERY_NAMES + DUMMY_NAMES + BUNNY_NAMES + FINAL_NAMES

# v2.1 (sound critic): foley raised so it reads over the music (footsteps -11 -> -7, typing -14 -> -9,
# pen -11 -> -6, paper -13 -> -9, breath -13 -> -8, radio_click -11 -> -8, chain -8 -> -1, creak -9 -> -3,
# key -10 -> -4, clock -15 -> -8; measured against the music in the final mix); hits sized down (impact_hit +1 -> -2, stinger 0 -> -2, braam -1 -> -3: AUDIO_SPEC hit peak +2 / +9)
LEVEL_LU = dict(knock_door=-3, doorbell_chime=-6, footsteps_porch=-7, footsteps_wood_inside=-8, car_pass=-12,
                car_idle=-23, car_door_open=-10, car_door_close=-6, siren_far=-15, police_radio_squelch=-8,
                radio_click=-8, radio_static=-19, bodycam_beep=-8, phone_ring=-7, phone_busy=-12, phone_vibrate=-9,
                phone_pickup=-8, mail_slot=-6, paper=-9, pen_click=-6, key_in_lock=-4, lock_turn=-6,
                chain_lock=-1, door_creak=-3, breath=-8, heartbeat=-8, whoosh=-9, riser=-5, braam=-3,
                impact_hit=0, sub_drop=-4, stinger=-2, glitch=-8, ui_pop=-12, typing=-9, tinnitus=-15,
                ambience_night=-25, room_tone=-31, clock_tick=-8, countdown_tick=-8, tv_off=-9, crowd_whisper=-13)
# delivery film: one-shots are momentary max, BEDS (and dur-given DUR_BEDS) integrated, LU rel the voice
# final mix (measured by measure_mix.py against the voice + music where each cue lands): touch_tap -12 -> -8,
# camera_shutter -7 -> -4, cloth_rustle -12 -> -9, box_creak -11 -> -7, phone_notify -10 -> -8 (all were 16-25 LU
# under the voice + music, i.e. inaudible); impact_hit -2 -> 0 (the reveal hits peaked ~4 LU under AUDIO_SPEC's +2)
LEVEL_LU.update(doorbell_dingdong=-4, doorbell_cam_chime=-9, phone_notify=-8, box_knock=-2, box_tap=-9, box_creak=-7,
                box_drop=-6, box_scrape=-8, box_open=-6, box_voice=-24, tape_rip=-6, hazard_ticks=-22,
                van_door_slide=-8, van_idle=-24, van_pull_away=-11, van_step=-9, keys_drop=-4, window_slide=-7,
                curtain_flutter=-18, cloth_rustle=-7, touch_tap=-8, stylus_scribble=-11, camera_shutter=-4,
                footsteps_stairs=-8, footsteps_hall=-9, mom_breath=-10, mom_sob=-9, ambience_suburb=-25,
                ambience_dawn=-26, room_tone_house=-31, hazard_tick=-10, window_latch=-7)
# dummy film. One-shots: momentary max, LU rel the voice, at gain_db 0. The cast's events (characters.py) arrive with
# their own gain_db on top (CAST.md): dummy_clack snap 0 / speech -14..-8, dummy_jaw -6, eyelid_click shut 0..-3 /
# open -6..-9, wood_creak tick -8..-14 / grind -4, flashlight_click -6 / -9, dummy_thud 0, case_latch -2,
# hand_squeeze -10 / -12, snort 0, sip -12; these levels put them where they read (clack snap -18 LUFS momentary,
# a speech clack -28..-32, the squeezes -28, the sip -28; the voice sits at -14).
LEVEL_LU.update(dummy_clack=-4, dummy_jaw=-4, eyelid_click=-4, wood_creak=-3, wood_knock=-6, tiny_steps=-8,
                glove_lift=-8, hand_slot=-8, hand_squeeze=0, case_latch=-4, case_lid=-6, velvet=-12, spoon_stir=-8,
                spoon_clink=-4, mug_set=-6, sip=-2, dummy_thud=-5, tv_on=-5, vcr=-9, tape_hiss=-26, studio_laugh=-5,
                applause=-8, lamp_flicker=-8, lamp_out=-6, flashlight_click=0, flashlight_hum=-32, heart_monitor=-16,
                monitor_flatline=-11, mom_scream=-5, snort=-6, owen_giggle=-9, owen_cry=-9, winks_laugh=-8,
                goodnight_hit=-2, old_clock=-27, hospital_tone=-30, museum_tone=-31, house_creaks=-27, tape_glitch=-9,
                keys_jangle=-6, paper_slide=-6, clock_chime=-6, tv_voice=0, rule_lie=-6)
SPACE_LU = dict(close=1.0, inside=0.0, outside=-7.0, doorbell_mic=-2.0, street=-6.0, phone=-4.0, radio=-3.0,
                car=-2.0, dry=0.0, porch=-2.0, window=-8.0, upstairs=-9.0, box=-3.0, app=-3.0,
                tight=1.0, next_room=-4.0, tv=-2.0, tape=-1.0, hospital=0.0, museum=-2.0, behind_glass=-9.0, memory=-1.0)
SPACE_ALIAS = dict(hall='inside', hallway='inside', house='inside', interior='inside', indoors='inside', stairs='inside',
                   room='close', bedroom='close', kitchen='close', near='close', foley='close',
                   door='outside', through_door='outside', behind_door='outside', front_door='outside',
                   camera='doorbell_mic', doorbell='doorbell_mic', cam='doorbell_mic', mic='doorbell_mic',
                   doorbell_cam='doorbell_mic', exterior='porch', outdoors='porch', yard='street', van='street',
                   road='street', far='street', curb='street', speaker='phone', tablet='app', upstairs_hall='upstairs',
                   lily_room='upstairs', none='dry', mono='dry', ui='dry', inside_box='box', cardboard='box')
# dummy film: the kitchen is heard from the hall / living room through the doorway (the rooms are "you" in a close
# shot: give 'close'), the old TV, the 1974 tape full-frame, the hospital memory, the museum and its glass case
SPACE_ALIAS.update(kitchen='next_room', doorway='next_room', other_room='next_room', next_door='next_room',
                   living_room='close', den='close', couch='close', dry_close='tight', jaw='tight', on_lap='tight',
                   arms='tight', television='tv', tv_speaker='tv', screen='tv', set='tv', vhs='tv', studio='tape',
                   broadcast='tape', tape_1974='tape', full_frame='tape', ward='hospital', hospital_room='hospital',
                   bedside='hospital', gallery='museum', glass='behind_glass', display='behind_glass',
                   display_case='behind_glass', flashback='memory', past='memory', stairs_up='upstairs',
                   kitchen_far='next_room', far_kitchen='next_room', from_kitchen='next_room')
SPACES = tuple(SPACE_LU)
PEAK_CAP = defaultdict(lambda: -7.0, knock_door=-5.0, impact_hit=-4.0, braam=-4.0, stinger=-4.0, sub_drop=-4.0,
                       riser=-5.0, car_door_close=-6.0, mail_slot=-6.0, lock_turn=-6.0,
                       doorbell_dingdong=-5.0, box_knock=-5.0, box_drop=-6.0, box_open=-4.0, tape_rip=-4.0,
                       keys_drop=-3.0, camera_shutter=-5.0, touch_tap=-6.0, van_door_slide=-6.0,
                       dummy_clack=-4.0, dummy_jaw=-5.0, eyelid_click=-6.0, case_latch=-5.0, spoon_clink=-4.0,
                       mug_set=-5.0, dummy_thud=-4.0, goodnight_hit=-4.0, mom_scream=-4.0, flashlight_click=-1.0,
                       studio_laugh=-4.0, lamp_out=-5.0, wood_knock=-5.0)
BEDS = ('ambience_night', 'room_tone', 'radio_static', 'car_idle', 'tinnitus', 'phone_busy', 'crowd_whisper',
        'hazard_ticks', 'van_idle', 'ambience_suburb', 'ambience_dawn', 'room_tone_house', 'box_voice',
        'tape_hiss', 'old_clock', 'hospital_tone', 'museum_tone', 'house_creaks', 'flashlight_hum')
DUR_BEDS = ('breath', 'siren_far', 'typing', 'heartbeat', 'curtain_flutter', 'mom_breath', 'mom_sob',
            'heart_monitor', 'owen_cry')   # with dur
TIMED = ('hazard_ticks',)
BED_BUS = BEDS + ('hazard_tick', 'curtain_flutter', 'heart_monitor', 'studio_laugh', 'applause')
# mix.py routes these to the bed bus (no foley dip of the music per relay tick / monitor beep; the open window's
# curtains run for a minute; the studio audience's laughter swells in the gaps and steps back under the narration
# with the music: test 3 measured a 'huge' wave on the events bus 3.5 LU under the voice's momentary peak, mid band)
HITS = ('impact_hit', 'stinger', 'braam', 'sub_drop', 'goodnight_hit')
DEFAULT_SPACE = defaultdict(lambda: 'close', knock_door='inside', footsteps_porch='outside', car_pass='street',
                            car_idle='outside', car_door_open='street', car_door_close='street', siren_far='street',
                            mail_slot='inside', key_in_lock='inside', lock_turn='inside', chain_lock='inside',
                            door_creak='inside', footsteps_wood_inside='inside', ambience_night='outside',
                            room_tone='inside', clock_tick='inside', phone_busy='phone', doorbell_chime='inside',
                            riser='dry', braam='dry', impact_hit='dry', sub_drop='dry', stinger='dry', whoosh='dry',
                            tinnitus='dry', glitch='dry', ui_pop='dry', heartbeat='dry')
DEFAULT_SPACE.update(doorbell_dingdong='inside', doorbell_cam_chime='close', phone_notify='close', box_knock='outside',
                     box_tap='doorbell_mic', box_creak='doorbell_mic', box_drop='doorbell_mic', box_scrape='doorbell_mic',
                     box_open='close', box_voice='box', tape_rip='close', hazard_ticks='street', van_door_slide='street',
                     van_idle='street', van_pull_away='street', van_step='doorbell_mic', keys_drop='inside',
                     window_slide='close', curtain_flutter='close', cloth_rustle='close', touch_tap='close',
                     stylus_scribble='close', camera_shutter='doorbell_mic', footsteps_stairs='inside',
                     footsteps_hall='inside', mom_breath='close', mom_sob='close', ambience_suburb='outside',
                     ambience_dawn='outside', room_tone_house='inside', hazard_tick='street', window_latch='close')
DEFAULT_SPACE.update(dummy_clack='tight', dummy_jaw='tight', eyelid_click='tight', wood_creak='tight',
                     wood_knock='close', tiny_steps='inside', glove_lift='close', hand_slot='tight', hand_squeeze='tight',
                     case_latch='close', case_lid='close', velvet='tight', spoon_stir='close', spoon_clink='close',
                     mug_set='close', sip='close', dummy_thud='close', tv_on='close', vcr='close', tape_hiss='tv',
                     studio_laugh='tv', applause='tv', lamp_flicker='close', lamp_out='close', flashlight_click='close',
                     flashlight_hum='dry', heart_monitor='hospital', monitor_flatline='hospital', mom_scream='close',
                     snort='close', owen_giggle='close', owen_cry='close', winks_laugh='tight', goodnight_hit='dry',
                     old_clock='dry', hospital_tone='dry', museum_tone='dry', house_creaks='dry', tape_glitch='tv',
                     keys_jangle='close', paper_slide='tight', clock_chime='inside', tv_voice='tv', rule_lie='dry')
# ---- the Bunnyman film. One-shots: momentary max, LU rel the voice at gain_db 0; beds (BEDS, and DUR_BEDS given a
# dur): integrated. Spaces: 'woods' (deep in the trees), 'door' (the hall heard from inside the shut bathroom: the
# panel's boom, the gap under the door, the tiled room), 'bathroom' (inside it), 'slot' (through the brass mail
# slot), 'vhs' (the 1987 camcorder tape), 'attic'.
LEVEL_LU.update(ambience_woods=-26, owl_hoot=-4, crowd_parade=-20, hospital_corridor=-28, hospital_room=-32,
                burn_barrel=-24, plastic_melt=-20, egg_tap=-8, egg_set=-12, egg_rattle=-8, egg_open=-6, ring_roll=-10,
                ring_drop=-6, ring_hand=-10, oven_mitt=-12, knock_family=-3, slot_flap=-6, girl_cry=-14, jingle=-18,
                attic_door=-8, bulb=-12, chest_lid=-8, page_flip=-10, diary_lock=-10, window_smash=0, door_crash=-1,
                wet_drag=-12, hatchet_step=-5, doorknob=-9, paper_under_door=-10, struggle=-3, key_outside=-5,
                sirens_arrive=-14, vhs_pause=-10, light_switch=-6, music_box_wind=-12, flash_pop=-8, dogs_search=-20,
                bathtub=-12, body_fall_stairs=-5, zipper=-10, fridge_paper=-9, curtain_close=-10, peephole=-12)
SPACE_LU.update(woods=-9.0, door=-6.0, bathroom=0.0, slot=-4.0, vhs=-2.0, attic=0.0)
SPACE_ALIAS.update(forest='woods', treeline='woods', trees='woods', bathroom_door='door', through_door='door',
                   closed_door='door', hallway_from_bathroom='door', tub='bathroom', mail_slot='slot', letterbox='slot',
                   camcorder='vhs', vcr_tape='vhs', home_video='vhs', loft='attic')
SPACES = tuple(SPACE_LU)
PEAK_CAP.update(window_smash=-3.0, door_crash=-3.0, struggle=-4.0, knock_family=-5.0, hatchet_step=-5.0,
                slot_flap=-6.0, egg_open=-6.0, ring_drop=-6.0, key_outside=-6.0, body_fall_stairs=-5.0, egg_tap=-6.0)
BEDS = BEDS + ('ambience_woods', 'crowd_parade', 'hospital_corridor', 'hospital_room', 'burn_barrel')
DUR_BEDS = DUR_BEDS + ('plastic_melt', 'girl_cry', 'jingle', 'bulb', 'dogs_search')
BED_BUS = BED_BUS + ('ambience_woods', 'crowd_parade', 'hospital_corridor', 'hospital_room', 'burn_barrel', 'jingle',
                     'dogs_search')
HITS = HITS + ('window_smash', 'door_crash')
DEFAULT_SPACE.update(ambience_woods='window', owl_hoot='woods', crowd_parade='dry', hospital_corridor='dry',
                     hospital_room='dry', burn_barrel='porch', plastic_melt='porch', egg_tap='inside', egg_set='porch',
                     egg_rattle='outside', egg_open='close', ring_roll='close', ring_drop='close', ring_hand='close',
                     oven_mitt='close', knock_family='inside', slot_flap='inside', girl_cry='slot', jingle='dry',
                     attic_door='inside', bulb='attic', chest_lid='attic', page_flip='attic', diary_lock='attic',
                     window_smash='next_room', door_crash='next_room', wet_drag='next_room', hatchet_step='door',
                     doorknob='bathroom', paper_under_door='bathroom', struggle='door', key_outside='bathroom',
                     sirens_arrive='street', vhs_pause='dry', light_switch='close', music_box_wind='close',
                     flash_pop='close', dogs_search='woods', bathtub='bathroom', body_fall_stairs='door', zipper='close',
                     fridge_paper='close', curtain_close='close', peephole='close')
# the final mix (FINAL_NAMES): one-shots momentary max, beds / dur-beds integrated, LU rel the voice at gain_db 0
LEVEL_LU.update(footsteps_grass=-9, wind_gust=-10, police_radio=-14, swap=-1, marker_strike=-10, water_tap=-16,
                creek=-16, magnet_click=-12, magic_sparkle=-11)
PEAK_CAP.update(swap=-3.0)
BEDS = BEDS + ('creek',)
DUR_BEDS = DUR_BEDS + ('water_tap', 'police_radio')
BED_BUS = BED_BUS + ('creek', 'water_tap', 'police_radio')
HITS = HITS + ('swap',)
DEFAULT_SPACE.update(footsteps_grass='outside', wind_gust='outside', police_radio='street', swap='dry',
                     marker_strike='close', water_tap='next_room', creek='woods', magnet_click='close',
                     magic_sparkle='vhs')


# ======================================================================================== basic DSP
def st(y):
    y = np.asarray(y, np.float32)
    if y.ndim == 1:
        return np.stack([y, y], 1)
    return y if y.shape[1] == 2 else np.repeat(y[:, :1], 2, 1)


def mono(y):
    return y.mean(1) if y.ndim == 2 else y


def n_(sec):
    return max(1, int(round(sec * SR)))


def no_pop_in(y, head_db=-20.5, body_db=-14.0):
    """The owner's pop-in test (measure_mix.py: first 10 ms > -20 dB re peak AND still > -14 dB at 50-150 ms, i.e. cut
    into a sustained sound): ease such an event in with the shortest raised-cosine fade-in (8-60 ms) that passes."""
    def hb(z):
        m = np.abs(mono(st(z))).astype(np.float64); pk = float(m.max()) + 1e-12
        r = lambda x: float(20 * np.log10(np.sqrt(np.mean(x ** 2)) / pk + 1e-12)) if len(x) else -120.0
        return r(m[:int(0.01 * SR)]), r(m[int(0.05 * SR):int(0.15 * SR)])
    if len(y) < int(0.16 * SR):
        return y
    h, b = hb(y)
    if h <= head_db or b <= body_db:
        return y
    z = y
    for ms in (8, 12, 16, 20, 25, 30, 40, 50, 60):
        n = int(ms * SR / 1000); r = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n))).astype(np.float32)
        z = np.array(y, np.float32, copy=True); z[:n] *= (r[:, None] if z.ndim == 2 else r)
        if hb(z)[0] <= head_db:
            break
    return z


def fade(y, fi=0.002, fo=0.015):
    """Fade the edges. Owner, 23 Nov: a sound must never pop in or stop dead in the middle of itself. If the cut lands
    while the sound is still going (first ms already loud = cut into it; last 50 ms still above -30 dB of the peak =
    cut off while ringing), the edge fade is lengthened: in to 15 ms, out to up to 350 ms (a quarter of the sound)."""
    y = np.array(y, np.float32, copy=True)
    m = np.abs(y if y.ndim == 1 else y.max(1))
    pk = float(m.max()) if len(m) else 0.0
    if pk > 0 and len(m) > n_(0.2):
        head = float(np.sqrt(np.mean(m[:n_(0.001)] ** 2)))
        tail = float(np.sqrt(np.mean(m[-n_(0.05):] ** 2)))
        if head > 0.15 * pk:
            fi = max(fi, 0.015)
        if tail > 0.0316 * pk:
            fo = max(fo, min(0.35, 0.25 * len(y) / SR))
    a, b = min(n_(fi), len(y) // 2), min(n_(fo), len(y) // 2)
    if a > 1:
        w = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
        y[:a] *= w[:, None] if y.ndim == 2 else w
    if b > 1:
        w = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
        y[-b:] *= w[:, None] if y.ndim == 2 else w
    return y


_SOS = {}


def _bw(kind, f, order):
    k = (kind, f, order)
    if k not in _SOS:
        _SOS[k] = signal.butter(order, f, kind, fs=SR, output='sos')
    return _SOS[k]


def hp(y, f, o=2):
    return signal.sosfilt(_bw('highpass', float(f), o), y, axis=0).astype(np.float32)


def lp(y, f, o=2):
    return signal.sosfilt(_bw('lowpass', float(min(f, SR * 0.49)), o), y, axis=0).astype(np.float32)


def bp(y, lo, hi, o=2):
    return signal.sosfilt(_bw('bandpass', (float(lo), float(min(hi, SR * 0.49))), o), y, axis=0).astype(np.float32)


def _rbj(kind, f0, g, q=0.707):
    A = 10 ** (g / 40); w = 2 * np.pi * f0 / SR; c = np.cos(w); s = np.sin(w)
    if kind == 'peak':
        al = s / (2 * q)
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    else:
        al = s / 2 * np.sqrt(2.0) * (q / 0.707) ** -1 if q else s / 2 * np.sqrt(2)
        r = 2 * np.sqrt(A) * al
        if kind == 'ls':
            b = [A * ((A + 1) - (A - 1) * c + r), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - r)]
            a = [(A + 1) + (A - 1) * c + r, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - r]
        else:
            b = [A * ((A + 1) + (A - 1) * c + r), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - r)]
            a = [(A + 1) - (A - 1) * c + r, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - r]
    return np.array(b + a) / a[0]


def eq(y, *bands):
    """bands: (kind, f0, gain_db, q) with kind 'peak' | 'ls' (low shelf) | 'hs' (high shelf)."""
    if not bands:
        return y
    sos = np.vstack([_rbj(*b) for b in bands])
    return signal.sosfilt(sos, y, axis=0).astype(np.float32)


def pan(y, p):
    p = float(np.clip(p, -1, 1))
    if abs(p) < 1e-3:
        return y
    a = (p + 1) * np.pi / 4
    y = st(y).copy()
    y[:, 0] *= np.sqrt(2) * np.cos(a); y[:, 1] *= np.sqrt(2) * np.sin(a)
    return y


def width(y, w):
    y = st(y); m = y.mean(1); s = (y[:, 0] - y[:, 1]) * 0.5 * w
    return np.stack([m + s, m - s], 1).astype(np.float32)


def rate(y, r):
    """Varispeed by ratio r (r > 1: shorter and higher)."""
    if abs(r - 1) < 1e-4:
        return y
    return soxr.resample(np.ascontiguousarray(y, np.float32), SR * r, SR, quality='HQ').astype(np.float32)


def semis(s):
    return 2.0 ** (s / 12.0)


def place(dst, src, i):
    i = int(i)
    a, b = max(0, i), min(len(dst), i + len(src))
    if b > a:
        dst[a:b] += src[a - i:b - i]
    return dst


def peak(y):
    return float(np.max(np.abs(y))) if len(y) else 0.0


def pnorm(y, to=1.0):
    p = peak(y)
    return y * (to / p) if p > 0 else y


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def sat(y, drive=2.0):
    p = peak(y)
    if p <= 0:
        return y
    return (np.tanh(y / p * drive) / np.tanh(drive) * p).astype(np.float32)


@njit(cache=True)
def follow(x, a_att, a_rel):
    """One-pole peak follower with separate attack/release coefficients (exp(-1/(tau*SR)))."""
    out = np.empty_like(x); v = 0.0
    for i in range(x.size):
        xi = x[i]
        if xi > v:
            v = a_att * v + (1.0 - a_att) * xi
        else:
            v = a_rel * v + (1.0 - a_rel) * xi
        out[i] = v
    return out


def coef(tau):
    return float(np.exp(-1.0 / (max(tau, 1e-5) * SR)))


def compress(y, thr_db, ratio=3.0, att=0.005, rel=0.12, knee=6.0, makeup=0.0, key=None):
    d = np.abs(mono(y if key is None else key)).astype(np.float64)
    env = follow(d, coef(att), coef(rel))
    over = db(env) - thr_db
    gr = np.where(over <= -knee / 2, 0.0, np.where(over >= knee / 2, over * (1 - 1 / ratio),
                                                   (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    g = (10 ** ((makeup - gr) / 20)).astype(np.float32)
    return y * (g[:, None] if y.ndim == 2 else g)


# ---------------------------------------------------------------------------------------- loudness (BS.1770)
_KB = (np.array([1.53512485958697, -2.69169618940638, 1.19839281085285]), np.array([1.0, -1.69065929318241, 0.73248077421585]))
_KH = (np.array([1.0, -2.0, 1.0]), np.array([1.0, -1.99004745483398, 0.99007225036621]))


def kw(y):
    return signal.lfilter(*_KH, signal.lfilter(*_KB, y, axis=0), axis=0)


_KSOS = np.vstack([np.concatenate(_KB), np.concatenate(_KH)])
SEG = 0.05


def seg_power(y, seg=SEG):
    """K-weighted mean power (channels summed) per seg-second segment, filtered in chunks (low memory for long mixes).
    Returns (powers, exact) where exact=False means the sound is shorter than one segment (one whole-sound value)."""
    y = st(y); n = len(y); s = n_(seg); m = n // s
    if m == 0:
        z = kw(y.astype(np.float64)); return np.array([(z ** 2).sum() / max(n, 1)]), False
    out = np.empty(m); zi = np.zeros((2, 2, 2)); step = s * 400
    for a in range(0, m * s, step):
        b = min(m * s, a + step)
        z, zi = signal.sosfilt(_KSOS, y[a:b].astype(np.float64), axis=0, zi=zi)
        out[a // s:b // s] = (z * z).sum(1).reshape(-1, s).mean(1)
    return out, True


def _blocks(y, win=0.4, hop=0.1):
    """Mean K-weighted power of win-second blocks every hop seconds (win, hop multiples of 50 ms)."""
    P, ok = seg_power(y)
    k = max(1, int(round(win / SEG))); h = max(1, int(round(hop / SEG)))
    if not ok or len(P) <= k:
        return np.array([P.mean()])
    c = np.concatenate([[0.0], np.cumsum(P)])
    i = np.arange(0, len(P) - k + 1, h)
    return (c[i + k] - c[i]) / k


def mom_max(y):
    return float(-0.691 + 10 * np.log10(_blocks(y).max() + 1e-20))


def lufs_int(y):
    e = _blocks(y)
    L = -0.691 + 10 * np.log10(e + 1e-20)
    e = e[L > -70]
    if not len(e):
        return -70.0
    g = -0.691 + 10 * np.log10(e.mean()) - 10
    e2 = e[-0.691 + 10 * np.log10(e) > g]
    return float(-0.691 + 10 * np.log10((e2 if len(e2) else e).mean()))


def onset_s(y, rel_db=-24):
    """Time of the first sample within rel_db of the peak (the transient)."""
    a = np.abs(mono(st(y)))
    if not len(a):
        return 0.0
    i = int(np.argmax(a > a.max() * 10 ** (rel_db / 20)))
    return i / SR


def env_peak_s(y, smooth=0.25):
    """Time of the loudest `smooth`-second stretch (moving mean of the power, centred; O(n) by cumulative sum)."""
    a = mono(st(y)).astype(np.float64) ** 2
    k = min(n_(smooth), len(a))
    c = np.concatenate([[0.0], np.cumsum(a)])
    e = c[k:] - c[:-k]                                   # window [i, i + k)
    return (int(np.argmax(e)) + k // 2) / SR


# ======================================================================================== impulse responses
_IR = {}
_REC_IR = dict(live='openair2__live_room', hall='openair__central_hall_university_york_ir_centre_stalls',
               recital='openair2__recital_hall', church='openair__1st_baptist_nashville_1st_baptist_nashville_far_close',
               reactor='openair__r1_nuclear_reactor_hall_stereo_r1_ortf_48k', forest='openair__forest_in_wheldrakewood_s1r1_ms')


def _unit(h):
    h = h.astype(np.float32)
    return h / np.sqrt((h ** 2).sum() / 2 + 1e-20)


def _tail(length, t60s, seed, t0=0.02):
    """Decorrelated stereo diffuse tail, per-band exponential decay (bands <250, 250-1k, 1-4k, 4-8k, >8k)."""
    rng = np.random.default_rng(seed); n = n_(length); t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    edges = [(None, 250), (250, 1000), (1000, 4000), (4000, 8000), (8000, None)]
    for ch in range(2):
        x = rng.standard_normal(n).astype(np.float32)
        for (lo, hi), T in zip(edges, t60s):
            b = lp(x, hi, 4) if lo is None else (hp(x, lo, 4) if hi is None else bp(x, lo, hi, 4))
            out[:, ch] += b * np.exp(-6.91 * t / T)
    ramp = np.clip((t - t0) / 0.015, 0, 1)[:, None]
    return out * ramp


def _shoebox(dims, src, mic, betas, order, t60s, length, seed, spread=0.18, tail_db=0.0):
    """Image-source early reflections (per-wall reflection coefficients betas = (x0, x1, y0, y1, z0, z1), HF loss per
    order) for two mics `spread` m apart, plus a per-band exponential diffuse tail."""
    n = n_(length); h = np.zeros((order + 1, n, 2), np.float64)
    L = np.array(dims, float); s = np.array(src, float)
    mics = [np.array(mic, float) + [-spread / 2, 0, 0], np.array(mic, float) + [spread / 2, 0, 0]]
    rng = range(-order, order + 1)
    for nx in rng:
        for ny in rng:
            for nz in rng:
                o = abs(nx) + abs(ny) + abs(nz)
                if o > order:
                    continue
                pos = []; amp = 1.0
                for k, nk in enumerate((nx, ny, nz)):
                    pos.append(nk * L[k] + s[k] if nk % 2 == 0 else (nk + 1) * L[k] - s[k])
                    hi_, lo_ = (math.ceil(nk / 2), nk // 2) if nk > 0 else (abs(nk) // 2, math.ceil(abs(nk) / 2))
                    amp *= betas[2 * k] ** lo_ * betas[2 * k + 1] ** hi_
                if amp < 1e-4:
                    continue
                pos = np.array(pos)
                for ch, m in enumerate(mics):
                    d = max(np.linalg.norm(pos - m), 0.3); x = d / 343.0 * SR
                    i = int(x); f = x - i
                    if i + 1 < n:
                        h[o, i, ch] += amp / d * (1 - f); h[o, i + 1, ch] += amp / d * f
    er = np.zeros((n, 2), np.float32)
    for o in range(order + 1):
        er += lp(h[o].astype(np.float32), 16000 / (1 + 0.8 * o), 2) if o else h[o].astype(np.float32)
    first = np.argmax(np.abs(er).sum(1) > 0)
    tl = _tail(length, t60s, seed, t0=first / SR + 0.012)
    e_er = (er[first + n_(0.004):] ** 2).sum()
    tl *= np.sqrt(e_er / ((tl ** 2).sum() + 1e-20)) * 10 ** (tail_db / 20)
    return _unit(er + tl)


def _street_ir(seed=7):
    rng = np.random.default_rng(seed); n = n_(1.8); h = np.zeros((n, 2), np.float32)
    h[0] = 1.0
    for k in range(9):                                  # facade / car / fence reflections
        d = rng.uniform(0.018, 0.17); g = rng.uniform(0.25, 0.55) * (0.02 / d) ** 0.35
        p = rng.uniform(-0.8, 0.8); i = n_(d)
        h[i, 0] += g * np.cos((p + 1) * np.pi / 4) * np.sqrt(2); h[i, 1] += g * np.sin((p + 1) * np.pi / 4) * np.sqrt(2)
    h[1:] = lp(h[1:], 6000, 2)
    f = ir('forest'); f = f[:n] if len(f) >= n else np.pad(f, ((0, n - len(f)), (0, 0)))
    return _unit(h + 0.55 * f * np.sqrt((h ** 2).sum() / ((f ** 2).sum() + 1e-20)))


def ir(name):
    if name in _IR:
        return _IR[name]
    if name in _REC_IR:
        y = LIB.load(_REC_IR[name])
        if name == 'forest':                             # OpenAIR M/S file -> L/R
            m, s = y[:, 0], y[:, 1]; y = np.stack([m + s, m - s], 1)
        if name == 'reactor':
            y = fade(y[:n_(7.0)], 0, 1.5)
        h = y
    elif name == 'hallway':
        h = _shoebox((1.4, 5.5, 2.5), (0.7, 0.35, 1.3), (0.75, 2.6, 1.6), (0.78, 0.78, 0.7, 0.8, 0.72, 0.8), 3,
                     (0.62, 0.55, 0.46, 0.34, 0.24), 1.2, 11)
    elif name == 'living':
        h = _shoebox((4.6, 5.8, 2.6), (2.0, 1.4, 1.2), (2.7, 4.1, 1.4), (0.75, 0.7, 0.75, 0.65, 0.6, 0.8), 3,
                     (0.6, 0.55, 0.45, 0.35, 0.25), 1.2, 12)
    elif name == 'porch':
        h = _shoebox((3.2, 2.6, 2.7), (1.6, 0.9, 1.5), (1.4, 0.4, 1.4), (0.0, 0.0, 0.85, 0.0, 0.8, 0.55), 2,
                     (0.4, 0.35, 0.3, 0.22, 0.15), 0.6, 13, tail_db=-9)
    elif name == 'car':
        h = _shoebox((1.45, 2.3, 1.15), (0.4, 0.6, 0.7), (1.0, 1.6, 0.8), (0.5, 0.5, 0.6, 0.45, 0.35, 0.4), 3,
                     (0.14, 0.12, 0.09, 0.07, 0.05), 0.35, 14)
    elif name == 'street':
        h = _street_ir()
    elif name == 'bathroom':                              # the upstairs bathroom: 1.9 x 2.6 x 2.4 m, tile and porcelain
        h = _shoebox((1.9, 2.6, 2.4), (0.9, 1.9, 1.3), (0.7, 0.8, 0.9), (0.92, 0.9, 0.9, 0.88, 0.85, 0.9), 4,
                     (0.75, 0.7, 0.62, 0.5, 0.36), 1.0, 16)
    elif name == 'attic':                                 # the attic: 4 x 6.5 x 2.2 m, rafters, boxes, insulation
        h = _shoebox((4.0, 6.5, 2.2), (2.2, 1.5, 0.6), (1.6, 4.4, 0.8), (0.55, 0.5, 0.6, 0.45, 0.6, 0.4), 3,
                     (0.42, 0.36, 0.28, 0.2, 0.14), 0.8, 17)
    elif name == 'box':                                   # inside the tall carton (0.42 x 0.42 x 1.25 m, soft walls)
        h = _shoebox((0.42, 0.42, 1.25), (0.2, 0.2, 0.55), (0.24, 0.22, 0.95), (0.55, 0.55, 0.55, 0.55, 0.5, 0.6), 4,
                     (0.09, 0.07, 0.05, 0.035, 0.02), 0.18, 15)
    else:
        raise KeyError(name)
    _IR[name] = _unit(h)
    return _IR[name]


def _conv(x, h):
    x = mono(st(x)).astype(np.float32)
    return np.stack([signal.oaconvolve(x, h[:, 0]), signal.oaconvolve(x, h[:, 1])], 1).astype(np.float32)


def reverb(y, name, wet=0.3, predelay=0.0, dry=1.0, hpf=None):
    y = st(y); h = ir(name)
    src = hp(y, hpf) if hpf else y
    w = _conv(src, h) * wet
    out = np.zeros((len(y) + len(h) + n_(predelay), 2), np.float32)
    out[:len(y)] += y * dry
    place(out, w, n_(predelay))
    return _trim_tail(out)


def _trim_tail(y, thr_db=-75):
    a = np.abs(y).max(1); p = a.max()
    if p <= 0:
        return y[:1]
    idx = np.nonzero(a > p * 10 ** (thr_db / 20))[0]
    end = min(len(y), idx[-1] + n_(0.02))
    return fade(y[:end], 0, 0.02)


# ======================================================================================== perspective spaces
def space(y, kind, seed=0, wet=None):
    """Perspective processing. 'close' near the listener, 'inside' in the hallway, 'outside' heard from inside through
    the closed front door, 'doorbell_mic' through the porch camera's mic (outdoor early reflections, band-limited,
    compressed, mono), 'street' distant outdoors, 'phone', 'radio', 'car' (inside the patrol car), 'dry'."""
    y = st(y)
    if kind in (None, 'dry'):
        return y
    if kind == 'close':
        return reverb(y, 'living', 0.12 if wet is None else wet, 0.002)
    if kind == 'inside':
        return reverb(lp(y, 15000, 1), 'hallway', 0.45 if wet is None else wet, 0.0)
    if kind == 'outside':
        m = mono(y)
        door = eq(lp(m, 1000, 2), ('peak', 160, 5, 1.1), ('peak', 420, 2, 1.5), ('hs', 2200, -9, 0.7))
        leak = bp(m, 1400, 5000, 2) * 0.035           # air gap round the door frame
        d = door + leak
        return width(reverb(d, 'hallway', 0.8 if wet is None else wet, 0.001), 0.6)
    if kind == 'doorbell_mic':
        x = reverb(y, 'porch', 0.35 if wet is None else wet)
        x = mono(reverb(x, 'forest', 0.12, 0.01))
        x = eq(lp(hp(x, 260, 4), 6800, 4), ('peak', 2700, 3.5, 1.2), ('peak', 900, -2, 1.0))
        x = compress(x, db(peak(x)) - 16, 4.0, 0.002, 0.09, makeup=0)
        return st(sat(x, 1.4))
    if kind == 'street':
        return reverb(lp(y, 9000, 1), 'street', 0.6 if wet is None else wet, 0.0, hpf=120)
    if kind == 'phone':
        x = bp(mono(y), 320, 3300, 4); x = sat(compress(x, db(peak(x)) - 14, 3.0, 0.003, 0.1), 1.6)
        return st(x)
    if kind == 'radio':
        x = bp(mono(y), 380, 3200, 4); return st(sat(x, 3.0))
    if kind == 'car':
        return reverb(lp(y, 11000, 1), 'car', 0.35 if wet is None else wet)
    if kind == 'porch':                                   # on the porch, near the source (exterior shots)
        x = reverb(lp(y, 15000, 1), 'porch', 0.25 if wet is None else wet)
        return reverb(x, 'forest', 0.08, 0.008)
    if kind == 'window':                                  # outdoors, heard through an open window
        x = eq(lp(y, 7000, 2), ('hs', 3000, -4, 0.7))
        return width(reverb(x, 'street', 0.5 if wet is None else wet, 0.0, hpf=120), 0.7)
    if kind == 'upstairs':                                # through the ceiling / far up the stairs
        m = mono(y)
        x = eq(lp(m, 1800, 2), ('peak', 180, 4, 1.0), ('hs', 1200, -6, 0.7))
        return width(reverb(x, 'hallway', 0.65 if wet is None else wet, 0.004), 0.5)
    if kind == 'box':                                     # inside the cardboard box: boxy, dull, close
        x = eq(lp(y, 2600, 2), ('peak', 190, 5, 1.2), ('peak', 430, 3, 1.4), ('peak', 950, -3, 1.0))
        return reverb(x, 'box', 0.55 if wet is None else wet, 0.0)
    if kind == 'app':                                     # doorbell camera mic, played by the phone's speaker
        x = mono(space(y, 'doorbell_mic', seed))
        x = eq(bp(x, 300, 7500, 2), ('peak', 2200, 2.5, 1.0), ('ls', 350, -5, 0.7))
        return st(x)
    # ---- dummy film
    if kind == 'tight':                                   # dry and close: the dummy's jaw and eyelids, on a lap
        return reverb(y, 'living', 0.05 if wet is None else wet, 0.001)
    if kind == 'next_room':                               # through the doorway from the next room (the kitchen)
        x = eq(lp(y, 8000, 2), ('hs', 2500, -3.0, 0.7), ('peak', 300, 1.5, 1.0))
        return reverb(x, 'living', 0.42 if wet is None else wet, 0.008)
    if kind == 'tv':                                      # the old console TV's speaker, across the living room
        x = lp(hp(mono(y), 200, 4), 4800, 4)
        x = sat(eq(x, ('peak', 1500, 3.0, 1.0), ('peak', 330, 2.5, 2.0)), 1.5)
        return reverb(x, 'living', 0.2 if wet is None else wet, 0.003)
    if kind == 'tape':                                    # the 1974 tape's own sound (the full-frame studio shots)
        x = sat(lp(hp(mono(y), 110, 2), 7000, 4), 1.25)
        return st(x)
    if kind == 'hospital':                                # a small, hard hospital room
        return reverb(hp(y, 80, 2), 'living', 0.25 if wet is None else wet, 0.002)
    if kind == 'museum':                                  # a big, still gallery
        return reverb(y, 'hall', 0.45 if wet is None else wet, 0.012)
    if kind == 'behind_glass':                            # inside the display case, heard through the glass
        x = eq(lp(y, 1600, 2), ('peak', 420, 3.0, 1.2))
        return reverb(x, 'hall', 0.35 if wet is None else wet, 0.01)
    if kind == 'memory':                                  # the hospital / bedtime memories (render_event adds memory_fx)
        return reverb(y, 'living', 0.12 if wet is None else wet, 0.002)
    # ---- the Bunnyman film
    if kind == 'woods':                                   # deep in the trees across the yard, at night
        x = eq(lp(y, 4800, 2), ('hs', 2500, -3.0, 0.7))
        return reverb(x, 'forest', 0.7 if wet is None else wet, 0.03, dry=0.5)
    if kind == 'door':                                    # the hall, heard from inside the shut bathroom
        m = mono(y)
        panel = eq(lp(m, 1600, 2), ('peak', 220, 4.0, 1.1), ('peak', 480, 1.5, 1.4), ('hs', 1400, -6.0, 0.7))
        gap = bp(m, 1400, 6000, 2) * 0.09                  # the crack under the door (tests: the Thunks read on a phone)
        x = reverb(panel + gap, 'hallway', 0.35, 0.002)
        return width(reverb(x, 'bathroom', 0.22 if wet is None else wet, 0.001), 0.5)
    if kind == 'bathroom':                                # inside the small tiled bathroom
        return reverb(y, 'bathroom', 0.28 if wet is None else wet, 0.001)
    if kind == 'slot':                                    # through the brass mail slot into the hall
        m = mono(y)
        x = eq(bp(m, 300, 3800, 2), ('peak', 1100, 5.0, 1.4), ('peak', 2400, 2.0, 2.0))
        k = n_(0.0036); c = np.zeros_like(x); c[k:] = x[:-k] * 0.35
        x = reverb(x + c, 'porch', 0.15, 0.0)
        return reverb(x, 'hallway', 0.3 if wet is None else wet, 0.002)
    if kind == 'vhs':                                     # 1987 home video (the camcorder at the parade)
        import jingle as JG
        return JG.camcorder(st(y), seed)
    if kind == 'attic':                                   # the attic: low, wooden, boxes everywhere (dead)
        return reverb(lp(y, 9000, 1), 'attic', 0.25 if wet is None else wet, 0.001)
    warn(f'unknown space {kind!r}: using close')
    return space(y, 'close', seed, wet)


# ======================================================================================== sample access, grains, picking
_AC = OrderedDict(); _AC_BYTES = [0]
_GC = None
_RECENT = defaultdict(lambda: deque(maxlen=6))


def reset():
    _RECENT.clear()


def audio(e):
    e = LIB.get(e); k = e['id']
    if k in _AC:
        _AC.move_to_end(k); return _AC[k]
    y = LIB.load(e).astype(np.float32)
    _AC[k] = y; _AC_BYTES[0] += y.nbytes
    while _AC_BYTES[0] > 1.5e9 and len(_AC) > 1:
        _, v = _AC.popitem(last=False); _AC_BYTES[0] -= v.nbytes
    return y


def _gcache():
    global _GC
    if _GC is None:
        p = os.path.join(CACHE, 'grains.json')
        _GC = json.load(open(p)) if os.path.exists(p) else {}
    return _GC


def _gsave():
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, 'grains.json'); tmp = p + '.%d' % os.getpid()
    json.dump(_GC, open(tmp, 'w')); os.replace(tmp, p)


def grains(e, mode='onset', gap=0.25, floor=-40.0, max_len=3.0, min_len=0.03, keep=-24.0):
    """Cut a recording into single events. mode 'onset' (spectral-flux onsets: knocks, steps, keys) or 'phrase'
    (split at gaps >= gap s of near-silence: doorbell phrases, car doors, beeps). Returns [(s0, s1)] in samples.
    Events weaker than `keep` dB under the file's loudest event are dropped. Cached in $S/pov2/cache/sfx/grains.json."""
    e = LIB.get(e)
    key = f"{e['id']}|{mode}|{gap}|{floor}|{max_len}|{min_len}|{keep}"
    gc = _gcache()
    if key in gc:
        return [tuple(g) for g in gc[key]]
    y = mono(audio(e)); hop = 120
    nf = len(y) // hop
    if nf < 4:
        gc[key] = [[0, len(y)]]; _gsave(); return [(0, len(y))]
    fr = y[:nf * hop].reshape(nf, hop)
    env = db(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    env = np.convolve(env, np.ones(3) / 3, 'same')
    noise = np.percentile(env, 10); P = env.max()
    thr = max(P + floor, noise + 6)
    out = []
    if mode == 'phrase':
        act = env > thr; g = int(gap * SR / hop)
        idx = np.nonzero(act)[0]
        if len(idx):
            runs = []; a = idx[0]; b = idx[0]
            for i in idx[1:]:
                if i - b > g:
                    runs.append((a, b)); a = i
                b = i
            runs.append((a, b))
            for a, b in runs:
                out.append((max(0, a * hop - n_(0.004)), min(len(y), (b + 1) * hop + n_(0.03))))
    else:
        import librosa, warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            o = librosa.onset.onset_detect(y=y, sr=SR, hop_length=256, backtrack=True, units='samples',
                                           wait=max(1, int(gap * SR / 256)), delta=0.08)
        o = sorted(set(int(v) for v in o))
        for k, s0 in enumerate(o):
            nxt = o[k + 1] if k + 1 < len(o) else len(y)
            f0 = s0 // hop; f1 = min(nf, nxt // hop)
            if f1 <= f0 + 1:
                continue
            pk = f0 + int(np.argmax(env[f0:f1]))
            after = np.nonzero(env[pk:f1] < max(env[pk] + floor, noise + 3))[0]
            end = (pk + after[0]) * hop if len(after) else f1 * hop
            end = min(end + n_(0.02), nxt - n_(0.004), s0 + n_(max_len))
            out.append((max(0, s0 - n_(0.003)), end))
    res = []
    for s0, s1 in out:
        s1 = min(s1, s0 + n_(max_len))
        if s1 - s0 < n_(min_len):
            continue
        f0, f1 = s0 // hop, max(s0 // hop + 1, min(nf, s1 // hop))
        if env[f0:f1].max() < P + keep:
            continue
        res.append((int(s0), int(s1)))
    if not res:
        res = [(0, min(len(y), n_(max_len)))]
    gc[key] = [list(r) for r in res]; _gsave()
    return res


def src(serves=None, category=None, tag=None, has=None, nothas=None, epi=None, tags=None):
    """Library entries: Epidemic kept even when flagged; free files dropped if clipped or noisy."""
    out = []
    for e in LIB.entries(category=category, serves=serves, tag=tag):
        isepi = e['source'] == 'epidemic'
        if not isepi and any(q.startswith('clip') or q == 'noise_floor_high' for q in e.get('qc', [])):
            continue
        if has and not any(s in e['id'] for s in has):
            continue
        if nothas and any(s in e['id'] for s in nothas):
            continue
        if epi is not None and isepi != epi:
            continue
        if tags and not set(tags) & set(e.get('tags', [])):
            continue
        out.append(e)
    return out


class Pool:
    """Weighted grain pool across several recordings; picks avoid the last few grains used under the same key."""

    def __init__(self, key, entries, mode='onset', epi_w=3.0, **seg):
        self.key = key; self.items = []; self.w = []
        for e in entries:
            gs = grains(e, mode, **seg)
            wt = (epi_w if e['source'] == 'epidemic' else 1.0) / np.sqrt(len(gs))
            for g in gs:
                self.items.append((e['id'], g[0], g[1])); self.w.append(wt)
        self.w = np.array(self.w, float)

    def __len__(self):
        return len(self.items)

    def pick(self, rng, avoid=3):
        n = len(self.items)
        if n == 0:
            raise KeyError('empty pool ' + self.key)
        rec = _RECENT[self.key]; ban = set(list(rec)[-min(avoid, n - 1):]) if n > 1 else set()
        cand = [i for i in range(n) if self.items[i] not in ban]
        w = self.w[cand]; w = w / w.sum()
        it = self.items[cand[int(rng.choice(len(cand), p=w))]]
        rec.append(it)
        return it

    def get(self, rng, rj=0.03, tilt=1.5, avoid=3, fi=0.002, fo=0.02):
        """One varied grain: random varispeed +-rj, high-shelf tilt +-tilt dB, peak-normalised."""
        eid, a, b = self.pick(rng, avoid)
        y = audio(eid)[a:b]
        y = rate(y, 1 + rng.uniform(-rj, rj)) if rj else y
        if tilt:
            y = eq(y, ('hs', 3000, rng.uniform(-tilt, tilt), 0.7))
        return fade(pnorm(y), fi, fo)


_POOLS = {}


def pool(key, entries_fn, mode='onset', **seg):
    if key not in _POOLS:
        _POOLS[key] = Pool(key, entries_fn(), mode, **seg)
    return _POOLS[key]


def excerpt(e, dur, rng, xfade=1.5, active=True):
    """A dur-second stretch of a recording starting at a random point; loops with equal-power crossfades if short."""
    y = audio(e); n = n_(dur); xf = min(n_(xfade), len(y) // 4)
    if len(y) >= n + n_(0.5):
        off = int(rng.integers(0, len(y) - n))
        return fade(y[off:off + n], 0.05, 0.08)
    out = np.zeros((n + xf, 2), np.float32); i = 0
    win = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    while i < n:
        off = int(rng.integers(0, max(1, len(y) // 3)))
        c = y[off:].copy()
        if i > 0:
            c[:xf] *= np.sqrt(win)[:, None]
        c[-xf:] *= np.sqrt(win[::-1])[:, None]
        place(out, c, i)
        i += len(c) - xf
    return fade(out[:n], 0.05, 0.08)


# ======================================================================================== synthesis building blocks
def modal(freqs, decays, amps, dur, seed=0, exc=0.002):
    """Bank of damped resonances excited by a short half-sine pulse (door panel, strike plate, bars)."""
    t = np.arange(n_(dur)) / SR; y = np.zeros_like(t)
    rng = np.random.default_rng(seed)
    for f, d, a in zip(freqs, decays, amps):
        y += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / d)
    k = n_(exc); pulse = np.sin(np.linspace(0, np.pi, k))
    y = np.convolve(y, pulse / pulse.sum(), 'full')[:len(t)]
    return fade(y.astype(np.float32), 0.0008, 0.02)


def sub_boom(f0=58, f1=31, dur=1.6, click=0.15, seed=0):
    t = np.arange(n_(dur)) / SR
    f = f1 + (f0 - f1) * np.exp(-t / (dur * 0.18))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / (dur * 0.33)) * (1 - np.exp(-t / 0.004))
    y = np.tanh(1.6 * y) / np.tanh(1.6)
    if click:
        nz = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t / 0.006)
        y = y + click * lp(nz.astype(np.float32), 2500, 2)
    return fade(y.astype(np.float32), 0.0005, 0.1)


def tone(freqs, dur, amps=None, att=0.004, rel=0.02):
    t = np.arange(n_(dur)) / SR; amps = amps or [1.0] * len(freqs)
    y = sum(a * np.sin(2 * np.pi * f * t) for f, a in zip(freqs, amps))
    return fade(np.asarray(y, np.float32) / len(freqs), att, rel)


def noise(dur, seed=0):
    return np.random.default_rng(seed).standard_normal(n_(dur)).astype(np.float32)


def sweep_bp(x, f_start, f_end=None, q=2.0, steps=48):
    """Time-varying band-pass (piecewise) for whooshes and risers; f follows a geometric path from f_start to f_end,
    or f_start is an array of `steps` centre frequencies (then f_end is ignored)."""
    n = len(x); out = np.zeros_like(x); seg = int(np.ceil(n / steps)); zi = None
    fs = np.geomspace(f_start, f_end, steps) if np.ndim(f_start) == 0 else np.asarray(f_start, float)
    steps = len(fs)
    for k in range(steps):
        f = float(np.clip(fs[k], 30, SR * 0.45)); bw = f / q
        sos = signal.butter(2, [max(20, f - bw / 2), min(SR * 0.48, f + bw / 2)], 'bandpass', fs=SR, output='sos')
        a, b = k * seg, min(n, (k + 1) * seg)
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[a:b], zi = signal.sosfilt(sos, x[a:b], zi=zi)
    return out


def siren_synth(dur, mode='wail', d0=90.0, speed=0.0, tc=None, seed=0):
    """Electronic siren: band-limited square-ish horn tone with a proper wail (slow rise, longer fall) or yelp, driven
    through a horn response; moving source with exact doppler (emission-time phase), 1/r level and distance
    air absorption, pan following the azimuth, ground bounce. Returns stereo (dry; add 'street' space)."""
    rng = np.random.default_rng(seed); n = n_(dur); t = np.arange(n) / SR
    tc = dur / 2 if tc is None else tc
    x = speed * (t - tc); r = np.sqrt(d0 ** 2 + x ** 2)
    te = t - r / 343.0                                   # emission time
    period = 4.6 if mode == 'wail' else 0.32
    tt = np.arange(int((dur + 2) * SR)) / SR - 1.0
    ph = (tt / period + rng.uniform()) % 1.0
    up = 0.42
    shape = np.where(ph < up, (1 - np.exp(-3.5 * ph / up)) / (1 - np.exp(-3.5)), 1 - np.clip((ph - up) / (1 - up), 0, 1) ** 0.85)
    f = 640 + (1450 - 640) * shape
    Phi = 2 * np.pi * np.cumsum(f) / SR
    P = np.interp(te, tt, Phi); fi = np.interp(te, tt, f)
    y = np.zeros(n)
    for k in range(1, 12):
        a = (1.0 / k) if k % 2 else 0.35 / k
        y += a * np.sin(k * P) * (k * fi < 9000)
    y = eq(y.astype(np.float32), ('peak', 1500, 5, 0.9), ('peak', 3000, 3, 1.4))
    y = bp(y, 350, 6000, 2)
    y = sat(y, 1.8)
    near, mid_, far = lp(y, 7000, 1), lp(y, 2800, 2), lp(y, 1100, 2)
    dn = np.clip((r - 30) / 300, 0, 1)
    y = (near * (1 - dn) ** 2 + mid_ * 2 * dn * (1 - dn) + far * dn ** 2) * (30.0 / np.maximum(r, 30.0))
    gb = np.roll(y, n_(0.004)) * 0.4                      # ground bounce
    y = y + gb
    az = np.arctan2(x, d0); p = np.sin(az) * 0.75
    a = (p + 1) * np.pi / 4
    return np.stack([y * np.cos(a) * np.sqrt(2), y * np.sin(a) * np.sqrt(2)], 1).astype(np.float32)


def _ring_cad(dur, on, off, f, phase=0.0, rng=None):
    t = np.arange(n_(dur)) / SR; per = on + off
    gate = (((t + phase) % per) < on).astype(np.float32)
    k = n_(0.006); gate = np.convolve(gate, np.ones(k) / k, 'same')
    return (sum(np.sin(2 * np.pi * fr * t) for fr in f) / len(f) * gate).astype(np.float32)


# ======================================================================================== recipes
# each returns (stereo audio, pre_s, level_offset_db, spaced) ; spaced=True means space() was already applied

def _seq(events, extra=0.5):
    """events: [(t_s, stereo)] -> one buffer."""
    end = max(n_(t) + len(y) for t, y in events) + n_(extra)
    out = np.zeros((end, 2), np.float32)
    for t, y in events:
        place(out, st(y), n_(t))
    return out


def r_knock_door(rng, sp, n=None, spacing=0.32, force=None, accel=0.0, material='wood', door=1, strength=None, soft=False,
                 **_):
    # the final mix: film.py cues every knock of a pattern on its own frame (params index / group): one knock each
    # (the default n=3 rendered three knocks per cue: 21 knocks for the 7 of rule 3)
    if n is None:
        n = 1 if ('index' in _ or 'group' in _) else 3
    # characters.Acting.knock emits strength (1.0 first knock .. 1.4 climax): 1.0 -> 0.7, 1.2 -> 0.85, 1.4 -> 1.0
    if soft and force is None:
        force = 0.3
    if force is None:
        force = 0.7 + 0.75 * (float(strength) - 1.0) if strength is not None else 0.7
    if material == 'glass':
        A = pool('knock_glass', lambda: src('knock_door', has=['glass_panel']), 'onset', gap=0.12, max_len=0.8)
    else:
        A = pool('knock_wood', lambda: src('knock_door', has=['knock_wood', 'plank', 'wood_heavy', 'officedoorknock']),
                 'onset', gap=0.12, max_len=0.9)
    K = pool('knuckle', lambda: src('knock_door', has=['wood_light', 'wood_heavy']), 'onset', gap=0.05, max_len=0.25)
    dr = np.random.default_rng(1000 + int(door))
    modes = np.array([88, 133, 181, 247, 338, 489, 702]) * (1 + 0.05 * dr.standard_normal())
    dec = np.array([0.2, 0.15, 0.12, 0.08, 0.06, 0.04, 0.025])
    amp = np.array([1.0, 0.8, 0.65, 0.45, 0.35, 0.22, 0.12])
    wb, wk, wbody = {'inside': (1.0, 0.35, 1.0), 'outside': (1.0, 0.2, 0.7)}.get(sp, (1.0, 0.8, 0.35))
    ev = []; t = 0.0; force = float(np.clip(force, 0.05, 1.0))
    for k in range(int(n)):
        v = force * (0.9 + 0.12 * (k == n - 1) + 0.05 * rng.standard_normal())
        v = float(np.clip(v, 0.05, 1.1))
        a = A.get(rng, rj=0.04) * v ** 1.2
        kn = hp(K.get(rng, rj=0.06, fo=0.03)[:n_(0.06)], 1800, 2) * 0.6 * v
        body = modal(modes * (1 + 0.01 * rng.standard_normal()), dec * (0.75 + 0.5 * v),
                     amp * v ** 1.6, 0.6, seed=int(rng.integers(1 << 30)))
        thump = lp(noise(0.03, int(rng.integers(1 << 30))) * np.exp(-np.arange(n_(0.03)) / n_(0.004)), 380, 2) * 0.6 * v
        b = np.zeros(max(len(a), len(body)), np.float32); b[:len(body)] += body * 0.5; b[:len(thump)] += thump
        layer = np.zeros((len(b), 2), np.float32); layer[:len(a)] += a * wb
        layer[:len(kn)] += kn * wk; layer += st(pnorm(b, 0.7) * wbody * v)
        ev.append((t, pan(layer, rng.uniform(-0.05, 0.05))))
        t += spacing * (1 - accel) ** k * (1 + 0.07 * rng.standard_normal())
    y = _seq(ev, 0.3)
    return y, 0.003, 16 * np.log10(force / 0.7), False      # +2.5 LU at full force: the escalation is heard


def r_doorbell_chime(rng, sp, kind='ding_dong', **kw):
    if kind != 'reception':                       # delivery film: the house's ding-dong (kind='reception': police chime)
        return r_doorbell_dingdong(rng, sp, **{k: v for k, v in kw.items() if k in ('n', 'spacing')})
    P = pool('doorbell', lambda: src('doorbell_chime'), 'phrase', gap=0.5, max_len=4.0, keep=-18)
    y = P.get(rng, rj=0.0, tilt=0.5, fo=0.25)
    # bar-chime body layer in the same pitch area, very low, for weight on small speakers
    body = st(modal([659.3, 1819, 523.3, 1444], [0.9, 0.3, 1.1, 0.35], [1, 0.25, 0, 0], 1.8, 3)) * 0.05
    y = _seq([(0, y), (0, body)], 0.1)
    return y, 0.0, 0.0, False


def _steps(rng, key, entries_fn, n=None, dur=None, rate_=1.8, approach=0.0, creak=0.3, weight=0.7):
    P = pool(key, entries_fn, 'onset', gap=0.18, max_len=0.7, keep=-20)
    C = pool('creak_short', lambda: src(category='sfx/creaks_scrapes', tags=['creak']), 'onset', gap=0.2, max_len=0.9)
    n = int(n or max(1, round((dur or 3.0) * rate_)))
    ev = []; t = 0.0
    for k in range(n):
        g = P.get(rng, rj=0.05, fo=0.04)
        prog = k / max(1, n - 1)
        gdb = (approach * (prog - 0.5) * 9) + (-1.2 if k % 2 else 0) + rng.normal(0, 0.8)
        cut = 9000 * 2 ** (approach * (prog - 0.5) * 1.2)
        g = lp(g, cut, 1) * 10 ** (gdb / 20) * (0.6 + 0.6 * weight)
        g = eq(g, ('ls', 150, (weight - 0.5) * 6, 0.7))
        ev.append((t, pan(g, (0.08 if k % 2 else -0.08))))
        if rng.uniform() < creak:
            ev.append((t + rng.uniform(0.02, 0.09), C.get(rng, rj=0.1)[:n_(0.5)] * 0.18 * 10 ** (gdb / 20)))
        t += (1.0 / rate_) * (1 + 0.05 * rng.standard_normal())
    return _seq(ev, 0.4)


def r_footsteps_porch(rng, sp, n=None, dur=None, rate=1.8, approach=0.0, creak=0.3, weight=0.7, foot=None, **_):
    y = _steps(rng, 'steps_porch', lambda: src('footsteps_porch', nothas=['civitas__footsteps']), n, dur, rate,
               approach, creak, weight)
    if foot in ('L', 'R'):
        y = pan(y, -0.08 if foot == 'L' else 0.08)
    return _door_presence(y, sp), 0.0, 0.0, False           # delivery film: the steps read through the door too


def r_footsteps_wood_inside(rng, sp, n=None, dur=None, rate=1.8, approach=0.0, creak=0.4, weight=0.6, stairs=False,
                            run=False, slippers=False, foot=None, direction=None, kind=None, **_):
    """stairs=True: stair treads (direction 'up' / 'down' / None = level); run=True: faster and heavier;
    slippers=True: soft scuffing slippers (mom); foot 'L' / 'R': one step of a walk (film.py cues every step);
    kind 'tiny' (dummy film, cast -12 dB): the little wooden figure's steps (= tiny_steps)."""
    if kind == 'tiny':
        y, pre, offs, spaced = r_tiny_steps(rng, sp, n=n or 1, dur=dur, approach=approach)
        return y, pre, offs + 4.0, spaced
    if run:
        rate, weight = rate * 1.5, max(weight, 0.85)
    if stairs:
        y = r_footsteps_stairs(rng, sp, direction=direction, n=n, dur=dur, rate=rate, weight=weight)[0]
    elif slippers:
        y = _steps(rng, 'steps_bare', lambda: src('footsteps_hall', has=['barefoot', 'creaky']), n, dur, rate, approach,
                   creak * 0.5, 0.35)
        y = lp(y, 2600, 2)
        sc = bp(noise(len(y) / SR, int(rng.integers(1 << 30))), 1500, 5000, 2)[:len(y)] * \
            np.abs(lp(mono(y), 30, 1)) * 3.0                     # the scuff follows each step
        y = y + st(sc)
    else:
        y = _steps(rng, 'steps_wood', lambda: src('footsteps_wood_inside', nothas=['barn_reverberant']), n, dur, rate,
               approach, creak, weight)
        y = eq(y, ('ls', 150, -2.5, 0.7), ('peak', 1100, 4.0, 0.8))   # final mix: some grains were all thud on a phone
        if foot in ('L', 'R'):
            # the Bunnyman's final mix: one picture step per cue (the foot plant's frame); some grains rise for 50-200 ms
            # before the plant (a scuff, a heel roll): the step's -12 dB onset lands on the cue, as the grass steps do
            return pan(y, -0.08 if foot == 'L' else 0.08), min(0.15, onset_s(y, -12)), 0.0, False
    if foot in ('L', 'R'):
        y = pan(y, -0.08 if foot == 'L' else 0.08)
    return y, 0.0, 0.0, False


def r_car_pass(rng, sp, dist=1.0, direction=1, dur=None, kind=None, **_):
    if kind == 'away':                                  # the van pulls away from the curb: starts at t
        return r_van_pull_away(rng, sp, dur=dur or 7.0)
    if kind == 'arrive':                                # a vehicle draws up and stops: starts at t, settles by t + dur
        return _arrive(rng, sp, dur or 5.0)
    E = src('car_pass'); e = E[int(rng.choice(len(E), p=_epi_w(E)))]
    y = audio(e); pk = env_peak_s(y, 0.5)
    pre = min(pk, (dur or 12) / 2); post = min(len(y) / SR - pk, (dur or 10) / 2)
    seg = y[n_(pk - pre):n_(pk + post)]
    if direction < 0:
        seg = seg[:, ::-1]
    if dist > 1:
        seg = lp(seg, 9000 / dist ** 0.7, 2)
    return fade(seg, 0.8, 1.0), pre, -6 * np.log2(max(dist, 0.25)), False


def _epi_w(E, w=3.0):
    p = np.array([w if e['source'] == 'epidemic' else 1.0 for e in E]); return p / p.sum()


def r_car_idle(rng, sp, dur=8.0, kind=None, **_):
    if kind in ('diesel', 'van'):
        return r_van_idle(rng, sp, dur=dur)
    E = src('car_idle'); e = E[int(rng.integers(len(E)))]
    y = excerpt(e, dur, rng)
    y = eq(y, ('ls', 90, 3, 0.7))
    return y, 0.0, 0.0, False


def _car_door_pools():
    E = src('car_door_close')
    if 'car_close' not in _POOLS:
        P = Pool('car_door', E, 'phrase', gap=0.35, max_len=2.5, keep=-26)
        feats = []
        for it in P.items:
            y = mono(audio(it[0])[it[1]:it[2]])
            lo = peak(lp(y, 250, 4)); feats.append((lo, peak(y)))
        close, opn = Pool.__new__(Pool), Pool.__new__(Pool)
        for q, k in ((close, 'car_close'), (opn, 'car_open')):
            q.key = k; q.items = []; q.w = []
        byfile = defaultdict(list)
        for i, it in enumerate(P.items):
            byfile[it[0]].append(i)
        for f, idx in byfile.items():
            best = max(feats[i][0] for i in idx)
            for i in idx:
                tgt = close if feats[i][0] >= best * 0.5 else opn
                tgt.items.append(P.items[i]); tgt.w.append(1.0)
        for q in (close, opn):
            if not q.items:
                q.items = list(P.items); q.w = [1.0] * len(P.items)
            q.w = np.array(q.w)
        _POOLS['car_close'], _POOLS['car_open'] = close, opn
    return _POOLS['car_open'], _POOLS['car_close']


def r_car_door_open(rng, sp, **_):
    o, _c = _car_door_pools()
    return o.get(rng, rj=0.03, fo=0.08), 0.0, 0.0, False


def r_car_door_close(rng, sp, n=1, spacing=0.45, **_):
    _o, c = _car_door_pools()
    ev = []; t = 0.0; on0 = None
    for k in range(max(1, int(n))):                     # n > 1 (dummy film): several doors, a little irregular
        y = c.get(rng, rj=0.03, fo=0.1)
        th = st(modal([62, 95, 140], [0.09, 0.06, 0.04], [1, 0.6, 0.3], 0.4, int(rng.integers(1 << 30)))) * 0.35
        on = onset_s(y, -12)
        on0 = on if on0 is None else on0
        a = 1.0 if k == 0 else rng.uniform(0.7, 0.95)
        ev += [(t, y * a), (t + on, th * a)]
        t += float(spacing) * (1 + 0.25 * rng.standard_normal())
    return _seq(ev, 0.1), on0, 0.0, False


def r_siren_far(rng, sp, dur=12.0, dist=1.0, synth=False, mode='wail', speed=0.0, **_):
    if synth or speed:
        y = siren_synth(dur, mode, 90 * dist, speed, seed=int(rng.integers(1 << 30)))
        pre = dur / 2 if speed else 0.0
        return fade(y, 1.0, 1.5), pre, -6 * np.log2(max(dist, 0.25)), False
    E = src('siren_far', nothas=['brazil']); e = E[int(rng.choice(len(E), p=_epi_w(E)))]
    y = excerpt(e, dur, rng)
    if dist > 1:
        y = lp(y, 6000 / dist ** 0.6, 2)
    y = fade(y, min(1.5, dur / 4), min(2.0, dur / 3))
    return y, 0.0, -6 * np.log2(max(dist, 0.25)), False


def _static_pool():
    return pool('static_burst', lambda: src('police_radio_squelch', has=['static_radio', 'lost_signal', 'interference']),
                'onset', gap=0.15, max_len=0.7, keep=-20)


def _click_pool():
    return pool('clicks', lambda: src('radio_click', nothas=['kenney_ui__switch']), 'onset', gap=0.05, max_len=0.2,
                keep=-18)


def _squelch_tail(rng, dur=0.16):
    x = noise(dur + 0.02, int(rng.integers(1 << 30)))
    t = np.arange(len(x)) / SR
    x = bp(x, 600, 4200, 2) * np.where(t < dur, 1.0, np.exp(-(t - dur) / 0.004)) * (0.8 + 0.2 * np.sin(2 * np.pi * 37 * t))
    return fade(x, 0.001, 0.004)


def r_police_radio_squelch(rng, sp, kind='key', **_):
    click = hp(_click_pool().get(rng, rj=0.05), 500, 2) * 0.5
    burst = _static_pool().get(rng, rj=0.04, fo=0.03)
    if kind == 'burst':
        burst = burst[:n_(rng.uniform(0.35, 0.7))]
    else:
        burst = burst[:n_(rng.uniform(0.12, 0.28))]
    tail = st(_squelch_tail(rng, rng.uniform(0.09, 0.16))) * 0.55
    if kind == 'unkey':
        ev = [(0, burst * 0.5), (0.04, tail), (0.2, click)]
    else:
        ev = [(0, click), (0.012, fade(burst, 0.003, 0.03)), (0.012 + len(burst) / SR * 0.8, tail)]
    y = _seq(ev, 0.05)
    y = st(sat(bp(mono(y), 300, 3600, 4), 2.2))
    return y, 0.0, 0.0, False


def r_radio_click(rng, sp, **_):
    c = hp(_click_pool().get(rng, rj=0.06), 300, 2)
    s = st(bp(noise(0.03, int(rng.integers(1 << 30))), 1000, 4000, 2) * np.exp(-np.arange(n_(0.03)) / n_(0.008))) * 0.12
    thock = st(modal([310, 720], [0.012, 0.007], [1, 0.4], 0.06, 2)) * 0.25
    return _seq([(0, c), (0.003, s), (0, thock)], 0.03), 0.0, 0.0, False


def r_radio_static(rng, sp, dur=3.0, amount=0.6, **_):
    E = src('radio_static'); e = E[int(rng.choice(len(E), p=_epi_w(E, 2)))]
    y = excerpt(e, dur, rng, 0.4)
    m = lp(noise(dur, int(rng.integers(1 << 30))), 7, 1); m = m / (peak(m) + 1e-9)
    y = bp(y, 250, 4800, 2) * (1 + 0.35 * amount * st(m)[:len(y)])
    return y, 0.0, 6 * np.log10(max(amount, 0.05) / 0.6), False


def r_bodycam_beep(rng, sp, n=2, **_):
    P = pool('cam_beep', lambda: src('bodycam_beep'), 'phrase', gap=0.06, max_len=0.6, keep=-14)
    ev = []
    for k in range(int(n)):
        b = P.get(rng, rj=0.005, tilt=0.3, fo=0.01)[:n_(0.2)]
        syn = st(tone([2730, 5460], 0.085, [1, 0.12], 0.003, 0.012)) * 0.35
        ev += [(k * 0.16, b * 0.8), (k * 0.16, syn)]
    return _seq(ev, 0.05), 0.0, 0.0, False


def r_phone_ring(rng, sp, dur=None, n=2, kind='ring', cycle=None, on=None, **_):
    """A phone ringing: library rings back to back (n, or as many as fit in dur), or, with cycle / on (s), bursts on
    the picture's cadence: a ring cut to `on` seconds (40 ms fade) every `cycle` seconds for dur (the Bunnyman's
    next-episode card rings 1.2 s on, 0.8 s off)."""
    if kind == 'ringback':
        d = dur or 6 * n - 3.5
        y = st(_ring_cad(d, 2.0, 4.0, [440, 480]) * 0.6)
        y = fade(y, 0.01, 0.05)
        return y, 0.0, -4.0, False
    P = pool('ring', lambda: src('phone_ring'), 'phrase', gap=0.4, max_len=4.0, keep=-15)
    ev = []; t = 0.0
    if cycle and on and dur:
        while t < float(dur) - 0.2:
            r = P.get(rng, rj=0.0, tilt=0.4, fo=0.06)
            m = min(len(r), n_(float(on)))
            ev.append((t, fade(r[:m], 0.002, 0.04))); t += float(cycle)
        return _seq(ev, 0.1), 0.0, 0.0, False
    for k in range(int(n if dur is None else max(1, round(dur / 2.4)))):
        r = P.get(rng, rj=0.0, tilt=0.4, fo=0.06)
        ev.append((t, r)); t += len(r) / SR + 0.55
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_phone_busy(rng, sp, dur=3.0, **_):
    E = src('phone_busy'); y = excerpt(E[0], dur, rng, 0.0)
    return fade(y, 0.005, 0.03), 0.0, 0.0, False


def r_phone_vibrate(rng, sp, n=2, **_):
    P = pool('vibe', lambda: src('phone_vibrate', has=['vibration', 'punchy']), 'phrase', gap=0.15, max_len=1.2, keep=-14)
    ev = []; t = 0.0
    for k in range(int(n)):
        v = P.get(rng, rj=0.01, fo=0.03); ev.append((t, v)); t += max(len(v) / SR + 0.35, 0.9)
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_phone_pickup(rng, sp, **_):
    H = pool('plastic', lambda: src('phone_pickup'), 'onset', gap=0.1, max_len=0.6)
    h = lp(H.get(rng, rj=0.08), 3500, 2) * 0.35
    c1 = hp(_click_pool().get(rng, rj=0.05), 600, 2) * 0.6
    c2 = hp(_click_pool().get(rng, rj=0.05), 600, 2) * 0.4
    line = st(bp(noise(0.35, int(rng.integers(1 << 30))), 400, 3200, 2) * np.exp(-np.arange(n_(0.35)) / n_(0.09))) * 0.05
    return _seq([(0, h), (0.12, c1), (0.165, c2), (0.17, line)], 0.05), 0.12, 0.0, False


def r_mail_slot(rng, sp, paper=False, **_):
    P = pool('mail', lambda: src('mail_slot'), 'onset', gap=0.12, max_len=1.2, keep=-22)
    a = P.get(rng, rj=0.03, fo=0.05)
    b = P.get(rng, rj=0.03, fo=0.05)
    if peak(lp(mono(a), 400, 2)) > peak(lp(mono(b), 400, 2)):
        a, b = b, a                                       # softer one opens, the snap closes
    ev = [(0, a * 0.7)]; t = len(a) / SR * 0.6 + rng.uniform(0.25, 0.5)
    if paper:
        pp = r_paper(rng, sp, dur=1.0)[0] * 0.8
        ev.append((t, pp)); t += 0.8
    ev.append((t, b))
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_paper(rng, sp, dur=1.2, kind=None, **_):
    if kind in ('slide', 'slip', 'out'):                 # dummy film: the P.S. sliding out of the slot (cast: paper, kind
        y, pre, offs, spaced = r_paper_slide(rng, sp, dur=dur)   # 'slide', -8 dB)
        return y, pre, offs + 5.0, spaced
    E = src('paper', nothas=['pencil', 'book']); e = E[int(rng.choice(len(E), p=_epi_w(E)))]
    y = audio(e); n = n_(dur)
    gs = grains(e, 'phrase', gap=0.2, max_len=8.0, keep=-18)
    s0, s1 = gs[int(rng.integers(len(gs)))]
    if s1 - s0 > n:
        o = int(rng.integers(s0, s1 - n)); seg = y[o:o + n]
    else:
        seg = y[s0:s1]
    return fade(seg, 0.02, 0.1), 0.0, 0.0, False


def r_pen_click(rng, sp, n=1, **_):
    P = pool('pen', lambda: src('pen_click', has=['click', 'clip', 'mech'], nothas=['kenney_ui__switch']), 'onset',
             gap=0.04, max_len=0.15, keep=-16)
    ev = []; t = 0.0
    for k in range(int(n)):
        a = hp(P.get(rng, rj=0.05), 700, 2)
        b = hp(P.get(rng, rj=0.05), 900, 2) * 0.55
        ev += [(t, a), (t + rng.uniform(0.07, 0.12), rate(b, 1.08))]
        t += rng.uniform(0.35, 0.5)
    return _seq(ev, 0.05), 0.0, 0.0, False


def r_key_in_lock(rng, sp, jingle=True, **_):
    J = pool('keys', lambda: src('key_in_lock', has=['keys_jingle_hand', 'keys_jingle']), 'phrase', gap=0.15,
             max_len=0.8, keep=-16)
    I = pool('key_insert', lambda: src('key_in_lock', has=['mechlock']), 'phrase', gap=0.12, max_len=2.2, keep=-16)
    k = I.get(rng, rj=0.03, fo=0.05)
    if not jingle:                                        # one key on its own (no bunch jingling before the click)
        return k, onset_s(k, -12), 0.0, False
    j = J.get(rng, rj=0.04, fo=0.08) * 0.45
    return _seq([(0, j), (0.18, k)], 0.05), 0.18 + onset_s(k, -12), 0.0, False   # the key's click lands on t


def r_lock_turn(rng, sp, **_):
    P = pool('lock', lambda: src('lock_turn', has=['deadbolt', 'mortise', 'frontdoorlock', 'metallatch', 'doorlockkey']),
             'onset', gap=0.15, max_len=1.0, keep=-14)
    y = P.get(rng, rj=0.03, fo=0.05)
    th = st(modal([182, 330, 610], [0.04, 0.025, 0.012], [1, 0.6, 0.3], 0.15, 4)) * 0.25
    on = onset_s(y, -6)
    return _seq([(0, y), (on, th)], 0.05), on, 0.0, False


def r_chain_lock(rng, sp, action='lock', kind=None, **_):
    if kind == 'rattle':                                # a hand on the chain: it swings and clinks, nothing locks
        E = src('chain_lock', has=['security_chain', 'chains'])
        e = _pick(rng, E); gs = grains(e, 'onset', gap=0.06, max_len=0.4, keep=-20)
        ev = []; t = 0.0
        for k in range(int(rng.integers(2, 4))):
            a0, a1 = gs[int(rng.integers(len(gs)))]
            g = fade(pnorm(audio(e)[a0:a1]), 0.002, 0.05) * rng.uniform(0.4, 0.9)
            ev.append((t, rate(g, 1 + rng.uniform(-0.04, 0.04)))); t += rng.uniform(0.05, 0.14)
        return _seq(ev, 0.1), 0.0, -3.0, False
    E = src('chain_lock', has=['chain_unlock' if action == 'unlock' else 'chain_lock'])
    y = fade(pnorm(audio(E[0])), 0.002, 0.05)
    y = rate(y, 1 + rng.uniform(-0.03, 0.03))
    C = pool('vsco_chain', lambda: src(category='sfx/design/vsco_misc', tag='chain'), 'onset', gap=0.1, max_len=0.6)
    lay = [(0, y)]
    if len(C):
        lay.append((rng.uniform(0.0, 0.05), C.get(rng, rj=0.05) * 0.15))
    return _seq(lay, 0.05), 0.0, 0.0, False


def r_door_creak(rng, sp, dur=None, slow=1.0, **_):
    D = pool('door_creak', lambda: src('door_creak', category='sfx/door_creak'), 'phrase', gap=0.2, max_len=4.0,
             keep=-18)
    B = pool('bass_creak', lambda: src(category='sfx/creaks_scrapes', tags=['creak', 'bow_noise', 'scrape']),
             'phrase', gap=0.2, max_len=4.0, keep=-18)
    a = D.get(rng, rj=0.04, fo=0.1)
    r = 1.0 / max(0.3, slow)
    if dur:
        r = float(np.clip(len(a) / SR / dur, 0.5, 1.6))
    a = rate(a, r)
    b = B.get(rng, rj=0.03, fo=0.15)
    b = rate(b, semis(-rng.uniform(2, 6)))
    b = b[:len(a) + n_(0.3)] if len(b) > len(a) else b
    return _seq([(0, a), (0.02, lp(b, 3500, 2) * 0.35)], 0.1), 0.0, 0.0, False


_BREATH_BOOST = dict(sob=2.0, sniff=10.0, gasp=3.0)   # dummy film: the cast emits these at -8..-12 dB (CAST.md)


def r_breath(rng, sp, kind='nervous', dur=3.0, **_):
    if kind == 'sob':
        y, pre, offs, spaced = r_mom_sob(rng, sp, dur=dur)
        return y, pre, offs + _BREATH_BOOST['sob'], spaced
    if kind in ('shaky', 'sniff'):
        y, pre, offs, spaced = r_mom_breath(rng, sp, kind=kind, dur=dur)
        return y, pre, offs + _BREATH_BOOST.get(kind, 0.0), spaced
    if kind in ('panic', 'panting'):
        E = src('breath', epi=True, has=['panic'] if kind == 'panic' else ['panting'])
        e = E[int(rng.integers(len(E)))]
        y = excerpt(e, dur, rng, 0.3)
        return fade(y, 0.15, 0.3), 0.0, 0.0, False
    if kind == 'gasp':
        P = pool('gasp', lambda: src('breath', has=['gasp', 'freaked', 'attenti'], epi=False), 'phrase', gap=0.2,
                 max_len=2.0, keep=-14)
        return P.get(rng, rj=0.03, fo=0.1), 0.0, _BREATH_BOOST['gasp'], False
    P = pool('breaths', lambda: src('breath', has=['breath'], nothas=['panic', 'panting']), 'phrase', gap=0.25,
             max_len=2.5, keep=-20)
    ev = []; t = 0.0
    held = kind == 'held'
    while t < dur:
        b = P.get(rng, rj=0.05, fo=0.12)
        ev.append((t, b * (0.6 if held else 1.0)))
        t += len(b) / SR + (rng.uniform(0.8, 1.6) if held else rng.uniform(0.15, 0.5))
    return _seq(ev, 0.1), 0.0, -3.0 if held else 0.0, False


def r_heartbeat(rng, sp, bpm=70, bpm_end=None, dur=6.0, **_):
    P = pool('heart', lambda: src('heartbeat'), 'onset', gap=0.12, max_len=0.35, keep=-16)
    bpm_end = bpm_end or bpm
    ev = []; t = 0.0
    while t < dur:
        b = bpm + (bpm_end - bpm) * (t / max(dur, 1e-3))
        per = 60.0 / b
        lub = lp(P.get(rng, rj=0.02, tilt=0.5, fo=0.04), 900, 2)
        dub = lp(P.get(rng, rj=0.02, tilt=0.5, fo=0.04), 1100, 2) * 0.55
        sub1 = st(sub_boom(62, 44, 0.22, 0.0)) * 0.6
        sub2 = st(sub_boom(75, 52, 0.16, 0.0)) * 0.3
        s2 = 0.27 * per ** 0.5
        ev += [(t, lub), (t, sub1), (t + s2, dub), (t + s2, sub2)]
        t += per
    return _seq(ev, 0.3), 0.0, 0.0, False


def r_whoosh(rng, sp, kind='soft', **_):
    P = pool('whoosh', lambda: src('whoosh'), 'phrase', gap=0.25, max_len=3.0, keep=-15)
    a = P.get(rng, rj=0.05, fo=0.15)
    if kind == 'soft':
        y = lp(a, 5500, 2)
        return y, env_peak_s(y, 0.08), -5.0, False
    b = rate(P.get(rng, rj=0.03, fo=0.15), 0.78)
    L = max(len(a), len(b)); d = L / SR
    nz = noise(d, int(rng.integers(1 << 30)))
    sw = sweep_bp(nz, np.concatenate([np.geomspace(180, 1400, 24), np.geomspace(1400, 250, 24)]), q=1.6)
    env = np.sin(np.linspace(0, np.pi, len(sw))) ** 3
    syn = st(sw * env * 0.5)
    ap = np.linspace(-0.7, 0.7, L)
    ys = _seq([(0, a), (0, lp(b, 3000, 2) * 0.7), (0, syn)], 0.1)
    ys[:L, 0] *= np.sqrt(2) * np.cos((ap + 1) * np.pi / 4); ys[:L, 1] *= np.sqrt(2) * np.sin((ap + 1) * np.pi / 4)
    return ys, env_peak_s(ys, 0.08), 0.0, False


def r_riser(rng, sp, dur=6.0, **_):
    E = src('riser')
    L = [e for e in E if e['dur'] >= dur * 0.8] or E
    e = L[int(rng.integers(len(L)))]
    y = audio(e); pk = env_peak_s(y, 0.15)
    end = min(len(y), n_(pk + 0.06))
    start = max(0, end - n_(dur))
    seg = y[start:end]
    if len(seg) < n_(dur) * 0.9:
        seg = rate(seg, len(seg) / n_(dur))
    seg = fade(seg, len(seg) / SR * 0.35, 0.04)
    d = len(seg) / SR; t = np.arange(len(seg)) / SR
    f = 32 + 26 * (t / d) ** 2
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 2.5 * 0.5
    nz = sweep_bp(noise(d, int(rng.integers(1 << 30))), 300, 5000, q=1.4) * (t / d) ** 3 * 0.25
    y = seg + st(sub + nz)[:len(seg)]
    return fade(y, 0.05, 0.03), len(y) / SR, 0.0, False


def r_braam(rng, sp, key='d', **_):
    E = src('braam')
    pref = [e for e in E if e['id'].endswith('_' + str(key).lower())] or E
    e = pref[int(rng.integers(len(pref)))] if rng.uniform() < 0.7 else E[int(rng.integers(len(E)))]
    y = fade(pnorm(audio(e)), 0.002, 0.5)
    f0 = 36.71 if str(key).lower() == 'd' else 41.2
    t = np.arange(n_(2.5)) / SR
    sub = st(np.sin(2 * np.pi * f0 * t) * np.exp(-t / 0.9) * (1 - np.exp(-t / 0.01)) * 0.5)
    y = _seq([(0, y), (0, sub)], 0.0)
    y = reverb(y, 'church', 0.28, 0.02, hpf=150)
    return y, onset_s(y, -20), 0.0, True


def mid_crack(rng, y, at=0.0, under_db=6.0, dur=0.32):
    """Add a short mid-band 'crack' (150 Hz - 2.5 kHz: a band-passed noise burst and a dry wooden knock) at `at` s into
    a hit, `under_db` under the hit's own loudest 50 ms: the body of a hit is mostly sub and vanishes on a phone (the
    review measured the regular hits 9-14 dB under the voice through a 300 Hz high-pass)."""
    y = st(np.asarray(y, np.float32)); n = int(dur * SR); i0 = int(at * SR)
    if i0 >= len(y): return y
    x = np.arange(n) / SR
    nz = bp(rng.standard_normal(n).astype(np.float32) * np.exp(-x / 0.045).astype(np.float32), 180, 2500, 2)
    kn = (np.sin(2 * np.pi * 172 * x) * np.exp(-x / 0.08) + 0.5 * np.sin(2 * np.pi * 410 * x) * np.exp(-x / 0.04)).astype(np.float32)
    c = st(nz / (np.abs(nz).max() + 1e-9) + 0.7 * kn)
    w = int(0.05 * SR)
    seg = y[i0:i0 + int(0.6 * SR)]
    pk = np.sqrt(np.convolve((seg ** 2).mean(1), np.ones(w) / w, 'valid').max()) if len(seg) > w else 1e-3
    pc = np.sqrt(np.convolve((c ** 2).mean(1), np.ones(w) / w, 'valid').max())
    c *= np.float32(pk / (pc + 1e-9) * 10 ** (-under_db / 20))
    m = min(n, len(y) - i0)
    y = y.copy(); y[i0:i0 + m] += c[:m]
    return y


def r_impact_hit(rng, sp, size=1.0, **_):
    A = pool('hits', lambda: src('impact_hit', epi=True), 'phrase', gap=0.6, max_len=8.0, keep=-12)
    B = pool('booms', lambda: src(category='score/percussion/bass_drum') + src(category='score/percussion/timpani'),
             'phrase', gap=0.5, max_len=4.0, keep=-12)
    a = A.get(rng, rj=0.02, fo=0.6)
    b = lp(B.get(rng, rj=0.03, fo=0.4), 2500, 2) * 0.45
    sb = st(sub_boom(55 * size ** -0.3, 30, 1.4 * size, 0.1, int(rng.integers(1 << 30)))) * 0.55
    on = onset_s(a, -14)
    y = _seq([(0, a), (on, b), (on, sb)], 0.0)
    y = mid_crack(rng, y, on)                     # final mix v2: a mid crack ~6 dB under the body (it reads on a phone)
    y = reverb(y, 'church', 0.22 * size, 0.015, hpf=180)
    return y, onset_s(y, -14), 6 * np.log10(max(size, 0.2)), True


def r_sub_drop(rng, sp, **_):
    E = src('sub_drop', epi=True); e = E[int(rng.integers(len(E)))]
    a = fade(pnorm(audio(e)), 0.002, 0.3)
    s = st(sub_boom(92, 27, 2.6, 0.0)) * 0.6
    on = onset_s(a, -14)
    return _seq([(0, a * 0.8), (on, s)], 0.0), on, 0.0, False


def _stinger_ok(e):
    """A stinger has to hit: at most 8 s long and at its peak within 0.3 s of its -20 dB onset (the shared library's
    score/stingers also hold a 26 s sub sting and 22 s string / organ swells peaking seconds in: the Bunnyman's final
    mix found both rule recall cards playing the 26 s sub sting, 135 ms late and inaudible on a phone)."""
    try:
        a = st(audio(e))
    except Exception:
        return False
    if len(a) > 8 * SR:
        return False
    pk = float(np.argmax(np.abs(a).max(1))) / SR
    return pk - onset_s(a, -20) <= 0.3


def r_stinger(rng, sp, kind=None, **_):
    if kind == 'eye_flash':
        return r_eye_flash(rng, sp)
    E = src('stinger', epi=True) + src(category='score/stingers')
    E = [e for e in E if _stinger_ok(e)] or E
    e = E[int(rng.choice(len(E), p=_epi_w(E, 2)))]
    a = fade(pnorm(audio(e)), 0.002, 0.4)
    S2 = pool('scrape', lambda: src(category='sfx/creaks_scrapes', tags=['scrape', 'bow_noise']), 'phrase', gap=0.2,
              max_len=2.5, keep=-15)
    sc = lp(S2.get(rng, rj=0.03, fo=0.3), 4000, 2) * 0.18
    y = _seq([(0, a), (0.01, sc)], 0.0)
    y = reverb(y, 'church', 0.2, 0.015, hpf=200)
    return y, onset_s(y, -14), 0.0, True


def r_glitch(rng, sp, dur=0.6, amount=0.7, **_):
    P = pool('glitch', lambda: src('glitch'), 'phrase', gap=0.12, max_len=2.0, keep=-18)
    g = P.get(rng, rj=0.08, fo=0.03)
    n = n_(dur); g = g[:n] if len(g) >= n else np.pad(g, ((0, n - len(g)), (0, 0)))
    out = g.copy()
    k = 0
    while k < n:                                          # stutter: repeat short slices
        L = n_(rng.uniform(0.02, 0.07))
        if rng.uniform() < amount * 0.6 and k + L < n:
            rep = int(rng.integers(2, 6)); s = g[k:k + L]
            for r in range(rep):
                a = k + r * L
                if a + L > n:
                    break
                out[a:a + L] = fade(s, 0.001, 0.002) * (0.9 ** r)
            k += rep * L
        else:
            k += L
    bits = int(8 - 3 * amount); q = 2 ** bits
    out = np.round(out * q) / q
    dec = int(2 + 8 * amount)
    out = np.repeat(out[::dec], dec, axis=0)[:n]
    out = bp(out, 150, 9000, 2)
    return fade(out, 0.002, 0.02), 0.0, 0.0, False


def r_ui_pop(rng, sp, kind=None, **_):
    if kind == 'speaker':                               # the doorbell camera's two-way speaker opening: tick + soft blip
        c = hp(_click_pool().get(rng, rj=0.03), 900, 2)[:n_(0.05)] * 0.5
        t = np.arange(n_(0.09)) / SR
        bl = st(np.sin(2 * np.pi * 1320 * t) * np.exp(-t / 0.02) * 0.25 + np.sin(2 * np.pi * 1760 * t) * np.exp(-t / 0.015)
                * 0.12 * (t > 0.045))
        return _seq([(0, c), (0.004, fade(bl, 0.002, 0.01))], 0.02), 0.0, -3.0, False
    P = pool('ui', lambda: src('ui_pop', has=['notification', 'glass_ui', 'confirm', 'kenney_ui']), 'onset', gap=0.06,
             max_len=0.4, keep=-14)
    a = lp(P.get(rng, rj=0.03), 7000, 2) * 0.8
    t = np.arange(n_(0.07)) / SR; f = 700 + 500 * (1 - np.exp(-t / 0.01))
    bl = st(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.018) * 0.35)
    return _seq([(0, a), (0, fade(bl, 0.001, 0.01))], 0.02), 0.0, 0.0, False


def r_typing(rng, sp, dur=3.0, cps=7.0, **_):
    P = pool('keys_typing', lambda: src('typing'), 'onset', gap=0.05, max_len=0.2, keep=-18)
    ev = []; t = 0.0
    while t < dur:
        burst = int(rng.integers(3, 9))
        for _k in range(burst):
            if t >= dur:
                break
            ev.append((t, P.get(rng, rj=0.04, tilt=1.0, fo=0.01) * 10 ** (rng.normal(0, 1.5) / 20)))
            t += rng.gamma(6, 1 / (cps * 6))
        t += rng.uniform(0.12, 0.45)
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_tinnitus(rng, sp, dur=4.0, freq=None, **_):
    E = src('tinnitus'); e = E[int(rng.integers(len(E)))]
    y = excerpt(e, dur, rng, 0.5) * 0.6
    f = freq or rng.uniform(3600, 4600)
    t = np.arange(n_(dur)) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * (f * 1.003) * t)) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.3 * t))
    y = y[:len(t)] + st(s.astype(np.float32) * 0.25)[:len(y)]
    return fade(y, dur * 0.3, dur * 0.35), 0.0, 0.0, False


def _buzz(dur, rng):
    t = np.arange(n_(dur)) / SR
    y = sum((0.8 / k) * np.sin(2 * np.pi * 120 * k * t + rng.uniform(0, 6)) for k in range(1, 14))
    fl = 1 + 0.25 * (lp(rng.standard_normal(len(t)).astype(np.float32), 3, 1) * 30)
    return bp(np.tanh(2 * y * fl).astype(np.float32), 100, 5000, 2)


def r_ambience_night(rng, sp, dur=30.0, dog=0.5, wind=0.5, buzz=0.5, **_):
    E = src('ambience_night', epi=True)
    base = excerpt(E[int(rng.integers(len(E)))], dur, rng, 3.0)
    F = src('ambience_night', epi=False, has=['cricket', 'night', 'owl'])
    lay = [(0, base)]
    if F:
        f2 = excerpt(F[int(rng.integers(len(F)))], dur, rng, 2.0)
        lay.append((0, f2 * (10 ** (-9 / 20)) * peak(base) / (peak(f2) + 1e-9)))
    D = src('ambience_night', has=['dog', 'bark'])
    if D and dog > 0:
        t = rng.exponential(25 / dog)
        while t < dur - 2:
            e = D[int(rng.integers(len(D)))]
            gs = grains(e, 'phrase', gap=0.4, max_len=3.0, keep=-15)
            s0, s1 = gs[int(rng.integers(len(gs)))]
            b = lp(audio(e)[s0:s1], 2500, 2)
            b = pan(fade(pnorm(b), 0.01, 0.2), rng.uniform(-0.8, 0.8)) * peak(base) * 0.7
            lay.append((t, reverb(b, 'forest', 0.5)))
            t += rng.exponential(25 / dog) + 6
    W = src('ambience_night', has=['wind', 'gust'])
    if W and wind > 0:
        w = excerpt(W[int(rng.integers(len(W)))], dur, rng, 2.0)
        lay.append((0, lp(w, 4000, 2) * peak(base) / (peak(w) + 1e-9) * 0.45 * wind))
    if buzz > 0:
        bz = pan(st(_buzz(dur, rng)), 0.3) * peak(base) * 0.045 * buzz
        lay.append((0, bz))
    y = _seq(lay, 0.0)[:n_(dur)]
    return fade(y, 1.0, 1.5), 0.0, 0.0, False


def r_room_tone(rng, sp, dur=10.0, kind=None, **_):
    if kind in ('hospital_hum', 'hospital'):                # dummy film (film.py room_tone kinds)
        y, pre, offs, spaced = r_hospital_tone(rng, sp, dur=dur)
        return y, pre, offs + 1.0, spaced
    if kind in ('gallery_hush', 'museum', 'gallery'):
        return r_museum_tone(rng, sp, dur=dur)
    if kind in ('house', 'grandpa_house'):
        return r_room_tone_house(rng, sp, dur=dur)
    E = src('room_tone', has=['roomtone']) or src('room_tone')
    y = lp(excerpt(E[int(rng.integers(len(E)))], dur, rng, 2.0), 9000, 2)
    return fade(y, 0.5, 0.8), 0.0, 0.0, False


def r_clock_tick(rng, sp, dur=6.0, bpm=60, **_):
    P = pool('clock', lambda: src('clock_tick', category='sfx/clock_tick'), 'onset', gap=0.3, max_len=0.25, keep=-14)
    a = P.get(rng, rj=0.0, tilt=0.0); b = rate(P.get(rng, rj=0.0, tilt=0.0), semis(-1.5))
    ev = []; t = 0.0; k = 0
    while t < dur:
        ev.append((t, (a if k % 2 == 0 else b) * (1 if k % 2 == 0 else 0.8)))
        t += 60.0 / bpm + rng.normal(0, 0.002); k += 1
    return _seq(ev, 0.2), 0.0, 0.0, False


def r_countdown_tick(rng, sp, n=1, spacing=1.0, rise=0.0, **_):
    T = pool('tick', lambda: src('countdown_tick', category='sfx/countdown_tick') + src('clock_tick', category='sfx/clock_tick'),
             'onset', gap=0.2, max_len=0.2, keep=-14)
    B = pool('blip', lambda: src('countdown_tick', category='sfx/ticks_blips'), 'phrase', gap=0.1, max_len=0.5, keep=-12)
    ev = []
    for k in range(int(n)):
        tk = hp(T.get(rng, rj=0.01, tilt=0.5), 400, 2)
        bl = lp(rate(B.get(rng, rj=0.0, tilt=0.0, avoid=0), semis(rise * k)), 3000, 2) * 0.25
        sb = st(sub_boom(70, 50, 0.18, 0.0)) * 0.35
        ev += [(k * spacing, tk), (k * spacing, bl), (k * spacing, sb)]
    return _seq(ev, 0.3), 0.0, 0.0, False


def r_tv_off(rng, sp, **_):
    P = pool('tvoff', lambda: src('tv_off', category='sfx/tv_off'), 'phrase', gap=0.2, max_len=2.0, keep=-15)
    a = lp(P.get(rng, rj=0.05, fo=0.2), 8000, 2)[:n_(1.2)]
    c = hp(_click_pool().get(rng, rj=0.03), 300, 2) * 0.7
    t = np.arange(n_(0.4)) / SR
    f = 60 + 840 * np.exp(-t / 0.08)
    pew = st(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12) * 0.25)
    crack = st(bp(noise(0.3, int(rng.integers(1 << 30))), 2000, 7000, 2) * np.exp(-np.arange(n_(0.3)) / n_(0.05))) * 0.3
    th = st(sub_boom(55, 40, 0.15, 0.0)) * 0.4
    return _seq([(0, c), (0.005, th), (0.01, pew), (0.0, crack), (0.02, fade(a, 0.002, 0.3) * 0.6)], 0.1), 0.0, 0.0, False


def r_crowd_whisper(rng, sp, dur=4.0, density=6.0, **_):
    W = pool('whisper', lambda: src('crowd_whisper', has=['whisper']) + src('breath', has=['shh', 'whisper']), 'phrase',
             gap=0.08, max_len=2.0, keep=-20)
    M = src('crowd_whisper', has=['murmur', 'walla', 'talk', 'crowd', 'restaurant', 'voices'])
    lay = []
    if M:
        m = excerpt(M[int(rng.integers(len(M)))], dur, rng, 1.0)
        m = rate(lp(m, 2500, 2), semis(-2))[:n_(dur)]
        lay.append((0, m * 0.25))
    t = 0.0
    while t < dur:
        g = W.get(rng, rj=0.0, fo=0.04, avoid=4)
        g = rate(g, semis(rng.uniform(-4, 3)))
        if rng.uniform() < 0.25:
            g = fade(g[::-1].copy(), 0.1, 0.01)
        g = pan(g * 10 ** (rng.uniform(-9, 0) / 20), rng.uniform(-0.9, 0.9))
        g = reverb(g, 'hall', rng.uniform(0.1, 0.6))
        lay.append((t, g))
        t += rng.exponential(1.0 / density)
    y = _seq(lay, 0.2)[:n_(dur) + n_(1.0)]
    return fade(y, 0.4, 0.8), 0.0, 0.0, False


# ======================================================================================== delivery film recipes
# The owner's Epidemic files first (the new delivery set, then the police and mirror sets: library.py lists them before
# the free library), layered and processed; synthesis only for body modes, sub thumps, air and fibre ticks.

def _pick(rng, E, w=3.0):
    if not E:
        raise KeyError('no recordings')
    return E[int(rng.choice(len(E), p=_epi_w(E, w)))]


def _fit(y, n, rng=None):
    """Crop (random offset) or loop (equal-power crossfades) a stereo grain to exactly n samples."""
    y = st(y)
    if len(y) >= n:
        o = int(rng.integers(0, len(y) - n + 1)) if rng is not None and len(y) > n else 0
        return y[o:o + n].copy()
    xf = min(n_(0.08), len(y) // 4); out = np.zeros((n + len(y), 2), np.float32); i = 0
    w = np.sin(np.linspace(0, np.pi / 2, max(xf, 2))) ** 2
    while i < n:
        c = y.copy()
        if i > 0 and xf > 1:
            c[:xf] *= np.sqrt(w)[:, None]
        if xf > 1:
            c[-xf:] *= np.sqrt(w[::-1])[:, None]
        place(out, c, i); i += len(c) - xf
    return out[:n]


def _sub_pool(key, entries, mode, sel, **seg):
    """Pool restricted to grains sel(index, n) of each recording (e.g. the 'on' ticks of a relay)."""
    if key not in _POOLS:
        P = Pool.__new__(Pool); P.key = key; P.items = []; P.w = []
        for e in entries:
            gs = grains(e, mode, **seg)
            for k, g in enumerate(gs):
                if sel(k, len(gs)):
                    P.items.append((e['id'], g[0], g[1])); P.w.append(1.0)
        P.w = np.array(P.w, float)
        _POOLS[key] = P
    return _POOLS[key]


def _tremolo(y, hz, depth, rng):
    t = np.arange(len(y)) / SR
    m = 1 - depth * (0.5 + 0.5 * np.sin(2 * np.pi * hz * t * (1 + 0.08 * np.sin(2 * np.pi * 0.7 * t)) + rng.uniform(0, 6)))
    return (st(y) * m[:, None]).astype(np.float32)


def _dingdong_pool():
    return pool('dingdong', lambda: src('doorbell_dingdong', has=['ding_dong', 'doorbell_doorbell_0']), 'phrase',
                gap=0.6, max_len=5.0, keep=-12)


def r_doorbell_dingdong(rng, sp, kind='house', n=1, spacing=None, **_):
    if kind in ('old', 'bell', 'electric'):
        P = pool('bell_old', lambda: src('doorbell_dingdong', has=['ring_old']), 'phrase', gap=0.4, max_len=4.0, keep=-10)
    else:
        P = _dingdong_pool()
    ev = []; t = 0.0
    for k in range(max(1, int(n))):
        y = P.get(rng, rj=0.0, tilt=0.5, fi=0.001, fo=0.3)
        on = onset_s(y, -18)
        body = st(modal([182, 410, 655], [0.05, 0.035, 0.02], [1, 0.5, 0.25], 0.25, int(rng.integers(1 << 30)))) * 0.12
        ev += [(t, y), (t + on, body)]                     # the chime box: a short knock under the strike
        t += spacing or (len(y) / SR * 0.55 + rng.uniform(0.2, 0.5))
    return _seq(ev, 0.2), 0.0, 0.0, False


def r_doorbell_cam_chime(rng, sp, **_):
    y = _dingdong_pool().get(rng, rj=0.0, tilt=0.0, fo=0.2)
    y = fade(rate(y, semis(5))[:n_(2.2)], 0.001, 0.5)                    # small, bright, digital
    y = eq(bp(y, 380, 7500, 2), ('peak', 2500, 3.0, 1.0), ('ls', 300, -6, 0.7))   # phone speaker
    N = pool('notif_app', lambda: src('phone_notify', has=['menu_ui_notification', 'select_notification']), 'phrase',
             gap=0.1, max_len=1.0, keep=-12)
    u = lp(N.get(rng, rj=0.0, tilt=0.0), 6000, 2) * 0.22
    return _seq([(0, u), (0.025, y)], 0.1), 0.0, 0.0, False


def r_phone_notify(rng, sp, kind='app', vibrate=True, **_):
    if kind == 'text':
        P = pool('notif_text', lambda: src('phone_notify', has=['text_message']), 'phrase', gap=0.4, max_len=1.6, keep=-6)
    else:
        P = pool('notif_app', lambda: src('phone_notify', has=['menu_ui_notification', 'select_notification']), 'phrase',
                 gap=0.1, max_len=1.0, keep=-12)
    a = eq(lp(P.get(rng, rj=0.0, tilt=0.3, fo=0.08), 8000, 2), ('ls', 400, -4, 0.7))
    ev = [(0, a)]
    if vibrate:
        V = pool('vibe_short', lambda: src('phone_vibrate', has=['punchy']), 'phrase', gap=0.15, max_len=0.6, keep=-12)
        ev.append((0.0, V.get(rng, rj=0.01, fo=0.03)[:n_(0.45)] * 0.45))
    return _seq(ev, 0.1), 0.0, 0.0, False


def _door_presence(x, sp):
    """Box sounds heard through the closed front door ('outside'): the attack comes through the gap round the door,
    so lift 750 Hz and take the low shelf down before the door filter; otherwise the door's 160 Hz boom buries the
    event and it nearly vanishes on a phone speaker (measured: 13-24 dB less loudness above 300 Hz than at the source)."""
    return eq(x, ('ls', 160, -4, 0.7), ('peak', 750, 6, 0.9)) if sp == 'outside' else x


def _carton_pool():
    return pool('carton_hit', lambda: src('box_knock', has=['cardboard']), 'onset', gap=0.1, max_len=0.6, keep=-14)


def _wood_knock_pool():
    return pool('knock_wood', lambda: src('knock_door', has=['knock_wood', 'plank', 'wood_heavy', 'officedoorknock']),
                'onset', gap=0.12, max_len=0.9)


def _parse_pattern(p):
    if p is None or p is False:
        return None
    if isinstance(p, str):
        import re
        p = [int(x) for x in re.split(r'[^0-9]+', p) if x]
    p = [int(x) for x in p if int(x) > 0]
    return p or None


def r_box_knock(rng, sp, n=1, pattern=None, gap=0.3, pause=0.72, strength=1.0, force=None, n_in_pattern=None,
                group=None, on='porch', small=False, **_):
    """on='porch' (the box standing on the porch), 'door' (the box leaning on the front door: the knock goes into the
    door slab), 'vent' (heard through Lily's bedroom vent: a tinny duct); small=True: a child's knuckles."""
    pat = _parse_pattern(pattern)
    seq = []
    if pat:
        t = 0.0
        for m in pat:
            for k in range(m):
                seq.append((t, 1.0 if k == 0 else 0.92)); t += gap
            t += pause - gap
    else:
        seq = [(k * gap, 1.0 if k == 0 else 0.92) for k in range(max(1, int(n)))]
    f = float(np.clip(force if force is not None else 0.75 * float(strength), 0.1, 1.2))
    if small:
        f = min(f, 0.5)
    C, K = _carton_pool(), _wood_knock_pool()
    big = (n_in_pattern == 1 and group == 2)               # the lone third knock lands a little heavier
    ev = []
    for t, s in seq:
        v = float(np.clip(f * s * (1.08 if big else 1.0) * (1 + 0.05 * rng.standard_normal()), 0.05, 1.3))
        # v2 (measured on small speakers): the knock must read above 300 Hz, not only as a sub thump. The first
        # version kept 12-21 dB less of its loudness above 300 Hz than the police door knock (8-9 dB), so on a phone
        # the film's signature sound nearly vanished. Panel modes moved up to a tall carton's (90-600 Hz, was 58-318),
        # knuckle and wood layers opened up, the sub thump kept but lowered.
        a = lp(C.get(rng, rj=0.05), 3400, 2) * v ** 1.2   # knuckle into cardboard from inside: top end soaked up
        ka = onset_s(a, -14)
        kn = lp(K.get(rng, rj=0.04, fo=0.03)[:n_(0.25)], 2400, 2) * 0.8 * v
        kn_t = max(0.0, ka - onset_s(kn, -14))
        modes = np.array([92, 141, 197, 262, 338, 446, 590]) * (1 + 0.02 * rng.standard_normal())
        body = modal(modes, [0.13, 0.1, 0.08, 0.06, 0.045, 0.035, 0.025], [0.8, 1.0, 0.85, 0.65, 0.5, 0.35, 0.22], 0.6,
                     int(rng.integers(1 << 30))) * v ** 1.5
        thump = st(sub_boom(66, 40, 0.4, 0.0)) * 0.25 * v * (0.3 if small else 1.0)
        tt = np.arange(n_(0.06)) / SR
        rattle = bp(noise(0.06, int(rng.integers(1 << 30))), 900, 3200, 2) * np.exp(-tt / 0.012) * 0.1 * v
        lay = [(0, a), (kn_t, kn), (ka, st(pnorm(body, 0.4))), (ka + 0.001, thump), (ka + 0.003, st(rattle))]
        if on == 'door':                                 # the box leans on the door: the slab rings with it
            dm = np.array([88, 133, 181, 247, 338, 489]) * (1 + 0.03 * rng.standard_normal())
            door = modal(dm, [0.2, 0.15, 0.12, 0.08, 0.06, 0.04], [1.0, 0.8, 0.65, 0.45, 0.35, 0.22], 0.6,
                         int(rng.integers(1 << 30)))
            lay.append((ka + 0.001, st(pnorm(door, 0.45)) * v))
        x = _door_presence(_seq(lay, 0.2), sp)
        if small:
            x = rate(x, 1.15)
        if on == 'vent':                                 # a tinny sheet-metal duct between the rooms
            m = mono(x); y2 = m.copy()
            for d, g in ((0.0031, 0.55), (0.0047, 0.4), (0.0083, 0.3)):
                k = n_(d); y2[k:] += m[:-k] * g
            x = st(eq(bp(y2, 280, 2600, 2), ('peak', 1150, 6, 3.0), ('peak', 640, 4, 3.0)))
        if not ev:
            pre0 = ka / (1.15 if small else 1.0)           # the first knuckle's transient lands on the cue time
        ev.append((t, x))
    return _seq(ev, 0.3), pre0, 12 * np.log10(f / 0.75) + (-3.0 if on == 'vent' else 0.0), False


def r_box_tap(rng, sp, n=1, spacing=0.22, **_):
    C = pool('carton_tap', lambda: src('box_tap', has=['cardboard']), 'onset', gap=0.08, max_len=0.4, keep=-16)
    ev = []
    for k in range(max(1, int(n))):
        a = fade(hp(C.get(rng, rj=0.08)[:n_(0.12)], 250, 2), 0.001, 0.04)
        nail = hp(_click_pool().get(rng, rj=0.05), 1500, 2) * 0.12
        ev += [(k * spacing, a * (1 if k == 0 else 0.85)), (k * spacing, nail)]
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_box_creak(rng, sp, dur=0.6, **_):
    C = pool('carton_creak', lambda: src('box_creak', has=['rummage', 'lid', 'cardboard_box_open']), 'onset', gap=0.08,
             max_len=1.0, keep=-20)
    a = rate(C.get(rng, rj=0.04, fo=0.08), 0.85)
    a = lp(_fit(a, n_(max(0.2, dur)), rng), 5000, 2)
    b = C.get(rng, rj=0.04, fo=0.08)[:n_(0.3)] * 0.4
    cr = rate(pool('creak_short', lambda: src(category='sfx/creaks_scrapes', tags=['creak']), 'onset', gap=0.2,
                   max_len=0.9).get(rng, rj=0.08), semis(-4))[:n_(dur)] * 0.12
    return fade(_seq([(0, a), (dur * 0.4, b), (0.03, lp(cr, 2500, 2))], 0.1), 0.02, 0.08), 0.0, 0.0, False


def r_box_drop(rng, sp, **_):
    C = _carton_pool()
    a = C.get(rng, rj=0.04)
    L = pool('carton_lid', lambda: src('box_drop', has=['lid']), 'onset', gap=0.1, max_len=0.6, keep=-14)
    b = lp(L.get(rng, rj=0.04), 3000, 2) * 0.5
    th = st(sub_boom(72, 44, 0.35, 0.0)) * 0.32           # (0.5 -> 0.32, mat 0.5 -> 0.3: the carton must read on a
    tt = np.arange(n_(0.08)) / SR                          #  phone, not only as a thud)
    mat = st(lp(noise(0.08, int(rng.integers(1 << 30))), 260, 2) * np.exp(-tt / 0.02)) * 0.3
    hit = onset_s(a, -14)                               # the carton meets the mat: lid, thump and mat land together
    y = _seq([(0, a), (max(0.0, hit - onset_s(b, -14)) + 0.004, b), (hit + 0.002, th), (hit, mat)], 0.2)
    return _door_presence(y, sp), hit, 0.0, False


def r_box_scrape(rng, sp, dur=0.8, surface='mat', **_):
    n = n_(max(0.15, float(dur)))
    D = src('box_scrape', has=['drag_on_carpet'])
    K = src('box_scrape', has=['drag_slide_smooth_concrete', 'scrape_concrete'])
    e = _pick(rng, D or K)
    s0, s1 = grains(e, 'phrase', gap=0.2, max_len=4.0, keep=-20)[0]
    seg = audio(e)[s0:s1]
    r = len(seg) / n
    seg = rate(seg, float(np.clip(r, 0.7, 1.3))) if 0.7 < r < 1.3 else seg
    a = _fit(seg, n, rng)
    lay = [(0, a * (0.7 if surface == 'concrete' else 1.0))]
    if K:
        k = audio(_pick(rng, K)); k = _fit(k[n_(0.03):], n, rng)
        lay.append((0, lp(k, 1400 if surface == 'mat' else 4000, 2) * (0.35 if surface == 'mat' else 0.9)))
    if surface == 'mat':                                 # coir bristles: dense little ticks
        tt = np.arange(n) / SR
        imp = (rng.random(n) < 70.0 / SR).astype(np.float32) * rng.uniform(0.3, 1.0, n).astype(np.float32)
        br = bp(np.convolve(imp, np.exp(-np.arange(n_(0.004)) / n_(0.0008)), 'same').astype(np.float32), 2200, 7000, 2)
        br *= np.sin(np.pi * np.clip(tt / max(tt[-1], 1e-3), 0, 1)) ** 0.5
        lay.append((0, st(br) * peak(a) * 0.5))
    return _door_presence(fade(_seq(lay, 0.0)[:n], 0.04, 0.12), sp), 0.0, 0.0, False


def r_box_open(rng, sp, keys=False, **_):
    O = pool('carton_open', lambda: src('box_open', has=['cardboard_box_open']), 'phrase', gap=0.3, max_len=2.5, keep=-18)
    R = pool('carton_remove', lambda: src('box_open', has=['remove_item']), 'phrase', gap=0.2, max_len=0.6, keep=-14)
    a = O.get(rng, rj=0.02, fo=0.2)
    ev = [(0, a), (len(a) / SR * 0.7, R.get(rng, rj=0.03) * 0.5)]
    if keys:
        J = pool('keys', lambda: src('key_in_lock', has=['keys_jingle_hand', 'keys_jingle']), 'phrase', gap=0.15,
                 max_len=0.8, keep=-16)
        k = lp(rate(J.get(rng, rj=0.03, fo=0.1), 0.82), 4500, 2) * 0.45      # rusted: duller, slower
        ev.append((len(a) / SR * 0.85, k))
    return _seq(ev, 0.2), 0.0, 0.0, False


def r_box_voice(rng, sp, dur=4.0, **_):
    """Bed under the box's lines: dark air inside the box, a few cardboard creaks, one faint breath."""
    n = n_(dur); t = np.arange(n) / SR
    env = 0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6))
    air = st(lp(hp(noise(dur, int(rng.integers(1 << 30))), 55, 2), 240, 2) * env) * 0.5
    lay = [(0, air)]
    C = pool('carton_creak', lambda: src('box_creak', has=['rummage', 'lid', 'cardboard_box_open']), 'onset', gap=0.08,
             max_len=1.0, keep=-20)
    tt = rng.uniform(0.3, 0.9)
    while tt < dur - 0.3:
        c = lp(rate(C.get(rng, rj=0.05, fo=0.06), semis(-rng.uniform(2, 6)))[:n_(0.35)], 2800, 2)
        lay.append((tt, pan(c * rng.uniform(0.25, 0.5), rng.uniform(-0.2, 0.2))))
        tt += rng.uniform(0.8, 1.7)
    B = pool('breaths', lambda: src('breath', has=['breath'], nothas=['panic', 'panting']), 'phrase', gap=0.25,
             max_len=2.5, keep=-20)
    lay.append((rng.uniform(0.1, 0.4), lp(B.get(rng, rj=0.03, fo=0.2), 1800, 2) * 0.35))
    return fade(_seq(lay, 0.0)[:n], 0.3, 0.6), 0.0, 0.0, False


def r_tape_rip(rng, sp, kind='rip', dur=None, soft=False, **_):
    if soft and kind == 'rip':
        kind = 'peel'
    R = pool('tape_rip', lambda: src('tape_rip'), 'phrase', gap=0.15, max_len=2.5, keep=-14)
    if kind in ('rip', 'peel'):
        y = R.get(rng, rj=0.03, fo=0.06)
        if kind == 'peel':
            y = lp(rate(y, 0.7), 6000, 2) * 0.8
        if dur:
            y = fade(_fit(y, n_(dur), rng), 0.005, 0.05)
        return y, 0.0, -2.0 if kind == 'peel' else 0.0, False
    L = float(dur or 0.38); n = n_(L); tt = np.arange(n) / SR       # cut: a blade through parcel tape
    env = np.sin(np.pi * np.clip(tt / L, 0, 1)) ** 0.6
    blade = sweep_bp(noise(L, int(rng.integers(1 << 30))), 2600, 5200, q=3.0) * env * 0.35
    imp = (rng.random(n) < 110.0 / SR).astype(np.float32) * rng.uniform(0.3, 1.0, n).astype(np.float32)
    fib = hp(np.convolve(imp, np.exp(-np.arange(n_(0.003)) / n_(0.0006)), 'same').astype(np.float32), 1800, 2) * env
    split = R.get(rng, rj=0.05, fo=0.03)[:n_(0.14)]
    rel = st(modal([140, 262, 410], [0.06, 0.04, 0.025], [1, 0.6, 0.3], 0.15, 6)) * 0.25
    y = _seq([(0, st(blade)), (0, st(fib) * 0.6), (L * 0.75, fade(split, 0.004, 0.04) * 0.7), (L, rel)], 0.1)
    return y, 0.0, 0.0, False


def r_hazard_ticks(rng, sp, dur=10.0, rate=1.25, duty=0.48, t_on=None, t_off=None, cue_t=0.0, **_):
    E = src('hazard_ticks')
    ON = _sub_pool('haz_on', E, 'onset', lambda k, m: k % 2 == 0, gap=0.15, max_len=0.25, keep=-12)
    OFF = _sub_pool('haz_off', E, 'onset', lambda k, m: k % 2 == 1, gap=0.15, max_len=0.25, keep=-12)
    base = float(t_on) if t_on is not None else 0.0
    P = 1.0 / max(0.2, float(rate)); c0 = float(cue_t); c1 = c0 + float(dur)
    ev = []; k = int(np.floor((c0 - base) / P)) - 1
    while base + k * P <= c1:
        a = base + k * P
        for tt, which in ((a, ON), (a + duty * P, OFF)):
            if c0 <= tt < c1 and (t_on is None or tt >= float(t_on)) and (t_off is None or tt < float(t_off)):
                g = which.get(rng, rj=0.004, tilt=0.4, fo=0.02, avoid=2) * (1.0 if which is ON else 0.7)
                ev.append((tt - c0, g))
        k += 1
    if not ev:
        return np.zeros((n_(0.1), 2), np.float32), 0.0, 0.0, False
    y = _seq(ev, 0.2)[:n_(dur) + n_(0.2)]
    return y, 0.0, 0.0, False


def r_van_door_slide(rng, sp, action='close', kind=None, **_):
    action = kind if kind in ('open', 'close') else action
    V = pool('van_slide', lambda: src('van_door_slide', has=['van_sliding']), 'phrase', gap=0.3, max_len=2.2, keep=-12)
    if action != 'open':
        y = V.get(rng, rj=0.02, fo=0.25)
        pk = env_peak_s(y, 0.02)
        th = st(sub_boom(70, 42, 0.4, 0.0)) * 0.4
        return _seq([(0, y), (pk, th)], 0.1), pk, 0.0, False
    G = pool('slide_open', lambda: src('van_door_slide', has=['doors_sliding']), 'phrase', gap=0.3, max_len=2.0, keep=-14)
    roll = lp(rate(G.get(rng, rj=0.03, fo=0.15), 0.75), 5000, 2)          # heavier rollers
    latch = hp(pool('lock', lambda: src('lock_turn', has=['deadbolt', 'mortise', 'frontdoorlock', 'metallatch',
                                                            'doorlockkey']),
                    'onset', gap=0.15, max_len=1.0, keep=-14).get(rng, rj=0.03)[:n_(0.18)], 700, 2) * 0.5
    stop = V.get(rng, rj=0.02); pk = n_(env_peak_s(stop, 0.02))
    clunk = lp(fade(stop[max(0, pk - n_(0.02)):pk + n_(0.35)], 0.003, 0.15), 1800, 2) * 0.55
    end = len(roll) / SR
    return _seq([(0, latch), (0.06, roll), (0.06 + end * 0.9, clunk),
                 (0.06 + end * 0.9, st(sub_boom(66, 40, 0.3, 0.0)) * 0.3)], 0.2), 0.0, 0.0, False


def _arrive(rng, sp, dur=5.0):
    """A vehicle draws up and stops: the approach half of a pass, braking (pitch and level fall), into the idle."""
    P = src('car_pass'); cp = audio(_pick(rng, P)); pk = env_peak_s(cp, 0.5)
    appr = cp[n_(max(0.0, pk - dur)):n_(pk)]
    m = len(appr)
    appr = _varispeed(appr, 1.0, 0.8, max(n_(0.5), m - n_(0.2))) * np.linspace(1.0, 0.6, max(n_(0.5), m - n_(0.2)))[:, None]
    idle = r_van_idle(rng, sp, dur=3.0)[0] * (peak(appr) / (peak(r_van_idle(rng, sp, dur=3.0)[0]) + 1e-9)) * 0.5
    y = _seq([(0, fade(appr, 1.0, 0.8)), (len(appr) / SR - 0.6, fade(idle, 0.6, 1.5))], 0.0)
    return y, 0.0, 0.0, False


def _diesel():
    return src('van_idle', has=['diesel']) or src('car_idle')


def r_van_idle(rng, sp, dur=8.0, **_):
    y = excerpt(_pick(rng, _diesel()), dur, rng)
    C = src('van_idle', has=['idle_close'])
    if C:
        y = y + lp(excerpt(C[0], dur, rng), 1800, 2)[:len(y)] * 0.3
    return eq(y, ('ls', 90, 3, 0.7), ('hs', 5000, -4, 0.7)), 0.0, 0.0, False


def _varispeed(y, r0, r1, n_out):
    """Read y with a playback rate gliding r0 -> r1 (linear interpolation), n_out samples."""
    rr = np.linspace(r0, r1, n_out)
    pos = np.concatenate([[0.0], np.cumsum(rr[:-1])])
    pos = np.minimum(pos, len(y) - 2)
    i = pos.astype(np.int64); f = (pos - i)[:, None].astype(np.float32)
    return (y[i] * (1 - f) + y[i + 1] * f).astype(np.float32)


def r_van_pull_away(rng, sp, dur=7.0, **_):
    dur = max(3.5, float(dur))
    e = _pick(rng, _diesel()); src_ = excerpt(e, 6.0, rng)
    idle = src_[:n_(1.6)]
    rev = _varispeed(src_[n_(1.0):], 1.0, 1.55, n_(2.0)) * np.linspace(1.0, 1.8, n_(2.0))[:, None]
    P = src('car_pass')
    cp = audio(_pick(rng, P)); pk = env_peak_s(cp, 0.5)
    away = cp[n_(max(0.0, pk - 0.3)):n_(pk + dur)]
    away = lp(away, 6000, 2) * (peak(rev) / (peak(away) + 1e-9)) * 0.9
    tire = st(bp(noise(0.5, int(rng.integers(1 << 30))), 180, 1400, 2) * np.exp(-np.arange(n_(0.5)) / n_(0.15))) * 0.08
    y = _seq([(0, fade(idle, 0.05, 0.4)), (1.2, fade(rev, 0.35, 0.6)), (1.25, tire), (2.6, fade(away, 0.5, 1.5))], 0.0)
    return fade(y[:n_(dur)], 0.05, 1.2), 0.0, 0.0, False


def r_van_step(rng, sp, **_):
    S_ = pool('steps_heavy', lambda: src('footsteps_porch', has=['heavy_up_on_porch']), 'onset', gap=0.18, max_len=0.7,
              keep=-16)
    a = S_.get(rng, rj=0.04, fo=0.05)
    hit = onset_s(a, -14)                               # the boot lands: the step's boom, clang and creak follow it
    M = src(has=['metal_impact_large_sheet_clang'])
    lay = [(0, a)]
    if M:
        m = lp(fade(audio(M[0])[n_(0.15):n_(0.75)], 0.002, 0.3), 2500, 2)
        lay.append((hit + 0.004, pnorm(m, 0.12)))
    cr = rate(pool('creak_short', lambda: src(category='sfx/creaks_scrapes', tags=['creak']), 'onset', gap=0.2,
                   max_len=0.9).get(rng, rj=0.08), semis(-5))[:n_(0.5)] * 0.18
    lay.append((hit + 0.05, lp(cr, 2200, 2)))
    lay.append((hit, st(sub_boom(60, 40, 0.3, 0.0)) * 0.3))
    return _seq(lay, 0.1), hit, 0.0, False


def r_keys_drop(rng, sp, surface='bowl', rust=False, bowl=False, jingle=False, lift=False, kind=None, **_):
    """bowl=True = surface 'bowl'; jingle=True: the keys jingle in the hand first; lift=True: keys lifted (jingle only);
    kind 'jangle' (dummy film: Mom grabs her keys) = keys_jangle."""
    if kind in ('jangle', 'grab', 'jingle', 'snatch'):
        y, pre, offs, spaced = r_keys_jangle(rng, sp)
        return y, pre, offs - 2.0, spaced
    if lift:
        J = pool('keys', lambda: src('key_in_lock', has=['keys_jingle_hand', 'keys_jingle']), 'phrase', gap=0.15,
                 max_len=0.8, keep=-16)
        y = J.get(rng, rj=0.03, fo=0.1)
        return (lp(rate(y, 0.85), 4500, 2) if rust else y), 0.0, -4.0, False
    if bowl:
        surface = 'bowl'
    has = {'carpet': ['drop_on_carpet'], 'wood': ['drop_on_wood'], 'floor': ['drop_on_wood']}.get(surface,
                                                                                               ['house_keys_drop', 'drop_on_wood'])
    K = src('keys_drop', has=has) or src('keys_drop', has=['keys'])
    e = _pick(rng, K)
    s0, s1 = grains(e, 'phrase', gap=0.15, max_len=1.2, keep=-30)[0]
    k = fade(pnorm(audio(e)[s0:s1]), 0.001, 0.06)
    k = rate(k, 1 + rng.uniform(-0.03, 0.03))
    if rust:
        k = lp(k, 4500, 2)
    lay = [(0, k)]
    pre_j = 0.0
    if jingle:
        J = pool('keys', lambda: src('key_in_lock', has=['keys_jingle_hand', 'keys_jingle']), 'phrase', gap=0.15,
                 max_len=0.8, keep=-16)
        j = J.get(rng, rj=0.03, fo=0.1)[:n_(0.45)] * 0.35
        pre_j = 0.35
        lay = [(-pre_j, fade(j, 0.01, 0.12))] + lay
    if surface in ('bowl', 'ceramic', 'dish'):
        hit = onset_s(k, -14)                           # the keys' impact (the grain can start with a little jingle)
        V = pool('vase_tap', lambda: src('keys_drop', has=['vase', 'glass_tap']), 'onset', gap=0.2, max_len=0.5, keep=-14)
        v = V.get(rng, rj=0.03, fo=0.15) * 0.45
        modes = np.array([1180, 2870, 5100, 7650]) * (1 + 0.03 * rng.standard_normal())
        ring = st(modal(modes, [0.55, 0.3, 0.16, 0.08], [1, 0.55, 0.3, 0.12], 1.2, int(rng.integers(1 << 30)))) * 0.22
        thunk = st(modal([210, 450], [0.03, 0.02], [1, 0.5], 0.15, 3)) * 0.3
        settle = lp(k[n_(hit + 0.12):], 6000, 2) * 0.3
        lay += [(max(0.0, hit - onset_s(v, -14)), v), (hit, ring), (hit, thunk), (hit + 0.14, settle)]
    lay = [(t + pre_j, x) for t, x in lay]
    return _seq(lay, 0.2), pre_j + onset_s(k, -14), 0.0, False


def r_window_slide(rng, sp, action='open', speed=1.0, **_):
    Wp = pool('window', lambda: src('window_slide', has=['windows_wood_sliding', 'greenhouse']), 'phrase', gap=0.3,
              max_len=2.0, keep=-14)
    y = Wp.get(rng, rj=0.03, fo=0.1)
    y = rate(y, float(np.clip(speed, 0.5, 2.0)))
    lay = [(0, y)]
    tt = np.arange(n_(0.05)) / SR
    rattle = st(hp(noise(0.05, int(rng.integers(1 << 30))), 2000, 2) * np.exp(-tt / 0.01)) * 0.1
    lay.append((0.02, rattle))
    if action == 'close':
        th = st(modal([290, 690, 1150], [0.04, 0.025, 0.015], [1, 0.5, 0.25], 0.15, 5)) * 0.5
        lay.append((len(y) / SR * 0.92, th))
    return _seq(lay, 0.1), 0.0, 0.0, False


def r_curtain_flutter(rng, sp, dur=4.0, wind=0.6, **_):
    C = pool('cloth_flap', lambda: src('curtain_flutter'), 'phrase', gap=0.25, max_len=2.0, keep=-18)
    n = n_(dur); ev = []; t = rng.uniform(0, 0.3)
    while t < dur:
        g = lp(C.get(rng, rj=0.06, fo=0.15), 7500, 2) * rng.uniform(0.5, 1.0)
        ev.append((t, pan(g, rng.uniform(-0.35, 0.35))))
        t += len(g) / SR * rng.uniform(0.35, 0.7) + rng.uniform(0.05, 0.4)
    y = _seq(ev, 0.0)
    y = np.pad(y, ((0, max(0, n - len(y))), (0, 0)))[:n]
    tt = np.arange(n) / SR
    gust = np.interp(tt, np.linspace(0, dur, int(dur * 0.8) + 3), rng.uniform(0.2, 1.0, int(dur * 0.8) + 3))
    air = st(lp(hp(noise(dur, int(rng.integers(1 << 30))), 120, 2), 900, 2) * gust) * peak(y) * 0.25 * wind
    return fade(y + air[:n], 0.3, 0.5), 0.0, 0.0, False


def r_cloth_rustle(rng, sp, kind='rustle', dur=None, **_):
    if kind == 'curtain':
        return r_curtain_flutter(rng, sp, dur=dur or 2.0)
    if kind == 'glove':                                  # dummy film (cast: -14 dB): the little glove lifting
        y, pre, offs, spaced = r_glove_lift(rng, sp)
        return y, pre, offs + 10.0, spaced
    if kind == 'slot':                                   # dummy film (cast: -10 dB): the hand through the slot
        y, pre, offs, spaced = r_hand_slot(rng, sp, dur=dur or 0.9)
        return y, pre, offs + 6.0, spaced
    P = pool('cloth', lambda: src('cloth_rustle') + src(category='sfx/foley/cloth'), 'phrase', gap=0.15, max_len=1.0,
             keep=-18)
    g = P.get(rng, rj=0.05, fo=0.08)
    if kind == 'grab':
        g = fade(hp(g[:n_(0.25)], 150, 2), 0.002, 0.06)
    else:
        g = fade(_fit(g, n_(float(dur) if dur else min(0.8, max(0.3, len(g) / SR))), rng), 0.02, 0.1)
    return g, 0.0, 0.0, False


def r_touch_tap(rng, sp, n=1, spacing=0.25, **_):
    T = pool('touch', lambda: src('touch_tap'), 'onset', gap=0.08, max_len=0.12, keep=-24)
    ev = []
    for k in range(max(1, int(n))):
        a = lp(hp(T.get(rng, rj=0.05, tilt=0.5, fo=0.01), 320, 2), 6000, 2)    # a fingertip on glass: no table thud
        ev.append((k * spacing * (1 + 0.08 * rng.standard_normal()), a * (1 if k == 0 else rng.uniform(0.7, 0.95))))
    return _seq(ev, 0.05), 0.0, 0.0, False


def r_stylus_scribble(rng, sp, dur=0.8, **_):
    dur = max(0.2, float(dur))
    S_ = pool('squeak', lambda: src('stylus_scribble', has=['glass_friction']), 'onset', gap=0.05, max_len=0.35, keep=-20)
    ev = [(0, r_touch_tap(rng, sp)[0] * 0.6)]; t = 0.04
    while t < dur:
        L = rng.uniform(0.06, 0.22)
        g = rate(S_.get(rng, rj=0.08, tilt=1.0, fo=0.02), semis(rng.uniform(3, 8)))[:n_(L)]
        g = lp(fade(hp(g, 1200, 2), 0.008, 0.03), 7500, 2) * rng.uniform(0.35, 1.0)
        ev.append((t, g))
        t += L + rng.uniform(0.02, 0.09)
    y = _seq(ev, 0.05)
    tt = np.arange(len(y)) / SR
    glide = bp(noise(len(y) / SR, int(rng.integers(1 << 30))), 2500, 6000, 2)[:len(y)] * 0.03 * \
        (0.5 + 0.5 * np.sin(2 * np.pi * 3.3 * tt))
    return fade(y + st(glide), 0.005, 0.05), 0.0, 0.0, False


def r_camera_shutter(rng, sp, kind='tablet', **_):
    E = src('camera_shutter', has=['camera'])
    e = E[0]
    gs = grains(e, 'phrase', gap=0.1, max_len=0.6, keep=-30)
    s0, s1 = gs[-1]                                     # the last event of the Nikon take is the shutter
    s = fade(pnorm(audio(e)[s0:s1]), 0.001, 0.03)
    s2 = rate(s, 1.12) * 0.5                            # second curtain
    lay = [(0, s), (0.07, s2)]
    if kind == 'tablet':
        lay = [(0, eq(hp(x, 250, 2), ('peak', 3000, 2.0, 1.0))) if i == 0 else (tt, x) for i, (tt, x) in enumerate(lay)]
    return _seq(lay, 0.05), 0.0, 0.0, False


def _foot_presence(y):
    """Socks / bare feet on wood are mostly thud: lift the heel-and-board click (1.2 kHz) and ease the 150 Hz boom so
    the steps still read on a phone speaker (measured: 15-17 dB of their loudness was below 300 Hz)."""
    return eq(y, ('ls', 150, -3.5, 0.7), ('peak', 1200, 5.0, 0.8))


def _barefoot_pool():
    return pool('steps_bare', lambda: src('footsteps_hall', has=['barefoot', 'creaky']), 'onset', gap=0.18,
                max_len=0.7, keep=-20)


def r_footsteps_stairs(rng, sp, direction='up', n=None, dur=None, rate=1.5, weight=0.6, **_):
    """direction 'up' (going away, duller), 'down' (coming nearer), None (level: no distance change)."""
    P = _barefoot_pool()
    C = pool('creak_short', lambda: src(category='sfx/creaks_scrapes', tags=['creak']), 'onset', gap=0.2, max_len=0.9)
    n = int(n or max(1, round((dur or 3.0) * rate)))
    ev = []; t = 0.0
    for k in range(n):
        prog = k / max(1, n - 1)
        away = prog if direction == 'up' else (1 - prog if direction == 'down' else 0.15)
        gdb = -7.0 * away + rng.normal(0, 0.8) + (-1.0 if k % 2 else 0.0)
        g = lp(P.get(rng, rj=0.05, fo=0.04), 7000 * 2 ** (-1.3 * away), 1) * 10 ** (gdb / 20) * (0.6 + 0.6 * weight)
        tread = st(modal(np.array([96, 168, 255, 340]) * (1 + 0.04 * rng.standard_normal()), [0.07, 0.05, 0.04, 0.03],
                         [1, 0.7, 0.45, 0.3], 0.25, int(rng.integers(1 << 30)))) * 0.2 * 10 ** (gdb / 20) * weight
        ev += [(t, pan(g, 0.06 if k % 2 else -0.06)), (t + 0.004, tread)]
        if rng.uniform() < 0.35:
            ev.append((t + rng.uniform(0.03, 0.1), lp(C.get(rng, rj=0.1)[:n_(0.5)], 3000, 2) * 0.2 * 10 ** (gdb / 20)))
        t += (1.0 / rate) * (1 + 0.06 * rng.standard_normal())
    return _foot_presence(_seq(ev, 0.4)), 0.0, 0.0, False


def r_footsteps_hall(rng, sp, n=None, dur=None, rate=1.7, approach=0.0, creak=0.35, weight=0.5, **_):
    y = _steps(rng, 'steps_bare', lambda: src('footsteps_hall', has=['barefoot', 'creaky']), n, dur, rate, approach,
               creak, weight)
    return _foot_presence(lp(y, 6500, 1)), 0.0, 0.0, False


def _female_breaths():
    return pool('breath_f', lambda: src('breath', has=['female']) + src('mom_breath', has=['calm']), 'phrase', gap=0.25,
                max_len=2.2, keep=-22)


def r_mom_breath(rng, sp, kind='shaky', dur=3.0, **_):
    if kind == 'gasp':
        P = pool('gasp', lambda: src('breath', has=['gasp', 'freaked', 'attenti'], epi=False), 'phrase', gap=0.2,
                 max_len=2.0, keep=-14)
        g = P.get(rng, rj=0.03, fo=0.1)
        return rate(g, semis(1.5)), 0.0, 0.0, False
    if kind == 'sniff':
        S_ = src('breath', has=['sniff'])
        if not S_:
            return r_mom_breath(rng, sp, kind='gasp')
        return fade(pnorm(audio(S_[0])), 0.005, 0.05), 0.0, -4.0, False
    P = _female_breaths(); ev = []; t = 0.0
    while t < dur:
        b = P.get(rng, rj=0.04, fo=0.15)
        b = hp(rate(b, semis(rng.uniform(0.5, 2.0))), 180, 2)
        if kind == 'shaky':
            b = _tremolo(b, rng.uniform(7, 10), 0.32, rng)
        ev.append((t, b * (0.6 if kind == 'held' else 1.0)))
        t += len(b) / SR + (rng.uniform(0.8, 1.6) if kind == 'held' else rng.uniform(0.15, 0.45))
    return _seq(ev, 0.1)[:n_(dur + 1.0)], 0.0, -3.0 if kind == 'held' else 0.0, False


def r_mom_sob(rng, sp, dur=3.0, intensity=0.7, **_):
    """Crying without a voice: stuttered inhales (3-4 catches), a shaking exhale, now and then a sniff."""
    P = _female_breaths()
    S_ = src('breath', has=['sniff'])
    ev = []; t = 0.0
    while t < dur:
        b = hp(P.get(rng, rj=0.04, fo=0.1), 180, 2)
        m = int(rng.integers(3, 5)); base = rng.uniform(0.0, max(0.0, len(b) / SR - 0.4))
        for k in range(m):                             # the catches: 70-100 ms slices of the inhale, rising
            sl = fade(b[n_(base + k * 0.08):n_(base + k * 0.08 + rng.uniform(0.07, 0.1))], 0.006, 0.03)
            ev.append((t, rate(sl, semis(1.5 + 0.4 * k)) * (0.55 + 0.15 * k) * (0.7 + 0.4 * intensity)))
            t += rng.uniform(0.11, 0.15)
        ex = _tremolo(rate(P.get(rng, rj=0.04, fo=0.2), semis(rng.uniform(0.5, 1.5))), rng.uniform(5, 6.5),
                      0.35 + 0.2 * intensity, rng)
        ev.append((t + 0.05, hp(ex, 160, 2) * 0.9))
        t += len(ex) / SR * 0.85 + rng.uniform(0.25, 0.7)
        if S_ and rng.uniform() < 0.35 and t < dur:
            ev.append((t, fade(pnorm(audio(S_[0])), 0.005, 0.05) * 0.5)); t += 0.5
    return _seq(ev, 0.1)[:n_(dur + 1.0)], 0.0, 0.0, False


def r_ambience_suburb(rng, sp, dur=30.0, dog=0.25, wind=0.4, buzz=0.3, traffic=0.4, **_):
    y, *_r = r_ambience_night(rng, sp, dur=dur, dog=dog, wind=wind, buzz=buzz)
    n = len(y); tt = np.arange(n) / SR
    m = 0.7 + 0.3 * np.interp(tt, np.linspace(0, dur, int(dur / 6) + 3), rng.uniform(0, 1, int(dur / 6) + 3))
    hum = st(lp(hp(noise(n / SR, int(rng.integers(1 << 30))), 50, 2), 320, 2)[:n] * m) * peak(y) * 0.06 * traffic
    return fade(y + hum, 1.0, 1.5), 0.0, 0.0, False


def _dawn_start(e, dur, rng):
    """Start time of a dur-second window of the birdsong take with the least rooster (strong 350-1600 Hz harmonics)."""
    gc = _gcache(); key = f"{e['id']}|dawn_score"
    if key not in gc:
        y = mono(audio(e)); hop = SR
        sc = []
        for i in range(0, len(y) - hop, hop):
            s = y[i:i + hop]; P = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2; f = np.fft.rfftfreq(len(s), 1 / SR)
            lo = P[(f > 350) & (f < 1600)].sum(); hi = P[(f > 2000) & (f < 8000)].sum()
            sc.append(float(lo / (hi + 1e-12)))
        gc[key] = sc; _gsave()
    sc = np.array(gc[key]); w = max(1, int(np.ceil(dur)))
    if len(sc) <= w:
        return 0.0
    cost = np.array([sc[i:i + w].max() for i in range(len(sc) - w)])
    good = np.flatnonzero(cost <= np.percentile(cost, 15))
    return float(good[int(rng.integers(len(good)))])


def r_ambience_dawn(rng, sp, dur=30.0, birds=0.6, **_):
    E = src('ambience_dawn')
    if not E:
        return r_ambience_suburb(rng, sp, dur=dur, dog=0.0)
    e = E[0]; y = audio(e); n = n_(dur)
    a = n_(_dawn_start(e, dur, rng))
    b = _fit(y[a:a + n] if a + n <= len(y) else y[a:], n, rng)
    b = lp(hp(b, 300, 2), 9000, 2) * birds
    base, *_r = r_ambience_night(rng, sp, dur=dur, dog=0.0, wind=0.3, buzz=0.0)
    lay = [(0, b), (0, base[:n] * (peak(b) / (peak(base) + 1e-9)) * 0.35)]
    return fade(_seq(lay, 0.0)[:n], 2.0, 2.0), 0.0, 0.0, False


def r_room_tone_house(rng, sp, dur=10.0, hum=0.3, clock=0.0, **_):
    E = src('room_tone_house', has=['wooden_cabin']) or src('room_tone')
    y = lp(excerpt(_pick(rng, E), dur, rng, 2.0), 9000, 2)
    n = len(y); tt = np.arange(n) / SR
    fr = sum(a * np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f, a in ((60, 1.0), (120, 0.5), (180, 0.25), (300, 0.12)))
    fr = fr * (0.8 + 0.2 * np.sin(2 * np.pi * 0.05 * tt)) + lp(noise(n / SR, int(rng.integers(1 << 30))), 400, 2)[:n] * 0.3
    lay = [(0, y), (0, st(fr.astype(np.float32)) * peak(y) * 0.06 * hum)]
    if clock > 0:
        c, *_r = r_clock_tick(rng, sp, dur=dur, bpm=60)
        lay.append((0, c * peak(y) * 0.5 * clock))
    return fade(_seq(lay, 0.0)[:n], 0.5, 0.8), 0.0, 0.0, False


def r_eye_flash(rng, sp, **_):
    """The driver's eyes flash white on the doorbell camera: a short dark stinger, a glassy bowed-metal glint, a sensor
    tick (dry, it lands on the flash frame)."""
    E = src('stinger', epi=True)
    a = fade(pnorm(audio(_pick(rng, E))), 0.002, 0.3)[:n_(1.4)] * 0.6
    M = src(category='score/percussion/bowed_metals')
    lay = [(0, fade(a, 0.002, 0.5))]
    if M:
        m = audio(M[int(rng.integers(len(M)))])
        lay.append((0.0, fade(hp(pnorm(m[:n_(1.2)]), 1800, 2), 0.004, 0.6) * 0.3))
    tt = np.arange(n_(0.02)) / SR
    lay.append((0.0, st(hp(noise(0.02, int(rng.integers(1 << 30))), 3000, 2) * np.exp(-tt / 0.004)) * 0.3))
    y = reverb(_seq(lay, 0.0), 'church', 0.18, 0.01, hpf=300)
    return y, onset_s(y, -14), -3.0, True


def r_hazard_tick(rng, sp, kind='on', **_):
    """One relay click of the van's flashers (film.py cues every tick from sets.hazard_ticks()): 'on' tick / 'off' tock."""
    E = src('hazard_ticks')
    if kind == 'off':
        P = _sub_pool('haz_off', E, 'onset', lambda k, m: k % 2 == 1, gap=0.15, max_len=0.25, keep=-12)
    else:
        P = _sub_pool('haz_on', E, 'onset', lambda k, m: k % 2 == 0, gap=0.15, max_len=0.25, keep=-12)
    return P.get(rng, rj=0.004, tilt=0.4, fo=0.02, avoid=2) * (1.0 if kind != 'off' else 0.7), 0.0, \
        (0.0 if kind != 'off' else -3.0), False


def r_window_latch(rng, sp, **_):
    """Checking a window: the hand tries the sash, the latch holds (a metal clack and a dull frame thud, no slide)."""
    Lk = pool('lock', lambda: src('lock_turn', has=['deadbolt', 'mortise', 'frontdoorlock', 'metallatch', 'doorlockkey']),
              'onset', gap=0.15, max_len=1.0, keep=-14)
    a = hp(Lk.get(rng, rj=0.05)[:n_(0.12)], 600, 2) * 0.7
    Wp = pool('window', lambda: src('window_slide', has=['windows_wood_sliding', 'greenhouse']), 'phrase', gap=0.3,
              max_len=2.0, keep=-14)
    w = Wp.get(rng, rj=0.04)
    pk = n_(env_peak_s(w, 0.01))
    jolt = lp(fade(w[max(0, pk - n_(0.01)):pk + n_(0.16)], 0.002, 0.08), 3500, 2) * 0.6
    th = st(modal([150, 290, 520], [0.05, 0.03, 0.02], [1, 0.6, 0.3], 0.15, int(rng.integers(1 << 30)))) * 0.45
    return _seq([(0, jolt), (0.005, th), (0.02, a), (0.21, jolt * 0.5), (0.215, th * 0.6)], 0.1), 0.0, 0.0, False


# ======================================================================================== dummy film recipes
# "If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH". The owner's dummy set first
# (W/samples/epidemic: wooden pole / blocks / box lid / woody click, spoon and mug, studio laughter, the old hifi and
# the VHS deck, the boy's and the men's laughs, the female screams, the heart monitor), then the delivery, police and
# mirror sets and the free library (kenney wood impacts, VSCO ratchet, oculus switches and HVAC); synthesis only for
# the dummy's hollow head and jaw hinge, the doll's eye, the CRT, the lamp's buzz, the sip and the flatline.

def _wood_pool():
    """Hard, dry, small wood hits: the dummy set's pole / blocks / box lid / woody click (3x weight), the kenney wood
    light and plank impacts."""
    return pool('dummy_wood', lambda: src('dummy_clack') + src(category='sfx/impacts', has=['impact_wood_light',
                                                                                         'impact_plank_medium']),
                'onset', gap=0.05, max_len=0.22, keep=-20)


def _wood_body_pool():
    """Heavier wood (the dummy's body on a chair, a table, a floor): kenney wood medium / heavy + the dummy set."""
    return pool('dummy_wood_body', lambda: src('wood_knock') + src(category='sfx/impacts', has=['impact_wood_medium',
                                                                                             'impact_wood_heavy']),
                'onset', gap=0.06, max_len=0.35, keep=-20)


def _creak_pool():
    """Short wooden creaks: bunk bed, mattress, wooden door, wood friction (mirror set)."""
    return pool('wood_creak', lambda: src('wood_creak'), 'onset', gap=0.12, max_len=1.2, keep=-22)


def _cloth_pool():
    return pool('cloth_soft', lambda: src('velvet') + src(category='sfx/foley/cloth', has=['kenney_rpg__cloth']),
                'phrase', gap=0.08, max_len=0.9, keep=-20)


def _head_modes(rng, scale=1.0, dec=1.0, dur=0.16, amp=None):
    """The hollow carved head (a 15 cm shell with the mouth slot): air cavity + shell modes, short and dry."""
    f = np.array([410.0, 760.0, 1240.0, 1890.0, 2650.0]) * scale * (1 + 0.03 * rng.standard_normal(5))
    d = np.array([0.045, 0.03, 0.02, 0.012, 0.008]) * dec
    a = np.array(amp or [1.0, 0.7, 0.5, 0.35, 0.2])
    return modal(f, d, a, dur, seed=int(rng.integers(1 << 30)), exc=0.0006)


def _click_burst(rng, dur=0.006, f=2500.0):
    tt = np.arange(n_(dur)) / SR
    return st(hp(noise(dur, int(rng.integers(1 << 30))), f, 2) * np.exp(-tt / (dur / 4)))


def _hinge(rng, f0=165.0, dec=0.035):
    """The jaw's wooden hinge / the head knocking on its stick: a low hollow thock."""
    return st(modal(np.array([f0, f0 * 1.63, f0 * 2.7]) * (1 + 0.04 * rng.standard_normal(3)), [dec, dec * 0.7, dec * 0.4],
                    [1.0, 0.6, 0.3], 0.18, int(rng.integers(1 << 30)), exc=0.0012))


def r_dummy_clack(rng, sp, kind='snap', **_):
    """The jaw snapping shut: a dry hardwood click (recorded), the hollow head ringing for 30-50 ms, a tiny sharp
    contact click, and the hinge's low thock. kind 'snap' (deliberate: "Clack."), 'slow' (after a slow close: a
    little heavier), 'speech' / 'soft' (one per syllable while he talks: lighter, shorter, no hinge, -1 dB: the cast's own gain_db -14..-8 makes them ticks under the line)."""
    light = kind in ('speech', 'soft', 'syllable', 'talk')
    g = _wood_pool().get(rng, rj=0.07, tilt=1.5, fo=0.025)[:n_(0.11 if light else 0.16)]
    g = hp(g, 380 if light else 300, 2)
    scale = rng.uniform(0.9, 1.12) * (1.1 if light else 1.0)
    lay = [(0.0, g), (0.0, st(_head_modes(rng, scale, 0.6 if light else 0.9)) * (0.28 if light else 0.42)),
           (0.0, _click_burst(rng, 0.004 if light else 0.006, 2800) * (0.2 if light else 0.32))]
    if not light:
        lay.append((0.0015, _hinge(rng, 150 if kind == 'slow' else 172) * (0.32 if kind == 'slow' else 0.2)))
    y = _seq(lay, 0.04)
    y = eq(y, ('peak', 1900, 3.0, 1.0), ('ls', 160, -2.0, 0.7))        # dry wooden bite that reads on a phone
    return y, onset_s(y, -18), (-1.0 if light else (1.0 if kind == 'slow' else 0.0)), False


def r_dummy_jaw(rng, sp, kind='drop', **_):
    """The jaw falling open and bottoming out on its hinge: a dull wooden knock (lower and rounder than the clack),
    the head's hollow, then the jaw bouncing once or twice (6 Hz, as characters.Winks.jaw_drop draws it)."""
    g = lp(_wood_body_pool().get(rng, rj=0.05, tilt=1.0, fo=0.04)[:n_(0.2)], 2600, 2)
    body = st(_head_modes(rng, rng.uniform(0.78, 0.86), 1.3)) * 0.5
    th = _hinge(rng, 128, 0.05) * 0.7
    y = _seq([(0.0, g), (0.0, body), (0.002, th)], 0.05)
    lay = [(0.0, y)]
    for k, (dt, a) in enumerate(((0.085, 0.16), (0.155, 0.06))):      # the bounce
        r = rate(_wood_pool().get(rng, rj=0.05, fo=0.02)[:n_(0.06)], 1.15)
        lay.append((dt + rng.uniform(-0.008, 0.008), lp(r, 3500, 2) * a))
    y = _seq(lay, 0.05)
    return y, onset_s(y, -18), 0.0, False


def r_eyelid_click(rng, sp, kind='shut', **_):
    """A doll's wooden eyelid: a tiny tight click (the dummy set's woody click / metal click), the glass eye's small
    ring (2.6-5.6 kHz, 8 ms) and the weighted lid's micro rattle. kind 'shut' (the wink, "Click."), 'open' (softer,
    a tone lower, -5 dB), 'wink' (= shut)."""
    P = pool('eyelid', lambda: src('eyelid_click', has=['woody', 'metal_click', 'wooden_block']), 'onset', gap=0.05,
             max_len=0.08, keep=-18)
    g = lp(hp(P.get(rng, rj=0.05, tilt=1.0, fo=0.012)[:n_(0.06)], 900, 2), 9000, 2)
    op = kind == 'open'
    if op:
        g = rate(g, semis(-2.0))
    eye = st(modal(np.array([2600.0, 3900.0, 5600.0]) * (1 + 0.03 * rng.standard_normal(3)) * (0.9 if op else 1.0),
                   [0.008, 0.006, 0.004], [1.0, 0.6, 0.35], 0.05, int(rng.integers(1 << 30)), exc=0.0003)) * 0.25
    lay = [(0.0, g), (0.0, eye), (0.0, _click_burst(rng, 0.003, 3500) * 0.2)]
    lay.append((0.022 + rng.uniform(0, 0.008), lp(g[:n_(0.02)], 5000, 2) * 0.18))        # the lid settles
    y = _seq(lay, 0.03)
    return y, onset_s(y, -18), (-5.0 if op else 0.0), False


def r_wood_creak(rng, sp, kind='tick', dur=None, **_):
    """A wooden joint. kind 'tick' (one small creak, dur 0.08-0.3: a finger, an elbow, the head ratcheting one notch),
    'grind' (the slow 180-degree head turn, dur default 3.0: a long wooden groan time-fitted to dur, pitched down, with
    the neck's ratchet ticking under it), 'creak' (a medium creak, dur default 0.7)."""
    C = _creak_pool()
    if kind == 'grind':
        d = float(dur or 3.0)
        D = pool('door_creak', lambda: src('door_creak', category='sfx/door_creak'), 'phrase', gap=0.2, max_len=4.0,
                 keep=-18)
        a = D.get(rng, rj=0.03, fo=0.1)
        a = rate(a, float(np.clip(len(a) / SR / d, 0.55, 1.6)) * semis(-3))
        a = _fit(a, n_(d), rng)
        lay = [(0.0, lp(hp(a, 160, 2), 4500, 2))]
        R = src(category='score/percussion/metals', has=['ratchet1_slow', 'ratchet1_crank'])
        if R:
            r = audio(_pick(rng, R, 1.0))
            r = _fit(rate(r, semis(-7)), n_(d), rng)                   # slower, lower: a wooden gear, not a toy
            lay.append((0.0, lp(hp(r, 250, 2), 3000, 2) * peak(a) / (peak(r) + 1e-9) * 0.35))
        M = src(category='sfx/creaks_scrapes', has=['arco_noise_moan', 'arco_noise_creak'])
        if M:
            m = _fit(rate(audio(_pick(rng, M, 1.0)), semis(-5)), n_(d), rng)
            lay.append((0.0, lp(m, 1200, 2) * peak(a) / (peak(m) + 1e-9) * 0.25))
        y = _seq(lay, 0.0)[:n_(d)]
        g = np.interp(np.arange(len(y)) / SR, [0, 0.12, d * 0.5, d - 0.25, d], [0.0, 0.8, 1.0, 0.9, 0.0])
        return fade(y * g[:, None].astype(np.float32), 0.02, 0.1), 0.0, 2.0, False
    d = float(dur or (0.7 if kind == 'creak' else 0.15))
    g = C.get(rng, rj=0.08, tilt=1.0, fo=0.03)
    g = rate(g, semis(rng.uniform(1.0, 4.0)) if kind == 'tick' else semis(rng.uniform(-2.0, 1.0)))
    g = fade(hp(g[:n_(max(0.05, d))], 250, 2), 0.004, min(0.04, d * 0.4))
    return g, 0.0, (4.0 if kind == 'tick' else 0.0), False


def r_wood_knock(rng, sp, n=1, spacing=0.18, size=1.0, **_):
    """The dummy's wooden body knocking against a chair / a table / the stairs: wood impact + a hollow body mode."""
    ev = []
    for k in range(max(1, int(n))):
        g = _wood_body_pool().get(rng, rj=0.05, fo=0.04)
        body = st(_head_modes(rng, 0.62 / max(0.5, float(size)), 1.4)) * 0.35
        y = _seq([(0, lp(g, 6000, 2)), (0.001, body)], 0.03) * (1.0 if k == 0 else rng.uniform(0.6, 0.85))
        ev.append((k * spacing * (1 + 0.1 * rng.standard_normal()), y))
    y = _seq(ev, 0.05)
    return y, onset_s(y, -18), 6 * np.log10(max(0.3, float(size))), False


def r_tiny_steps(rng, sp, n=None, dur=None, rate_=None, approach=0.0, **kw):
    """A knee-high wooden figure walking: tiny double knocks (heel, then toe 30-40 ms later) of small wooden shoes on
    floorboards, quick and light, a board creaking now and then. n or dur, rate (steps/s, default 3.0),
    approach (+1 nearer, -1 away)."""
    rt = float(kw.get('rate', rate_ or 3.0))
    n = int(n or max(1, round((dur or 2.0) * rt)))
    W_ = _wood_pool(); C = _creak_pool()
    ev = []; t = 0.0
    for k in range(n):
        prog = k / max(1, n - 1)
        gdb = approach * (prog - 0.5) * 8 + rng.normal(0, 1.0) + (-1.5 if k % 2 else 0.0)
        heel = lp(rate(W_.get(rng, rj=0.06, fo=0.02)[:n_(0.07)], semis(rng.uniform(1, 4))), 6500, 2)
        toe = lp(rate(W_.get(rng, rj=0.06, fo=0.02)[:n_(0.05)], semis(rng.uniform(3, 6))), 5000, 2) * 0.45
        board = st(modal([118 * rng.uniform(0.9, 1.1), 236, 410], [0.05, 0.03, 0.02], [1, 0.4, 0.2], 0.15,
                         int(rng.integers(1 << 30)))) * 0.25
        a = 10 ** (gdb / 20)
        ev += [(t, pan(heel * a, -0.05 if k % 2 else 0.05)), (t + 0.001, board * a), (t + rng.uniform(0.03, 0.042), toe * a)]
        if rng.uniform() < 0.18:
            ev.append((t + rng.uniform(0.02, 0.06), C.get(rng, rj=0.1)[:n_(0.3)] * 0.12 * a))
        t += (1.0 / rt) * (1 + 0.08 * rng.standard_normal())
    y = _seq(ev, 0.2)
    return y, onset_s(y, -18), 0.0, False


def r_glove_lift(rng, sp, **_):
    """A small white cotton glove lifting off the table: a cloth whisper and the finger joint's micro wood tick."""
    g = _cloth_pool().get(rng, rj=0.05, fo=0.06)
    g = fade(lp(hp(g[:n_(0.28)], 450, 2), 7000, 2), 0.01, 0.08)
    tk = r_wood_creak(rng, sp, kind='tick', dur=0.08)[0] * 0.5
    return _seq([(0.0, g), (0.04, tk)], 0.05), 0.0, 0.0, False


def r_hand_slot(rng, sp, dur=1.0, **_):
    """Your hand pushed through the slot in his back: the jacket's fabric sliding, the wooden edge of the slot rubbing
    the wrist, and the hollow inside answering when the hand reaches the head stick."""
    d = max(0.4, float(dur))
    c = _cloth_pool().get(rng, rj=0.04, fo=0.1)
    c = fade(lp(_fit(c, n_(d), rng), 4500, 2), 0.05, 0.15)
    tt = np.arange(n_(d)) / SR
    rub_env = np.interp(tt, [0, 0.15 * d, 0.6 * d, d], [0, 1, 0.7, 0]) * (0.75 + 0.25 * np.abs(np.sin(2 * np.pi * 7.3 * tt)))
    rub = st(bp(noise(d, int(rng.integers(1 << 30))), 500, 2400, 2) * rub_env) * peak(c) * 0.22
    inside = st(lp(_head_modes(rng, 0.62, 1.6, 0.3), 1600, 2)) * peak(c) * 0.9
    knock = lp(_wood_pool().get(rng, rj=0.05, fo=0.03)[:n_(0.08)], 2000, 2) * peak(c) * 0.4
    y = _seq([(0, c), (0, rub), (0.72 * d, inside), (0.72 * d, knock)], 0.2)
    return y, 0.0, 0.0, False


def r_hand_squeeze(rng, sp, **_):
    """One soft squeeze (a hand inside the dummy squeezing yours; Grandpa's three squeezes): fabric compressing and
    skin, close and quiet, with a faint low pressure thump."""
    g = _cloth_pool().get(rng, rj=0.05, fo=0.06)
    g = fade(lp(hp(g[:n_(0.22)], 180, 2), 2600, 2), 0.02, 0.08)
    tt = np.arange(n_(0.12)) / SR
    th = st(lp(np.sin(2 * np.pi * 95 * tt) * np.exp(-tt / 0.03), 300, 2).astype(np.float32)) * peak(g) * 0.4
    d = 0.16; t2 = np.arange(n_(d)) / SR                 # the skin of two hands creaking: a short rubbery squeak
    f = 420 + 380 * (t2 / d) + 40 * np.sin(2 * np.pi * 31 * t2)
    sq = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.15 * rng.standard_normal(len(t2)))
    sq = bp((sq * np.interp(t2, [0, 0.03, 0.1, d], [0, 1, 0.6, 0])).astype(np.float32), 300, 1200, 2)
    return _seq([(0.0, g), (0.03, th), (0.02, st(sq) * peak(g) * 0.35)], 0.05), 0.0, 0.0, False


def r_case_latch(rng, sp, kind='pop', **_):
    """A brass latch of the old leather case snapping open: the latch (flightcase latch / metal click), a small brass
    ring and the leather case's dull body. kind 'pop' (open) | 'close'."""
    A = pool('case_latch', lambda: src('case_latch', has=['flightcase', 'metal_click']), 'onset', gap=0.08,
             max_len=0.2, keep=-16)
    a = hp(A.get(rng, rj=0.04, tilt=1.0, fo=0.03), 400, 2)
    ring = st(modal(np.array([2150.0, 3420.0, 5200.0]) * (1 + 0.02 * rng.standard_normal(3)), [0.09, 0.05, 0.03],
                    [1.0, 0.5, 0.25], 0.25, int(rng.integers(1 << 30)), exc=0.0004)) * 0.12
    body = st(modal([175.0, 320.0, 560.0], [0.04, 0.03, 0.02], [1.0, 0.5, 0.25], 0.15, int(rng.integers(1 << 30)))) * 0.35
    y = _seq([(0, a), (0.0005, ring), (0.001, body)], 0.05)
    return y, onset_s(y, -16), (-2.0 if kind == 'close' else 0.0), False


def r_case_lid(rng, sp, action='open', **_):
    """The case lid: 'open' (the leather case's squeaky hinge and the lid swinging back onto the table), 'close'
    (the wooden lid coming down on the velvet: a soft wooden thump)."""
    if action == 'close':
        L_ = pool('box_lid', lambda: src('case_lid', has=['wooden_box', 'shoe_box']), 'phrase', gap=0.15, max_len=0.6,
                  keep=-14)
        a = lp(L_.get(rng, rj=0.04, fo=0.05), 5000, 2)
        th = st(modal([140.0, 260.0], [0.06, 0.04], [1.0, 0.4], 0.2, int(rng.integers(1 << 30)))) * 0.4
        y = _seq([(0, a), (0.002, th)], 0.05)
        return y, onset_s(y, -16), 0.0, False
    E = src('case_lid', has=['briefcase'])
    e = _pick(rng, E)
    y = fade(pnorm(audio(e)), 0.003, 0.08)
    y = rate(y, 1 + rng.uniform(-0.04, 0.02))
    flop = st(modal([120.0, 230.0], [0.07, 0.05], [1.0, 0.4], 0.25, int(rng.integers(1 << 30)))) * 0.3
    return _seq([(0, y), (len(y) / SR * 0.85, flop)], 0.1), 0.0, 0.0, False


def r_velvet(rng, sp, dur=0.8, **_):
    """Fingers pressing into and brushing the red velvet lining: soft plush friction, no highs."""
    d = max(0.2, float(dur))
    g = _fit(_cloth_pool().get(rng, rj=0.04, fo=0.1), n_(d), rng)
    g = eq(lp(hp(g, 200, 2), 3500, 2), ('peak', 900, 2.0, 0.8))
    return fade(g, min(0.08, d / 4), min(0.2, d / 3)), 0.0, 0.0, False


def r_spoon_stir(rng, sp, dur=3.0, clink=False, **_):
    """A teaspoon stirring in a ceramic mug (the dummy set's mug / teacup stirs), time-fitted to dur; clink=True ends
    on a tap on the rim."""
    d = max(0.5, float(dur))
    E = src('spoon_stir')
    e = _pick(rng, E)
    gs = grains(e, 'phrase', gap=0.3, max_len=8.0, keep=-24)
    s0, s1 = max(gs, key=lambda g: g[1] - g[0])
    y = _fit(audio(e)[s0:s1], n_(d), rng)
    y = fade(hp(y, 280, 2), 0.08, 0.15)
    lay = [(0.0, y)]
    if clink:
        c, pre, *_r = r_spoon_clink(rng, sp, n=1)
        lay.append((max(0.0, d - 0.05 - pre), c * 0.8))
    return _seq(lay, 0.1), 0.0, 0.0, False


def _clink_pool():
    return pool('spoon_clink', lambda: src('spoon_clink', has=['single_glass_clink', 'ramekins', 'spoon_stir_clink']),
                'onset', gap=0.08, max_len=0.5, keep=-14)


def r_spoon_clink(rng, sp, n=3, spacing=0.62, times=None, **_):
    """'Clink. Clink. Clink.': the spoon tapped on the mug's rim, deliberately, one per word. A recorded clink, the
    mug's ceramic ring and the spoon's thin metal ring. n, spacing (s) or times=[offsets in s] (to sit on the words);
    the first transient lands on the cue time."""
    T = [float(x) for x in times] if times else [k * float(spacing) for k in range(max(1, int(n)))]
    C = _clink_pool()
    ev = []
    for k, t in enumerate(T):
        g = hp(C.get(rng, rj=0.03, tilt=1.0, fo=0.05), 700, 2)
        g = g[n_(max(0.0, onset_s(g, -14) - 0.002)):]
        mug = st(modal(np.array([1980.0, 3110.0, 4700.0]) * (1 + 0.01 * rng.standard_normal(3)), [0.28, 0.16, 0.08],
                       [1.0, 0.5, 0.25], 0.6, int(rng.integers(1 << 30)), exc=0.0003)) * 0.16
        spn = st(modal([5230.0, 7900.0], [0.06, 0.04], [1.0, 0.4], 0.15, int(rng.integers(1 << 30)), exc=0.0002)) * 0.06
        a = 1.0 if k == 0 else rng.uniform(0.85, 1.0)
        ev += [(t, g * a), (t, mug * a), (t, spn * a)]
    y = _seq(ev, 0.3)
    return y, onset_s(y, -16), 0.0, False


def r_mug_set(rng, sp, kind='down', **_):
    """The mug: kind 'down' (set down on the wooden table: a ceramic thunk, the table, coffee sloshing), 'pickup'
    (lifted: a short scrape and a faint clink of the spoon)."""
    if kind in ('pickup', 'lift', 'up'):
        tt = np.arange(n_(0.15)) / SR
        scr = st(bp(noise(0.15, int(rng.integers(1 << 30))), 700, 3500, 2) * np.interp(tt, [0, 0.03, 0.15], [0, 1, 0]))
        c = _clink_pool().get(rng, rj=0.03, fo=0.05) * 0.25
        return _seq([(0, scr * 0.5), (0.08, hp(c, 1500, 2))], 0.2), 0.0, -4.0, False
    P = pool('mug_place', lambda: src('mug_set', has=['placing', 'ramekins']), 'onset', gap=0.1, max_len=0.4, keep=-14)
    g = lp(P.get(rng, rj=0.04, fo=0.06), 6000, 2)
    tbl = st(modal([180.0, 410.0, 760.0], [0.045, 0.03, 0.02], [1.0, 0.5, 0.3], 0.2, int(rng.integers(1 << 30)))) * 0.5
    tt = np.arange(n_(0.3)) / SR
    slosh = st(bp(noise(0.3, int(rng.integers(1 << 30))), 280, 1100, 2) *
               (np.exp(-tt / 0.08) * (0.6 + 0.4 * np.sin(2 * np.pi * 8 * tt)))) * 0.12
    y = _seq([(0, g), (0.001, tbl), (0.02, slosh)], 0.1)
    return y, onset_s(y, -16), 0.0, False


def r_sip(rng, sp, **_):
    """A sip of hot coffee: a careful slurp (air drawn over the liquid), a swallow, a small breath out."""
    d = 0.42; tt = np.arange(n_(d)) / SR
    cen = 900 + 800 * (tt / d)
    turb = 0.7 + 0.3 * lp(noise(d, int(rng.integers(1 << 30))), 25, 1)[:len(tt)] * 6
    sl = sweep_bp(noise(d, int(rng.integers(1 << 30))), cen[::max(1, len(cen) // 32)][:32], q=3.0) * turb * \
        np.interp(tt, [0, 0.05, 0.3, d], [0, 1, 0.8, 0])
    t2 = np.arange(n_(0.09)) / SR
    gulp = np.sin(2 * np.pi * np.cumsum(190 - 600 * t2) / SR) * np.exp(-t2 / 0.025)
    lay = [(0.0, st(sl.astype(np.float32)) * 0.6), (0.55, st(lp(gulp.astype(np.float32), 900, 2)) * 0.5)]
    B = src('sip', has=['calm'])
    if B:
        gs = grains(B[0], 'phrase', gap=0.25, max_len=2.5, keep=-20)
        s0, s1 = gs[int(rng.integers(len(gs)))]
        b = fade(lp(hp(audio(B[0])[s0:min(s1, s0 + n_(0.5))], 200, 2), 2500, 2), 0.05, 0.15)
        lay.append((0.75, pnorm(b) * 0.25))
    return _seq(lay, 0.1), 0.0, 0.0, False


def r_dummy_thud(rng, sp, kind='rug', **_):
    """Mister Winks falling face down: the body on the rug (a cloth-padded thump), the wooden torso, the head knocking
    a beat later, the little limbs clattering, a low floor thump. kind 'rug' | 'floor' (bare boards: harder)."""
    rug = kind != 'floor'
    lay = []
    if rug:
        P = pool('cloth_impact', lambda: src('dummy_thud', has=['cloth_impact']), 'onset', gap=0.15, max_len=0.5,
                 keep=-14)
        lay.append((0.0, lp(P.get(rng, rj=0.04, fo=0.1), 2500, 2)))
    b = _wood_body_pool().get(rng, rj=0.04, fo=0.06)
    lay.append((0.004, lp(b, 1800 if rug else 5000, 2) * (0.8 if rug else 1.0)))
    hd = _seq([(0, lp(_wood_pool().get(rng, rj=0.04, fo=0.03), 3200 if rug else 7000, 2)),
               (0, st(_head_modes(rng, 0.85, 1.2)) * 0.5)], 0.02)
    lay.append((0.028 + rng.uniform(0, 0.01), hd * 0.75))
    for dt, a in ((0.065, 0.35), (0.11, 0.22), (0.17, 0.12)):        # arms and legs settle
        r = _wood_pool().get(rng, rj=0.06, fo=0.02)[:n_(0.05)]
        lay.append((dt + rng.uniform(-0.01, 0.01), lp(rate(r, semis(rng.uniform(1, 4))), 4000 if rug else 8000, 2) * a))
    lay.append((0.0, st(sub_boom(72, 46, 0.35, 0.0)) * 0.35))
    y = _seq(lay, 0.1)
    return y, onset_s(y, -16), 0.0, False


def r_tv_on(rng, sp, **_):
    """The old console TV turning on by itself: the power switch's clunk (the old hifi), the degauss 'thoom' (a 60 Hz
    coil burst with its beat), the screen charging (static crackle 2-7 kHz, falling away over 1.5 s), the flyback
    whine and the set's fan / transformer hum settling in."""
    E = src('tv_on', has=['hifi'])
    e = E[0] if E else None
    lay = []
    hum_len = 3.0
    if e is not None:
        y = audio(e)
        on = n_(0.1)
        lay.append((0.0, eq(fade(y[on:on + n_(0.55)], 0.002, 0.1), ('peak', 1200, 4.0, 0.9))))
        whir = y[n_(0.7):n_(0.7 + hum_len)]
        g = np.interp(np.arange(len(whir)) / SR, [0, 0.4, hum_len], [0, 1, 0.0])[:, None]
        lay.append((0.25, lp(whir, 3000, 2) * g.astype(np.float32) * 0.6))
    tt = np.arange(n_(1.1)) / SR
    dg = (np.sin(2 * np.pi * 60 * tt) + 0.6 * np.sin(2 * np.pi * 120 * tt + 0.5) + 0.25 * np.sin(2 * np.pi * 61.5 * tt)) * \
        np.exp(-tt / 0.32) * (1 - np.exp(-tt / 0.01)) * (1 + 0.3 * np.sin(2 * np.pi * 7 * tt))
    lay.append((0.06, st(lp(hp(dg.astype(np.float32), 45, 2), 450, 2)) * 0.32))
    t3 = np.arange(n_(1.6)) / SR
    imp = (rng.uniform(size=len(t3)) < 0.0035 * np.exp(-t3 / 0.5)).astype(np.float32)
    crk = bp(np.convolve(imp * rng.standard_normal(len(t3)).astype(np.float32), np.exp(-np.arange(n_(0.004)) / n_(0.0008)),
                         'same').astype(np.float32), 2000, 7000, 2)
    lay.append((0.08, st(crk) * 0.9))
    wh = np.sin(2 * np.pi * 15734.0 * t3) * np.interp(t3, [0, 0.3, 1.6], [0, 1, 0.8]) * 0.012
    lay.append((0.1, st(wh.astype(np.float32))))
    y = _seq(lay, 0.1)
    return y, onset_s(y, -18), 0.0, False


def r_vcr(rng, sp, action='play', dur=None, **_):
    """Grandpa's old VCR: 'play' / 'insert' (the cassette mechanism threading the tape: the dummy set's Into VHS),
    'rewind' (the rewinding motor, dur), 'stop' (the mechanism unthreading: the last clunks)."""
    if action == 'rewind':
        E = src('vcr', has=['rewind'])
        e = _pick(rng, E)
        y = excerpt(e, float(dur or 4.0), rng, 0.5)
        return fade(hp(y, 120, 2), 0.05, 0.3), 0.0, -3.0, False
    E = src('vcr', has=['into_vhs'])
    y = pnorm(audio(E[0])) if E else noise(1.0) * 0.01
    if action == 'stop':
        y = y[n_(1.7):]
    if dur:
        y = y[:n_(float(dur))]
    return fade(hp(y, 120, 2), 0.005, 0.1), 0.0, 0.0, False


def r_tape_hiss(rng, sp, dur=10.0, kind=None, **_):
    """BED: an old VHS tape running (heard from the TV): hiss with flutter, the 30 Hz head-switch buzz, mains hum;
    kind 'vhs_hiss_crowd' (film.py tv_bed) adds the studio audience's murmur between the laughs, far under."""
    if kind in ('vhs_hiss_crowd', 'crowd'):
        y, *_r = r_tape_hiss(rng, sp, dur=dur)
        M = src(category='sfx/crowd_whisper', has=['civitas__crowd']) or src('studio_laugh')
        if M:
            m = lp(hp(excerpt(_pick(rng, M, 1.0), float(dur), rng, 1.5), 200, 2), 2500, 2)
            y = y + m[:len(y)] * (peak(y) / (peak(m) + 1e-9)) * 0.8
        return y, 0.0, 0.0, False
    d = float(dur); n = n_(d); tt = np.arange(n) / SR
    h = bp(noise(d, int(rng.integers(1 << 30))), 1500, 9000, 2)
    h = h * (1 + 0.12 * np.sin(2 * np.pi * 6.3 * tt) + 0.06 * np.sin(2 * np.pi * 0.7 * tt))
    pulse = ((tt * 29.97) % 1.0 < 0.012).astype(np.float32)
    buzz = lp(hp(pulse, 60, 2), 2200, 2) * 0.35
    hum = (np.sin(2 * np.pi * 60 * tt) + 0.5 * np.sin(2 * np.pi * 180 * tt)) * 0.05
    y = st((h + buzz + hum).astype(np.float32))
    return fade(y, 0.3, 0.5), 0.0, 0.0, False


def _laugh_files():
    return {k: src('studio_laugh', has=[k]) for k in ('audience_large_studio', 'medium_02', 'medium_03',
                                                       'large_audience_short')}


def r_studio_laugh(rng, sp, size='medium', dur=None, align='start', swell=None, roar=None, **_):
    """The 1974 studio audience. size 'short' (a 2-4 s burst), 'medium' (one 6-7 s laugh), 'huge' (three takes layered
    and widened into one roaring wave, 7-12 s: "a huge, roaring wave of laughter fills the dark house"); dur cuts and
    fades it; swell (s) fades it in over that time (a wave rising); align 'peak' puts the loudest moment of the wave
    on the cue time (pre = time to the crest), 'start' (default) starts it there."""
    if roar is not None:                                  # film.py studio_laughter: roar=True a big wave, else a burst
        size = 'huge' if roar else ('short' if dur and float(dur) < 3.2 else 'medium')
    F = _laugh_files()
    pick = lambda k: F[k][0] if F.get(k) else _pick(rng, src('studio_laugh'))
    if size == 'short':
        e = pick('large_audience_short') if rng.uniform() < 0.5 else pick('audience_large_studio')
        y = fade(pnorm(audio(e)[:n_(3.2)]), 0.01, 1.0)
    elif size in ('huge', 'big', 'roar', 'wave'):
        a = pnorm(audio(pick('audience_large_studio')))
        b = pnorm(audio(pick('medium_02')))
        c = pnorm(audio(pick('medium_03')))
        lay = [(0.0, a), (0.35, pan(rate(b, 1.03), -0.45) * 0.75), (0.7, pan(rate(c, 0.97), 0.45) * 0.7),
               (2.6, pan(rate(a, 0.95), 0.25) * 0.45)]
        y = _seq(lay, 0.0)
        y = width(y, 1.3)
    else:
        e = pick('audience_large_studio') if rng.uniform() < 0.6 else pick('medium_03')
        y = fade(pnorm(audio(e)), 0.01, 0.8)
    if dur:
        y = fade(y[:n_(float(dur))], 0.01, min(1.5, float(dur) * 0.35))
    if swell:
        sw = float(swell)
        g = np.clip(np.arange(len(y)) / SR / max(0.05, sw), 0, 1) ** 1.5
        y = y * g[:, None].astype(np.float32)
    y = fade(hp(y, 90, 2), 0.01, 0.3)
    pre = env_peak_s(y, 0.5) if align == 'peak' else 0.0
    return y, pre, (1.5 if size in ('huge', 'big', 'roar', 'wave') else (-2.0 if size == 'short' else 0.0)), False


def r_applause(rng, sp, dur=4.0, **_):
    """The studio audience applauding (the tails of the laughter-and-applause takes), dur."""
    E = src('applause')
    e = _pick(rng, E)
    y = audio(e); n = len(y)
    seg = y[n // 3:] if n > n_(3) else y
    y = _fit(seg, n_(float(dur)), rng)
    return fade(hp(y, 120, 2), 0.3, 0.8), 0.0, 0.0, False


def _lamp_buzz(d, rng):
    tt = np.arange(n_(d)) / SR
    y = sum((0.9 / k) * np.sin(2 * np.pi * 120 * k * tt + rng.uniform(0, 6)) for k in range(1, 18))
    y = np.tanh(2.2 * y) * (1 + 0.15 * lp(rng.standard_normal(len(tt)).astype(np.float32), 8, 1) * 20)
    return bp(y.astype(np.float32), 110, 4500, 2)


def r_lamp_flicker(rng, sp, dur=1.2, times=None, buzz=0.6, kind=None, **_):
    """The lamp flickering: on/off edges (times=[offsets s], else 4-6 irregular flicks over dur), each edge a
    filament tick and a 'zzt' arc, the lamp's 120 Hz buzz while it is on, the static of the socket under it.
    kind 'buzz' / 'on' (film.py bulb_buzz): no flicker, the bulb's steady buzz for dur (default 4), fading in."""
    if kind in ('buzz', 'on', 'steady', 'hum'):
        d = max(0.5, float(dur if dur not in (None, 1.2) else 4.0))
        bz = st(_lamp_buzz(d, rng)) * np.interp(np.arange(n_(d)) / SR, [0, 0.25, d - 0.4, d], [0, 1, 1, 0])[:, None]
        return bz.astype(np.float32), 0.0, -2.0, False
    d = max(0.3, float(dur))
    if times:
        edges = sorted(float(x) for x in times)
    else:
        edges = []; t = 0.0
        while t < d - 0.12:
            t += rng.uniform(0.04, 0.22); edges.append(t)
    n = n_(d + 0.3); tt = np.arange(n) / SR
    state = np.ones(n, np.float32)
    on = True
    for i, e in enumerate(edges):
        on = not on
        state[n_(e):] = 1.0 if on else 0.0
    k = n_(0.004); state = np.convolve(state, np.ones(k) / k, 'same').astype(np.float32)
    bz = _lamp_buzz(d + 0.3, rng) * state * 0.25 * buzz
    lay = [(0.0, st(bz))]
    for e in edges:
        lay.append((e, _click_burst(rng, 0.004, 3000) * 0.5))
        z = bp(noise(0.035, int(rng.integers(1 << 30))), 1800, 5000, 2) * np.exp(-np.arange(n_(0.035)) / n_(0.008))
        lay.append((e, st(z.astype(np.float32)) * 0.35))
    S_ = src('lamp_flicker', has=['buzz_noise'])
    if S_:
        s = excerpt(_pick(rng, S_, 1.0), d + 0.3, rng, 0.2)
        lay.append((0.0, bp(s, 150, 4000, 2) * state[:len(s), None] * peak(bz) / (peak(s) + 1e-9) * 0.3))
    return fade(_seq(lay, 0.0), 0.003, 0.05), 0.0, 0.0, False


def r_lamp_out(rng, sp, kind='out', **_):
    """'out' / 'pop' / 'buzz_off': the lamp dies (the filament's tink and pop, its buzz cut dead, a soft low whump of
    the dark); 'on' / 'buzz_on': it comes back (the switch, the buzz returning); 'switch': a wall switch alone;
    'pull_chain': a lamp's pull chain (a little chain rattle and the click)."""
    if kind in ('switch', 'pull_chain', 'chain'):
        S_ = pool('switch', lambda: src(category='sfx/clicks', has=['mechswtch', 'kenney_ui__switch']), 'onset',
                  gap=0.05, max_len=0.2, keep=-14)
        c = S_.get(rng, rj=0.03, fo=0.03)
        lay = [(0.0, c)]
        if kind != 'switch':
            C = pool('vsco_chain', lambda: src(category='sfx/design/vsco_misc', tag='chain'), 'onset', gap=0.1, max_len=0.6)
            if len(C):
                lay = [(0.0, lp(C.get(rng, rj=0.05), 6000, 2) * 0.25), (0.06, c)]
        y = _seq(lay, 0.05)
        return y, onset_s(y, -8), -2.0, False
    if kind in ('on', 'buzz_on', 'switch_on', 'back'):
        S_ = pool('switch', lambda: src(category='sfx/clicks', has=['mechswtch', 'kenney_ui__switch']), 'onset',
                  gap=0.05, max_len=0.2, keep=-14)
        c = S_.get(rng, rj=0.03, fo=0.03)
        bz = st(_lamp_buzz(0.8, rng)) * np.linspace(0, 1, n_(0.8))[:, None].astype(np.float32) ** 2 * 0.06
        return _seq([(0.0, c), (0.02, bz)], 0.05), 0.0, -2.0, False
    tink = st(modal([4200.0, 6100.0, 8300.0], [0.05, 0.03, 0.02], [1.0, 0.5, 0.25], 0.15, int(rng.integers(1 << 30)),
                    exc=0.0002)) * 0.1
    pop = _click_burst(rng, 0.004, 1500) * 0.5
    bz = st(_lamp_buzz(0.25, rng)) * 0.08
    bz *= np.linspace(0, 1, len(bz))[:, None].astype(np.float32) ** 2       # swells in: the pop is the transient
    bz[-n_(0.01):] *= np.linspace(1, 0, n_(0.01))[:, None].astype(np.float32)
    wh = st(sub_boom(62, 34, 0.7, 0.0)) * 0.3
    y = _seq([(0.0, bz), (0.25, pop), (0.25, tink), (0.252, wh)], 0.2)
    return y, 0.25, 0.0, False


def r_flashlight_click(rng, sp, kind='on', **_):
    """The usher's little flashlight: the switch (the mirror set's flashlight / Maglite switch takes) and the small
    plastic body. kind 'on' | 'off' (a tone lower, softer)."""
    P = pool('torch', lambda: src('flashlight_click'), 'onset', gap=0.08, max_len=0.25, keep=-16)
    g = hp(P.get(rng, rj=0.03, tilt=1.0, fo=0.03), 300, 2)
    # the Bunnyman's final mix: some grains carry ~45 ms of switch noise before the click; under the memory / through-
    # the-door processing it rose within 12 dB of the click and the sound read 45 ms early: the grain starts 3 ms
    # before its -20 dB onset
    g = fade(g[max(0, n_(onset_s(g, -20) - 0.003)):], 0.002, 0.0)
    if kind == 'off':
        g = rate(g, semis(-1.5)) * 0.8
    body = st(modal([980.0, 2300.0], [0.012, 0.008], [1.0, 0.5], 0.05, int(rng.integers(1 << 30)), exc=0.0003)) * 0.3
    snap = _click_burst(rng, 0.005, 1500) * 0.45
    y = _seq([(0, g), (0.0005, body), (onset_s(g, -12), snap)], 0.03)
    return y, onset_s(y, -12), (-2.0 if kind == 'off' else 0.0), False     # the switch's first click on the cue


def r_flashlight_hum(rng, sp, dur=6.0, **_):
    """BED: the flashlight's faint electric hum (the beam on the wall): a soft 100 Hz hum with a thin shimmer around
    2.2 kHz, wobbling slowly as the beam sweeps."""
    d = float(dur); tt = np.arange(n_(d)) / SR
    w = 1 + 0.25 * np.sin(2 * np.pi * 0.23 * tt + rng.uniform(0, 6))
    y = (np.sin(2 * np.pi * 100 * tt) + 0.4 * np.sin(2 * np.pi * 200 * tt) +
         0.06 * np.sin(2 * np.pi * 2210 * tt * (1 + 0.002 * np.sin(2 * np.pi * 0.4 * tt)))) * w
    return fade(st(y.astype(np.float32)), 0.8, 0.8), 0.0, 0.0, False


def _beep_pool():
    return pool('monitor_beep', lambda: src('heart_monitor'), 'phrase', gap=0.25, max_len=0.6, keep=-12)


def r_heart_monitor(rng, sp, dur=None, bpm=62.0, bpm_end=None, flatline_at=None, kind=None, **_):
    """The hospital heart monitor: the recorded beep (488 Hz) at bpm (ramping to bpm_end) for dur (default 8);
    flatline_at (s): from there one continuous tone. kind 'beep': ONE beep (film.py cues every beat, +8 dB: the cast
    level -12 / -9 is relative to the run's integrated level); kind 'flatline': the tone for dur (+8 dB)."""
    if kind == 'beep':
        g = hp(_beep_pool().get(rng, rj=0.0, tilt=0.0, fo=0.04, avoid=0), 250, 2)
        return g, 0.0, 8.0, False
    if kind in ('flatline', 'flat'):
        y, pre, offs, spaced = r_monitor_flatline(rng, sp, dur=float(dur or 3.0), beeps=0)
        return y, pre, offs + 8.0, spaced
    d = float(dur or 8.0); P = _beep_pool()
    bpm_end = float(bpm_end or bpm)
    ev = []; t = rng.uniform(0.05, 0.4)
    fl = float(flatline_at) if flatline_at is not None else None
    while t < d - 0.1 and (fl is None or t < fl - 0.2):
        b = bpm + (bpm_end - bpm) * (t / max(d, 1e-3))
        g = P.get(rng, rj=0.0, tilt=0.0, fo=0.04, avoid=0)
        ev.append((t, hp(g, 250, 2)))
        t += 60.0 / b * (1 + 0.01 * rng.standard_normal())
    if fl is not None and fl < d:
        f, *_r = r_monitor_flatline(rng, sp, dur=d - fl, beeps=0)
        ev.append((fl, f))
    if not ev:
        ev = [(0.0, np.zeros((n_(0.1), 2), np.float32))]
    y = _seq(ev, 0.1)[:n_(d)]
    return y, 0.0, 0.0, False


def r_monitor_flatline(rng, sp, dur=4.0, beeps=2, bpm=38.0, **_):
    """The flatline: `beeps` last, slowing beeps, then the monitor's tone held (the recorded beep's steady part
    looped, so it is the same voice), dur seconds of tone."""
    P = _beep_pool()
    g = P.get(rng, rj=0.0, tilt=0.0, fo=0.02, avoid=0)
    a = n_(0.05); b = n_(0.19)
    core = g[a:b] if len(g) > b else g
    ev = []; t = 0.0
    for k in range(int(beeps)):
        ev.append((t, hp(P.get(rng, rj=0.0, tilt=0.0, fo=0.04, avoid=0), 250, 2)))
        t += 60.0 / bpm * (1 + 0.25 * k)
    tone = _fit(core, n_(max(0.3, float(dur))), rng)
    tone = fade(hp(tone, 250, 2), 0.003, 0.3)
    ev.append((t, tone))
    return _seq(ev, 0.1), 0.0, 0.0, False


def r_mom_scream(rng, sp, kind='mid', breath=True, **_):
    """Mom's scream (the dummy set's female screams: 'mid', 'short', 'falling'), a sharp inhale before it."""
    E = src('mom_scream', has=[{'mid': 'scream_mid', 'short': 'scream_short', 'falling': 'falling'}.get(kind, 'scream_mid')]) \
        or src('mom_scream')
    y = fade(pnorm(audio(_pick(rng, E))), 0.004, 0.12)
    lay = [(0.0, y)]
    pre = 0.0
    if breath:
        g, *_r = r_mom_breath(rng, sp, kind='gasp')
        g = g[:n_(0.35)]
        pre = 0.3
        lay = [(0.0, fade(g, 0.02, 0.08) * 0.35)] + [(pre, y)]
    return _seq(lay, 0.2), pre, 0.0, False


def _boy_pool():
    return pool('boy_laugh', lambda: src('owen_giggle'), 'phrase', gap=0.12, max_len=1.5, keep=-22)


def r_snort(rng, sp, **_):
    """Owen's stifled snort-laugh: the laugh caught in the nose. A boy's laugh grain cut to a 0.2 s burst and pushed
    through the nose (nasal band, no mouth), a sharp nasal air burst, a shaking suppressed giggle after it."""
    P = _boy_pool()
    g = P.get(rng, rj=0.03, fo=0.05)[:n_(0.22)]
    g = eq(bp(g, 350, 4500, 2), ('peak', 1100, 5.0, 1.4), ('peak', 2600, -4.0, 1.0))
    d = 0.12; tt = np.arange(n_(d)) / SR
    nz = bp(noise(d, int(rng.integers(1 << 30))), 700, 3200, 2) * np.interp(tt, [0, 0.01, 0.04, d], [0, 1, 0.5, 0])
    after = P.get(rng, rj=0.03, fo=0.1)[:n_(0.45)]
    after = _tremolo(lp(after, 2500, 2), 9.0, 0.6, rng) * 0.3
    y = _seq([(0.0, st(nz.astype(np.float32)) * peak(g) * 0.9), (0.0, g * 0.7), (0.2, after)], 0.1)
    return y, 0.0, 0.0, False


def r_owen_giggle(rng, sp, dur=1.5, **_):
    """Owen (9) giggling: a phrase of the boy's laugh take, fitted to dur."""
    P = _boy_pool()
    g = P.get(rng, rj=0.02, fo=0.15)
    return fade(_fit(g, n_(float(dur)), rng) if len(g) < n_(float(dur)) else g[:n_(float(dur))], 0.01, 0.2), 0.0, 0.0, False


def r_owen_cry(rng, sp, kind='cry', dur=3.0, **_):
    """Owen: kind 'shriek' (a child's shriek: the short female scream up 3 semitones, smaller and thinner), 'cry' /
    'whimper' (a frightened boy crying: the stuttered sobbing breaths up 5 semitones and the boy's laugh slowed into
    shaking sobs underneath), dur."""
    if kind == 'shriek':
        E = src('mom_scream', has=['scream_short']) or src('mom_scream')
        y = rate(pnorm(audio(_pick(rng, E))), semis(3.0))
        return fade(lp(hp(y, 300, 2), 7500, 2), 0.004, 0.1), 0.0, 0.0, False
    d = float(dur)
    s, *_r = r_mom_sob(rng, sp, dur=d, intensity=0.8 if kind == 'cry' else 0.5)
    s = rate(s, semis(5.0))
    P = _boy_pool(); ev = []; t = 0.1
    while t < d - 0.3:
        g = _tremolo(rate(P.get(rng, rj=0.03, fo=0.1)[:n_(0.5)], 0.82), rng.uniform(5, 7), 0.55, rng)
        ev.append((t, lp(g, 3000, 2) * 0.35))
        t += rng.uniform(0.8, 1.4)
    y = _seq([(0.0, s)] + ev, 0.1)[:n_(d + 0.5)]
    return fade(y, 0.05, 0.3), 0.0, (-3.0 if kind == 'whimper' else 0.0), False


def r_winks_laugh(rng, sp, kind='giggle', dur=None, **_):
    """Mister Winks laughing. 'giggle': a man's laugh pushed up 6 semitones (a small body), boxed in the hollow head,
    with a light jaw clack on every syllable; 'dark': the insane laugh slowed 4 semitones into a long hall (use once,
    for a stinger layer)."""
    if kind == 'dark':
        E = src('winks_laugh', has=['insane'])
        y = excerpt(_pick(rng, E), float(dur or 3.0), rng, 0.3)
        y = lp(rate(y, semis(-4)), 3200, 2)
        y = reverb(y, 'hall', 0.5, 0.02)
        return fade(y, 0.2, 0.8), 0.0, -2.0, False
    P = pool('man_laugh', lambda: src('winks_laugh', nothas=['insane']), 'phrase', gap=0.2, max_len=2.5, keep=-18)
    g = P.get(rng, rj=0.02, fo=0.15)
    if dur:
        g = g[:n_(float(dur))]
    g = rate(g, semis(6.0))
    g = eq(lp(hp(g, 250, 2), 5500, 2), ('peak', 520, 4.0, 1.3), ('peak', 1250, 2.0, 1.5))
    on = []
    m = np.abs(mono(g)); hop = n_(0.01)
    env = np.array([m[i:i + hop].max() for i in range(0, len(m) - hop, hop)])
    thr = env.max() * 0.35
    for i in range(1, len(env)):
        if env[i] > thr and env[i - 1] <= thr:
            on.append(i * 0.01)
    lay = [(0.0, g)]
    for t in on[:12]:
        c, pre, *_r = r_dummy_clack(rng, sp, kind='speech')
        lay.append((max(0.0, t - pre + 0.04), c * 0.35 * peak(g) / (peak(c) + 1e-9)))
    return fade(_seq(lay, 0.1), 0.01, 0.15), 0.0, 0.0, False


def r_goodnight_hit(rng, sp, swell=0.9, **_):
    """'Goodnight, Owen.' landing in near silence: a short reversed air swell into one deep, soft sub thump (D, 37 Hz
    falling), the washed braam far under it, a long dark tail. Not loud: felt. pre = the swell, so the thump lands
    on the cue time."""
    sw = max(0.2, float(swell))
    nz = sweep_bp(noise(sw, int(rng.integers(1 << 30))), 300, 2200, q=1.2)
    tt = np.arange(len(nz)) / SR
    rev = st((nz * (tt / sw) ** 3).astype(np.float32)) * 0.12
    th = st(sub_boom(55, 30, 3.2, 0.05, int(rng.integers(1 << 30)))) * 0.8
    t2 = np.arange(n_(2.5)) / SR                         # a felt low D-A fifth (73 / 110 Hz, saturated): the hit has a
    fifth = np.tanh(2.5 * (np.sin(2 * np.pi * 73.42 * t2) + 0.7 * np.sin(2 * np.pi * 110.0 * t2))) * \
        np.exp(-t2 / 0.7) * (1 - np.exp(-t2 / 0.01))       # body a small speaker still plays
    lay = [(0.0, rev), (sw, th), (sw, st(lp(fifth.astype(np.float32), 1200, 2)) * 0.7)]
    E = src('goodnight_hit', has=['braam_washed', 'bass_drop_deep'])
    if E:
        b = fade(pnorm(audio(_pick(rng, E, 1.0))), 0.01, 1.2)
        lay.append((sw, lp(b, 1500, 2) * 0.5))
    y = _seq(lay, 0.0)
    y = reverb(y, 'church', 0.22, 0.02, hpf=120)
    return y, sw, 0.0, True


def r_old_clock(rng, sp, dur=10.0, bpm=60.0, **_):
    """BED: Grandpa's old clock: a deep tick-tock (the mirror set's wall clock pitched down 4 semitones, its wooden
    case's body), the tock a semitone lower and softer, a little of the hall's room."""
    P = pool('clock_old', lambda: src('old_clock', has=['wall_clock']) or src('old_clock'), 'onset', gap=0.3,
             max_len=0.25, keep=-14)
    ev = []; t = 0.0; k = 0
    while t < float(dur):
        g = rate(P.get(rng, rj=0.0, tilt=0.0, fo=0.04, avoid=0), semis(-4.0 - (1.0 if k % 2 else 0.0)))
        case = st(modal([210.0, 520.0, 980.0], [0.05, 0.03, 0.015], [1.0, 0.5, 0.25], 0.15, 7 + k % 2)) * 0.3
        ev += [(t, hp(g, 200, 2) * (1.0 if k % 2 == 0 else 0.7)), (t, case * (1.0 if k % 2 == 0 else 0.7))]
        t += 60.0 / float(bpm) + rng.normal(0, 0.002); k += 1
    y = _seq(ev, 0.3)[:n_(float(dur))]
    return reverb(y, 'hallway', 0.3), 0.0, 0.0, False


def r_hospital_tone(rng, sp, dur=20.0, **_):
    """BED: the hospital room: ventilation (oculus HVAC loop), the fluorescent tube's 120 Hz buzz, the room's air."""
    E = src(category='sfx/room_tone', has=['machhvac_hvac_loop']) or src('hospital_tone')
    y = lp(excerpt(_pick(rng, E, 1.0), float(dur), rng, 2.0), 2500, 2)
    bz = st(_lamp_buzz(float(dur), rng)) * peak(y) * 0.05
    return fade(y + bz[:len(y)], 1.0, 1.5), 0.0, 0.0, False


def r_museum_tone(rng, sp, dur=20.0, **_):
    """BED: the museum gallery at night: a big still room (room tone through the hall), the faint hum of the display
    case lights."""
    E = src('museum_tone') or src('room_tone')
    y = lp(excerpt(_pick(rng, E, 1.0), float(dur), rng, 2.0), 6000, 2)
    y = reverb(y, 'hall', 0.5)[:len(y)]
    hm = st(_lamp_buzz(float(dur), rng)) * peak(y) * 0.02
    return fade(y + hm[:len(y)], 1.5, 2.0), 0.0, 0.0, False


def r_house_creaks(rng, sp, dur=20.0, density=0.12, **_):
    """BED: the old house settling at night: sparse, distant timber creaks (pitched down, dull), each somewhere else
    in the dark (random pan), down the hall."""
    D = pool('door_creak', lambda: src('door_creak', category='sfx/door_creak'), 'phrase', gap=0.2, max_len=4.0, keep=-18)
    C = _creak_pool()
    d = float(dur); ev = []
    t = rng.uniform(0.3, max(0.4, min(d - 1.0, 0.6 / max(density, 1e-3))))   # the first creak always inside the bed
    while t < d - 0.5:
        g = (D if rng.uniform() < 0.5 else C).get(rng, rj=0.05, fo=0.2)
        L_ = rng.uniform(0.3, 1.0)
        g = fade(lp(rate(g[:n_(L_ * 1.4)], semis(-rng.uniform(3, 8))), 2200, 2), 0.05, 0.2)
        ev.append((t, pan(g * 10 ** (-rng.uniform(0, 8) / 20), rng.uniform(-0.8, 0.8))))
        t += rng.exponential(1.0 / max(density, 1e-3)) + 1.0
    if not ev:
        ev = [(0.0, np.zeros((n_(0.1), 2), np.float32))]
    y = _seq(ev, 0.5)[:n_(d)]
    y = np.pad(y, ((0, max(0, n_(d) - len(y))), (0, 0)))
    return reverb(y, 'hallway', 0.6)[:n_(d) + n_(1.0)], 0.0, 0.0, False


def r_tape_glitch(rng, sp, kind='stop', dur=0.8, **_):
    """The VHS tape: 'stop' (the tape drags to a halt: the hiss and the hum dive in pitch, the mechanism clunks),
    'tracking' (a tracking-error burst: noise tearing at 30 Hz, the head buzz), 'warble' (the picture's sound
    wobbling for dur)."""
    d = max(0.2, float(dur)); n = n_(d); tt = np.arange(n) / SR
    if kind == 'tracking':
        tear = bp(noise(d, int(rng.integers(1 << 30))), 900, 6000, 2) * ((np.sin(2 * np.pi * 29.97 * tt) > 0.2) * 1.0)
        bz = np.sign(np.sin(2 * np.pi * 59.94 * tt)) * 0.15
        y = st(lp((tear + bz).astype(np.float32), 7000, 2) * np.interp(tt, [0, 0.03, d - 0.05, d], [0, 1, 1, 0]))
        return y, 0.0, 0.0, False
    if kind == 'warble':
        h, *_r = r_tape_hiss(rng, sp, dur=d)
        r = 1 + 0.08 * np.sin(2 * np.pi * 3.0 * tt)
        return h * r[:len(h), None].astype(np.float32), 0.0, -4.0, False
    f = 120.0 * np.exp(-tt / (d * 0.35))
    hum = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * 0.6))
    hs = sweep_bp(noise(d, int(rng.integers(1 << 30))), 4000, 300, q=1.0) * np.exp(-tt / (d * 0.5))
    lay = [(0.0, st((hum * 0.5 + hs * 0.6).astype(np.float32)))]
    E = src('vcr', has=['into_vhs'])
    if E:
        y = audio(E[0]); gs = grains(E[0], 'onset', gap=0.08, max_len=0.3, keep=-20)
        s0, s1 = gs[-1]
        lay.append((d * 0.7, fade(pnorm(y[s0:s1]), 0.002, 0.05) * 0.6))
    return _seq(lay, 0.1), 0.0, 0.0, False


def r_keys_jangle(rng, sp, **_):
    """Keys snatched up (Mom grabs her keys): a quick jingle in the hand."""
    J = pool('keys', lambda: src('key_in_lock', has=['keys_jingle_hand', 'keys_jingle']), 'phrase', gap=0.15,
             max_len=0.8, keep=-16)
    y = J.get(rng, rj=0.04, fo=0.1)[:n_(0.55)]
    return fade(lp(y, 8000, 2), 0.003, 0.12), 0.0, 0.0, False


def r_paper_slide(rng, sp, dur=0.8, **_):
    """Folded paper sliding out of fabric (the P.S. out of the slot in his back): a paper rustle, smooth friction,
    a soft flop as it falls free."""
    d = max(0.3, float(dur))
    E = src('paper', nothas=['pencil', 'book'])
    e = _pick(rng, E)
    gs = grains(e, 'phrase', gap=0.2, max_len=8.0, keep=-18)
    s0, s1 = gs[int(rng.integers(len(gs)))]
    g = _fit(audio(e)[s0:s1], n_(d), rng)
    g = fade(hp(g, 500, 2), 0.04, 0.1)
    tt = np.arange(n_(d)) / SR
    fr = st(bp(noise(d, int(rng.integers(1 << 30))), 1800, 6000, 2) * np.interp(tt, [0, 0.2 * d, 0.8 * d, d], [0, 1, 1, 0])) \
        * peak(g) * 0.25
    flop = st(lp(noise(0.06, int(rng.integers(1 << 30))) * np.exp(-np.arange(n_(0.06)) / n_(0.012)), 900, 2)) * peak(g) * 0.5
    return _seq([(0.0, g * 0.8), (0.0, fr), (d * 0.92, flop)], 0.1), 0.0, 0.0, False


def _bell(f0, dur, rng, bright=1.0):
    """A struck bell / chime rod: inharmonic partials (hum, prime, tierce, quint, nominal...), long decays."""
    ratios = [0.5, 1.0, 1.183, 1.506, 2.0, 2.514, 2.662, 3.011, 4.166]
    amps = [0.5, 1.0, 0.6, 0.35, 0.7, 0.25 * bright, 0.2 * bright, 0.15 * bright, 0.08 * bright]
    decs = [3.5, 2.6, 2.0, 1.6, 1.4, 0.9, 0.8, 0.6, 0.4]
    y = modal(np.array(ratios) * f0 * (1 + 0.002 * rng.standard_normal(len(ratios))), np.array(decs) * dur / 3.0, amps,
              dur, int(rng.integers(1 << 30)), exc=0.0015)
    return y


def r_clock_chime(rng, sp, kind='hour', n=1, spacing=1.6, **_):
    """Grandpa's old clock chiming (film.py: 'quarter' at 1:15, 'hour' x3 at 3 AM): 'hour' = one deep bong on a chime
    rod (D3, a 3.5 s ring, the case's wooden knock under the strike); 'quarter' = the four-note Westminster phrase
    (E4 C4 D4 G3), lighter. n / spacing for repeated hour strikes in one cue."""
    lay = []
    if kind == 'quarter':
        notes = [329.6, 261.6, 293.7, 196.0]
        for k, f in enumerate(notes):
            b = _bell(f, 2.2, rng, 0.8) * (1.0 if k else 1.1)
            lay.append((k * 0.62, st(b)))
    else:
        for k in range(max(1, int(n))):
            b = _bell(146.8, 4.0, rng, 1.4)
            knock = modal([210.0, 520.0], [0.05, 0.03], [1.0, 0.5], 0.15, int(rng.integers(1 << 30))) * 0.35
            lay += [(k * float(spacing), st(b)), (k * float(spacing), st(knock))]
    y = _seq(lay, 0.2)
    y = eq(lp(y, 6000, 2), ('ls', 200, -4.0, 0.7), ('peak', 600, 3.0, 1.0))
    return y, onset_s(y, -16), 0.0, False


_VO = {}


def r_tv_voice(rng, sp, src_t0=None, src_t1=None, cut=False, **_):
    """The tape's own voice: a stretch of the narration recording (src_t0..src_t1, film seconds of W/align/vo_en.wav)
    replayed through the old TV (film.py: the dummy's joke on the 1974 tape, under the narration). cut=True: it stops
    dead (the tape stops mid-joke), else a short fade. Tape wow, band-limited by the 'tv' space."""
    if src_t0 is None or src_t1 is None:
        raise KeyError('tv_voice needs src_t0 / src_t1')
    p = os.path.join(W, 'align', 'vo_en.wav')
    if p not in _VO:
        _VO.clear()
        x, sr = sf.read(p, dtype='float32', always_2d=True)
        x = x.mean(1)
        if sr != SR:
            x = soxr.resample(x, sr, SR).astype(np.float32)
        _VO[p] = x
    x = _VO[p][n_(float(src_t0)):n_(float(src_t1))].copy()
    if len(x) < n_(0.05):
        raise KeyError('tv_voice: empty source span')
    nn = len(x); t = np.arange(nn) / SR
    r = 1 + 0.003 * np.sin(2 * np.pi * 0.5 * t + rng.uniform(0, 6)) + 0.0008 * np.sin(2 * np.pi * 6.2 * t)
    pos = np.clip(np.cumsum(r) - r[0], 0, nn - 2); i = pos.astype(np.int64); f = (pos - i).astype(np.float32)
    x = x[i] * (1 - f) + x[i + 1] * f
    x = fade(x.astype(np.float32), 0.01, 0.008 if cut else 0.12)
    return st(x), 0.0, 0.0, False


def r_rule_lie(rng, sp, mode='flicker', **_):
    """The rule-6 card revealed as the lie (film.py): mode 'flicker' (the card's light stutters: an electrical zap,
    arc ticks, a lamp-flicker burst) | 'tear' (the paper tearing: a sharp rip, a low thud)."""
    if mode == 'tear':
        E = src(category='sfx/foley/paper', has=['papertear']) or src('tape_rip')
        y = fade(pnorm(audio(_pick(rng, E, 1.0))), 0.003, 0.1)
        y = _seq([(0.0, hp(y, 200, 2)), (0.0, st(sub_boom(70, 45, 0.5, 0.0)) * 0.3)], 0.1)
        return y, onset_s(y, -12), 0.0, False
    f, *_r = r_lamp_flicker(rng, sp, dur=0.45, times=[0.0, 0.05, 0.11, 0.2, 0.26, 0.45])
    g, *_r = r_glitch(rng, sp, dur=0.3, amount=0.6)
    y = _seq([(0.0, f), (0.0, g * 0.5)], 0.05)
    return y, 0.0, 0.0, False


def memory_fx(y, rng):
    """21 years ago: duller, further, a slow tape wow, a little more room."""
    y = eq(lp(hp(st(y), 120, 2), 4500, 2), ('hs', 2500, -3, 0.7))
    n = len(y)
    if n > n_(0.3):
        r = 1 + 0.003 * np.sin(2 * np.pi * 0.6 * np.arange(n) / SR + rng.uniform(0, 6))
        pos = np.minimum(np.cumsum(r) - r[0], n - 2); i = pos.astype(np.int64); f = (pos - i)[:, None]
        y = (y[i] * (1 - f) + y[i + 1] * f).astype(np.float32)
    return reverb(y, 'hall', 0.18, 0.01, hpf=200)


# ======================================================================================== Bunnyman film recipes
# "If The Bunnyman Asks You To Close Your Eyes... DON'T COUNT TO SEVEN". The owner's bunny set first
# (W/samples/epidemic: knuckle knocks, door kick-ins and impacts, glass, fire, plastic boxes, rings and coins, books,
# the music-box winding, owls, parade crowds, hospital corridors, fights and bones; the verdict on every file is in
# W/mix/sfx_review.md), then the dummy, delivery, police and mirror sets and the free library; synthesis for the
# plastic egg's shell, the brass flap, the barrel's metal, the bulb, the zipper, the curtain rings and the
# cry (audio/voicesynth.py: the real Laurie's own voice). The jingle's versions come from audio/jingle.py.

def _has(name, *keys, **kw):
    """Entries serving `name` whose id contains any of keys (all if none)."""
    return src(name, has=list(keys) if keys else None, **kw)


def _bunny_pool(key, name, keys, mode='onset', **seg):
    return pool(key, lambda: _has(name, *keys), mode, **seg)


def _ramp_env(n, a, r):
    e = np.ones(n, np.float32)
    a, r = min(n, n_(a)), min(n, n_(r))
    if a > 1: e[:a] = np.linspace(0, 1, a) ** 2
    if r > 1: e[-r:] *= np.linspace(1, 0, r) ** 1.5
    return e


def r_ambience_woods(rng, sp, dur=30.0, crickets=0.6, owl=0.5, wind=0.5, frogs=0.25, dog=0.0, **_):
    """BED. The night at the edge of Holloway Woods in early spring: crickets and a few frogs in the long grass, wind
    moving through bare branches, a tawny owl now and then (the bunny set; its two digital drop-outs are skipped), a
    far dog when dog > 0."""
    d = float(dur); n = n_(d)
    out = np.zeros((n, 2), np.float32)
    C = src(category='sfx/ambience', has=['night_crickets_ambience_on_rural', 'ambforst_night', 'swamp_cricket', '12_cricket'])
    if C:
        for k, e in enumerate(C[:4]):
            x = excerpt(e, d, rng, 2.0)
            single = '12_cricket' in e['id'] or 'swamp_cricket' in e['id']           # one cricket close: kept back
            out += hp(x, 900 if single else 350, 2) * (0.12 if single else (0.5 if k else 1.0)) * crickets
    S = _has('ambience_woods', 'evening_ambience_crickets_distant_traffic')
    if S:                                              # the suburban crickets (the traffic hum filtered away)
        out += hp(excerpt(S[0], d, rng, 2.0), 600, 4) * 0.45 * crickets
    F = _has('ambience_woods', 'rural_lake')
    if F and frogs > 0:
        out += lp(hp(excerpt(F[0], d, rng, 2.0), 300, 2), 5000, 2) * 0.5 * frogs
    O = _has('ambience_woods', 'tawny_owl')
    if O and owl > 0:
        e = O[0]; y = audio(e); L = len(y)
        ok = [(int(a * SR), int(b * SR)) for a, b in ((1.0, 28.0), (31.0, 117.5)) if b * SR < L]
        t = 0
        while ok and t < n:
            a, b = ok[int(rng.integers(len(ok)))]
            m = min(n - t, b - a - SR)
            if m <= SR:
                break
            o = int(rng.integers(a, b - m)) if b - a - m > 0 else a
            seg = fade(y[o:o + m], 1.0, 1.0)
            place(out, lp(seg, 6000, 2) * owl * 1.4, t); t += m - SR
    if len(O) > 1 and owl > 0:
        out += lp(excerpt(O[1], d, rng, 2.0), 3000, 2) * 0.4 * owl
    Wd = src(category='sfx/ambience', has=['civitas__wind', 'civitas__gust'])
    if Wd and wind > 0:
        w_ = excerpt(Wd[0], d, rng, 2.0)
        tt = np.arange(n) / SR
        g = (0.55 + 0.45 * np.sin(2 * np.pi * tt / rng.uniform(9, 15) + rng.uniform(0, 6))) ** 2
        branches = bp(noise(d, int(rng.integers(1 << 30))), 600, 3200, 2) * (lp(noise(d, int(rng.integers(1 << 30))), 3, 1) * 30) ** 2
        out += (lp(w_, 2200, 2) * 0.8 + st(branches) * 0.002) * g[:, None].astype(np.float32) * wind
    if dog > 0:
        D = src(category='sfx/ambience', has=['civitas__dog'])
        for _k in range(int(max(1, d / 20 * dog))):
            if D:
                b = lp(audio(_pick(rng, D, 1.0)), 2500, 2)
                place(out, reverb(b, 'forest', 0.6, 0.03) * 0.25 * dog, int(rng.uniform(0, max(1, n - len(b)))))
    return fade(out, 1.0, 1.0), 0.0, 0.0, False


def r_owl_hoot(rng, sp, **_):
    """One tawny owl call, deep in the trees."""
    P = _bunny_pool('owl', 'owl_hoot', ['tawny_owl_song_male_forest_night'], 'phrase', gap=0.6, max_len=4.0, keep=-12)
    y = P.get(rng, rj=0.0, tilt=0.5, fo=0.3)
    return fade(hp(y, 250, 2), 0.05, 0.3), 0.0, 0.0, False


def r_crowd_parade(rng, sp, dur=20.0, cheer=0.6, drums=0.0, applause=0.3, swell_at=None, **_):
    """BED. The 1987 Easter parade: kids cheering close (the bunny set's Norwegian children), the adult walla far
    (low-passed), applause rising as a float passes (swell_at: s), a passing snare cadence when drums > 0 (never
    under the jingle: its tempo is not the jingle's)."""
    d = float(dur); n = n_(d)
    out = np.zeros((n, 2), np.float32)
    K = _has('crowd_parade', 'kids_cheering')
    A = _has('crowd_parade', 'festival_parade_ring')
    Ap = _has('crowd_parade', 'winner_horse')
    Dr = _has('crowd_parade', 'snare_drum')
    if K: out += lp(excerpt(K[0], d, rng, 1.5), 9500, 2) * (0.5 + 0.7 * cheer)
    if A:
        e = A[0]; y = audio(e)[n_(2.0):]
        o = int(rng.integers(0, max(1, len(y) - n))) if len(y) > n else 0
        out += _fit(lp(y[o:o + n], 2500, 2), n, rng) * 0.35
    if Ap and applause > 0: out += lp(excerpt(Ap[0], d, rng, 1.5), 4000, 2) * 0.4 * applause
    if Dr and drums > 0: out += lp(excerpt(Dr[0], d, rng, 1.5), 3500, 2) * 0.5 * drums
    if swell_at is not None:
        tt = np.arange(n) / SR
        out *= (1 + 1.4 * np.clip(1 - np.abs(tt - float(swell_at)) / 2.5, 0, 1) ** 1.5)[:, None].astype(np.float32)
    return fade(out, 0.5, 0.8), 0.0, 0.0, False


def r_hospital_corridor(rng, sp, dur=20.0, busy=0.4, **_):
    """BED. Holloway State Hospital's corridor: far walla, doors, a phone, footsteps (the bunny set's quiet
    corridor), with the busier Polish ward (speakerphone, beeps) low-passed under it when busy > 0."""
    d = float(dur)
    Q = _has('hospital_corridor', 'different_distances')
    B = _has('hospital_corridor', 'speakerphone')
    out = excerpt(Q[0], d, rng, 2.0) if Q else noise(d) * 0.001
    out = st(out)
    if B and busy > 0:
        out = out + lp(excerpt(B[0], d, rng, 2.0), 3200, 2) * 0.35 * busy
    return fade(out, 0.8, 0.8), 0.0, 0.0, False


def r_hospital_room(rng, sp, dur=20.0, hum=0.4, **_):
    """BED. A quiet hospital room with the door shut: the corridor through it (2.6 kHz), the HVAC, a faint
    fluorescent hum (120 Hz + harmonics)."""
    d = float(dur); n = n_(d)
    Q = _has('hospital_room', 'different_distances')
    out = lp(excerpt(Q[0], d, rng, 2.0), 2600, 2) * 0.6 if Q else np.zeros((n, 2), np.float32)
    H = src(category='sfx/room_tone', has=['machhvac_hvac_loop', 'ambhome_roomtone'])
    if H:
        out = out + lp(excerpt(H[0], d, rng, 2.0), 1500, 2) * 0.5
    tt = np.arange(n) / SR
    fl = sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((120, 1.0), (240, 0.5), (360, 0.25), (480, 0.12)))
    out = out + st(fl.astype(np.float32)) * 0.0025 * hum
    return fade(out, 0.8, 0.8), 0.0, 0.0, False


def _barrel_ticks(d, rng, density=1.2):
    """The steel drum heating: sparse metallic ticks and pings."""
    n = n_(d); out = np.zeros(n, np.float32)
    for _k in range(int(d * density)):
        t = int(rng.uniform(0, max(1, n - SR // 2)))
        f = rng.uniform(1800, 4200)
        m = modal([f, f * 1.47, f * 2.3], [0.08, 0.05, 0.03], [1, 0.4, 0.2], 0.3, int(rng.integers(1 << 30)), exc=0.0003)
        out[t:t + len(m)] += m[:n - t] * rng.uniform(0.2, 1.0)
    return out


def r_burn_barrel(rng, sp, dur=15.0, ignite=False, size=0.6, **_):
    """BED. The burn barrel in the backyard: embers crackling (the bunny set's carbon embers), a low flame body (the
    big windy flame low-passed: a barrel, not a bonfire), the steel ticking as it heats. ignite=True: Mom sets it
    alight first (the bunny set's burst, a whoomp)."""
    d = float(dur); n = n_(d)
    E = _has('burn_barrel', 'embers')
    F = _has('burn_barrel', 'large_flame')
    out = np.zeros((n, 2), np.float32)
    if E: out += excerpt(E[0], d, rng, 1.5) * 0.9
    if F: out += lp(excerpt(F[0], d, rng, 1.5), 1800 + 1500 * size, 2) * (0.35 + 0.5 * size)
    out += st(_barrel_ticks(d, rng)) * 0.05
    pre = 0.0
    if ignite:
        B = _has('burn_barrel', 'burst')
        if B:
            gs = grains(B[0], 'phrase', gap=0.1, max_len=1.4, keep=-12)
            a, b = gs[int(rng.integers(len(gs)))]
            whoomp = fade(pnorm(audio(B[0])[a:b]), 0.003, 0.3)
            out *= np.clip(np.arange(n) / n_(0.9), 0, 1)[:, None].astype(np.float32)
            place(out, whoomp * 1.2, 0)
    return fade(out, 0.02 if ignite else 0.6, 1.0), pre, 0.0, False


def r_plastic_melt(rng, sp, dur=4.0, **_):
    """DUR. A plastic egg melting in the fire: the shell softening (a low sizzle), bubbles popping, the plastic
    crackling and sagging (pitched-down crackle), a sweet hiss."""
    d = float(dur); n = n_(d)
    F = _has('plastic_melt', 'large_flame')
    E = _has('plastic_melt', 'embers')
    out = np.zeros((n, 2), np.float32)
    if F: out += hp(excerpt(F[0], d, rng, 1.0), 2500, 2) * 0.5
    if E: out += _fit(rate(lp(excerpt(E[0], d * 0.8, rng, 1.0), 6000, 2), 0.8), n, rng) * 0.6
    t = 0.2
    while t < d - 0.2:                                   # bubbles
        L = rng.uniform(0.01, 0.03); tt = np.arange(n_(L)) / SR
        f = rng.uniform(300, 1200)
        b = np.sin(2 * np.pi * np.cumsum(f * (1 + 2 * tt / L)) / SR) * np.exp(-tt / (L / 3))
        place(out, st(b.astype(np.float32)) * rng.uniform(0.05, 0.15), n_(t)); t += rng.uniform(0.08, 0.35)
    return fade(out, 0.3, 0.6), 0.0, 0.0, False


def _egg_shell(rng, f0=None, dec=1.0):
    """The hollow plastic egg: a thin shell's modes (1-4.5 kHz), short."""
    f0 = f0 or rng.uniform(1150, 1450)
    return modal(np.array([1.0, 1.62, 2.31, 3.1]) * f0, np.array([0.03, 0.02, 0.014, 0.01]) * dec, [1.0, 0.6, 0.4, 0.25],
                 0.12, int(rng.integers(1 << 30)), exc=0.0005)


def _ring_tick(rng, f0=None, ring=1.0):
    """A small gold band touching plastic or wood: a tiny tick and its own high ring (inharmonic, 3-9 kHz)."""
    f0 = f0 or rng.uniform(3100, 3700)
    m = modal(np.array([1.0, 1.58, 2.21, 2.79]) * f0, np.array([0.25, 0.12, 0.08, 0.05]) * ring, [1.0, 0.5, 0.35, 0.2],
              0.6, int(rng.integers(1 << 30)), exc=0.0002)
    return m


def _plastic_pool():
    return pool('plastic_snaps', lambda: _has('egg_open', 'plastic_box_small', 'thermometer', 'lunch_box', 'food_box'),
                'onset', gap=0.06, max_len=0.35, keep=-14)


def r_egg_tap(rng, sp, **_):
    """'At midnight, there's one soft tap on the front door.' One soft knuckle tap (the bunny set's old wooden door),
    the door's boom under it."""
    K = pool('knuckle_new', lambda: _has('knock_family', 'knuckles'), 'onset', gap=0.08, max_len=0.6, keep=-10)
    g = K.get(rng, rj=0.03, tilt=1.0, fo=0.15)
    body = st(modal([88, 133, 181, 247], [0.18, 0.14, 0.1, 0.07], [1, 0.7, 0.5, 0.3], 0.5, int(rng.integers(1 << 30)))) * 0.25
    y = _seq([(0, g * 0.8), (0.002, body)], 0.2)
    return y, onset_s(y, -12), -4.0, False


def r_egg_set(rng, sp, surface='mat', **_):
    """The plastic egg set down: on the coir doormat (a dull small plastic tock, the mat's bristles) or 'wood'."""
    P = _plastic_pool()
    g = lp(P.get(rng, rj=0.05, fo=0.05), 6000 if surface == 'wood' else 3500, 2) * 0.7
    sh = st(_egg_shell(rng, dec=0.6)) * 0.25
    lay = [(0, g), (0.001, sh)]
    if surface != 'wood':
        lay.append((0.0, st(bp(noise(0.08, int(rng.integers(1 << 30))), 2000, 7000, 2) * np.exp(-np.arange(n_(0.08)) / n_(0.02))) * 0.08))
    E = _has('egg_set', 'egg_take_out')
    if E:
        lay.append((0.0, lp(pnorm(audio(E[0]))[:n_(0.06)], 4000, 2) * 0.12))
    y = _seq(lay, 0.1)
    return y, onset_s(y, -12), 0.0, False


def r_egg_rattle(rng, sp, dur=1.6, strength=1.0, **_):
    """'And out on the doormat, the egg rattles. Like something inside wants out.' The egg rocking on the mat
    (plastic knocks) with the ring loose inside it (metal ticks inside a plastic shell), in shaking bursts."""
    P = _plastic_pool()
    d = float(dur); ev = []; t = 0.0
    while t < d:
        k = int(rng.integers(3, 7))
        for j in range(k):
            a = rng.uniform(0.5, 1.0) * strength
            if rng.uniform() < 0.55:
                g = lp(P.get(rng, rj=0.08, fo=0.03)[:n_(0.06)], 5000, 2) * 0.35 * a
                ev.append((t, g))
            r_ = st(lp(_ring_tick(rng, ring=0.25), 7000, 2)) * 0.10 * a
            ev.append((t + rng.uniform(0, 0.01), st(_egg_shell(rng, dec=0.5)) * 0.18 * a))
            ev.append((t + rng.uniform(0.003, 0.015), r_))
            t += rng.uniform(0.035, 0.075)
        t += rng.uniform(0.15, 0.45)
    y = _seq(ev, 0.2)
    return fade(y, 0.005, 0.1), 0.0, 0.0, False


def r_egg_open(rng, sp, ring=True, **_):
    """'And I open the egg.' The two old plastic halves pop apart (the bunny set's thermometer case / small box
    lid), the shell's hollow ring, and the gold ring inside clinking against the plastic."""
    E = _has('egg_open', 'thermometer') + _has('egg_open', 'plastic_box_small')
    e = _pick(rng, E)
    gs = grains(e, 'onset', gap=0.05, max_len=0.3, keep=-10)
    a, b = gs[0] if len(gs) else (0, n_(0.2))
    g = fade(pnorm(audio(e)[a:b]), 0.001, 0.05)
    lay = [(0.0, g), (0.002, st(_egg_shell(rng, dec=1.4)) * 0.3)]
    if ring:
        for k, dt in enumerate((0.09, 0.16, 0.21)):
            lay.append((dt + rng.uniform(-0.01, 0.01), st(_ring_tick(rng, ring=0.3)) * (0.12 - 0.03 * k)))
    y = _seq(lay, 0.3)
    return y, onset_s(y, -12), 0.0, False


def r_ring_roll(rng, sp, dur=1.6, **_):
    """'Inside, rolling around, is a gold ring.' The ring rolling round inside the plastic half: a coin rolling (the
    bunny set, its glass brightness taken off) coloured by the shell, with small ticks as it wobbles."""
    R = _has('ring_roll', 'roll_on_glass')
    d = float(dur); n = n_(d)
    if R:
        y = excerpt(_pick(rng, R), d, rng, 0.3)
        y = eq(lp(hp(y, 600, 2), 7500, 2), ('hs', 4000, -8.0, 0.7), ('peak', 1350, 4.0, 1.5), ('peak', 2200, 3.0, 2.0))
    else:
        y = st(bp(noise(d, int(rng.integers(1 << 30))), 1000, 5000, 2)) * 0.2
    tt = np.arange(n) / SR
    wob = (0.6 + 0.4 * np.sin(2 * np.pi * (3 + 4 * tt / d) * tt)) ** 2            # the wobble speeds up as it settles
    y = y[:n] * (wob * np.clip(1 - tt / d, 0, 1) ** 0.5)[:, None].astype(np.float32)
    ev = [(0, y)]
    for k in range(int(d * 5)):
        ev.append((rng.uniform(0, d * 0.9), st(_ring_tick(rng, ring=0.3)) * 0.08))
    return fade(_seq(ev, 0.2), 0.02, 0.15), 0.0, 0.0, False


def r_ring_drop(rng, sp, surface='hand', **_):
    """The ring falling: 'hand' (into a palm: a tiny tick, skin), 'egg' (into the plastic half), 'floor' (on the
    boards: the bunny set's metal shell drop pitched down 4 semitones, its bounces and its ring)."""
    if surface == 'floor':
        P = _bunny_pool('shell_drop', 'ring_drop', ['bullets_shell'], 'phrase', gap=0.35, max_len=1.2, keep=-12)
        g = rate(P.get(rng, rj=0.03, fo=0.2), semis(-4.0))
        y = lp(g, 9000, 2)
        return y, onset_s(y, -12), 0.0, False
    J = _has('ring_drop', 'ring_drop_into_glass_jar', 'jewelry_ring')
    lay = []
    if J:
        e = _pick(rng, J); a = onset_s(audio(e), -12)
        g = fade(pnorm(audio(e)[n_(a):n_(a + 0.04)]), 0.0005, 0.02)            # only the ring's own tick
        lay.append((0.0, hp(g, 1500, 2) * 0.6))
    lay.append((0.001, st(_ring_tick(rng, ring=0.5 if surface == 'hand' else 1.0)) * 0.35))
    if surface == 'hand':
        lay.append((0.0, st(lp(noise(0.05, int(rng.integers(1 << 30))) * np.exp(-np.arange(n_(0.05)) / n_(0.01)), 1500, 2)) * 0.15))
    else:
        lay.append((0.0, st(_egg_shell(rng, dec=0.8)) * 0.3))
    y = _seq(lay, 0.3)
    return y, onset_s(y, -12), 0.0, False


def r_ring_hand(rng, sp, kind='take', **_):
    """The ring handled: 'take' (Mom takes it out of my hand: two tiny ticks, fingers on skin), 'pocket' (into her
    pocket: cloth, a muffled tick against something)."""
    C = _cloth_pool()
    lay = [(0.0, lp(C.get(rng, rj=0.05, fo=0.08), 4000, 2) * 0.4)]
    if kind == 'pocket':
        lay.append((0.18, lp(st(_ring_tick(rng, ring=0.2)), 2500, 2) * 0.15))
        lay.append((0.1, lp(C.get(rng, rj=0.05, fo=0.1), 2500, 2) * 0.5))
    else:
        lay += [(0.05, st(_ring_tick(rng, ring=0.4)) * 0.12), (0.12, st(_ring_tick(rng, ring=0.3)) * 0.07)]
    return _seq(lay, 0.2), 0.0, 0.0, False


def r_oven_mitt(rng, sp, dur=1.0, **_):
    """Quilted oven mitts handling the egg: padded cloth, slow."""
    C = _cloth_pool()
    ev = []; t = 0.0
    while t < float(dur):
        ev.append((t, rate(lp(C.get(rng, rj=0.05, fo=0.1), 2800, 2), 0.85) * rng.uniform(0.5, 0.9)))
        t += rng.uniform(0.18, 0.4)
    return _seq(ev, 0.2), 0.0, 0.0, False


KNOCK_JINGLE = (0.0, 1.0, 3.0, 3.5, 4.0, 6.0, 7.0)    # jingle.KNOCK_BEATS: "Hop, hop" / "The Bun-ny" / two more


def _knuckle_pool():
    return pool('knuckle_new', lambda: _has('knock_family', 'knuckles'), 'onset', gap=0.08, max_len=0.6, keep=-10)


def _crisp_knuckle_pool():
    """The knuckle grains without the dullest 40 % (energy share above 1 kHz): the final mix measured some family knocks
    -21 to -27 dB above 300 Hz (a thud on a phone); the knock is rule 3's whole sound and must read."""
    key = 'knuckle_crisp'
    if key not in _POOLS:
        P = _knuckle_pool()
        sc = []
        for eid, a, b in P.items:
            y = mono(audio(eid)[a:b]).astype(np.float64)
            sc.append(float(np.sum(hp(y.astype(np.float32), 1000, 2).astype(np.float64) ** 2) / (np.sum(y ** 2) + 1e-12)))
        thr = float(np.percentile(sc, 40)) if sc else 0.0
        Q = Pool.__new__(Pool); Q.key = key
        keep = [i for i, v in enumerate(sc) if v >= thr] or list(range(len(P.items)))
        Q.items = [P.items[i] for i in keep]; Q.w = np.array([P.w[i] for i in keep], float)
        _POOLS[key] = Q
    return _POOLS[key]


def r_knock_family(rng, sp, beat=0.476, groups=None, force=0.75, soft=False, door=1, times=None, **_):
    """The family knock, 2-3-2, on the jingle's beat (beat = s per quarter, jingle.TEMPO 126 -> 0.476): knocks on
    beats 0, 1 | 3, 3.5, 4 | 6, 7 ("Hop, hop" / "The Bun-ny" ... ). groups: the start time (s from the cue) of each
    of the three groups, to sit them in the narration's gaps (the spacing inside a group stays on the beat).
    Recorded knuckles on an old wooden door (the bunny set) + the door's body modes + its low boom; the first
    transient lands on the cue. soft=True: Grandma's knock on the kitchen table (the memory), or a gentle one."""
    K = _knuckle_pool() if soft else _crisp_knuckle_pool()
    dr = np.random.default_rng(2000 + int(door))
    modes = np.array([86, 131, 179, 244, 334, 482]) * (1 + 0.04 * dr.standard_normal())
    g_beats = [(0.0, 1.0), (3.0, 3.5, 4.0), (6.0, 7.0)]
    starts = [g[0] * beat for g in g_beats] if not groups else [float(x) for x in groups]
    if times is not None:                                 # the final mix: the knocks on the picture's own frames
        tl_ = [float(x) for x in (times if isinstance(times, (list, tuple)) else [times])]
        g_beats = [(0.0,)] * len(tl_); starts = tl_; beat = 0.0
    ev = []
    f = 0.35 if soft else float(force)
    for gi, (gb, s0) in enumerate(zip(g_beats, starts)):
        for j, b in enumerate(gb):
            t = s0 + (b - gb[0]) * beat + rng.normal(0, 0.006)
            v = f * (1.0 if j == 0 else 0.9) * rng.uniform(0.92, 1.04)
            g = K.get(rng, rj=0.03, tilt=1.0, fo=0.1)
            body = st(modal(modes * (1 + 0.01 * rng.standard_normal()), [0.18, 0.14, 0.11, 0.08, 0.06, 0.04],
                            np.array([1, 0.8, 0.6, 0.45, 0.3, 0.2]) * v ** 1.5, 0.6, int(rng.integers(1 << 30))))
            lay = _seq([(0, g * v), (0.001, body * (0.15 if soft else 0.25))], 0.05)
            if not soft:                                  # final mix: the knuckle's crack above 1.5 kHz, so a phone
                lay = _seq([(0, lay), (0, hp(g, 1500, 2) * 0.9 * v)], 0.0)   # hears the knock (was -21 dB > 300 Hz)
            ev.append((t, lay))
    y = _seq(ev, 0.4)
    if soft:
        y = lp(y, 5000, 2)
    return y, onset_s(y, -12), (-6.0 if soft else 0.0), False


def r_slot_flap(rng, sp, action='open', dur=None, **_):
    """The brass flap of the mail slot. 'open': pushed open from outside, slowly: the spring hinge creaks, the plate
    scrapes its frame, the brass rings faintly; 'close': let down gently; 'snap': snapped shut (a bright brass clack,
    the door answering); 'hold' (dur: held open while the voice comes through: the spring straining, the plate
    trembling, very faint). Synthesised brass plate modes over the recorded mailbox / latch (police set) for the
    mechanism."""
    M = pool('mailbox', lambda: _has('slot_flap', 'mailbox') + _has('slot_flap', 'metal_click'), 'onset', gap=0.08,
             max_len=0.5, keep=-16)
    plate = lambda dec=1.0: st(modal(np.array([1730, 2890, 4120, 6050]) * (1 + 0.01 * rng.standard_normal()),
                                     np.array([0.09, 0.06, 0.04, 0.025]) * dec, [1.0, 0.7, 0.45, 0.2], 0.4,
                                     int(rng.integers(1 << 30)), exc=0.0003))
    if action in ('open', 'creak'):
        d = 1.1; tt = np.arange(n_(d)) / SR
        C = pool('creak_short', lambda: src(category='sfx/creaks_scrapes', tags=['creak']), 'onset', gap=0.2, max_len=0.9)
        cr = C.get(rng, rj=0.05, fo=0.1)
        cr = bp(rate(cr, semis(rng.uniform(6, 9))), 700, 5000, 2)           # the small spring hinge: a dry, high creak
        cr = _fit(cr, n_(0.75), rng) * np.sin(np.pi * np.clip(np.arange(n_(0.75)) / n_(0.75), 0, 1))[:, None].astype(np.float32) ** 0.7
        scr = st(bp(noise(d, int(rng.integers(1 << 30))), 1500, 6000, 2) * np.sin(np.pi * tt / d) ** 2) * 0.03
        g = M.get(rng, rj=0.05, fo=0.05) * 0.25
        y = _seq([(0.0, g), (0.05, cr * 0.6), (0.0, scr), (0.05, plate(0.5) * 0.08)], 0.2)
        return y, 0.0, 0.0, False
    if action == 'hold':                                  # held open from outside (dur): the spring straining,
        d = float(dur or 2.0); n = n_(d); ev = []         # the plate trembling in its frame: tiny ticks, faint creaks
        t = rng.uniform(0.1, 0.4)
        while t < d - 0.1:
            ev.append((t, plate(0.25) * rng.uniform(0.01, 0.03)))
            t += rng.uniform(0.25, 0.7)
        tt = np.arange(n) / SR
        strain = bp(noise(d, int(rng.integers(1 << 30))), 1800, 4500, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * tt)) * 0.004
        y = _seq([(0.0, st(strain))] + ev, 0.1)
        return fade(y, 0.1, 0.2), 0.0, -8.0, False
    g = M.get(rng, rj=0.04, fo=0.05)
    v = 0.45 if action == 'close' else 1.0
    door = st(modal([110, 170, 260], [0.08, 0.06, 0.04], [1, 0.6, 0.35], 0.3, int(rng.integers(1 << 30)))) * 0.3 * v
    y = _seq([(0.0, g * 0.6 * v), (0.001, plate(1.2 if action == 'snap' else 0.7) * 0.35 * v), (0.002, door)], 0.2)
    return y, onset_s(y, -12), (-5.0 if action == 'close' else 0.0), False


_CRY = {}


def _voice_sig():
    """A short hash of the character voices (tools/vo_voices.VOICES) and the narration edit: cached renders made of
    the narrator's voice (the girl's crying, the hums, the girl's broken song) are keyed by it, so a voice or edit
    change re-renders them (fix round 1: the crying was still the old x1.02 girl from the cache)."""
    import voicesynth as VS
    try:
        st_ = os.stat(VS.VO_CLEAN); ed = f'{st_.st_size}_{int(st_.st_mtime)}'
    except OSError:
        ed = ''
    return hashlib.md5((json.dumps(VS.VV.VOICES, sort_keys=True, default=str) + ed).encode()).hexdigest()[:8]


def r_girl_cry(rng, sp, dur=6.0, intensity=0.75, seed_voice=None, sobs=None, **_):
    """DUR. 'On the other side of the door, the little girl starts to cry. Not like a monster. Like a kid who's been
    lost for a very, very long time.' The real Laurie's own voice (the narration's girl voice through vo_voices L:
    a girl's pitch in a man's body, the man an octave under) crying: long wails that crack and shake, hiccup sobs,
    shaky gasps (audio/voicesynth.cry; no library crying: the bunny set's crying is a toddler boy)."""
    import voicesynth as VS
    sv = int(seed_voice if seed_voice is not None else rng.integers(1 << 20))
    sk = hashlib.md5(json.dumps([round(float(x), 3) for x in sobs]).encode()).hexdigest()[:8] if sobs else 'free'
    key = (round(float(dur), 2), round(float(intensity), 2), sv, sk)
    if key not in _CRY:
        p = os.path.join(CACHE, f'cry_{key[0]}_{key[1]}_{sv}_{sk}_{_voice_sig()}.wav')
        if os.path.exists(p):
            _CRY[key] = sf.read(p, dtype='float32')[0]
        else:
            y = VS.cry(float(dur), 'L', sv, float(intensity), sobs=sobs).astype(np.float32)
            os.makedirs(CACHE, exist_ok=True); sf.write(p, y, SR, subtype='FLOAT'); _CRY[key] = y
    y = st(_CRY[key])
    return fade(y, 0.05, 0.4), 0.0, 0.0, False


def r_jingle(rng, sp, version='speaker', dur=None, stop='fade', seed_tune=None, **kw):
    """The Pemberton's jingle as a sound in the scene (audio/jingle.py renders it; cached): version 'speaker' (the
    dying portable speaker in the woods), 'vhs', 'parade', 'musicbox', 'hum' (Mom), 'hum_x' (the old body),
    'girl', 'knocks', 'climax', 'count' (n=1..7), 'outro', 'studio'. dur crops it (stop 'fade' | 'cut' | 'drag': the
    tape dragging to a halt). Extra keys go to jingle.render (anchors, tempo, loops, speed...)."""
    import jingle as JG
    sv = int(seed_tune if seed_tune is not None else 3)
    keyd = json.dumps({'v': version, 's': sv, 'voices': _voice_sig() if version in ('hum', 'hum_x', 'girl') else '',
                       **{k: v for k, v in kw.items() if k not in ('cue_t',)}}, sort_keys=True, default=str)
    h = hashlib.md5(keyd.encode()).hexdigest()[:12]
    p = os.path.join(CACHE, f'jingle_{version}_{h}.wav')
    if os.path.exists(p):
        y = sf.read(p, dtype='float32', always_2d=True)[0]
    else:
        y, _info = JG.render(version, seed=sv, **{k: v for k, v in kw.items() if k not in ('cue_t',)})
        os.makedirs(CACHE, exist_ok=True); sf.write(p, y, SR, subtype='FLOAT')
    y = st(y)
    if dur:
        n = n_(float(dur))
        if stop == 'drag' and len(y) > n:
            k = min(n, n_(1.0)); r = np.linspace(1.0, 0.05, k) ** 1.5
            pos = np.concatenate([np.arange(n - k), (n - k) + np.cumsum(r)])
            pos = np.clip(pos, 0, len(y) - 2); i = pos.astype(np.int64); f = (pos - i)[:, None].astype(np.float32)
            y = (y[i] * (1 - f) + y[i + 1] * f) * np.concatenate([np.ones(n - k), np.linspace(1, 0, k) ** 0.7])[:, None].astype(np.float32)
        else:
            y = y[:n]
            y = fade(y, 0.0, 0.015 if stop == 'cut' else 0.6)
    return y, 0.0, 0.0, False


def r_attic_door(rng, sp, action='open', **_):
    """The narrow attic door: 'open' (the latch, a long dry creak), 'close' (a soft wooden thump, the latch)."""
    L = pool('latch_small', lambda: src('lock_turn', has=['metallatch', 'deadbolt']), 'onset', gap=0.1, max_len=0.4, keep=-14)
    if action == 'close':
        I = pool('light_door', lambda: _has('attic_door', 'impact_light_door'), 'onset', gap=0.15, max_len=0.9, keep=-12)
        y = _seq([(0.0, lp(I.get(rng, rj=0.04, fo=0.15), 4000, 2)), (0.03, L.get(rng, rj=0.04) * 0.3)], 0.2)
        return y, onset_s(y, -12), 0.0, False
    c, *_r = r_door_creak(rng, sp, dur=1.6, slow=1.2)
    y = _seq([(0.0, L.get(rng, rj=0.04) * 0.5), (0.12, c * 0.9)], 0.2)
    return y, 0.0, 0.0, False


def r_bulb(rng, sp, kind='chain', dur=6.0, **_):
    """The attic's bare bulb: 'chain' (the pull chain's tinkle, the socket's click, the filament's tink as it
    lights), 'buzz' (BED with dur: its faint 120 Hz buzz and a whine)."""
    if kind == 'buzz':
        d = float(dur); tt = np.arange(n_(d)) / SR
        b = sum(a * np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f, a in ((120, 1.0), (240, 0.6), (360, 0.3),
                                                                                 (480, 0.2), (7830, 0.02)))
        b = b * (1 + 0.1 * np.sin(2 * np.pi * 0.7 * tt))
        return fade(st(b.astype(np.float32)) * 0.05, 0.2, 0.3), 0.0, 0.0, False
    c, pre, *_r = r_lamp_out(rng, sp, kind='pull_chain')
    tink = st(modal([4300.0, 6300.0], [0.04, 0.02], [1.0, 0.4], 0.1, int(rng.integers(1 << 30)), exc=0.0002)) * 0.05
    return _seq([(0.0, c), (pre + 0.01, tink)], 0.1), pre, 0.0, False


def r_chest_lid(rng, sp, action='open', **_):
    """Mom's old toy chest: 'open' (the heavy lid's dry hinges groan, the lid resting back against the wall, a
    puff of stale air), 'close' (the lid down: a hollow wooden boom)."""
    if action == 'close':
        B = _wood_body_pool()
        y = _seq([(0.0, lp(B.get(rng, rj=0.04, fo=0.1), 3000, 2)),
                  (0.002, st(modal([95, 150, 240, 410], [0.12, 0.09, 0.06, 0.03], [1, 0.7, 0.4, 0.2], 0.4, int(rng.integers(1 << 30)))) * 0.4)], 0.2)
        return y, onset_s(y, -12), 0.0, False
    cr, *_r = r_wood_creak(rng, sp, kind='grind', dur=1.3)
    rest = _wood_body_pool().get(rng, rj=0.04, fo=0.1) * 0.35
    air = st(lp(noise(0.6, int(rng.integers(1 << 30))), 900, 2) * np.hanning(n_(0.6))) * 0.02
    return _seq([(0.0, rate(cr, 0.9) * 0.8), (1.35, lp(rest, 3500, 2)), (0.2, air)], 0.2), 0.0, 0.0, False


def r_page_flip(rng, sp, n=1, rate_=None, **kw):
    """Diary pages turning (the bunny set's small book): n flips, rate (pages/s, default 2.2 when n > 1)."""
    P = _bunny_pool('pages', 'page_flip', ['book'], 'phrase', gap=0.15, max_len=1.2, keep=-14)
    r_ = float(kw.get('rate', rate_ or 2.2))
    ev = []; t = 0.0
    for k in range(max(1, int(n))):
        ev.append((t, P.get(rng, rj=0.05, fo=0.08) * rng.uniform(0.7, 1.0)))
        t += (1.0 / r_) * rng.uniform(0.8, 1.2)
    return _seq(ev, 0.2), 0.0, 0.0, False


def r_diary_lock(rng, sp, **_):
    """The diary's little pink plastic lock: a tiny plastic snap and the clasp."""
    P = _plastic_pool()
    g = hp(P.get(rng, rj=0.05, fo=0.03), 900, 2)[:n_(0.08)]
    y = _seq([(0.0, g * 0.6), (0.0, st(_egg_shell(rng, f0=2600, dec=0.4)) * 0.2)], 0.05)
    return y, onset_s(y, -12), -3.0, False


def r_window_smash(rng, sp, **_):
    """'At 4:30, the kitchen window explodes.' The bunny set's window smashes layered (the big one, a second for
    density), the frame struck (a heavy wooden thud), shards raining onto the counter and the floor."""
    G = pool('glass_smash', lambda: _has('window_smash'), 'phrase', gap=0.25, max_len=3.4, keep=-12)
    a = G.get(rng, rj=0.03, tilt=1.0, fo=0.3)
    b = G.get(rng, rj=0.05, tilt=1.0, fo=0.3) * 0.55
    fr = _wood_body_pool().get(rng, rj=0.04, fo=0.1)
    tail = st(hp(noise(1.6, int(rng.integers(1 << 30))), 3000, 2) * np.exp(-np.arange(n_(1.6)) / n_(0.4)))
    tl = np.zeros_like(tail)
    for _k in range(18):
        place(tl, st(modal([rng.uniform(3000, 7000)], [0.02], [1.0], 0.05, int(rng.integers(1 << 30)), exc=0.0002)) *
              rng.uniform(0.05, 0.25), n_(rng.uniform(0.2, 1.5)))
    y = _seq([(0.0, a), (0.015, b), (0.0, lp(fr, 2500, 2) * 0.6), (0.25, tail * 0.04 + tl * 0.3),
              (0.0, st(sub_boom(70, 40, 0.5, 0.0)) * 0.3)], 0.3)
    return y, onset_s(y, -10), 0.0, False


def r_door_crash(rng, sp, **_):
    """'The back door crashes open.' A kick-in (the bunny set's 70s door), the door flung into the wall, the frame
    splintering (the mirror set's plywood snap when present), the door bouncing back."""
    K = pool('kick_in', lambda: _has('door_crash', 'kick_out') + _has('door_crash', 'kick_open'), 'phrase', gap=0.3,
             max_len=2.6, keep=-10)
    a = K.get(rng, rj=0.03, fo=0.3)
    S = src(category=None, has=['wood_break_panel_plywood', 'wooden_framesbreaking'])
    lay = [(0.0, a)]
    if S:
        lay.append((0.01, lp(pnorm(audio(_pick(rng, S, 1.0)))[:n_(0.6)], 6000, 2) * 0.35))
    W_ = _wood_body_pool()
    lay.append((0.42, lp(W_.get(rng, rj=0.04, fo=0.15), 3000, 2) * 0.6))    # into the wall
    lay.append((0.0, st(sub_boom(65, 38, 0.6, 0.0)) * 0.4))
    y = _seq(lay, 0.3)
    return y, onset_s(y, -10), 0.0, False


def r_wet_drag(rng, sp, dur=2.5, wet=0.6, **_):
    """'Something heavy comes inside. Wet. Dragging.' A heavy, soft weight dragged over the kitchen floor (the bunny
    set's chair-with-felt-pads drag, slowed), the boards complaining (the stool drag low-passed), the wet,
    matted plush (a squelching, sticky noise layer)."""
    d = float(dur); n = n_(d)
    S = _has('wet_drag', 'floor_protectors')
    R = _has('wet_drag', 'stool_drag', 'chair_wooden_drag')
    out = np.zeros((n, 2), np.float32)
    if S:
        out += _fit(rate(pnorm(audio(S[0])), 0.7), n, rng) * 0.8
    if R:
        out += _fit(lp(rate(pnorm(audio(_pick(rng, R))), 0.75), 1500, 2), n, rng) * 0.4
    tt = np.arange(n) / SR
    am = np.clip(lp(noise(d, int(rng.integers(1 << 30))), 14, 1) * 25, 0, None) ** 1.5
    sq = bp(noise(d, int(rng.integers(1 << 30))), 250, 1800, 2) * am
    out += st(sq) * 0.25 * wet
    pulls = np.zeros(n, np.float32)                      # it moves in heaves
    t = 0.0
    while t < d:
        L = rng.uniform(0.5, 0.9); pulls += np.clip(1 - np.abs(tt - t - L / 2) / (L / 2), 0, 1) ** 0.8; t += L + rng.uniform(0.1, 0.35)
    out *= (0.25 + 0.75 * np.clip(pulls, 0, 1))[:, None]
    return fade(out, 0.1, 0.3), 0.0, 0.0, False


def r_hatchet_step(rng, sp, n=4, rate=0.75, weight=1.0, thunk_only=False, far=False, **_):
    """'Footsteps on the stairs. Slow. And behind them, something hard knocking against every step. Thunk. Thunk.'
    Per step: a heavy, slow tread on the wooden stair (the barefoot pool, weighted, the tread's modes), then 0.3 s
    later the hatchet head knocking the step it just left (the bunny set's wood chop + the axe on a wooden edge,
    low-passed: no metal ring), a short scrape of the head over the nosing between. The first tread lands on t;
    every Thunk is at t + k / rate + 0.3."""
    T = _barefoot_pool()
    Ch = pool('chop', lambda: _has('hatchet_step', 'wood_chopping') + _has('hatchet_step', 'shield_edge'), 'onset',
              gap=0.2, max_len=0.6, keep=-10)
    Sc = pool('axe_scrape', lambda: _has('hatchet_step', 'axe_scrape'), 'phrase', gap=0.1, max_len=1.8, keep=-12)
    ev = []
    for k in range(int(n)):
        t = k / float(rate) * (1 + 0.05 * rng.standard_normal()) if k else 0.0
        g = lp(T.get(rng, rj=0.04, fo=0.05), 3500, 2) * weight
        tread = st(modal(np.array([92, 160, 248, 330]) * (1 + 0.03 * rng.standard_normal()), [0.09, 0.07, 0.05, 0.03],
                         [1, 0.7, 0.45, 0.3], 0.3, int(rng.integers(1 << 30)))) * 0.25 * weight
        sc = Sc.get(rng, rj=0.05, fo=0.05)
        o = int(rng.integers(0, max(1, len(sc) - n_(0.22))))
        sc = fade(lp(sc[o:o + n_(0.22)], 2800, 2), 0.03, 0.08) * 0.18
        th = lp(Ch.get(rng, rj=0.03, fo=0.12), 3200, 2)
        bite = pnorm(hp(th, 900, 2), 0.5 * peak(th))     # the head's bite into the tread: what a phone speaker keeps
        tail = [(t + 0.12, sc), (t + 0.3, th * rng.uniform(0.85, 1.0)), (t + 0.3, bite),
                (t + 0.302, st(modal([120, 210, 330], [0.06, 0.04, 0.03], [1, 0.6, 0.3], 0.2, int(rng.integers(1 << 30)))) * 0.2)]
        ev += tail if thunk_only else [(t, g), (t + 0.004, tread)] + tail
    y = _seq(ev, 0.4)
    if thunk_only:                     # the final mix: film.py cues each Thunk on its frame (hatchet_thunk): the
        y = y[n_(0.1):]                # scrape and the head only, the head's bite landing on the cue
        if far:
            y = lp(y, 2400, 2) * 0.7
        y = eq(hp(y, 80, 2), ('ls', 220, -6.0, 0.7), ('peak', 1800, 3.0, 1.0))
        return y, 0.2, 0.0, False
    y = eq(hp(y, 80, 2), ('ls', 220, -6.0, 0.7), ('peak', 1800, 3.0, 1.0))   # through the door the knock must still
    return y, onset_s(y, -14), 0.0, False                                      # read on a phone (tests: -18 dB > 300 Hz)


def r_doorknob(rng, sp, kind='turn', **_):
    """The bathroom doorknob from inside: 'turn' (turned gently from outside: the spindle's small squeak, the
    latch sliding back to the locked bolt and stopping), 'rattle' (tried hard)."""
    P = pool('knob', lambda: _has('doorknob') + src(category='sfx/foley/locks', has=['frontdoorknob']), 'onset', gap=0.08,
             max_len=0.5, keep=-14)
    d = 0.7; tt = np.arange(n_(d)) / SR
    f = 2200 + 400 * tt / d
    sq = bp(np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32) * np.abs(np.sin(2 * np.pi * 9 * tt)), 1500, 4000, 2)
    sq = st(sq * np.sin(np.pi * tt / d) * 0.03)
    if kind == 'rattle':
        ev = [(0.05 * k + rng.uniform(0, 0.02), P.get(rng, rj=0.05, fo=0.04) * rng.uniform(0.5, 0.9)) for k in range(5)]
        return _seq(ev, 0.1), 0.0, 0.0, False
    a = P.get(rng, rj=0.04, fo=0.05) * 0.5
    stop = P.get(rng, rj=0.04, fo=0.05) * 0.35
    return _seq([(0.0, sq), (0.05, a), (0.62, stop)], 0.1), 0.0, 0.0, False


def r_paper_under_door(rng, sp, dur=1.2, **_):
    """'Something slides under the door.' A sheet of drawing paper pushed through the gap under the bathroom door:
    paper on the tile (dry friction), the door's bottom edge catching it, a last flick."""
    d = float(dur)
    P = _has('paper_under_door', 'paper_handle', 'rustl')
    base = excerpt(_pick(rng, P), d, rng, 0.2) if P else st(noise(d) * 0.01)
    base = eq(hp(base, 700, 2), ('hs', 5000, -3.0, 0.7))
    tt = np.arange(len(base)) / SR
    env = np.clip(tt / 0.15, 0, 1) * np.clip((d - tt) / 0.25, 0, 1)
    fr = st(bp(noise(d, int(rng.integers(1 << 30))), 2500, 8000, 2) * env) * 0.02
    y = base * env[:, None].astype(np.float32) * 0.8 + fr
    return fade(y, 0.05, 0.1), 0.0, 0.0, False


def r_struggle(rng, sp, kind='full', dur=5.0, **_):
    """The fight in the hallway, heard from the bathroom ('door' space by default). kind 'wall' (bodies thrown
    against the hall walls: heavy wooden impacts with frames rattling, grabs in cloth), 'shake' (the whole hallway
    shakes: a run of thuds and rattles over ~1.5 s), 'slam' (something slams into the bathroom door: the bunny set's
    boomy kick, an internal-door kick for the attack, the frame rattling, a low whoosh before), 'crack' (a wet, heavy
    crack: the heavy bone break low-passed under a dull body thud and a wet squelch: restrained, not a cartoon),
    'full' (dur: grabs and wall impacts building, the slam, the crack at the end)."""
    I = pool('cab_impact', lambda: _has('struggle', 'cabinet_wood_shelf'), 'phrase', gap=0.2, max_len=1.6, keep=-12)
    G = pool('grabs', lambda: _has('struggle', 'grab_punch_cloth'), 'onset', gap=0.12, max_len=0.45, keep=-14)
    Ld = pool('light_door', lambda: _has('attic_door', 'impact_light_door'), 'onset', gap=0.15, max_len=0.9, keep=-12)

    def wall(v=1.0):
        a = lp(I.get(rng, rj=0.04, fo=0.2), 3500, 2) * v
        r_ = lp(Ld.get(rng, rj=0.06, fo=0.15), 5000, 2) * 0.35 * v
        return _seq([(0.0, a), (0.04, r_), (0.0, st(sub_boom(70, 42, 0.4, 0.0)) * 0.3 * v)], 0.2)

    def slam(v=1.0):
        K = pool('slam_kick', lambda: _has('struggle', 'kick_out_03'), 'phrase', gap=0.3, max_len=2.2, keep=-10)
        Ko = pool('kick_open', lambda: _has('struggle', 'kick_open_internal'), 'phrase', gap=0.2, max_len=0.8, keep=-12)
        Wh = _has('struggle', 'blade_impact_05')
        lay = [(0.0, lp(K.get(rng, rj=0.03, fo=0.3), 1800, 2)), (0.0, lp(Ko.get(rng, rj=0.03, fo=0.1), 4500, 2) * 0.6),
               (0.03, lp(Ld.get(rng, rj=0.06, fo=0.15), 4000, 2) * 0.5),
               (0.0, st(sub_boom(60, 34, 0.9, 0.0)) * 0.6)]
        if Wh:
            w_ = lp(pnorm(audio(Wh[0])), 900, 2)
            ons = onset_s(w_, -6)
            lay.append((-min(0.25, ons), w_[:n_(ons + 0.05)] * 0.25))
        y = _seq([(x + 0.25, s) for x, s in lay], 0.3)
        return y * v, 0.25

    def crack(v=1.0):
        B = pool('bone', lambda: _has('struggle', 'bone_break_heavy') + _has('struggle', 'bone_crack_bone_cracking'),
                 'onset', gap=0.12, max_len=0.6, keep=-10)
        c = lp(B.get(rng, rj=0.03, fo=0.15), 2200, 2)
        th = lp(I.get(rng, rj=0.04, fo=0.2), 1500, 2) * 0.8
        wet = st(bp(noise(0.25, int(rng.integers(1 << 30))), 300, 1500, 2) * np.exp(-np.arange(n_(0.25)) / n_(0.06))) * 0.1
        return _seq([(0.0, th), (0.012, c * 0.9), (0.02, wet), (0.0, st(sub_boom(55, 30, 0.8, 0.0)) * 0.5)], 0.3) * v

    if kind == 'wall':
        y = wall()
        return y, onset_s(y, -12), 0.0, False
    if kind == 'slam':
        y, pre = slam()
        return y, pre, 0.0, False
    if kind == 'crack':
        y = crack()
        return y, onset_s(y, -12), 0.0, False
    if kind == 'shake':
        ev = [(t, wall(rng.uniform(0.4, 0.8))) for t in np.cumsum(rng.uniform(0.2, 0.4, 5)) - 0.2]
        y = _seq(ev, 0.3)
        return y, 0.0, 0.0, False
    if kind != 'full':                 # the final mix: film.py's door_slam kinds ('body', a memory recall...) are one
        y, pre = slam()                # slam, never the 5 s fight
        return y, pre, 0.0, False
    d = float(dur); ev = []; t = 0.0                     # 'full'
    while t < d - 1.2:
        if rng.uniform() < 0.5:
            ev.append((t, wall(rng.uniform(0.5, 0.9))))
        else:
            for j in range(int(rng.integers(2, 4))):
                ev.append((t + 0.09 * j, lp(G.get(rng, rj=0.05, fo=0.08), 3000, 2) * rng.uniform(0.4, 0.8)))
        t += rng.uniform(0.3, 0.7)
    s_, pre = slam(); ev.append((max(0.0, d - 1.2 - pre), s_))
    ev.append((d - 0.25, crack()))
    return _seq(ev, 0.4), 0.0, 0.0, False


def r_key_outside(rng, sp, **_):
    """'The lock turns by itself. From the outside. Mom has a key.' The key pushed into the bathroom lock from the
    hall side (a scrape, the pins), a pause, the bolt turning back (the lock's click on the cue)."""
    k, pre_k, *_r = r_key_in_lock(rng, sp)
    l, pre_l, *_r = r_lock_turn(rng, sp)
    y = _seq([(0.0, lp(k, 6000, 2) * 0.8), (0.75, l)], 0.2)
    return y, 0.75 + pre_l, 0.0, False


def r_sirens_arrive(rng, sp, dur=10.0, n_cars=2, **_):
    """Police cars arriving at the house at dawn: two sirens coming up the road (doppler), the engines, cut off
    one after the other as they pull up. The first siren is the police set's recording, the second synthesised."""
    d = float(dur)
    a, *_r = r_siren_far(rng, 'street', dur=d, dist=1.2, speed=0.0)
    b = siren_synth(d, 'yelp' if n_cars > 1 else 'wail', 120.0, 14.0, d * 0.9, int(rng.integers(1 << 30)))
    n = n_(d); tt = np.arange(n) / SR
    up = np.clip(tt / (d * 0.75), 0, 1) ** 1.5
    cut1, cut2 = d * 0.78, d * 0.9
    ga = (0.3 + 0.7 * up) * np.clip((cut1 - tt) / 0.15, 0, 1)
    gb = (0.2 + 0.8 * up) * np.clip((cut2 - tt) / 0.12, 0, 1)
    y = st(a)[:n] * ga[:len(st(a)[:n]), None].astype(np.float32)
    y = _seq([(0.0, y), (0.6, st(b)[:n] * gb[:n, None].astype(np.float32) * 0.6)], 0.5)
    return fade(y, 0.5, 0.5), 0.0, 0.0, False


def r_vhs_pause(rng, sp, kind='pause', dur=None, **_):
    """The comment prompt's VHS pause: 'pause' (the deck's pause key: a clunk, the picture freezing: the head drum's
    hum and whine, a band of tracking noise, all faint), 'play' (released: a clunk, the transport catching up),
    'stop'. The dummy set's VCR mechanism + synthesis."""
    E = src('vcr', has=['into_vhs'])
    mech = pnorm(audio(E[0])) if E else st(noise(1.0) * 0.01)
    clunk = fade(hp(mech[n_(0.2):n_(0.45)], 150, 2), 0.002, 0.05)
    on = min(0.2, onset_s(clunk, -12))                   # final mix: the clunk's transient on the cue (was +109 ms)
    if kind in ('play', 'resume'):
        rw = hp(mech[n_(1.0):n_(1.5)], 200, 2)
        return _seq([(0.0, clunk), (0.08, fade(rw, 0.02, 0.2) * 0.4)], 0.1), on, 0.0, False
    d = float(dur or 2.5); n = n_(d); tt = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 30 * tt) * 0.5 + np.sin(2 * np.pi * 60 * tt) * 0.4 + np.sin(2 * np.pi * 15734 * tt) * 0.02)
    trk = bp(noise(d, int(rng.integers(1 << 30))), 1500, 7000, 2) * (0.4 + 0.6 * (np.sin(2 * np.pi * 1.7 * tt) > 0.6))
    bed = st((hum * 0.05 + trk * 0.025).astype(np.float32)) * _ramp_env(n, 0.05, 0.3)[:, None]
    return _seq([(0.0, clunk), (0.05, bed)], 0.1), on, 0.0, False


def r_light_switch(rng, sp, kind='wall', **_):
    """'You can turn a light on now.' kind 'wall': a house light switch (a clean toggle snap, the plate);
    'porch': the old porch-light toggle by the front door (a heavier snap) and the bulb outside coming on (a
    tink, its hum starting); 'porch_off': the same switched off."""
    if kind in ('porch', 'porch_on', 'porch_off'):
        c, pre, *_r = r_lamp_out(rng, sp, kind='switch')
        lay = [(0.0, c * 1.1)]
        if kind != 'porch_off':
            lay.append((pre + 0.01, st(modal([4300.0, 6400.0], [0.04, 0.02], [1.0, 0.4], 0.1, int(rng.integers(1 << 30)),
                                             exc=0.0002)) * 0.04))
            bz = st(_lamp_buzz(1.2, rng)) * (np.linspace(0, 1, n_(1.2)) ** 2)[:, None].astype(np.float32) * 0.03
            lay.append((pre + 0.02, bz))
        y = _seq(lay, 0.1)
        return y, pre, 0.0, False
    c, pre, *_r = r_lamp_out(rng, sp, kind='switch')
    return c, pre, 0.0, False


def r_music_box_wind(rng, sp, dur=None, **_):
    """The music box being wound (the bunny set's winding ratchet), dur crops it."""
    E = _has('music_box_wind', 'winding_up')
    y = pnorm(audio(E[0])) if E else st(noise(1.0) * 0.01)
    if dur:
        y = y[:n_(float(dur))]
    return fade(y, 0.005, 0.1), 0.0, 0.0, False


def r_flash_pop(rng, sp, **_):
    """The 1987 newspaper photographer: the shutter, the flash bulb's pop, the film winder."""
    s, *_r = r_camera_shutter(rng, sp, kind='camera')
    pop = st(bp(noise(0.03, int(rng.integers(1 << 30))), 600, 6000, 2) * np.exp(-np.arange(n_(0.03)) / n_(0.006))) * 0.5
    tt = np.arange(n_(0.45)) / SR
    wind = st((bp(noise(0.45, int(rng.integers(1 << 30))), 800, 3000, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 38 * tt))) *
              _ramp_env(len(tt), 0.03, 0.08)) * 0.08
    return _seq([(0.0, s), (0.01, pop), (0.25, wind)], 0.1), 0.0, 0.0, False


def r_dogs_search(rng, sp, dur=8.0, n_dogs=2, **_):
    """1987: the search dogs in Holloway Woods, far off: barks and bays between the trees."""
    D = src(category='sfx/ambience', has=['civitas__dog'])
    d = float(dur); out = np.zeros((n_(d), 2), np.float32)
    for k in range(int(n_dogs) * 3):
        if not D:
            break
        e = _pick(rng, D, 1.0)
        b = audio(e)
        if len(b) > n_(3.0):
            o = int(rng.integers(0, len(b) - n_(2.0))); b = b[o:o + n_(2.0)]
        b = fade(lp(b, 3000, 2), 0.02, 0.2) * rng.uniform(0.4, 1.0)
        place(out, pan(b, rng.uniform(-0.7, 0.7)), int(rng.uniform(0, max(1, len(out) - len(b)))))
    return out, 0.0, 0.0, False


def r_bathtub(rng, sp, kind='settle', **_):
    """The empty porcelain bathtub: 'settle' (two people sitting down in it: clothes on porcelain, a hollow thud),
    'squeak' (skin or a sock squeaking on the enamel)."""
    G = src(category=None, has=['glass_friction_finger_rub'])
    if kind == 'squeak' and G:
        g = pnorm(audio(_pick(rng, G, 1.0)))
        o = int(rng.integers(0, max(1, len(g) - n_(0.5))))
        return fade(rate(g[o:o + n_(0.5)], semis(-5)), 0.02, 0.1) * 0.6, 0.0, 0.0, False
    th = st(modal([140, 230, 410, 760], [0.12, 0.08, 0.05, 0.03], [1, 0.6, 0.35, 0.2], 0.4, int(rng.integers(1 << 30)))) * 0.5
    c = _cloth_pool().get(rng, rj=0.05, fo=0.1) * 0.5
    return _seq([(0.0, c), (0.05, th)], 0.2), 0.05, 0.0, False


def r_body_fall_stairs(rng, sp, n=5, **_):
    """A heavy body in a matted plush suit going down the wooden stairs: thumps on the treads, accelerating, the
    last one on the hall floor (the bunny set's cabinet impacts, low-passed, the soft heavy kenney thumps)."""
    I = pool('cab_impact', lambda: _has('struggle', 'cabinet_wood_shelf'), 'phrase', gap=0.2, max_len=1.6, keep=-12)
    S = pool('soft_heavy', lambda: src(category='sfx/impacts', has=['impact_soft_heavy']), 'onset', gap=0.1, max_len=0.5)
    ev = []; t = 0.0
    for k in range(int(n)):
        v = 0.6 + 0.4 * (k == int(n) - 1)
        ev += [(t, lp(I.get(rng, rj=0.05, fo=0.15), 2000, 2) * v * 0.6), (t, S.get(rng, rj=0.05) * v * 0.7),
               (t, st(sub_boom(70, 40, 0.3, 0.0)) * 0.25 * v)]
        t += max(0.12, 0.35 - 0.05 * k)
    y = _seq(ev, 0.4)
    return y, onset_s(y, -12), 0.0, False


def r_zipper(rng, sp, dur=1.0, **_):
    """'It has a zipper in the back, where zippers go.' A long zipper drawn (synthesised: the teeth, the slider)."""
    d = float(dur); n = n_(d); tt = np.arange(n) / SR
    rate_ = 90 + 220 * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 0.7
    ph = np.cumsum(rate_) / SR
    ticks = np.zeros(n, np.float32)
    idx = np.flatnonzero(np.diff(np.floor(ph)) > 0)
    for i in idx:
        L = n_(0.003)
        ticks[i:i + L] += (rng.standard_normal(min(L, n - i)) * np.exp(-np.arange(min(L, n - i)) / (L / 4))).astype(np.float32)
    y = bp(ticks, 1800, 7000, 2) + bp(noise(d, int(rng.integers(1 << 30))), 2500, 8000, 2) * 0.05
    return fade(st(y * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 0.3), 0.01, 0.05), 0.0, 0.0, False


def r_fridge_paper(rng, sp, magnet=True, **_):
    """'At sundown, the rules went up on the fridge.' The laminated sheet against the fridge door (a flat slap on
    hollow metal), tape torn and pressed, a magnet's clack."""
    t_, *_r = r_tape_rip(rng, sp, kind='rip')
    slap = st(modal([310, 520, 840, 1250], [0.05, 0.035, 0.02, 0.012], [1, 0.6, 0.35, 0.2], 0.2, int(rng.integers(1 << 30)))) * 0.25
    mag = st(modal([2100, 3300], [0.02, 0.01], [1, 0.5], 0.06, int(rng.integers(1 << 30)), exc=0.0003)) * 0.25
    y = _seq([(0.0, slap), (0.35, t_ * 0.6)] + ([(1.1, mag)] if magnet else []), 0.1)
    return y, 0.0, 0.0, False


def r_curtain_close(rng, sp, dur=1.0, **_):
    """'I close the curtains downstairs.' Curtain rings running along a metal rod, the heavy fabric swishing."""
    d = float(dur); n = n_(d); tt = np.arange(n) / SR
    ev = []
    for k in range(int(rng.integers(7, 12))):
        t0 = rng.uniform(0, d * 0.8)
        ev.append((t0, st(modal([rng.uniform(2500, 4000), rng.uniform(5000, 7000)], [0.03, 0.02], [1, 0.4], 0.08,
                                int(rng.integers(1 << 30)), exc=0.0003)) * rng.uniform(0.05, 0.15)))
    swish = bp(noise(d, int(rng.integers(1 << 30))), 400, 3500, 2) * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.2
    rod = bp(noise(d, int(rng.integers(1 << 30))), 2000, 6000, 2) * np.sin(np.pi * np.clip(tt / d, 0, 1)) * 0.3
    y = _seq([(0.0, st((swish * 0.05 + rod * 0.02).astype(np.float32)))] + ev, 0.1)
    return fade(y, 0.02, 0.1), 0.0, 0.0, False


def r_peephole(rng, sp, **_):
    """The front-door peephole's little brass cover swung aside."""
    tt = np.arange(n_(0.12)) / SR
    sc = st(bp(noise(0.12, int(rng.integers(1 << 30))), 2500, 7000, 2) * np.sin(np.pi * tt / 0.12)) * 0.006
    tk = st(modal([3900, 6100], [0.02, 0.01], [1, 0.4], 0.06, int(rng.integers(1 << 30)), exc=0.0002)) * 0.15
    y = _seq([(0.0, sc), (0.1, tk)], 0.05)
    return y, 0.1, 0.0, False



# ---------------------------------------------------------------------------------------- the final mix: picture names
def r_footsteps_grass(rng, sp, n=None, dur=None, rate=1.8, approach=0.0, weight=0.7, foot=None, heavy=False, **_):
    """Steps on grass and the woods path (the yard at night, the 1987 path into Holloway Woods, the burn barrel): the
    shared library's CC0 grassy footsteps (freesfx), soft and dull; heavy=True: the mascot's big padded feet."""
    E = lambda: src(category='sfx/footsteps', has=['grass']) or src('footsteps_porch')
    if heavy:
        weight = max(weight, 1.0)
    y = _steps(rng, 'steps_grass', E, n, dur, rate, approach, 0.0, weight)
    # final mix: the grass grains are mostly < 300 Hz thump (thin on a phone) and peak ~100 ms after their start: the
    # crunch is lifted and the step's peak lands on the cue (the foot plant's frame)
    y = eq(hp(lp(y, 4200 if heavy else 6500, 2), 160, 2), ('peak', 2600, 5.0, 0.9), ('ls', 180, 2.0 if heavy else -2.0, 0.7))
    if foot in ('L', 'R'):
        y = pan(y, -0.08 if foot == 'L' else 0.08)
    return y, min(0.15, onset_s(y, -12)), 0.0, False


def r_wind_gust(rng, sp, strength=0.7, **_):
    """A gust through the bare trees (the shared library's CC0 gusts, civitas), dulled with distance."""
    E = src(category='sfx/ambience', has=['civitas__gust'])
    if E:
        y = pnorm(audio(_pick(rng, E)))[:n_(4.0)]
    else:
        L = 2.0; y = st(lp(noise(L, int(rng.integers(1 << 30))), 700, 2) * np.sin(np.linspace(0, np.pi, n_(L))) ** 2)
    y = lp(hp(y, 120, 2), 3200 + 2500 * float(strength), 2)
    return fade(y, 0.25, 0.6), 0.0, 0.0, False


def r_police_radio(rng, sp, dur=3.0, **_):
    """DUR. The patrol cars' radios at the house at dawn: a garbled dispatch voice (the police set's Epidemic walkie
    recording, band-limited, squelched on and off), far under the narration."""
    d = float(dur or 3.0)
    E = src(None, has=['walkie_talkie_police_radio'])
    v = excerpt(E[0], d, rng, 0.3) if E else st(noise(d, int(rng.integers(1 << 30))) * 0.02)
    v = eq(bp(v, 450, 3000, 3), ('peak', 1600, 4.0, 1.0))
    v = np.tanh(pnorm(v) * 1.8) / np.tanh(1.8)
    k1, *_r = r_police_radio_squelch(rng, sp, kind='key')
    k2, *_r = r_police_radio_squelch(rng, sp, kind='unkey')
    y = _seq([(0.0, k1 * 0.5), (0.08, fade(v, 0.02, 0.05)), (0.1 + d, k2 * 0.4)], 0.2)
    return y, 0.0, 0.0, False


def r_swap(rng, sp, kind='now', **_):
    """The trade under the hand ('...opens them somewhere else. In someone else.' and the narrator's "Seven."): a
    reverse swell sucked in toward the cue (a breath of air and a glassy C#, the count's last note, never home, played
    backwards out of a cold room), cut on the cue by a close, deep thump and the C# ringing forward. kind '1987' (the
    story told): shorter, softer, duller; 'now': the full one. The swell's end lands on t."""
    big = kind != '1987'
    L = 1.35 if big else 0.75
    f = 554.37                                             # C#5 (jingle.COUNT_MIDI: Seven)
    tb = np.arange(n_(0.9)) / SR
    tone_ = (np.sin(2 * np.pi * f * tb) + 0.45 * np.sin(2 * np.pi * f * 2.004 * tb + 1.0)
             + 0.25 * np.sin(2 * np.pi * f * 3.011 * tb + 2.0)) * np.exp(-tb / 0.3)
    burst = np.zeros(len(tb)); k = n_(0.06)
    burst[:k] = noise(0.06, int(rng.integers(1 << 30)))[:k] * np.exp(-np.arange(k) / n_(0.015))
    x = st(lp((tone_ * 0.35 + burst).astype(np.float32), 7000 if big else 4500, 2))
    wet = reverb(x, 'church', 1.0, 0.0, dry=0.25)
    rev = wet[::-1]
    rev = rev[-n_(L):] if len(rev) > n_(L) else rev
    rev = rev * (np.linspace(0, 1, len(rev)) ** 1.6)[:, None].astype(np.float32)
    rev = fade(rev, 0.05, 0.004)
    th = st(sub_boom(58, 30, 1.6 if big else 1.0, 0.12, int(rng.integers(1 << 30)))) * (0.8 if big else 0.5)
    knock = st(modal([96, 158, 236, 410], [0.12, 0.09, 0.06, 0.03], [1, 0.7, 0.45, 0.25], 0.6,
                     int(rng.integers(1 << 30)))) * (0.35 if big else 0.2)
    tg = np.arange(n_(2.5)) / SR
    glass = (np.sin(2 * np.pi * f * tg) + np.sin(2 * np.pi * f * 1.0045 * tg + 0.7)) * np.exp(-tg / 0.7) * 0.5
    glass = reverb(st(glass.astype(np.float32)), 'church', 0.45, 0.02)
    y = _seq([(0.0, rev * 0.9), (L, th), (L, knock), (L + 0.005, glass * (0.22 if big else 0.12))], 0.3)
    if not big:
        y = lp(y, 5000, 2)
    return y, L, 0.0, False


def r_marker_strike(rng, sp, dur=0.42, **_):
    """'There's no Holloway. No Pemberton's.' A felt-tip marker struck hard across newsprint / the egg's stamp: the
    felt's dry fibrous squeal (band noise with a fast fibre chatter, a thin squeak riding it), the paper under it, a
    tick as the tip lifts. Synthesised (the library has no marker)."""
    d = float(dur); n = n_(d); t = np.arange(n) / SR
    env = np.clip(t / 0.02, 0, 1) * np.clip((d - t) / 0.07, 0, 1)
    chatter = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * rng.uniform(55, 85) * t + rng.uniform(0, 6)))
    fib = lp(bp(noise(d, int(rng.integers(1 << 30))), 1500, 5000, 2), 5500, 4) * chatter
    fib = eq(fib, ('peak', 2900, 9.0, 3.0), ('peak', 4300, 5.0, 3.0))
    fq = rng.uniform(2600, 3400) * (1 + 0.08 * t / d)
    sq = np.sin(2 * np.pi * np.cumsum(fq) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 23 * t)) * 0.25
    body = bp(noise(d, int(rng.integers(1 << 30))), 350, 1300, 2) * 0.3
    y = st(((fib + sq + body) * env).astype(np.float32))
    tick = st(modal([3100, 5200], [0.01, 0.006], [1, 0.4], 0.04, int(rng.integers(1 << 30)), exc=0.0002)) * 0.2
    return _seq([(0.0, y), (d - 0.02, tick)], 0.05), 0.0, 0.0, False


def r_water_tap(rng, sp, dur=2.5, **_):
    """DUR. Mom at the kitchen sink: the tap running into the steel basin (turbulent splash noise, bright little drops).
    Synthesised (the library has no tap); heard across the kitchen ('next_room')."""
    d = float(dur); n = n_(d); t = np.arange(n) / SR
    tu = lp(noise(d, int(rng.integers(1 << 30))), 30, 1); tu = 0.75 + 0.5 * tu / (np.abs(tu).max() + 1e-9)
    spl = eq(lp(bp(noise(d, int(rng.integers(1 << 30))), 500, 5000, 2), 5000, 4), ('peak', 1500, 5.0, 1.0),
             ('peak', 3000, 2.0, 1.5)) * tu
    drops = np.zeros(n, np.float32); k = 0.0
    while True:
        k += rng.exponential(1 / 25.0)
        i = n_(k)
        if i >= n - 2000:
            break
        f0 = rng.uniform(700, 2600); L = n_(rng.uniform(0.01, 0.03)); tt = np.arange(L) / SR
        ch = np.sin(2 * np.pi * f0 * (1 + 2.0 * tt / tt[-1]) * tt) * np.exp(-tt / 0.008) * rng.lognormal(0, 0.5)
        drops[i:i + L] += ch.astype(np.float32)
    env = np.clip(t / 0.25, 0, 1) * np.clip((d - t) / 0.4, 0, 1)
    y = st(((spl * 0.4 + lp(drops, 6000, 2) * 0.5) * env).astype(np.float32))
    return y, 0.0, 0.0, False


def r_creek(rng, sp, dur=10.0, flow=0.6, **_):
    """BED. The creek in the ravine under the railroad bridge (the library has none): a dull rush breathing slowly and
    a babble of tiny bubbles (short sine chirps rising in pitch, 300-1600 Hz), decorrelated left and right."""
    d = float(dur); n = n_(d); t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    for c in range(2):
        rush = lp(hp(noise(d, int(rng.integers(1 << 30))), 150, 2), 1100, 2)
        rush = rush * (0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(0.05, 0.12) * t + rng.uniform(0, 6))).astype(np.float32)
        b = np.zeros(n, np.float32); k = 0.0; r_ = 40 + 60 * float(flow)
        while True:
            k += rng.exponential(1.0 / r_)
            if k >= d - 0.06:
                break
            i = n_(k); f0 = float(np.exp(rng.uniform(np.log(300), np.log(1600))))
            tau = rng.uniform(0.004, 0.015); L = n_(tau * 5); tt = np.arange(L) / SR
            ph = 2 * np.pi * np.cumsum(f0 * (1 + 0.3 * float(flow) * tt / tau)) / SR
            m = min(L, n - i)
            b[i:i + m] += (np.sin(ph) * np.exp(-tt / tau) * rng.lognormal(0, 0.6))[:m].astype(np.float32)
        out[:, c] = rush * 0.4 + bp(b, 250, 4000, 2) * 0.1
    return fade(out, 0.8, 1.0), 0.0, 0.0, False


def r_magnet_click(rng, sp, **_):
    """A fridge magnet snapped onto the door (the bunny magnet on the laminated rules): a hard little clack and the
    hollow door's thump."""
    mag = st(modal([2100, 3300, 5200], [0.02, 0.012, 0.006], [1, 0.5, 0.25], 0.06, int(rng.integers(1 << 30)), exc=0.0003))
    door = st(modal([310, 520, 840], [0.05, 0.035, 0.02], [1, 0.6, 0.35], 0.15, int(rng.integers(1 << 30)))) * 0.2
    y = _seq([(0.0, mag), (0.001, door)], 0.05)
    return y, onset_s(y, -12), 0.0, False


def r_magic_sparkle(rng, sp, **_):
    """The Bunnyman's magic trick in 1987 (the egg appears in his empty paw in a little burst of light): a toy-chime
    twinkle in the jingle's key (D major: D6 F#6 A6 D7 F#7 up in 45 ms steps, glockenspiel bars: the 1 : 2.76 : 5.40
    partials of a free bar, a short metal tick on each strike) and a soft high shimmer under it. Synthesised, no samples."""
    notes = [1174.66, 1479.98, 1760.0, 2349.32, 2959.96]
    out = []
    for k, f in enumerate(notes):
        dec = 0.55 - 0.06 * k
        bar = modal([f, f * 2.76, f * 5.40], [dec, dec * 0.35, dec * 0.12], [1.0, 0.32, 0.12], dec + 0.1,
                    int(rng.integers(1 << 30)), exc=0.0002)
        out.append((0.045 * k + float(rng.uniform(-0.004, 0.004)), pan(st(bar) * (0.85 - 0.08 * k), -0.35 + 0.18 * k)))
    tt = np.arange(n_(0.9)) / SR
    shim = st(hp(noise(0.9, int(rng.integers(1 << 30))), 6000, 2) * np.exp(-tt / 0.25) * (1 - np.exp(-tt / 0.03))) * 0.05
    y = _seq(out + [(0.0, shim)], 0.1)
    return y, onset_s(y, -12), 0.0, False


# ---------------------------------------------------------------------------------------- names: aliases + fallbacks

# ======================================================================================== Doctor film recipes
# "If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND". The owner's doctor set first (W/samples/epidemic, flat:
# the old telephone, the classic electric bells, ballpoint pens, the crocodile clip, masking tape, the cinema ticket,
# the match strikes, burning paper, fridge hums, electric buzz, rain in a car, the car idling and driving, the
# automatic glass doors, gurneys, wheelchairs, heart monitors, the hospital waiting room; the verdict on every file
# is in W/mix/sfx_review.md), then the bunny, dummy, delivery, police and mirror sets and the free library; synthesis
# only for the bell's gongs, the plastic and wood bodies, the ballast hum, the wipers and the tones. The HOLD MUSIC
# (audio/hold.py) is reachable here as 'hold_music' (version=...) for the picture's diegetic placements; the score's
# identity events play it too (score.py 'hold').
DOCTOR_NAMES = ('house_night', 'fridge_hum', 'wall_clock', 'landline_ring', 'receiver_up', 'receiver_down',
                'cord_yank', 'dial_tone', 'line_hiss', 'rotary_dial', 'hold_music', 'pen_scratch', 'clipboard',
                'match_strike', 'paper_burn', 'rain_house', 'halverson_car', 'streetlight', 'waiting_room',
                'tv_dead', 'ticket_tear', 'now_serving', 'pulse_count', 'tape_peel', 'medicine_cabinet',
                'carry_child', 'drive_rain', 'er_doors', 'wheelchair', 'er_bustle', 'chair_rock', 'sit_down',
                'office_3am', 'phone_connect', 'typewriter', 'card_tear')
NAMES = NAMES + DOCTOR_NAMES
# one-shots: momentary max, LU rel the voice at gain_db 0; beds (BEDS, and DUR_BEDS given a dur): integrated
# (test 7: tape_peel -3 peaked -2.7 LU over... the voice and drove the limiter 3 dB: -6)
# (test 1: house_night -30 and waiting_room -27 measured -30 LU momentary under the voice, masked by the music: +3)
LEVEL_LU.update(house_night=-27, fridge_hum=-31, wall_clock=-20, landline_ring=-4, receiver_up=-7, receiver_down=-5,
                cord_yank=-3, dial_tone=-20, line_hiss=-26, rotary_dial=-8, hold_music=-17, pen_scratch=-12,
                clipboard=-7, match_strike=-5, paper_burn=-19, rain_house=-27, halverson_car=-29, streetlight=-31,
                waiting_room=-24, tv_dead=-31, ticket_tear=-3, now_serving=-5, pulse_count=-11, tape_peel=-6,
                medicine_cabinet=-6, carry_child=-11, drive_rain=-23, er_doors=-8, wheelchair=-14, er_bustle=-23,
                chair_rock=-9, sit_down=-8, office_3am=-31, phone_connect=-8, typewriter=-12, card_tear=-3,
                pen_click=-6)
# transients (clicks, peels, clacks) read 6-10 dB under their momentary target at the default -7 dBFS cap (the
# check render: pen_click -30.7 for -19, tape_peel -25 for -17): their caps are raised so they reach their level
PEAK_CAP.update(landline_ring=-5.0, cord_yank=-3.0, receiver_down=-4.0, receiver_up=-4.0, ticket_tear=-3.0,
                tape_peel=-2.0, match_strike=-4.0, now_serving=-6.0, card_tear=-3.0, chair_rock=-5.0, er_doors=-6.0,
                pen_click=-3.0, clipboard=-4.0, medicine_cabinet=-4.0, sit_down=-4.0)
BEDS = BEDS + ('house_night', 'fridge_hum', 'dial_tone', 'line_hiss', 'rain_house', 'halverson_car', 'streetlight',
               'waiting_room', 'tv_dead', 'drive_rain', 'er_bustle', 'office_3am')
DUR_BEDS = DUR_BEDS + ('wall_clock', 'hold_music', 'pen_scratch', 'paper_burn', 'pulse_count', 'wheelchair',
                       'typewriter', 'carry_child')
BED_BUS = BED_BUS + ('house_night', 'fridge_hum', 'dial_tone', 'line_hiss', 'rain_house', 'halverson_car',
                     'streetlight', 'waiting_room', 'tv_dead', 'drive_rain', 'er_bustle', 'office_3am', 'wall_clock',
                     'hold_music')
# spaces: 'kitchen_far' (the kitchen heard from the hall / living room), 'waiting' (the villain's waiting room: hard,
# low, fluorescent), 'er' (the bright, busy ER), 'office' (the narrator's small office at 3 AM)
SPACE_LU.update(waiting=0.0, er=0.0, office=0.0)
SPACE_ALIAS.update(waiting_room='waiting', villain='waiting', living_room_waiting='waiting', emergency='er',
                   er_bay='er', ward_er='er', night_office='office', doctors_office='office', driveway='window',
                   porch_out='outside', front_door_out='outside', car_interior='car', back_seat='car', sink='close',
                   counter='close', medicine='close', bathroom_cab='close')
SPACES = tuple(SPACE_LU)
SPACE_ALIAS.update(wait='waiting', waitingroom='waiting', bath='bathroom', clinic='hospital')   # film.py's short names
DEFAULT_SPACE.update(house_night='dry', fridge_hum='next_room', wall_clock='inside', landline_ring='close',
                     receiver_up='close', receiver_down='close', cord_yank='close', dial_tone='dry', line_hiss='dry',
                     rotary_dial='close', hold_music='dry', pen_scratch='inside', clipboard='close',
                     match_strike='close', paper_burn='close', rain_house='dry', halverson_car='window',
                     streetlight='window', waiting_room='dry', tv_dead='waiting', ticket_tear='waiting',
                     now_serving='waiting', pulse_count='dry', tape_peel='tight', medicine_cabinet='close',
                     carry_child='close', drive_rain='dry', er_doors='er', wheelchair='er', er_bustle='dry',
                     chair_rock='er', sit_down='close', office_3am='dry', phone_connect='close', typewriter='close',
                     card_tear='close', pen_click='close')


def _space_doctor(y, kind, seed=0, wet=None):
    if kind == 'waiting':                             # low ceiling, hard floor, chairs: short, bright-ish, a flutter
        x = reverb(lp(y, 9000, 1), 'hallway', 0.42 if wet is None else wet, 0.003)
        return eq(x, ('peak', 1800, 1.5, 1.0))
    if kind == 'er':                                  # a big, busy, hard room: wider, longer
        return reverb(y, 'hall', 0.28 if wet is None else wet, 0.006)
    if kind == 'office':                              # a small office: close, a little room
        return reverb(y, 'living', 0.14 if wet is None else wet, 0.002)
    return None


_space_prev = space


def space(y, kind, seed=0, wet=None):             # noqa: F811 (the doctor spaces first, then every earlier one)
    r = _space_doctor(st(y), kind, seed, wet)
    return r if r is not None else _space_prev(y, kind, seed, wet)


def _dp(key, name, keys=(), mode='onset', **seg):
    """A grain pool over the files serving `name` (those whose id has any of keys, when given)."""
    return pool('doc_' + key, lambda: (_has(name, *keys) if keys else src(name)), mode, **seg)


def _dx(name, keys, dur, rng, xfade=1.5):
    """A dur-second stretch of one of the files serving `name` (keys narrow it), looped if short."""
    E = _has(name, *keys) if keys else src(name)
    if not E:
        E = src(name)
    return excerpt(_pick(rng, E), float(dur), rng, xfade)


def _loop(y, n, rng, xf=0.9):
    """Loop a stereo array to n samples with long equal-power crossfades from random points (an idle engine, a
    hum: no seam you can hear)."""
    y = st(y); xf = min(n_(xf), len(y) // 3)
    out = np.zeros((n + len(y), 2), np.float32); i = 0
    win = np.sin(np.linspace(0, np.pi / 2, xf)) ** 2
    while i < n:
        off = int(rng.integers(0, max(1, len(y) // 3)))
        c = y[off:].copy()
        if i > 0:
            c[:xf] *= np.sqrt(win)[:, None]
        c[-xf:] *= np.sqrt(win[::-1])[:, None]
        place(out, c, i); i += len(c) - xf
    return out[:n]


def _lv(y, lufs):
    L = lufs_int(y) if len(y) > n_(0.6) else mom_max(y)
    return (y * 10 ** ((lufs - L) / 20)).astype(np.float32) if np.isfinite(L) and L > -90 else y


def r_fridge_hum(rng, sp, dur=20.0, **_):
    """BED: the kitchen fridge: the compressor's low hum (the doctor set's two fridges), its 120 Hz, a faint rattle."""
    y = lp(_dx('fridge_hum', (), dur, rng, 2.0), 1800, 2)
    return fade(y, 0.8, 1.0), 0.0, 0.0, False


def r_wall_clock(rng, sp, dur=8.0, bpm=60.0, bpm_end=None, sag=0.0, **_):
    """The kitchen wall clock. bpm_end slows it over dur (the pulse count: the clock slowing); sag (semitones) drags
    its pitch down as it slows. Ticks from the earlier sets' wall clocks, a small wooden case under each."""
    P = pool('clock_old', lambda: src('old_clock', has=['wall_clock']) or src('old_clock') or src('clock_tick'),
             'onset', gap=0.3, max_len=0.25, keep=-14)
    d = float(dur); b0 = float(bpm); b1 = float(bpm_end or bpm)
    ev = []; t = 0.0; k = 0
    while t < d:
        f = t / max(d, 1e-3)
        g = rate(P.get(rng, rj=0.0, tilt=0.0, fo=0.04, avoid=0), semis(-2.0 - (1.0 if k % 2 else 0.0) - sag * f))
        case = st(modal([260.0, 640.0, 1150.0], [0.05, 0.03, 0.015], [1.0, 0.5, 0.25], 0.15, 3 + k % 2)) * 0.3
        a = 1.0 if k % 2 == 0 else 0.72
        ev += [(t, hp(g, 250, 2) * a), (t, case * a)]
        t += 60.0 / (b0 + (b1 - b0) * f) + rng.normal(0, 0.002); k += 1
    return _seq(ev, 0.3)[:n_(d + 0.3)], 0.0, 0.0, False


def r_house_night(rng, sp, dur=30.0, fridge=0.6, clock=0.5, rain=0.0, creaks=0.3, **_):
    """BED: Grandma's house at night (the kitchen, the hall): the room's tone, the fridge's hum from the kitchen, the
    wall clock, a creak now and then, and rain on the windows when rain > 0. Calibrated as one bed."""
    d = float(dur)
    base = _lv(r_room_tone_house(rng, sp, dur=d, hum=0.25)[0], -40)
    lay = [(0, base)]
    if fridge > 0:
        fr = space(r_fridge_hum(rng, sp, dur=d)[0], 'next_room', 1)[:n_(d)]
        lay.append((0, _lv(fr, -44) * (fridge / 0.6)))
    if clock > 0:
        c = space(r_wall_clock(rng, sp, dur=d, bpm=60)[0], 'inside', 2)[:n_(d)]
        lay.append((0, _lv(c, -47) * (clock / 0.5)))
    if creaks > 0:
        try:
            cr = r_house_creaks(rng, sp, dur=d, density=0.08)[0][:n_(d)]
            lay.append((0, _lv(cr, -50) * creaks / 0.3))
        except Exception:
            pass
    if rain > 0:
        lay.append((0, _lv(r_rain_house(rng, sp, dur=d)[0], -42) * rain))
    y = _seq(lay, 0.0)[:n_(d)]
    return fade(y, 0.8, 1.2), 0.0, 0.0, False


def _gong(f, dur, rng):
    """One gong of an old telephone bell (a struck steel dome: inharmonic partials, long ring)."""
    return modal([f, f * 2.76, f * 5.40, f * 8.93], [1.4, 0.6, 0.25, 0.1], [1.0, 0.45, 0.2, 0.08], dur,
                 int(rng.integers(1 << 20)))


def _bell_burst(rng, on=2.0):
    """One ring of the old landline: the clapper hammering two gongs at ~20 Hz for `on` seconds (synthesised:
    two detuned domes) under a recorded electric bell (the doctor set's classic doorbell / its long ring) for the
    metal and the buzz, then the ring-out."""
    n = n_(on + 0.9)
    out = np.zeros((n, 2), np.float32)
    g1 = st(_gong(1180.0 + rng.uniform(-8, 8), 1.2, rng)); g2 = st(_gong(1410.0 + rng.uniform(-8, 8), 1.2, rng))
    t = 0.0; k = 0
    while t < on:
        a = 0.55 + 0.1 * rng.uniform()
        place(out, (g1 if k % 2 == 0 else g2) * a, n_(t))
        t += 1 / 20.0 + rng.normal(0, 0.0015); k += 1
    out = hp(out, 600, 2) * 0.25
    try:
        P = _dp('bell', 'landline_ring', ('classic', 'electric'), 'phrase', gap=0.3, max_len=4.0, keep=-18)
        g = P.get(rng, rj=0.0, tilt=0.0, fo=0.05)
        g = eq(lp(hp(g, 500, 2), 7000, 2), ('peak', 1300, 3.0, 1.0))
        rec = _fit(g, n_(on), rng)
        rec[-n_(0.05):] *= np.linspace(1, 0, n_(0.05))[:, None]
        place(out, pnorm(rec) * 0.8, 0)
    except KeyError:
        pass
    env = np.ones(n, np.float32); env[n_(on):] = np.exp(-np.arange(n - n_(on)) / n_(0.22 if on >= 0.4 else 0.07))   # short rings (the nine): a hand-damped ring-out
    return out * env[:, None]


def r_landline_ring(rng, sp, n=1, cycle=6.0, on=2.0, count=None, **_):
    """The old kitchen landline's bell: n rings (count= is the same), each `on` s of bell then silence, one every
    `cycle` s (the US cadence 2 on / 4 off). Each ring is its own event: cue it per ring to count them on picture,
    or give n. Rule 1: seven rings, then nine; rule 2: the unplugged phone rings anyway."""
    n = int(count or n)
    ev = [(k * float(cycle), _bell_burst(rng, float(on))) for k in range(max(1, n))]
    return _seq(ev, 0.2), 0.0, 0.0, False


def _phone_pool():
    return _dp('handset', 'receiver_up', ('telephone_pick_up', 'old_reciever', 'intercom'), 'onset', gap=0.18,
               max_len=0.6, keep=-18)


def r_receiver_up(rng, sp, **_):
    """Lifting the old receiver off its cradle: the hook switch's clack, the handset's plastic, a tiny bell tink."""
    E = _has('receiver_up', 'old_reciever_lift')
    if E:
        y = audio(_pick(rng, E)); y = fade(pnorm(y[:n_(0.5)]), 0.001, 0.05)
    else:
        y = _phone_pool().get(rng, rj=0.03)
    tink = st(_gong(1180.0, 0.4, rng)) * 0.04
    return _seq([(0, y), (0.01, tink)], 0.2), onset_s(y, -12), 0.0, False


def r_receiver_down(rng, sp, kind='hang', **_):
    """'hang': the receiver slammed onto the cradle (Grandma hangs up: the clack, the bell's jolt). 'set': laid down on
    the kitchen counter "like a sleeping baby" (a soft plastic touch on laminate, no clack)."""
    g = _phone_pool().get(rng, rj=0.03)
    if kind == 'set':
        y = lp(g, 2500, 2) * 0.35
        body = st(modal([210.0, 480.0, 950.0], [0.06, 0.04, 0.02], [1.0, 0.4, 0.15], 0.2, 5)) * 0.25
        return _seq([(0, y), (0.004, body)], 0.2), onset_s(y, -12), -6.0, False
    jolt = st(_gong(1410.0, 0.7, rng)) * 0.10
    body = st(modal([180.0, 410.0], [0.08, 0.05], [1.0, 0.5], 0.25, 6)) * 0.35
    y = _seq([(0, g), (0.003, jolt), (0.0, body)], 0.3)
    return y, onset_s(y, -12), 0.0, False


def r_cord_yank(rng, sp, **_):
    """Grandma pulls the phone cord out of the wall: the cord whipping taut (a short tear, its paper taken off), the
    plastic jack snapping out of the socket, the phone jerking on the counter (its bell's tink)."""
    T = _dp('tear', 'paper_tear', ('tear_11', 'tear_08'), 'onset', gap=0.08, max_len=0.25, keep=-14)
    whip = lp(hp(T.get(rng, rj=0.1), 600, 2), 4000, 2) * 0.45
    snap = st(modal([2800.0, 4100.0, 6900.0], [0.012, 0.008, 0.004], [1.0, 0.6, 0.3], 0.05, 9)) * 0.8
    thump = st(modal([140.0, 330.0], [0.06, 0.04], [1.0, 0.4], 0.2, 4)) * 0.5
    tink = st(_gong(1180.0, 0.5, rng)) * 0.06
    y = _seq([(0, whip), (0.11, snap), (0.13, thump), (0.135, tink)], 0.3)
    return y, onset_s(y, -12), 0.0, False         # (test 2: a fixed 0.11 s put the loud whip 77 ms early)


def r_dial_tone(rng, sp, dur=4.0, **_):
    """BED: the dial tone (350 + 440 Hz, the doctor set's recording looped), in the telephone band."""
    # synthesised: the doctor set's 1.8 s recording loops with audible seams (beating at every crossfade)
    tt = np.arange(n_(float(dur))) / SR
    y = st((np.sin(2 * np.pi * 350 * tt) + np.sin(2 * np.pi * 440 * tt)).astype(np.float32) * 0.3)
    y = y + st(bp(noise(float(dur), int(rng.integers(1 << 30))), 300, 3400, 2)[:len(tt)]) * 0.004
    return fade(bp(y, 300, 3400, 2), 0.01, 0.05), 0.0, 0.0, False


def r_line_hiss(rng, sp, dur=4.0, **_):
    """BED: an open line that has gone quiet (the outro's warning): the walkie-talkie's white noise squeezed into the
    telephone band, a faint mains hum, a crackle."""
    y = bp(_dx('line_hiss', (), dur, rng, 1.0), 300, 3400, 3)
    tt = np.arange(len(y)) / SR
    hm = st((np.sin(2 * np.pi * 60 * tt) * 0.02 + np.sin(2 * np.pi * 180 * tt) * 0.01).astype(np.float32)) * peak(y)
    return fade(y + hm, 0.05, 0.2), 0.0, 0.0, False


def r_rotary_dial(rng, sp, digits=7, **_):
    """The rotary dial turning and running back, one gesture per digit (the doctor set's old dials)."""
    P = _dp('rotary', 'rotary_dial', (), 'phrase', gap=0.25, max_len=1.6, keep=-16)
    ev = []; t = 0.0
    for k in range(int(digits)):
        g = P.get(rng, rj=0.03)
        ev.append((t, g)); t += len(g) / SR + rng.uniform(0.15, 0.35)
    return _seq(ev, 0.2), 0.0, 0.0, False


def r_hold_music(rng, sp, version='landline', dur=None, off=0.0, **kw):
    """The hold music (audio/hold.py) as a sound in the scene: version ('landline' the receiver on the counter,
    'phone_1979', 'rooms', 'ceiling', 'car_radio', 'far_hall', 'hum', 'pulse', 'studio', 'warm'); dur crops it (with
    a fade), off skips into it. Already processed: space 'dry'."""
    import hold as HM
    keys = {k: kw[k] for k in ('tempo', 'loops', 'phrases', 'transpose', 'counts', 'speeds', 'who') if k in kw}
    y, info = HM.render(str(version), seed=int(rng.integers(1, 9)), **keys)
    y = st(y)[n_(float(off)):]
    if dur:
        y = _fit(y, n_(float(dur)), None)
    return fade(y, 0.02, 0.6), 0.0, 0.0, True


def r_pen_click(rng, sp, n=1, spacing=None, **_):  # noqa: F811 (the doctor set's ballpoints first)
    """A ballpoint pen clicking (Doctor Later's pen in the dark hallway; Halverson's pen): the doctor set's ballpoint
    and retractable clicks (the clipped 'pen_ballpoint_pen_click' file excluded), n clicks."""
    P = pool('pen_doc', lambda: (_has('pen_click', 'ballpoint_pen_click', 'retractable_click', 'pen_click_open')
                                  or src('pen_click')), 'onset', gap=0.05, max_len=0.18, keep=-16)
    ev = []; t = 0.0
    for k in range(int(n)):
        a = eq(lp(hp(P.get(rng, rj=0.04), 400, 2), 7000, 2), ('hs', 4500, -4.0, 0.7))
        body = st(modal([1250.0, 2100.0, 3300.0], [0.012, 0.008, 0.005], [1.0, 0.6, 0.3], 0.04, 11)) * 0.45
        ev += [(t, a), (t, body)]
        t += float(spacing) if spacing else rng.uniform(0.3, 0.45)
    y = _seq(ev, 0.05)
    y = sat(y / (peak(y) + 1e-9), 3.0) * 0.5          # shave the 5 ms spike so the click reaches its level
    return y, onset_s(y, -12), 0.0, False


def r_pen_scratch(rng, sp, dur=2.5, **_):
    """A pen scratching on paper (something in the hallway writing down what Milo said; Halverson's marker note):
    the doctor set's ballpoint writing on paper, its brightest air taken off."""
    E = _has('pen_scratch', 'write_on_paper') or src('pen_scratch')
    y = excerpt(_pick(rng, E), float(dur), rng, 0.3)
    y = eq(lp(hp(y, 250, 2), 7000, 2), ('peak', 1800, 2.0, 1.0))
    return fade(y, 0.05, 0.15), 0.0, 0.0, False


def r_clipboard(rng, sp, **_):
    """The clipboard's metal clip snapping (the doctor set's crocodile clip, a bigger spring: 3 semitones down) on a
    hardboard (its body thump)."""
    P = _dp('clip', 'clipboard', (), 'onset', gap=0.06, max_len=0.2, keep=-14)
    g = lp(rate(P.get(rng, rj=0.03), semis(-3.0)), 8000, 2)
    board = st(modal([190.0, 430.0, 910.0], [0.05, 0.03, 0.015], [1.0, 0.5, 0.2], 0.15, 8)) * 0.4
    y = _seq([(0, g), (0.002, board)], 0.1)
    return y, onset_s(y, -12), 0.0, False


def r_match_strike(rng, sp, **_):
    """Grandma strikes a match over the sink: the scrape on the box (the doctor set's match strikes), the flare
    catching (a soft burst of air), a little sputter."""
    P = _dp('match', 'match_strike', ('match_strike', 'strike_box'), 'phrase', gap=0.25, max_len=1.4, keep=-18)
    g = lp(P.get(rng, rj=0.02), 11000, 2)
    fl = st(lp(noise(0.6, int(rng.integers(1 << 30))), 1800, 2)) * np.exp(-np.arange(n_(0.6)) / n_(0.15))[:, None]
    y = _seq([(0, g), (len(g) / SR * 0.55, fl * 0.08 * peak(g) / (peak(fl) + 1e-9))], 0.3)
    return y, onset_s(y, -14), 0.0, False


def r_paper_burn(rng, sp, dur=6.0, **_):
    """The folded results burning in the sink: the paper catching and crackling (the doctor set's small pile of paper
    burning indoors), close, its low rumble kept small."""
    y = _dx('paper_burn', (), dur, rng, 1.0)
    y = eq(hp(y, 120, 2), ('peak', 2500, 2.0, 1.0))
    ramp = np.clip(np.arange(len(y)) / n_(0.8), 0, 1) ** 1.5
    return fade(y * ramp[:, None].astype(np.float32), 0.02, 0.8), 0.0, 0.0, False


def r_rain_house(rng, sp, dur=30.0, heavy=0.6, **_):
    """BED: rain outside Grandma's house, heard inside: steady rain on the roof (the doctor set's rain on a car roof
    and on a windshield, darkened to the house's walls and glass), drips at the window now and then."""
    a = _dx('rain_car', ('car_on_roof',), dur, rng, 2.0)
    b = _dx('rain_car', ('windshield',), dur, rng, 2.0)
    y = lp(a, 2600, 2) * 0.8 + lp(hp(b, 300, 2), 5000, 2) * 0.35 * (0.5 + heavy)
    return fade(width(y, 1.2), 1.2, 1.5), 0.0, 0.0, False


def r_halverson_car(rng, sp, dur=30.0, start=False, rain=0.5, **_):
    """BED: Doctor Halverson's car in the driveway, engine running, rain on its roof: the doctor set's car idling
    (its idle looped; start=True plays the start at the head), outside."""
    E = src('halverson_car')
    if not E:
        return r_car_idle(rng, sp, dur=dur)
    x = audio(_pick(rng, E, 1.0))
    idle = x[n_(1.6):]
    y = _loop(idle, n_(float(dur)), rng, 0.9)
    if start:
        y = np.concatenate([fade(x[:n_(1.6)], 0.002, 0.02), y])[:n_(float(dur))]
    y = lp(y, 3500, 2)
    if rain > 0:
        y = y + _lv(lp(_dx('rain_car', ('car_on_roof',), dur, rng, 2.0), 3500, 2), lufs_int(y) - 6) * rain
    return fade(y, 0.4, 1.0), 0.0, 0.0, False


def r_streetlight(rng, sp, dur=20.0, flicker=0.6, **_):
    """BED: the flickering streetlight at the bus stop: an electric buzz (the doctor set's interference buzz) that
    stutters with the lamp, the starter's ticks on each flicker."""
    d = float(dur)
    y = hp(_dx('fluorescent', ('interference',), d, rng, 1.0), 90, 2)
    n = len(y); tt = np.arange(n) / SR
    g = np.ones(n, np.float32); ev = []
    t = rng.uniform(0.5, 2.0)
    while t < d - 0.5:
        k = int(rng.integers(2, 6))
        for j in range(k):
            a = n_(t + j * 0.07); b = min(n, a + n_(rng.uniform(0.02, 0.05)))
            g[a:b] *= 0.15
            ev.append((t + j * 0.07, st(modal([3100.0, 5200.0], [0.004, 0.003], [1.0, 0.5], 0.02, j)) * 0.05))
        t += rng.uniform(1.5, 5.0) / max(flicker, 0.1)
    from scipy.ndimage import uniform_filter1d
    g = uniform_filter1d(g, n_(0.006))
    y = y * g[:, None]
    tick = _seq(ev, 0.0) if ev else np.zeros((1, 2), np.float32)
    out = np.zeros_like(y); out += y; out[:min(n, len(tick))] += tick[:n] * peak(y) * 3
    return fade(out, 0.5, 0.8), 0.0, 0.0, False


def _ballast(d, rng, flicker=0.4):
    """Fluorescent tubes: 120 Hz ballast hum with its odd harmonics, a little beating between two tubes, and (with
    flicker) a half-dead tube's stutter (the hum dips and ticks)."""
    n = n_(d); tt = np.arange(n) / SR
    h = sum(a * np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) for f, a in ((120, 1.0), (240, 0.35), (360, 0.3),
                                                                             (600, 0.12), (1080, 0.05)))
    h2 = sum(a * np.sin(2 * np.pi * f * 1.004 * tt) for f, a in ((120, 0.6), (360, 0.2)))
    y = (h + h2).astype(np.float32)
    if flicker > 0:
        g = np.ones(n, np.float32); t = rng.uniform(0.5, 2.0)
        while t < d - 0.3:
            for j in range(int(rng.integers(1, 4))):
                a = n_(t + j * 0.09); g[a:a + n_(0.03)] *= 0.3
            t += rng.uniform(2.0, 6.0) / flicker
        from scipy.ndimage import uniform_filter1d
        y = y * uniform_filter1d(g, n_(0.005))
    return y


def r_waiting_room(rng, sp, dur=30.0, flicker=0.5, tv=0.0, buzz=0.6, **_):
    """BED: the living room that has become a waiting room (the villain's world): the fluorescent tubes' ballast hum,
    half of them dying (stutters), the recorded electric buzz under it, the dead air of a room full of people who do
    not move (no walla), and the dead TV's hiss when tv > 0. Sickly, low, still."""
    d = float(dur)
    bal = st(_ballast(d, rng, flicker))
    bz = hp(_dx('fluorescent', ('buzz_hum_buzz_hum',), d, rng, 1.0), 80, 2)
    air = st(lp(noise(d, int(rng.integers(1 << 30))), 300, 2))
    lay = [(0, _lv(bal, -40)), (0, _lv(bz, -46) * buzz / 0.6), (0, _lv(air, -50))]
    if tv > 0:
        lay.append((0, _lv(r_tv_dead(rng, sp, dur=d)[0], -46) * tv))
    y = reverb(_seq(lay, 0.0)[:n_(d)], 'hallway', 0.35)[:n_(d)]
    return fade(width(y, 0.8), 1.0, 1.0), 0.0, 0.0, False


def r_tv_dead(rng, sp, dur=10.0, **_):
    """BED: a television on the wall showing nothing: the snow's hiss (soft, darkened), the tube's faint 15.7 kHz
    whine kept very low, a 60 Hz hum."""
    d = float(dur); n = n_(d); tt = np.arange(n) / SR
    z = lp(hp(noise(d, int(rng.integers(1 << 30))), 400, 2), 6500, 2)
    wh = (np.sin(2 * np.pi * 15734 * tt) * 0.004 + np.sin(2 * np.pi * 60 * tt) * 0.02).astype(np.float32)
    y = st(z * 0.3 + wh)
    return fade(y, 0.3, 0.5), 0.0, 0.0, False


def r_ticket_tear(rng, sp, **_):
    """A ticket torn off the take-a-number machine: the dispenser's ratchet click, the perforated paper tearing (the
    doctor set's cinema ticket)."""
    P = _dp('ticket', 'ticket_tear', (), 'onset', gap=0.08, max_len=0.4, keep=-16)
    g = P.get(rng, rj=0.03)
    ratchet = st(modal([1400.0, 2600.0, 4300.0], [0.01, 0.006, 0.004], [1.0, 0.5, 0.3], 0.04, 12)) * 0.25
    y = _seq([(0, ratchet), (0.06, g)], 0.2)
    return y, 0.06, 0.0, False


def r_card_tear(rng, sp, **_):
    """The narrator tears the yellow card out of the medicine cabinet: old tape letting go, card stock ripping."""
    T = _dp('cardtear', 'paper_tear', ('paper_bag', 'tear_08'), 'phrase', gap=0.15, max_len=0.9, keep=-16)
    Pp = _dp('peel', 'tape_peel', ('masking_tape_peel_off', 'sticky_tape_peel_off'), 'onset', gap=0.1, max_len=0.6,
             keep=-16)
    y = _seq([(0, Pp.get(rng, rj=0.05) * 0.6), (0.12, lp(T.get(rng, rj=0.04), 9000, 2))], 0.2)
    return y, 0.12, 0.0, False


def r_now_serving(rng, sp, sour=0.0, **_):
    """The NOW SERVING sign's ding: a two-note electronic chime (the doctor set's ting, pitched to G6 then E6);
    sour (0..1) drags the second note down toward a tritone and slows it (the sign frozen on 1979)."""
    P = _dp('ting', 'now_serving', ('high_tings',), 'onset', gap=0.15, max_len=0.6, keep=-20)
    g = P.get(rng, rj=0.0, tilt=0.0)
    f0 = 2793.0
    a = rate(g, 1567.98 / f0)
    b = rate(g, (1318.5 * 2 ** (-3.0 * sour / 12)) / f0 * (1 - 0.15 * sour))
    y = _seq([(0, a), (0.42 + 0.2 * sour, b * 0.85)], 0.6)
    return reverb(lp(y, 7000, 2), 'living', 0.15), 0.0, 0.0, False


def r_pulse_count(rng, sp, dur=14.0, counts=(0.0, 4.5, 9.0), bpm=(64, 50, 38, 28), clock=0.7, **_):
    """The pulse count (rule 7): he takes the narrator's wrist and counts. A heartbeat felt through the wrist (low,
    close) that steps slower at each count (counts: seconds from the start, bpm: the rate before / after each), the
    kitchen clock slowing with it (its pitch sagging). Cue it on "One..." with counts at "One", "Two", "Three"."""
    d = float(dur); counts = list(counts); bpm = list(bpm)
    P = pool('heart', lambda: src('heartbeat'), 'onset', gap=0.12, max_len=0.35, keep=-16)

    def rate_at(t):
        k = sum(1 for c in counts[1:] if t >= c)
        return bpm[min(k, len(bpm) - 1)] * (1 - 0.0 * t)
    ev = []; t = 0.0
    while t < d:
        per = 60.0 / rate_at(t)
        lub = lp(P.get(rng, rj=0.02, tilt=0.5, fo=0.04), 700, 2)
        sub = st(sub_boom(58, 40, 0.25, 0.0)) * 0.7
        ev += [(t, lub), (t, sub), (t + 0.3 * per ** 0.5, lp(P.get(rng, rj=0.02, fo=0.04), 900, 2) * 0.5)]
        t += per
    y = _seq(ev, 0.4)[:n_(d + 0.4)]
    if clock > 0:
        c = r_wall_clock(rng, sp, dur=d, bpm=60.0, bpm_end=24.0, sag=4.0)[0]
        y = _seq([(0, y), (0, reverb(c, 'hallway', 0.35)[:len(y)] * clock * peak(y) / (peak(c) + 1e-9) * 0.35)], 0.0)
    return y, 0.0, 0.0, False


def r_tape_peel(rng, sp, q=1, **_):
    """One question, one strip: old yellow tape peeling off his head (the doctor set's masking tape peeling, its long
    strip ripping). q = 1..4, the question's number: each strip longer, slower to start, louder at the end."""
    q = int(max(1, min(4, q)))
    P = _dp('peelp', 'tape_peel', ('masking_tape', 'sticky_tape_rip_from_roll_long'), 'phrase', gap=0.2,
            max_len=1.2, keep=-18)
    ev = []; t = 0.0
    for k in range(1 + q):                            # the strip comes away in 2..5 pulls, each a little lower
        g = lp(hp(rate(P.get(rng, rj=0.03), semis(-1.5 - 0.5 * q - 0.4 * k)), 200, 2), 9000, 2)
        ev.append((t, g * (0.7 + 0.3 * k / max(1, q))))
        t += len(g) / SR * rng.uniform(0.55, 0.8)
    y = _seq(ev, 0.1)
    return fade(y, 0.01, 0.06), onset_s(y, -16), 0.0, False


def r_medicine_cabinet(rng, sp, action='open', **_):
    """The medicine cabinet's mirror door swinging aside ('open') or shut ('close'): the hinge and the catch (the
    doctor set's kitchen cabinet), the mirror's glass and the bottles inside rattling (its medicine cabinet)."""
    C = _dp('cab', 'kitchen_cabinet', (), 'onset', gap=0.15, max_len=0.6, keep=-18)
    G = _dp('medcab', 'medicine_cabinet', (), 'onset', gap=0.12, max_len=0.4, keep=-14)
    h = C.get(rng, rj=0.04)
    glass = hp(G.get(rng, rj=0.05), 900, 2) * 0.35
    ring = st(modal([2250.0, 3720.0, 5600.0], [0.18, 0.1, 0.05], [1.0, 0.5, 0.2], 0.4, 13)) * 0.04
    lay = [(0, h), (0.02, glass), (0.01, ring)] if action == 'open' else [(0, h * 1.1), (0.0, glass), (0.0, ring)]
    y = _seq(lay, 0.3)
    return y, onset_s(y, -12), 0.0, False


def r_carry_child(rng, sp, dur=3.0, **_):
    """The narrator lifts Milo and carries him (cloth, quick steps on the hall boards, a strained breath)."""
    d = float(dur)
    cl = r_cloth_rustle(rng, sp, dur=d)[0]
    fs = r_footsteps_hall(rng, sp, dur=d, rate=2.2, weight=0.7)[0]
    br = r_breath(rng, sp, kind='nervous', dur=min(d, 3.0))[0]
    y = _seq([(0, _lv(cl, -30)), (0.3, _lv(fs, -28)), (0.1, _lv(br, -34))], 0.2)[:n_(d + 0.2)]
    return fade(y, 0.05, 0.3), 0.0, 0.0, False


def _wipers(d, rng, period=1.1):
    ev = []; t = 0.2
    while t < d:
        sw = lp(hp(noise(0.35, int(rng.integers(1 << 30))), 400, 2), 2500, 2)
        sw = st(sw * np.sin(np.linspace(0, np.pi, len(sw))) ** 2) * 0.05
        th = st(modal([95.0, 210.0], [0.05, 0.03], [1.0, 0.4], 0.12, int(t * 10))) * 0.25
        ev += [(t, sw), (t + 0.36, th)]
        t += period
    return _seq(ev, 0.2)


def r_drive_rain(rng, sp, dur=30.0, speed='fast', wipers=True, **_):
    """BED: inside Halverson's car, driving fast at night in the rain: the doctor set's interior night drive (road
    and engine), rain on the roof and on the windshield, the wipers' sweep and thunk."""
    d = float(dur)
    road = _dx('drive_rain', ('fast_driving',) if speed == 'fast' else ('driving_steady',), d, rng, 2.0)
    roof = _dx('rain_car', ('car_on_roof',), d, rng, 2.0)
    wind = _dx('rain_car', ('windshield',), d, rng, 2.0)
    lay = [(0, _lv(road, -30)), (0, _lv(lp(roof, 6000, 2), -35)), (0, _lv(wind, -38))]
    if wipers:
        lay.append((0, _lv(_wipers(d, rng), -40)))
    y = _seq(lay, 0.0)[:n_(d)]
    return fade(y, 0.8, 1.2), 0.0, 0.0, False


def r_er_doors(rng, sp, **_):
    """The ER's automatic glass doors sliding open before they reach them (the doctor set's automatic doors)."""
    E = src('er_doors')
    if not E:
        return r_van_door_slide(rng, sp)
    x = audio(_pick(rng, E, 1.0))
    y = fade(x[:n_(3.2)], 0.01, 0.4)
    return y, 0.0, 0.0, False


def r_wheelchair(rng, sp, dur=3.0, **_):
    """Mom running with a wheelchair: its wheels on the hospital floor (the doctor set's empty wheelchair passes),
    lifted (it was recorded quiet)."""
    y = hp(_dx('wheelchair', ('empty_chair',), dur, rng, 0.5), 70, 2)
    return fade(y, 0.1, 0.4), 0.0, 0.0, False


def r_er_bustle(rng, sp, dur=30.0, monitors=0.6, gurney=0.4, warm=1.0, **_):
    """BED: the ER, warm and alive: a waiting room with people talking softly (the doctor set's hospital waiting
    room and its walla, kept far and low so no word reads), heart monitors beeping steadily, a gurney now and then.
    Nobody is waiting here: it moves."""
    d = float(dur)
    a = lp(_dx('waiting_room', ('hospital_waiting',), d, rng, 2.0), 5000, 2)
    b = lp(_dx('waiting_room', ('walla',), d, rng, 2.0), 3000, 2)
    lay = [(0, _lv(a, -36)), (0, _lv(b, -40) * warm)]
    if monitors > 0:
        m = _dx('heart_monitor_er', ('steady_distant',), d, rng, 1.0)
        lay.append((0, _lv(m, -42) * monitors / 0.6))
    if gurney > 0:
        g = _dx('gurney', ('approach', 'away', 'turning'), min(d, 8.0), rng, 0.5)
        lay.append((rng.uniform(0, max(0.1, d - 8.0)), _lv(g, -40) * gurney / 0.4))
    y = reverb(_seq(lay, 0.0)[:n_(d)], 'hall', 0.15)[:n_(d)]
    return fade(width(y, 1.1), 1.0, 1.5), 0.0, 0.0, False


def r_chair_rock(rng, sp, dur=3.5, **_):
    """The empty plastic chair next to his, still rocking a little: its legs tapping the tile, slower and softer,
    a faint dry creak on the swing."""
    d = float(dur); ev = []; t = 0.0; k = 0; per = 0.42
    Cr = _dp('creak', 'chair_creak', ('short_dry',), 'onset', gap=0.15, max_len=0.4, keep=-18)
    while t < d:
        a = np.exp(-t / (d * 0.45))
        foot = st(modal([340.0, 910.0, 1750.0], [0.04, 0.025, 0.012], [1.0, 0.5, 0.25], 0.12, k)) * 0.5 * a
        ev.append((t, foot))
        if k % 2 == 0:
            ev.append((t + 0.05, lp(Cr.get(rng, rj=0.05), 4000, 2) * 0.12 * a))
        t += per; per *= 1.06; k += 1
    return _seq(ev, 0.3), 0.0, 0.0, False


def r_sit_down(rng, sp, kind='plastic', **_):
    """Someone sitting down: 'plastic' (a bolted plastic waiting-room chair: the office-chair sit, its padding
    thinned, a plastic creak), 'armchair' (Grandpa's chair: the sofa springs), 'office'."""
    if kind == 'armchair':
        E = _has('sit_down', 'sofa') or src('sit_down')
    else:
        E = _has('sit_down', 'office_chair') or src('sit_down')
    y = fade(pnorm(audio(_pick(rng, E))), 0.005, 0.2)
    if kind == 'plastic':
        y = hp(y, 180, 2)
        y = _seq([(0, y), (0.08, st(modal([620.0, 1450.0], [0.05, 0.03], [1.0, 0.4], 0.12, 3)) * 0.2)], 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_office_3am(rng, sp, dur=30.0, **_):
    """BED: the narrator's office at 3 AM (Larkfield General): the building's ventilation and the lamp's faint buzz
    (hospital_tone), a heart monitor far down the hall."""
    d = float(dur)
    a = r_hospital_tone(rng, sp, dur=d)[0]
    lay = [(0, _lv(a, -40))]
    E = _has('heart_monitor_er', 'steady_distant')
    if E:
        m = lp(excerpt(_pick(rng, E), d, rng, 1.0), 2500, 2)
        lay.append((0, _lv(reverb(m, 'hall', 0.6)[:len(m)], -50)))
    return fade(_seq(lay, 0.0)[:n_(d)], 1.0, 1.0), 0.0, 0.0, False


def r_phone_connect(rng, sp, **_):
    """The outro's phone that connects instantly: three quick keypad tones (the doctor set's speed-dial tones), one
    ring-back purr, the pick-up click."""
    E = _has('phone_connect', 'speed_dial')
    lay = []
    if E:
        lay.append((0, lp(audio(_pick(rng, E))[:n_(1.0)], 4000, 2)))
    tt = np.arange(n_(0.6)) / SR
    rb = st(((np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * 0.15).astype(np.float32))
    rb = fade(bp(rb, 300, 3400, 2), 0.02, 0.05)
    lay.append((1.1, rb))
    lay.append((1.9, _phone_pool().get(rng, rj=0.03) * 0.6))
    return _seq(lay, 0.2), 0.0, 0.0, False


def r_typewriter(rng, sp, dur=3.0, **_):
    """Typing on an old typewriter (the rules, typed on a typewriter, paper the colour of weak tea)."""
    y = _dx('typewriter', ('hermes',), dur, rng, 0.3)
    return fade(lp(y, 9000, 2), 0.02, 0.2), 0.0, 0.0, False


ALIASES = {
    'ding_dong': ('doorbell_dingdong', {}), 'doorbell': ('doorbell_dingdong', {}), 'doorbell_ring': ('doorbell_dingdong', {}),
    'doorbell_ding_dong': ('doorbell_dingdong', {}), 'house_chime': ('doorbell_dingdong', {}),
    'doorbell_cam': ('doorbell_cam_chime', {}), 'cam_chime': ('doorbell_cam_chime', {}),
    'app_chime': ('doorbell_cam_chime', {}), 'doorbell_app': ('doorbell_cam_chime', {}),
    'doorbell_camera_chime': ('doorbell_cam_chime', {}),
    'notification': ('phone_notify', {}), 'notify': ('phone_notify', {}), 'app_notify': ('phone_notify', {}),
    'text_notify': ('phone_notify', {'kind': 'text'}), 'phone_notification': ('phone_notify', {}),
    'box_thump': ('box_knock', {}), 'knock_box': ('box_knock', {}), 'box_knocks': ('box_knock', {'pattern': [2, 1]}),
    'box_knock_pattern': ('box_knock', {'pattern': [2, 1]}), 'dad_knock': ('box_knock', {'pattern': [2, 1]}),
    'box_drag': ('box_scrape', {}), 'box_slide': ('box_scrape', {}), 'box_set_down': ('box_drop', {}),
    'box_flaps': ('box_open', {}), 'box_cut': ('tape_rip', {'kind': 'cut'}),
    'tape': ('tape_rip', {}), 'tape_cut': ('tape_rip', {'kind': 'cut'}), 'tape_peel': ('tape_rip', {'kind': 'peel'}),
    'hazard': ('hazard_ticks', {}), 'hazards': ('hazard_ticks', {}), 'hazard_lights': ('hazard_ticks', {}),
    'indicator': ('hazard_ticks', {}), 'hazard_bed': ('hazard_ticks', {}),
    'text_notification': ('phone_notify', {}), 'app_notification': ('phone_notify', {}),
    'window_check': ('window_latch', {}), 'latch': ('window_latch', {}),
    'van_door': ('van_door_slide', {}), 'sliding_door': ('van_door_slide', {}),
    'van_door_open': ('van_door_slide', {'action': 'open'}), 'van_door_close': ('van_door_slide', {'action': 'close'}),
    'van_drive_away': ('van_pull_away', {}), 'van_leave': ('van_pull_away', {}), 'van_depart': ('van_pull_away', {}),
    'van_drive_off': ('van_pull_away', {}), 'van_engine': ('van_idle', {}),
    'keys_bowl': ('keys_drop', {'surface': 'bowl'}), 'keys': ('keys_drop', {}), 'bowl': ('keys_drop', {'surface': 'bowl'}),
    'window_open': ('window_slide', {'action': 'open'}), 'window_close': ('window_slide', {'action': 'close'}),
    'window': ('window_slide', {}), 'curtain': ('curtain_flutter', {}), 'curtains': ('curtain_flutter', {}),
    'tablet_tap': ('touch_tap', {}), 'screen_tap': ('touch_tap', {}), 'tap': ('touch_tap', {}),
    'stylus': ('stylus_scribble', {}), 'stylus_squeak': ('stylus_scribble', {}), 'stylus_sign': ('stylus_scribble', {}),
    'signature': ('stylus_scribble', {}), 'sign': ('stylus_scribble', {}),
    'shutter': ('camera_shutter', {}), 'photo': ('camera_shutter', {}), 'delivery_photo': ('camera_shutter', {}),
    'footsteps': ('footsteps_porch', {}), 'stairs': ('footsteps_stairs', {}), 'footsteps_hallway': ('footsteps_hall', {}),
    'footsteps_upstairs': ('footsteps_stairs', {'direction': 'up'}),
    'sob': ('mom_sob', {}), 'cry': ('mom_sob', {}), 'mom_cry': ('mom_sob', {}), 'gasp': ('breath', {'kind': 'gasp'}),
    'mom_gasp': ('mom_breath', {'kind': 'gasp'}), 'sniff': ('mom_breath', {'kind': 'sniff'}),
    'ambience_suburban': ('ambience_suburb', {}), 'suburb': ('ambience_suburb', {}), 'dawn': ('ambience_dawn', {}),
    'birds': ('ambience_dawn', {}), 'sunrise': ('ambience_dawn', {}), 'house_tone': ('room_tone_house', {}),
    'room_tone_inside': ('room_tone_house', {}),
    'eye_flash': ('stinger', {'kind': 'eye_flash'}), 'knock': ('knock_door', {}), 'hit': ('impact_hit', {}),
    'boom': ('impact_hit', {}), 'drop': ('sub_drop', {}), 'rattle': ('chain_lock', {'kind': 'rattle'}),
    'grab': ('cloth_rustle', {'kind': 'grab'}), 'car_door': ('car_door_close', {}),
    # ---- dummy film
    'clack': ('dummy_clack', {}), 'jaw_clack': ('dummy_clack', {}), 'jaw_snap': ('dummy_clack', {}),
    'speech_clack': ('dummy_clack', {'kind': 'speech'}), 'jaw_drop': ('dummy_jaw', {}), 'jaw_open': ('dummy_jaw', {}),
    'eyelid': ('eyelid_click', {}), 'wink': ('eyelid_click', {'kind': 'shut'}), 'wink_click': ('eyelid_click', {}),
    'blink': ('eyelid_click', {}), 'click_click': ('eyelid_click', {}), 'head_turn': ('wood_creak', {'kind': 'grind'}),
    'head_creak': ('wood_creak', {'kind': 'grind'}), 'neck_creak': ('wood_creak', {'kind': 'grind'}),
    'joint_creak': ('wood_creak', {'kind': 'tick'}), 'wood_tick': ('wood_creak', {'kind': 'tick'}),
    'dummy_knock': ('wood_knock', {}), 'body_knock': ('wood_knock', {}), 'dummy_steps': ('tiny_steps', {}),
    'little_steps': ('tiny_steps', {}), 'tiny_footsteps': ('tiny_steps', {}), 'glove': ('glove_lift', {}),
    'hand_inside': ('hand_slot', {}), 'slot': ('hand_slot', {}), 'squeeze': ('hand_squeeze', {}),
    'squeezes': ('hand_squeeze', {}), 'latch_pop': ('case_latch', {}), 'case_latches': ('case_latch', {}),
    'case_open': ('case_lid', {'action': 'open'}), 'case_close': ('case_lid', {'action': 'close'}),
    'lid': ('case_lid', {}), 'spoon': ('spoon_stir', {}), 'stir': ('spoon_stir', {}), 'coffee_stir': ('spoon_stir', {}),
    'clink': ('spoon_clink', {}), 'clinks': ('spoon_clink', {'n': 3}), 'mug': ('mug_set', {}), 'mug_down': ('mug_set', {}),
    'mug_pickup': ('mug_set', {'kind': 'pickup'}), 'cup': ('mug_set', {}), 'drink': ('sip', {}), 'slurp': ('sip', {}),
    'thud': ('dummy_thud', {}), 'rug_thud': ('dummy_thud', {'kind': 'rug'}), 'fall': ('dummy_thud', {}),
    'tv': ('tv_on', {}), 'tv_power': ('tv_on', {}), 'television_on': ('tv_on', {}), 'crt_on': ('tv_on', {}),
    'vhs': ('vcr', {}), 'vcr_play': ('vcr', {'action': 'play'}), 'tape_play': ('vcr', {'action': 'play'}),
    'rewind': ('vcr', {'action': 'rewind'}), 'tape_noise': ('tape_hiss', {}), 'hiss': ('tape_hiss', {}),
    'laugh_track': ('studio_laugh', {}), 'laughter': ('studio_laugh', {}), 'audience_laugh': ('studio_laugh', {}),
    'studio_laughter': ('studio_laugh', {}), 'laugh_wave': ('studio_laugh', {'size': 'huge'}),
    'audience_roar': ('studio_laugh', {'size': 'huge'}), 'clapping': ('applause', {}), 'flicker': ('lamp_flicker', {}),
    'lamp': ('lamp_flicker', {}), 'lights_out': ('lamp_out', {}), 'lamp_on': ('lamp_out', {'kind': 'on'}),
    'flashlight': ('flashlight_click', {}), 'torch': ('flashlight_click', {}), 'torch_click': ('flashlight_click', {}),
    'flashlight_on': ('flashlight_click', {'kind': 'on'}), 'flashlight_off': ('flashlight_click', {'kind': 'off'}),
    'monitor': ('heart_monitor', {}), 'heart_beeps': ('heart_monitor', {}), 'ecg': ('heart_monitor', {}),
    'flatline': ('monitor_flatline', {}), 'scream': ('mom_scream', {}), 'shriek': ('owen_cry', {'kind': 'shriek'}),
    'owen_shriek': ('owen_cry', {'kind': 'shriek'}), 'giggle': ('owen_giggle', {}), 'owen_laugh': ('owen_giggle', {}),
    'owen_snort': ('snort', {}), 'dummy_laugh': ('winks_laugh', {}), 'goodnight': ('goodnight_hit', {}),
    'clock': ('old_clock', {}), 'grandfather_clock': ('old_clock', {}), 'hospital': ('hospital_tone', {}),
    'museum': ('museum_tone', {}), 'creaks': ('house_creaks', {}), 'house_settle': ('house_creaks', {}),
    'tape_stop': ('tape_glitch', {'kind': 'stop'}), 'tracking': ('tape_glitch', {'kind': 'tracking'}),
    'keys_grab': ('keys_jangle', {}), 'p_s': ('paper_slide', {}), 'ps_slide': ('paper_slide', {}),
    'van_arrive': ('car_pass', {'kind': 'arrive'}), 'museum_van': ('car_pass', {'kind': 'arrive'}),
    'van_away': ('van_pull_away', {}), 'van_doors': ('car_door_close', {}),
    # film.py's names (the director's cue sheets)
    'studio_laughter': ('studio_laugh', {}), 'kid_laugh': ('owen_giggle', {}), 'tv_bed': ('tape_hiss', {}),
    'tv_static': ('tape_glitch', {'kind': 'tracking'}), 'light_switch': ('lamp_out', {'kind': 'switch'}),
    'bulb_buzz': ('lamp_flicker', {'kind': 'buzz'}), 'bulb_flicker': ('lamp_flicker', {}),
    'ambience_morning': ('ambience_dawn', {}), 'chime': ('clock_chime', {}), 'tape_voice': ('tv_voice', {}),
    'lie_card': ('rule_lie', {}),
    # ---- the Bunnyman film
    'woods': ('ambience_woods', {}), 'night_woods': ('ambience_woods', {}), 'woods_night': ('ambience_woods', {}),
    'ambience_forest': ('ambience_woods', {}), 'treeline': ('ambience_woods', {}), 'owl': ('owl_hoot', {}),
    'parade': ('crowd_parade', {}), 'parade_crowd': ('crowd_parade', {}), 'cheering': ('crowd_parade', {}),
    'kids_cheering': ('crowd_parade', {}), 'hospital_hall': ('hospital_corridor', {}),
    'corridor': ('hospital_corridor', {}), 'ward_room': ('hospital_room', {}), 'visiting_room': ('hospital_room', {}),
    'fire': ('burn_barrel', {}), 'barrel': ('burn_barrel', {}), 'burn': ('burn_barrel', {}),
    'barrel_ignite': ('burn_barrel', {'ignite': True}), 'melt': ('plastic_melt', {}), 'egg_melt': ('plastic_melt', {}),
    'egg_knock': ('egg_tap', {}), 'soft_tap': ('egg_tap', {}), 'egg': ('egg_set', {}), 'egg_down': ('egg_set', {}),
    'egg_shake': ('egg_rattle', {}), 'rattle_egg': ('egg_rattle', {}), 'egg_pop': ('egg_open', {}),
    'open_egg': ('egg_open', {}), 'ring': ('ring_drop', {}), 'ring_rolling': ('ring_roll', {}),
    'ring_take': ('ring_hand', {}), 'pocket': ('ring_hand', {'kind': 'pocket'}), 'mitts': ('oven_mitt', {}),
    'oven_mitts': ('oven_mitt', {}), 'family_knock': ('knock_family', {}), 'secret_knock': ('knock_family', {}),
    'knock_232': ('knock_family', {}), 'grandma_knock': ('knock_family', {'soft': True}),
    'mail_flap': ('slot_flap', {}), 'brass_flap': ('slot_flap', {}), 'letterbox': ('slot_flap', {}),
    'mail_slot_open': ('slot_flap', {'action': 'open'}), 'mail_slot_close': ('slot_flap', {'action': 'close'}),
    'mail_slot_snap': ('slot_flap', {'action': 'snap'}), 'crying': ('girl_cry', {}), 'girl_crying': ('girl_cry', {}),
    'child_cry': ('girl_cry', {}), 'laurie_cry': ('girl_cry', {}), 'song': ('jingle', {}),
    'pembertons': ('jingle', {}), 'jingle_speaker': ('jingle', {'version': 'speaker'}),
    'jingle_vhs': ('jingle', {'version': 'vhs'}), 'hum': ('jingle', {'version': 'hum'}),
    'mom_hum': ('jingle', {'version': 'hum'}), 'music_box': ('jingle', {'version': 'musicbox'}),
    'attic': ('attic_door', {}), 'bulb_chain': ('bulb', {'kind': 'chain'}), 'pull_chain': ('bulb', {'kind': 'chain'}),
    'bulb_hum': ('bulb', {'kind': 'buzz'}), 'chest': ('chest_lid', {}), 'toy_chest': ('chest_lid', {}),
    'page': ('page_flip', {}), 'pages': ('page_flip', {'n': 3}), 'diary_pages': ('page_flip', {'n': 4}),
    'lock_diary': ('diary_lock', {}), 'window_break': ('window_smash', {}), 'glass_break': ('window_smash', {}),
    'smash': ('window_smash', {}), 'kick_in': ('door_crash', {}), 'back_door': ('door_crash', {}),
    'drag': ('wet_drag', {}), 'dragging': ('wet_drag', {}), 'hatchet': ('hatchet_step', {}),
    'thunk': ('hatchet_step', {'n': 1}), 'knob': ('doorknob', {}), 'knob_turn': ('doorknob', {'kind': 'turn'}),
    'drawing_slide': ('paper_under_door', {}), 'paper_slide_door': ('paper_under_door', {}),
    'fight': ('struggle', {}), 'slam': ('struggle', {'kind': 'slam'}), 'door_slam_body': ('struggle', {'kind': 'slam'}),
    'crack': ('struggle', {'kind': 'crack'}), 'bone': ('struggle', {'kind': 'crack'}),
    'hall_shake': ('struggle', {'kind': 'shake'}), 'key_turn_outside': ('key_outside', {}),
    'sirens': ('sirens_arrive', {}), 'police_arrive': ('sirens_arrive', {}), 'pause': ('vhs_pause', {}),
    'vhs_play': ('vhs_pause', {'kind': 'play'}), 'switch': ('light_switch', {}),
    'porch_light': ('light_switch', {'kind': 'porch'}), 'winding': ('music_box_wind', {}),
    'wind_up': ('music_box_wind', {}), 'flash': ('flash_pop', {}), 'flashbulb': ('flash_pop', {}),
    'dogs': ('dogs_search', {}), 'search_dogs': ('dogs_search', {}), 'tub': ('bathtub', {}),
    'fall_stairs': ('body_fall_stairs', {}), 'zip': ('zipper', {}), 'rules_fridge': ('fridge_paper', {}),
    'curtain_rings': ('curtain_close', {}), 'close_curtains': ('curtain_close', {}), 'peep': ('peephole', {}),
    # the final mix: film.py's picture names (audio/sfx_plan.py PICTURE refines them further)
    'hatchet_thunk': ('hatchet_step', {'thunk_only': True, 'n': 1}), 'magnet': ('magnet_click', {}),
    'deadbolt': ('lock_turn', {}), 'wet_crack': ('struggle', {'kind': 'crack'}),
    'birds_dawn': ('ambience_dawn', {'dur': 3.0, 'birds': 0.9}), 'birds_day': ('ambience_dawn', {'dur': 2.5, 'birds': 0.8}),
    'key_turn': ('key_in_lock', {}), 'floor_creak_heavy': ('wood_creak', {'kind': 'creak', 'dur': 0.8}),
    'stairs_creak': ('wood_creak', {'kind': 'creak', 'dur': 0.6}),
    'footsteps_heavy': ('footsteps_wood_inside', {'weight': 1.0}), 'wet_step': ('footsteps_wood_inside', {'weight': 1.0}),
    'vhs_glitch': ('tape_glitch', {'kind': 'tracking', 'dur': 0.3}), 'camera_flash': ('flash_pop', {}),
    'fire_crackle': ('burn_barrel', {}), 'fire_whoosh': ('burn_barrel', {'ignite': True, 'dur': 2.5}),
    'crowd_cheer': ('crowd_parade', {'dur': 3.5, 'cheer': 1.0, 'swell_at': 1.2}),
    'dogs_bark_far': ('dogs_search', {'dur': 4.0}), 'mug_set_down': ('mug_set', {}),
    'pen_write': ('stylus_scribble', {'dur': 1.0}), 'door_slam': ('struggle', {'kind': 'slam'}),
    'gust': ('wind_gust', {}), 'water': ('water_tap', {}), 'faucet': ('water_tap', {}), 'stream': ('creek', {}),
    'marker': ('marker_strike', {}),
}
KEYWORDS = [('jingle', 'jingle'), ('pemberton', 'jingle'), ('hum', 'jingle'), ('egg', 'egg_set'), ('ring', 'ring_drop'),
            ('owl', 'owl_hoot'), ('woods', 'ambience_woods'), ('forest', 'ambience_woods'), ('parade', 'crowd_parade'),
            ('crowd', 'crowd_parade'), ('cheer', 'crowd_parade'), ('hospital', 'hospital_room'), ('fire', 'burn_barrel'),
            ('barrel', 'burn_barrel'), ('melt', 'plastic_melt'), ('mitt', 'oven_mitt'), ('flap', 'slot_flap'),
            ('mail', 'slot_flap'), ('girl', 'girl_cry'), ('cry', 'girl_cry'), ('attic', 'attic_door'),
            ('bulb', 'bulb'), ('chest', 'chest_lid'), ('page', 'page_flip'), ('diary', 'page_flip'),
            ('glass', 'window_smash'), ('smash', 'window_smash'), ('kick', 'door_crash'), ('drag', 'wet_drag'),
            ('hatchet', 'hatchet_step'), ('axe', 'hatchet_step'), ('knob', 'doorknob'), ('fight', 'struggle'),
            ('struggle', 'struggle'), ('slam', 'struggle'), ('siren', 'sirens_arrive'), ('pause', 'vhs_pause'),
            ('switch', 'light_switch'), ('zip', 'zipper'), ('dog', 'dogs_search'), ('tub', 'bathtub'),
            ('curtain', 'curtain_close'), ('wind_up', 'music_box_wind'), ('music_box', 'jingle'),
            ('clack', 'dummy_clack'), ('jaw', 'dummy_jaw'), ('eyelid', 'eyelid_click'), ('wink', 'eyelid_click'),
            ('blink', 'eyelid_click'), ('laugh', 'studio_laugh'), ('applau', 'applause'), ('audience', 'studio_laugh'),
            ('spoon', 'spoon_stir'), ('stir', 'spoon_stir'), ('clink', 'spoon_clink'), ('mug', 'mug_set'),
            ('coffee', 'spoon_stir'), ('latch', 'case_latch'), ('stair', 'footsteps_stairs'), ('case_', 'case_lid'), ('velvet', 'velvet'),
            ('glove', 'glove_lift'), ('squeeze', 'hand_squeeze'), ('slot', 'hand_slot'), ('vcr', 'vcr'), ('vhs', 'vcr'),
            ('tape_', 'tape_hiss'), ('tv', 'tv_on'), ('television', 'tv_on'), ('flicker', 'lamp_flicker'),
            ('lamp', 'lamp_out'), ('flashlight', 'flashlight_click'), ('torch', 'flashlight_click'),
            ('monitor', 'heart_monitor'), ('flatline', 'monitor_flatline'), ('scream', 'mom_scream'),
            ('shriek', 'owen_cry'), ('snort', 'snort'), ('giggle', 'owen_giggle'), ('sip', 'sip'), ('thud', 'dummy_thud'),
            ('rug', 'dummy_thud'), ('dummy', 'wood_knock'), ('wood', 'wood_knock'), ('goodnight', 'goodnight_hit'),
            ('clock', 'old_clock'), ('hospital', 'hospital_tone'), ('museum', 'museum_tone'),
            ('doorbell', 'doorbell_dingdong'), ('chime', 'doorbell_dingdong'), ('box', 'box_creak'),
            ('carton', 'box_creak'), ('tape', 'tape_rip'), ('knock', 'knock_door'), ('hazard', 'hazard_ticks'),
            ('stair', 'footsteps_stairs'), ('step', 'footsteps_porch'), ('foot', 'footsteps_porch'),
            ('key', 'keys_drop'), ('window', 'window_slide'), ('curtain', 'curtain_flutter'), ('cloth', 'cloth_rustle'),
            ('stylus', 'stylus_scribble'), ('tap', 'touch_tap'), ('notif', 'phone_notify'), ('phone', 'phone_notify'),
            ('camera', 'camera_shutter'), ('photo', 'camera_shutter'), ('sob', 'mom_sob'), ('cry', 'mom_sob'),
            ('breath', 'breath'), ('ambien', 'ambience_suburb'), ('tone', 'room_tone_house'), ('whoosh', 'whoosh'),
            ('impact', 'impact_hit'), ('hit', 'impact_hit'), ('sting', 'stinger'), ('braam', 'braam'),
            ('rise', 'riser'), ('creak', 'door_creak'), ('door', 'door_creak'), ('lock', 'lock_turn'),
            ('chain', 'chain_lock'), ('glitch', 'glitch'), ('beep', 'bodycam_beep'), ('ui', 'ui_pop'),
            ('click', 'radio_click'), ('heart', 'heartbeat'), ('clock', 'clock_tick'), ('tick', 'clock_tick'),
            ('whisper', 'crowd_whisper')]
# the Doctor film's aliases and keywords (looser words a cue sheet may use)
ALIASES.update({
    'phone_ring_old': ('landline_ring', {}), 'landline': ('landline_ring', {}), 'old_phone_ring': ('landline_ring', {}),
    'kitchen_phone': ('landline_ring', {}), 'bell_ring': ('landline_ring', {}), 'receiver_lift': ('receiver_up', {}),
    'pick_up': ('receiver_up', {}), 'hang_up': ('receiver_down', {}), 'receiver_hang': ('receiver_down', {}),
    'receiver_set': ('receiver_down', {'kind': 'set'}), 'set_receiver': ('receiver_down', {'kind': 'set'}),
    'cord_pull': ('cord_yank', {}), 'unplug': ('cord_yank', {}), 'hold': ('hold_music', {}),
    'hold_line': ('hold_music', {'version': 'landline'}), 'pen_write': ('pen_scratch', {}),
    'pen_scribble': ('pen_scratch', {}), 'writing': ('pen_scratch', {}), 'clip_board': ('clipboard', {}),
    'match': ('match_strike', {}), 'burn_paper': ('paper_burn', {}), 'sink_fire': ('paper_burn', {}),
    'rain': ('rain_house', {}), 'car_engine': ('halverson_car', {}), 'engine_idle': ('halverson_car', {}),
    'fluorescent': ('waiting_room', {}), 'fluorescent_hum': ('waiting_room', {}), 'tv_hiss': ('tv_dead', {}),
    'ticket': ('ticket_tear', {}), 'take_a_number': ('ticket_tear', {}), 'ding': ('now_serving', {}),
    'serving_ding': ('now_serving', {}), 'pulse': ('pulse_count', {}), 'tape_rip_head': ('tape_peel', {}),
    'unmask': ('tape_peel', {}), 'mirror_cabinet': ('medicine_cabinet', {}), 'cabinet': ('medicine_cabinet', {}),
    'carry': ('carry_child', {}), 'drive': ('drive_rain', {}), 'driving': ('drive_rain', {}),
    'wipers': ('drive_rain', {}), 'sliding_doors': ('er_doors', {}), 'automatic_doors': ('er_doors', {}),
    'er': ('er_bustle', {}), 'hospital_bustle': ('er_bustle', {}), 'monitors': ('er_bustle', {}),
    'rocking_chair': ('chair_rock', {}), 'empty_chair': ('chair_rock', {}), 'sit': ('sit_down', {}),
    'office': ('office_3am', {}), 'hospital_night': ('office_3am', {}), 'call_connect': ('phone_connect', {}),
    'knock_front': ('knock_door', {'n': 4, 'force': 0.75}), 'knock_halverson': ('knock_door', {'n': 4, 'force': 0.8}),
    'dawn': ('ambience_dawn', {}), 'lamp_click': ('light_switch', {}), 'coffee_set': ('mug_set', {}),
    'office_phone': ('phone_ring', {}), 'ambulance_far': ('siren_far', {}), 'house': ('house_night', {}),
    'room_tone_night': ('house_night', {}), 'clock_slow': ('wall_clock', {'bpm_end': 24.0, 'sag': 4.0}),
    'tear_card': ('card_tear', {}), 'card_rip': ('card_tear', {}), 'type': ('typewriter', {}),
})
KEYWORDS = [('landline', 'landline_ring'), ('receiver', 'receiver_up'), ('cord', 'cord_yank'),
            ('hold', 'hold_music'), ('fridge', 'fridge_hum'), ('clock', 'wall_clock'), ('pen', 'pen_click'),
            ('match', 'match_strike'), ('burn', 'paper_burn'), ('rain', 'rain_house'), ('ticket', 'ticket_tear'),
            ('serving', 'now_serving'), ('pulse', 'pulse_count'), ('tape', 'tape_peel'),
            ('cabinet', 'medicine_cabinet'), ('wheelchair', 'wheelchair'), ('streetlight', 'streetlight'),
            ('buzz', 'waiting_room'), ('waiting', 'waiting_room'), ('drive', 'drive_rain')] + KEYWORDS

_WARNED = set()


def warn(msg):
    if msg not in _WARNED:
        _WARNED.add(msg)
        print('[sfx] WARNING:', msg, file=sys.stderr, flush=True)


def resolve(name, params=None):
    """name -> (recipe name, params, note). note is None for a known name, 'alias' for an alias, a warning text for a
    keyword guess; recipe name None when nothing fits."""
    params = dict(params) if isinstance(params, dict) else {}
    if not isinstance(name, str):
        name = str(name)
    if name in RECIPES:
        return name, params, None
    key = str(name).lower().strip().replace('-', '_').replace(' ', '_')
    if key in RECIPES:
        return key, params, 'alias'
    if key in ALIASES:
        canon, extra = ALIASES[key]
        return canon, {**extra, **params}, 'alias'
    for kw, canon in KEYWORDS:
        if kw in key:
            return canon, params, f'unknown SFX {name!r}: keyword fallback to {canon!r}'
    return None, params, f'unknown SFX {name!r}: no fallback, skipped'


def resolve_space(sp, name):
    if sp is not None and not isinstance(sp, str):
        d = DEFAULT_SPACE[name]
        warn(f'space {sp!r} for {name!r} is not a name: using {d!r}')
        return d
    if sp is None or sp in SPACE_LU:
        return sp
    k = str(sp).lower().strip()
    if k in SPACE_LU:
        return k
    if k in SPACE_ALIAS:
        return SPACE_ALIAS[k]
    d = DEFAULT_SPACE[name]
    warn(f'unknown space {sp!r} for {name!r}: using {d!r}')
    return d


# ======================================================================================== Bus film recipes
# "If The School Bus Stops At Midnight... DON'T GET ON". The owner's bus set first (W/samples/epidemic_bus/sfx: the
# air brakes, idles, folding doors, horns, pass-bys, bus interiors, skids, metal scrapes, car-window glass, PA /
# megaphone / spring feedback, walkie-talkies, tapes, the CRT, the VHS eject, glitches, referee whistles, hole
# punches, seat belts, the flag cable and the rope on a mast, the bendy pole, wood snaps, cloth rips, latex gloves,
# big cats, school walla), then the doctor (school bell, buzz, phones, the night interstate), police (suburban
# crickets and the far dog, the deadbolt), mirror (bare feet, stairs), dummy (VHS insert / rewind) and bunny sets;
# synthesis only for the bodies (door slap, mirror housing, clipboard board), the mains thump, the tape transport,
# DTMF and the roger beep. Every verdict on a new file is in W/mix/sfx_review.md. The PSA jingle is not an SFX: it is
# audio/jingle_bus.py, placed by score.py ('jingle' events of music_plan.IDENTITY).
BUS_NAMES = ('suburb_night', 'dog_far', 'street_flicker', 'bus_air_brake', 'bus_idle', 'bus_door', 'his_unfold',
             'pa_crackle', 'bus_pull_away', 'bus_horn', 'bus9_start', 'bus9_drive', 'bus_swerve', 'mirror_rip',
             'bus_fast_night', 'dash_radio', 'tire_screech', 'whistle', 'ticket_punch', 'deadbolt', 'walkie',
             'power_down', 'power_up', 'run_asphalt', 'cat_rumble', 'glove_squeak', 'tape_skip', 'crt_on',
             'vhs_tape', 'tape_ff', 'tape_slide', 'seatbelt', 'flag_rope', 'broom_bend', 'broom_crack', 'cloth_rip',
             'school_bell', 'bus_rewind', 'clipboard_drop', 'morning_bus', 'dial_911', 'his_bus_interior',
             'school_night', 'mailbox_unscrew')
BUS_NAMES = BUS_NAMES + ('hand_slap',)                # sound fix round 3
NAMES = NAMES + BUS_NAMES
# one-shots: momentary max, LU rel the voice at gain_db 0; beds (BEDS, and DUR_BEDS given a dur): integrated
# (test 1: pa_crackle -9 sat 20-22 LU under his loudspeaker voice through the window: -4; tests 2-4: glove_squeak
# -10 sat 22-26 LU under the narration: -6)
LEVEL_LU.update(suburb_night=-27, dog_far=-14, street_flicker=-12, bus_air_brake=-5, bus_idle=-24, bus_door=-6,
                his_unfold=-8, pa_crackle=-4, bus_pull_away=-10, bus_horn=-6, bus9_start=-8, bus9_drive=-24,
                bus_swerve=-1, mirror_rip=0, bus_fast_night=-23, dash_radio=-18, tire_screech=-4, whistle=-3,
                ticket_punch=-3, deadbolt=-4, walkie=-8, power_down=-3, power_up=-4, run_asphalt=-8,
                cat_rumble=-26, glove_squeak=-6, tape_skip=-7, crt_on=-8, vhs_tape=-7, tape_ff=-12, tape_slide=-10,
                seatbelt=-5, flag_rope=-20, broom_bend=-6, broom_crack=-2, cloth_rip=-4, school_bell=-6,
                bus_rewind=-4, clipboard_drop=-4, morning_bus=-24, dial_911=-10, his_bus_interior=-27,
                school_night=-27, mailbox_unscrew=-11)
PEAK_CAP.update(bus_air_brake=-5.0, bus_door=-4.0, bus_horn=-5.0, bus_swerve=-3.0, mirror_rip=-2.0, tire_screech=-4.0,
                whistle=-4.0, ticket_punch=-2.0, deadbolt=-3.0, walkie=-5.0, power_down=-3.0, power_up=-4.0,
                tape_skip=-4.0, seatbelt=-3.0, broom_crack=-3.0, cloth_rip=-4.0, bus_rewind=-3.0,
                clipboard_drop=-2.0, glove_squeak=-5.0, street_flicker=-6.0, crt_on=-5.0, vhs_tape=-4.0,
                run_asphalt=-5.0, mailbox_unscrew=-5.0, dial_911=-6.0)
BEDS = BEDS + ('suburb_night', 'bus_idle', 'bus9_drive', 'bus_fast_night', 'morning_bus', 'his_bus_interior',
               'school_night')
DUR_BEDS = DUR_BEDS + ('dash_radio', 'cat_rumble', 'flag_rope', 'tape_ff', 'run_asphalt')
BED_BUS = BED_BUS + ('suburb_night', 'bus_idle', 'bus9_drive', 'bus_fast_night', 'morning_bus', 'his_bus_interior',
                     'school_night', 'dash_radio', 'cat_rumble', 'flag_rope')
HITS = HITS + ('mirror_rip', 'bus_swerve', 'power_down', 'bus_rewind')
# spaces: 'bus' (inside a bus: a small metal box, seats), 'school' (the schoolyard at night: brick walls, a flat slap),
# 'pa' (heard through his loudspeaker horn), 'lawn' (out on the front lawn, the house behind)
SPACE_LU.update(bus=0.0, school=-3.0, pa=-2.0, lawn=-3.0)
SPACE_ALIAS.update(bus_9='bus', bus9='bus', cab='bus', aisle='bus', his_bus='bus', on_bus='bus', schoolyard='school',
                   school_doors='school', parking='school', loudspeaker='pa', speakerhorn='pa', front_lawn='lawn',
                   driveway_out='lawn', mailbox='lawn', curtains='window', living='close', grandma_room='close',
                   bedroom_door='inside', stair='inside', upstairs_hallway='upstairs', road_chase='street')
SPACES = tuple(SPACE_LU)
DEFAULT_SPACE.update(suburb_night='dry', dog_far='street', street_flicker='street', bus_air_brake='street',
                     bus_idle='street', bus_door='street', his_unfold='street', pa_crackle='pa', bus_pull_away='street',
                     bus_horn='street', bus9_start='lawn', bus9_drive='dry', bus_swerve='bus', mirror_rip='bus',
                     bus_fast_night='dry', dash_radio='bus', tire_screech='street', whistle='close',
                     ticket_punch='close', deadbolt='close', walkie='close', power_down='inside', power_up='inside',
                     run_asphalt='lawn', cat_rumble='dry', glove_squeak='close', tape_skip='dry', crt_on='close',
                     vhs_tape='close', tape_ff='close', tape_slide='dry', seatbelt='bus', flag_rope='school',
                     broom_bend='school', broom_crack='school', cloth_rip='close', school_bell='school',
                     bus_rewind='school', clipboard_drop='school', morning_bus='dry', dial_911='close',
                     his_bus_interior='dry', school_night='dry', mailbox_unscrew='lawn')


def _space_bus(y, kind, seed=0, wet=None):
    if kind == 'bus':                                   # a bus: hard seats and metal, a short boxy slap, a rattle
        x = reverb(lp(y, 11000, 1), 'car', 0.3 if wet is None else wet, 0.001)
        return eq(x, ('peak', 320, 2.0, 1.2), ('peak', 2400, -1.5, 1.0))
    if kind == 'school':                                # the schoolyard: brick walls, a flat slap, open sky
        x = reverb(y, 'street', 0.32 if wet is None else wet, 0.004)
        sl = np.zeros_like(x); k = n_(0.085); sl[k:] = x[:-k] * 0.22
        return x + lp(sl, 3500, 2)
    if kind == 'pa':                                    # through his loudspeaker horn, out on the street
        m = mono(y)
        m = eq(lp(hp(m, 420, 4), 3600, 4), ('peak', 1900, 5.0, 1.3))
        pk = peak(m) + 1e-9
        m = (np.tanh(2.0 * m / pk) / np.tanh(2.0) * pk).astype(np.float32)
        return reverb(st(m), 'street', 0.3 if wet is None else wet, 0.01)
    if kind == 'lawn':                                  # out front: the house fronts, the street beyond
        return reverb(y, 'porch', 0.28 if wet is None else wet, 0.002)
    return None


_space_prev_bus = space


def space(y, kind, seed=0, wet=None):             # noqa: F811 (the bus spaces first, then every earlier one)
    r = _space_bus(st(y), kind, seed, wet)
    return r if r is not None else _space_prev_bus(y, kind, seed, wet)


def _bp(key, name, keys=(), mode='onset', **seg):
    """A grain pool over the files serving `name` (those whose id has any of keys)."""
    return pool('bus_' + key + '|' + ','.join(keys), lambda: (_has(name, *keys) if keys else src(name)), mode, **seg)


def _bx(name, keys, dur, rng, xfade=1.5):
    E = _has(name, *keys) if keys else src(name)
    return excerpt(_pick(rng, E or src(name)), float(dur), rng, xfade)


def _grain_list(name, keys, mode='phrase', **seg):
    """[(entry, (s0, s1))] of every grain of the files serving name (keys narrow it), file order kept."""
    out = []
    for e in (_has(name, *keys) if keys else src(name)):
        for g in grains(e, mode, **seg):
            out.append((e, g))
    return out


def _cut(e, g):
    return audio(e)[g[0]:g[1]]


def _dom_hz(y, lo=1500.0, hi=5000.0):
    m = mono(y); n = min(len(m), n_(0.5))
    s = np.abs(np.fft.rfft(m[:n] * np.hanning(n))); f = np.fft.rfftfreq(n, 1 / SR)
    k = (f > lo) & (f < hi)
    return float(f[k][np.argmax(s[k])]) if k.any() else 0.0


def r_suburb_night(rng, sp, dur=30.0, dog=0.35, inside=False, **_):
    """BED: Larch Street at midnight: crickets and the far suburb (the police set's suburban nights), a far dog now and
    then, a whisper of wind. inside=True: heard in the living room through the glass (dark, 9 dB down, the house's
    room tone under it)."""
    d = float(dur)
    y = lp(hp(_bx('suburb_night', ('crickets',), d, rng, 2.0), 120, 2), 9000, 2)
    if dog > 0:
        try:                                   # final mix (Obsession): the Bus film's dog pool is not linked here
            P = _bp('dog', 'dog_far', (), 'onset', gap=0.25, max_len=1.2, keep=-18); P.get(np.random.default_rng(0))
        except KeyError:
            P = None
        t = rng.uniform(3, 9)
        while P is not None and t < d - 2:
            if rng.uniform() < dog:
                for j in range(int(rng.integers(1, 3))):
                    g = lp(P.get(rng, rj=0.04), 3500, 2) * 0.35
                    place(y, reverb(g, 'street', 0.6), n_(t + j * rng.uniform(0.4, 0.7)))
            t += rng.uniform(8, 18)
    if inside:
        y = lp(y, 2200, 2) * 0.35 + st(lp(noise(d, int(rng.integers(1 << 30))), 180, 2)) * 0.004
    return fade(y, 1.0, 1.5), 0.0, 0.0, False


def r_dog_far(rng, sp, n=2, **_):
    """A dog two streets away: n barks (the police set's distant dog barks)."""
    P = _bp('dog', 'dog_far', (), 'onset', gap=0.25, max_len=1.2, keep=-18)
    y = _seq([(j * rng.uniform(0.45, 0.8), P.get(rng, rj=0.04)) for j in range(int(n))], 0.4)
    return lp(y, 4000, 2), onset_s(y, -14), 0.0, False


def r_street_flicker(rng, sp, n=3, dur=None, **_):
    """'The streetlight flickers.' The sodium lamp's ballast buzz stuttering (the doctor set's interference buzz),
    n quick drop-outs with the starter's ticks, a low ballast thunk on the last."""
    d = float(dur or 0.35 + 0.16 * n)
    y = hp(_dx('fluorescent', ('interference',), d + 0.4, rng, 0.5), 90, 2)[:n_(d + 0.4)]
    g = np.ones(len(y), np.float32); ev = []
    for j in range(int(n)):
        t = 0.12 + j * rng.uniform(0.11, 0.2)
        a = n_(t); b = a + n_(rng.uniform(0.03, 0.07))
        g[a:b] = 0.05
        ev.append((t, st(modal([3100.0, 5200.0, 900.0], [0.004, 0.003, 0.01], [1.0, 0.5, 0.4], 0.03, j)) * 0.4))
    from scipy.ndimage import uniform_filter1d
    y = y * uniform_filter1d(g, n_(0.004))[:, None]
    y = y / (peak(y) + 1e-9)
    tick = _seq(ev + [(ev[-1][0] + 0.03, st(sub_boom(70, 45, 0.25, 0.1, 3)) * 0.5)], 0.2)
    out = np.zeros((max(len(y), len(tick)), 2), np.float32); out[:len(y)] += y; out[:len(tick)] += tick
    return fade(out, 0.03, 0.15), 0.1, 0.0, False


def r_bus_air_brake(rng, sp, **_):
    """'Air brakes hiss outside.' The bus set's stationary air-brake releases (the compressor's burst, the long hiss),
    the chassis settling on its springs (a low creak and thump under it)."""
    E = _has('bus_air_brake', 'compressor')
    gl = []
    for e in E:
        gl += [(e, g) for g in grains(e, 'phrase', gap=0.35, max_len=4.0, keep=-14) if (g[1] - g[0]) > n_(0.6)]
    if not gl:
        gl = _grain_list('bus_air_brake', (), 'phrase', gap=0.35, max_len=4.0, keep=-14)
    e, g = gl[int(rng.integers(len(gl)))]
    y = pnorm(fade(_cut(e, g), 0.003, 0.25))
    y = eq(hp(y, 150, 2), ('hs', 7000, -3.0, 0.7))
    body = st(sub_boom(62, 40, 0.7, 0.05, int(rng.integers(1 << 20)))) * 0.5
    y = _seq([(0, y), (0.02, body)], 0.2)
    return y, onset_s(y, -14), 0.0, False


def _sick_rattle(d, rng, amount=0.6):
    """A loose panel and something loose in the engine bay: bursts of band-passed noise through panel modes at an
    unsteady ~11 Hz, coming and going."""
    n = n_(d); t = np.arange(n) / SR
    rate_ = 11.0 * (1 + 0.15 * np.sin(2 * np.pi * 0.23 * t + rng.uniform(0, 6)))
    ph = np.cumsum(rate_) / SR
    gate = (np.sin(2 * np.pi * ph) > 0.55).astype(np.float32)
    from scipy.ndimage import uniform_filter1d
    gate = uniform_filter1d(gate, n_(0.003))
    swell = 0.5 + 0.5 * np.clip(np.sin(2 * np.pi * 0.11 * t + rng.uniform(0, 6)) * 1.6, -1, 1)
    z = bp(noise(d, int(rng.integers(1 << 30))), 700, 2600, 2)[:n] * gate * swell * amount
    z = eq(z, ('peak', 1150, 6.0, 4.0), ('peak', 1730, 4.0, 5.0))
    return st(z.astype(np.float32))


def r_bus_idle(rng, sp, dur=20.0, rattle=0.6, kind='his', **_):
    """BED: a school bus idling. kind 'his': HIS old bus at the curb, a bigger, sicker diesel (the bus set's idles,
    1.5 semitones down, a loping 0.7 Hz miss) with a loose rattle; kind 'bus9': Grandma's bus 9 idling in the driveway
    (clean, steady)."""
    d = float(dur)
    E = _has('bus_idle', 'engine_idle', 'engine_perspective', 'standing_still') or src('bus_idle')
    x = audio(_pick(rng, E, 1.0))
    x = x[n_(2.0):-n_(3.0)] if len(x) > n_(10) else x                    # skip the start / the engine-off tail
    y = _loop(x, n_(d + 1.0), rng, 1.2)
    if kind == 'his':
        y = rate(y, semis(-1.5))[:n_(d)]
        t = np.arange(len(y)) / SR
        lope = 1 - 0.18 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * t + rng.uniform(0, 6))) ** 4
        y = y * lope[:, None].astype(np.float32)
        y = lp(y, 3200, 2)
        if rattle > 0:
            y = y + _lv(_sick_rattle(len(y) / SR, rng, 1.0), lufs_int(y) - 9) * rattle
    else:
        y = lp(y[:n_(d)], 5000, 2)
    return fade(y[:n_(d)], 0.8, 1.0), 0.0, 0.0, False


def r_bus_door(rng, sp, action='open', slap=1.0, **_):
    """The folding bus door. 'open': the air valve's burst and the two leaves folding back (the bus set's door
    takes, first phrase); 'close': the leaves swinging in and SLAPPING shut on the rubber (last phrase + a rubber and
    sheet-metal slap)."""
    gl = _grain_list('bus_door', ('no_engine', 'compressor_air', 'no_passengers'), 'phrase', gap=0.45, max_len=3.0,
                     keep=-18)
    byfile = {}
    for e, g in gl:
        byfile.setdefault(e['id'], []).append((e, g))
    files = [v for v in byfile.values() if len(v) >= 2] or list(byfile.values())
    f = files[int(rng.integers(len(files)))]
    e, g = f[0] if action == 'open' else f[-1]
    y = pnorm(fade(_cut(e, g), 0.003, 0.08))
    if action != 'open' and slap > 0:
        s = st(modal([118.0, 290.0, 640.0, 1460.0], [0.07, 0.05, 0.025, 0.01], [1.0, 0.7, 0.4, 0.15], 0.35,
                     int(rng.integers(1 << 20))))
        s = s * 0.8 / (peak(s) + 1e-9)
        k = int(np.argmax(np.abs(mono(y)) > 0.5 * peak(y)))
        y = _seq([(0, y), (k / SR, s * slap)], 0.3)
    return y, onset_s(y, -12), 0.0, False


def r_his_unfold(rng, sp, n=5, spacing=0.34, **_):
    """'Something unfolds out of it. Like a ladder. Up, and up, and up.' n segments: each a long joint creak (the
    bus set's bendy pole, a fifth down) ending in a latch click, each one higher than the last."""
    P = _bp('pole', 'broom_bend', ('bendy_pole',), 'phrase', gap=0.15, max_len=1.2, keep=-20)
    ev = []
    for j in range(int(n)):
        c = rate(P.get(rng, rj=0.03), semis(-7.0 + 1.2 * j))
        c = fade(c[:n_(spacing * 1.4)], 0.01, 0.06) * 0.7
        clk = st(modal([1900.0 + 150 * j, 3400.0, 760.0], [0.006, 0.004, 0.02], [1.0, 0.5, 0.6], 0.05, j)) * 0.6
        ev += [(j * spacing, c), (j * spacing + spacing * 0.8, clk)]
    y = _seq(ev, 0.3)
    return y, 0.0, 0.0, False


def r_pa_crackle(rng, sp, kind='on', dur=None, **_):
    """His bus loudspeaker. 'on': keyed open (a pop, crackle, a breath of feedback rising); 'off': keyed shut (a
    crackle and the pop); 'feedback': a feedback ring (the bus set's microphone / megaphone feedback, band-passed in
    the horn's range) for dur (default 1.6)."""
    C = _bp('crk', 'vinyl_crackle', (), 'phrase', gap=0.3, max_len=2.0, keep=-30)
    crk = hp(C.get(rng, rj=0.05)[:n_(0.5)], 900, 2) * 0.5
    pop = st(sub_boom(120, 60, 0.08, 0.3, int(rng.integers(1 << 20)))) * 0.6
    if kind == 'feedback':
        d = float(dur or 1.6)
        F = _has('pa_crackle', 'feedback_single', 'feedback_resonance', 'megaphone') or src('pa_crackle')
        y = excerpt(_pick(rng, F, 1.0), d, rng, 0.3)
        y = bp(y, 600, 4000, 2)
        return fade(y, 0.15, 0.3), 0.0, 0.0, False
    F = _has('pa_crackle', 'feedback_single', 'megaphone') or src('pa_crackle')
    fb = bp(excerpt(_pick(rng, F, 1.0), 0.6, rng, 0.2), 900, 3600, 2)
    fb = fb * (0.25 / (peak(fb) + 1e-9)) * np.linspace(0, 1, len(fb))[:, None].astype(np.float32) ** 2
    if kind == 'off':
        y = _seq([(0, crk[:n_(0.25)]), (0.2, pop)], 0.2)
    else:
        y = _seq([(0, pop), (0.01, crk), (0.15, fb)], 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_bus_pull_away(rng, sp, dur=7.0, kind='his', **_):
    """'The bus pulls away with no lights on.' A bus moving off and away down the street (the bus set's start /
    drive-away take, the drive part); kind 'his': a semitone down and darker."""
    E = _has('bus_pull_away', 'drive_away') or src('bus_pull_away')
    x = audio(_pick(rng, E, 1.0))
    y = x[n_(2.5):n_(2.5 + float(dur))] if len(x) > n_(2.5 + dur) else _fit(x, n_(dur), rng)
    if kind == 'his':
        y = lp(rate(y, semis(-1.0)), 3500, 2)
    y = y * np.linspace(1.0, 0.15, len(y))[:, None].astype(np.float32) ** 1.5
    return fade(y, 0.2, 1.2), 0.0, 0.0, False


def r_bus_horn(rng, sp, kind='short', **_):
    """A bus horn: 'short' (a short blast from the bus set's horns), 'long' (the long blast)."""
    gl = _grain_list('bus_horn', (), 'phrase', gap=0.2, max_len=4.0, keep=-12)
    gl = sorted(gl, key=lambda eg: eg[1][1] - eg[1][0])
    pickf = gl[:max(1, len(gl) // 2)] if kind == 'short' else gl[len(gl) // 2:]
    e, g = pickf[int(rng.integers(len(pickf)))]
    y = fade(pnorm(_cut(e, g)), 0.004, 0.08)
    return y, onset_s(y, -12), 0.0, False


def r_bus9_start(rng, sp, **_):
    """Bus 9 starting in the driveway: the starter and the diesel catching (the bus set's start take, first 3.5 s)."""
    E = _has('bus9_drive', 'engine_start') or _has('bus_pull_away', 'engine_start')
    x = audio(_pick(rng, E, 1.0))
    y = fade(x[:n_(3.5)], 0.01, 0.6)
    return y, onset_s(y, -14), 0.0, False


def r_bus9_drive(rng, sp, dur=30.0, speed='medium', **_):
    """BED: inside Grandma's bus 9 on the road at night (the bus set's on-board drive and the double-decker's rattle);
    speed 'fast': the night interstate under it (the doctor set) and the wind at the windows."""
    d = float(dur)
    y = lp(_bx('bus9_drive', ('on_board_driving',), d, rng, 2.0), 6000, 2)
    r = _has('bus9_drive', 'double_decker')
    if r:
        y = y + _lv(lp(excerpt(_pick(rng, r, 1.0), d, rng, 2.0), 5000, 2), lufs_int(y) - 7)
    if speed == 'fast':
        f = _bx('bus_fast_night', ('fast_driving',), d, rng, 2.0)
        y = y * 0.8 + _lv(lp(f, 4500, 2), lufs_int(y) - 2)
    return fade(y, 1.0, 1.0), 0.0, 0.0, False


def r_bus_fast_night(rng, sp, dur=30.0, **_):
    """BED: the chase: bus 9 flat out at night (the doctor set's night interstate, the bus interior's rattle and
    hum over it)."""
    return r_bus9_drive(rng, sp, dur=dur, speed='fast')


def r_tire_screech(rng, sp, dur=1.4, **_):
    """Tyres screeching (the bus set's skids), cut to dur, a little lower (a heavy vehicle)."""
    P = _bp('skid', 'tire_screech', ('skid',), 'phrase', gap=0.3, max_len=3.0, keep=-12)
    y = rate(P.get(rng, rj=0.02, tilt=0), semis(-2.0))
    y = fade(y[:n_(dur)], 0.02, 0.25)
    return y, onset_s(y, -14), 0.0, False


def r_bus_swerve(rng, sp, **_):
    """'Grandma swerves.' The tyres screeching, the body leaning (a low lurch and the seats' metal creak), everything
    loose in the bus rattling at once."""
    sc, _p, _o, _s = r_tire_screech(rng, sp, dur=1.2)
    lurch = st(sub_boom(55, 32, 1.0, 0.05, int(rng.integers(1 << 20)))) * 0.7
    rat = _sick_rattle(0.8, rng, 1.0)
    rat = rat * (0.35 / (peak(rat) + 1e-9)) * np.exp(-np.arange(len(rat)) / n_(0.3))[:, None].astype(np.float32)
    y = _seq([(0, sc), (0.05, lurch), (0.1, rat)], 0.3)
    return y, onset_s(y, -14), 0.0, False


def r_mirror_rip(rng, sp, **_):
    """'His bumper rips our side mirror off.' The housing torn off its arm: a big metal scrape (the bus set's large
    loud scrapes, 0.7 s), the mirror glass smashing (a car-window smash, its first hit and the debris), the plastic
    housing cracking, the bits skittering away behind."""
    S = _bp('scrape', 'metal_scrape', ('large_loud',), 'phrase', gap=0.2, max_len=2.0, keep=-12)
    sc = S.get(rng, rj=0.03)[:n_(0.75)]
    sc = fade(sc, 0.005, 0.2)
    G = _bp('glass', 'glass_break', ('car_window',), 'onset', gap=0.08, max_len=1.6, keep=-8)
    gl = G.get(rng, rj=0.02)
    crack = st(modal([420.0, 1150.0, 2600.0], [0.03, 0.015, 0.006], [1.0, 0.6, 0.4], 0.12, int(rng.integers(1 << 20))))
    crack = crack * 0.7 / (peak(crack) + 1e-9)
    boom = st(sub_boom(60, 34, 1.2, 0.2, int(rng.integers(1 << 20)))) * 0.6
    y = _seq([(0, sc), (0.06, crack), (0.08, gl * 0.9), (0.0, boom)], 0.5)
    return y, onset_s(y, -14), 0.0, False


def r_dash_radio(rng, sp, dur=3.0, kind='crackle', **_):
    """Bus 9's radio to the depot: 'crackle' (the dash speaker's static between stations, band-limited, squelch pops
    at the edges, dur); 'key' (one squelch-and-crackle burst: before / after his voice)."""
    if kind == 'key':
        y, *_r = r_walkie(rng, sp, kind='squelch')
        return y, onset_s(y, -14), 0.0, False
    d = float(dur)
    y = _bx('dash_radio', ('station_search',), d, rng, 0.6)
    y = eq(bp(y, 350, 3200, 2), ('peak', 1300, 3.0, 1.0))
    pop = hp(st(sub_boom(160, 80, 0.06, 0.4, 1)), 300, 2) * peak(y) * 0.25
    y = _seq([(0, y), (0, pop), (max(0.0, d - 0.08), pop)], 0.1)
    return fade(y, 0.01, 0.05), 0.0, 0.0, False


def r_whistle(rng, sp, kind='short', n=2, spacing=0.27, far=False, tune=True, **_):
    """His silver whistle (the bus set's referee whistles). kind 'short': "Fweet-fweet" = n short blasts (spacing s
    apart, the jingle's hook rhythm); 'long': one long, loud blast (about 2.2 s: drowning the calling out). tune=True
    pitches each blast so its whistle tone sits on A7 (3520 Hz), the jingle's hook an octave pair up; far=True: the
    10-metre take."""
    keys = ('10_metres',) if far else ('referee_whistle_01', 'referee_whistle_02')
    gl = _grain_list('whistle', keys, 'onset', gap=0.12, max_len=2.5, keep=-14)
    if not gl:
        gl = _grain_list('whistle', ('referee',), 'onset', gap=0.12, max_len=2.5, keep=-14)
    gl = sorted(gl, key=lambda eg: eg[1][1] - eg[1][0])
    def tuned(y):
        if not tune:
            return y
        f = _dom_hz(y, 2000, 4800)
        return rate(y, 3520.0 / f) if f > 0 and 0.7 < 3520.0 / f < 1.45 else y
    if kind == 'long':
        e, g = gl[-1]
        y = tuned(pnorm(_cut(e, g)))
        a = n_(0.12); body = y[a:]
        y = np.concatenate([y[:a], _fit(body, n_(2.1), rng)])
        env = np.ones(len(y), np.float32); k = n_(0.15); env[-k:] = np.linspace(1, 0, k)
        y = y * env[:, None]
        return fade(y, 0.003, 0.05), onset_s(y, -12), 0.0, False
    short = [eg for eg in gl if (eg[1][1] - eg[1][0]) < n_(0.6)] or gl[:3]
    ev = []
    for j in range(int(n)):
        e, g = short[int(rng.integers(len(short)))]
        b = tuned(pnorm(_cut(e, g)))[:n_(0.17)]
        ev.append((j * spacing, fade(b, 0.002, 0.025) * (1.0 if j else 0.92)))
    y = _seq(ev, 0.4)
    return y, onset_s(y, -12), 0.0, False


def r_ticket_punch(rng, sp, **_):
    """"Click-clack." His ticket punch: the jaws biting through the card (the bus set's hole punches: the click) and
    springing back (a second grain, higher: the clack), a little metal ring."""
    P = _bp('punch', 'ticket_punch', ('single',), 'onset', gap=0.06, max_len=0.35, keep=-16)
    a = rate(P.get(rng, rj=0.02), semis(-1.0))
    b = rate(P.get(rng, rj=0.02), semis(2.0)) * 0.8
    ring = st(modal([2650.0, 4100.0], [0.03, 0.02], [1.0, 0.5], 0.08, 3)) * 0.12
    y = _seq([(0, a), (0.0, ring), (0.13, b)], 0.15)
    return y, onset_s(y, -12), 0.0, False


def r_deadbolt(rng, sp, action='slide', **_):
    """Grandma's deadbolt: 'slide' (the bolt sliding back: the police set's deadbolt / mortise turns, the long one),
    'lock' (thrown shut)."""
    P = _bp('bolt', 'deadbolt', (), 'phrase', gap=0.15, max_len=1.2, keep=-16)
    y = P.get(rng, rj=0.02)
    if action == 'slide':
        y = rate(y, 0.85)
    return y, onset_s(y, -12), 0.0, False


def r_walkie(rng, sp, kind='squelch', dur=None, **_):
    """The kids' walkie-talkies: 'engage' (the PTT key), 'squelch' (the squelch tail), 'beep' (a roger beep:
    1.1 kHz then 1.6 kHz, 70 ms each, through the little speaker), 'glitch' (a stuttering, glitchy squelch: HIS voice
    on the walkie), 'hiss' (the open channel, dur)."""
    if kind == 'beep':
        t = np.arange(n_(0.07)) / SR
        b = np.concatenate([np.sin(2 * np.pi * 1100 * t), np.sin(2 * np.pi * 1600 * t)]).astype(np.float32)
        b = bp(b * np.hanning(len(b)) ** 0.2, 500, 3500, 2)
        y = st(b) * 0.5
        return y, 0.0, 0.0, False
    if kind == 'hiss':
        d = float(dur or 2.0)
        y = st(bp(noise(d, int(rng.integers(1 << 30))), 400, 3600, 2)) * 0.1
        return fade(y, 0.02, 0.05), 0.0, 0.0, False
    keys = {'engage': ('engage',), 'glitch': ('glitchy',), 'squelch': ('glitchy_short', 'engage')}.get(kind, ())
    P = _bp('wk_' + kind, 'walkie', keys, 'phrase', gap=0.12, max_len=1.6 if kind == 'glitch' else 0.6, keep=-18)
    y = P.get(rng, rj=0.03)
    if kind == 'squelch':
        y = y[:n_(0.35)]
    return fade(y, 0.002, 0.03), onset_s(y, -12), 0.0, False


def _mains(direction, rng):
    """The house's mains: 'down' (the fridge and the lights' hum falling in pitch and dying, a sub thunk), 'up' (a
    thunk and the hum snapping back)."""
    d = 0.9
    t = np.arange(n_(d)) / SR
    if direction == 'down':
        f = 120 * (1 - 0.45 * np.clip(t / 0.6, 0, 1))
        env = np.clip(1 - t / 0.7, 0, 1) ** 1.5
    else:
        f = np.full_like(t, 120.0)
        env = np.clip(t / 0.02, 0, 1) * np.exp(-t / 0.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    h = (np.sin(ph) + 0.4 * np.sin(3 * ph) + 0.15 * np.sin(5 * ph)) * env * 0.12
    th = sub_boom(55, 35, 0.6, 0.12, int(rng.integers(1 << 20))) * 0.9
    out = np.zeros(max(len(h), len(th)), np.float32)
    out[:len(h)] += h.astype(np.float32); out[:len(th)] += th
    return st(out)


def r_power_down(rng, sp, **_):
    """'Every light dies. Total black.' The lights' switch-off clank (the bus set's fluorescent light switch, its
    off edge), the house's hum diving and dying, a mains thunk you feel more than hear; then nothing."""
    P = _bp('fl', 'power_flicker', (), 'phrase', gap=0.2, max_len=1.2, keep=-18)
    sw = P.get(rng, rj=0.02)[:n_(0.4)]
    y = _seq([(0, sw * 0.7), (0.01, _mains('down', rng))], 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_power_up(rng, sp, **_):
    """'The lights snap back on.' The thunk of the mains returning, the switch's clank, the fluorescent tink and buzz
    coming back (the bus set's fluorescent power-up)."""
    P = _bp('fl', 'power_flicker', (), 'phrase', gap=0.2, max_len=1.2, keep=-18)
    sw = P.get(rng, rj=0.02)
    y = _seq([(0, _mains('up', rng)), (0.02, sw * 0.8)], 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_run_asphalt(rng, sp, n=None, dur=2.5, rate_=3.2, **_):
    """Running on the road (the bus set's running takes on asphalt): footfalls at rate_ per second, dur s."""
    P = _bp('runasph', 'run_asphalt', (), 'onset', gap=0.12, max_len=0.35, keep=-16)
    k = int(n or max(2, round(float(dur) * rate_)))
    ev = [(j / rate_ + rng.uniform(-0.015, 0.015), P.get(rng, rj=0.03) * rng.uniform(0.75, 1.0)) for j in range(k)]
    y = _seq(ev, 0.3)
    return y, onset_s(y, -14), 0.0, False


def r_cat_rumble(rng, sp, dur=6.0, **_):
    """Under his closest moments, barely there: a big cat's low rumble (the bus set's lion / tiger growls), a fourth
    down, low-passed at 350 Hz (felt, not heard), slow in and out."""
    d = float(dur)
    y = _bx('cat_rumble', ('low_rumble', 'deep_rumble'), d / 0.75 + 0.5, rng, 1.5)
    y = lp(rate(y, semis(-5.0)), 350, 4)[:n_(d)]
    env = np.sin(np.pi * np.clip(np.arange(len(y)) / max(1, len(y) - 1), 0, 1)) ** 0.7
    return y * env[:, None].astype(np.float32), 0.0, 0.0, False


def r_glove_squeak(rng, sp, kind='stretch', knuckles=True, **_):
    """His white gloves: 'stretch' (latex stretching and squeaking as the fingers curl: the bus set's latex glove
    takes), 'squeak' (one short squeak); knuckles=True adds the too-many joints: three tiny dry pops."""
    P = _bp('glove', 'glove_squeak', (), 'phrase', gap=0.15, max_len=1.4 if kind == 'stretch' else 0.4, keep=-18)
    y = P.get(rng, rj=0.04)
    ev = [(0, y)]
    if knuckles:
        for j in range(3):
            ev.append((0.12 + 0.11 * j, st(modal([2300.0 + 400 * j, 5100.0], [0.003, 0.002], [1.0, 0.4], 0.02, j)) * 0.3))
    y = _seq(ev, 0.15)
    return y, onset_s(y, -14), 0.0, False


def r_tape_skip(rng, sp, amount=0.7, frames=3, **_):
    """His tape-skip, one per jump closer: the VHS stutter (a 40 ms slice of a glitch / tape take repeated `frames`
    times, each a little lower), a tracking crackle (noise torn at 30 Hz with the head buzz), a soft low 'thup'."""
    P = _bp('skip', 'tape_skip', (), 'phrase', gap=0.1, max_len=1.0, keep=-20)
    g = P.get(rng, rj=0.05)
    a = int(rng.integers(0, max(1, len(g) - n_(0.05))))
    sl = g[a:a + n_(0.042)]
    st_ = np.concatenate([fade(rate(sl, 1 - 0.04 * j), 0.002, 0.004) for j in range(int(frames))])
    t = np.arange(n_(0.22)) / SR
    tear = bp(noise(0.22, int(rng.integers(1 << 30))), 1500, 7000, 2)[:len(t)] * (np.sin(2 * np.pi * 30 * t) > 0.2)
    tear = st((tear * np.exp(-t / 0.08) * 0.25 * amount).astype(np.float32))
    thup = st(sub_boom(90, 50, 0.25, 0.1, int(rng.integers(1 << 20)))) * 0.35 * amount
    y = _seq([(0, st_), (0.0, thup), (0.03, tear)], 0.1)
    return y, onset_s(y, -12), 0.0, False


def r_crt_on(rng, sp, **_):
    """The TV cart's CRT switching on (the bus set's Commodore monitor power-on, its first phrase): the relay clunk,
    the degauss thoom, the screen's static charge; a faint 15.7 kHz whine settling in."""
    gl = _grain_list('crt_on', ('crt_monitor',), 'phrase', gap=0.4, max_len=3.0, keep=-20)
    if gl:
        e, g = gl[0]
        y = lp(pnorm(fade(_cut(e, g), 0.003, 0.2)), 9000, 2)
    else:
        y, *_r = r_tv_on(rng, sp)
    t = np.arange(n_(1.6)) / SR
    wh = st((np.sin(2 * np.pi * 15734 * t) * np.clip(t / 0.4, 0, 1) * np.clip((1.6 - t) / 0.4, 0, 1) * 0.0015).astype(np.float32))
    thoom = st(sub_boom(60, 50, 0.5, 0.0, 2)) * 0.4
    y = _seq([(0, y), (0.05, thoom), (0.1, wh)], 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_vhs_tape(rng, sp, action='insert', **_):
    """The tape in the TV cart's VCR: 'insert' (pushed in and threaded: the dummy set's into-VHS), 'eject' (the bus
    set's VHS eject)."""
    key = ('eject',) if action == 'eject' else ('into_vhs',)
    E = _has('vhs', *key) or src('vhs')
    e = _pick(rng, E, 1.0)
    y = fade(pnorm(audio(e)[:n_(3.0)]), 0.003, 0.2)
    return y, onset_s(y, -14), 0.0, False


def r_tape_ff(rng, sp, dur=2.5, stop=True, **_):
    """Fast-forwarding the 1994 tape: the transport's whine (the bus set's tape camera fast-forward / edit / stop,
    the FF part), dur s, and the stop clunk at the end."""
    E = _has('tape_ff', 'fast_forward') or src('tape_ff')
    x = audio(_pick(rng, E, 1.0))
    gl = grains(E[0], 'phrase', gap=0.25, max_len=6.0, keep=-20) if E else []
    body = x[gl[0][0]:gl[0][1]] if gl else x
    y = lp(_fit(body, n_(float(dur)), rng), 8000, 2)
    ev = [(0, fade(y, 0.02, 0.05))]
    if stop:
        clunk = st(modal([180.0, 520.0, 1300.0], [0.03, 0.015, 0.006], [1.0, 0.5, 0.3], 0.1, 4)) * peak(y) * 1.4
        ev.append((float(dur) - 0.02, clunk))
    return _seq(ev, 0.15), 0.0, 0.0, False


def r_tape_slide(rng, sp, dur=1.2, **_):
    """The slowing-tape slide that ends an imitation ("...Clever."): the tape's hiss and the 60 Hz hum diving half a
    speed down over dur, the capstan's flutter wobbling (laid under the voice FX 'mimic', which slides the voice)."""
    d = float(dur); n = n_(d); t = np.arange(n) / SR
    r = 1 - 0.5 * np.clip(t / d, 0, 1) ** 1.3
    ph = 2 * np.pi * np.cumsum(60 * r * (1 + 0.01 * np.sin(2 * np.pi * 6 * t))) / SR
    hum = (np.sin(ph) + 0.5 * np.sin(3 * ph)) * 0.05
    hs = bp(noise(d + 0.1, int(rng.integers(1 << 30))), 1500, 7000, 2)[:n]
    hs = SX_lp_var(hs, r)
    y = st(((hum + hs * 0.08) * np.clip(t / 0.05, 0, 1)).astype(np.float32))
    return fade(y, 0.02, 0.15), 0.0, 0.0, False


def SX_lp_var(x, r):
    """A crude falling low-pass on noise (two fixed low-passes cross-faded by r): the hiss darkening as it slows."""
    a = lp(x, 7000, 2); b = lp(x, 2000, 2)
    w = np.clip((r - 0.5) / 0.5, 0, 1)
    return (a * w + b * (1 - w)).astype(np.float32)


def r_seatbelt(rng, sp, **_):
    """'Belt on.' A seat belt pulled and clicked into its lock (the bus set's seat belt clicks)."""
    P = _bp('belt', 'seatbelt', (), 'phrase', gap=0.15, max_len=1.0, keep=-14)
    y = P.get(rng, rj=0.02)
    return y, onset_s(y, -12), 0.0, False


def r_flag_rope(rng, sp, dur=8.0, **_):
    """'A flag rope, clinking.' The school's flagpole: the halyard's clip clanking on the hollow pole in the night
    wind (the bus set's post-flag cable and the mast rope), dur s."""
    y = _bx('flag_rope', ('cable_clanking', 'rope_clanking'), float(dur), rng, 1.0)
    return fade(hp(y, 200, 2), 0.3, 0.6), 0.0, 0.0, False


def r_broom_bend(rng, sp, dur=1.6, **_):
    """'The handle bends.' The broom handle caught in the closing doors, bowing and creaking (the bus set's bendy
    pole stretch and creak, a fourth down: a thicker stick), the rubber door edges squeezing it."""
    P = _bp('pole', 'broom_bend', ('bendy_pole',), 'phrase', gap=0.15, max_len=2.0, keep=-20)
    y = rate(P.get(rng, rj=0.03), semis(-5.0))
    y = _fit(y, n_(float(dur)), rng)
    y = fade(y, 0.05, 0.2) * np.linspace(0.6, 1.0, len(y))[:, None].astype(np.float32)
    return y, 0.0, 0.0, False


def r_broom_crack(rng, sp, **_):
    """'The broom cracks.' The handle snapping (the bus set's stick snap), a splinter tail, a low thump."""
    P = _bp('snap', 'broom_crack', ('stick_branch', 'snapping'), 'onset', gap=0.1, max_len=1.2, keep=-10)
    y = P.get(rng, rj=0.02)
    th = st(sub_boom(85, 50, 0.35, 0.2, int(rng.integers(1 << 20)))) * 0.4
    y = _seq([(0, y), (0.0, th)], 0.3)
    return y, onset_s(y, -12), 0.0, False


def r_cloth_rip(rng, sp, dur=0.55, **_):
    """'Rip.' Sami's pajamas tearing in the glove (the bus set's T-shirt / thin-material rips), cut to dur."""
    P = _bp('rip', 'cloth_rip', (), 'phrase', gap=0.2, max_len=1.5, keep=-14)
    y = P.get(rng, rj=0.03)
    y = fade(y[:n_(dur)], 0.003, 0.12)
    return y, onset_s(y, -12), 0.0, False


def r_school_bell(rng, sp, dur=4.0, **_):
    """'Three o'clock. The school bell rings.' The classic electric school bell (the doctor set's), heard outside
    the building at night, dur s."""
    E = _has('school_bell') or src('school_bell')
    x = audio(_pick(rng, E, 1.0))
    a = int(np.argmax(np.abs(mono(x)) > 0.2 * peak(x)))
    y = lp(_fit(x[a:], n_(float(dur)), None), 7000, 2)
    return fade(y, 0.003, 0.4), 0.0, 0.0, False


def r_hand_slap(rng, sp, **_):
    """'My hand slaps over his mouth.' (sound fix round 3: the cloth grab alone read as no slap): a palm smacking onto
    a small face, close: a bright skin crack (band noise 900-6000 Hz, 18 ms decay), the palm's dull thump under it
    (140 Hz, 35 ms) and the pajama sleeve's rustle after."""
    r2 = int(rng.integers(1 << 20))
    k = n_(0.09); tt = np.arange(k) / SR
    crack = bp(noise(0.09, r2), 900, 6000, 2)[:k] * np.exp(-tt / 0.018)
    thump = lp((np.sin(2 * np.pi * 140 * tt) * np.exp(-tt / 0.035)).astype(np.float32), 400, 2) * 0.7
    y = (crack / (peak(crack) + 1e-9) + thump).astype(np.float32)
    y = st(fade(y / (peak(y) + 1e-9) * 0.7, 0.002, 0.02))
    g = _cloth_pool().get(rng, rj=0.05, fo=0.06)
    g = fade(lp(hp(g[:n_(0.3)], 200, 2), 3000, 2), 0.02, 0.1)
    return _seq([(0.0, y), (0.05, g * (peak(y) / (peak(g) + 1e-9)) * 0.3)], 0.05), 0.0, 0.0, False


def r_bus_rewind(rng, sp, dur=2.8, **_):
    """'The bus rewinds into the dark.' His bus played backwards and speeding up (the bus set's pass-by, reversed,
    varispeed 0.8 -> 3x), the VHS rewind whine on top (the dummy set's rewinds), a tracking tear; it cuts dead."""
    d = float(dur)
    E = _has('bus_pull_away', 'pass_by') or src('bus_pull_away')
    x = audio(_pick(rng, E, 1.0))[::-1]
    y = _varispeed(np.concatenate([x, x]), 0.8, 3.0, n_(d))
    y = lp(y, 5000, 2)
    R = _has('tape_ff', 'vhs_rewind')
    if R:
        w = excerpt(_pick(rng, R, 1.0), d, rng, 0.3)
        y = y + _lv(hp(w, 500, 2), lufs_int(y) - 4) * np.linspace(0.3, 1.0, n_(d))[:len(w), None].astype(np.float32)
    sk, *_r = r_tape_skip(rng, sp, amount=1.0, frames=3)
    y = _seq([(0, y * np.linspace(0.6, 1.0, len(y))[:, None].astype(np.float32)), (d - 0.1, sk)], 0.0)
    env = np.ones(len(y), np.float32); env[n_(d):] = 0.0
    return fade(y * env[:, None], 0.15, 0.01), 0.0, 0.0, False


def r_clipboard_drop(rng, sp, **_):
    """'His clipboard clatters onto the asphalt.' A hardboard clipboard landing flat and bouncing twice (board
    modes), the metal clip clacking (the doctor set's crocodile clip), the asphalt's grit."""
    rng2 = int(rng.integers(1 << 20))
    ev = []
    for j, (t, g) in enumerate(((0.0, 1.0), (0.16, 0.45), (0.27, 0.2))):
        b = st(modal([150.0, 340.0, 760.0, 1650.0], [0.05, 0.03, 0.012, 0.006], [1.0, 0.7, 0.4, 0.2], 0.2, rng2 + j))
        grit = st(bp(noise(0.05, rng2 + 10 + j), 1500, 7000, 2) * np.exp(-np.arange(n_(0.05)) / n_(0.012))) * 0.3
        ev += [(t, b * g / (peak(b) + 1e-9)), (t, grit * g)]
    try:
        P = _bp('clipb', 'clipboard', (), 'onset', gap=0.06, max_len=0.2, keep=-14)
        ev.append((0.008, rate(P.get(rng, rj=0.03), semis(-3.0)) * 0.5))
    except KeyError:
        pass
    y = _seq(ev, 0.3)
    return y, onset_s(y, -12), 0.0, False


def r_morning_bus(rng, sp, dur=30.0, kids=0.5, **_):
    """BED: the morning bus: bus 9 driving in daylight (the on-board drive), the kids' chatter around (the bus set's
    school walla, low-passed: inside the bus), warm."""
    d = float(dur)
    y = lp(_bx('bus9_drive', ('on_board_driving',), d, rng, 2.0), 5000, 2)
    k = _has('kids_chatter') or []
    if k and kids > 0:
        w = lp(excerpt(_pick(rng, k, 1.0), d, rng, 2.0), 4500, 2)
        y = y + _lv(w, lufs_int(y) + 2) * kids
    return fade(y, 1.0, 1.5), 0.0, 0.0, False


def r_dial_911(rng, sp, kind='call', **_):
    """'Call 911.' kind 'call': the three DTMF keys (9, 1, 1), one ring-back (440 + 480 Hz, 2 s) and the operator's
    pickup click, through the phone's speaker; 'fail': no bars: the call drops (two short low error tones)."""
    def dt(lo, hi, d=0.11):
        t = np.arange(n_(d)) / SR
        e = np.sin(np.pi / 2 * np.clip(np.minimum(t / 0.025, (t[-1] - t) / 0.015), 0, 1)) ** 2   # the owner: no key tone pops in
        return ((np.sin(2 * np.pi * lo * t) + np.sin(2 * np.pi * hi * t)) * 0.25 * e).astype(np.float32)
    if kind == 'fail':
        t = np.arange(n_(0.18)) / SR
        a = (np.sin(2 * np.pi * 480 * t) * 0.3).astype(np.float32); b = (np.sin(2 * np.pi * 380 * t) * 0.3).astype(np.float32)
        y = _seq([(0, st(dt(852, 1477))), (0.22, st(dt(697, 1209))), (0.44, st(dt(697, 1209))), (1.0, st(a)), (1.25, st(b))], 0.2)
    else:
        t = np.arange(n_(2.0)) / SR
        ring = ((np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 480 * t)) * 0.15).astype(np.float32)
        click = st(modal([900.0, 2200.0], [0.004, 0.002], [1.0, 0.5], 0.02, 5)) * 0.4
        y = _seq([(0, st(dt(852, 1477))), (0.22, st(dt(697, 1209))), (0.44, st(dt(697, 1209))), (0.9, st(fade(ring, 0.02, 0.05))),
                  (3.1, click)], 0.2)
    y = eq(bp(y, 300, 3400, 2), ('peak', 1800, 2.0, 1.0))
    return y, 0.0, 0.0, False


def r_his_bus_interior(rng, sp, dur=20.0, **_):
    """BED: inside HIS bus (amber light, every seat dark): his diesel idling far forward, an old fluorescent ballast
    humming in the ceiling, the tape's hiss under everything (his world is a tape)."""
    d = float(dur)
    y, *_r = r_bus_idle(rng, sp, dur=d, rattle=0.4, kind='his')
    y = lp(y, 1800, 2)
    b = st(_ballast(d, rng, 0.3)[:len(y)]) * 0.01
    h = st(bp(noise(d, int(rng.integers(1 << 30))), 1500, 7000, 2)[:len(y)]) * 0.004
    out = y + _lv(b, lufs_int(y) - 6) + _lv(h, lufs_int(y) - 10)
    return fade(out, 0.8, 1.0), 0.0, 0.0, False


def r_school_night(rng, sp, dur=20.0, **_):
    """BED: Larkfield Elementary at 2:57 a.m.: the empty schoolyard (crickets far off, the night air), the flag rope
    clinking on the pole now and then."""
    d = float(dur)
    y, *_r = r_suburb_night(rng, sp, dur=d, dog=0.0)
    y = lp(y, 6000, 2) * 0.7
    f, *_r = r_flag_rope(rng, sp, dur=d)
    y = y + _lv(f, lufs_int(y) - 3)
    return fade(y, 1.0, 1.0), 0.0, 0.0, False


def r_mailbox_unscrew(rng, sp, n=2, **_):
    """'Grandma unscrews the letters off our mailbox.' A small screw backing out (the bus set's flashlight-cap and
    screwdriver unscrews: the threads' little squeaks), then the tin letter coming off with a tink, n times."""
    P = _bp('screw', 'unscrew', ('flashlight',), 'phrase', gap=0.15, max_len=1.0, keep=-18)
    ev = []
    for j in range(int(n)):
        ev.append((j * 1.1, P.get(rng, rj=0.03)))
        ev.append((j * 1.1 + 0.75, st(modal([3100.0, 5400.0, 1250.0], [0.05, 0.03, 0.02], [1.0, 0.5, 0.4], 0.15, j)) * 0.3))
    y = _seq(ev, 0.3)
    return y, onset_s(y, -14), 0.0, False


ALIASES.update({
    'crickets': ('suburb_night', {}), 'night_street': ('suburb_night', {}), 'larch_street': ('suburb_night', {}),
    'house_night_bus': ('suburb_night', {'inside': True}), 'dog': ('dog_far', {}), 'dog_bark': ('dog_far', {}),
    'streetlight_flicker': ('street_flicker', {}), 'flicker': ('street_flicker', {}),
    'air_brake': ('bus_air_brake', {}), 'air_brakes': ('bus_air_brake', {}), 'brakes_hiss': ('bus_air_brake', {}),
    'diesel_idle': ('bus_idle', {}), 'his_bus_idle': ('bus_idle', {'kind': 'his'}),
    'bus9_idle': ('bus_idle', {'kind': 'bus9', 'rattle': 0.0}),
    'bus_door_open': ('bus_door', {'action': 'open'}), 'bus_door_close': ('bus_door', {'action': 'close'}),
    'doors_slap': ('bus_door', {'action': 'close'}), 'door_fold': ('bus_door', {'action': 'open'}),
    'unfold': ('his_unfold', {}), 'ladder': ('his_unfold', {}), 'loudspeaker': ('pa_crackle', {}),
    'pa_on': ('pa_crackle', {'kind': 'on'}), 'pa_off': ('pa_crackle', {'kind': 'off'}),
    'pa_feedback': ('pa_crackle', {'kind': 'feedback'}), 'pull_away': ('bus_pull_away', {}),
    'horn': ('bus_horn', {}), 'bus9_drive_fast': ('bus_fast_night', {}), 'chase': ('bus_fast_night', {}),
    'swerve': ('bus_swerve', {}), 'side_mirror': ('mirror_rip', {}), 'mirror_ripped': ('mirror_rip', {}),
    'screech': ('tire_screech', {}), 'skid': ('tire_screech', {}), 'depot_radio': ('dash_radio', {}),
    'radio_crackle': ('dash_radio', {}), 'fweet': ('whistle', {'kind': 'short'}),
    'fweet_fweet': ('whistle', {'kind': 'short', 'n': 2}), 'whistle_long': ('whistle', {'kind': 'long'}),
    'long_whistle': ('whistle', {'kind': 'long'}), 'click_clack': ('ticket_punch', {}), 'punch': ('ticket_punch', {}),
    'bolt': ('deadbolt', {}), 'walkie_squelch': ('walkie', {'kind': 'squelch'}),
    'walkie_engage': ('walkie', {'kind': 'engage'}), 'walkie_beep': ('walkie', {'kind': 'beep'}),
    'walkie_glitch': ('walkie', {'kind': 'glitch'}), 'lights_out': ('power_down', {}),
    'power_out': ('power_down', {}), 'lights_die': ('power_down', {}), 'lights_on': ('power_up', {}),
    'power_back': ('power_up', {}), 'lights_back': ('power_up', {}), 'run_road': ('run_asphalt', {}),
    'running': ('run_asphalt', {}), 'run_grass': ('footsteps_grass', {'rate': 3.0}),
    'bare_feet': ('footsteps_stairs', {}), 'bare_feet_stairs': ('footsteps_stairs', {}),
    'purr': ('cat_rumble', {}), 'rumble': ('cat_rumble', {}), 'glove': ('glove_squeak', {}),
    'gloves': ('glove_squeak', {}), 'knuckles': ('glove_squeak', {}), 'tape_jump': ('tape_skip', {}),
    'skip': ('tape_skip', {}), 'tracking': ('tape_skip', {}), 'tv_cart': ('crt_on', {}), 'crt': ('crt_on', {}),
    'vhs_insert': ('vhs_tape', {'action': 'insert'}), 'vhs_eject': ('vhs_tape', {'action': 'eject'}),
    'fast_forward': ('tape_ff', {}), 'tape_stop': ('tape_glitch', {'kind': 'stop'}), 'slowing_tape': ('tape_slide', {}),
    'seat_belt': ('seatbelt', {}), 'belt_click': ('seatbelt', {}), 'flagpole': ('flag_rope', {}),
    'flag': ('flag_rope', {}), 'broom': ('broom_bend', {}), 'broom_snap': ('broom_crack', {}),
    'rip': ('cloth_rip', {}), 'pajama_rip': ('cloth_rip', {}), 'tail_rip': ('cloth_rip', {}),
    'bell': ('school_bell', {}), 'three_oclock': ('school_bell', {}), 'rewind': ('bus_rewind', {}),
    'clipboard_clatter': ('clipboard_drop', {}), 'porch_light': ('light_switch', {'kind': 'porch'}),
    'kids_bus': ('morning_bus', {}), 'call_911': ('dial_911', {}), 'no_bars': ('dial_911', {'kind': 'fail'}),
    'his_bus': ('his_bus_interior', {}), 'amber_bus': ('his_bus_interior', {}), 'school': ('school_night', {}),
    'unscrew': ('mailbox_unscrew', {}), 'mailbox': ('mailbox_unscrew', {}),
    'ticket_slide': ('paper_under_door', {'dur': 0.8}), 'ticket_under_door': ('paper_under_door', {'dur': 0.8}),
    'knock_three': ('knock_door', {'n': 3, 'force': 0.75}), 'knocks': ('knock_door', {'n': 3, 'force': 0.75}),
    'knock_knock': ('knock_door', {'n': 2, 'force': 0.6}),
})
KEYWORDS = [('whistle', 'whistle'), ('punch', 'ticket_punch'), ('walkie', 'walkie'), ('brake', 'bus_air_brake'),
            ('bus_door', 'bus_door'), ('fold', 'bus_door'), ('idle', 'bus_idle'), ('horn', 'bus_horn'),
            ('screech', 'tire_screech'), ('mirror', 'mirror_rip'), ('radio', 'dash_radio'), ('glove', 'glove_squeak'),
            ('skip', 'tape_skip'), ('tracking', 'tape_skip'), ('crt', 'crt_on'), ('vhs', 'vhs_tape'),
            ('broom', 'broom_bend'), ('flag', 'flag_rope'), ('bell', 'school_bell'), ('rip', 'cloth_rip'),
            ('clipboard', 'clipboard_drop'), ('belt', 'seatbelt'), ('cricket', 'suburb_night'),
            ('purr', 'cat_rumble'), ('power', 'power_down')] + KEYWORDS


# ============================================================================== THIS film: the Ice Cream film's block
# audio/sfx_ice.py runs in this module's namespace (its names, levels, spaces, aliases and keyword guesses come last,
# so they win); see its header for every name the picture emits.
exec(compile(open(os.path.join(HERE, 'sfx_ice.py')).read(), os.path.join(HERE, 'sfx_ice.py'), 'exec'))
# THIS film, the Walls film ("If Your Little Brother Says Someone Lives In The Walls... DON'T LAUGH"): audio/sfx_walls.py
# (its names, spaces 'in_wall' / 'in_wall_far' / 'vent', aliases and keyword guesses come last, so they win)
exec(compile(open(os.path.join(HERE, 'sfx_walls.py')).read(), os.path.join(HERE, 'sfx_walls.py'), 'exec'))
# THIS film, the Buttons film ("If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET"): audio/sfx_buttons.py
# (tik, ping and this film's foley and beds; its aliases and keyword guesses come last, so they win)
exec(compile(open(os.path.join(HERE, 'sfx_buttons.py')).read(), os.path.join(HERE, 'sfx_buttons.py'), 'exec'))
# THIS film, the Obsession film ("If a Girl Is OBSESSED With Being Your Only Friend... DON'T WRITE YOUR NAME"):
# audio/sfx_obsession.py (Evie's chalk, the song's pings, this film's foley and beds; DEFAULT_GAIN = the cast's levels)
exec(compile(open(os.path.join(HERE, 'sfx_obsession.py')).read(), os.path.join(HERE, 'sfx_obsession.py'), 'exec'))

RECIPES = {k: globals()['r_' + k] for k in NAMES}


# ======================================================================================== public entry points
# the Bunnyman's final mix: footsteps and knocks that are all thump (< 300 Hz) vanish on a phone speaker; after the
# space they get a high shelf until their loudness above 300 Hz is within 12 dB of the whole (measure_mix's phone check)
PHONE_FIX = ('footsteps_wood_inside', 'footsteps_grass', 'footsteps_stairs', 'footsteps_porch', 'footsteps_hall',
             'knock_door')
PHONE_FIX = PHONE_FIX + ICE_PHONE_FIX                  # the Ice Cream film (audio/sfx_ice.py)
PHONE_FIX = PHONE_FIX + WALLS_PHONE_FIX                # the Walls film (audio/sfx_walls.py)
PHONE_FIX = PHONE_FIX + BUTTONS_PHONE_FIX              # the Buttons film (audio/sfx_buttons.py)
PHONE_FIX = PHONE_FIX + OBSESSION_PHONE_FIX            # THIS film (audio/sfx_obsession.py)


def phone_presence(y, floor=-12.0, max_db=12.0):
    """Lift the top of a short foley sound (high shelf at 400 Hz, at most max_db) until its loudness above 300 Hz is no
    more than -floor dB under its full-band loudness: the thump stays, the click a small speaker can play comes up."""
    tot = 0.0
    for _ in range(3):
        L = mom_max(y)
        ph = mom_max(hp(hp(y, 300, 2), 300, 2)) - L
        if not (np.isfinite(ph) and np.isfinite(L)) or ph >= floor or tot >= max_db - 0.05:
            break
        g = min(max_db - tot, floor - ph + 0.5)
        y = eq(y, ('hs', 400, g, 0.7)); tot += g
    return y


def render_event(name, seed=0, space=None, level=0.0, **params):
    """Render one SFX. Returns (stereo float32 at 48 kHz, pre_s). Aliases and keyword guesses go through resolve()
    (a guess prints a warning); KeyError only when no recipe fits. An unknown space falls back with a warning."""
    canon, params, note = resolve(name, params)
    if canon is None:
        raise KeyError(note)
    if note and note != 'alias':
        warn(note)
    name = canon
    sp = space or params.pop('space', None) or DEFAULT_SPACE[name]
    params.pop('space', None)
    sp = resolve_space(sp, name)
    h = int(hashlib.md5(f'{name}|{seed}'.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(h)
    memory = bool(params.pop('memory', False)) or sp == 'memory'
    hard_end = bool(params.pop('hard_end', False))      # a deliberate dead stop (e.g. a tape stop): keep its edge
    y, pre, offs, spaced = RECIPES[name](rng, sp, **params)
    params['hard_end'] = hard_end
    y = st(y)
    if memory:                                            # 21 years ago (film.py: memory=True)
        y = memory_fx(y, rng)
    if not spaced:
        y0 = len(y)
        y = globals()['space'](y, sp, seed)
    if name in PHONE_FIX:
        y = phone_presence(y)
    if not params.get('hard_end'):                        # owner, 23 Nov: no sound pops in or stops dead mid-sound,
        y = fade(y, 0.0, 0.0)                             # whichever path the recipe took (fade() eases loud edges)
        y = no_pop_in(y)                                  # the Walls full mix: a sample cut into its body eases in
    target = REF + LEVEL_LU[name] + SPACE_LU.get(sp, 0.0) + offs + float(level)
    bed = name in BEDS or (params.get('dur') and name in DUR_BEDS)
    L = lufs_int(y) if bed else mom_max(y)
    if np.isfinite(L) and L > -90:
        y = y * 10 ** ((target - L) / 20)
    cap = 10 ** ((PEAK_CAP[name] + float(level) + offs) / 20)     # short transients: momentary loudness under-reads them
    pk = peak(y)
    if pk > cap:
        y = y * (cap / pk)
    return np.ascontiguousarray(y, np.float32), float(pre)


def render(name, seed=0, space=None, level=0.0, **params):
    """Render one SFX as stereo float32 [n, 2] at 48 kHz (see module docstring for params)."""
    return render_event(name, seed, space, level, **params)[0]


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='render one SFX to a wav')
    ap.add_argument('name'); ap.add_argument('out'); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--space'); ap.add_argument('--params', default='{}')
    a = ap.parse_args()
    y = render(a.name, a.seed, a.space, **json.loads(a.params))
    sf.write(a.out, y, SR, subtype='FLOAT')
    print(a.name, round(len(y) / SR, 2), 's', 'peak %.1f dBFS' % db(peak(y)), 'Mmax %.1f' % mom_max(y))
