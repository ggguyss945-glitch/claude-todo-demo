"""characters.py: the cast, their creepy faces and an acting timeline (police v2 cast, the delivery film cast, the
dummy film cast: Mister Winks, Grandpa, the real Walter, young Walter 1974, Mom, Owen, you; and the Bunnyman film cast,
which lives in characters_bunny.py and is run into this module at import: see its BUNNY_API, CAST.md, and the section
"Bunnyman film additions" at the end of this docstring).

Everything draws with skia in the engine's 1920x1080 design space, on any canvas the engine hands a Layer (camera zoom and
render size are already in the canvas matrix). Line weight follows the VISUAL_SPEC: about 8 design px on close-ups and
3 to 4 on wide shots, colour LINE (#1d1f26).

Cast (`CAST`): 'officer' (cap, badge 4471, shoulder radio with coiled cord, bodycam, duty belt), 'officer2' (female
officer, bun), 'double' (your face but wrong: grey coat, scar on his RIGHT, ring on his RIGHT hand, hair parted the other
way), 'you' (hoodie, scar on your LEFT, ring on your LEFT hand), 'mum' (elderly, curly grey hair, glasses, cardigan,
pearls). Left/right are the character's own sides (in a front view the character's left is screen right).

Drawing
    draw(pen, who, x, y_feet, height, pose=None, detail=None, light=None, t=None, aim=None)
        Full body. height = feet to crown in design px (hats and hair go above). pose: Pose, expression name, dict or
        None. detail: 0 wide, 1 medium, 2 close (None = automatic from the on-screen head size, camera zoom included).
        aim=(x, y): while pose.approach rises 0 -> 1 the figure slides so its head reaches that point (the lens axis
        for lean_in toward a doorbell or peephole; pair with Layer(acting.depth(base), ..., ref_depth=base)).
        Returns the Body rig (Body.p3 projects body-unit points if you need to pin a HUD tag to a hand or the head).
    draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None)
        Head-and-shoulders close-up. scale 1.0 = head (crown to chin) 600 design px, head centre at (cx, cy) (eyes sit
        about 0.04 head heights above it). The torso, arms and hands are the real rig, so gestures (radio, hand to
        glass, held props) work in close-ups too. pose.approach > 0 grows the face toward the lens (lean_in).
    draw_head(pen, who, cx, cy, size, pose=None, detail=2, light=None)   head only, size = head height in design px.
    draw_hand(pen, who, x, y, size, shape='open', angle=0, side=1, pose=None)   a single hand (shape: mitt, fist, point,
        open, flat (pressed on glass), grip). draw_prop(pen, name, x, y, size, angle=0): 'radio', 'card', 'notebook',
        'key' (orange key ring), 'phone', 'photo', 'badge'.
    hud_phone_hand(pen, w, h, skin, a, front): drop-in replacement for engine.hud._hand
        (`hud._hand = characters.hud_phone_hand`).
    light = dict(rim='#9fb6ff', rim_a=70, side=1, key=0.0): a cool rim on one side; key in -1..1 darkens (night) or
        warms (porch lamp) the skin. police_flash red/blue on faces: light=dict(rim='#ff3040', rim_a=120, side=-1).

Poses
    Pose(**params) holds every animatable number (see POSE_DEFAULTS) plus discrete fields (hand shapes, props).
    Pose.expr(name) / EXPR[name]: 'neutral', 'calm_smirk', 'polite', 'creep_smile', 'wide_grin', 'stare', 'dead_stare',
        'nervous', 'fear', 'angry', 'whisper', 'shout', 'scream', 'cry', 'grin_cry', 'shock', 'sad', 'suspicious',
        'sweaty', 'blank', 'talk_smile'.
    Pose.lerp(a, b, k) blends two poses continuously.
    View: pose.turn (body yaw) and pose.h_turn (head yaw) in quarter turns: 0 front, +-0.5 three-quarter (+ = facing
        screen right), +-1 profile, +-2 back. VIEWS = {'front':0, 'q_right':0.5, 'q_left':-0.5, 'profile_right':1,
        'profile_left':-1, 'back':2}.

Speed (2560x1440, one process, best of runs on a shared machine): full body 18-27 ms, bust filling the frame 36-51 ms.

Acting (timeline builder; every clip is eased, sub-frame continuous and layered over breathing, blinks and noise)
    a = Acting('officer', seed=1, height=700, expr='neutral', blink=None)   blink None = cast default (the officer and
        the double never blink; you and mum blink 1-2 frames).
    a.at(t) -> Pose          a.events -> SFX events [{t, name, gain_db, pan, params}]   a.depth(base, k) -> f(t)
    Non-sound clips return the Acting (chainable); clips that make a sound return their list of events.
    a.expr(name, t0, t1=None, fade=0.35)             blend to an expression (t1 None = hold)
    a.idle(t0, t1)                                   restore plain idle look-around
    a.stare(t0, t1=None)                             pupils shrink and lock on the lens, no blinks, everything stills
    a.creep_smile(t0, dur=4.0, t1=None, amount=1.0)  slow grin growth (teeth appear at ~40%), eyes do not smile
    a.wide_grin(t0, t1=None, fade=0.6)               too-wide toothy grin with gums, tiny pupils
    a.head_tilt(t0, angle=32, dur=1.6, t1=None, back='ease')  tilt beyond natural; back='snap' snaps upright at t1
    a.snap_turn(t, frm=1.0, to=0.0)                  head snaps to the lens (spring overshoot), eyes lead, body follows
    a.lean_in(t0, dur=2.5, t1=None, amount=1.0)      torso leans to the lens, face grows (pose.approach 0..1)
    a.knock(t0, n=3, spacing=0.32, side=0.0) -> [knock_door events]   side: -1/+1 door to screen left/right, 0 = lens
    a.talk(intervals, text=None, intensity=1.0)      visemes from text (vowels/consonants) or pseudo-syllables;
        intervals: [(t0, t1)] or [(t0, t1, text)]; a.talk_lines(timeline_lines, who='O') takes timeline.json lines
        (who may be a code or a tuple of codes: 'winks' talks on ('K', 'U', 'R') and on 'G' lines with fx 'dummy')
    a.radio_to_mouth(t0, t1) -> [radio_click x2, police_radio_squelch]   hand keys the shoulder mic, head dips to it
    a.press_bodycam(t, on=True) -> [bodycam_beep]    finger presses the chest camera; LED follows pose.cam_on
    a.hold_up(prop, t0, t1, side=-1) -> [paper|...]  raises a prop toward the lens (side -1 = right hand)
    a.hand_on_glass(t0, t1, side=1) -> [knock_door soft]   palm comes at the lens and flattens (pressure-pale fingertips)
    a.walk(t0, t1, x_from, x_to, facing=None, surface='porch') -> [footsteps]   real walk cycle; pose.dx in design px
    a.turn(t0, to, dur=0.6) / a.turn_back(t0, dur=0.45)   body+head yaw with overlapping action
    a.cry(t0, t1=None, smile=False) -> [breath sobs] tears stream, shoulders sob; smile=True = smiling while crying
    a.scream(t0, t1)                                 huge mouth, head shake, tiny pupils
    a.nervous_glance(t0, n=2, side=-1, dur=1.4)      eyes dart to the side and back with quick blinks
    a.twitch(times, amp=1.0)                         sudden jerks (head, eyes, shoulder) with spring settle
    a.freeze(t0, t1) / a.jerk(t, amp=1.0)            total stillness (even breathing), then a jerk back to life
    a.look(t0, x, y, dur=0.12) / a.head_down(t0, t1=None, amount=1.0) / a.sit(t0, t1=None) / a.point(t0, t1, side=-1)
    a.blink(t) forces a blink; hands: hr_* = character's right (screen left in a front view), hl_* = left
    a.set(t0, t1, fade, **params)                    any pose numbers over a window (escape hatch)
    Clips layer in the order they are added (later ones win where they overlap). Overlapping action is built in: eyes
    lead the head, the head leads the body, the shoulder-mic cord, drawstrings and skirts swing from lagged motion
    (pose.sec_x). Events are dicts {t, name, gain_db, pan, params, who} using the required SFX names (knock_door,
    radio_click, police_radio_squelch, bodycam_beep, paper, footsteps_porch / footsteps_wood_inside, breath).

v2.1 additions (character fixer; everything above still works unchanged)
    Acting / lip sync
    a.talk(intervals, text=None, intensity=1.0, env='auto', words='auto', lead=0.02)
        The mouth now follows the real voice: env='auto' samples the vo_en.wav RMS envelope (voice_envelope(), cached as
        $S/pov2/cache/vo_env_*.npy), shut below -40 dBFS and normalised per line; words='auto' places each word's visemes
        in its own ASR window (asr_cache en_words). Grins talk through the teeth (jaw drops on top of the grin), shout /
        scream modulate around their open base, so no line is mouthed with a frozen mouth. Film check (crit sync.py, 31
        visible lines): zero-lag r median 0.16 -> 0.71, p10 -0.19 -> 0.54, frozen-mouth lines 4 -> 0 (best lag now -1
        frame: the mouth leads the voice by ~1 frame). Pass env=None, words=None for the old behaviour.
        CAST[who]['talk'] scales the mouth per character (officer2 0.62: flat, polite).
        voice_envelope(path=None) -> 100 fps dBFS array; voice_words(path=None) -> [(word, t_start)].
    a.snap_turn(t, frm=1.0, to=0.0, hold=0.6, body=0.35, until=None, release=0.5)
        Now OVERRIDES the head yaw (it runs after every other clip, whatever the order they were added in) and holds `to`
        after the snap (until None = for good). A held look_side() underneath no longer wins: yaw at snap+0.5 s = 0.0.
        frm=None starts from the current yaw.
    a.knock(t0, n=3, spacing=0.32, side=0.0, hand=None, strength=1.0, reach=0.72)
        side +1/-1 (door slab to screen right/left of the doorbell): the near hand (hand=None picks it) reaches out at
        shoulder height (0.72 arm length) with a forearm snap per hit, a 2-4 deg body rock, head locked on the lens.
        side 0 = knock ON the lens (peephole / doorbell glass): fist at face height in front, growing ~1.3x per hit; the
        events carry params lens=True -> add a ~1.5 % cam.hit at each event t. Events pan 0.35*side for side knocks.
    a.radio_to_mouth(t0, t1, side=1, tilt=13.0)   the shoulder speaker-mic comes up beside the mouth in the hand (the coiled
        cord follows), the head tilts 13 deg into it with the eyes locked on the lens, the thumb squashes the PTT key on
        each click. Frame busts at cy ~ 470, scale <= 0.9 so the mic is in frame.
    a.phone_to_ear(t0, t1=None, side=1, fade=0.5, tilt=6.0)   phone pressed to the ear in busts and full body: wrist under
        the ear, elbow forward and down, the dark back of the phone on the cheek, the hand wrapped round it. The old
        film.phone_ear() pose (prop 'phone', hand raised near the shoulder) is detected and drawn the same way, so
        existing shots are fixed without changes (no more purple spike).
    a.blink(t, dur=0.067) / a.blink_burst(t0, n=4, dur=1.0)   blinks are 1-2 frames at 30 fps now (shut in 17 ms, open by
        67 ms); ~28 % of the scheduled blinks of you / mum are nervous doubles.
    a.life(t0, t1=None, amount=0.0)   scales the new always-on idle life. Acting(..., life=1.0) sets it per actor.
        Creepy cast (officer, officer2, double) and anyone staring: breathing never stops, slow +-3 deg head drift, a head
        re-settle (pose swap, 1.5-4.5 deg) every 2-3.6 s, slow weight shifts, and (creepy cast) a small involuntary twitch
        every 4.5-8.5 s; no blinks. Scared cast (you, mum): quick nervous head re-orients every 1.3-2.6 s scaled by the
        fear in the face, and a shiver with pose.tremble. freeze() still stops everything. Crit activity metric on the
        same film plan, old -> new characters.py: officer frozen 42 -> 36 %, you 67 -> 59 %, double 49 -> 41 %, mum 63 -> 53 %,
        officer2 56 -> 51 %; holds >= 2 s 9/8/7/5/1 -> 4/2/2/1/0 (critic's v2 baseline: officer 65 %, you 91 %).
        Use a.life(t0, t1, 0) for a deliberate dead-still beat (or freeze()).
    a.hand_to_mouth(t0, t1=None, side=-1, fade=0.45, shock=True)   hand over the mouth (stifled sob / shock), eyes wide.
    a.wipe_tears(t0, side=1, dur=1.3)   back of the fingers wipes under one eye and out across the cheek.
    a.glasses_off(t0, t1=None, side=1)  mum takes her glasses off at t0 + 0.55 and holds them at chest height (back on at t1).
    a.creep(t0, t1, tilt=8.0, jerk_at=None, side=None, sway=5.0)   one-call weird beat for a held creepy shot: slow
                                        over-long tilt across the shot, weight shift, a jerk at 55 % (critic's creep()).
    a.impatient(t0, dur=2.6, side=1)    weight shift, glance away to the street, sharp look back, twitch on arrival.
    a.flinch(t, amp=1.0)                startle on a knock / hit / countdown number: head jerks back, shoulders up, 2-frame
                                        squeeze, wide-eyed settle. Good on 'you' at every knock event time.
    Pose fields: life, hl_ear / hr_ear (phone at the ear), hl_scale / hr_scale (hand size, the lens knock uses it), specs
    (mum's glasses on the face).

    Faces
    Rounder egg / bean skulls with tapered jaws for the whole cast (officer jaw@82 88 -> 76, mum 92 -> 76; silhouette fill
    0.876 -> 0.82); grins push the cheeks out ~5 %. EXPR 'scream' = terror (O mouth with corners pulled DOWN, bottom teeth
    only, up-slanted pinched brows, tremble); 'fear' / 'shout' / 'shock' get downturned corners too. 'you' / double
    brows are drawn over the fringe (never hidden). Tears are thin pale-blue streaks with a white highlight that stop at
    the jaw outline and drip from it (below mum's glasses rims). Wrinkles are a few clean folds (forehead folds only
    when the brows lift); pore texture halved. officer2's lips are muted (#8f6466) and her talk is 0.62.

    Hands and inserts
    draw_hand(...) shapes now have real fingers (3 phalanges, nails, knuckle creases, one shade step): 'open' (back of the
        hand), 'flat' (palm, pressed pads), 'fist' (knuckles + wrapped thumb), 'point', 'grip' (4 finger rolls round a prop,
        thumb on the side), 'relaxed' (fingers together), 'palm4' (no thumb), 'mitt'. The ring is a gold band ON the
        ring finger with a glint. Angle convention unchanged: angle 0 = fingers DOWN, 180 = fingers up.
    draw_hands_lap(pen, who, cx, cy, size, rub_phase=0.0, ring_side=None, t=0.0, detail=2, light=None, cuffs=True,
                   thread=False, rub_amp=12.0, rub=True) -> dict(ring_xy=(x, y) design point of the ring, ...)
        Two hands folded in the lap, arms coming in from both top corners: the lower hand back up (it wears the ring when
        ring_side is +1 = character's left = screen right, -1 = screen left; None or 0 = no ring), the other cradling it
        with its thumb over the base of the ring finger, rocking +-12 deg with rub_phase (None = still). size = one hand
        length in design px (the group spans ~2.4x size). cuffs=False if the set already draws sleeves; thread=True hangs
        the lit loose thread from the lower cuff (pass p.get('thread')). Use ring_xy for the RING tag leader line.
    draw_palm_on_glass(pen, who, x, y, size, press=1.0, t=0.0, angle=0.0, side=1, alpha=1.0, halo=1.0, slide=0.0)
        Open hand pressed on glass, FINGERS UP at angle 0, 5 spread fingers, pale flattened pads, darker pressed rim,
        condensation halo. (x, y) = wrist; slide = extra y for the slow slide down the glass; alpha fades it. For the
        back-seat window put it beside the face (x ~ face x + 0.7 head width) and drop act=hand_on_glass so there is
        one hand only.
    hud_phone_hand (installed as engine.hud._hand) draws real fingertips curling round the phone edge and a thumb.
    Props: 'mic' (shoulder speaker-mic), 'phone_back' (dark back of a phone).
    Creepy cast (lock >= 0.5): a smile never squints their eyes (the eyes do not smile). 'flat' hands with press > 0 are
    drawn pale with a darker pressed rim (hand_on_glass).
    Self-test: python3 characters.py --selftest (snap override, blink length, phone at the ear, lip-sync correlation).

Delivery film additions ("If A Delivery Driver Rings Your Doorbell At 3 AM..."; the police cast above still works)
    Cast: 'driver' (Nightline courier: brown shirt, crescent NIGHTLINE patch, name tag NO. 307, brown cap with a long bill
        whose shadow hides the eyes, work boots, keys on a carabiner; the officer's creepy face, gaunt, never blinks),
        'mom' (the police mum in a robe, no glasses, slippers), 'lily' (8: big head, bob with bangs, star clip, moon-print
        pajamas, bare feet), 'dad' (21 years ago: flannel, moustache), 'you' (now in socks). Times below are FILM time.
    Driver smile: DRIVER_STAGES 0..5 + 'off'; DRIVER_ARC = [(t, stage, transition s)] applied under every clip (Acting
        arc=None uses the cast's arc, arc=False switches it off); driver_stage(t) -> params; a.smile_stage(t0, stage, t1)
        overrides a window; a.smile_arc(arc|None). talk(..., lag=None): the driver's mouth lags the voice 0.2 s.
    Driver clips: carry_tablet(t0, t1, side) | hold_tablet_up(t0, t1, side, screen, height) | ring_bell(t0, side=0) ->
        doorbell_chime | tap_label(t0, n, side, spacing, target) -> box_tap | tilt_box(t0, t1, side) -> box_creak |
        lean_close(t0, dur, t1, tilt, side) | listen_tilt(t0, t1, side, angle) | slow_look_side(t0, dur, side, back) |
        look_at_box(t0, t1, side) | set_box_down(t0, dur, side) -> box_drop, box_scrape | take_photo(t0, side) ->
        camera_shutter (pose.tablet_flash) | walk_away(t0, t1) -> footsteps | climb_in(t0) -> van_step, car_door_close |
        reach_up(t0, t1, side, prop, stretch, grow) (the too-long arm: stretch 1 = twice its length) |
        eye_flash(t0, dur) -> stinger (pose.eyeshine: pupils shine white over the brim shadow) | reach(t0, t1, side, out,
        down, fwd, shape) generic.
    Family clips: mom squint_light, reach_chain -> chain_lock rattles, hands_over_mouth -> breath gasp, shaking_hand,
        sit_floor; tremble(t0, t1, amp); Lily lean_out(t0, t1, side, reach_t) -> touch_tap, sleepy; dad sign -> touch_tap,
        stylus_scribble, drop_keys -> keys_drop; you look_at_phone, catch_wrist -> cloth_rustle, hold_close, push_door ->
        door_creak. escalate(a, t0, t1, kind) = the film's acting arc (driver twitches by act, none while his face is
        still 435.8-446.4 s; FEAR_ARC tremble for you / mom).
    Props: draw_box(pen, x, y, h, BoxActing.at(t), t, view, label, to, tape) + BoxActing (knock(t0) two-then-one ->
        box_knock, knock_loop(t0, t1, period, accel), tilt, slide -> box_scrape, cut); draw_box_inside (sunrise, rusted
        keys); draw_tablet(pen, cx, cy, size, screen 'sign'|'sent'|'camera'|'off'|'glow', sig None|'initial'|'lily', ink,
        ts, glitch, flash); props 'tablet' / 'tablet_back' / 'stylus' / 'keys_dad' in hands (pose.tablet_screen,
        tablet_ink, tablet_flash); draw_keys_bowl(pen, x, y, size, drop, hand) (KEYS_DROP_IMPACT); draw_keyring(rust).
    Helpers: hand_pos(who, pose, side, x/y_feet/height | cx/cy/scale) -> (wrist, fingertip); draw_arm(...) draws one
        arm alone (a figure clipped by a window sill with its reaching arm over the sill). light keys: under (screen /
        tablet uplight colour) + under_a, brim (driver's bill shadow strength, default 1).
    Pose fields: eyeshine, floor, tiptoe, hl_/hr_stretch, hl_/hr_shake, tablet_ink, tablet_flash, tablet_screen.
    See CAST.md for the beat map and sheets (W/cast/*.jpg, tools/cast_sheets.py).

Dummy film additions ("If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH"; everything above still works;
the delivery 'mom' / police 'you' designs live on as 'mom_delivery' / 'you_police'). Times are FILM time.
    Cast: 'winks' (Mister Winks, a 0.85 m vent figure: lacquered ivory wood, carved auburn hair with a hard side part,
        faded rouge, glossy staring eyes with small near-black irises under low wooden lids, heavy sharply arched black-brown
        brows angled down to the nose, a tight wide grin in thin dark-red lips and the LOWER JAW BLOCK on two marionette
        slot lines, a burgundy usher's jacket with brass buttons and gold braid, a pillbox cap, white gloves, the usher's
        flashlight, a slot in his back), 'grandpa' (86, the thing: bald with a white fringe, big ears, the hooked Kemp
        nose, bushy white brows, moss cardigan; too-still smile, lips barely move: talk 0.3), 'grandpa_bed' (the same in
        a hospital gown, gaunt), 'walter' (the real Walter in that body for one hour: lucid, terrified, a scared cast),
        'walter74' (young Walter on the 1974 tape: pompadour and sideburns, powder-blue suit, wide tie; lips never move:
        talk 0), 'mom' (mid 40s: long camel coat, teal scarf, dark low bun), 'owen' (9: cowlick, big ears, a missing front
        tooth, mustard hoodie), 'owen_new' (the thing in Owen's body at the end: never blinks, lips barely move), 'you'
        (16: dark curtain bangs, denim jacket over a grey hoodie). Heights: winks 0.85 m (DUMMY_M), grandpa 1.72, walter74
        1.78, mom 1.65, you 1.74, owen 1.32.
    Mister Winks's face: pose.jaw (0 shut .. 1 wide: the block drops straight down and shows the black hollow), lid_l /
        lid_r (wooden lids; his LEFT is the wink eye), grin_w (painted grin width by stage), crack (varnish cracks),
        desperate (the soul inside looking out: pleading brows, wet eyes), tears, gloss (varnish shine), lock (the glass
        eyes follow the lens). The arc is automatic: WINKS_ARC = [(t, stage, transition)] with WINKS_STAGES 0..5 (the grin
        widens, the stare hardens), 'asleep' (lids shut, 567.1-655.6), 'owen' (Owen inside, from 655.6), plus 'show' /
        'tape' for the 1974 tape (Acting('winks', arc=WINKS_TAPE_ARC)); winks_stage(t), stage_at(t, arc, stages, keys),
        a.smile_stage(t0, stage, t1) overrides a window.
    Talking: a.talk(...) on 'winks' drives the JAW (hard open / snap shut on each syllable from the local contrast of the
        voice envelope) and adds a 'dummy_clack' event (kind speech, -14..-8 dB) at every snap shut.
    Winks clips: jaw_drop(t0, amount) -> dummy_jaw | jaw_hang(t0, amount) | clack(t, dur) -> dummy_clack (dur > 0.3 = the
        slow close; clacks end any drop / hang) | wink(t, side, hold) / blink_click(t) -> eyelid_click x2 | try_wink(t, gap,
        hold) -> eyelid_click x2 (both lids close: Owen inside) | lids(t0, t1, amount, side) | eyes_open(t0, dur) ->
        eyelid_click | doll_turn(t0, to, dur, steps, frm, until, body) -> wood_creak per step (ratchet) | head_turn_180(t0,
        dur, frm, to) -> wood_creak (grind, params dur) | head_snap(t, to) | tick(t, tilt) -> wood_creak | sit_dummy(t0,
        t1, hands 'knees'|'table'|'limp') | glove_lift(t0, side) -> wood_creak, cloth_rustle | fingers_curl(t, side) |
        elbow_bend(t, side) -> wood_creak | stand_on_chair(t0) -> wood_creak x3, footsteps_wood_inside | torch_on(t, ang,
        side, t1, hold 'side'|'up'|'lens'|'chin') -> flashlight_click | torch_sweep(t0, t1, a0, a1) | puppet(t0, t1, look)
        (worked on a lap) | carried(t0, t1, recline) | fall_face_down(t0) -> dummy_thud | face_down(t0, t1) |
        paper_out(t0) -> paper (the P.S. slides out of his back slot; pose.slot_paper).
    Family clips: mom open_latches(t0) -> case_latch x2, smell_mug(t0, t1, side, pale_at) -> breath sniff / gasp,
        pull_dummy(t0, t1) -> cloth_rustle per pull, grab_keys(t0) -> keys_drop (jangle), laugh_soft(t0); Owen snort(t) ->
        snort, try_wink_kid(t), jump_hug(t0) -> footsteps, wave(t0, t1), hold_mug(t0, t1, sip=[t]) -> sip, doorway_smile(t0);
        you grab_dummy(t0) -> cloth_rustle, hand_inside(t0) -> cloth_rustle, squeezed([t, t, t]) -> hand_squeeze x3,
        hold_dummy(t0), kneel(t0), clamp_mouth(t0) -> cloth_rustle, spin_around(t0) -> whoosh; Grandpa tuck_in(t0),
        squeeze_hand(t0, n=3) -> hand_squeeze x3, in_bed(), grab_wrist(t0) -> cloth_rustle (the real Walter); vent_pose(t0,
        t1, side, free) and showman(t0, t1) for whoever works him (Grandpa in bed, young Walter, Owen). EXPR adds 'lucid',
        'kid_grin', 'still_smile', 'showman'.
    Composites: draw_lap(pen, who, x, y_feet, height, pose, dpose, side, m, ...) (the person, the dummy on that knee, the
        operating hand hidden in his back); draw_carry(pen, who, ..., pose, dpose) (cradled across your arms); lap_anchor(who,
        pose, side, ...) -> (x, y) of the knee top; pose.perch (y_feet = the surface a sitting figure sits on: chair seat,
        stair, shelf, lap), pose.recline (tip the figure about its hips), pose.lie (1 face down on the floor, -1 face up);
        draw_bust keeps a seated / kneeling figure's face where the bust was asked for.
    Flashlight: prop 'flashlight' in a hand turns with pose.torch_ang (0 up); torch_pos(who, pose, side, ...) -> (x, y,
        angle) of its lens; draw_torch_beam(pen, x, y, ang, length, spread, a, t, lens) draws the cone or, with lens 1, the
        glare into the camera; light=dict(under='#fff1c8', under_a=210) is the flashlight under his chin. Prop 'mug'
        (steam with pose.steam), 'key'.
    escalate(a, t0, t1, kind) now also gives Mister Winks his wooden ticks (WINKS_TICKS, none in WINKS_QUIET or with
        kind='worked') and you / mom / owen the dummy film's FEAR_ARC tremble.

Bunnyman film additions (characters_bunny.py; everything above still works; the dummy film's 'mom' / delivery 'dad' live on
as 'mom_dummy' / 'dad_delivery'). See CAST.md for the cast table, the staging rules and the beat map.
    Cast: 'bunny' (now: matted, one ear snapped, rust-brown belly, rips, dead matte glass eyes, zipper in the back),
        'bunny87' (the clean 1987 mascot), 'mom' (Laurie, 43), 'mom_hosp' (the narrator in Mom's body), 'june',
        'june_dress', 'laurie87', 'narrator', 'narrator_new' / 'narrator_neat' (the thing in the narrator's body),
        'narrator_kid', 'grandma', 'dad', 'dale' (the face under the mask), 'cop', 'cop2', 'doctor', 'nurse'.
        height_px(who, px_per_m) keeps everyone to scale. v3 faces: iris eyes with resting lids, tapered brows, line
        weights that follow the on-screen head size; new hair styles; outfits cardigan3, hoodie3, pj3, dress3, gran3,
        jacket3, labcoat3, scrubs3, gown3, neat3. The Bunnyman's suit: _bunny_figure / _bunny_head, paws, pose.unmask.
    Body3 (now the global Body): pose.seat (hips on a seat, feet on the floor), pose.knees (kneel style 0/1/2), pose.run,
        and a planted walk for the v3 cast. v3 arms (_arm_data) drop the elbow when a hand is held forward.
    World-space staging (a.place(x, y_floor) first): a.where(t, part), a.look_at(t0, target, t1, dur, z, body),
        a.reach_to(t0, side, target, t1, dur, z, contact), a.point_at, a.head_to, a.hand_over, a.hold_hand, a.smooth_hair,
        a.sit_on / a.seated / a.stand_up, a.kneel_down, a.crouch, a.run, a.climb, a.lie, a.dead, a.face, a.wave,
        a.hum, a.knock_pattern, a.eyes_shut, a.unmask, a.mama, a.drag_hatchet, a.open_egg; targets are points, callables,
        (actor, part) or PropTrack; misses land in a.misses; a.foot_gap(t) checks the feet. Solves run in a post pass
        after the idle life, so contact holds on the drawn pose.
    Props: PROPS3 (egg, egg_gold, egg_top / egg_bot / egg_bot_ring, ring, hatchet, maglite, diary, diary_open,
        dress_tiny, drawing, basket, key, clipboard) in real centimetres; draw_prop3(pen, name, x, y, px_per_cm);
        PropTrack (rest / held / gone keys) + a.pick_up / a.put_down / a.give / a.hold_prop; hand shape 'oven' (mitts);
        torch_pos3(actor, t, side) for the maglite beam; draw_crayon_drawing(pen, cx, cy, w); draw_arm (v3 + paws).

Typical use in a shot
    a = Acting('officer', seed=7, height=700); a.stare(0); a.creep_smile(1.0, 3.5); ev = a.knock(0.4)
    Layer(a.depth(1.0), lambda pen, t: draw(pen, 'officer', 960, 905, 700, a.at(t), aim=(960, 470)), 'officer', ref_depth=1.0)
    Close-up: Layer(1.0, lambda pen, t: draw_bust(pen, 'officer', 960, 560, 1.1, a.at(t), light=dict(rim='#9fb6ff')), 'face')
"""
import math, os, sys
from contextlib import contextmanager
import numpy as np
import skia

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)
from engine.core import (CFG, LINE, col, mix, Pen, smooth, poly, rect, rrect, oval, inter, union, minus, clamp, lerp, prog,  # noqa: E402
                         set_render_size,
                         ease, ease_in_out, ease_out_cubic, ease_in_cubic, ease_out_back, ease_out_quad, spring, noise1, hash01,
                         tex, text)
from engine.core import _ramp, _stops_key                                                   # noqa: E402

PI = math.pi
INF = float('inf')
VIEWS = {'front': 0.0, 'q_right': 0.5, 'q_left': -0.5, 'profile_right': 1.0, 'profile_left': -1.0, 'back': 2.0}

# ====================================================================================================== cast
_POLICE = dict(shirt='#1f2a44', shirt_sh='#121a2d', shirt_hi='#33446a', trousers='#161d30', trousers_sh='#0d1220',
               cap='#18213a', cap_sh='#0f1528', visor='#0a0c11', tie='#0e121c', gold='#c9a64a', gold_sh='#86682a',
               gold_hi='#f2dc94', silver='#a7aeb7', silver_sh='#5f666f', black='#15161a', black_hi='#3a3d45',
               patch='#24386e', patch_rim='#c9a64a', shoes='#0c0c0f', belt='#0f1013')

CAST = {
    'officer': dict(
        outfit='police', hat='cap', hair='short', sex='m', hh=178.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 56, 80, 95, 100, 99, 91, 76, 54, 29, 0],
        eye_dx=44, eye_y=-10, eye_r=20.5, pupil=0.78, brow_th=11, nose_len=26, mouth_y=60, mouth_w=24,
        skin='#c4ada2', skin_sh='#937b76', skin_dp='#5e4a50', blush='#d4979b', lip='#97706f', stubble='#4f5966', stub=0.6,
        hair_c='#41352f', brow_c='#221c1c', bags=1.0, age=0.8, blink_rate=0.0, lock=1.0, micro=0.5, breath=0.8,
        scar=0, ring=0, part=0, lashes=0.0,
        body=dict(sh=130, ch=124, wa=106, hip=110, arm=(52, 42), leg=(66, 52), neck=50, hand=1.0),
        cloth=dict(_POLICE)),
    'officer2': dict(
        outfit='police', hat='cap', hair='bun', sex='f', hh=176.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 50, 72, 87, 92, 90, 81, 64, 43, 22, 0],
        eye_dx=41, eye_y=-8, eye_r=19.5, pupil=0.85, brow_th=8, nose_len=20, mouth_y=58, mouth_w=21,
        skin='#c5ae a0'.replace(' ', ''), skin_sh='#937a73', skin_dp='#6a5257', blush='#dc9a9e', lip='#8f6466', stubble=None, stub=0, lips=0.6, talk=0.62,
        hair_c='#2b1d19', brow_c='#2b1d19', bags=0.55, age=0.35, blink_rate=0.0, lock=1.0, micro=0.45, breath=0.7,
        scar=0, ring=0, part=0, lashes=1.4, earrings=True,
        body=dict(sh=114, ch=110, wa=90, hip=104, arm=(44, 36), leg=(58, 46), neck=41, hand=0.88),
        cloth=dict(_POLICE, shirt='#22304d', shirt_hi='#38496f')),
    'you': dict(
        outfit='hoodie', hat=None, hair='messy', sex='m', hh=178.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 50, 74, 91, 97, 96, 86, 69, 47, 24, 0],
        eye_dx=43, eye_y=-8, eye_r=20, pupil=1.0, brow_th=9.5, nose_len=22, mouth_y=58, mouth_w=22,
        skin='#c9aa98', skin_sh='#97786c', skin_dp='#634c4b', blush='#dd9b97', lip='#a06f6a', stubble='#5a5550', stub=0.25,
        hair_c='#382821', brow_c='#2d211c', bags=0.6, age=0.3, blink_rate=0.35, lock=0.0, micro=1.0, breath=1.0,
        scar=1, ring=1, part=1, lashes=0.0,
        body=dict(sh=120, ch=118, wa=108, hip=106, arm=(54, 46), leg=(58, 48), neck=46, hand=1.0),
        cloth=dict(top='#34443f', top_sh='#212d2a', top_hi='#4b5f58', trousers='#2a3347', trousers_sh='#1a2030',
                   shoes='#b9b3a6', shoes_sh='#7c776d', string='#cfc9bb')),
    'double': dict(
        outfit='coat', hat=None, hair='messy', sex='m', hh=178.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 50, 74, 91, 97, 96, 86, 69, 47, 24, 0],
        eye_dx=43, eye_y=-8, eye_r=20.5, pupil=0.62, brow_th=9.5, nose_len=22, mouth_y=58, mouth_w=22,
        skin='#bcaea8', skin_sh='#8a7c7a', skin_dp='#584a52', blush='#c99a9c', lip='#8f6f6e', stubble='#5a5a5c', stub=0.3,
        hair_c='#382821', brow_c='#2d211c', bags=0.95, age=0.35, blink_rate=0.0, lock=1.0, micro=0.3, breath=0.5,
        scar=-1, ring=-1, part=-1, lashes=0.0,
        body=dict(sh=122, ch=118, wa=108, hip=110, arm=(52, 44), leg=(56, 46), neck=46, hand=1.0),
        cloth=dict(coat='#6b6f74', coat_sh='#4c5056', coat_hi='#8a8f95', shirt='#26282e', trousers='#23252b',
                   trousers_sh='#16171b', shoes='#111113', button='#2c2d31')),
    'mum': dict(
        outfit='cardigan', hat=None, hair='curly', sex='f', hh=190.0,
        head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 52, 77, 94, 100, 99, 91, 76, 54, 28, 0],
        eye_dx=42, eye_y=-6, eye_r=18.5, pupil=1.0, brow_th=7, nose_len=24, mouth_y=60, mouth_w=21,
        skin='#c8ab9f', skin_sh='#96786f', skin_dp='#6a5153', blush='#de9c9c', lip='#a5716f', stubble=None, stub=0, lips=0.45,
        hair_c='#c2beba', brow_c='#8d8580', bags=0.85, age=1.0, blink_rate=0.3, lock=0.0, micro=1.0, breath=1.0,
        scar=0, ring=1, part=0, lashes=0.6, glasses=True,
        body=dict(sh=100, ch=108, wa=104, hip=112, arm=(42, 34), leg=(38, 32), neck=34, hand=0.85),
        cloth=dict(top='#6c5270', top_sh='#4c3850', top_hi='#86688a', blouse='#ddd3c2', blouse_sh='#b3a893',
                   skirt='#3a3342', skirt_sh='#27222d', legs='#a58e86', shoes='#2a2220', pearl='#ece6dc')),
}
CAST['officer2']['skin'] = '#cdb3a6'

# ---------------------------------------------------------------------------------------- delivery film cast
# "If A Delivery Driver Rings Your Doorbell At 3 AM...": the Nightline driver (built on the officer's creepy face: locked
# unblinking stare, ashen skin, deep bags; a fixed smile that widens in stages over the film, see DRIVER_ARC), mom (the
# police mum's face in a robe, no glasses: she came down squinting), Lily (8, pajamas with moons), dad (memory, 21 years
# younger than he would be now: flannel, moustache). 'you' is the police 'you' in socks (3 AM, at home).
_NIGHTLINE = dict(shirt='#5b3f2b', shirt_sh='#3d2a1d', shirt_hi='#7c5b42', trousers='#46311f', trousers_sh='#2d1f15',
                  cap='#4c3424', cap_sh='#301f15', bill='#3a281b', patch='#1b2236', patch_rim='#d9bb6a', moon='#e9cf7e',
                  tag='#e6dfcc', tag_ink='#2a2420', shoes='#21170f', belt='#1d140d', buckle='#a3967c', top='#5b3f2b',
                  top_sh='#3d2a1d', top_hi='#7c5b42')
CAST['driver'] = dict(
    outfit='courier', hat='courier', hair='crop', sex='m', hh=178.0,
    head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 53, 77, 90, 93, 91, 85, 73, 55, 31, 0],
    eye_dx=42, eye_y=-10, eye_r=21.5, pupil=0.62, brow_th=9.5, nose_len=30, mouth_y=63, mouth_w=25,
    skin='#c0b1aa', skin_sh='#8a7b7b', skin_dp='#554851', blush='#c39a9c', lip='#86696b', stubble='#575a64', stub=0.4,
    hair_c='#2a221e', brow_c='#1c1717', bags=1.2, age=0.6, blink_rate=0.0, lock=1.0, micro=0.3, breath=0.6,
    scar=0, ring=0, part=0, lashes=0.0, gaunt=1.0, grin_k=1.1, tooth_w=11.0, talk_lag=0.2, talk=0.72, feet='boots', grin_lim=0.97,
    body=dict(sh=124, ch=116, wa=100, hip=104, arm=(50, 40), leg=(60, 48), neck=45, hand=1.04),
    cloth=dict(_NIGHTLINE))
CAST['mom'] = dict(
    outfit='robe', hat=None, hair='curly', sex='f', hh=188.0,
    head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 52, 77, 94, 100, 99, 91, 76, 54, 28, 0],
    eye_dx=42, eye_y=-6, eye_r=18.5, pupil=1.0, brow_th=7.5, nose_len=24, mouth_y=60, mouth_w=21,
    skin='#c9ab9f', skin_sh='#96786f', skin_dp='#6a5153', blush='#de9c9c', lip='#a5716f', stubble=None, stub=0, lips=0.4,
    hair_c='#8a817b', brow_c='#5e5550', bags=0.9, age=0.85, blink_rate=0.3, lock=0.0, micro=1.0, breath=1.0,
    scar=0, ring=1, part=0, lashes=0.6, glasses=False, feet='slippers',
    body=dict(sh=100, ch=106, wa=104, hip=110, arm=(44, 36), leg=(40, 33), neck=34, hand=0.85),
    cloth=dict(top='#6e4a57', top_sh='#4b303b', top_hi='#8d6673', collar='#83606b', gown='#e0d6c6', gown_sh='#b9ad9a',
               belt='#5a3c47', legs='#c4a598', shoes='#8e7f86', shoes_sh='#625660'))
CAST['lily'] = dict(
    outfit='pajamas', hat=None, hair='kid', sex='f', hh=236.0, child=True,
    head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 58, 84, 98, 102, 102, 97, 85, 63, 34, 0],
    eye_dx=40, eye_y=6, eye_r=22.5, pupil=1.45, brow_th=6.0, nose_len=13, mouth_y=64, mouth_w=16,
    skin='#d6b6a6', skin_sh='#a8877b', skin_dp='#76595a', blush='#ee9f9b', lip='#bf8079', stubble=None, stub=0, lips=0.3,
    hair_c='#6e4b33', brow_c='#5a3d2b', bags=0.1, age=0.0, blink_rate=0.3, lock=0.0, micro=0.9, breath=0.9,
    scar=0, ring=0, part=1, lashes=1.0, feet='bare',
    body=dict(sh=80, ch=80, wa=78, hip=82, arm=(34, 28), leg=(42, 34), neck=30, hand=0.74, arm_k=0.86),
    cloth=dict(top='#8b84b8', top_sh='#625b8e', top_hi='#aaa3d4', trim='#d7d1ef', print_c='#f1e2a2', trousers='#8b84b8',
               trousers_sh='#625b8e', legs='#d6b6a6', shoes='#d6b6a6', shoes_sh='#a8877b'))
CAST['dad'] = dict(
    outfit='flannel', hat=None, hair='messy', sex='m', hh=178.0,
    head_ys=[-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120], head_ws=[0, 51, 75, 92, 98, 97, 88, 72, 50, 26, 0],
    eye_dx=43, eye_y=-8, eye_r=19.5, pupil=1.0, brow_th=10.5, nose_len=24, mouth_y=60, mouth_w=22,
    skin='#c7a693', skin_sh='#957465', skin_dp='#634b48', blush='#d99690', lip='#9c6d66', stubble='#4e4038', stub=0.45,
    hair_c='#3a2a20', brow_c='#2c1f18', bags=0.5, age=0.45, blink_rate=0.3, lock=0.0, micro=0.9, breath=1.0,
    scar=0, ring=1, part=-1, lashes=0.0, moustache='#3a2a20', feet='boots',
    body=dict(sh=128, ch=124, wa=114, hip=110, arm=(56, 46), leg=(60, 50), neck=50, hand=1.04),
    cloth=dict(top='#7b3a2d', top_sh='#53241c', top_hi='#9a5242', check='#2b1a16', check_hi='#c98a62', tee='#d9d2c4',
               trousers='#3b4a66', trousers_sh='#263147', shoes='#3a2c22', shoes_sh='#241b15'))
CAST['you']['feet'] = 'socks'                          # 3 AM at home: grey socks (the delivery photo shows them)
CAST['you']['cloth'].update(socks='#8d8f96', socks_sh='#5f6169')

# ---------------------------------------------------------------------------------------- dummy film cast
# "If Your Grandpa's Ventriloquist Dummy Tells You A Joke... DON'T LAUGH". This film's cast takes the plain names
# ('mom', 'you'); the delivery designs stay as 'mom_delivery' / 'you_police' (the police / delivery 'you' in socks).
CAST['mom_delivery'] = CAST['mom']
CAST['you_police'] = CAST['you']
_FACE_OLD = [-120, -114, -100, -70, -30, 10, 50, 82, 104, 116, 120]
# Mister Winks: a 0.85 m ventriloquist figure (big carved head, skinny stuffed limbs). His head is drawn by _winks_head
# (painted wooden face, hinged jaw block, wooden eyelids, painted red hair, pillbox cap); body units as everyone else.
CAST['winks'] = dict(
    outfit='usher', hat='pillbox', hair='painted', sex='m', hh=300.0, dummy=True,
    head_ys=_FACE_OLD, head_ws=[0, 60, 87, 100, 104, 102, 96, 89, 80, 56, 0],
    eye_dx=41, eye_y=-14, eye_r=28.5, pupil=0.55, brow_th=18, nose_len=14, mouth_y=52, mouth_w=50,
    skin='#efdcc3', skin_sh='#b8977f', skin_dp='#45282a', blush='#b0525a', lip='#7a1420', stubble=None, stub=0,
    hair_c='#8c2b13', brow_c='#22130e', bags=0.0, age=0.0, blink_rate=0.0, lock=1.0, micro=0.0, breath=0.0,
    scar=0, ring=0, part=1, lashes=0.0, talk=1.0, feet='shoes', iris='#2a1a12',
    body=dict(sh=82, ch=74, wa=66, hip=64, arm=(30, 24), leg=(32, 27), neck=22, hand=1.22, arm_k=0.8),
    cloth=dict(top='#7d1d2b', top_sh='#4e0f19', top_hi='#a8384a', brass='#d8b04c', brass_sh='#8a6a22', brass_hi='#fff0b8',
               braid='#d6b257', trousers='#262a40', trousers_sh='#161828', stripe='#c9a24a', shoes='#3b1712',
               glove='#f4f0e6', glove_sh='#c8c0ad', shirt='#efe9dc', cap='#7d1d2b', cap_sh='#4e0f19', strap='#17121a'))
# Grandpa (86): the thing that lived as Walter Kemp. Bald dome, white tufts over big ears, a long hooked nose, bushy
# white brows, deep folds; the kind cardigan look in memories, the gown in the hospital. His smile is a little too still
# and his lips barely move when he talks (talk 0.3): sixty years of never moving them.
_GRANDPA = dict(
    hat=None, hair='bald', sex='m', hh=180.0,
    head_ys=_FACE_OLD, head_ws=[0, 52, 76, 89, 92, 89, 80, 69, 53, 31, 0],
    eye_dx=40, eye_y=-6, eye_r=17.5, pupil=0.85, brow_th=11, nose_len=36, mouth_y=64, mouth_w=21, nose='hook',
    skin='#d3ae9c', skin_sh='#a07f72', skin_dp='#6a5050', blush='#d99594', lip='#9a6a68', stubble='#d9d4cc', stub=0.25,
    hair_c='#dcd8d2', brow_c='#d6d1ca', bags=1.1, age=1.35, blink_rate=0.1, lock=0.45, micro=0.25, breath=0.6,
    scar=0, ring=1, part=0, lashes=0.0, ears=1.35, brows='bushy', spots=1.0, talk=0.3, lids=0.2,
    body=dict(sh=112, ch=108, wa=104, hip=100, arm=(44, 36), leg=(50, 42), neck=38, hand=0.98))
CAST['grandpa'] = dict(_GRANDPA, outfit='cardi_m', feet='slippers',
                       cloth=dict(top='#5e6a45', top_sh='#3e472c', top_hi='#7a875c', shirt='#e7dcc4', shirt_sh='#bfb196',
                                  check='#b49a7a', trousers='#6a4f3a', trousers_sh='#463325', shoes='#5a3b2c', shoes_sh='#3b261c',
                                  button='#8a6440'))
CAST['grandpa_bed'] = dict(_GRANDPA, outfit='gown', feet='socks', gaunt=0.8, blink_rate=0.06,
                           cloth=dict(top='#a9c3d6', top_sh='#7894aa', top_hi='#cddcea', print_c='#5f7c96', trousers='#c7a596',
                                      trousers_sh='#9a7b70', socks='#c9b28a', socks_sh='#9a8462', band='#f2f2ee'))
# the real Walter, back in his own dying body for one hour: the same face and gown, lucid and terrified (scared cast)
CAST['walter'] = dict(CAST['grandpa_bed'], lock=0.0, blink_rate=0.3, micro=1.0, talk=0.85, lids=0.0)
# young Walter on the 1974 tape: thick dark hair and sideburns, the family nose and ears, a powder-blue suit with huge
# lapels, a big showman smile, and lips that never move (talk 0: the dummy does the talking)
CAST['walter74'] = dict(
    outfit='suit70', hat=None, hair='pomp', sex='m', hh=178.0,
    head_ys=_FACE_OLD, head_ws=[0, 53, 77, 91, 96, 95, 89, 77, 58, 33, 0],
    eye_dx=41, eye_y=-8, eye_r=18.5, pupil=0.8, brow_th=10.5, nose_len=30, mouth_y=62, mouth_w=22, nose='hook',
    skin='#d2a98f', skin_sh='#a37b66', skin_dp='#6b4b44', blush='#dc958d', lip='#a06a62', stubble='#4a3a30', stub=0.3,
    hair_c='#3b2a1f', brow_c='#2b1e16', bags=0.4, age=0.4, blink_rate=0.05, lock=0.45, micro=0.35, breath=0.6,
    scar=0, ring=1, part=1, lashes=0.0, ears=1.25, talk=0.0, feet='shoes',
    body=dict(sh=124, ch=118, wa=106, hip=106, arm=(52, 42), leg=(58, 48), neck=46, hand=1.02),
    cloth=dict(top='#8fb2cf', top_sh='#617f9b', top_hi='#b6d0e6', shirt='#efe3c4', shirt_sh='#cbbd9b', tie='#9a6a24',
               tie_hi='#d4a24a', trousers='#8fb2cf', trousers_sh='#617f9b', shoes='#4a2e1e', shoes_sh='#2e1c12', square='#d4a24a'))
# Mom (mid 40s): drove up tonight. Long camel coat, a chunky teal scarf, dark hair in a low bun with loose strands,
# tired eyes. Grieving and holding it together.
CAST['mom'] = dict(
    outfit='longcoat', hat=None, hair='lowbun', sex='f', hh=182.0,
    head_ys=_FACE_OLD, head_ws=[0, 49, 71, 87, 92, 90, 82, 66, 46, 24, 0],
    eye_dx=40, eye_y=-6, eye_r=18.0, pupil=1.0, brow_th=7.5, nose_len=24, mouth_y=60, mouth_w=21,
    skin='#d9b19a', skin_sh='#a9806d', skin_dp='#6d4f4c', blush='#de9a95', lip='#a8666a', stubble=None, stub=0, lips=0.55,
    hair_c='#3a2620', brow_c='#2e1f1a', bags=0.75, age=0.45, blink_rate=0.3, lock=0.0, micro=1.0, breath=1.0,
    scar=0, ring=1, part=0, lashes=0.9, earrings=True, feet='boots',
    body=dict(sh=104, ch=104, wa=92, hip=104, arm=(44, 36), leg=(46, 38), neck=36, hand=0.86),
    cloth=dict(top='#b28a5e', top_sh='#806040', top_hi='#cfa878', button='#4a3424', scarf='#2f6a66', scarf_sh='#1d4846',
               scarf_hi='#4b8c86', sweater='#5b4a5e', trousers='#2b2f3e', trousers_sh='#1a1d28', shoes='#3a2a22', shoes_sh='#22180f'))
# Owen (9): big round head, a cowlick that never lies down, big ears, a missing front tooth, a mustard hoodie, red
# sneakers. He can't wink: both eyes close (Acting.try_wink).
CAST['owen'] = dict(
    outfit='hoodie', hat=None, hair='cowlick', sex='m', hh=232.0, child=True,
    head_ys=_FACE_OLD, head_ws=[0, 58, 85, 99, 104, 104, 99, 87, 66, 36, 0],
    eye_dx=40, eye_y=4, eye_r=22.5, pupil=1.4, brow_th=7.0, nose_len=14, mouth_y=64, mouth_w=18, nose='button',
    skin='#e2b89c', skin_sh='#b38a72', skin_dp='#7a5752', blush='#ef9f96', lip='#c07c74', stubble=None, stub=0, lips=0.0,
    hair_c='#8a5a32', brow_c='#6b4428', bags=0.15, age=0.0, blink_rate=0.35, lock=0.0, micro=1.0, breath=1.0,
    scar=0, ring=0, part=1, lashes=0.4, ears=1.3, gap=True, feet='shoes',
    body=dict(sh=84, ch=82, wa=80, hip=80, arm=(36, 30), leg=(40, 34), neck=30, hand=0.78, arm_k=0.88),
    cloth=dict(top='#d9a12c', top_sh='#a6741a', top_hi='#f0c55a', trousers='#3c5a86', trousers_sh='#273d5e', shoes='#c43a32',
               shoes_sh='#8a2620', string='#f4ead2'))
# the thing in Owen's body at the end: the same boy, a creepy cast (never blinks, the too-still smile, Grandpa's way)
CAST['owen_new'] = dict(CAST['owen'], lock=1.0, blink_rate=0.0, micro=0.25, talk=0.3, pupil=1.05)
# you (the narrator, ~16): long face, dark curtain bangs parted in the middle over the ears, a blue denim jacket over a
# heather-grey hoodie, black jeans, white sneakers
CAST['you'] = dict(
    outfit='denim', hat=None, hair='shaggy', sex='m', hh=184.0,
    head_ys=_FACE_OLD, head_ws=[0, 50, 72, 88, 93, 92, 85, 69, 49, 25, 0],
    eye_dx=41, eye_y=-4, eye_r=19.5, pupil=1.05, brow_th=8.5, nose_len=22, mouth_y=60, mouth_w=20,
    skin='#c99c80', skin_sh='#9a7260', skin_dp='#5f4442', blush='#d88f86', lip='#a16a62', stubble=None, stub=0, lips=0.0,
    hair_c='#231b1a', brow_c='#1d1615', bags=0.55, age=0.12, blink_rate=0.35, lock=0.0, micro=1.0, breath=1.0,
    scar=0, ring=0, part=0, lashes=0.2, feet='shoes',
    body=dict(sh=112, ch=106, wa=96, hip=98, arm=(46, 38), leg=(50, 42), neck=40, hand=0.96),
    cloth=dict(top='#3d5f8c', top_sh='#2a4466', top_hi='#5d80ad', hood='#8d9097', hood_sh='#62656c', button='#c9a24a',
               trousers='#1f2026', trousers_sh='#121318', shoes='#e8e4dc', shoes_sh='#a8a39a', string='#e8e4dc'))

# ====================================================================================================== pose
POSE_DEFAULTS = dict(
    # placement / body (body units: 1000 = feet to crown)
    dx=0.0, dy=0.0, turn=0.0, lean=0.0, tilt=0.0, sway=0.0, bob=0.0, breath=0.5, approach=0.0, sit=0.0, crouch=0.0,
    shrug=0.0, hunch=0.0,
    # head
    h_turn=0.0, h_tilt=0.0, h_nod=0.0, h_dx=0.0, h_dy=0.0, h_scale=1.0,
    # eyes: look in -1..1 (relative to the face), lock 1 = pupils on the lens whatever the head does
    look_x=0.0, look_y=0.0, lock=0.0, pupil=1.0, eye_open=1.0, blink=0.0, wide=0.0, squint=0.0, bloodshot=0.0, wet=0.0,
    # brows
    brow_up=0.0, brow_angry=0.0, brow_sad=0.0, brow_asym=0.0,
    # mouth
    m_open=0.0, m_wide=0.0, m_round=0.0, smile=0.0, grin=0.0, teeth=0.0, gums=0.0, tremble=0.0, m_side=0.0, m_press=0.0,
    # skin extras
    tears=0.0, sweat=0.0, blush=0.0, pale=0.0, jitter=0.0, glint=0.0,
    # arms: hand target relative to its shoulder: out (away from body), down, fwd (toward the character's front)
    hl_out=10.0, hl_down=336.0, hl_fwd=6.0, hr_out=10.0, hr_down=336.0, hr_fwd=6.0,
    hl_up=0.0, hr_up=0.0, hl_press=0.0, hr_press=0.0, hl_rot=0.0, hr_rot=0.0, thumb=0.0,
    # legs
    walk_ph=0.0, walk_amt=0.0, stance=0.0,
    # secondary motion and gadgets
    sec_x=0.0, sec_y=0.0, cam_on=1.0, still=0.0, t=0.0,
    # v2.1: idle-life scale (creepy drift / re-settles / weight shifts / micro twitches), phone-to-ear arm weights,
    # per-hand size (fist punch toward the lens)
    life=1.0, hl_ear=0.0, hr_ear=0.0, hl_scale=1.0, hr_scale=1.0, specs=1.0,
    # delivery film: eyeshine (animal eyes on the doorbell camera), sitting on the floor, tiptoe, a too-long arm
    # (stretch 0.5 = 1.5x arm length), hand tremor (shake), tablet screen ink (signature progress) and camera flash
    eyeshine=0.0, floor=0.0, tiptoe=0.0, hl_stretch=0.0, hr_stretch=0.0, hl_shake=0.0, hr_shake=0.0,
    tablet_ink=1.0, tablet_flash=0.0,
    # dummy film: jaw (Mister Winks's hinged jaw block, 0 shut .. 1 hanging wide), lid_l / lid_r (eyelids per side,
    # character's left / right: wooden lids on the dummy, a squeeze on people), crack (paint cracks spreading), desperate
    # (the soul inside looking out: sad brows, wet eyes, under a painted grin), torch (usher's flashlight on 0..1) and
    # torch_ang (deg, 0 = beam up, 90 = to the character's left/screen right in a front view, 180 = down, 'lens' via
    # torch_lens 1 = pointed into the camera), lie (0 upright .. 1 lying face down on the floor, -1 face up), slot_paper
    # (the torn P.S. sliding out of his back slot), steam (mug steam), kneel (one knee down)
    jaw=0.0, lid_l=0.0, lid_r=0.0, crack=0.0, desperate=0.0, torch=0.0, torch_ang=0.0, torch_lens=0.0, lie=0.0,
    slot_paper=0.0, steam=1.0, kneel=0.0, grin_w=0.0, gloss=1.0,
    # perch 1: y_feet is the surface a sitting figure sits on (chair seat, lap, stair, shelf): the figure drops so its
    # seat rests there and the legs hang below (works with pose.sit; Mister Winks's sit clips set it)
    perch=0.0, recline=0.0,
)
POSE_DISCRETE = dict(hl_shape='mitt', hr_shape='mitt', hl_prop=None, hr_prop=None, tablet_screen='sign')


class Pose:
    """All animatable pose numbers (POSE_DEFAULTS) plus discrete hand shapes / props (POSE_DISCRETE)."""

    def __init__(self, expr=None, **kw):
        d = self.__dict__
        d.update(POSE_DEFAULTS); d.update(POSE_DISCRETE)
        if expr: self.mix(EXPR[expr], 1.0)
        d.update(kw)

    def copy(self):
        p = Pose.__new__(Pose); p.__dict__ = dict(self.__dict__); return p

    def mix(self, params, w=1.0):
        """Blend toward params (dict) by weight w (0..1). Discrete fields switch at w >= 0.5."""
        if w <= 0: return self
        d = self.__dict__
        for k, v in params.items():
            if k in POSE_DISCRETE or not isinstance(v, (int, float)):
                if w >= 0.5: d[k] = v
            else:
                c = d.get(k, 0.0); d[k] = c + (v - c) * min(1.0, w)
        return self

    def add(self, params, w=1.0):
        d = self.__dict__
        for k, v in params.items(): d[k] = d.get(k, 0.0) + v * w
        return self

    def expr(self, name, w=1.0):
        return self.mix(EXPR[name], w)

    @staticmethod
    def lerp(a, b, k):
        p = a.copy(); p.mix({k_: v for k_, v in b.__dict__.items()}, k); return p

    def __repr__(self):
        return 'Pose(%s)' % ', '.join('%s=%.2f' % (k, v) for k, v in self.__dict__.items()
                                      if isinstance(v, float) and abs(v - POSE_DEFAULTS.get(k, 0)) > 1e-3)


EXPR = {
    'neutral': {},
    'blank': dict(pupil=0.8, eye_open=0.92),
    'calm_smirk': dict(smile=0.38, m_side=0.6, brow_angry=0.2, squint=0.22, pupil=0.9, brow_asym=0.3),
    'polite': dict(smile=0.5, teeth=0.15, brow_up=0.15, squint=0.1),
    'talk_smile': dict(smile=0.55, teeth=0.4, brow_up=0.2, pupil=0.75),
    'creep_smile': dict(smile=0.9, grin=0.45, teeth=0.75, pupil=0.55, wide=0.3, brow_up=0.3, bloodshot=0.35, lock=1.0),
    'wide_grin': dict(smile=1.0, grin=1.0, teeth=1.0, gums=0.7, m_open=0.22, pupil=0.42, wide=0.55, brow_up=0.55,
                      bloodshot=0.6, lock=1.0),
    'stare': dict(pupil=0.5, wide=0.5, brow_up=0.3, bloodshot=0.45, lock=1.0, still=1.0),
    'dead_stare': dict(pupil=0.55, eye_open=0.82, wide=0.1, m_press=0.6, lock=1.0, still=1.0, bloodshot=0.3),
    'nervous': dict(brow_sad=0.75, brow_up=0.25, smile=-0.3, tremble=0.7, wide=0.25, pupil=0.85, sweat=0.5, m_press=0.3),
    'fear': dict(wide=0.75, pupil=0.4, brow_sad=0.85, brow_up=0.6, brow_angry=0.15, m_open=0.28, m_round=0.3, smile=-0.4,
                 tremble=0.6, sweat=0.7),
    'angry': dict(brow_angry=1.0, smile=-0.45, squint=0.35, m_open=0.16, teeth=0.8, m_wide=0.55, pupil=0.7),
    'whisper': dict(m_open=0.1, m_round=0.45, brow_up=0.2, squint=0.25, smile=0.18, pupil=0.62, h_nod=0.1, lock=1.0),
    'shout': dict(m_open=0.85, m_round=0.35, brow_angry=0.95, wide=0.35, pupil=0.55, teeth=0.4, smile=-0.35),
    'scream': dict(m_open=1.0, m_round=0.4, smile=-0.7, wide=0.85, pupil=0.3, brow_up=0.5, brow_sad=0.9, brow_angry=0.3,
                   teeth=0.35, gums=0.0, tremble=0.45),
    'cry': dict(tears=1.0, brow_sad=1.0, smile=-0.55, m_open=0.32, m_round=0.35, tremble=0.65, squint=0.3, blush=0.7, wet=1.0),
    'grin_cry': dict(tears=1.0, smile=1.0, grin=0.9, teeth=1.0, gums=0.3, brow_sad=0.95, wide=0.4, pupil=0.48, blush=0.6,
                     wet=1.0, lock=1.0),
    'shock': dict(m_open=0.62, m_round=0.85, wide=0.85, pupil=0.38, brow_up=0.85, smile=-0.25),
    'sad': dict(brow_sad=0.85, smile=-0.45, pupil=0.95, eye_open=0.8, h_nod=0.08, wet=0.5),
    'suspicious': dict(squint=0.5, brow_angry=0.45, brow_asym=0.7, smile=0.12, m_side=-0.7, pupil=0.8, look_x=-0.35),
    'sweaty': dict(sweat=1.0, brow_sad=0.55, wide=0.3, smile=-0.2, tremble=0.35, pupil=0.7, m_press=0.4),
    # dummy film
    'lucid': dict(wide=0.85, pupil=0.42, brow_sad=0.95, brow_up=0.75, tears=0.75, wet=1.0, m_open=0.14, m_round=0.45, smile=-0.35,
                  tremble=0.5, lock=1.0),                                        # the real Walter: awake, terrified, whispering
    'kid_grin': dict(smile=1.0, teeth=1.0, m_open=0.2, brow_up=0.35, squint=0.15, pupil=1.0),   # Owen delighted (the gap tooth)
    'still_smile': dict(smile=0.42, m_press=0.38, pupil=0.85, still=0.6),          # Grandpa: a kind smile that never moves
    'showman': dict(smile=1.0, grin=0.5, teeth=1.0, brow_up=0.3, pupil=0.75, lock=0.8),
}


# ====================================================================================================== drawing context
_TXI = {}


def _overlay_img(name, k=2.2):
    """Normal-blend version of a core texture: dark specks = black with alpha, light = white with alpha (fast src-over)."""
    key = (name, k)
    if key not in _TXI:
        g = tex(name)
        d = np.clip((0.5 - g) * k, 0, 1); l_ = np.clip((g - 0.5) * k, 0, 1)
        a = np.maximum(d, l_)
        v = np.where(l_ > d, l_, 0.0)
        arr = np.dstack([v * 255, v * 255, v * 255, a * 255]).astype(np.uint8)
        arr = np.ascontiguousarray(arr)
        _TXI[key] = (skia.Image.fromarray(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType), arr)
    return _TXI[key][0]


_LINS = skia.SamplingOptions(skia.FilterMode.kNearest)
_GIMG = {}


def _gimg(kind, stops):
    """Cached gradient image (premultiplied BGRA): 'r' 512x512 radial, 'l' 1024x2 linear. Drawn as a nearest-sampled
    image shader on the path: ~10x faster than stretched image rects and correct under any rotation."""
    key = (kind, _stops_key(stops))
    im = _GIMG.get(key)
    if im is None:
        if kind == 'r':
            n = 512
            yy, xx = np.mgrid[0:n, 0:n]
            r = np.sqrt((xx + 0.5 - n / 2) ** 2 + (yy + 0.5 - n / 2) ** 2) / (n / 2)
            arr = _ramp(key[1], np.clip(r, 0, 1))
        elif kind == 'v':
            arr = np.repeat(_ramp(key[1], (np.arange(1024) + 0.5) / 1024)[:, None, :], 2, axis=1)
        else:
            arr = np.repeat(_ramp(key[1], (np.arange(1024) + 0.5) / 1024)[None, :, :], 2, axis=0)
        arr = np.ascontiguousarray(arr)
        im = (skia.Image.fromarray(arr, skia.kBGRA_8888_ColorType, skia.kPremul_AlphaType), arr)
        if len(_GIMG) > 400: _GIMG.clear()
        _GIMG[key] = im
    return im[0]


def _snap_axis(m, cx, cy, tol=0.105):
    """Drop a small rotation (< ~6 deg) from a shader matrix, keeping the image point (cx, cy) in place: rotated image
    sampling is skia's slow path, and idle head sway would otherwise put every face gradient on it."""
    a, b, c, d = m.getScaleX(), m.getSkewX(), m.getSkewY(), m.getScaleY()
    if (b == 0 and c == 0) or abs(b) > tol * abs(d) or abs(c) > tol * abs(a): return m
    px = a * cx + b * cy + m.getTranslateX(); py = c * cx + d * cy + m.getTranslateY()
    a2 = math.copysign(math.hypot(a, c), a); d2 = math.copysign(math.hypot(b, d), d)
    r = skia.Matrix(); r.setAll(a2, 0, px - a2 * cx, 0, d2, py - d2 * cy, 0, 0, 1)
    return r


class Ctx:
    """Local drawing frame: geometry in local units goes through matrix M onto the (axis-aligned) engine canvas, so the
    engine's fast gradient paths keep working even when a head is tilted. lw = outline width in local units."""
    __slots__ = ('pen', 'cv', 'M', 's', 'lw', 'm6', 'det')

    def __init__(self, pen, M, lw):
        self.pen, self.cv, self.M = pen, pen.cv, M
        a, b, c, d = M.getScaleX(), M.getSkewX(), M.getSkewY(), M.getScaleY()
        self.det = a * d - b * c
        self.s = math.sqrt(abs(self.det)) or 1e-6
        self.lw = lw
        self.m6 = (a, b, M.getTranslateX(), c, d, M.getTranslateY())

    def sub(self, tx=0.0, ty=0.0, rot=0.0, sx=1.0, sy=None):
        m = skia.Matrix(); m.preConcat(self.M); m.preTranslate(tx, ty)
        if rot: m.preRotate(rot)
        sy = sx if sy is None else sy
        if sx != 1.0 or sy != 1.0: m.preScale(sx, sy)
        k = math.sqrt(abs(sx * sy)) or 1e-6
        return Ctx(self.pen, m, self.lw / k)

    def P(self, path):
        q = skia.Path(path); q.transform(self.M); return q

    def pt(self, x, y):
        a, b, tx, c, d, ty = self.m6
        return a * x + b * y + tx, c * x + d * y + ty

    def fill(self, path, c, a=255):
        if a > 0.5: self.pen.fill(self.P(path), c, a)

    def line(self, path, w=None, c=LINE, a=255, cap='round'):
        if a > 0.5: self.pen.line(self.P(path), (self.lw if w is None else w) * self.s, c, a, cap)

    def shape(self, path, c, w=None, lc=LINE, a=255):
        q = self.P(path)
        self.pen.fill(q, c, a)
        self.pen.line(q, (self.lw if w is None else w) * self.s, lc, a)

    def _shade_path(self, path, img, m, a):
        sm = skia.Matrix(); sm.preConcat(self.M); sm.preConcat(m)
        sm = _snap_axis(sm, img.width() / 2.0, img.height() / 2.0)
        p = skia.Paint(AntiAlias=True, Shader=img.makeShader(skia.TileMode.kClamp, skia.TileMode.kClamp, _LINS, sm), Alphaf=float(clamp(a)))
        self.cv.drawPath(self.P(path), p)

    def radial(self, path, cx, cy, r, stops, sy=1.0, a=1.0, clip=True):
        """Radial gradient (local coords, rotates with the frame). path None: just the gradient's ellipse (clip=False)
        or everything visible (clip=True, beyond r = last stop)."""
        m = skia.Matrix(); m.setScale(2 * r / 512.0, 2 * r * sy / 512.0); m.postTranslate(cx - r, cy - r * sy)
        if path is None:
            if clip: path = rect(cx - 4000, cy - 4000, 8000, 8000)
            else: path = oval(cx, cy, r, r * sy)
        self._shade_path(path, _gimg('r', stops), m, a)

    def glow(self, cx, cy, rx, ry, c, a):
        if a > 0.5: self.radial(None, cx, cy, rx, [(0, c, a), (0.5, c, a * 0.5), (1, c, 0)], sy=ry / rx, clip=False)

    def grad(self, path, x0, y0, x1, y1, stops, a=1.0):
        """Linear gradient between two local points (clamped beyond them)."""
        dx, dy = x1 - x0, y1 - y0
        m = skia.Matrix()
        if abs(dx) <= 0.02 * abs(dy):                      # vertical: axis-aligned matrix keeps skia on its fast path
            m.setScale(1.0, dy / 1024.0); m.postTranslate(x0, y0)
            self._shade_path(path, _gimg('v', stops), m, a); return
        if abs(dy) <= 0.02 * abs(dx):
            m.setScale(dx / 1024.0, 1.0); m.postTranslate(x0, y0)
            self._shade_path(path, _gimg('l', stops), m, a); return
        L = math.hypot(dx, dy)
        m.setScale(L / 1024.0, 1.0); m.postRotate(math.degrees(math.atan2(dy, dx))); m.postTranslate(x0, y0)
        self._shade_path(path, _gimg('l', stops), m, a)

    def texture(self, path, name, alpha=0.2, scale=1.0, dx=0.0, dy=0.0):
        if alpha <= 0.01: return
        img = _overlay_img(name)
        m = skia.Matrix(); m.preConcat(self.M); m.preTranslate(dx, dy); m.preScale(scale, scale)
        m = _snap_axis(m, 0.0, 0.0)
        p = skia.Paint(AntiAlias=True, Shader=img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, _LINS, m),
                       Alphaf=float(clamp(alpha)))
        self.cv.drawPath(self.P(path), p)

    @contextmanager
    def clip(self, path, diff=False):
        self.cv.save()
        self.cv.clipPath(self.P(path), skia.ClipOp.kDifference if diff else skia.ClipOp.kIntersect, True)
        try: yield
        finally: self.cv.restore()


@contextmanager
def _noop():
    yield


def _lw_for(head_px):
    """Outline width (design px) for a head of head_px design px: ~3.7 on wide shots, ~8.2 on close-ups (VISUAL_SPEC)."""
    return clamp(2.8 + 0.009 * head_px, 2.4, 9.5)


def _auto_detail(pen, head_design):
    m = pen.cv.getTotalMatrix()
    px = head_design * math.sqrt(abs(m.getScaleX() * m.getScaleY() - m.getSkewX() * m.getSkewY()))
    return 0 if px < 70 else (1 if px < 260 else 2)


def _pts_path(xs, ys, closed=True, k=1.0):
    return smooth(list(zip(xs.tolist() if hasattr(xs, 'tolist') else xs, ys.tolist() if hasattr(ys, 'tolist') else ys)), closed, k)


def _multi(paths):
    """Several open/closed paths as one path (one draw call)."""
    p = skia.Path()
    for q in paths: p.addPath(q)
    return p


def _crescent(path, dx, dy):
    """The part of `path` not covered by itself moved by (dx, dy): a shade / rim band (path op, no clip mask)."""
    q = skia.Path(path); q.offset(dx, dy)
    r = skia.Op(path, q, skia.PathOp.kDifference_PathOp)
    return r if r is not None else skia.Path()


def _circle_pts(cx, cy, rx, ry=None, n=16, a0=0.0):
    ry = rx if ry is None else ry
    a = np.linspace(0, 2 * PI, n, endpoint=False) + a0
    return cx + rx * np.cos(a), cy + ry * np.sin(a)


# ====================================================================================================== head mapping
class HeadMap:
    """Maps front-view face coordinates (head units: crown -120, chin +120, half-width ~100) onto the turned head.
    The cross-section is an egg: a flat-ish face in front (depth DF * w) and a deep cranium behind (DB * w), so turned
    faces stay inside the silhouette and profiles put the nose on the edge. yaw (rad, + = facing screen right), pitch
    (rad, + = nod down), jaw (head units the chin drops by). Returns local 2D points (roll/scale/translate live in Ctx)."""
    DF, DB = 0.74, 1.2

    def __init__(self, sp, yaw, pitch, jaw=0.0, cheek=0.0):
        self.ys = np.asarray(sp['head_ys'], float); self.ws = np.asarray(sp['head_ws'], float)
        if cheek > 0.01:                                  # v2.1: a grin pushes the cheeks out (4-6 % at y ~ 40)
            self.ws = self.ws * (1.0 + 0.055 * cheek * np.exp(-((self.ys - 40.0) / 26.0) ** 2))
        self.yaw, self.pitch, self.jaw = yaw, pitch, jaw
        self.ct, self.st = math.cos(yaw), math.sin(yaw)
        self.cp, self.spi = math.cos(pitch), math.sin(pitch)
        self.dk = self.DF

    def W(self, y):
        return np.interp(y, self.ys, self.ws)

    def J(self, y):
        """Jaw drop: stretches everything below the mouth line."""
        y = np.asarray(y, float)
        return y + self.jaw * np.clip((y - 40.0) / 80.0, 0, None) if self.jaw else y

    def map(self, x0, y0, dz=0.0):
        x0 = np.asarray(x0, float); y0 = np.asarray(y0, float)
        w = np.maximum(self.W(y0), 1.0)
        s = np.clip(x0 / w, -1.0, 1.0)
        c = np.sqrt(1.0 - s * s)
        pz = self.DF * w * c + dz
        yj = self.J(y0)
        y1 = yj * self.cp + pz * self.spi
        z1 = pz * self.cp - yj * self.spi
        X = x0 * self.ct + z1 * self.st
        nx, nz = s * self.DF, c
        nn = np.sqrt(nx * nx + nz * nz) + 1e-9
        vis = (-nx * self.st + nz * self.cp * self.ct) / nn
        return X, y1, vis

    def map1(self, x0, y0, dz=0.0):
        X, Y, V = self.map(x0, y0, dz); return float(X), float(Y), float(V)

    def sx(self, x0, y0, dz=0.0):
        """Horizontal foreshortening at a face point."""
        a = self.map1(x0 - 1.0, y0, dz); b = self.map1(x0 + 1.0, y0, dz)
        return max(0.08, abs(b[0] - a[0]) / 2.0)

    def extent(self, w, df=None, db=None):
        """(left, right) screen x of a cross-section of half-width w."""
        df = self.DF if df is None else df; db = self.DB if db is None else db
        fr = np.sqrt((w * self.ct) ** 2 + (w * df * self.st) ** 2)
        bk = np.sqrt((w * self.ct) ** 2 + (w * db * self.st) ** 2)
        return (-bk, fr) if self.st >= 0 else (-fr, bk)

    def silhouette(self, grow=0.0, y_top=-120.0, y_bot=120.0, n=26):
        ys = np.linspace(y_top, y_bot, n)
        w = self.W(np.clip(ys, -120, 120)) + grow * (self.W(np.clip(ys, -120, 120)) > 0)
        xl, xr = self.extent(w)
        yy = self.J(ys) * self.cp + self.DF * w * self.spi * 0.25
        xs = np.concatenate([xr, xl[::-1]])
        yv = np.concatenate([yy, yy[::-1]])
        return _pts_path(xs, yv, True, 0.9)

    def arc(self, yfun, n=64):
        """Visible part of a curve running right round the head (phi in -pi..pi, 0 = front). yfun(phi) -> height.
        Returns 2D points sorted left to right."""
        phis = np.linspace(-PI, PI, n, endpoint=False)
        y0 = yfun(phis)
        w = np.maximum(self.W(y0), 1.0)
        c = np.cos(phis); s = np.sin(phis)
        d = np.where(c > 0, self.DF, self.DB)
        px = w * s; pz = d * w * c
        y1 = self.J(y0) * self.cp + pz * self.spi
        z1 = pz * self.cp - y0 * self.spi
        X = px * self.ct + z1 * self.st
        nx, nz = s * d, c
        vis = (-nx * self.st + nz * self.ct)
        k = vis > -0.02
        X, Y = X[k], y1[k]
        o = np.argsort(X)
        return X[o], Y[o]

    def arc_phi(self, yfun, n=96):
        """Like arc(), but the visible run of the curve in phi order (no sorting by x), so steep hairlines (bangs that
        drop into side curtains) stay a clean, non-folding edge. Returns X, Y left to right."""
        phis = np.linspace(-PI, PI, n, endpoint=False)
        y0 = yfun(phis)
        w = np.maximum(self.W(np.clip(y0, -120, 120)), 1.0)
        c = np.cos(phis); s = np.sin(phis)
        d = np.where(c > 0, self.DF, self.DB)
        px = w * s; pz = d * w * c
        y1 = self.J(y0) * self.cp + pz * self.spi
        z1 = pz * self.cp - y0 * self.spi
        X = px * self.ct + z1 * self.st
        vis = (-s * d * self.st + c * self.ct) > -0.02
        if not vis.any(): return np.array([]), np.array([])
        if vis.all(): i0 = int(np.argmin(X))
        else:
            i0 = int(np.argmax(vis & ~np.roll(vis, 1)))        # start of a visible run
        idx = (np.arange(n) + i0) % n
        idx = idx[vis[idx]]
        run = [idx[0]]
        for j in idx[1:]:
            if (j - run[-1]) % n != 1: break
            run.append(j)
        run = np.array(run)
        X, Y = X[run], y1[run]
        if X[0] > X[-1]: X, Y = X[::-1], Y[::-1]
        return X, Y


# ====================================================================================================== head drawing
def _skin_cols(sp, P, light):
    skin, sh, dp = sp['skin'], sp['skin_sh'], sp['skin_dp']
    if P.pale > 0:
        skin = mix(skin, '#b9b4b4', 0.6 * P.pale); sh = mix(sh, '#7d7880', 0.6 * P.pale)
    k = (light or {}).get('key', 0.0)
    if k > 0: skin = mix(skin, '#e2b48a', 0.25 * k); sh = mix(sh, '#9a6a52', 0.25 * k)
    elif k < 0: skin = mix(skin, '#7d8496', -0.35 * k); sh = mix(sh, '#4a5064', -0.35 * k)
    return skin, sh, dp


def _ear(c, hm, sp, side, skin, sh, det):
    y = 4.0
    w = float(hm.W(y))
    ph = 0.2
    ax3, az3 = side * w * math.cos(ph) * 0.95, -hm.DB * w * math.sin(ph)
    AX = ax3 * hm.ct + az3 * hm.st
    AY = float(hm.J(y)) * hm.cp + az3 * hm.spi * 0.3
    du = side * 0.8 * hm.ct - 0.86 * hm.st          # ear plane direction (outward and back) on screen
    nz = -side * hm.st
    if nz < -0.5: return
    pts = [(0, -24), (9, -29), (19, -20), (21, -2), (15, 18), (5, 27), (-1, 17)]
    ek = sp.get('ears', 1.0)                         # dummy film: big ears (Grandpa, young Walter, Owen)
    if ek != 1.0: pts = [(u * ek, v * ek + 3.0 * (ek - 1.0)) for u, v in pts]
    P_ = [(AX + u * du, AY + v) for u, v in pts]
    p = smooth(P_, True, 0.9)
    c.fill(p, skin); c.line(p, c.lw * 0.9)
    if sp.get('earrings'):
        ex_, ey_ = AX + 6 * du, AY + 24
        c.fill(oval(ex_, ey_, 4.5), '#d8b04c'); c.line(oval(ex_, ey_, 4.5), c.lw * 0.35)
        if det >= 1: c.fill(oval(ex_ - 1.3, ey_ - 1.3, 1.4), '#fff2c0')
    if det >= 1 and abs(du) > 0.3:
        inner = smooth([(AX + 13 * du * ek, AY - 16 * ek), (AX + 6 * du * ek, AY - 6 * ek), (AX + 10 * du * ek, AY + 8 * ek),
                        (AX + 4 * du * ek, AY + 14 * ek)], False)
        c.line(inner, c.lw * 0.5, sp['skin_dp'], 190)
        c.glow(AX + 8 * du * ek, AY, 9 * ek, 14 * ek, sh, 110)


def _eye(c, hm, sp, P, side, det, t, skin, sh):
    """One eye: big white, tiny pupil, lids, bags, veins, lashes. side -1 = screen-left eye (character's right)."""
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']
    X, Y, V = hm.map1(ex0, ey0, 2.0)
    if V < 0.12: return None
    fs = hm.sx(ex0, ey0)
    r = sp['eye_r'] * (1.0 + 0.16 * P.wide) * (1.0 + 0.04 * P.brow_up)
    asym = P.brow_asym * 0.0
    bl_ = max(P.blink, P.lid_l if side > 0 else P.lid_r)
    op = clamp(P.eye_open * (1.0 - bl_) * (1.0 - 0.45 * P.squint) * (1.0 - 0.3 * sp.get('lids', 0.0)) + 0.18 * P.wide * (1 - bl_), 0, 1.25)
    rx = r * fs
    # sockets and bags (under everything else of the eye)
    c.glow(X, Y + 2, rx * 1.9, r * 1.7, sp['skin_dp'], 46 + 34 * P.wide + 30 * sp['bags'])
    bags = sp['bags']
    if bags > 0:
        bag = smooth([(X - rx * 0.95, Y + r * 0.55), (X, Y + r * 1.42 + 3 * bags), (X + rx * 0.95, Y + r * 0.55), (X, Y + r * 1.05)], True, 0.9)
        c.fill(bag, mix(sh, sp['skin_dp'], 0.45), 80 * bags)
        if det >= 1:
            fold = smooth([(X - rx * 0.8, Y + r * 1.0), (X, Y + r * 1.48 + 3 * bags), (X + rx * 0.8, Y + r * 1.0)], False)
            c.line(fold, c.lw * 0.42, sp['skin_dp'], 150 * bags)
            if det >= 2 and bags > 0.7:
                f2 = smooth([(X - rx * 0.55, Y + r * 1.42), (X, Y + r * 1.78 + 2 * bags), (X + rx * 0.55, Y + r * 1.42)], False)
                c.line(f2, c.lw * 0.32, sp['skin_dp'], 90 * bags)
    if op < 0.07:                                                     # closed: lid curve + lashes
        lid = smooth([(X - rx * 1.02, Y + r * 0.05), (X, Y + r * 0.42), (X + rx * 1.02, Y + r * 0.05)], False)
        c.line(lid, c.lw * 1.05)
        if sp['lashes'] > 0:
            for k in (0.55, 0.85):
                x1 = X + side * rx * k; c.line(poly([(x1, Y + r * 0.25), (x1 + side * 6, Y + r * 0.55)], False), c.lw * 0.5)
        return (X, Y, r, fs)
    xs, ys = _circle_pts(X, Y, rx, r, 20)
    white = _pts_path(xs, ys)
    wc = '#ebe9e3' if P.pale < 0.5 else '#e3e3e1'
    if sp.get('eye_glow'):                      # optional red glow on the skin around the eye (thumbnail use)
        c.glow(X, Y + 2, rx * 1.75, r * 1.6, sp['eye_glow'], sp.get('eye_glow_a', 120))
    c.fill(white, wc)
    if det >= 1:
        c.radial(white, X, Y + r * 0.15, r * 1.05, [(0, wc, 0), (0.62, wc, 0), (1, sp.get('eye_edge', '#b9b0aa'), 230)], sy=1.0)
    # pupils
    lock = clamp(P.lock)
    lx = lerp(P.look_x, -math.sin(hm.yaw) * 0.85, lock)
    ly = lerp(P.look_y, -math.sin(hm.pitch) * 1.1 - 0.05, lock)
    pr = r * 0.40 * sp['pupil'] * P.pupil
    pr = max(pr, 2.2)
    reach = r - pr - 1.5
    px = X + lx * reach * fs; py = Y + ly * reach
    with c.clip(white):
        if det >= 1 and P.bloodshot > 0.02:
            a_v = min(255.0, 150 * clamp(P.bloodshot) * sp.get('vein_a', 1.0))
            vs, vs2 = [], []
            nv_ = int((6 if det >= 2 else 3) * sp.get('veins', 1.0)); vin = sp.get('vein_in', 0.42)
            for k in range(nv_):
                if sp.get('vein_even'):                  # spread evenly round the eye (thumbnail use)
                    ang = (k + 0.35 * hash01(k, 7 + side)) * 2 * PI / nv_ + side * 0.4
                else:
                    ang = (hash01(k, 7 + side) * 2 - 1) * PI
                x1, y1 = X + math.cos(ang) * rx * 1.02, Y + math.sin(ang) * r * 1.02
                mx_, my_ = X + math.cos(ang + 0.3) * rx * (vin + 0.2), Y + math.sin(ang + 0.3) * r * (vin + 0.2)
                x2, y2 = X + math.cos(ang - 0.15) * rx * vin, Y + math.sin(ang - 0.15) * r * vin
                vs.append(smooth([(x1, y1), (mx_, my_), (x2, y2)], False))
                if det >= 2:
                    vs2.append(smooth([(mx_, my_), (mx_ + math.cos(ang + 1.4) * r * 0.2, my_ + math.sin(ang + 1.4) * r * 0.2)], False))
            c.line(_multi(vs), c.lw * 0.22 * sp.get('vein_w', 1.0), '#b8424c', a_v)
            if vs2: c.line(_multi(vs2), c.lw * 0.15 * sp.get('vein_w', 1.0), '#c04a52', a_v * 0.8)
        if P.wet > 0 and det >= 1:
            c.fill(smooth([(X - rx, Y + r * 0.62), (X, Y + r * 0.85), (X + rx, Y + r * 0.62), (X, Y + r * 1.1)], True), '#a8c8f0', 120 * P.wet)
        if sp.get('iris'):                           # optional glowing iris (thumbnail use; the film's eyes have none)
            ir = r * sp.get('iris_r', 0.5)
            c.glow(px, py, ir * 1.9, ir * 1.9, sp['iris'], 120)
            c.radial(oval(px, py, ir * fs, ir), px - ir * 0.2, py - ir * 0.25, ir * 1.1,
                     [(0, '#ff6070', 255), (0.55, sp['iris'], 255), (1, '#7d0614', 255)], sy=1.0)
            c.line(oval(px, py, ir * fs, ir), c.lw * 0.32, '#4a0209', 255)
            pr = ir * sp.get('iris_pupil', 0.36)
        c.fill(oval(px, py, pr * fs, pr), '#0b0b0e')
        cl = max(pr * 0.3, 1.6)
        c.fill(oval(px - pr * 0.38 * fs, py - pr * 0.38, cl * fs, cl), '#f4f4f2')
        if det >= 2: c.fill(oval(px + pr * 0.35 * fs, py + pr * 0.3, cl * 0.45 * fs, cl * 0.45), '#f4f4f2', 200)
        shine = clamp(getattr(P, 'eyeshine', 0.0))
        if shine > 0.01:                         # delivery: eyeshine, the pupils catch the porch light like an animal's
            sr = lerp(pr, r * 0.66, ease_out_cubic(shine))
            c.fill(white, '#f6fffb', 120 * shine)
            c.radial(oval(px, py, sr * fs, sr), px, py, sr, [(0, '#ffffff', 255), (0.5, '#f4fffb', 255), (0.82, '#c6f2e4', 245),
                                                             (1, '#86d6c0', 220)], sy=1.0, a=shine)
        # upper lid
        lid_y = Y - r + (1.0 - min(op, 1.0)) * 2.0 * r
        if op < 0.99:
            lidp = smooth([(X - rx * 1.3, Y - r * 1.5), (X + rx * 1.3, Y - r * 1.5), (X + rx * 1.3, lid_y - r * 0.05),
                           (X, lid_y + r * 0.18 * (1 - op)), (X - rx * 1.3, lid_y - r * 0.05)], True, 0.6)
            c.fill(lidp, mix(skin, sh, 0.35))
            c.line(smooth([(X - rx * 1.1, lid_y - r * 0.05), (X, lid_y + r * 0.18 * (1 - op)), (X + rx * 1.1, lid_y - r * 0.05)], False), c.lw * 1.05)
        else:
            c.radial(None, X, Y - r * 1.05, rx * 1.1, [(0, '#5a4a4a', 70), (1, '#5a4a4a', 0)], sy=0.45, clip=False)
        # lower lid (squint / smile push)
        sq = P.squint * 0.75 + max(0.0, P.smile) * 0.12 * (1 - P.wide) * (0.0 if sp['lock'] >= 0.5 else 1.0)   # creepy: eyes never smile
        if sq > 0.03:
            ly2 = Y + r - sq * r * 1.1
            low = smooth([(X - rx * 1.3, Y + r * 1.5), (X - rx * 1.3, ly2 + r * 0.2), (X, ly2), (X + rx * 1.3, ly2 + r * 0.2), (X + rx * 1.3, Y + r * 1.5)], True, 0.6)
            c.fill(low, skin)
            c.line(smooth([(X - rx * 1.05, ly2 + r * 0.25), (X, ly2), (X + rx * 1.05, ly2 + r * 0.25)], False), c.lw * 0.6)
    if op < 0.99:
        with c.clip(rect(X - rx * 2, lid_y, rx * 4, r * 4)): c.line(white, c.lw * 0.85)
        c.line(smooth([(X - rx * 1.06, lid_y + r * 0.02), (X, lid_y + r * 0.18 * (1 - op) - 1), (X + rx * 1.06, lid_y + r * 0.02)], False), c.lw * 1.15)
    else:
        c.line(white, c.lw * 0.85)
    if sp['lashes'] > 0 and det >= 1:
        ly_ = max(Y - r, lid_y if op < 0.99 else Y - r)
        for k, ln in ((0.62, 7), (0.86, 9), (1.0, 8)):
            ang = -PI / 2 + side * k * 1.25
            x1, y1 = X + math.cos(ang) * rx, ly_ + (Y - r - ly_) * 0 + (math.sin(ang) + 1) * r * 0.5 * (1 if op >= 0.99 else 0.3)
            c.line(poly([(x1, y1), (x1 + side * ln * 0.75 * fs, y1 - ln * 0.6)], False), c.lw * 0.45 * sp['lashes'])
    # lower lash line
    if det >= 1:
        c.line(smooth([(X - rx * 0.7, Y + r * 0.86), (X, Y + r * 1.06), (X + rx * 0.7, Y + r * 0.86)], False), c.lw * 0.4, sp['skin_dp'], 120)
    return (X, Y, r, fs, px, py, op)


def _brow(c, hm, sp, P, side, eyeinfo):
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']; r = sp['eye_r'] * (1 + 0.16 * P.wide)
    up = P.brow_up + (P.brow_asym * 0.5 * side)
    if sp['hair'] == 'messy': up = min(up, 0.55)              # keep the brow tops clear of the fringe
    base = ey0 - r - 15 - 13 * up
    inner_dy = 13 * P.brow_angry - 14 * P.brow_sad
    outer_dy = -5 * P.brow_angry + 7 * P.brow_sad
    th = sp['brow_th']
    xi, xo = ex0 - side * 24, ex0 + side * 28
    pts_top = [(xi, base + inner_dy - th * 0.55), ((xi + xo) / 2, base - 6 - th * 0.5 + (inner_dy + outer_dy) * 0.3), (xo, base + outer_dy - th * 0.1)]
    pts_bot = [(xo, base + outer_dy + th * 0.25), ((xi + xo) / 2, base - 6 + th * 0.55 + (inner_dy + outer_dy) * 0.3), (xi, base + inner_dy + th * 0.55)]
    allp = pts_top + pts_bot
    X, Y, V = hm.map([p[0] for p in allp], [p[1] for p in allp], 3.0)
    if V.mean() < 0.1: return
    path = _pts_path(X, Y, True, 0.8)
    c.fill(path, sp['brow_c'])
    c.line(path, c.lw * 0.3, sp['brow_c'])
    if sp.get('brows') == 'bushy':                        # Grandpa: wiry white brow hairs sticking up and out
        hs = []
        for k in range(7):
            u = k / 6.0
            x0 = xi + (xo - xi) * u; y0 = base - 6 + (inner_dy + outer_dy) * 0.3 * (1 - abs(2 * u - 1)) + (inner_dy * (1 - u) + outer_dy * u) * 0.5
            a_, b_, v_ = hm.map1(x0, y0 - th * 0.3, 3.5)
            a2, b2, _ = hm.map1(x0 + side * (6 + 4 * u), y0 - th * 0.9 - 6 * hash01(k, 61 + side), 3.5)
            if v_ > 0.1: hs.append(poly([(a_, b_), (a2, b2)], False))
        c.line(path, c.lw * 0.45, mix(sp['brow_c'], '#7a746c', 0.6), 200)
        if hs: c.line(_multi(hs), c.lw * 0.35, sp['brow_c'], 230); c.line(_multi(hs), c.lw * 0.12, '#8a847c', 120)


def _nose(c, hm, sp, P, det, skin, sh):
    L = sp['nose_len']; ey = sp['eye_y']
    root_y, tip_y = ey + 4, sp['mouth_y'] - 28
    side = 1.0 if hm.st >= -0.05 else -1.0
    turned = abs(hm.st) > 0.32
    # soft shade under the nose
    X, Y, V = hm.map1(0, tip_y + 6, L * 0.4)
    if V > -0.2 and not turned:
        c.glow(X + 6 * side, Y + 4, 20, 9, sh, 90)
    if not turned and sp.get('nose') == 'button':        # dummy film: Owen's small round button nose
        X, Y, V = hm.map1(0, tip_y + 2, L * 0.8)
        fs_ = hm.sx(0, tip_y)
        tip = oval(X, Y, 10 * fs_, 8)
        c.fill(tip, mix(skin, sh, 0.15))
        c.line(smooth([(X - 10 * fs_, Y), (X - 6 * fs_, Y + 7), (X + 6 * fs_, Y + 7), (X + 10 * fs_, Y)], False), c.lw * 0.7)
        if det >= 1:
            for s2 in (-1, 1): c.fill(oval(X + s2 * 4.5 * fs_, Y + 4, 2.4 * fs_, 1.6), sp['skin_dp'], 170)
            c.fill(oval(X - 3 * fs_, Y - 3, 2.6 * fs_, 2), '#ffffff', 90)
        return
    if not turned:
        pts = [(side * 5, root_y + 6), (side * 9, tip_y - 6), (side * 13, tip_y + 2), (side * 7, tip_y + 9), (-side * 4, tip_y + 8)]
        dz = [3, L * 0.7, L * 0.85, L * 0.55, L * 0.35]
        if sp.get('nose') == 'hook':                      # the Kemp nose: long, a bump on the bridge, a heavy tip
            pts = [(side * 4, root_y + 4), (side * 10, root_y + 22), (side * 8, tip_y - 8), (side * 15, tip_y + 3), (side * 9, tip_y + 12),
                   (-side * 5, tip_y + 11)]
            dz = [3, L * 0.6, L * 0.75, L * 0.85, L * 0.55, L * 0.35]
        X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], np.array(dz))
        c.line(_pts_path(X, Y, False, 0.8), c.lw * 0.85)
        if det >= 1:
            for s2 in (-1, 1):
                nx, ny, nv = hm.map1(s2 * 9, tip_y + 6, L * 0.4)
                if nv > 0.1: c.fill(oval(nx, ny, 3.2 * hm.sx(s2 * 9, tip_y + 6), 2.2), sp['skin_dp'], 160)
        return
    pts = [(0, root_y), (0, tip_y), (0, tip_y + 8), (side * 0.0, tip_y + 12)]
    dz = np.array([4.0, L * 1.05, L * 0.7, 2.0])
    X, Y, V = hm.map([0, 0, 0, 0], [root_y, tip_y, tip_y + 9, tip_y + 13], dz)
    wedge = smooth([(X[0], Y[0]), (X[1], Y[1]), (X[2], Y[2]), (X[3] - side * 8, Y[3]), (X[0] - side * 10, Y[0] + 8)], True, 0.5)
    c.fill(wedge, skin)
    c.line(_pts_path(X[:3], Y[:3], False, 0.7), c.lw * 0.9)
    nx = X[2] - side * 9; ny = Y[2] - 1
    c.line(smooth([(nx + side * 5, ny - 6), (nx, ny), (nx + side * 4, ny + 3)], False), c.lw * 0.55)


def _mouth_geom(sp, P, t):
    """Mouth contour in front coords: returns (upper pts, lower pts, corner y, half width, open height)."""
    my = sp['mouth_y']
    o, wd, rd, sm, g = clamp(P.m_open), P.m_wide, clamp(P.m_round), clamp(P.smile, -1, 1), clamp(P.grin)
    hw = sp['mouth_w'] * (1.0 + 0.32 * wd - 0.48 * rd + 0.12 * o) + 10.0 * max(sm, 0) + 54.0 * g * sp.get('grin_k', 1.0)
    hw = max(hw, 8.0)
    cy = my - 12.0 * sm - 15.0 * g - 3 * o * (1 - rd)
    if sp.get('grin_lim'):                       # delivery: the grin saturates just inside the jaw line (never past it)
        lim = sp['grin_lim'] * float(np.interp(cy, sp['head_ys'], sp['head_ws'])) * (1.0 + 0.05 * g)
        k0 = 0.78 * lim
        if hw > k0: hw = k0 + (hw - k0) * (lim - k0) / (hw - k0 + lim - k0)
    side_lift = 9.0 * P.m_side
    up_mid = my + 3.0 * g + 1.5 * max(sm, 0) - 5.0 * o * rd - 1.0 * o - 3.0 * min(sm, 0) * 0.3
    open_h = 42.0 * o * (1 + 0.2 * rd) + 31.0 * g + 4.0 * max(sm, 0) * clamp(P.teeth) * (1 - g)
    lo_mid = up_mid + open_h
    # roundness pulls corners toward mid height
    cyr = lerp(cy, (up_mid + lo_mid) * 0.5, rd * min(1.0, o * 3))
    dn = clamp(-sm) * clamp((o - 0.4) / 0.35)                         # v2.1: terror pulls the corners down (∩ upper lip)
    cyr += dn * 0.34 * (lo_mid - up_mid)
    cl_y, cr_y = cyr - side_lift, cyr + side_lift * 0.4
    q = 0.55 + 0.3 * rd
    qu = q + 0.08 * dn; ql = q + 0.2 * dn
    upper = [(-hw, cl_y), (-hw * qu, up_mid - 0.2 * (up_mid - cl_y) - 2 * rd * o + 2 * dn), (0, up_mid), (hw * qu, up_mid - 0.2 * (up_mid - cr_y) - 2 * rd * o + 2 * dn), (hw, cr_y)]
    lower = [(hw, cr_y), (hw * ql, lo_mid - 0.35 * (lo_mid - cr_y) * (1 - rd) * (1 - dn)), (0, lo_mid), (-hw * ql, lo_mid - 0.35 * (lo_mid - cl_y) * (1 - rd) * (1 - dn)), (-hw, cl_y)]
    if P.tremble > 0.01:
        f = 2.6 * P.tremble
        for arr in (upper, lower):
            for i in range(1, len(arr) - 1):
                x_, y_ = arr[i]
                arr[i] = (x_, y_ + f * math.sin(x_ * 0.28 + t * 31.0 + i) + f * 0.6 * noise1(t * 9 + i, 5))
    return upper, lower, (cl_y, cr_y), hw, lo_mid - up_mid


def _densify(pts, n=3):
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for k in range(n):
            u = k / n; out.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u))
    out.append(pts[-1]); return out


def _mouth(c, hm, sp, P, det, t, skin, sh):
    upper, lower, (cly, cry), hw, oh = _mouth_geom(sp, P, t)
    dzf = lambda xs: 10.0 - 0.0 * np.asarray(xs)   # noqa: E731
    up_d = _densify(upper, 3); lo_d = _densify(lower, 3)
    UX, UY, UV = hm.map([p[0] for p in up_d], [p[1] for p in up_d], 6.0)
    if UV.max() < 0.1: return
    LX, LY, _ = hm.map([p[0] for p in lo_d], [p[1] for p in lo_d], 6.0)
    sm, g, te = P.smile, P.grin, clamp(P.teeth)
    # folds that make smiles read: nasolabial lines, cheek bulges, dimples
    fold_a = clamp(0.28 * sp['age'] + 0.55 * max(sm, 0) + 0.5 * g + 0.25 * P.m_wide)
    if fold_a > 0.05:
        for s in (-1, 1):
            cx_ = s * (hw + 7)
            pts = [(s * 22, sp['mouth_y'] - 30), (s * (hw * 0.55 + 22), sp['mouth_y'] - 14 - 6 * g), (cx_, (cly if s < 0 else cry) + 6)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 5.0)
            if V.min() > 0.0: c.line(_pts_path(X, Y, False), c.lw * (0.5 + 0.2 * g), sp['skin_dp'], 200 * fold_a)
    if g > 0.25 and det >= 1:
        for s in (-1, 1):
            pts = [(s * 50, sp['eye_y'] + 34), (s * 64, sp['eye_y'] + 42), (s * 72, sp['eye_y'] + 34)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 3.0)
            if V.min() > 0.05: c.line(_pts_path(X, Y, False), c.lw * 0.45, sp['skin_dp'], 160 * (g - 0.25) / 0.75)
    lipk = sp.get('lips', 0.0)
    if lipk > 0 and det >= 1:                                         # coloured lips (officer2, mum)
        top_ = [(x, y - 5.5 * (1 - abs(x) / (hw + 1e-6)) ** 0.6 - 1.0) for x, y in up_d]
        bot_ = [(x, y + 8.5 * (1 - abs(x) / (hw + 1e-6)) ** 0.7 + 1.0) for x, y in lo_d]
        TX, TY, _ = hm.map([p[0] for p in top_], [p[1] for p in top_], 7.0)
        BX, BY, _ = hm.map([p[0] for p in bot_], [p[1] for p in bot_], 7.0)
        lips = _pts_path(np.concatenate([TX, BX[1:-1]]), np.concatenate([TY, BY[1:-1]]), True, 0.85)
        c.fill(lips, sp['lip'], 255 * lipk)
        c.line(lips, c.lw * 0.45, mix(sp['lip'], '#000000', 0.45), 200 * lipk)
        if det >= 2: c.glow(float(BX[len(BX) // 2]) - 4, float(BY[len(BY) // 2]) - 4, 9, 3, '#ffffff', 90 * lipk)
    if oh < 2.2:                                                      # closed mouth: one expressive line
        line = _pts_path(UX, UY, False, 0.9)
        c.line(line, c.lw * (0.95 + 0.25 * P.m_press))
        if det >= 1:
            lx_, ly_, lv = hm.map1(0, max(p[1] for p in upper) + 10 + 3 * P.m_press, 8.0)
            if lv > 0: c.line(smooth([(lx_ - 11, ly_), (lx_, ly_ + 2.5), (lx_ + 11, ly_)], False), c.lw * 0.45, sp['skin_dp'], 150)
            for s in (-1, 1):
                if sm > 0.2 or P.m_press > 0.2:
                    i = 0 if s < 0 else -1
                    x_, y_ = UX[i], UY[i]
                    c.line(smooth([(x_ - s * 2, y_ - 6), (x_ + s * 3, y_), (x_ - s * 1, y_ + 6)], False), c.lw * 0.45, LINE, 200)
        return
    ring_x = np.concatenate([UX, LX[1:-1]]); ring_y = np.concatenate([UY, LY[1:-1]])
    inner = _pts_path(ring_x, ring_y, True, 0.85)
    # lip volume below the mouth (close-ups)
    if det >= 1:
        lip = _pts_path(np.concatenate([LX, LX[::-1]]), np.concatenate([LY, (LY + 9 + 4 * P.m_open)[::-1]]), True, 0.8)
        c.fill(lip, mix(sp['lip'], skin, 0.4), 110)
    c.fill(inner, '#2a0e11')
    mid_x = float(np.mean(ring_x)); bot = float(LY[len(LY) // 2]); top = float(UY[len(UY) // 2])
    with c.clip(inner):
        if oh > 16 and g < 0.8:
            c.fill(oval(mid_x, bot - oh * 0.08, hw * 0.62 * hm.sx(0, sp['mouth_y']), oh * 0.32), '#93434d')
            if det >= 1: c.line(smooth([(mid_x, bot - oh * 0.3), (mid_x, bot - oh * 0.05)], False), c.lw * 0.35, '#5e2129', 150)
        c.glow(mid_x, top + oh * 0.55, hw * 0.9, oh * 0.6, '#000000', 140)
        tshow = max(te, 0.85 * clamp(g * 1.4))
        if tshow > 0.02:
            gum = 7.0 * clamp(P.gums) + 2.0 * g
            th_u = min(oh * (0.5 if g > 0.3 else 0.42), 13.0 + 6 * g) * clamp(tshow * 1.3)
            th_u *= 1.0 - clamp(-min(sm, 0.0) * 1.6) * clamp((P.m_open - 0.4) / 0.3)   # terror: bottom row only
            th_l = min(oh * (0.5 if g > 0.3 else 0.3), 11.0 + 6 * g) * clamp(tshow * 1.3) * (1.0 if g > 0.2 or P.m_wide > 0.3 else 0.6)
            if gum > 0.3:
                gp = _pts_path(np.concatenate([UX, UX[::-1]]), np.concatenate([UY - 2, (UY + gum)[::-1]]), True, 0.8)
                c.fill(gp, '#b9616d')
                if det >= 1: c.line(_pts_path(UX, UY + gum, False), c.lw * 0.3, '#7d3540', 160)
            _teeth_row(c, hm, sp, UX, UY + gum, th_u, +1, det, P, hw)
            if th_l > 1.0:
                _teeth_row(c, hm, sp, LX[::-1], LY[::-1], th_l, -1, det, P, hw)
    c.line(inner, c.lw)
    for s, i in ((-1, 0), (1, -1)):                                   # corner tucks
        x_, y_ = UX[i], UY[i]
        c.line(smooth([(x_ + s * 1, y_ - 7), (x_ + s * 4, y_), (x_ + s * 1, y_ + 7)], False), c.lw * 0.55)


def _teeth_row(c, hm, sp, X, Y, th, direction, det, P, hw):
    """A row of individual teeth hanging from (upper, direction +1) or standing on (lower, -1) the contour X, Y."""
    X = np.asarray(X); Y = np.asarray(Y)
    x0, x1 = float(X[0]), float(X[-1])
    span = x1 - x0
    if span < 4: return
    n = int(clamp(round(abs(span) / (sp.get('tooth_w', 13.0) if det >= 1 else 18.0)), 4, 20))
    if n % 2: n += 1
    edges = np.linspace(0, 1, n + 1)
    # front teeth wider: warp positions toward the centre
    edges = 0.5 + (edges - 0.5) * (0.82 + 0.18 * np.abs(edges - 0.5) * 2)
    ex = x0 + edges * span
    ey = np.interp(ex, X if x1 > x0 else X[::-1], Y if x1 > x0 else Y[::-1])
    # band polygon
    band_pts = []
    bot = []
    for i in range(n):
        xa, xb = ex[i], ex[i + 1]
        ya, yb = ey[i], ey[i + 1]
        centre = abs((i + 0.5) / n - 0.5) * 2
        h = th * (1.0 - 0.38 * centre ** 2) * (0.92 + 0.12 * hash01(i, 31))
        bot.append((xa, ya + direction * h * 0.92))
        bot.append(((xa + xb) / 2, (ya + yb) / 2 + direction * h))
    bot.append((ex[-1], ey[-1] + direction * th * 0.55))
    top = list(zip(ex.tolist(), (ey - direction * 3).tolist()))
    band = poly(top + bot[::-1], True)
    tooth = '#e8e2d2'
    c.fill(band, tooth)
    if det >= 1:
        cxm = (x0 + x1) / 2
        c.grad(band, x0, 0, x1, 0, [(0, '#8e8470', 255), (0.22, tooth, 0), (0.78, tooth, 0), (1, '#8e8470', 255)])
        if det >= 2:
            for i in range(n):                                        # grime on a couple of teeth
                hv = hash01(i, 77 + int(P.grin * 0))
                if hv > 0.8:
                    xa, xb = ex[i], ex[i + 1]
                    c.fill(rect(min(xa, xb) + 1, min(ey[i], ey[i] + direction * th) , abs(xb - xa) - 2, th), '#b4a27a', 70)
    if sp.get('gap') and direction > 0 and n >= 4:              # Owen: a missing front tooth (a dark gap)
        i = n // 2
        xa, xb = ex[i], ex[i + 1]
        gp = poly([(xa + 0.8, ey[i] - 2), (xb - 0.8, ey[i + 1] - 2), (xb - 0.8, ey[i + 1] + th * 1.05), (xa + 0.8, ey[i] + th * 1.05)])
        c.fill(gp, '#2a0e11')
    c.line(_pts_path(np.array([p[0] for p in bot]), np.array([p[1] for p in bot]), False, 0.6), c.lw * 0.45)
    seps = []
    for i in range(1, n):
        ya = ey[i]
        h = th * (1.0 - 0.38 * (abs(i / n - 0.5) * 2) ** 2) * 0.95
        seps.append(poly([(ex[i], ya - direction * 2), (ex[i] + (0.6 if ex[i] < (x0 + x1) / 2 else -0.6), ya + direction * h)], False))
    c.line(_multi(seps), c.lw * (0.42 if det >= 1 else 0.5))


def _jaw_y(sp, x):
    """Front-view y of the face outline below the cheek at |x| (where a tear running down meets the jaw)."""
    ys = np.asarray(sp['head_ys'], float); ws = np.asarray(sp['head_ws'], float)
    k = ys >= 20.0
    yy, ww = ys[k][::-1], ws[k][::-1]                    # ascending width from the chin up
    return float(np.interp(abs(x), ww, yy))


def _tears(c, hm, sp, P, t, det, eyes):
    """v2.1 tears: 2 pale-blue (#a8c8f0) tapered wet streaks per eye with a thin white highlight, no dark outline. They
    run down the cheek and stop at the jaw outline, where a drop gathers and falls. Below the glasses rim on mum."""
    a = clamp(P.tears)
    if a <= 0.01: return
    glasses = sp.get('glasses')
    for side, info in eyes.items():
        if info is None: continue
        ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']; r = sp['eye_r']
        for k, off in enumerate((-0.42, 0.5)):
            x_start = ex0 + side * off * r
            y_start = ey0 + r * 0.92 + (31.0 - r * 0.92 if glasses else 0.0)
            drift = side * (5 + 4 * k)
            y_end = _jaw_y(sp, x_start + drift) - 3.0
            Lmax = max(4.0, y_end - y_start)
            L = Lmax * clamp(a * 1.25) * (0.88 + 0.12 * k)
            n = 9
            us = np.linspace(0, 1, n)
            xs = x_start + drift * us + 2.2 * np.sin(us * 5 + k * 2 + side) * us
            ys = y_start + L * us
            w = (2.3 - 0.9 * us) * (0.75 + 0.25 * a)
            X, Y, V = hm.map(xs, ys, 4.0)
            if V[0] < 0.1 or V[-1] < 0.0: continue
            dx = np.gradient(X); dy = np.gradient(Y); nn = np.hypot(dx, dy) + 1e-6
            nxs, nys = -dy / nn, dx / nn
            Lx = np.concatenate([X + nxs * w, (X - nxs * w)[::-1]]); Ly = np.concatenate([Y + nys * w, (Y - nys * w)[::-1]])
            rib = _pts_path(Lx, Ly, True, 0.7)
            c.fill(rib, '#a8c8f0', 200)
            if det >= 1: c.line(_pts_path(X - nxs * w * 0.35, Y - nys * w * 0.35, False), c.lw * 0.22, '#f4f9ff', 220)
            # one bead running down the streak
            u = ((t * (0.45 + 0.1 * k) + hash01(3 * k + side + 1, 11)) % 1.0)
            if det >= 1 and u * L > 6:
                i_f = u * (n - 1); i0 = int(i_f); fr = i_f - i0; i1 = min(i0 + 1, n - 1)
                bx = X[i0] + (X[i1] - X[i0]) * fr; by = Y[i0] + (Y[i1] - Y[i0]) * fr
                bw = w[i0] * 1.25
                c.fill(smooth([(bx, by - bw * 1.7), (bx + bw, by + bw * 0.2), (bx, by + bw * 1.15), (bx - bw, by + bw * 0.2)], True), '#bcd8f8', 220)
                c.fill(oval(bx - bw * 0.3, by - bw * 0.15, bw * 0.3), '#ffffff', 220)
            if a > 0.7 and L >= Lmax * 0.85:                     # a drop gathers on the jaw line and falls
                u2 = (t * 0.6 + 0.37 * k + 0.5 * side) % 1.0
                grow = clamp(u2 / 0.6); fall = clamp((u2 - 0.6) / 0.4)
                bx, by = X[-1], Y[-1] + 2 + 40.0 * ease_in_cubic(fall)
                rr = (1.6 + 2.2 * grow) * (0.8 + 0.2 * a)
                c.fill(smooth([(bx, by - rr * 1.5), (bx + rr, by + rr * 0.3), (bx, by + rr * 1.2), (bx - rr, by + rr * 0.3)], True), '#bcd8f8',
                       230 * (1 - 0.7 * fall))


def _sweat(c, hm, sp, P, t, det):
    a = clamp(P.sweat)
    if a <= 0.02: return
    spots = [(-58, -66, 0), (32, -72, 1), (70, -40, 2), (-74, -20, 3), (8, -60, 4), (52, 6, 5)]
    for (x0, y0, k) in spots[:int(2 + 4 * a)]:
        slide = ((t * 0.08 + hash01(k, 3)) % 1.0)
        yy = y0 + 22 * slide
        X, Y, V = hm.map1(x0, yy, 3.0)
        if V < 0.15: continue
        s_ = (5.5 + 2 * hash01(k, 9)) * (0.7 + 0.3 * a)
        d = smooth([(X, Y - s_ * 1.7), (X + s_, Y + s_ * 0.3), (X, Y + s_ * 1.1), (X - s_, Y + s_ * 0.3)], True)
        c.fill(d, '#dde8f2', 200 * (1 - 0.5 * slide))
        c.line(d, c.lw * 0.28, '#7d93ab', 200 * (1 - 0.5 * slide))
        c.fill(oval(X - s_ * 0.3, Y - s_ * 0.2, s_ * 0.3), '#ffffff', 220)


def _wrinkles(c, hm, sp, P, det, sh):
    """v2.1: a few clean fold lines (VISUAL_SPEC: flat fills, one shade step, no hatching). Forehead folds only when the
    brows lift (2, a third on big lifts), frown lines only on angry / pained brows, one chin crease, soft jowls on the
    old. Eye bags (drawn with the eyes) carry the age. Weight 0.35x the outline."""
    age = sp['age']
    dp = sp['skin_dp']
    ey = sp['eye_y']; r = sp['eye_r']
    lw = c.lw * 0.35
    lift = P.brow_up + 0.6 * P.brow_sad + 0.3 * P.wide
    a_f = clamp((lift - 0.3) / 0.5)
    if a_f > 0.03 and det >= 1:
        folds = []
        for k, yy in enumerate((-60, -49, -39)):
            if k == 2 and (det < 2 or a_f < 0.6): break
            w_ = 34 - k * 6
            mid = yy - 3 - 3 * P.brow_sad
            pts = [(-w_, yy + 2), (0, mid), (w_, yy + 2)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 2.0)
            if V.min() > 0.05: folds.append(_pts_path(X, Y, False))
        if folds: c.line(_multi(folds), lw, dp, 150 * a_f)
    a_v = clamp(1.1 * P.brow_angry + 0.6 * P.brow_sad - 0.25)
    if a_v > 0.05 and det >= 1:
        ls = []
        for s_ in (-1, 1):
            pts = [(s_ * 7, ey - r - 21), (s_ * 9, ey - r - 9)]
            X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 4.0)
            if V.min() > 0.1: ls.append(_pts_path(X, Y, False))
        if ls: c.line(_multi(ls), lw * 1.1, dp, 160 * a_v)
    if det >= 1:
        a_ch = clamp(0.2 * age + 0.5 * max(-P.smile, 0) + 0.4 * P.m_press)
        cy_ = min(100.0, _jaw_y(sp, 0.0) - 18)
        X, Y, V = hm.map([-11, 0, 11], [cy_, cy_ - 3 - 3 * P.m_press, cy_], 6.0)
        if V.min() > 0.1 and a_ch > 0.05: c.line(_pts_path(X, Y, False), lw, dp, 140 * a_ch)
        if age > 0.7:
            ls = []
            for s_ in (-1, 1):
                ys_ = [66.0, 80.0, 92.0]
                xs_ = [s_ * 0.66 * float(np.interp(y_, sp['head_ys'], sp['head_ws'])) for y_ in ys_]
                X, Y, V = hm.map(xs_, ys_, 3.0)
                if V.min() > 0.1: ls.append(_pts_path(X, Y, False))
            if ls: c.line(_multi(ls), lw, dp, 90 * age)


def _scar(c, hm, sp, side, det):
    x0, y0 = side * (sp['mouth_w'] + 9), sp['mouth_y'] + 2
    X, Y, V = hm.map([x0, x0 + side * 4, x0 + side * 6], [y0 - 9, y0 + 1, y0 + 11], 6.0)
    if V.min() < 0.12: return
    p = _pts_path(X, Y, False)
    c.line(p, c.lw * 0.75, '#d8a39d', 255)
    c.line(p, c.lw * 0.3, '#8d5552', 200)
    if det >= 1:
        for k in range(3):
            u = 0.2 + 0.3 * k
            x_ = X[0] + (X[-1] - X[0]) * u; y_ = Y[0] + (Y[-1] - Y[0]) * u
            c.line(poly([(x_ - 4, y_ + 1.5), (x_ + 4, y_ - 1.5)], False), c.lw * 0.22, '#8d5552', 180)


def _stubble(c, hm, sp, det, sil):
    a = sp['stub']
    if a <= 0 or not sp.get('stubble'): return
    my = sp['mouth_y']
    pts = [(-92, 34), (-84, 82), (-58, 108), (0, 122), (58, 108), (84, 82), (92, 34), (60, my - 6), (24, my - 16), (0, my - 14),
           (-24, my - 16), (-60, my - 6)]
    X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 1.0)
    reg = inter(_pts_path(X, Y, True, 0.8), sil)
    c.fill(reg, sp['stubble'], 26 * a)


def _nape(ph):
    """Back of the skull: the hair covers it down to the nape (behind the ears it drops to ~y 84, at the back ~y 96), so
    a head seen from behind is hair over the whole skull, small ears and a neck strip (no pale 'face' oval)."""
    return np.interp(np.abs(ph), [0.0, 1.66, 1.82, 2.1, PI], [-400.0, -400.0, 36.0, 84.0, 96.0])


def _hairline(style, part):
    """(yf(phi) -> hairline height round the head, grow) for a hair style."""
    if style == 'short':
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 1.05, 1.25, 1.62, 2.3, PI], [-74, -72, -30, -24, 12, 30])
        grow = 3.0
    elif style == 'crop':                                        # driver: short back and sides down to a low nape
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 1.05, 1.25, 1.62, 2.1, PI], [-74, -72, -26, -18, 40, 74])
        grow = 3.0
    elif style == 'bun':
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.55, 0.95, 1.3, 1.7, 2.3, PI], [-74, -72, -50, -6, 4, 26, 36])
        grow = 6.0
    elif style == 'messy':
        def yf0(ph):
            a = np.abs(ph)
            fr = -70.0 + 6.0 * np.sin(ph * 3.0 + part) + 7.0 * part * np.clip(ph * part, 0, 1)
            return np.interp(a, [0, 1.0, 1.3, 1.6, 2.0, PI], [0, 0, 1, 1, 1, 1]) * (np.interp(a, [1.0, 1.3, 1.6, 2.15, 2.6, PI], [-60, -24, -14, 50, 78, 88])) + \
                (1 - np.interp(a, [0, 1.0, 1.3], [0, 0, 1])) * fr
        grow = 9.0
    elif style == 'painted':                                     # Mister Winks: carved hair, hard side part on his left
        def yf0(ph):
            return np.interp(ph, [-PI, -2.35, -2.0, -1.78, -1.5, -1.25, -0.95, -0.35, 0.28, 0.42, 0.56, 0.95, 1.25, 1.5, 1.78, 2.0, 2.35, PI],
                             [92.0, 88.0, 40.0, -24.0, -32.0, -52.0, -68.0, -78.0, -83.0, -96.0, -84.0, -72.0, -52.0, -34.0, -24.0, 38.0, 88.0, 92.0])
        return yf0, 5.0
    elif style == 'shaggy':                                      # you: curtain bangs parted in the middle, over the ears
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.12, 0.3, 0.6, 0.95, 1.2, 1.6, 1.9, 2.3, PI], [-84, -62, -52, -46, -30, -8, 6, 40, 82, 90])
        return yf0, 11.0
    elif style == 'cowlick':                                     # Owen: short boy's cut, an uneven fringe
        def yf0(ph):
            a = np.abs(ph)
            fr = -62.0 + 4.0 * np.sin(ph * 9.0) * (a < 0.9)
            return np.interp(a, [0, 0.9, 1.2, 1.55, 2.1, PI], [0, 0, 1, 1, 1, 1]) * np.interp(a, [0.9, 1.2, 1.55, 2.1, 2.6, PI], [-56, -26, -18, 54, 80, 86]) + \
                (1 - np.interp(a, [0, 0.9, 1.2], [0, 0, 1])) * fr
        return yf0, 8.0
    elif style == 'lowbun':                                      # mom: centre part, pulled back over the ears to a low bun
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.12, 0.6, 1.0, 1.3, 1.7, 1.95, 2.3, PI], [-78, -71, -64, -46, -14, -8, 50, 80, 86])
        return yf0, 6.0
    elif style == 'pomp':                                        # young Walter: thick 70s hair, side part, long sideburns
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.8, 1.08, 1.18, 1.38, 1.5, 1.72, 1.9, 2.2, PI], [-70, -64, -48, 34, 34, -14, -16, 44, 82, 90])
        return yf0, 14.0
    elif style == 'bald':                                        # Grandpa: the LOWER edge of the white fringe (see _bald_fringe)
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 1.16, 1.24, 1.4, 1.65, 2.2, PI], [-400, -400, -2, 10, 22, 60, 70])
        return yf0, 10.0
    elif style == 'kid':                                         # Lily: bob with straight bangs, hair framing the face
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.62, 0.86, 1.02, 1.2, PI], [-46, -50, -40, 30, 112, 112])
        return yf0, 13.0
    else:  # curly
        def yf0(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 0.9, 1.25, 1.55, 2.0, 2.5, PI], [-58, -54, -20, -6, 40, 60, 66])
        grow = 22.0
    return (lambda ph: np.maximum(yf0(ph), _nape(ph))), grow


def _nape_cut(hm, sp):
    """Seen from behind (yaw past ~100 deg): the part of the head silhouette below the back hairline is the jaw, which a
    real head hides behind the skull and neck. Returns the region to leave out of the skull fill (the body's neck shows
    there), or None."""
    if not sp.get('hair') or sp['hair'] == 'kid' or -hm.ct < 0.2: return None
    yf, _ = _hairline(sp['hair'], sp['part'])
    phis = np.linspace(-PI, PI, 160, endpoint=False)
    phis = phis[np.abs(phis) >= 1.8]
    y0 = yf(phis)
    w = np.maximum(hm.W(np.clip(y0, -120, 120)), 1.0)
    c_, s_ = np.cos(phis), np.sin(phis)
    px = w * s_; pz = hm.DB * w * c_
    Y = hm.J(y0) * hm.cp + pz * hm.spi
    z1 = pz * hm.cp - y0 * hm.spi
    X = px * hm.ct + z1 * hm.st
    vis = (-s_ * hm.DB * hm.st + c_ * hm.ct) > -0.02
    if vis.sum() < 3: return None
    X, Y = X[vis], Y[vis]
    o = np.argsort(X); X, Y = X[o], Y[o]
    Y = np.minimum(Y + 2.0, 118.0)
    near_back = abs(hm.st) < 0.5
    ext_l = 300.0 if (near_back or hm.st > 0) else 0.0
    ext_r = 300.0 if (near_back or hm.st < 0) else 0.0
    pts = [(float(X[0]) - ext_l, float(Y[0]) + (0.0 if ext_l else 400.0))] + [(float(x), float(y)) for x, y in zip(X, Y)] + \
          [(float(X[-1]) + ext_r, float(Y[-1]) + (0.0 if ext_r else 400.0)), (float(X[-1]) + ext_r, 500.0), (float(X[0]) - ext_l, 500.0)]
    return poly(pts, True)


_NEW_HAIR = ('shaggy', 'cowlick', 'lowbun', 'pomp', 'bald')
_EARLESS = ('kid', 'shaggy')


def _region_above(X, Y, top=-420.0):
    return poly([(float(X[0]) - 300, top)] + [(float(x), float(y)) for x, y in zip(X, Y)] + [(float(X[-1]) + 300, top)], True)


def _strands(c, hm, lines, grow, lw, colr, a):
    """Hair strand lines given as [(phis, ys)] on the head surface (drawn only where they face the camera)."""
    ps = []
    for ph, ys in lines:
        X, Y, V = _sph(hm, ph, ys, grow)
        m = V > 0.02
        if m.sum() > 2: ps.append(_pts_path(X[m], Y[m], False, 0.9))
    if ps: c.line(_multi(ps), lw, colr, a)


def _lowbun(c, hm, sp, det, behind):
    """Mom's low bun at the nape (drawn behind the skull when it faces away, over the hair when we see the back)."""
    X, Y, V = _sph(hm, np.array([PI]), np.array([54.0]), 20.0)
    X, Y, V = float(X[0]), float(Y[0]), float(V[0])
    if (V < 0) != behind: return
    hc = sp['hair_c']; hsh = mix(hc, '#000000', 0.4); hhi = mix(hc, '#ffffff', 0.22)
    rx = 30.0 * (0.75 + 0.25 * abs(hm.st)); ry = 25.0
    bun = oval(X, Y, rx, ry)
    c.fill(bun, hc); c.radial(bun, X - 8, Y - 10, rx * 1.3, [(0, hhi, 160), (0.6, hc, 0), (1, hsh, 220)])
    if det >= 1:
        c.line(_multi([smooth([(X - rx * 0.8, Y - 4 + k * 8), (X, Y - 12 + k * 8), (X + rx * 0.8, Y - 2 + k * 8)], False) for k in range(3)]),
               c.lw * 0.35, hsh, 180)
    c.line(bun, c.lw)


def _hair_new(c, hm, sp, P, det, sil, t):
    """The dummy film's hair styles: 'shaggy' (you), 'cowlick' (Owen), 'lowbun' (mom), 'pomp' (young Walter), 'bald'
    (Grandpa's white fringe over big ears, liver spots and a shine on the dome)."""
    style = sp['hair']; hc = sp['hair_c']
    hsh = mix(hc, '#000000', 0.38); hhi = mix(hc, '#ffffff', 0.28)
    yf, grow = _hairline(style, sp['part'])
    X, Y = hm.arc_phi(yf, 120)
    if len(X) < 3: return
    region = _region_above(X, Y)
    if style == 'shaggy':
        vol = _bumpy(hm, grow, 9, 5.0, -125.0, 92.0, spiky=True, seed=4)
    elif style == 'cowlick':
        vol = _bumpy(hm, grow, 11, 6.0, -127.0, 94.0, spiky=True, seed=1)
    elif style == 'lowbun':
        vol = hm.silhouette(grow=grow, y_top=-120 - grow * 0.5, y_bot=80)
    elif style == 'pomp':
        vol = union(hm.silhouette(grow=grow, y_top=-120 - grow * 1.1, y_bot=50), hm.silhouette(grow=4.0, y_top=-120, y_bot=60))
        fx, fy, fv = hm.map1(-14, -104, 16)
        vol = union(vol, oval(fx, fy - 4, 70 * max(0.6, hm.sx(-14, -104, 16)), 26))
    else:                                                       # bald: a fluffy fringe between two lines round the back
        vol = _bumpy(hm, grow, 22, 6.0, -100.0, 84.0, spiky=False)
        def yu(ph):
            a = np.abs(ph)
            return np.interp(a, [0, 1.16, 1.24, 1.4, 1.65, 2.0, 2.6, PI], [400.0, 400.0, -8.0, -26.0, -42.0, -54.0, -60.0, -62.0])
        Xu, Yu = hm.arc_phi(yu, 120)
        if len(Xu) < 3: return
        Yu = Yu + 4.5 * np.sin(Xu * 0.33) + 2.5 * np.sin(Xu * 0.71 + 1.0)       # a wispy, uneven top edge
        region = inter(region, _region_above(Xu, Yu, 420.0))
    hair = inter(union(vol, sil), region)
    if style == 'bald':                                         # the dome: liver spots and a shine (under the fringe)
        if det >= 1:
            spots = [(-58, -76, 7), (48, -88, 5), (-26, -100, 4.5), (66, -58, 4), (-74, -40, 3.5), (12, -108, 3.5)]
            Xs, Ys, Vs = hm.map([p[0] for p in spots], [p[1] for p in spots], 1.0)
            ds = [oval(float(Xs[i]), float(Ys[i]), spots[i][2] * hm.sx(spots[i][0], spots[i][1]), spots[i][2] * 0.8) for i in range(len(spots)) if Vs[i] > 0.1]
            if ds: c.fill(_multi(ds), '#9c7258', 120 * sp.get('spots', 1.0))
        gx, gy, gv = hm.map1(-28, -96, 2)
        if gv > -0.2:
            c.glow(gx, gy, 34, 16, '#ffffff', 80)
            c.line(smooth([(gx - 20, gy + 4), (gx - 4, gy - 4), (gx + 16, gy - 2)], False), c.lw * 0.5, '#ffffff', 120)
    c.fill(hair, hc)
    with c.clip(hair):
        c.radial(None, -30, -90, 175, [(0, hhi, 120), (0.5, hc, 0), (1, hsh, 200)], clip=False)
        if det >= 1:
            L = []
            if style == 'shaggy':                               # curtain bangs from the centre part, sweeping out and down
                for k in range(5):
                    for sd in (-1, 1):
                        ph = sd * np.linspace(0.02 + 0.03 * k, 0.4 + 0.25 * k, 8)
                        L.append((ph, np.linspace(-118.0 + 6 * k, -42.0 + 10 * k, 8)))
                for k in range(8):
                    ph0 = 1.7 + k * 0.2
                    L.append((np.full(6, ph0), np.linspace(-110.0, 70.0, 6))); L.append((np.full(6, -ph0), np.linspace(-110.0, 70.0, 6)))
            elif style == 'cowlick':
                for k in range(8):
                    ph = np.linspace(-0.8 + 0.2 * k, -0.6 + 0.2 * k, 5)
                    L.append((ph, np.linspace(-120.0, -64.0, 5)))
            elif style == 'lowbun':                             # combed back from the part
                for k in range(1, 6):
                    for sd in (-1, 1):
                        ph = sd * np.linspace(0.06, 1.6 + 0.2 * k, 9)
                        L.append((ph, np.linspace(-118.0 + 4 * k, -60.0 + 16 * k, 9)))
            elif style == 'pomp':
                for k in range(6):
                    ph = np.linspace(-0.45, 1.1 + 0.15 * k, 9)
                    L.append((ph, np.linspace(-124.0 + 5 * k, -84.0 + 12 * k, 9)))
            elif style == 'bald':
                for k in range(10):
                    ph0 = 1.25 + k * 0.2
                    for sd in (-1, 1):
                        L.append((np.full(4, sd * ph0) + sd * np.linspace(0, 0.08, 4), np.linspace(-58.0 + 3 * k, 20.0 + 4 * k, 4)))
            _strands(c, hm, L, grow * 0.5, c.lw * 0.32, hsh, 160)
        if style == 'pomp':                                     # brilliantine shine on the wave
            Xs, Ys, Vs = _sph(hm, np.linspace(-0.6, 0.7, 8), np.linspace(-104.0, -112.0, 8), grow)
            m = Vs > 0.1
            if m.sum() > 2: c.line(_pts_path(Xs[m], Ys[m], False), c.lw * 1.8, '#ffffff', 60)
    if style == 'lowbun' or style == 'pomp':                    # the part
        ph0 = 0.0 if style == 'lowbun' else -0.45
        Xp, Yp, Vp = _sph(hm, np.full(6, ph0), np.linspace(-78.0 if style == 'lowbun' else -70.0, -119.0, 6), 1.0)
        m = Vp > 0.02
        if m.sum() > 2: c.line(_pts_path(Xp[m], Yp[m], False), c.lw * 0.6, mix(hsh, '#000000', 0.3))
    c.line(hair, c.lw)
    if style == 'cowlick':                                      # the tuft at the crown that never lies down
        X0, Y0, V0 = _sph(hm, np.array([-0.4]), np.array([-116.0]), grow)
        x0, y0 = float(X0[0]), float(Y0[0])
        k_ = 1.0 if hm.ct > -0.3 else -1.0
        tuft = smooth([(x0 - 12, y0 + 6), (x0 - 10 * k_, y0 - 14), (x0 + 2 * k_, y0 - 34), (x0 + 4 * k_, y0 - 16), (x0 + 16 * k_, y0 - 30),
                       (x0 + 14 * k_, y0 - 6), (x0 + 12, y0 + 6)], True, 0.55)
        c.fill(tuft, hc); c.line(tuft, c.lw * 0.9)
        c.fill(_crescent(tuft, -4, 3), hsh, 120)
    if style == 'lowbun' and det >= 1 and hm.map1(0, 0)[2] > 0.0:   # loose strands that slipped out, framing her face
        for sd in (-1, 1):
            if -sd * hm.st > 0.3: continue                      # only at the face's edge, never across the cheek
            ph = sd * np.linspace(1.12, 1.3, 6)
            ys = np.linspace(-50.0, 44.0, 6)
            X_, Y_, V_ = _sph(hm, ph, ys, 4.0)
            m = V_ > 0.0
            if m.sum() > 2:
                q = _pts_path(X_[m] + sd * 3.0 * np.sin(np.linspace(0, 3, int(m.sum()))), Y_[m], False)
                c.line(q, c.lw * 0.8, LINE); c.line(q, c.lw * 0.4, hhi)
    if style == 'bald' and det >= 1:                            # two wisps of white hair on the dome
        for sd in (-1, 1):
            X_, Y_, V_ = hm.map([sd * 8, sd * 14, sd * 6], [-112, -128, -134], 2.0)
            if V_.min() > -0.3: c.line(_pts_path(X_, Y_, False), c.lw * 0.5, mix(hc, '#9a958e', 0.3), 230)


def _hair_region(c, hm, sp, P, det, sil, t):
    style = sp['hair']; hc = sp['hair_c']
    if style in _NEW_HAIR: return _hair_new(c, hm, sp, P, det, sil, t)
    hsh = mix(hc, '#000000', 0.35); hhi = mix(hc, '#ffffff', 0.25)
    part = sp['part']
    yf, grow = _hairline(style, part)
    if style == 'kid':
        X, Y = hm.arc_phi(yf, 120)
    else:
        X, Y = hm.arc(yf, 44)
    if len(X) < 3: return
    if style != 'kid':
        order = np.argsort(X)
        X, Y = X[order], Y[order]
    top = -400.0
    region = poly([(float(X[0]) - 300, top)] + [(float(x), float(y)) for x, y in zip(X, Y)] + [(float(X[-1]) + 300, top)], True)
    vol = hm.silhouette(grow=grow, y_top=-120 - grow * 0.4, y_bot=70)
    if style == 'curly':
        vol = _cloud(hm, grow, 14, 11.0)
    elif style == 'kid':
        vol = union(hm.silhouette(grow=grow, y_top=-120 - grow * 0.5, y_bot=40), _kid_hang(hm, grow, 112.0))
    elif style == 'messy':
        vol = _bumpy(hm, grow, 9, 9.0, -128.0, 94.0, spiky=True, seed=part)   # down to the nape (back views)
    hair = inter(union(vol, sil), region)
    c.fill(hair, hc)
    with c.clip(hair):
        c.radial(None, -30, -90, 175, [(0, hhi, 120), (0.5, hc, 0), (1, hsh, 200)], clip=False)
        if det >= 1 and style in ('messy', 'short', 'bun', 'crop'):
            for k in range(7 if det >= 2 else 4):
                x_ = -70 + k * 22 + 6 * part
                c.line(smooth([(x_, -112), (x_ + 10 * part + 6, -92), (x_ + 4 + 8 * part, -70)], False), c.lw * 0.3, hsh, 150)
        if style == 'curly':
            _curls(c, hm, det, hc, hsh, hhi)
        if style == 'kid' and det >= 1:
            for k in range(-4, 5):
                x_ = k * 21.0
                c.line(smooth([(x_ * 0.6, -118), (x_ * 0.9, -86), (x_, -52)], False), c.lw * 0.3, hsh, 150)
            for s_ in (-1, 1):
                xl_, xr_ = hm.extent(float(hm.W(20.0)) + grow * 0.6)
                xe = xr_ if s_ > 0 else xl_
                c.line(smooth([(xe - s_ * 6, -10), (xe - s_ * 4, 40), (xe - s_ * 8, 104)], False), c.lw * 0.3, hsh, 150)
    c.line(hair, c.lw)
    if style == 'kid' and hm.map1(0, -60)[2] > 0.0:              # a yellow star hair clip on her left
        cx_, cy_, cv_ = hm.map1(46, -58, 16)
        if cv_ > 0.05:
            st_ = []
            for k in range(10):
                a_ = -PI / 2 + k * PI / 5; rr = 13 if k % 2 == 0 else 6
                st_.append((cx_ + math.cos(a_) * rr * hm.sx(46, -58, 16), cy_ + math.sin(a_) * rr))
            star = poly(st_)
            c.fill(star, '#f0c843'); c.line(star, c.lw * 0.55)
            if det >= 1: c.fill(oval(cx_ - 2, cy_ - 3, 2.4), '#fff4c4')
    if style == 'bun':
        pass


def _bumpy(hm, grow, n, amp, ytop, ybot, spiky=False, seed=0):
    ys = np.linspace(ytop, ybot, 30)
    ws = hm.W(np.clip(ys, -119.9, 119.9)) + grow
    ws = np.where(ys < -119, grow * 0.6 + 40, ws)
    xl, xr = hm.extent(ws)
    m = len(ys)
    ring = [(float(xr[i]), float(ys[i])) for i in range(m)] + [(float(xl[i]), float(ys[i])) for i in range(m - 1, -1, -1)]
    cx_ = float(np.mean([p[0] for p in ring])); cy_ = -20.0
    pts = []
    for i, (x, y) in enumerate(ring):
        ang = math.atan2(y - cy_, x - cx_)
        if spiky:
            bump = amp * (0.5 + 0.5 * math.sin(ang * n + seed * 1.7)) ** 3 * (1 if y < -30 else 0.3)
        else:
            bump = amp * abs(math.sin(ang * n)) ** 0.8
        d = math.hypot(x - cx_, y - cy_) + 1e-6
        pts.append((x + (x - cx_) / d * bump, y + (y - cy_) / d * bump))
    return smooth(pts, True, 0.9)


def _cloud(hm, grow, n, amp):
    """Curly hair cloud: an ellipse over the skull with round bumps, following the head's turn."""
    xl, xr = hm.extent(float(hm.W(-20.0)) + grow)
    cx, rx = (xl + xr) / 2, (xr - xl) / 2
    cy, ry = -22.0, 104.0 + grow * 0.75
    angs = np.linspace(math.radians(158), math.radians(382), 64)
    pts = []
    for a in angs:
        k = 1.0 + amp / rx * abs(math.sin(n * a)) ** 0.7
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    pts += [(cx + rx * 0.92, 70.0), (cx - rx * 0.92, 70.0)]
    return smooth(pts, True, 0.9)


def _curls(c, hm, det, hc, hsh, hhi):
    xl, xr = hm.extent(float(hm.W(-20.0)) + 18.0)
    cx, rx = (xl + xr) / 2, (xr - xl) / 2
    dark, light = skia.Path(), skia.Path()
    for k in range(34 if det >= 2 else 16):
        a = math.radians(165 + 210 * hash01(k, 41))
        rr = 0.35 + 0.62 * hash01(k, 43) ** 0.6
        x, y = cx + math.cos(a) * rx * rr, -22 + math.sin(a) * 118 * rr
        rad = 7 + 7 * hash01(k, 47)
        st = 360 * hash01(k, 49)
        dark.addArc(skia.Rect.MakeLTRB(x - rad, y - rad, x + rad, y + rad), st, 230)
        if det >= 2: light.addArc(skia.Rect.MakeLTRB(x - rad * 0.55 - 2, y - rad * 0.55 - 3, x + rad * 0.55 - 2, y + rad * 0.55 - 3), 200, 80)
    c.line(dark, c.lw * 0.42, hsh, 170)
    if det >= 2: c.line(light, c.lw * 0.32, hhi, 170)


def _cap(c, hm, sp, P, det, cl, t):
    """Police peaked cap: band, flared crown, badge, gold cord and a glossy black visor that shadows the eyes."""
    navy, navy_sh = cl['cap'], cl['cap_sh']
    grow = 7.0
    (l0, r0), (l1, r1) = [hm.extent(float(hm.W(y)) + grow, 0.95, 1.1) for y in (-100.0, -72.0)]
    band = smooth([(l0, -100), (r0, -100), (r1, -70), (l1, -70)], True, 0.25)
    wc = 120.0
    cl_, cr_ = hm.extent(wc, 1.0, 1.12)
    sh_c = (cl_ + cr_) / 2; half_c = (cr_ - cl_) / 2
    lift = 12.0 * hm.spi
    crown = smooth([(l0 + 2, -96), (cl_, -128 - lift * 0.3), (sh_c - half_c * 0.72, -141 - lift), (sh_c, -145 - lift),
                    (sh_c + half_c * 0.72, -141 - lift), (cr_, -128 - lift * 0.3), (r0 - 2, -96)], True, 0.7)
    # visor (behind band when facing away)
    phis = np.linspace(-1.15, 1.15, 13)
    vy0 = -72.0
    w = float(hm.W(vy0)) + grow
    vx_in = w * np.sin(phis)
    dz_out = 30.0 * np.cos(phis) ** 1.2 + 3
    X_in, Y_in, V_in = hm.map(vx_in, np.full_like(phis, vy0), grow * np.cos(phis))
    X_out, Y_out, _ = hm.map(vx_in * 1.03, np.full_like(phis, vy0 + 4) + 15 * np.cos(phis) ** 0.7, grow + dz_out)
    vis_v = float(V_in[len(V_in) // 2])
    visor = _pts_path(np.concatenate([X_in, X_out[::-1]]), np.concatenate([Y_in, Y_out[::-1]]), True, 0.7)
    # visor shadow over the face
    if vis_v > -0.2:
        sy_ = float(np.max(Y_out)) - 2
        c.grad(inter(hm.silhouette(), rect(-140, sy_ - 30, 280, 100)), 0, sy_ - 4, 0, sy_ + 34 + 30 * max(0.0, P.h_nod),
               [(0, '#0b0d14', 170), (1, '#0b0d14', 0)])
    if vis_v <= 0:
        c.shape(visor, cl['visor'])
    c.fill(crown, navy)
    with c.clip(crown):
        c.grad(crown, 0, -146, 0, -96, [(0, mix(navy, '#ffffff', 0.12), 255), (0.6, navy, 255), (1, navy_sh, 255)])
        c.fill(_crescent(crown, -30, 0), navy_sh, 150)
    c.line(crown, c.lw)
    c.fill(band, cl['visor'] if det < 1 else '#11141c')
    with c.clip(band):
        if det >= 1:
            c.line(_multi([poly([(k * 16, -100), (k * 16 + 6, -70)], False) for k in range(-8, 9)]), c.lw * 0.25, '#2a2f3d', 140)
    c.line(band, c.lw)
    # gold chin cord on the band front
    if vis_v > 0.0:
        Xc, Yc, Vc = hm.map(np.linspace(-0.85, 0.85, 9) * w * 0.9, np.full(9, -80.0), grow + 1)
        c.line(_pts_path(Xc, Yc, False), c.lw * 1.25, cl['gold_sh'])
        c.line(_pts_path(Xc, Yc - 1, False), c.lw * 0.6, cl['gold'])
        for s in (0, -1):
            c.fill(oval(Xc[s], Yc[s], 5.5), cl['gold']); c.line(oval(Xc[s], Yc[s], 5.5), c.lw * 0.5)
    # cap badge
    bx, by, bv = hm.map1(0, -114, 14)
    if bv > 0.1:
        fs = hm.sx(0, -114, 14)
        cb = c.sub(bx, by, 0, fs, 1.0)
        shield = smooth([(0, -20), (13, -14), (16, 2), (8, 15), (0, 21), (-8, 15), (-16, 2), (-13, -14)], True, 0.6)
        cb.fill(shield, cl['gold'])
        cb.radial(shield, -4, -6, 22, [(0, cl['gold_hi'], 255), (0.5, cl['gold'], 255), (1, cl['gold_sh'], 255)])
        cb.line(shield, c.lw * 0.7)
        if det >= 1:
            cb.fill(oval(0, 0, 6.5), '#26386e'); cb.line(oval(0, 0, 6.5), c.lw * 0.35)
            cb.fill(oval(-1.5, -1.5, 2), cl['gold_hi'])
    if vis_v > 0:
        c.fill(visor, cl['visor'])
        with c.clip(visor):
            hx = float(X_out[len(X_out) // 2])
            c.radial(None, hx - 30, float(Y_in.mean()) + 6, 70, [(0, '#5b6378', 200), (0.5, '#2a2f3d', 90), (1, '#0a0c11', 0)], sy=0.25, clip=False)
            if det >= 1:
                c.line(_pts_path(X_in * 0.98 + X_out * 0.02, Y_in + 3, False), c.lw * 0.5, '#4a5163', 200)
        c.line(visor, c.lw)


def _glasses(c, hm, sp, P, det, eyes, t):
    fr = '#3a2f2c'
    pts_c = []
    for side, info in eyes.items():
        ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']
        X, Y, V = hm.map1(ex0, ey0 + 2, 18.0)
        if V < 0.05: continue
        fs = hm.sx(ex0, ey0, 18.0)
        rx, ry = 31 * fs, 25
        lens = rrect(X - rx, Y - ry, rx * 2, ry * 2, 14)
        c.fill(lens, '#d9e6f2', 38)
        g = 0.5 + 0.5 * math.sin(t * 0.7 + side) if P.glint <= 0 else P.glint
        with c.clip(lens):
            c.fill(poly([(X - rx * 0.6 + 40 * g - 20, Y - ry), (X - rx * 0.2 + 40 * g - 20, Y - ry), (X - rx * 0.9 + 40 * g - 20, Y + ry),
                         (X - rx * 1.3 + 40 * g - 20, Y + ry)]), '#ffffff', 70)
        c.line(lens, c.lw * 0.75, fr)
        pts_c.append((side, X, Y, rx))
    if len(pts_c) == 2:
        (s0, x0, y0, r0), (s1, x1, y1, r1) = sorted(pts_c, key=lambda p: p[1])
        c.line(smooth([(x0 + r0, y0 - 6), ((x0 + x1) / 2, y0 - 12), (x1 - r1, y1 - 6)], False), c.lw * 0.7, fr)
    for side, X, Y, rx in pts_c:
        ear_x, ear_y, ev = hm.map1(side * float(hm.W(0)), -2, -6)
        if ev > -0.6 and abs(ear_x - X) > rx:
            c.line(poly([(X + (rx if ear_x > X else -rx), Y - 8), (ear_x, ear_y - 4)], False), c.lw * 0.6, fr)


def _pearls(c, cx, cy, w, n, det, colr):
    for k in range(n):
        u = k / (n - 1) - 0.5
        x = cx + u * w; y = cy + 30 * (1 - (2 * u) ** 2) - 30
        c.fill(oval(x, y, 7), colr); c.line(oval(x, y, 7), c.lw * 0.35, '#8c8478')
        if det >= 1: c.fill(oval(x - 2, y - 2, 2.2), '#ffffff', 220)


def _kid_hang(hm, grow, y_bot):
    """Straight hair hanging beside the face / behind the jaw down to y_bot (head units): a slab between the head's
    extents at cheek height, slightly flared, with a rounded, uneven hem."""
    w0 = float(hm.W(10.0)) + grow
    xl, xr = hm.extent(w0)
    xl2, xr2 = hm.extent(w0 + 8.0)
    pts = [(xl, -30.0), (xr, -30.0), (xr2 + 2, y_bot - 14), (xr2 - 6, y_bot), ((xl2 + xr2) * 0.5 + 10, y_bot + 3),
           ((xl2 + xr2) * 0.5 - 12, y_bot - 1), (xl2 + 6, y_bot + 2), (xl2 - 2, y_bot - 12)]
    return smooth(pts, True, 0.6)


def _kid_hair_back(c, hm, sp, P, det, t):
    """Back mass of Lily's bob (behind the face and neck, over the shoulders), drawn before the skull."""
    hc = sp['hair_c']; hsh = mix(hc, '#000000', 0.42)
    sw = 4.0 * P.sec_x
    back = union(hm.silhouette(grow=13.0, y_top=-126, y_bot=30), _kid_hang(hm, 15.0, 118.0 + 4.0 * abs(P.sec_x)))
    if sw: back = moved_path(back, sw * 0.5, 0)
    c.fill(back, hsh)
    if det >= 1:
        c.radial(back, 0, 40, 150, [(0, '#000000', 0), (0.7, '#000000', 40), (1, '#000000', 110)], sy=1.2)
    c.line(back, c.lw)


def _moustache(c, hm, sp, P, det):
    """Dad's moustache: a full, soft brush above the upper lip that rides up with a smile."""
    my = sp['mouth_y'] - 6.0 * clamp(P.smile, 0, 1) - 4.0 * clamp(P.grin)
    w = sp['mouth_w'] + 14.0 + 8.0 * clamp(P.smile, 0, 1)
    pts = [(-w, my + 2), (-w * 0.78, my - 11), (-w * 0.4, my - 18), (0, my - 15), (w * 0.4, my - 18), (w * 0.78, my - 11), (w, my + 2),
           (w * 0.62, my - 4), (w * 0.3, my - 7), (0, my - 5), (-w * 0.3, my - 7), (-w * 0.62, my - 4)]
    X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 12.0)
    if V.mean() < 0.1: return
    m = _pts_path(X, Y, True, 0.75)
    col_ = sp['moustache']
    c.fill(m, col_)
    if det >= 1:
        hs = []
        for k in range(-5, 6):
            x0 = k * w * 0.17
            a, b, _ = hm.map1(x0, my - 13 + abs(k) * 1.2, 12.0)
            a2, b2, _ = hm.map1(x0 * 1.12, my - 4 + abs(k) * 0.6, 12.0)
            hs.append(poly([(a, b), (a2, b2)], False))
        c.line(_multi(hs), c.lw * 0.3, mix(col_, '#000000', 0.45), 170)
    c.line(m, c.lw * 0.6)


def _band_path(X0, Y0, X1, Y1):
    """Union of the quads between two point rows (consistently wound, nonzero fill), so a strip that folds over itself
    when seen edge-on (a cap brim in profile) still fills."""
    p = skia.Path()
    for i in range(len(X0) - 1):
        q = [(X0[i], Y0[i]), (X0[i + 1], Y0[i + 1]), (X1[i + 1], Y1[i + 1]), (X1[i], Y1[i])]
        a = sum(q[k][0] * q[(k + 1) % 4][1] - q[(k + 1) % 4][0] * q[k][1] for k in range(4))
        if abs(a) < 1e-3: continue
        if a < 0: q = q[::-1]
        p.addPoly([skia.Point(float(x), float(y)) for x, y in q], True)
    p.setFillType(skia.PathFillType.kWinding)
    return skia.Op(p, skia.Path(), skia.PathOp.kUnion_PathOp) or p


def _cap_courier(c, hm, sp, P, det, cl, t, light=None):
    """Nightline courier cap: a soft brown six-panel crown hugging the skull, a crescent-moon logo on the front panel and
    a long curved bill that throws the eyes into shadow (their whites and any eyeshine read out of the dark)."""
    brown, brown_sh = cl['cap'], cl['cap_sh']
    grow = 6.0
    def yf(ph):
        a = np.abs(ph)
        return np.interp(a, [0, 0.8, 1.4, 2.2, PI], [-63.0, -61.0, -52.0, -44.0, -42.0])
    X, Y = hm.arc(yf, 40)
    if len(X) < 3: return
    region = poly([(float(X[0]) - 300, -420.0)] + [(float(x), float(y)) for x, y in zip(X, Y)] + [(float(X[-1]) + 300, -420.0)], True)
    dome = inter(hm.silhouette(grow=grow, y_top=-132, y_bot=-20), region)
    # bill geometry (in front of the forehead)
    phis = np.linspace(-1.2, 1.2, 15)
    vy0 = -62.0
    w = float(hm.W(vy0)) + grow
    vx_in = w * np.sin(phis)
    dz_out = 58.0 * np.cos(phis) ** 1.2 + 3
    X_in, Y_in, V_in = hm.map(vx_in, np.full_like(phis, vy0), grow * np.cos(phis))
    X_out, Y_out, _ = hm.map(vx_in * 1.14, np.full_like(phis, vy0 + 4) + 27 * np.cos(phis) ** 0.9, grow + dz_out)
    vis_v = float(V_in[len(V_in) // 2])
    bill = _pts_path(np.concatenate([X_in, X_out[::-1]]), np.concatenate([Y_in, Y_out[::-1]]), True, 0.7)
    if abs(hm.st) > 0.25: bill = _band_path(X_in, Y_in, X_out, Y_out)
    bk = (light or {}).get('brim', 1.0) * (1.0 - 0.45 * clamp(P.approach))
    if vis_v > -0.2 and bk > 0.01:                                # deep shadow of the bill over the eyes (light['brim'])
        sy_ = float(np.max(Y_out)) - 2
        fxs = np.linspace(-1.0, 1.0, 11)                          # only on the face front (not the temples / ears)
        fy0, fy1 = -66.0, sy_ + 70.0
        fw0, fw1 = float(hm.W(fy0)) * 0.98, float(hm.W(min(fy1, 110.0))) * 0.98
        TX, TY, TV = hm.map(fxs * fw0, np.full(11, fy0), 2.0)
        BX, BY, BV = hm.map(fxs[::-1] * fw1, np.full(11, fy1), 2.0)
        face = _pts_path(np.concatenate([TX, BX]), np.concatenate([TY, BY]), True, 0.6)
        c.grad(inter(inter(hm.silhouette(), face), rect(-140, sy_ - 40, 280, 130)), 0, sy_ - 6, 0, sy_ + 58 + 30 * max(0.0, P.h_nod),
               [(0, '#080605', min(255, 215 * bk)), (0.45, '#080605', min(255, 140 * bk)), (1, '#080605', 0)])
    if abs(hm.st) > 0.25 and abs(hm.ct) < 0.97:                   # turned: the brim's thickness / top surface as a lit band
        k_ = clamp((abs(hm.st) - 0.25) / 0.5)
        top_ = union(_band_path(X_in, Y_in - 9 * k_, X_out, Y_out - 7 * k_), _band_path(X_out, Y_out - 7 * k_, X_out, Y_out))
        top_ = union(top_, _band_path(X_in, Y_in - 9 * k_, X_in, Y_in))
        if vis_v <= 0: top_ = minus(top_, hm.silhouette(grow=grow))
        c.fill(top_, mix(cl['bill'], '#ffffff', 0.12)); c.line(top_, c.lw * 0.8)
    if vis_v <= 0:
        bb_ = minus(bill, hm.silhouette(grow=grow))
        c.fill(bb_, cl['bill']); c.line(bb_, c.lw)
    c.radial(dome, -30 + hm.st * 30, -128, 150, [(0, mix(brown, '#ffffff', 0.18), 255), (0.5, brown, 255), (1, brown_sh, 255)], sy=0.8)
    if det >= 1:
        c.texture(dome, 'fabric', 0.1, 0.5)
        seams = []
        for ph in (-1.05, -0.35, 0.35, 1.05):
            ys = np.linspace(-128.0, float(yf(np.array([ph]))[0]) - 2, 6)
            ws_ = hm.W(np.clip(ys, -119.9, 119.9)) + grow
            px_ = ws_ * math.sin(ph); pz_ = np.where(math.cos(ph) > 0, hm.DF, hm.DB) * ws_ * math.cos(ph)
            y1 = hm.J(ys) * hm.cp + pz_ * hm.spi
            z1 = pz_ * hm.cp - ys * hm.spi
            Xs = px_ * hm.ct + z1 * hm.st
            vis = (-math.sin(ph) * hm.st + math.cos(ph) * hm.ct)
            if vis > 0.05: seams.append(_pts_path(Xs, y1, False))
        if seams: c.line(_multi(seams), c.lw * 0.35, brown_sh, 200)
        bx_, by_, bv_ = hm.map1(0, -128, grow)
        if bv_ > -0.3: c.shape(oval(bx_, by_ + 2, 7, 5), brown, c.lw * 0.4)
    # sweatband edge
    c.line(_pts_path(X, Y, False), c.lw * 0.5, brown_sh, 220)
    c.line(dome, c.lw)
    # logo on the front panel: crescent moon in a ring
    lx, ly, lv = hm.map1(0, -92, grow + 2)
    if lv > 0.15:
        fs = hm.sx(0, -92, grow + 2)
        lc = c.sub(lx, ly, 0, fs, 1.0)
        lc.fill(oval(0, 0, 15), cl['patch']); lc.line(oval(0, 0, 15), c.lw * 0.6, cl['patch_rim'])
        moon = minus(oval(-1, 0, 9), oval(4, -3, 8))
        lc.fill(moon, cl['moon'])
        if det >= 1: lc.fill(oval(6, 5, 1.6), cl['moon'])
    if vis_v > 0:
        c.fill(bill, '#24180f')                                   # the underside, in its own shadow
        with c.clip(bill):
            hx = float(X_out[len(X_out) // 2])
            c.grad(bill, 0, float(Y_in.mean()), 0, float(Y_out.max()), [(0, '#140d08', 255), (0.6, '#33241a', 255), (1, '#5a4130', 255)])
            if det >= 1:
                for f in (0.35, 0.62):                            # stitch rows on the brim
                    c.line(_pts_path(X_in * (1 - f) + X_out * f, Y_in * (1 - f) + Y_out * f, False), c.lw * 0.3, '#4a3424', 170)
        # the lit front rim of the brim
        c.line(_pts_path(X_out, Y_out, False), c.lw * 1.6, cl['bill'])
        c.line(_pts_path(X_out, Y_out - 1.5, False), c.lw * 0.5, mix(cl['bill'], '#ffffff', 0.25), 200)
        c.line(bill, c.lw)


def draw_head_local(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    """Head in head units (crown -120 .. chin +120) on Ctx c (origin at the head centre). yaw/pitch in radians."""
    sp = sp or CAST[who]
    if sp.get('dummy'): return _winks_head(c, who, P, yaw, pitch, det, t, light, sp)
    hm = HeadMap(sp, yaw, pitch, jaw=26.0 * clamp(P.m_open) + 5.0 * clamp(P.grin), cheek=clamp(P.grin + 0.4 * max(P.smile, 0.0)))
    skin, sh, dp = _skin_cols(sp, P, light)
    sil_full = hm.silhouette()
    cut = _nape_cut(hm, sp)
    sil = minus(sil_full, cut) if cut is not None else sil_full
    face_v = hm.map1(0, 0)[2]
    cl = sp['cloth']
    # behind-head things
    if sp['hair'] == 'bun':
        bx, by, bv = hm.map1(0, -40, -150)
        if bv < 0.2 or abs(hm.st) > 0.2:
            bun = oval(bx, by - 18, 34, 30)
            c.shape(bun, sp['hair_c'])
            if det >= 1: c.line(smooth([(bx - 20, by - 26), (bx, by - 36), (bx + 22, by - 22)], False), c.lw * 0.4, mix(sp['hair_c'], '#000000', 0.4))
    if sp['hair'] == 'kid':
        _kid_hair_back(c, hm, sp, P, det, t)
    if sp['hair'] == 'lowbun': _lowbun(c, hm, sp, det, True)
    for side in (-1, 1):
        if -side * hm.st < 0.25 and sp['hair'] not in _EARLESS: _ear(c, hm, sp, side, skin, sh, det)
    # skull
    c.fill(sil, skin)
    # skin shading: every layer is drawn on a path inside the silhouette (no clip masks: they are slow at 2560)
    lx = -0.35 * 100 * ((light or {}).get('side', 1))
    c.radial(sil, lx * 0.5 + hm.st * 20, -30, 150, [(0, skin, 0), (0.62, skin, 0), (0.9, sh, 70), (1.0, sh, 135)], sy=1.15)
    ls = (light or {}).get('side', 1)
    c.fill(_crescent(sil, -ls * 30, 6), sh, 42)
    if cut is not None:                                     # seen from behind: the cheek edge past the ear sits in shadow
        c.fill(sil, sh, 110 * clamp((-hm.ct - 0.2) / 0.4))
    if det >= 2: c.texture(inter(sil, rect(-130, -78 if sp['hat'] else -125, 260, 260)), 'skin', 0.06, 0.32)
    if face_v > -0.3:
        for side in (-1, 1):
            bx_, by_, bv_ = hm.map1(side * 56, sp['eye_y'] + 36, 2)
            if bv_ > 0.1: c.glow(bx_, by_, 24 * hm.sx(side * 56, sp['eye_y'] + 36), 13, sp['blush'], 90 + 80 * P.blush)
    if sp.get('gaunt') and face_v > -0.3:                      # delivery driver: hollow cheeks under high cheekbones
        g_ = sp['gaunt']
        for side in (-1, 1):
            hx_, hy_, hv_ = hm.map1(side * 66, 58, 2)
            if hv_ > 0.05:
                c.glow(hx_ + side * 4, hy_, 20 * hm.sx(side * 66, 58), 30, sh, 120 * g_)
                bx_, by_, _ = hm.map1(side * 60, 22, 2)
                c.glow(bx_, by_, 22 * hm.sx(side * 60, 22), 8, mix(skin, '#ffffff', 0.3), 60 * g_)
    _stubble(c, hm, sp, det, sil)
    c.radial(inter(sil, rect(-150, 70, 300, 120)), hm.st * 30, 128, 90, [(0, dp, 90), (0.5, dp, 45), (1, dp, 0)], sy=22 / 90.0)
    if light and light.get('under'):                         # screen / tablet glow from below (uplight)
        ua = light.get('under_a', 120)
        c.grad(sil, 0, -125, 0, 40, [(0, '#07080d', 0.55 * ua), (1, '#07080d', 0)])
        c.radial(sil, hm.st * 20, 150, 210, [(0, light['under'], ua), (0.55, light['under'], 0.45 * ua), (1, light['under'], 0)], sy=0.8)
    if light and light.get('rim'):
        rs = light.get('side', 1)
        c.fill(_crescent(sil, -rs * 7, 3), light['rim'], light.get('rim_a', 70))
    eyes = {}
    if face_v > -0.35:
        with (c.clip(hm.silhouette(grow=1.5)) if abs(hm.st) > 0.22 or abs(P.h_nod) > 0.3 else _noop()):
            _wrinkles(c, hm, sp, P, det, sh)
            _mouth(c, hm, sp, P, det, t, skin, sh)
            if sp['scar']: _scar(c, hm, sp, sp['scar'], det)
            for side in (-1, 1):
                eyes[side] = _eye(c, hm, sp, P, side, det, t, skin, sh)
            if sp['hair'] not in ('messy', 'shaggy'):
                for side in (-1, 1):
                    _brow(c, hm, sp, P, side, eyes.get(side))
            if sp.get('spots') and det >= 1:              # Grandpa: liver spots on the temples
                for (x_, y_, r_) in ((-70, -44, 4.5), (72, -30, 3.5), (-60, 20, 3.0)):
                    X_, Y_, V_ = hm.map1(x_, y_, 1.0)
                    if V_ > 0.1: c.fill(oval(X_, Y_, r_ * hm.sx(x_, y_), r_ * 0.8), '#9c7258', 110)
            _tears(c, hm, sp, P, t, det, eyes)
            _sweat(c, hm, sp, P, t, det)
    c.line(sil, c.lw)
    if face_v > -0.35:
        _nose(c, hm, sp, P, det, skin, sh)
        if sp.get('moustache'): _moustache(c, hm, sp, P, det)
    if sp['hair']:
        if sp['hat'] != 'cap' or True:
            _hair_region(c, hm, sp, P, det, sil_full, t)
        if sp['hair'] == 'lowbun': _lowbun(c, hm, sp, det, False)
        if sp['hair'] in ('messy', 'shaggy') and face_v > -0.35:   # v2.1: brows over the fringe so fear/scream angles read
            for side in (-1, 1):
                _brow(c, hm, sp, P, side, eyes.get(side))
    for side in (-1, 1):
        if -side * hm.st >= 0.25 and sp['hair'] not in _EARLESS: _ear(c, hm, sp, side, skin, sh, det)
    if sp.get('glasses') and face_v > -0.2 and getattr(P, 'specs', 1.0) > 0.5:
        _glasses(c, hm, sp, P, det, eyes, t)
    if sp['hat'] == 'cap':
        _cap(c, hm, sp, P, det, cl, t)
    elif sp['hat'] == 'courier':
        _cap_courier(c, hm, sp, P, det, cl, t, light)
    shine = clamp(getattr(P, 'eyeshine', 0.0))
    if shine > 0.01:                     # eyeshine sits over the brim shadow and blooms past the lids
        for side, info in eyes.items():
            if info is None or len(info) < 7 or info[6] < 0.2: continue
            X_, Y_, r_, fs_, px_, py_, op_ = info
            sr = lerp(r_ * 0.4 * sp['pupil'] * P.pupil, r_ * 0.66, ease_out_cubic(shine))
            c.glow(px_, py_, r_ * 2.9 * fs_, r_ * 2.6, '#e6fff4', 150 * shine)
            c.radial(oval(px_, py_, sr * fs_, sr), px_, py_, sr, [(0, '#ffffff', 255), (0.55, '#f4fffb', 255), (0.85, '#c6f2e4', 240),
                                                                   (1, '#86d6c0', 220)], sy=1.0, a=shine)
            c.glow(px_, py_, r_ * 1.15 * fs_, r_ * 1.05, '#ffffff', 210 * shine)
    return hm



# ====================================================================================================== body rig
def _ik(S, H, L1, L2, pole):
    """Two-bone IK in 3D. S shoulder/hip, H target (np arrays). Returns elbow/knee and the reachable end point."""
    d = H - S; dist = float(np.linalg.norm(d)) + 1e-9
    u = d / dist
    reach = L1 + L2 - 0.5
    if dist > reach: dist = reach; H = S + u * dist
    dist = max(dist, abs(L1 - L2) + 1.0)
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(L1 * L1 - a * a, 0.0))
    pp = pole - u * float(np.dot(pole, u)); n = float(np.linalg.norm(pp))
    pp = pp / n if n > 1e-6 else np.array([1.0, 0.0, 0.0])
    return S + u * a + pp * h, H


def _tube(pts, widths, k=0.9):
    """Tapered limb outline through 2D points with per-point widths (full width)."""
    pts = np.asarray(pts, float); n = len(pts)
    left, right = [], []
    for i in range(n):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, n - 1)]
        dx, dy = b - a; L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = widths[i] / 2
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w)); right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    # round caps
    def cap(p, q, w, sgn):
        dx, dy = p[0] - q[0], p[1] - q[1]; L = math.hypot(dx, dy) or 1.0
        return (p[0] + dx / L * w * 0.42 * sgn, p[1] + dy / L * w * 0.42 * sgn)
    end = cap(pts[-1], pts[-2], widths[-1], 1); start = cap(pts[0], pts[1], widths[0], 1)
    return smooth(left + [end] + right[::-1] + [start], True, k)


class Body:
    """Projects body-frame points (x right, y down, feet y=0, crown y=-1000, z toward the camera) through lean (about the
    hips), yaw, a mild perspective and the 2D tilt/sway/bob of the upper body."""
    D = 1400.0

    def __init__(self, sp, P):
        self.sp, self.P = sp, P
        b = sp['body']; hh = sp['hh']
        self.b = b
        self.yc = -1000.0 + hh                         # chin
        self.y_sh = self.yc + 44 - 3.0 * (P.breath - 0.5) * sp['breath'] - 26 * P.shrug
        self.y_ch = self.y_sh + 78
        self.y_wa = -540.0; self.y_belt = -478.0; self.y_hip = -422.0; self.y_cr = -392.0
        self.th = P.turn * PI / 2; self.ct, self.st = math.cos(self.th), math.sin(self.th)
        self.L = P.lean * 0.62 + P.hunch * 0.22
        self.cL, self.sL = math.cos(self.L), math.sin(self.L)
        self.sit = clamp(P.sit)
        self.floor = clamp(getattr(P, 'floor', 0.0))
        self.tip = clamp(getattr(P, 'tiptoe', 0.0))
        self.kneel = clamp(getattr(P, 'kneel', 0.0))
        self.hip_drop = 170.0 * self.sit * (1.0 - self.floor) + P.crouch * 120 + 330.0 * self.floor - 34.0 * self.tip + 40.0 * self.kneel
        self.y0c = -620.0
        self.tilt = math.radians(P.tilt)
        self.ctl, self.stl = math.cos(self.tilt), math.sin(self.tilt)
        bk = 1.0 + 0.014 * (P.breath - 0.5) * sp['breath']
        self.chest_k = bk
        # walk: phases and the hip drop that keeps the stance foot on the ground
        self.walk = clamp(P.walk_amt)
        self.ph = P.walk_ph * 2 * PI
        self.stride = 230.0 * self.walk
        drop = 0.0
        for sd in (-1, 1):
            f = self.foot_fwd(sd)
            if self.foot_lift(sd) < 1: drop = max(drop, math.sqrt(384.0 ** 2 + f * f) - 384.0)
        self.bob = P.bob + drop + 5.0 * self.walk * math.cos(2 * self.ph) + self.hip_drop

    # ---- walk helpers (side: -1 = character's right leg, +1 = left)
    def leg_phase(self, side):
        return self.ph + (0.0 if side > 0 else PI)

    def foot_fwd(self, side):
        return self.stride / 2 * math.cos(self.leg_phase(side))

    def foot_lift(self, side):
        return max(0.0, -math.sin(self.leg_phase(side))) * 62.0 * self.walk

    # ---- projection
    def p3(self, x, y, z=0.0, upper=True):
        y = y + self.bob
        if upper:
            yp = self.y_hip + self.bob
            dy = y - yp
            z1 = z * self.cL - dy * self.sL
            y1 = yp + dy * self.cL + z * self.sL
        else:
            z1, y1 = z, y
        X = x * self.ct + z1 * self.st
        Z = -x * self.st + z1 * self.ct
        s = self.D / (self.D - Z)
        Xs = X * s; Ys = self.y0c + (y1 - self.y0c) * s
        if upper and (self.tilt or self.P.sway):
            hx, hy = 0.0, self.y_hip + self.bob
            dx, dy = Xs - hx, Ys - hy
            Xs = hx + dx * self.ctl - dy * self.stl + self.P.sway
            Ys = hy + dx * self.stl + dy * self.ctl
        return Xs, Ys, s, Z

    def rows(self, ys, ws, ds):
        """Torso rows -> (left pts, right pts) projected."""
        L, R = [], []
        for y, w, d in zip(ys, ws, ds):
            hw = math.sqrt((w * self.ct) ** 2 + (d * self.st) ** 2)
            up = y <= self.y_hip + 1
            X, Y, s, _ = self.p3(0.0, y, 0.0, up)
            # lean pushes rows toward the camera: half width grows with perspective; tilt rotates the row
            dxr, dyr = hw * s * self.ctl, hw * s * self.stl if up else 0.0
            if not up: dxr = hw * s
            L.append((X - dxr, Y - dyr)); R.append((X + dxr, Y + dyr))
        return L, R

    def surf(self, x0, y0, dz=0.0, back=False, rows=None):
        """Point on the torso surface given front-view coords (x0, y0). Returns X, Y, vis, scale."""
        ys, ws, ds = rows
        w = max(float(np.interp(y0, ys, ws)), 1.0); d = float(np.interp(y0, ys, ds))
        s_ = clamp(x0 / w, -1, 1); c_ = math.sqrt(1 - s_ * s_)
        z = (d * c_ + dz) * (-1 if back else 1)
        X, Y, s, _ = self.p3(x0, y0, z, y0 <= self.y_hip + 1)
        nx, nz = s_ * d, c_ * w * (-1 if back else 1)
        nn = math.hypot(nx, nz) + 1e-9
        vis = (-nx * self.st + nz * self.cL * self.ct) / nn
        fs = max(0.06, abs(self.ct * c_ * w * 1.0 - (d * s_) * self.st * (-1 if back else 1)) / (w * c_ + 1e-6) * c_ if c_ > 0.05 else 0.06)
        return X, Y, vis, s * fs


def _hull(pts):
    import cv2
    a = np.asarray(pts, np.float32).reshape(-1, 1, 2)
    h = cv2.convexHull(a).reshape(-1, 2)
    return [(float(x), float(y)) for x, y in h]


# ---------------------------------------------------------------------------------------------- hands & props
# v2.1 hands: real fingers (3 phalanges, knuckle creases, nails, one shade step). Hand coords: wrist at (0, 0), fingers
# toward +y, thumb toward -side * x; about 66 units wrist to fingertip. The finger order runs from the thumb side:
# index, middle, ring, little.
_FING = (  # (base offset along the knuckle line from the thumb side, phalanx lengths, base width, splay rad)
    (1.5, (14.0, 9.5, 8.0), 9.6, 0.20), (0.5, (15.0, 10.5, 8.5), 10.0, 0.06),
    (-0.5, (14.0, 10.0, 8.0), 9.6, -0.08), (-1.5, (11.0, 7.5, 7.0), 8.4, -0.22))


def _finger_pts(bx, by, ang, lens, curl=0.0, side_bend=0.0):
    """Centre line of a finger: base (bx, by), direction ang (rad from +y toward +x), 3 phalanges bending by curl."""
    pts = [(bx, by)]
    a = ang
    x, y = bx, by
    for i, ln in enumerate(lens):
        x += math.sin(a) * ln; y += math.cos(a) * ln
        pts.append((x, y))
        a += side_bend
    if curl:
        # curl foreshortens the outer phalanges toward the palm (seen from the back)
        k = 1.0 - 0.55 * curl
        (x0, y0) = pts[1]
        pts = pts[:2] + [(x0 + (px - x0) * k, y0 + (py - y0) * k) for px, py in pts[2:]]
    return pts


def _fattube(pts, w0, w1):
    n = len(pts)
    ws = [w0 + (w1 - w0) * (i / (n - 1)) for i in range(n)]
    return _tube(pts, ws, 0.9)


def _hand_geom(shape, side, press=0.0):
    """dict(fills=[paths], nails=[paths], creases=[paths], press=[paths], lines=[paths], ring=(x, y, ang_deg, w))."""
    th = -side
    G = dict(fills=[], nails=[], creases=[], press=[], lines=[], ring=None)
    sq = 1.0 + 0.06 * press

    def nail(pts, w, back=True):
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        ang = math.degrees(math.atan2(x2 - x1, y2 - y1))
        L_ = math.hypot(x2 - x1, y2 - y1)
        m = skia.Matrix(); m.setRotate(-ang); m.postTranslate(x2, y2)
        p = rrect(-w * 0.32, -L_ * 0.78, w * 0.64, L_ * 0.62, w * 0.3); p.transform(m)
        G['nails'].append(p)

    def crease(pts, i, w):
        (x1, y1) = pts[i]; (x0, y0) = pts[i - 1] if i > 0 else pts[i]; (x2, y2) = pts[i + 1]
        dx, dy = x2 - x0, y2 - y0; L_ = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L_, dx / L_; ux, uy = dx / L_, dy / L_
        h = w * 0.3
        G['creases'].append(smooth([(x1 + nx * h - ux * 1.2, y1 + ny * h - uy * 1.2), (x1 + ux * 1.0, y1 + uy * 1.0),
                                    (x1 - nx * h - ux * 1.2, y1 - ny * h - uy * 1.2)], False))

    if shape in ('open', 'flat', 'wave', 'relaxed', 'palm4'):
        flat = shape == 'flat'
        spread = (1.45 if flat else (0.4 if shape in ('relaxed', 'palm4') else 1.0)) * (1.0 + 0.1 * press)
        palm = smooth([(-15 * sq, 0), (15 * sq, 0), (19 * sq, 18), (19.5 * sq, 33), (12, 38), (-12, 38), (-19.5 * sq, 33), (-19 * sq, 18)], True, 0.75)
        G['fills'].append(palm)
        for k, (off, lens, w, spl) in enumerate(_FING):
            bx = th * off * 9.6 * sq
            pts = _finger_pts(bx, 31.0 - abs(off) * 2.0, th * spl * spread, lens, 0.0, -th * spl * 0.12)
            G['fills'].append(_fattube(pts, w * sq, w * 0.78 * sq))
            if flat:
                (x2, y2) = pts[-1]; (x1, y1) = pts[-2]
                G['press'].append(oval(x1 + (x2 - x1) * 0.55, y1 + (y2 - y1) * 0.55, w * 0.42 * sq, w * 0.62))
                crease(pts, 1, w); crease(pts, 2, w * 0.9)
            else:
                nail(pts, w * 0.8)
                crease(pts, 2, w * 0.85)
                if k < 4: G['creases'].append(smooth([(pts[0][0] - 3, pts[0][1] + 1), (pts[0][0], pts[0][1] - 1.5), (pts[0][0] + 3, pts[0][1] + 1)], False))
            if k == 2:
                (x0, y0), (x1, y1) = pts[0], pts[1]
                G['ring'] = (x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.45, math.degrees(math.atan2(x1 - x0, y1 - y0)), w)
        ta = th * (0.78 if flat else 0.55)
        tb = _finger_pts(th * 15.0, 10.0, ta, (15.5, 12.5), 0.0, -th * 0.18)
        if shape == 'palm4': return G
        G['fills'].append(_fattube(tb, 12.0 * sq, 9.0 * sq))
        if flat:
            (x2, y2) = tb[-1]; G['press'].append(oval(x2 - th * 1.5, y2 - 2, 4.8, 5.6))
            G['press'].append(oval(0, 20, 12.5 * sq, 9.5))
            G['lines'].append(smooth([(th * 12, 13), (th * 4, 22), (th * 2, 34)], False))           # life line
            G['lines'].append(smooth([(-th * 17, 25), (-th * 4, 27), (th * 9, 24)], False))         # heart line
        else:
            nail(tb, 9.5)
            G['creases'].append(smooth([(-9, 8), (0, 6), (9, 8)], False))                           # wrist tendon hint
        return G
    if shape in ('fist', 'point'):
        # knuckles toward the viewer: a block with 4 curled finger rolls and the thumb wrapped across
        blk = rrect(-17, -2, 34, 30, 11)
        G['fills'].append(blk)
        for k, (off, lens, w, spl) in enumerate(_FING):
            if shape == 'point' and k == 0: continue
            x = th * off * 8.4
            roll = rrect(x - w * 0.5, 17, w, 18 - abs(off) * 1.6, w * 0.46)
            G['fills'].append(roll)
            G['creases'].append(smooth([(x - w * 0.36, 25), (x, 23.6), (x + w * 0.36, 25)], False))
            if k == 2: G['ring'] = (x, 22.0, 0.0, w)
        if shape == 'point':
            pts = _finger_pts(th * 12.6, 20.0, th * 0.05, (15.0, 11.0, 9.0))
            G['fills'].append(_fattube(pts, 9.8, 8.0)); nail(pts, 7.8); crease(pts, 1, 9.0); crease(pts, 2, 8.4)
        tb = [(th * 18.0, 4.0), (th * 13.0, 15.0), (th * 2.0, 21.0)]
        G['fills'].append(_fattube(tb, 12.0, 9.5))
        nail(tb, 8.5)
        return G
    if shape == 'grip':
        # wrapped round a handle / phone seen from the front: 4 stacked finger rolls across the prop, thumb along the side
        palm = rrect(-17, -2, 34, 16, 9)
        G['fills'].append(palm)
        for k in range(4):
            y = 9.0 + k * 8.6
            ln = (34.0, 35.0, 33.0, 28.0)[k]
            x0 = th * 15.0; x1 = x0 - th * ln
            roll = _fattube([(x0, y), ((x0 + x1) / 2, y + 0.8), (x1, y)], 9.4 - 0.6 * k, 8.4 - 0.5 * k)
            G['fills'].append(roll)
            G['creases'].append(smooth([(x0 - th * ln * 0.55, y - 3.2), (x0 - th * ln * 0.58, y), (x0 - th * ln * 0.55, y + 3.2)], False))
            tip = rrect(min(x1, x1 + th * 7) - 0.5, y - 3.0, 7.0, 6.0, 3.0)
            G['nails'].append(tip)
            if k == 2: G['ring'] = (x0 - th * ln * 0.22, y, 90.0, 9.0)
        tb = [(th * 16.0, 0.0), (th * 17.5 + th * 1.5 * press, 12.0), (th * 15.5 + th * 3.0 * press, 22.0)]
        G['fills'].append(_fattube(tb, 12.0, 10.0))
        nail([tb[1], tb[2]], 9.0)
        return G
    # mitt (reference style, wide shots)
    palm = smooth([(-16, 0), (16, 0), (18, 30), (12, 52), (-10, 54), (-18, 30)], True, 0.8)
    thumb = rrect(-4.5, -2, 9, 26, 4.5)
    m = skia.Matrix(); m.setRotate(-side * 30); m.postTranslate(th * 16, 8); thumb.transform(m)
    G['fills'].append(union(palm, thumb))
    G['creases'] = [poly([(-5 + k * 9, 40), (-5 + k * 9, 52)], False) for k in range(2)]
    G['ring'] = (side * 4.0, 40.0, 0.0, 9.0)
    return G


def _hand_path(shape, L, side, press=0.0, t=0.0):
    """Legacy view of _hand_geom: [(path, kind)] with kind fill / line / detail / press."""
    G = _hand_geom(shape, side, press)
    u = G['fills'][0]
    for p in G['fills'][1:]: u = union(u, p)
    out = [(u, 'fill')]
    out += [(p, 'detail') for p in G['creases']] + [(p, 'press') for p in G['press']] + [(p, 'line') for p in G['lines']]
    return out


_HANDC = {}


def _hand_cached(shape, side, press):
    key = (shape, side, press)
    if key not in _HANDC:
        G = _hand_geom(shape, side, press)
        u = G['fills'][0]
        for p in G['fills'][1:]: u = union(u, p)
        G['union'] = u
        G['shade'] = _crescent(u, -5, -2.5)
        G['creases_p'] = _multi(G['creases']) if G['creases'] else None
        G['lines_p'] = _multi(G['lines']) if G['lines'] else None
        # finger separation lines: outline of each finger inside the union, drawn thin
        G['seps'] = _multi(G['fills'][1:]) if len(G['fills']) > 1 else None
        if len(_HANDC) > 300: _HANDC.clear()
        _HANDC[key] = G
    return _HANDC[key]


def _ring_band(hc, ring, det, t=0.0, lw=None):
    """Gold band across a finger at (x, y, ang, w): the back half darker (occluded), the front half lit, a glint."""
    x, y, ang, w = ring
    rc = hc.sub(x, y, -ang)
    hw = w * 0.53
    band = smooth([(-hw, -1.5), (0, -0.7), (hw, -1.5), (hw, 1.6), (0, 2.4), (-hw, 1.6)], True, 0.5)
    rc.fill(band, '#d8b04c')
    rc.grad(band, -hw, 0, hw, 0, [(0, '#7a5a1c', 255), (0.3, '#f2d77e', 255), (0.62, '#d8b04c', 255), (1, '#6e5018', 255)])
    rc.line(band, hc.lw * 0.3)
    if det >= 1:
        g = 0.5 + 0.5 * math.sin(t * 2.3)
        rc.fill(oval(-hw * 0.38, 0.0, 1.0 + 0.5 * g, 0.55), '#fffbe8', 190 + 60 * g)


def _draw_hand(c, sp, shape, x, y, scale, angle, side, det, skin, sh, ring=False, press=0.0, t=0.0):
    hc = c.sub(x, y, angle, scale * sp['body'].get('hand', 1.0))
    G = _hand_cached(shape, side, round(press, 1))
    u = G['union']
    hc.fill(u, skin)
    hc.fill(G['shade'], sh, 150)
    if det >= 1 and G['seps'] is not None and shape != 'mitt':
        hc.line(G['seps'], hc.lw * 0.42, LINE, 150)
    hc.line(u, hc.lw * 0.9)
    if det >= 1 and sp.get('dummy'):                         # white glove: soft creases, three stitch lines on the back
        if G['creases_p'] is not None: hc.line(G['creases_p'], hc.lw * 0.32, '#9a917e', 150)
        if shape in ('open', 'flat', 'relaxed', 'mitt', 'palm4', 'fist', 'grip', 'point'):
            hc.line(_multi([poly([(k * 6.0, 8.0), (k * 7.5, 26.0)], False) for k in (-1, 0, 1)]), hc.lw * 0.4, '#a39a86', 200)
    elif det >= 1:
        if G['creases_p'] is not None: hc.line(G['creases_p'], hc.lw * 0.32, sp['skin_dp'], 170)
        if G['lines_p'] is not None: hc.line(G['lines_p'], hc.lw * 0.35, sp['skin_dp'], 150)
        nailc = mix(skin, '#ffffff', 0.38)
        for p in G['nails']:
            hc.fill(p, nailc, 230); hc.line(p, hc.lw * 0.25, sp['skin_dp'], 200)
    if press > 0.05:
        if shape == 'flat':                                     # pressed on glass: paler skin, darker pressed rim
            hc.fill(u, '#f1e6e0', 70 * press)
            hc.line(u, hc.lw * 1.6, mix(skin, '#6b4c46', 0.55), 120 * press)
            hc.line(u, hc.lw * 0.9)
        for p in G['press']: hc.fill(p, '#f3e8e2', 200 * press)
    if ring and G['ring'] is not None:
        _ring_band(hc, G['ring'], det, t)


def moved_path(p, dx, dy):
    q = skia.Path(p); q.offset(dx, dy); return q


def _prop(c, name, det, t=0.0, P=None):
    """Props in prop coords (centred, about 60-90 units tall), facing the camera."""
    if name in ('tablet', 'tablet_back', 'stylus', 'keys_dad'):
        _prop_delivery(c, name, det, t, P); return
    if name == 'card':
        r = rrect(-46, -30, 92, 60, 6)
        c.shape(r, '#e9e6dc'); c.fill(rrect(-46, -30, 92, 14, 6), '#3f5f9c'); c.fill(rect(-46, -22, 92, 6), '#3f5f9c')
        c.shape(rect(-38, -8, 22, 28), '#b9a99c', c.lw * 0.4)
        c.fill(oval(-27, 0, 6), '#7a6a60'); c.fill(rect(-36, 8, 18, 12), '#7a6a60')
        for k in range(4): c.fill(rect(-8, -6 + k * 7, 44 - k * 6, 3), '#7b7f88', 200)
        if det >= 2: text(c.cv, '', 0, 0)
    elif name == 'pen':                       # black ballpoint, held upright: barrel, silver clip and tip
        c.shape(rrect(-6, -44, 12, 80, 5), '#17181c')
        c.fill(rrect(-4, -40, 3, 70, 1.5), '#4a4d57', 160)
        c.shape(rrect(3, -42, 4, 30, 2), '#c9ccd3', c.lw * 0.5)
        c.shape(poly([(-6, 36), (6, 36), (1.2, 50), (-1.2, 50)]), '#c9ccd3', c.lw * 0.5)
        c.fill(rrect(-6, -46, 12, 6, 3), '#2b2d33')
    elif name == 'notebook':
        r = rrect(-34, -46, 68, 92, 5)
        c.shape(r, '#1a1b1f'); c.fill(rect(18, -46, 6, 92), '#33343a'); c.line(rect(18, -46, 6, 92), c.lw * 0.4)
        c.fill(rect(-34, -40, 4, 80), '#d8d2c2')
    elif name == 'key':
        c.line(oval(0, -18, 15), c.lw * 2.6, '#ff7a12')
        c.line(oval(0, -18, 15), c.lw * 0.5)
        c.line(oval(0, -18, 15 + c.lw * 1.3), c.lw * 0.5)
        c.line(oval(0, -18, 15 - c.lw * 1.3), c.lw * 0.5)
        blade = poly([(-4, -2), (4, -2), (4, 40), (0, 46), (-4, 40)])
        head = oval(0, 0, 10)
        k_ = union(blade, head)
        c.shape(k_, '#b9bec6', c.lw * 0.6)
        for k in range(3): c.fill(rect(4, 18 + k * 7, 5, 4), '#b9bec6'); c.line(rect(4, 18 + k * 7, 5, 4), c.lw * 0.35)
        c.fill(oval(0, 0, 3.5), '#2a2a2e')
        c.shape(rrect(14, -42, 22, 28, 5), '#ff7a12', c.lw * 0.5)
    elif name == 'phone':
        r = rrect(-22, -44, 44, 88, 8)
        c.shape(r, '#121317')
        c.fill(rrect(-18, -38, 36, 74, 4), '#9fc3e8')
        c.radial(rrect(-18, -38, 36, 74, 4), -4, -10, 50, [(0, '#e6eef6', 255), (1, '#6f8fb8', 255)])
    elif name == 'phone_back':
        r = rrect(-21, -46, 42, 92, 9)
        c.shape(r, '#17181d')
        c.grad(r, -21, 0, 21, 0, [(0, '#3a3d47', 255), (0.35, '#1c1d23', 255), (1, '#0b0b0e', 255)])
        c.line(r, c.lw * 0.9)
        cam_ = rrect(-15, -40, 15, 22, 5)
        c.fill(cam_, '#0d0d10'); c.line(cam_, c.lw * 0.4, '#3d404a')
        c.fill(oval(-7.5, -34, 4), '#23252c'); c.fill(oval(-7.5, -24, 4), '#23252c')
        if det >= 1: c.fill(oval(-8.5, -35, 1.4), '#9fb0d0', 200)
    elif name == 'glasses':
        fr = '#3a2f2c'
        for sx_ in (-1, 1):
            l_ = rrect(sx_ * 26 - 22, -16, 44, 32, 12)
            c.fill(l_, '#d9e6f2', 60); c.line(l_, c.lw * 0.75, fr)
            c.fill(poly([(sx_ * 26 - 12, -16), (sx_ * 26 - 4, -16), (sx_ * 26 - 14, 16), (sx_ * 26 - 22, 16)]), '#ffffff', 60)
        c.line(smooth([(-4, -6), (0, -10), (4, -6)], False), c.lw * 0.7, fr)
        c.line(poly([(-48, -8), (-56, 18)], False), c.lw * 0.6, fr); c.line(poly([(48, -8), (56, 18)], False), c.lw * 0.6, fr)
    elif name == 'mic':
        r = rrect(-16, -26, 32, 52, 8)
        c.fill(r, '#15161a')
        c.grad(r, -16, 0, 16, 0, [(0, '#3a3d45', 255), (0.5, '#15161a', 255), (1, '#08080a', 255)])
        c.line(r, c.lw * 0.8)
        for k in range(5): c.line(poly([(-10, -18 + k * 6), (10, -18 + k * 6)], False), c.lw * 0.35, '#050506')
        c.shape(rrect(-21, -4, 7, 18, 2), '#2a2c33', c.lw * 0.4)
        c.fill(oval(9, 17, 2.6), '#3bd157' if (t % 1.0) < 0.6 else '#145a22')
        if det >= 1: c.glow(9, 17, 7, 7, '#3bd157', 90)
    elif name == 'photo':
        r = rect(-40, -32, 80, 64)
        c.shape(r, '#e8e4da', c.lw * 0.6); c.fill(rect(-33, -25, 66, 46), '#4d4a52')
        c.fill(oval(-10, -6, 9), '#b6a092'); c.fill(oval(12, -4, 8), '#b6a092'); c.fill(rect(-22, 4, 46, 17), '#2f3340')
    elif name == 'badge':
        r = rrect(-30, -42, 60, 84, 6)
        c.shape(r, '#2a1d17')
        sh_ = smooth([(0, -26), (17, -18), (20, 2), (10, 20), (0, 27), (-10, 20), (-20, 2), (-17, -18)], True, 0.6)
        c.shape(sh_, '#c9a64a', c.lw * 0.6)
        c.radial(sh_, -5, -8, 26, [(0, '#f2dc94', 255), (1, '#86682a', 255)]); c.line(sh_, c.lw * 0.6)
    elif name == 'flashlight':                # the usher's torch: chrome barrel, a wider head with the lens at the top (-y)
        on = clamp(P.torch) if P is not None else 0.0
        body = rrect(-7, -14, 14, 52, 5)
        c.shape(body, '#9aa0a8'); c.grad(body, -7, 0, 7, 0, [(0, '#e6eaf0', 255), (0.4, '#a5abb4', 255), (1, '#4c5058', 255)]); c.line(body, c.lw * 0.6)
        hd = poly([(-12, -36), (12, -36), (8, -14), (-8, -14)])
        c.shape(hd, '#b8bec6'); c.grad(hd, -12, 0, 12, 0, [(0, '#f2f4f8', 255), (0.45, '#b8bec6', 255), (1, '#5a5e66', 255)]); c.line(hd, c.lw * 0.6)
        c.shape(rrect(-3, 0, 6, 9, 2), '#8a1f2b', c.lw * 0.4)                     # the red slide switch
        lens = oval(0, -36, 12, 4)
        c.fill(lens, '#fff6d0' if on > 0.5 else '#6b7078'); c.line(lens, c.lw * 0.5)
        if on > 0.01: c.glow(0, -38, 30, 18, '#fff4cc', 200 * on)
    elif name == 'mug':                       # Grandpa's mug: cream ceramic, a brown band, coffee, steam (pose.steam)
        bd = smooth([(-24, -30), (24, -30), (22, 26), (16, 32), (-16, 32), (-22, 26)], True, 0.3)
        hdl = minus(oval(28, -2, 14, 17), oval(28, -2, 7, 10))
        c.shape(hdl, '#ece4d2', c.lw * 0.6)
        c.fill(bd, '#ece4d2'); c.grad(bd, -24, 0, 24, 0, [(0, '#fffaf0', 255), (0.5, '#ece4d2', 255), (1, '#a99e88', 255)])
        c.fill(rect(-24, -6, 48, 9), '#8a5a3a', 230)
        c.line(bd, c.lw * 0.7)
        top = oval(0, -30, 24, 6); c.fill(top, '#3a2416'); c.line(top, c.lw * 0.5)
        st_ = clamp(P.steam) if P is not None else 1.0
        if st_ > 0.01 and det >= 1:                # soft wisps that curl up and fade
            for k in range(3):
                ph = t * 1.3 + k * 2.1
                pts = [((-10 + 10 * k) + 6 * math.sin(ph + u * 3.0), -36 - 56 * u) for u in np.linspace(0, 1, 7)]
                for j in range(3):
                    seg = smooth(pts[j * 2:j * 2 + 3], False)
                    a_ = st_ * (1.0 - j / 3.0)
                    c.line(seg, c.lw * 2.6, '#ffffff', 34 * a_); c.line(seg, c.lw * 0.8, '#ffffff', 70 * a_)
    elif name == 'radio':
        r = rrect(-17, -40, 34, 80, 8)
        c.shape(r, '#17181c')
        c.fill(rrect(-11, -32, 22, 30, 4), '#2a2c32')
        for k in range(5): c.line(poly([(-8, -28 + k * 6), (8, -28 + k * 6)], False), c.lw * 0.35, '#0b0b0d')
        c.shape(rrect(-6, 6, 12, 10, 3), '#c23b3b', c.lw * 0.4)
        c.shape(rrect(-4, -54, 8, 16, 3), '#17181c', c.lw * 0.6)


def draw_prop(pen, name, x, y, size=80.0, angle=0.0, detail=2, t=0.0, pose=None):
    """A prop facing the camera, centred at (x, y); size = its height in design px (default props are ~80 units).
    Delivery props: 'tablet' (screen to the viewer; pose.tablet_screen / tablet_ink / tablet_flash drive the screen),
    'tablet_back', 'stylus', 'keys_dad' (dad's ring of keys on the bead keychain)."""
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 2.2) * 0.8).sub(x, y, angle, size / 80.0)
    _prop(c, name, detail, t, _as_pose(pose) if pose is not None else None)


# ---------------------------------------------------------------------------------------------- delivery props
# Handwriting as stroke lists in a unit box (y down). 'J' = the first letter of your name in your own cursive hand (the
# stroke stops halfway); LILY = a child's print signature 'Lily.' (wobbly, uneven baseline).
HAND_STROKES = {
    'J': [[(0.06, 0.30), (0.20, 0.12), (0.45, 0.04), (0.72, 0.06), (0.86, 0.13), (0.80, 0.20), (0.66, 0.24), (0.60, 0.40),
           (0.55, 0.62), (0.47, 0.84), (0.34, 0.97), (0.20, 0.95), (0.16, 0.84), (0.27, 0.72), (0.48, 0.62), (0.80, 0.55),
           (1.02, 0.56)]],
    'LILY': [[(0.02, 0.05), (0.04, 0.55), (0.05, 0.96), (0.38, 0.97)],
             [(0.56, 0.48), (0.57, 0.97)], [(0.565, 0.28), (0.575, 0.30)],
             [(0.80, 0.02), (0.79, 0.50), (0.81, 0.98)],
             [(1.00, 0.46), (1.08, 0.70), (1.17, 0.88)], [(1.34, 0.45), (1.22, 0.80), (1.10, 1.18), (1.02, 1.30)],
             [(1.50, 0.95), (1.515, 0.97)]],
}


def _strokes_path(strokes, x, y, sx, sy, ink=1.0, wobble=0.0, seed=0, t=0.0):
    """Path of the handwriting strokes scaled into (x, y, sx, sy), cut at `ink` (0..1 of the total length).
    Returns (path, end point or None)."""
    segs = []
    for si, st in enumerate(strokes):
        pts = []
        for k, (u, v) in enumerate(st):
            if wobble:
                u += wobble * 0.025 * noise1(k * 0.7 + si * 3.1, seed + 1)
                v += wobble * 0.035 * noise1(k * 0.9 + si * 2.3, seed + 2) + wobble * 0.04 * math.sin(si * 1.7)
            pts.append((x + u * sx, y + v * sy))
        segs.append(pts)
    lens = [sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(p_, p_[1:])) + 2.0 for p_ in segs]
    total = sum(lens) or 1.0
    left = clamp(ink) * total
    path = skia.Path(); end = None
    for pts, L in zip(segs, lens):
        if left <= 0: break
        if left >= L:
            path.addPath(smooth(pts, False, 0.7) if len(pts) > 2 else poly(pts, False)); end = pts[-1]; left -= L
            continue
        out = [pts[0]]; acc = 0.0
        for a, b in zip(pts, pts[1:]):
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            if acc + d >= left:
                f = (left - acc) / max(d, 1e-6); out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)); break
            out.append(b); acc += d
        if len(out) >= 2: path.addPath(smooth(out, False, 0.7) if len(out) > 2 else poly(out, False)); end = out[-1]
        left = 0
    return path, end


def _tablet_screen(c, x0, y0, w, h, screen='sign', ink=1.0, t=0.0, det=2, ts='3:09 AM', sig='initial', flash=0.0,
                   name='', glitch=0.0):
    """The Nightline handheld's screen in local coords (x0, y0, w, h). screen: 'sign' (signature request: sig None empty,
    'initial' your first letter cut off at ink 0..1, 'lily' the child's 'Lily.'), 'sent' (green 'RETURN COMPLETE'),
    'camera' (viewfinder), 'off' (dark glass), 'glow' (plain lit screen: far / small)."""
    scr = rrect(x0, y0, w, h, 3)
    if screen == 'off':
        c.fill(scr, '#0b0d12'); c.grad(scr, x0, y0, x0 + w, y0 + h, [(0, '#2a2f3c', 200), (0.45, '#0b0d12', 0), (1, '#0b0d12', 0)])
        c.line(scr, c.lw * 0.5); return
    if screen == 'glow' or det < 1:
        c.fill(scr, '#dfe9f2'); c.radial(scr, x0 + w * 0.5, y0 + h * 0.4, max(w, h) * 0.7, [(0, '#ffffff', 255), (1, '#9fb4c8', 255)])
        c.fill(rect(x0, y0, w, h * 0.14), '#1b2236'); c.line(scr, c.lw * 0.5); return
    if screen == 'camera':
        c.fill(scr, '#121519'); c.radial(scr, x0 + w / 2, y0 + h / 2, max(w, h) * 0.7, [(0, '#3a3f48', 255), (1, '#0b0c10', 255)])
        L = min(w, h) * 0.12
        for (cx_, cy_, dx, dy) in ((x0 + 4, y0 + 4, 1, 1), (x0 + w - 4, y0 + 4, -1, 1), (x0 + 4, y0 + h - 4, 1, -1), (x0 + w - 4, y0 + h - 4, -1, -1)):
            c.line(poly([(cx_ + dx * L, cy_), (cx_, cy_), (cx_, cy_ + dy * L)], False), c.lw * 0.5, '#ffffff', 220)
        c.fill(oval(x0 + w / 2, y0 + h - 9, 5), '#ffffff', 230)
        if flash > 0: c.fill(scr, '#ffffff', 255 * flash)
        c.line(scr, c.lw * 0.5); return
    bg = '#eef1f4'
    c.fill(scr, bg)
    hb = h * 0.13
    c.fill(rrect(x0, y0, w, hb, 3), '#1b2236'); c.fill(rect(x0, y0 + hb * 0.5, w, hb * 0.5), '#1b2236')
    c.fill(minus(oval(x0 + hb * 0.55, y0 + hb * 0.5, hb * 0.3), oval(x0 + hb * 0.68, y0 + hb * 0.4, hb * 0.27)), '#e9cf7e')
    if det >= 2:
        text(c.cv, 'NIGHTLINE', *c.pt(x0 + w * 0.56, y0 + hb * 0.68), 900, hb * 0.42 * c.s, '#e9cf7e', 255, 0.08, 'center')
        text(c.cv, 'SIGNATURE REQUIRED', *c.pt(x0 + w / 2, y0 + hb + h * 0.075), 900, h * 0.05 * c.s, '#1b2236', 255, 0.03, 'center')
        text(c.cv, 'FROM: RETURN', *c.pt(x0 + w * 0.08, y0 + hb + h * 0.14), 800, h * 0.04 * c.s, '#53607a', 255, 0.04, 'left')
        text(c.cv, ('TO: ' + name) if name else 'TO:', *c.pt(x0 + w * 0.08, y0 + hb + h * 0.195), 800, h * 0.04 * c.s, '#53607a', 255, 0.04, 'left')
    else:
        for k, ww in enumerate((0.7, 0.45, 0.35)):
            c.fill(rect(x0 + w * (0.5 - ww / 2 if k == 0 else 0.08), y0 + hb + h * (0.05 + 0.065 * k), w * ww, h * 0.03), '#8a94a8')
    # signature box
    bx, by, bw, bh = x0 + w * 0.07, y0 + h * 0.42, w * 0.86, h * 0.36
    box = rrect(bx, by, bw, bh, 2)
    c.fill(box, '#ffffff'); c.line(box, c.lw * 0.35, '#9aa4b6')
    c.line(poly([(bx + bw * 0.08, by + bh * 0.8), (bx + bw * 0.92, by + bh * 0.8)], False), c.lw * 0.35, '#7b869b')
    c.line(_multi([poly([(bx + bw * 0.06, by + bh * 0.6), (bx + bw * 0.12, by + bh * 0.72)], False),
                   poly([(bx + bw * 0.12, by + bh * 0.6), (bx + bw * 0.06, by + bh * 0.72)], False)]), c.lw * 0.4, '#7b869b')
    if sig == 'initial':
        pth, end = _strokes_path(HAND_STROKES['J'], bx + bw * 0.2, by + bh * 0.05, bw * 0.34, bh * 0.82, 0.68 * ink, 0.3, 11, t)
        c.line(pth, max(1.4, c.lw * 0.55), '#1a2a6c')
        if end is not None and ink >= 0.999:
            c.fill(oval(end[0], end[1], max(1.6, c.lw * 0.45)), '#1a2a6c')          # the pen stopped here (a blot)
    elif sig == 'lily':
        pth, end = _strokes_path(HAND_STROKES['LILY'], bx + bw * 0.2, by + bh * 0.12, bw * 0.38, bh * 0.56, ink, 1.0, 23, t)
        c.line(pth, max(1.6, c.lw * 0.65), '#1a2a6c')
    # timestamp + glitch bar
    if det >= 2 and ts:
        text(c.cv, ts, *c.pt(x0 + w * 0.93, y0 + h * 0.93), 800, h * 0.045 * c.s, '#53607a', 255, 0.03, 'right')
    if glitch > 0.01:
        gy = y0 + h * (0.2 + 0.6 * ((t * 7.3) % 1.0))
        c.fill(rect(x0, gy, w, h * 0.03), '#ff2a3a', 120 * glitch); c.fill(rect(x0 + 3, gy + h * 0.03, w, h * 0.012), '#2af0ff', 90 * glitch)
    if screen == 'sent':
        c.fill(rect(x0, by - h * 0.04, w, h * 0.16), '#2f9a5a', 235)
        if det >= 2: text(c.cv, 'RETURN COMPLETE', *c.pt(x0 + w / 2, by + h * 0.065), 900, h * 0.05 * c.s, '#ffffff', 255, 0.04, 'center')
    if flash > 0: c.fill(scr, '#ffffff', 255 * flash)
    c.line(scr, c.lw * 0.5)


def _tablet_body(c, det, P=None, t=0.0, back=False, screen=None, **kw):
    """Rugged courier handheld in prop units: 64 wide x 104 tall, centred. Front: bumper corners, screen, a row of keys
    and a red scanner window on the top edge; a stylus on a coiled tether. Back: hand strap and a NIGHTLINE sticker."""
    body = rrect(-32, -52, 64, 104, 10)
    c.fill(body, '#25272d')
    c.grad(body, -32, 0, 32, 0, [(0, '#3d4048', 255), (0.35, '#25272d', 255), (1, '#121317', 255)])
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            c.fill(rrect(sx_ * 32 - (14 if sx_ > 0 else 0), sy_ * 52 - (14 if sy_ > 0 else 0), 14, 14, 6), '#3a3c43')
    c.fill(rrect(-12, -56, 24, 6, 2), '#7a1418'); c.glow(0, -54, 14, 4, '#ff3a3a', 60)
    if back:
        c.line(body, c.lw * 0.8)
        strap = rrect(-24, -22, 48, 46, 8)
        c.fill(strap, '#15161a'); c.line(strap, c.lw * 0.5)
        if det >= 1:
            c.line(_multi([poly([(-18, -16 + k * 9), (18, -16 + k * 9)], False) for k in range(5)]), c.lw * 0.25, '#2c2e35', 200)
            c.fill(rrect(-16, 30, 32, 12, 2), '#1b2236'); c.fill(minus(oval(-9, 36, 4), oval(-7, 34, 3.6)), '#e9cf7e')
        c.fill(rrect(-18, -46, 16, 12, 4), '#0d0e12'); c.fill(oval(-10, -40, 4.2), '#2a3446')     # back camera + flash
        c.fill(oval(6, -40, 3.2), '#e8e2c8')
        fl = getattr(P, 'tablet_flash', 0.0) if P is not None else kw.get('flash', 0.0)
        if fl > 0.01:
            c.glow(6, -40, 120, 120, '#ffffff', 230 * fl); c.glow(6, -40, 40, 40, '#ffffff', 255 * fl)
        return
    scr_kind = screen or (getattr(P, 'tablet_screen', 'sign') if P is not None else 'sign')
    ink = getattr(P, 'tablet_ink', 1.0) if P is not None else kw.get('ink', 1.0)
    flash = getattr(P, 'tablet_flash', 0.0) if P is not None else kw.get('flash', 0.0)
    sig = kw.get('sig', 'initial' if scr_kind == 'sign' else ('lily' if scr_kind in ('lily', 'sent') else None))
    if scr_kind == 'lily': scr_kind = 'sign'
    _tablet_screen(c, -26, -44, 52, 66, scr_kind, ink, t, det, kw.get('ts', '3:09 AM'), sig, flash, kw.get('name', ''), kw.get('glitch', 0.0))
    if scr_kind not in ('off',):
        c.glow(0, -10, 46, 52, '#cfe2ff', 40)
    for k in range(4):
        kx = -21 + k * 14
        c.fill(rrect(kx - 5, 29, 10, 7, 2), '#3c3f47'); c.line(rrect(kx - 5, 29, 10, 7, 2), c.lw * 0.25)
    c.fill(rrect(-8, 40, 16, 6, 2), '#2f6a3a')
    c.line(body, c.lw * 0.8)
    if det >= 1:                                                   # stylus tether coiling off the right edge
        pts = []
        for k in range(90):
            u = k / 89.0
            bx_ = 32 + 6 * u + 2.5 * math.sin(t * 1.3 + u * 3)
            pts.append((bx_ + 3.2 * math.cos(u * 2 * PI * 11), 14 + 70 * u + 1.6 * math.sin(u * 2 * PI * 11)))
        cp = smooth(pts, False, 0.6)
        c.line(cp, c.lw * 0.7, LINE, 230); c.line(cp, c.lw * 0.35, '#5a5d66', 255)


def _keyring(c, det, t=0.0, rust=0.0, n=4, spread=1.0, beads=True, jangle=0.0):
    """Dad's ring of keys on the keychain you made him in second grade (pony beads and three letter cubes D-A-D on a
    cord, a lumpy clay star). Prop units: the ring centred at (0, 0), about 90 units across. rust 0..1 (the box at
    sunrise: orange-brown keys, faded beads, frayed cord). jangle adds a decaying swing (after a drop)."""
    rcol = mix('#b8bcc4', '#8a4a22', rust); rsh = mix('#6c7078', '#4a2410', rust)
    c.line(oval(0, 0, 15), c.lw * 2.0, LINE); c.line(oval(0, 0, 15), c.lw * 1.1, rcol)
    keys = [('#c9a95a', 46, -0.55), ('#b8bcc4', 54, -0.15), ('#9aa0a8', 40, 0.25), ('#c9a95a', 34, 0.62)][:n]
    sw = jangle * math.sin(t * 17.0) * math.exp(-0)
    for k, (kc, L, a0) in enumerate(keys):
        a_ = a0 * spread + 0.25 * sw * (1 if k % 2 else -1)
        kc = mix(kc, '#7a3a18', rust * (0.75 + 0.25 * hash01(k, 3)))
        kk = c.sub(math.sin(a_) * 15, math.cos(a_) * 15, -math.degrees(a_))
        head = rrect(-11, 0, 22, 20, 7)
        blade = poly([(-4.5, 18), (4.5, 18), (4.5, 18 + L * 0.85), (0, 18 + L), (-4.5, 18 + L * 0.85)])
        kp = union(head, blade)
        kk.fill(kp, kc)
        kk.fill(_crescent(kp, 3, 0), mix(kc, '#000000', 0.35), 140)
        if det >= 1:
            for j in range(3): kk.fill(rect(4.5, 26 + j * L * 0.2, 4, 4), kc)
            kk.fill(oval(0, 7, 3.5), '#20160f')
            if rust > 0.05:
                for j in range(5):
                    kk.fill(oval((hash01(j + 9 * k, 5) - 0.5) * 8, 20 + hash01(j + 9 * k, 6) * L * 0.8, 2.2 + 2 * hash01(j, 7)),
                            '#5a2a10', 160 * rust)
        kk.line(kp, c.lw * 0.6)
    if beads:                                                     # the keychain: cord, beads, D-A-D cubes, clay star
        cordc = mix('#3a7bd5', '#7d7466', rust * 0.8)
        a_ = 2.6 + 0.3 * sw
        cx_, cy_ = math.sin(a_) * 15, math.cos(a_) * 15
        pts = [(cx_, cy_), (cx_ - 14, cy_ + 18), (cx_ - 20, cy_ + 44), (cx_ - 16, cy_ + 70)]
        c.line(smooth(pts, False), c.lw * 1.2, LINE); c.line(smooth(pts, False), c.lw * 0.6, cordc)
        bead_cols = ['#e5483d', '#f2c230', '#3fb26b', '#3a7bd5', '#b14fd0']
        for k in range(6):
            u = (k + 0.6) / 7.0
            bx = cx_ - 14 * u - 6 * u * u; by = cy_ + 70 * u
            if k in (1, 2, 3):
                cube = rrect(bx - 7, by - 7, 14, 14, 2.5)
                c.fill(cube, mix('#f3efe6', '#b8a98c', rust)); c.line(cube, c.lw * 0.45)
                if det >= 2:
                    text(c.cv, 'DAD'[k - 1], *c.pt(bx, by + 4.0), 900, 10.5 * c.s, mix('#1d1f26', '#5a4a3a', rust), 255, 0, 'center')
            else:
                bc = mix(bead_cols[k % 5], '#8a7a66', rust * 0.7)
                c.fill(oval(bx, by, 6.5), bc); c.line(oval(bx, by, 6.5), c.lw * 0.4)
                if det >= 1: c.fill(oval(bx - 2, by - 2, 1.8), '#ffffff', 170 * (1 - rust))
        sx_, sy_ = pts[-1][0], pts[-1][1] + 12
        st_ = []
        for k in range(10):
            a2 = -PI / 2 + k * PI / 5 + 0.2; rr = 14 if k % 2 == 0 else 7
            st_.append((sx_ + math.cos(a2) * rr * (1 + 0.12 * hash01(k, 8)), sy_ + math.sin(a2) * rr))
        star = smooth(st_, True, 0.35)
        c.fill(star, mix('#f08a3c', '#8a6a4a', rust)); c.line(star, c.lw * 0.6)
        if det >= 1: c.fill(oval(sx_ - 3, sy_ - 2, 2.2), '#1d1f26', 200)


def _prop_delivery(c, name, det, t=0.0, P=None):
    if name == 'tablet': _tablet_body(c, det, P, t)
    elif name == 'tablet_back': _tablet_body(c, det, P, t, back=True)
    elif name == 'stylus':
        c.shape(rrect(-4, -40, 8, 80, 3), '#2a2c33', c.lw * 0.6); c.fill(poly([(-4, 40), (4, 40), (0, 50)]), '#8a8f99')
    elif name == 'keys_dad': _keyring(c.sub(0, -30, 0, 0.8), det, t)


def draw_tablet(pen, cx, cy, size, screen='sign', sig=None, ink=1.0, t=0.0, ts='3:09 AM', flash=0.0, name='', glitch=0.0,
                back=False, angle=0.0, detail=2):
    """The Nightline handheld at any scale (insert: 'the tablet fills the frame'). size = device height in design px,
    centred at (cx, cy). screen 'sign' | 'sent' | 'camera' | 'off' | 'glow'; sig None (empty line) | 'initial' (your first
    letter, stroke stopping halfway: ink 0..1 animates the pen, the blot appears at 1) | 'lily' ('Lily.' in a child's
    hand); ts = timestamp text (flicker it yourself: '3:09 AM' / '3:08 AM'); glitch 0..1 adds a torn scanline."""
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 1.4) * 0.85).sub(cx, cy, angle, size / 104.0)
    if sig is None and screen == 'sign': sig = 'none'
    _tablet_body(c, detail, None, t, back=back, screen=screen, sig=sig, ink=ink, ts=ts, flash=flash, name=name, glitch=glitch)


def draw_keyring(pen, x, y, size, t=0.0, rust=0.0, angle=0.0, jangle=0.0, detail=2):
    """Dad's keys on the second-grade bead keychain. size = overall height (ring to star) in design px; (x, y) = the ring."""
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 2.4) * 0.8).sub(x, y, angle, size / 110.0)
    _keyring(c, detail, t, rust, jangle=jangle)


# ---------------------------------------------------------------------------------------------- outfits
def _torso_rows(sp, B):
    b = sp['body']; o = sp['outfit']; k = B.chest_k
    ys = [B.y_sh - 30, B.y_sh - 10, B.y_sh + 16, B.y_ch, B.y_ch + 80, B.y_wa, B.y_belt, B.y_hip]
    ws = [b['neck'] + 16, b['sh'] * 0.84, b['sh'], b['ch'] * k, b['ch'] * 0.97 * k, b['wa'], b['hip'] * 0.98, b['hip']]
    if o == 'hoodie':
        ws = [b['neck'] + 22, b['sh'] * 0.86, b['sh'], b['ch'] * k, b['ch'] * k, b['wa'] + 6, b['hip'] + 6, b['hip'] + 4]
    elif o == 'robe':                                     # thick terry: fuller chest and waist, belt cinch
        ws = [b['neck'] + 24, b['sh'] * 0.9, b['sh'] + 4, b['ch'] * k + 6, b['ch'] * k + 4, b['wa'] + 2, b['hip'] + 8, b['hip'] + 10]
    elif o == 'pajamas':                                  # loose, boxy kid's top
        ws = [b['neck'] + 14, b['sh'] * 0.88, b['sh'] + 2, b['ch'] * k + 4, b['ch'] * k + 6, b['wa'] + 8, b['hip'] + 8, b['hip'] + 6]
    elif o == 'flannel':
        ws = [b['neck'] + 18, b['sh'] * 0.86, b['sh'], b['ch'] * k + 2, b['ch'] * k, b['wa'] + 4, b['hip'] + 2, b['hip']]
    elif o == 'usher':                                    # the dummy's stiff little jacket: square shoulders, short
        ws = [b['neck'] + 18, b['sh'] * 0.92, b['sh'] + 2, b['ch'] * k + 4, b['ch'] * k + 2, b['wa'] + 4, b['hip'] + 4, b['hip'] + 2]
    elif o in ('longcoat', 'denim', 'suit70', 'cardi_m'):
        ws = [b['neck'] + 22, b['sh'] * 0.9, b['sh'] + 4, b['ch'] * k + 6, b['ch'] * k + 4, b['wa'] + 6, b['hip'] + 6, b['hip'] + 6]
    elif o == 'gown':                                     # thin cotton over a gaunt body: hangs loose
        ws = [b['neck'] + 12, b['sh'] * 0.86, b['sh'] - 2, b['ch'] * k, b['ch'] * k + 2, b['wa'] + 10, b['hip'] + 10, b['hip'] + 10]
    if ys[4] >= ys[5] - 4:                                # a big-headed figure (the dummy): keep the rows ascending
        ys[4] = (ys[3] + ys[5]) * 0.5
    ds = [w * f for w, f in zip(ws, [0.55, 0.52, 0.5, 0.56, 0.6, 0.6, 0.62, 0.64])]
    return ys, ws, ds


def _cloth_shade(c, path, sh, a, lside=1.0, dx=30.0, hi=None, hi_a=0):
    c.fill(_crescent(path, -lside * dx, 0), sh, a)
    if hi: c.fill(_crescent(path, lside * dx * 0.5, 0), hi, hi_a)


def _surf_poly(B, rows, pts, back=False, dz=0.0):
    out = []; vis = []
    for x0, y0 in pts:
        X, Y, v, _ = B.surf(x0, y0, dz, back, rows)
        out.append((X, Y)); vis.append(v)
    return out, min(vis)


def _police_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    sh = b['sh']; ch = b['ch']
    ys, ws, ds = rows
    yS, yC, yB = B.y_sh, B.y_ch, B.y_belt
    male = sp['sex'] == 'm'
    # placket + buttons
    pts, v = _surf_poly(B, rows, [(0, yS + 10), (0, yB - 16)])
    if v > 0.05:
        c.line(poly(pts, False), lw * 0.5, '#0c1120', 220)
        c.line(poly([(pts[0][0] + 5, pts[0][1]), (pts[1][0] + 5, pts[1][1])], False), lw * 0.35, cl['shirt_hi'], 120)
        for k in range(4):
            X, Y, vv, s = B.surf(4, yC + 40 + k * 62, 2, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 3.6 * s, 3.6 * s), '#0b0f1a'); c.fill(oval(X - 1, Y - 1, 1.3 * s), '#4a5677')
    # pockets with flaps (both chests)
    for side in (-1, 1):
        x0, x1 = side * 26, side * (ch * 0.72)
        y0, y1 = yC - 44, yC + 34
        pk, v = _surf_poly(B, rows, [(x0, y0 + 14), (x1, y0 + 14), (x1, y1), ((x0 + x1) / 2, y1 + 6), (x0, y1)])
        if v > 0.05:
            pp = poly(pk)
            c.fill(pp, cl['shirt_sh'], 90); c.line(pp, lw * 0.5, '#0b101d')
            fl, _ = _surf_poly(B, rows, [(x0 - side * 2, y0), (x1 + side * 2, y0), (x1 + side * 2, y0 + 16), ((x0 + x1) / 2, y0 + 26), (x0 - side * 2, y0 + 16)])
            fp = poly(fl)
            c.fill(fp, cl['shirt']); c.line(fp, lw * 0.55, '#0b101d')
            if det >= 1:
                ctr, _ = _surf_poly(B, rows, [((x0 + x1) / 2, y0 + 26), ((x0 + x1) / 2, y1 + 2)])
                c.line(poly(ctr, False), lw * 0.35, '#0b101d', 160)
                X, Y, vv, s = B.surf((x0 + x1) / 2, y0 + 19, 2, False, rows)
                c.fill(oval(X, Y, 3.2 * s), '#0b0f1a')
                if det >= 2:
                    st_, _ = _surf_poly(B, rows, [(x0 + side * 4, y0 + 20), (x1 - side * 4, y0 + 20)])
    # epaulettes
    for side in (-1, 1):
        ep, v = _surf_poly(B, rows, [(side * (b['neck'] + 12), yS - 24), (side * sh * 0.92, yS + 2), (side * sh * 0.9, yS + 18), (side * (b['neck'] + 10), yS - 8)], dz=3)
        if v > -0.1:
            epp = poly(ep); c.fill(epp, cl['shirt_sh']); c.line(epp, lw * 0.5, '#0b101d')
            X, Y, vv, s = B.surf(side * (b['neck'] + 22), yS - 12, 5, False, rows)
            c.fill(oval(X, Y, 4.2 * s), cl['silver']); c.line(oval(X, Y, 4.2 * s), lw * 0.3)
    # tie
    if male:
        tie, v = _surf_poly(B, rows, [(-8, yS - 16), (8, yS - 16), (13, yC + 120), (0, yC + 140), (-13, yC + 120)], dz=4)
        if v > 0.05:
            tp = smooth(tie, True, 0.3); c.fill(tp, cl['tie']); c.line(tp, lw * 0.5)
            knot, _ = _surf_poly(B, rows, [(-10, yS - 30), (10, yS - 30), (7, yS - 12), (-7, yS - 12)], dz=5)
            c.shape(poly(knot), cl['tie'], lw * 0.5)
            X, Y, vv, s = B.surf(0, yC + 30, 6, False, rows)
            c.fill(rrect(X - 16 * s, Y - 2.5 * s, 32 * s, 5 * s, 2 * s), cl['gold']); c.line(rrect(X - 16 * s, Y - 2.5 * s, 32 * s, 5 * s, 2 * s), lw * 0.3)
    # collar
    for side in (-1, 1):
        col_, v = _surf_poly(B, rows, [(side * 4, yS - 22), (side * (b['neck'] + 16), yS - 34), (side * (b['neck'] + 8), yS - 14), (side * 34, yS + 22)], dz=6)
        if v > -0.2:
            cp = poly(col_); c.fill(cp, cl['shirt']); c.line(cp, lw * 0.6)
    # badge (character's left = +x), name plate (right)
    X, Y, v, s = B.surf(ch * 0.47, yC - 64, 8, False, rows)
    if v > 0.1:
        bc = c.sub(X, Y, 0, s * (B.surf(ch * 0.47 + 1, yC - 64, 8, False, rows)[0] - X) / max(s, 1e-3) if False else s, s)
        star = []
        for k in range(16):
            a_ = -PI / 2 + k * PI / 8; rr = 22 if k % 2 == 0 else 15
            star.append((math.cos(a_) * rr, math.sin(a_) * rr * 1.05))
        sp_ = smooth(star, True, 0.25)
        bc.fill(sp_, cl['gold']); bc.radial(sp_, -6, -8, 26, [(0, cl['gold_hi'], 255), (0.55, cl['gold'], 255), (1, cl['gold_sh'], 255)])
        bc.line(sp_, lw * 0.6)
        if det >= 1:
            bc.fill(oval(0, 1, 9), cl['gold_sh']); bc.line(oval(0, 1, 9), lw * 0.3)
            if det >= 2:
                c.cv.save(); m = skia.Matrix(); m.preConcat(bc.M); c.cv.concat(m)
                text(c.cv, '4471', 0, 4, 900, 8, '#2a1f08', 255, 0.5, 'center'); c.cv.restore()
    X, Y, v, s = B.surf(-ch * 0.47, yC - 60, 6, False, rows)
    if v > 0.1:
        npl = rrect(X - 24 * s, Y - 6 * s, 48 * s, 12 * s, 2 * s)
        c.fill(npl, cl['silver']); c.line(npl, lw * 0.4)
        if det >= 2:
            text(c.cv, 'M. DALE' if male else 'K. VOSS', X, Y + 3.5 * s, 800, 8.5 * s, '#1b1e26', 255, 0.5, 'center')
        elif det >= 1:
            c.fill(rect(X - 16 * s, Y - 1.5 * s, 32 * s, 3 * s), '#4b5160')
    # bodycam (centre chest)
    X, Y, v, s = B.surf(0, yC + 8, 10, False, rows)
    if v > 0.1:
        bc = c.sub(X, Y, 0, s)
        bc.fill(rrect(-21, -26, 42, 56, 7), '#000000', 90)
        bx = rrect(-20, -28, 40, 54, 7)
        bc.fill(bx, cl['black']); bc.grad(bx, 0, -28, 0, 26, [(0, cl['black_hi'], 255), (0.4, cl['black'], 255), (1, '#0a0a0c', 255)])
        bc.line(bx, lw * 0.7)
        bc.fill(oval(0, -6, 11), '#0a0b10'); bc.line(oval(0, -6, 11), lw * 0.45)
        bc.radial(oval(0, -6, 9), -3, -9, 12, [(0, '#5a6a8a', 255), (0.5, '#1a2030', 255), (1, '#05060a', 255)])
        bc.fill(oval(-3, -9, 2.5), '#c8d4f0', 220)
        on = clamp(P.cam_on)
        blink = 1.0 if (t * 1.2) % 1.0 < 0.55 else 0.35
        bc.fill(oval(12, 16, 3.6), mix('#3a1010', '#ff2a2a', on * blink)); bc.line(oval(12, 16, 3.6), lw * 0.3)
        if on * blink > 0.5: bc.glow(12, 16, 12, 12, '#ff3030', 120 * on)
        bc.fill(rrect(-12, 13, 14, 7, 2), '#2c2e35')
        if det >= 2:
            for k in range(3): bc.line(poly([(-13 + k * 5, 24), (-11 + k * 5, 24)], False), lw * 0.3, '#5a5e68')
    # shoulder mic (character's left shoulder) + coiled cord to belt radio
    mx, my, mv, ms = B.surf(sh * 0.66, yS + 14, 12, False, rows)
    rx_, ry_, rv_, rs_ = B.surf(b['hip'] * 0.82, yB - 2, 14, False, rows)
    held = (P.hl_prop in ('radio', 'mic'))
    if held:                                          # v2.1: the cord runs from the held mic (the hand) to the belt
        _S, _E, _W = _arm_data(sp, B, P, 1)
        hp_ = B.p3(*_W)
        mx, my, ms = hp_[0], hp_[1] - 22 * hp_[2], hp_[2]
        mv = 1.0
    if mv > -0.3:
        sway = 8 * P.sec_x
        cord = [(mx, my + 22 * ms)]
        for k in range(1, 9):
            u = k / 8
            cx_ = mx + (rx_ - mx) * u + math.sin(u * PI) * (30 + sway) * ms
            cy_ = my + 22 * ms + (ry_ - my - 22 * ms) * u + math.sin(u * PI) * 20 * ms
            cord.append((cx_, cy_))
        cp_ = smooth(cord, False)
        c.line(cp_, lw * 1.5, LINE); c.line(cp_, lw * 0.75, '#2b2d33')
        if det >= 1:
            coils = []
            for k in range(1, 18):
                u = k / 18
                i_f = u * 8; i0 = int(i_f); fr = i_f - i0
                x_ = cord[i0][0] + (cord[min(i0 + 1, 8)][0] - cord[i0][0]) * fr; y_ = cord[i0][1] + (cord[min(i0 + 1, 8)][1] - cord[i0][1]) * fr
                coils.append(oval(x_, y_, 4.2 * ms, 2.2 * ms))
            c.line(_multi(coils), lw * 0.3, '#4a4d55', 200)
        if not held:
            mc = c.sub(mx, my, -8 + 6 * P.sec_x, ms)
            body_ = rrect(-15, -24, 30, 48, 7)
            mc.fill(body_, cl['black']); mc.grad(body_, -15, 0, 15, 0, [(0, cl['black_hi'], 255), (0.5, cl['black'], 255), (1, '#08080a', 255)])
            mc.line(body_, lw * 0.7)
            for k in range(5): mc.line(poly([(-9, -16 + k * 6), (9, -16 + k * 6)], False), lw * 0.35, '#050506')
            mc.shape(rrect(-17, 6, 6, 14, 2), '#2a2c33', lw * 0.35)
            mc.fill(oval(9, 15, 2.5), '#2f8a3a' if (t % 2.0) < 1.6 else '#123516')


def _police_belt(c, sp, B, rows, P, det, back=False):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yB = B.y_belt
    w = b['hip'] * 0.98
    top, bot = [], []
    for k in range(13):
        x0 = -w + 2 * w * k / 12
        X, Y, v, s = B.surf(x0, yB - 17, 3, back, rows); top.append((X, Y))
        X, Y, v, s = B.surf(x0, yB + 17, 3, back, rows); bot.append((X, Y))
    band = smooth(top + bot[::-1], True, 0.4)
    c.fill(band, cl['belt'])
    if det >= 1:
        c.line(smooth(top, False, 0.4), lw * 0.3, '#3a3d45', 200)
        for k in range(-3, 4):
            X, Y, v, s = B.surf(k * w * 0.27, yB, 4, back, rows)
            if v > 0.1: c.fill(rrect(X - 4 * s, Y - 18 * s, 8 * s, 36 * s, 2 * s), '#1c1d22'); c.line(rrect(X - 4 * s, Y - 18 * s, 8 * s, 36 * s, 2 * s), lw * 0.3)
    c.line(band, lw * 0.7)
    if not back:
        X, Y, v, s = B.surf(0, yB, 5, False, rows)
        if v > 0.1:
            bk = rrect(X - 15 * s, Y - 13 * s, 30 * s, 26 * s, 3 * s)
            c.fill(bk, cl['silver']); c.radial(bk, X - 5 * s, Y - 5 * s, 22 * s, [(0, '#e6eaef', 255), (1, cl['silver_sh'], 255)]); c.line(bk, lw * 0.5)
            c.fill(rrect(X - 8 * s, Y - 6 * s, 16 * s, 12 * s, 2 * s), cl['belt'])
    # gear: holster (char right = -x), mag pouch, cuffs, radio (char left = +x), flashlight
    gear = [(-w * 0.86, 'holster'), (-w * 0.42, 'cuffs'), (w * 0.4, 'mags'), (w * 0.84, 'radio'), (-w * 0.98, 'light')]
    for x0, kind in gear:
        X, Y, v, s = B.surf(x0, yB, 12 if kind != 'holster' else 16, back, rows)
        if v < -0.15: continue
        gc = c.sub(X, Y, 0, s)
        if kind == 'holster':
            g = smooth([(-14, -14), (14, -14), (16, 70), (6, 112), (-12, 112), (-16, 70)], True, 0.5)
            gc.fill(g, '#121317'); gc.grad(g, -16, 0, 16, 0, [(0, '#2b2d34', 255), (0.6, '#121317', 255), (1, '#060607', 255)]); gc.line(g, lw * 0.7)
            grip = smooth([(-8, -14), (8, -14), (18, -44), (6, -50), (-6, -26)], True, 0.5)
            gc.shape(grip, '#1e1f24', lw * 0.6)
            if det >= 1:
                for k in range(3): gc.line(poly([(-2 + k * 4, -24 - k * 6), (8 + k * 3, -30 - k * 6)], False), lw * 0.25, '#3a3c44')
                gc.fill(rrect(-10, 10, 20, 26, 4), '#1b1c21'); gc.line(rrect(-10, 10, 20, 26, 4), lw * 0.35)
                gc.fill(oval(0, 23, 2.5), cl['silver'])
        elif kind == 'radio':
            g = rrect(-15, -6, 30, 58, 5)
            gc.fill(g, '#16171b'); gc.grad(g, -15, 0, 15, 0, [(0, '#33363e', 255), (1, '#0a0a0c', 255)]); gc.line(g, lw * 0.6)
            gc.shape(rrect(-10, -38, 7, 34, 3), '#111114', lw * 0.5)
            gc.shape(oval(6, -12, 5), '#24262c', lw * 0.4)
            if det >= 1:
                gc.fill(rect(-9, 8, 18, 10), '#4f7a5a'); gc.line(rect(-9, 8, 18, 10), lw * 0.3)
        elif kind == 'mags':
            for k in (-1, 1):
                gc.shape(rrect(k * 9 - 8, -10, 16, 40, 4), '#141519', lw * 0.5)
                gc.fill(oval(k * 9, -2, 2.4), cl['silver'])
        elif kind == 'cuffs':
            gc.shape(rrect(-14, -10, 28, 30, 5), '#141519', lw * 0.5)
            gc.fill(oval(0, -2, 2.4), cl['silver'])
        elif kind == 'light':
            gc.shape(rrect(-6, -16, 12, 70, 4), '#1a1b20', lw * 0.5)


def _hoodie_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    # kangaroo pocket
    pk, v = _surf_poly(B, rows, [(-62, B.y_wa - 10), (62, B.y_wa - 10), (80, B.y_hip - 18), (-80, B.y_hip - 18)], dz=3)
    if v > 0.05:
        pp = smooth(pk, True, 0.25); c.fill(pp, cl['top_sh'], 120); c.line(pp, lw * 0.6)
        for side in (-1, 1):
            sl, _ = _surf_poly(B, rows, [(side * 62, B.y_wa - 10), (side * 76, B.y_wa + 60)], dz=4)
            c.line(poly(sl, False), lw * 0.5)
    # hem rib
    hem, v = _surf_poly(B, rows, [(-b['hip'] - 4, B.y_hip - 26), (b['hip'] + 4, B.y_hip - 26)], dz=2)
    if v > -0.2: c.line(poly(hem, False), lw * 0.45, LINE, 200)
    # neckline + drawstrings
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 14, yS - 28), (0, yS - 2), (b['neck'] + 14, yS - 28)], dz=4)
    if v > -0.2: c.line(smooth(nk, False), lw * 0.7)
    for side in (-1, 1):
        sw = 4 * P.sec_x
        st, v = _surf_poly(B, rows, [(side * 16, yS - 6), (side * 18 + sw, yC + 10), (side * 15 + sw * 1.5, yC + 60)], dz=7)
        if v > 0.0:
            sp_ = smooth(st, False); c.line(sp_, lw * 2.2, LINE); c.line(sp_, lw * 1.0, cl['string'])
            x_, y_ = st[-1]
            c.fill(rrect(x_ - 3.5, y_, 7, 14, 2), '#8c8a84'); c.line(rrect(x_ - 3.5, y_, 7, 14, 2), lw * 0.35)
    # raglan seams
    if det >= 1:
        for side in (-1, 1):
            sm, v = _surf_poly(B, rows, [(side * (b['neck'] + 10), yS - 24), (side * b['ch'] * 0.86, yC + 10)], dz=1)
            if v > 0.0: c.line(smooth(sm, False), lw * 0.4, cl['top_sh'], 220)


def _coat_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    # shirt opening and lapels
    op, v = _surf_poly(B, rows, [(-14, yS - 24), (14, yS - 24), (10, yC + 70), (0, yC + 92), (-10, yC + 70)], dz=3)
    if v > 0.05:
        c.fill(smooth(op, True, 0.2), cl['shirt']); c.line(smooth(op, True, 0.2), lw * 0.5)
        for side in (-1, 1):
            lp, _ = _surf_poly(B, rows, [(side * 12, yS - 30), (side * (b['neck'] + 26), yS - 36), (side * (b['neck'] + 30), yS - 4),
                                         (side * 56, yC - 10), (side * 40, yC + 6), (side * 10, yC + 86)], dz=6)
            lpp = poly(lp)
            c.fill(lpp, cl['coat_hi'] if side < 0 else cl['coat']); c.line(lpp, lw * 0.7)
        for k in range(3):
            X, Y, vv, s = B.surf(8, yC + 110 + k * 80, 4, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 6.5 * s), cl['button'], lw * 0.4)
        cl_, _ = _surf_poly(B, rows, [(2, yC + 92), (2, -232)], dz=2)
        c.line(poly(cl_, False), lw * 0.55)
        for side in (-1, 1):
            fl, _ = _surf_poly(B, rows, [(side * 30, B.y_wa + 70), (side * 92, B.y_wa + 66), (side * 94, B.y_wa + 88), (side * 30, B.y_wa + 92)], dz=4)
            c.shape(poly(fl), cl['coat'], lw * 0.5)


def _cardigan_front(c, sp, B, rows, P, det, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-30, yS - 26), (30, yS - 26), (24, B.y_hip - 20), (-18, B.y_hip - 20)], dz=2)
    if v > 0.05:
        bl = smooth(op, True, 0.2); c.fill(bl, cl['blouse']); c.line(bl, lw * 0.5)
        with c.clip(bl):
            c.grad(bl, 0, yS, 0, B.y_hip, [(0, cl['blouse'], 0), (1, cl['blouse_sh'], 200)])
        for side in (-1, 1):
            cc, _ = _surf_poly(B, rows, [(0, yS - 20), (side * 30, yS - 26), (side * 36, yS + 4), (side * 6, yS + 6)], dz=5)
            c.shape(smooth(cc, True, 0.6), cl['blouse'], lw * 0.55)
        X, Y, vv, s = B.surf(0, yS + 34, 6, False, rows)
        _pearls(c.sub(X, Y - 14 * s, 0, s), 0, 0, 64, 9, det, cl['pearl'])
        for side in (-1, 1):
            ed, _ = _surf_poly(B, rows, [(side * 30, yS - 26), (side * 26, B.y_hip - 20)], dz=3)
            c.line(poly(ed, False), lw * 2.4, LINE); c.line(poly(ed, False), lw * 1.3, cl['top_hi'])
        for k in range(4):
            X, Y, vv, s = B.surf(-33, yC + k * 60, 5, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 5 * s), '#d8cfc0', lw * 0.35)
    if det >= 1:
        for k in range(-5, 6):
            if abs(k) < 2: continue
            rb, v = _surf_poly(B, rows, [(k * 18, yS + 8), (k * 19, B.y_hip - 26)], dz=1)
            if v > 0.1: c.line(poly(rb, False), lw * 0.25, cl['top_sh'], 150)
        hem, v = _surf_poly(B, rows, [(-b['hip'], B.y_hip - 24), (b['hip'], B.y_hip - 24)], dz=1)
        if v > -0.2: c.line(poly(hem, False), lw * 0.4, LINE, 200)


# ---------------------------------------------------------------------------------------------- delivery outfits
def _courier_front(c, sp, B, rows, P, det, t):
    """Nightline work shirt: pointed collar open at the throat (dark undershirt), button placket, two flap pockets, the
    crescent-moon NIGHTLINE patch on his left chest and a cream name tag 'NO. 307' on the right (3:07)."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    ch = b['ch']; yS, yC, yB = B.y_sh, B.y_ch, B.y_belt
    # undershirt in the open collar
    vn, v = _surf_poly(B, rows, [(-22, yS - 26), (22, yS - 26), (0, yS + 22)], dz=3)
    if v > 0.0: c.fill(poly(vn), '#2a2420'); c.line(poly(vn), lw * 0.4)
    pts, v = _surf_poly(B, rows, [(0, yS + 22), (0, yB - 16)])
    if v > 0.05:
        c.line(poly(pts, False), lw * 0.5, mix(cl['shirt_sh'], '#000000', 0.4), 220)
        for k in range(4):
            X, Y, vv, s_ = B.surf(4, yC + 34 + k * 62, 2, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 3.6 * s_), '#2a1d14'); c.fill(oval(X - 1, Y - 1, 1.3 * s_), '#9a7a5e')
    for side in (-1, 1):
        x0, x1 = side * 26, side * (ch * 0.72)
        y0, y1 = yC - 40, yC + 36
        pk, v = _surf_poly(B, rows, [(x0, y0 + 14), (x1, y0 + 14), (x1, y1), ((x0 + x1) / 2, y1 + 5), (x0, y1)])
        if v > 0.05:
            pp = poly(pk); c.fill(pp, cl['shirt_sh'], 80); c.line(pp, lw * 0.5, '#1e140c')
            fl, _ = _surf_poly(B, rows, [(x0 - side * 2, y0), (x1 + side * 2, y0), (x1 + side * 2, y0 + 16), (x0 - side * 2, y0 + 16)])
            c.fill(poly(fl), cl['shirt']); c.line(poly(fl), lw * 0.55, '#1e140c')
            if det >= 1 and side < 0:                         # a pen clipped in his right pocket
                X, Y, vv, s_ = B.surf(x0 + side * 14, y0 + 2, 4, False, rows)
                c.fill(rrect(X - 3 * s_, Y - 26 * s_, 6 * s_, 30 * s_, 2 * s_), '#14161b'); c.line(rrect(X - 3 * s_, Y - 26 * s_, 6 * s_, 30 * s_, 2 * s_), lw * 0.35)
                c.fill(rect(X + 1 * s_, Y - 24 * s_, 2 * s_, 16 * s_), '#b9bcc4')
    for side in (-1, 1):
        col_, v = _surf_poly(B, rows, [(side * 3, yS - 24), (side * (b['neck'] + 14), yS - 34), (side * (b['neck'] + 10), yS - 10), (side * 40, yS + 26)], dz=6)
        if v > -0.2: cp = poly(col_); c.fill(cp, cl['shirt']); c.line(cp, lw * 0.6)
    # NIGHTLINE patch (character's left = +x): navy, gold rim, crescent moon, lettering on close-ups
    X, Y, v, s_ = B.surf(ch * 0.47, yC - 70, 7, False, rows)
    if v > 0.1:
        pc = c.sub(X, Y, 0, s_)
        pat = rrect(-34, -15, 68, 30, 9)
        pc.fill(pat, cl['patch']); pc.line(pat, lw * 1.0, cl['patch_rim']); pc.line(pat, lw * 0.35)
        pc.fill(minus(oval(-21, 0, 10), oval(-17, -4, 9)), cl['moon'])
        if det >= 2:
            c.cv.save(); m = skia.Matrix(); m.preConcat(pc.M); c.cv.concat(m)
            text(c.cv, 'NIGHTLINE', 8, 3.5, 900, 9.0, cl['moon'], 255, 0.06, 'center'); c.cv.restore()
        elif det >= 1:
            pc.fill(rect(-6, -2, 32, 4), cl['moon'], 200)
    X, Y, v, s_ = B.surf(-ch * 0.47, yC - 68, 6, False, rows)
    if v > 0.1:
        tg = rrect(X - 27 * s_, Y - 9 * s_, 54 * s_, 18 * s_, 3 * s_)
        c.fill(tg, cl['tag']); c.line(tg, lw * 0.45)
        if det >= 2:
            text(c.cv, 'NO. 307', X, Y + 4.2 * s_, 900, 11 * s_, cl['tag_ink'], 255, 0.08, 'center')
        elif det >= 1:
            c.fill(rect(X - 17 * s_, Y - 1.5 * s_, 34 * s_, 3 * s_), cl['tag_ink'], 200)


def _courier_belt(c, sp, B, rows, P, det, back=False):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yB = B.y_belt; w = b['hip'] * 0.98
    top, bot = [], []
    for k in range(13):
        x0 = -w + 2 * w * k / 12
        X, Y, v, s_ = B.surf(x0, yB - 11, 3, back, rows); top.append((X, Y))
        X, Y, v, s_ = B.surf(x0, yB + 11, 3, back, rows); bot.append((X, Y))
    band = smooth(top + bot[::-1], True, 0.4)
    c.fill(band, cl['belt']); c.line(band, lw * 0.6)
    if not back:
        X, Y, v, s_ = B.surf(0, yB, 5, False, rows)
        if v > 0.1:
            bk = rrect(X - 13 * s_, Y - 11 * s_, 26 * s_, 22 * s_, 3 * s_)
            c.fill(bk, cl['buckle']); c.line(bk, lw * 0.45)
            c.fill(rrect(X - 7 * s_, Y - 5 * s_, 14 * s_, 10 * s_, 2 * s_), cl['belt'])
        # a ring of keys on a carabiner at his right hip (it jingles when he walks)
        X, Y, v, s_ = B.surf(-w * 0.62, yB + 4, 6, False, rows)
        if v > 0.0 and det >= 1:
            sw = 6.0 * P.sec_x
            c.line(oval(X, Y + 8 * s_, 6 * s_, 9 * s_), lw * 0.7, '#9aa0a8')
            for k in range(3):
                a_ = math.radians(-20 + k * 22 + sw * 2)
                kx, ky = X + math.sin(a_) * 20 * s_, Y + 16 * s_ + math.cos(a_) * 20 * s_
                kp = poly([(X + math.sin(a_) * 8 * s_, Y + 16 * s_), (kx, ky)], False)
                c.line(kp, lw * 0.9, LINE); c.line(kp, lw * 0.5, ('#c9ad62', '#aab0b8', '#8d939b')[k])


def _robe_front(c, sp, B, rows, P, det, t):
    """Mom's bathrobe: shawl collar wrapping left over right into a V that shows the cream nightgown with a lace edge."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC, yW = B.y_sh, B.y_ch, B.y_wa
    gown, v = _surf_poly(B, rows, [(-34, yS - 26), (34, yS - 26), (10, yC + 70), (0, yC + 96), (-12, yC + 70)], dz=2)
    if v > 0.05:
        gp = smooth(gown, True, 0.25); c.fill(gp, cl['gown']); c.line(gp, lw * 0.5)
        if det >= 1:
            lace, _ = _surf_poly(B, rows, [(-30, yS - 14), (0, yS + 4), (30, yS - 14)], dz=3)
            c.line(smooth(lace, False), lw * 1.6, cl['gown_sh'], 160)
            c.line(smooth(lace, False), lw * 0.4, '#ffffff', 160)
    for side in (1, -1):                                         # the right panel first, the left overlaps it
        lp, v = _surf_poly(B, rows, [(side * 30, yS - 32), (side * (b['neck'] + 26), yS - 30), (side * (b['neck'] + 30), yS + 10),
                                     (side * 30, yC + 40), (-side * 6, yW + 4), (-side * 18, yW + 4), (side * 6, yC + 60),
                                     (side * 14, yS - 10)], dz=6 + (2 if side < 0 else 0))
        if v > -0.2:
            pp = smooth(lp, True, 0.35)
            c.fill(pp, cl['collar']); c.fill(_crescent(pp, -side * 9, 0), cl['top_sh'], 110)
            if det >= 1: c.texture(pp, 'fabric', 0.16, 0.6)
            c.line(pp, lw * 0.75)
    if det >= 1:
        for k in (-1, 1):
            pk, v = _surf_poly(B, rows, [(k * 46, yC + 70), (k * 92, yC + 70), (k * 92, yC + 112)], dz=2)
            if v > 0.1: c.line(poly(pk, False), lw * 0.4, cl['top_sh'], 200)


def _robe_skirt_front(c, sp, B, P, det, y_hem):
    cl = sp['cloth']
    X0, Y0, _, _ = B.p3(-8, B.y_wa + 20, 0, upper=True)
    X1, Y1, _, _ = B.p3(-22, y_hem, 0, upper=False)
    sw = P.sec_x * 10
    c.line(smooth([(X0, Y0), ((X0 + X1) / 2 - 4, (Y0 + Y1) / 2), (X1 + sw, Y1)], False), c.lw * 0.8)
    if det >= 1:
        for k in (-1, 1):                                       # patch pocket
            xp, yp, s_, _ = B.p3(k * 60, B.y_hip + 40, 30, upper=False)
            pk = rrect(xp - 30 * s_, yp - 24 * s_, 60 * s_, 54 * s_, 8 * s_)
            c.fill(pk, cl['top_sh'], 60); c.line(pk, c.lw * 0.5)
            c.line(poly([(xp - 30 * s_, yp - 14 * s_), (xp + 30 * s_, yp - 14 * s_)], False), c.lw * 0.35, cl['top_sh'], 220)


def _robe_belt(c, sp, B, rows, P, det, back, t):
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yB = B.y_wa + 12; w = b['wa'] + 6
    top, bot = [], []
    for k in range(11):
        x0 = -w + 2 * w * k / 10
        X, Y, v, s_ = B.surf(x0, yB - 12, 5, back, rows); top.append((X, Y))
        X, Y, v, s_ = B.surf(x0, yB + 12, 5, back, rows); bot.append((X, Y))
    band = smooth(top + bot[::-1], True, 0.4)
    c.fill(band, cl['belt']); c.line(band, lw * 0.6)
    if back: return
    X, Y, v, s_ = B.surf(w * 0.55, yB, 9, False, rows)                 # knot at her left with two hanging tails
    if v > 0.0:
        sw = 10.0 * P.sec_x
        for k, (dx, ln) in enumerate(((-6, 120), (10, 100))):
            tail = _tube([(X + dx * s_, Y + 6 * s_), (X + (dx + sw * 0.4) * s_, Y + ln * 0.5 * s_), (X + (dx + sw) * s_, Y + ln * s_)],
                         [20 * s_, 19 * s_, 18 * s_])
            c.fill(tail, cl['belt']); c.fill(_crescent(tail, -5, 0), cl['top_sh'], 120); c.line(tail, lw * 0.6)
        kn = oval(X, Y, 16 * s_, 13 * s_)
        c.fill(kn, cl['belt']); c.line(kn, lw * 0.6)
        if det >= 1: c.line(smooth([(X - 8 * s_, Y - 5 * s_), (X, Y + 2 * s_), (X + 7 * s_, Y - 6 * s_)], False), lw * 0.35, LINE, 160)


def _pajama_front(c, sp, B, rows, P, det, t):
    """Lily's pajama top: rounded collar with piping, a placket of four buttons."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    for side in (-1, 1):
        cc, v = _surf_poly(B, rows, [(side * 2, yS - 22), (side * (b['neck'] + 10), yS - 30), (side * (b['neck'] + 16), yS - 6),
                                     (side * 26, yS + 18), (side * 4, yS + 6)], dz=5)
        if v > -0.2:
            cp = smooth(cc, True, 0.7); c.fill(cp, cl['top_hi']); c.line(cp, lw * 1.2, cl['trim']); c.line(cp, lw * 0.5)
    pts, v = _surf_poly(B, rows, [(0, yS + 8), (0, B.y_hip - 20)])
    if v > 0.05:
        c.line(poly(pts, False), lw * 1.3, cl['trim'], 220)
        for k in range(4):
            X, Y, vv, s_ = B.surf(0, yC - 20 + k * 52, 3, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 5 * s_), '#f6f2ff'); c.line(oval(X, Y, 5 * s_), lw * 0.35)
    hem, v = _surf_poly(B, rows, [(-b['hip'] - 6, B.y_hip - 12), (b['hip'] + 6, B.y_hip - 12)], dz=2)
    if v > -0.2: c.line(poly(hem, False), lw * 1.2, cl['trim'], 220)


def _moon_print(c, B, rows, cl, back):
    """Small crescent moons and dots over the pajama top (fixed to the body surface)."""
    ys, ws, ds = rows
    ms, dots = [], []
    for k in range(16):
        x0 = (hash01(k, 51) * 2 - 1) * 0.86; y0 = ys[1] + (ys[-1] - ys[1]) * (0.08 + 0.86 * hash01(k, 52))
        w = float(np.interp(y0, ys, ws))
        X, Y, v, s_ = B.surf(x0 * w, y0, 2, back, rows)
        if v < 0.1: continue
        if k % 3 == 2: dots.append(oval(X, Y, 3.2 * s_))
        else: ms.append(minus(oval(X, Y, 9 * s_), oval(X + 4.5 * s_, Y - 3 * s_, 8 * s_)))
    if ms: c.fill(_multi(ms), cl['print_c'], 210)
    if dots: c.fill(_multi(dots), '#ffffff', 170)


def _plaid(c, path, cl, B, det):
    """Flannel check: wide dark bands and thin light lines both ways, clipped to the garment path."""
    bb = path.getBounds()
    with c.clip(path):
        x0, x1, y0, y1 = bb.left() - 40, bb.right() + 40, bb.top() - 40, bb.bottom() + 40
        dk = []; lt = []
        x = x0 - (x0 % 56.0)
        while x < x1:
            dk.append(rect(x, y0, 18, y1 - y0)); lt.append(poly([(x + 34, y0), (x + 34, y1)], False)); x += 56.0
        y = y0 - (y0 % 56.0)
        while y < y1:
            dk.append(rect(x0, y, x1 - x0, 18)); lt.append(poly([(x0, y + 34), (x1, y + 34)], False)); y += 56.0
        c.fill(_multi(dk), cl['check'], 85)
        if det >= 1: c.line(_multi(lt), c.lw * 0.35, cl['check_hi'], 130)


def _flannel_front(c, sp, B, rows, P, det, t):
    """Dad's flannel shirt (21 years ago): white tee at the open collar, placket, two flap pockets."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    ch = b['ch']; yS, yC = B.y_sh, B.y_ch
    vn, v = _surf_poly(B, rows, [(-26, yS - 26), (26, yS - 26), (0, yS + 30)], dz=3)
    if v > 0.0: c.fill(poly(vn), cl['tee']); c.line(poly(vn), lw * 0.4)
    pts, v = _surf_poly(B, rows, [(0, yS + 30), (0, B.y_hip - 20)])
    if v > 0.05:
        c.line(poly(pts, False), lw * 0.5, '#1c0e0b', 220)
        for k in range(4):
            X, Y, vv, s_ = B.surf(4, yC + 30 + k * 66, 2, False, rows)
            if vv > 0.1: c.fill(oval(X, Y, 3.6 * s_), '#e8dfcf'); c.line(oval(X, Y, 3.6 * s_), lw * 0.3)
    for side in (-1, 1):
        x0, x1 = side * 30, side * (ch * 0.7)
        y0, y1 = yC - 36, yC + 30
        pk, v = _surf_poly(B, rows, [(x0, y0 + 14), (x1, y0 + 14), (x1, y1), (x0, y1)])
        if v > 0.05:
            c.line(poly(pk), lw * 0.5, '#1c0e0b')
            fl, _ = _surf_poly(B, rows, [(x0 - side * 2, y0), (x1 + side * 2, y0), (x1 + side * 2, y0 + 16), (x0 - side * 2, y0 + 16)])
            c.fill(poly(fl), cl['top_sh']); c.line(poly(fl), lw * 0.55, '#1c0e0b')
        col_, v = _surf_poly(B, rows, [(side * 6, yS - 24), (side * (b['neck'] + 14), yS - 34), (side * (b['neck'] + 10), yS - 10), (side * 42, yS + 30)], dz=6)
        if v > -0.2: cp = poly(col_); c.fill(cp, cl['top']); c.line(cp, lw * 0.6)


# ---------------------------------------------------------------------------------------------- dummy film outfits
def _braid(c, pts, lw, cl, w=1.0):
    """Gold braid piping along a polyline (a gold line inside two dark edges)."""
    p_ = poly(pts, False) if len(pts) < 3 else smooth(pts, False)
    c.line(p_, lw * 1.9 * w, LINE); c.line(p_, lw * 1.2 * w, cl['braid']); c.line(p_, lw * 0.35 * w, '#fff0b8', 170)


def _brass_button(c, X, Y, r, cl, lw):
    c.fill(oval(X, Y, r), cl['brass']); c.radial(oval(X, Y, r), X - r * 0.3, Y - r * 0.35, r * 1.3, [(0, cl.get('brass_hi', '#fff0b8'), 255),
                                                                                                    (0.6, cl['brass'], 255), (1, cl['brass_sh'], 255)])
    c.line(oval(X, Y, r), lw * 0.35)


def _usher_front(c, sp, B, rows, P, det, t):
    """Mister Winks's usher jacket: mandarin collar with gold braid, two rows of brass buttons narrowing to the waist,
    gold piping down the front and round the short hem, little gold shoulder boards."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    yH = B.y_hip - 10
    col_, v = _surf_poly(B, rows, [(-b['neck'] - 13, yS - 40), (b['neck'] + 13, yS - 40), (b['neck'] + 17, yS - 16), (0, yS - 12), (-b['neck'] - 17, yS - 16)], dz=6)
    if v > -0.3:
        cp = smooth(col_, True, 0.25); c.fill(cp, cl['top_sh']); c.line(cp, lw * 0.6)
        tp, _ = _surf_poly(B, rows, [(-b['neck'] - 13, yS - 39), (b['neck'] + 13, yS - 39)], dz=7)
        _braid(c, tp, lw * 0.55, cl)
    pf, v = _surf_poly(B, rows, [(0, yS - 13), (0, yH)], dz=2)
    if v > 0.05:
        c.line(poly(pf, False), lw * 0.7, LINE, 230)
        _braid(c, pf, lw * 0.4, cl)
    hm_, v = _surf_poly(B, rows, [(-b['hip'] - 2, yH), (-b['hip'] * 0.5, yH + 2), (0, yH + 4), (b['hip'] * 0.5, yH + 2), (b['hip'] + 2, yH)], dz=2)
    if v > -0.3: _braid(c, hm_, lw * 0.5, cl)
    for k in range(4):                                       # 2 x 4 brass buttons, the rows narrowing to the waist
        yy = yS + 14 + k * (yH - yS - 40) / 3.0
        xx = 24.0 - 8.0 * k / 3.0
        for side in (-1, 1):
            X, Y, vv, s_ = B.surf(side * xx, yy, 6, False, rows)
            if vv > 0.12: _brass_button(c, X, Y, 6.2 * s_, cl, lw)
    for side in (-1, 1):                                     # shoulder boards
        bd, v = _surf_poly(B, rows, [(side * (b['neck'] + 6), yS - 22), (side * (b['sh'] - 6), yS - 14), (side * (b['sh'] - 4), yS + 2),
                                     (side * (b['neck'] + 8), yS - 6)], dz=8)
        if v > -0.2:
            bp = poly(bd); c.fill(bp, cl['braid']); c.line(bp, lw * 0.5)
            if det >= 1:
                fr = [poly([(bd[1][0] + (bd[2][0] - bd[1][0]) * u, bd[1][1] + (bd[2][1] - bd[1][1]) * u),
                            (bd[1][0] + (bd[2][0] - bd[1][0]) * u + side * 5, bd[1][1] + (bd[2][1] - bd[1][1]) * u + 2)], False) for u in (0.2, 0.5, 0.8)]
                c.line(_multi(fr), lw * 0.4, '#8a6a22')


def _usher_back(c, sp, B, rows, P, det, t):
    """The back of the jacket: the slot the operator's hand goes through (the hollow with the head stick), and the torn
    P.S. sliding out of it (pose.slot_paper)."""
    cl = sp['cloth']; lw = c.lw
    y0, y1 = B.y_sh + 6, B.y_ch + 52
    sl, v = _surf_poly(B, rows, [(-13, y0 + 12), (-7, y0), (7, y0), (13, y0 + 12), (12, y1), (-12, y1)], back=True, dz=2)
    if v > 0.0:
        sp_ = smooth(sl, True, 0.4)
        c.fill(sp_, '#0b0607'); c.line(sp_, lw * 0.8)
        if det >= 1:
            ed, _ = _surf_poly(B, rows, [(-17, y0 + 10), (-16, y1 + 4), (16, y1 + 4), (17, y0 + 10)], back=True, dz=2)
            c.line(smooth(ed, False), lw * 0.35, cl['top_hi'], 200)
        ppr = clamp(P.slot_paper)
        if ppr > 0.01:                                       # a folded corner of hospital notepaper slides out
            X0, Y0, _, s_ = B.surf(0, y0 + (y1 - y0) * 0.55, 3, True, rows)
            k = c.sub(X0, Y0, -24.0 + 10.0 * ppr, s_)
            pp = poly([(-16, 10), (14, 6), (20, 10 - 58 * ppr), (-10, 10 - 52 * ppr)])
            k.fill(pp, '#efe9d6'); k.line(pp, lw * 0.5 / s_)
            if det >= 1:
                k.line(_multi([poly([(-13 + 4 * j, 4 - 12 * j * ppr), (12 + 3 * j, 0 - 12 * j * ppr)], False) for j in range(1, 4) if 12 * j < 52 * ppr]),
                       lw * 0.25 / s_, '#8fb0d6', 200)
    hm_, v = _surf_poly(B, rows, [(-sp['body']['hip'], B.y_hip - 10), (sp['body']['hip'], B.y_hip - 10)], back=True, dz=2)
    if v > -0.3: _braid(c, hm_, lw * 0.5, cl)
    cs, v = _surf_poly(B, rows, [(0, B.y_sh - 10), (0, B.y_hip - 12)], back=True, dz=1)
    if v > 0.05: c.line(poly(cs, False), lw * 0.4, LINE, 150)


def _scarf(c, sp, B, rows, P, det, t):
    """Mom's chunky knit scarf: a thick loop round the neck and one long end down the front, fringed."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS = B.y_sh
    loop, v = _surf_poly(B, rows, [(-b['neck'] - 30, yS - 40), (0, yS - 30), (b['neck'] + 30, yS - 40), (b['neck'] + 40, yS - 6),
                                    (b['neck'] + 16, yS + 22), (0, yS + 26), (-b['neck'] - 16, yS + 22), (-b['neck'] - 40, yS - 6)], dz=16)
    sw = 6.0 * P.sec_x
    tail, v2 = _surf_poly(B, rows, [(10, yS + 4), (44, yS + 2), (48 + sw * 0.5, B.y_ch + 70), (52 + sw, B.y_wa + 30), (18 + sw, B.y_wa + 34),
                                     (14 + sw * 0.5, B.y_ch + 60)], dz=14)
    for pth, vv in ((tail, v2), (loop, v)):
        if vv < -0.4: continue
        q = smooth(pth, True, 0.45)
        c.fill(q, cl['scarf'])
        c.fill(_crescent(q, -10, 4), cl['scarf_sh'], 170)
        if det >= 1:
            c.texture(q, 'fabric', 0.22, 0.6)
            bb = q.getBounds()
            with c.clip(q):
                rib = [poly([(bb.left() + k * 9.0, bb.top()), (bb.left() + k * 9.0 + 3, bb.bottom())], False) for k in range(int(bb.width() / 9) + 2)]
                c.line(_multi(rib), lw * 0.35, cl['scarf_sh'], 150)
        c.line(q, lw * 0.8)
    if v2 > -0.4 and det >= 1:                               # fringe at the end of the tail
        a, b_ = tail[3], tail[4]
        fr = [poly([(a[0] + (b_[0] - a[0]) * u, a[1] + (b_[1] - a[1]) * u), (a[0] + (b_[0] - a[0]) * u + 1.5 * sw, a[1] + (b_[1] - a[1]) * u + 16)], False)
              for u in np.linspace(0.05, 0.95, 7)]
        c.line(_multi(fr), lw * 0.9, LINE); c.line(_multi(fr), lw * 0.5, cl['scarf_hi'])


def _longcoat_front(c, sp, B, rows, P, det, t):
    """Mom's long camel coat: notched lapels open on a plum sweater, double-breasted buttons, then the scarf."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    vn, v = _surf_poly(B, rows, [(-30, yS - 26), (30, yS - 26), (14, yC + 60), (-14, yC + 60)], dz=2)
    if v > 0.0: q = poly(vn); c.fill(q, cl['sweater']); c.fill(_crescent(q, -6, 0), mix(cl['sweater'], '#000000', 0.3), 120); c.line(q, lw * 0.4)
    for side in (-1, 1):
        lp, v = _surf_poly(B, rows, [(side * 24, yS - 30), (side * (b['neck'] + 30), yS - 34), (side * (b['neck'] + 34), yS - 2),
                                     (side * 64, yC - 4), (side * 52, yC + 14), (side * 14, yC + 64)], dz=6)
        if v > -0.2:
            lpp = poly(lp); c.fill(lpp, cl['top_hi'] if side < 0 else cl['top']); c.line(lpp, lw * 0.7)
    cl_, v = _surf_poly(B, rows, [(-12, yC + 64), (-12, B.y_hip - 10)], dz=3)
    if v > 0.05: c.line(poly(cl_, False), lw * 0.55)
    for k in range(2):
        for side in (-1, 1):
            X, Y, vv, s_ = B.surf(side * 30 - 6, yC + 96 + k * 66, 5, False, rows)
            if vv > 0.12: c.shape(oval(X, Y, 6.5 * s_), cl['button'], lw * 0.4)
    _scarf(c, sp, B, rows, P, det, t)


def _denim_front(c, sp, B, rows, P, det, t):
    """Your denim jacket open on a grey hoodie: pointed collar, chest pockets with flaps, copper buttons, the waistband,
    contrast stitching; the hoodie's drawstrings hang in the gap."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    gap, v = _surf_poly(B, rows, [(-34, yS - 24), (34, yS - 24), (26, B.y_hip - 4), (-26, B.y_hip - 4)], dz=2)
    if v > 0.0:
        q = poly(gap); c.fill(q, cl['hood']); c.fill(_crescent(q, -8, 0), cl['hood_sh'], 120)
        if det >= 1: c.texture(q, 'fabric', 0.14, 0.6)
        c.line(q, lw * 0.5)
        for side in (-1, 1):
            sw = 4 * P.sec_x
            st, vs = _surf_poly(B, rows, [(side * 12, yS - 4), (side * 13 + sw, yC + 20), (side * 11 + sw * 1.5, yC + 72)], dz=5)
            if vs > 0.0:
                sp_ = smooth(st, False); c.line(sp_, lw * 2.1, LINE); c.line(sp_, lw * 0.95, cl['string'])
    for side in (-1, 1):
        fr, v = _surf_poly(B, rows, [(side * 34, yS - 26), (side * 30, B.y_hip - 4)], dz=4)
        if v > -0.1:
            c.line(poly(fr, False), lw * 2.3, LINE); c.line(poly(fr, False), lw * 1.1, cl['top_hi'])
        x0, x1 = side * 40, side * (b['ch'] * 0.82)
        y0, y1 = yC - 30, yC + 26
        pk, v = _surf_poly(B, rows, [(x0, y0 + 12), (x1, y0 + 12), (x1, y1), ((x0 + x1) / 2, y1 + 8), (x0, y1)], dz=3)
        if v > 0.05:
            c.line(poly(pk), lw * 0.45)
            fl, _ = _surf_poly(B, rows, [(x0 - side * 2, y0), (x1 + side * 2, y0), (x1 + side * 2, y0 + 15), ((x0 + x1) / 2, y0 + 22), (x0 - side * 2, y0 + 15)], dz=4)
            c.fill(poly(fl), cl['top_sh']); c.line(poly(fl), lw * 0.5)
            X, Y, vv, s_ = B.surf((x0 + x1) / 2, y0 + 15, 6, False, rows)
            if vv > 0.1: c.shape(oval(X, Y, 4.0 * s_), cl['button'], lw * 0.35)
            if det >= 1:
                st_, _ = _surf_poly(B, rows, [(x0 + side * 3, y0 + 18), (x0 + side * 3, y1 - 2)], dz=3)
                c.line(poly(st_, False), lw * 0.25, '#d9a24a', 200)
        col_, v = _surf_poly(B, rows, [(side * 26, yS - 34), (side * (b['neck'] + 28), yS - 40), (side * (b['neck'] + 40), yS - 6), (side * 58, yS + 22),
                                       (side * 36, yS - 4)], dz=7)
        if v > -0.2: cp = poly(col_); c.fill(cp, cl['top']); c.fill(_crescent(cp, -side * 4, 3), cl['top_sh'], 120); c.line(cp, lw * 0.6)
        for k in range(2):
            X, Y, vv, s_ = B.surf(side * 30, yC + 80 + k * 50, 6, False, rows)
            if vv > 0.12: c.shape(oval(X, Y, 4.5 * s_), cl['button'], lw * 0.35)
    wb, v = _surf_poly(B, rows, [(-b['hip'] - 6, B.y_hip - 34), (-34, B.y_hip - 32), (-34, B.y_hip - 4), (-b['hip'] - 6, B.y_hip - 6)], dz=3)
    for side in (-1, 1):
        wb, v = _surf_poly(B, rows, [(side * (b['hip'] + 6), B.y_hip - 34), (side * 30, B.y_hip - 32), (side * 30, B.y_hip - 4), (side * (b['hip'] + 6), B.y_hip - 6)], dz=3)
        if v > -0.1: q = poly(wb); c.fill(q, cl['top_sh']); c.line(q, lw * 0.5)


def _cardi_m_front(c, sp, B, rows, P, det, t):
    """Grandpa's moss cardigan open on a cream checked shirt (collar points), leather buttons, ribbed hem, pockets."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    op, v = _surf_poly(B, rows, [(-28, yS - 28), (28, yS - 28), (18, B.y_hip - 18), (-18, B.y_hip - 18)], dz=2)
    if v > 0.05:
        q = smooth(op, True, 0.2); c.fill(q, cl['shirt'])
        if det >= 1:
            bb = q.getBounds()
            with c.clip(q):
                gl_ = [poly([(bb.left() + k * 13.0, bb.top()), (bb.left() + k * 13.0, bb.bottom())], False) for k in range(int(bb.width() / 13) + 2)]
                gl_ += [poly([(bb.left(), bb.top() + k * 13.0), (bb.right(), bb.top() + k * 13.0)], False) for k in range(int(bb.height() / 13) + 2)]
                c.line(_multi(gl_), lw * 0.35, cl['check'], 140)
        c.fill(_crescent(q, -8, 0), cl['shirt_sh'], 120); c.line(q, lw * 0.5)
        pl, _ = _surf_poly(B, rows, [(0, yS - 4), (0, B.y_hip - 18)], dz=3)
        c.line(poly(pl, False), lw * 0.35, LINE, 160)
        for side in (-1, 1):
            cc, _ = _surf_poly(B, rows, [(0, yS - 22), (side * 30, yS - 30), (side * 26, yS + 8), (side * 4, yS - 2)], dz=6)
            c.shape(smooth(cc, True, 0.5), cl['shirt'], lw * 0.55)
    for side in (-1, 1):
        ed, v = _surf_poly(B, rows, [(side * 28, yS - 28), (side * 20, B.y_hip - 18)], dz=4)
        if v > -0.2: c.line(poly(ed, False), lw * 2.6, LINE); c.line(poly(ed, False), lw * 1.4, cl['top_hi'])
        pk, v = _surf_poly(B, rows, [(side * 40, B.y_wa - 4), (side * 84, B.y_wa - 4), (side * 84, B.y_wa + 52), (side * 40, B.y_wa + 52)], dz=3)
        if v > 0.05: c.line(poly(pk), lw * 0.5)
    for k in range(4):
        X, Y, vv, s_ = B.surf(-24, yC + k * 58, 6, False, rows)
        if vv > 0.12: c.shape(oval(X, Y, 5.5 * s_), cl['button'], lw * 0.4)
    if det >= 1:
        for k in range(-6, 7):
            if abs(k) < 2: continue
            rb, v = _surf_poly(B, rows, [(k * 16, B.y_hip - 44), (k * 16, B.y_hip - 18)], dz=1)
            if v > 0.1: c.line(poly(rb, False), lw * 0.3, cl['top_sh'], 170)
        hem, v = _surf_poly(B, rows, [(-b['hip'] - 6, B.y_hip - 44), (b['hip'] + 6, B.y_hip - 44)], dz=1)
        if v > -0.2: c.line(poly(hem, False), lw * 0.4, LINE, 200)


def _gown_front(c, sp, B, rows, P, det, t):
    """Hospital gown: pale blue cotton, a little diamond print, a round neck with a tie, a snap shoulder."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS = B.y_sh
    nk, v = _surf_poly(B, rows, [(-b['neck'] - 12, yS - 30), (0, yS + 4), (b['neck'] + 12, yS - 30)], dz=3)
    if v > -0.2: c.line(smooth(nk, False), lw * 0.7)
    for side in (-1, 1):
        X, Y, vv, s_ = B.surf(side * (b['neck'] + 26), yS - 22, 4, False, rows)
        if vv > 0.1: c.shape(oval(X, Y, 3.5 * s_), '#e8eef4', lw * 0.3)


def _gown_print(c, B, rows, cl, det, path):
    if det < 1: return
    bb = path.getBounds()
    ds = []
    for i in range(int(bb.width() / 26) + 2):
        for j in range(int(bb.height() / 26) + 2):
            x = bb.left() + i * 26 + (13 if j % 2 else 0); y = bb.top() + j * 26
            ds.append(poly([(x, y - 4), (x + 3, y), (x, y + 4), (x - 3, y)]))
    with c.clip(path):
        c.fill(_multi(ds), cl['print_c'], 120)


def _suit70_front(c, sp, B, rows, P, det, t):
    """Young Walter's 1974 powder-blue suit: huge peak lapels, a cream shirt whose wide collar spreads over them, a wide
    tie, a pocket square, two buttons."""
    cl = sp['cloth']; b = sp['body']; lw = c.lw
    yS, yC = B.y_sh, B.y_ch
    vn, v = _surf_poly(B, rows, [(-34, yS - 26), (34, yS - 26), (8, yC + 98), (-8, yC + 98)], dz=2)
    if v > 0.0:
        q = poly(vn); c.fill(q, cl['shirt']); c.fill(_crescent(q, -6, 0), cl['shirt_sh'], 140); c.line(q, lw * 0.4)
        ti, _ = _surf_poly(B, rows, [(-9, yS - 18), (9, yS - 18), (16, yC + 70), (0, yC + 96), (-16, yC + 70)], dz=4)
        tp = poly(ti); c.fill(tp, cl['tie'])
        if det >= 1:
            with c.clip(tp):
                bb = tp.getBounds()
                c.line(_multi([poly([(bb.left() - 20, bb.top() + k * 22), (bb.right() + 20, bb.top() + k * 22 + 18)], False) for k in range(12)]),
                       lw * 1.4, cl['tie_hi'], 160)
        c.line(tp, lw * 0.5)
        kn, _ = _surf_poly(B, rows, [(-10, yS - 26), (10, yS - 26), (7, yS - 8), (-7, yS - 8)], dz=5)
        c.shape(poly(kn), cl['tie'], lw * 0.5)
    for side in (-1, 1):
        lp, v = _surf_poly(B, rows, [(side * 30, yS - 30), (side * (b['neck'] + 28), yS - 36), (side * (b['neck'] + 38), yS - 10),
                                     (side * 96, yS + 6), (side * 72, yC + 26), (side * 10, yC + 100)], dz=6)
        if v > -0.2:
            lpp = poly(lp); c.fill(lpp, cl['top_hi'] if side < 0 else cl['top']); c.fill(_crescent(lpp, -side * 5, 3), cl['top_sh'], 110)
            c.line(lpp, lw * 0.7)
        sc, v = _surf_poly(B, rows, [(side * 8, yS - 26), (side * (b['neck'] + 30), yS - 30), (side * (b['neck'] + 44), yS + 16), (side * 22, yS + 10)], dz=9)
        if v > -0.2: q = poly(sc); c.fill(q, cl['shirt']); c.line(q, lw * 0.55)
    X, Y, vv, s_ = B.surf(-62, yC + 6, 7, False, rows)
    if vv > 0.1:
        sq = smooth([(X - 11 * s_, Y + 4 * s_), (X - 6 * s_, Y - 9 * s_), (X + 1 * s_, Y - 2 * s_), (X + 7 * s_, Y - 8 * s_), (X + 11 * s_, Y + 4 * s_)], True, 0.5)
        c.shape(sq, cl['square'], lw * 0.4)
        pk, _ = _surf_poly(B, rows, [(-84, yC + 4), (-40, yC + 4)], dz=6); c.line(poly(pk, False), lw * 0.5)
    for k in range(2):
        X, Y, vv, s_ = B.surf(14, yC + 112 + k * 46, 6, False, rows)
        if vv > 0.12: c.shape(oval(X, Y, 5.5 * s_), mix(cl['top'], '#000000', 0.3), lw * 0.4)
    cl_, v = _surf_poly(B, rows, [(10, yC + 100), (12, B.y_hip - 6)], dz=3)
    if v > 0.05: c.line(poly(cl_, False), lw * 0.55)


# ---------------------------------------------------------------------------------------------- figure
def _limb_cols(sp):
    cl = sp['cloth']; o = sp['outfit']
    if o == 'police': return cl['shirt'], cl['shirt_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'hoodie': return cl['top'], cl['top_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'coat': return cl['coat'], cl['coat_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'courier': return cl['shirt'], cl['shirt_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o in ('pajamas', 'flannel'): return cl['top'], cl['top_sh'], cl['trousers'], cl['trousers_sh'], cl['shoes']
    if o == 'robe': return cl['top'], cl['top_sh'], cl['legs'], mix(cl['legs'], '#7a5a52', 0.35), cl['shoes']
    if 'trousers' in cl and o != 'cardigan':           # dummy film outfits: usher, longcoat, denim, cardi_m, gown, suit70
        return cl['top'], cl['top_sh'], cl['trousers'], cl.get('trousers_sh', mix(cl['trousers'], '#000000', 0.3)), cl.get('shoes', '#222')
    return cl['top'], cl['top_sh'], cl['legs'], mix(cl['legs'], '#000000', 0.25), cl['shoes']


def _arm_data(sp, B, P, side):
    """side +1 = character's left (screen right in front view). Returns 3D points S, E, W and hand info."""
    b = sp['body']
    pre = 'hl_' if side > 0 else 'hr_'
    g = lambda k: getattr(P, pre + k)   # noqa: E731
    sx = side * (b['sh'] - 17)
    S = np.array([sx, B.y_sh + 20, 0.0])
    swing = 0.0
    if B.walk > 0:
        swing = -60.0 * B.walk * math.cos(B.leg_phase(-side))
    H = S + np.array([side * g('out'), g('down'), g('fwd') + swing])
    shk = getattr(P, pre + 'shake', 0.0)
    if shk > 0.01:                                       # delivery: a shaking hand (fear), 9-13 Hz
        tt_ = P.t
        H = H + np.array([5.0 * shk * math.sin(tt_ * 61.0) + 3.0 * shk * noise1(tt_ * 13.0, 5 + side),
                          4.0 * shk * math.sin(tt_ * 73.0 + 1.3), 3.0 * shk * noise1(tt_ * 11.0, 9 + side)])
    pole = np.array([side * 0.75, 0.25, -0.65])
    kup = clamp((S[1] - H[1] - 10.0) / 60.0)            # v2.1: hand raised above the shoulder -> elbow down and out
    if kup > 0: pole = pole + (np.array([side * 0.7, 1.0, 0.25]) - pole) * kup
    ear = _ear_weight(P, side)
    if ear > 0:
        # v2.1 phone at the ear: wrist just below the ear so the phone covers ear and cheek; elbow forward and down
        hh = sp['hh']
        hw = float(np.interp(4.0, sp['head_ys'], sp['head_ws'])) * hh / 240.0
        hy = P.h_turn * PI / 2
        ex = side * (hw * 1.0 + 9.0) * math.cos(hy) + P.h_dx
        ey = B.yc - hh / 2 + 3.0 * hh / 240.0 + P.h_dy
        He = np.array([ex + side * 4.0, ey + 0.31 * hh, 26.0 - side * hw * 0.9 * math.sin(hy)])
        H = H + (He - H) * ear
        pole = pole + (np.array([side * 0.2, 1.0, 0.75]) - pole) * ear
    ak = b.get('arm_k', 1.0) * (1.0 + max(0.0, getattr(P, pre + 'stretch', 0.0)))
    E, Wp = _ik(S, H, 182.0 * ak, 166.0 * ak, pole)
    return S, E, Wp


def _ear_weight(P, side):
    """Phone-to-ear weight of one arm: pose.hl_ear/hr_ear, or 1 for the legacy film.phone_ear() pose (prop 'phone',
    hand raised close to the shoulder: up > 0.5, fwd < 120, down < 60)."""
    pre = 'hl_' if side > 0 else 'hr_'
    ear = getattr(P, pre + 'ear', 0.0)
    if getattr(P, pre + 'prop') == 'phone' and getattr(P, pre + 'up') > 0.5 and getattr(P, pre + 'fwd') < 120 \
            and getattr(P, pre + 'down') < 60:
        ear = max(ear, 1.0)
    return clamp(ear)


def _draw_arm(c, sp, B, P, side, det, t, skin, sh, sleeve, sleeve_sh, light):
    S, E, Wr = _arm_data(sp, B, P, side)
    b = sp['body']
    pts = [B.p3(*S), B.p3(*E), B.p3(*Wr)]
    P2 = [(p[0], p[1]) for p in pts]
    aw0, aw1 = b['arm']
    hz = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0)
    widths = [aw0 * pts[0][2], (aw0 + aw1) / 2 * max(pts[1][2], hz ** 0.5), aw1 * hz]
    o = sp['outfit']
    if o == 'robe': widths[2] *= 1.45; widths[1] *= 1.12          # wide terry sleeves
    if o == 'longcoat': widths[2] *= 1.25; widths[1] *= 1.08
    # extend the sleeve top into the shoulder
    tp = _tube([(P2[0][0] - side * 4, P2[0][1] - 14)] + P2, [widths[0] * 1.05] + widths)
    if o == 'gown':                                       # short sleeves: a bare, thin old arm below them
        c.fill(tp, skin); _cloth_shade(c, tp, sh, 120, 1.0, 8 * pts[0][2])
        if det >= 1:
            ex_, ey_ = P2[1]
            c.line(smooth([(ex_ - 8, ey_ - 4), (ex_, ey_ + 2), (ex_ + 7, ey_ - 3)], False), c.lw * 0.35, sp['skin_dp'], 160)
        c.line(tp, c.lw)
        mx_, my_ = (P2[0][0] + (P2[1][0] - P2[0][0]) * 0.55, P2[0][1] + (P2[1][1] - P2[0][1]) * 0.55)
        sl_ = _tube([(P2[0][0] - side * 4, P2[0][1] - 14), P2[0], (mx_, my_)], [widths[0] * 1.15, widths[0] * 1.2, widths[0] * 1.35])
        c.fill(sl_, sleeve); _cloth_shade(c, sl_, sleeve_sh, 160, 1.0, 10)
        _gown_print(c, None, None, sp['cloth'], det, sl_)
        c.line(sl_, c.lw)
    else:
        c.fill(tp, sleeve)
        _cloth_shade(c, tp, sleeve_sh, 170, 1.0, 12 * pts[0][2])
    if o == 'flannel':
        _plaid(c, tp, sp['cloth'], None, det)
    elif o in ('robe', 'usher', 'longcoat', 'cardi_m', 'denim') and det >= 1:
        with c.clip(tp): c.texture(tp, 'fabric', 0.12, 0.7)
    if o != 'gown': c.line(tp, c.lw)
    # elbow crease + cuff + patch
    if det >= 1:
        ex, ey = P2[1]
        dx, dy = P2[2][0] - P2[0][0], P2[2][1] - P2[0][1]
        c.line(smooth([(ex - 10, ey - 6), (ex, ey + 2), (ex + 9, ey - 4)], False), c.lw * 0.4, LINE, 150)
    wx, wy = P2[2]
    ang = math.degrees(math.atan2(P2[2][1] - P2[1][1], P2[2][0] - P2[1][0])) - 90
    cuffc = sleeve_sh if o != 'hoodie' else mix(sleeve, '#000000', 0.15)
    if o == 'pajamas': cuffc = sp['cloth']['trim']
    elif o == 'robe': cuffc = sp['cloth']['collar']
    elif o == 'suit70': cuffc = sp['cloth']['shirt']
    elif o == 'usher': cuffc = sp['cloth']['braid']
    elif o == 'cardi_m': cuffc = mix(sleeve, '#000000', 0.12)
    cuff = c.sub(wx, wy, ang, hz)
    cw = aw1 * (0.8 if o == 'robe' else (0.68 if o == 'longcoat' else 0.55))
    if o == 'gown':
        if side > 0:                                      # the hospital ID band on his left wrist
            bp = rrect(-aw1 * 0.5, -16, aw1, 9, 3); cuff.fill(bp, sp['cloth']['band']); cuff.line(bp, c.lw * 0.5 / hz)
    elif o == 'usher':                                    # gold braid cuff ring, then the white glove's flared gauntlet
        cpath = rrect(-cw * 1.05, -24, cw * 2.1, 10, 4)
        cuff.fill(cpath, cuffc); cuff.line(cpath, c.lw * 0.6 / hz)
        gaunt = poly([(-cw * 0.95, -15), (cw * 0.95, -15), (cw * 1.35, 6), (-cw * 1.35, 6)])
        cuff.fill(gaunt, sp['cloth']['glove']); cuff.fill(_crescent(gaunt, 3, 0), sp['cloth']['glove_sh'], 160); cuff.line(gaunt, c.lw * 0.7 / hz)
    else:
        cpath = rrect(-cw, -22, cw * 2, 22 if o != 'pajamas' else 14, 5)
        cuff.fill(cpath, cuffc); cuff.line(cpath, c.lw * 0.7 / hz)
    if o == 'hoodie' and det >= 1:
        cuff.line(_multi([poly([(k * cw / 4, -20), (k * cw / 4, -3)], False) for k in range(-3, 4)]), c.lw * 0.3 / hz, LINE, 140)
    if o == 'courier':
        # Nightline sleeve patch: navy shield, gold rim, crescent moon
        ux, uy = P2[0][0] + (P2[1][0] - P2[0][0]) * 0.28, P2[0][1] + (P2[1][1] - P2[0][1]) * 0.28
        if side * B.ct + 0.2 > 0 or abs(B.st) < 0.5:
            pc = c.sub(ux + side * 6 * pts[0][2] * abs(B.ct), uy, 0, pts[0][2] * (0.45 + 0.55 * abs(B.ct)), pts[0][2])
            cl = sp['cloth']
            pat = rrect(-15, -14, 30, 28, 8)
            pc.fill(pat, cl['patch']); pc.line(pat, c.lw * 0.8 / pts[0][2], cl['patch_rim']); pc.line(pat, c.lw * 0.3 / pts[0][2])
            if det >= 1: pc.fill(minus(oval(-1, 0, 8), oval(3, -3, 7)), cl['moon'])
    if o == 'police':
        # shoulder patch on the upper arm, outer side
        ux, uy = P2[0][0] + (P2[1][0] - P2[0][0]) * 0.28, P2[0][1] + (P2[1][1] - P2[0][1]) * 0.28
        vis = side * B.ct + 0.2 > 0 or abs(B.st) < 0.5
        if vis:
            pc = c.sub(ux + side * 6 * pts[0][2] * abs(B.ct), uy, 0, pts[0][2] * (0.45 + 0.55 * abs(B.ct)), pts[0][2])
            pat = smooth([(-15, -16), (15, -16), (17, 6), (0, 22), (-17, 6)], True, 0.5)
            cl = sp['cloth']
            pc.fill(pat, cl['patch']); pc.line(pat, c.lw * 0.9 / pts[0][2], cl['patch_rim'])
            pc.line(pat, c.lw * 0.35 / pts[0][2])
            if det >= 1:
                pc.fill(oval(0, -1, 6), cl['gold']); pc.fill(rect(-11, -13, 22, 4), '#e8e2d0', 220)
    # hand
    hand_shape = getattr(P, 'hl_shape' if side > 0 else 'hr_shape')
    prop = getattr(P, 'hl_prop' if side > 0 else 'hr_prop')
    up = getattr(P, 'hl_up' if side > 0 else 'hr_up')
    rot = getattr(P, 'hl_rot' if side > 0 else 'hr_rot')
    press = getattr(P, 'hl_press' if side > 0 else 'hr_press')
    ear = _ear_weight(P, side)
    if ear > 0.5:
        up, rot = 1.0, -side * 14.0 * B.ct
    hang = ang * (1 - up) + (180.0) * up + rot
    hs = clamp(900.0 / (900.0 - pts[2][3]), 0.6, 3.0) * getattr(P, 'hl_scale' if side > 0 else 'hr_scale', 1.0)
    ring = (sp['ring'] == side)
    if o == 'usher':                                      # white cotton gloves (the hands of a vent figure)
        skin, sh = sp['cloth']['glove'], sp['cloth']['glove_sh']
    if prop:
        if ear > 0.5 and prop == 'phone':
            # phone pressed to the ear: dark back of the phone along the cheek, the hand wrapped round it
            pc = c.sub(wx + math.sin(math.radians(-hang)) * 30 * hs, wy + math.cos(math.radians(hang)) * 30 * hs,
                       side * 17.0 * B.ct, hs * 1.0)
            _prop(pc, 'phone_back', det, t)
            _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
        elif prop == 'flashlight':                         # the torch lies in the fist, pointing along pose.torch_ang
            fx_ = wx + math.sin(math.radians(-hang)) * 34 * hs; fy_ = wy + math.cos(math.radians(hang)) * 34 * hs
            pc = c.sub(fx_, fy_, P.torch_ang, hs * 1.15 * sp['body'].get('hand', 1.0))
            _prop(pc, 'flashlight', det, t, P)
            _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
        else:
            pk_ = 1.15 * (1.28 if prop in ('tablet', 'tablet_back') else 1.0)
            off_ = 30 * (2.6 if prop in ('tablet', 'tablet_back') else 1.0)      # tablet: the fingers wrap its near edge
            pc = c.sub(wx + math.sin(math.radians(-hang)) * off_ * hs, wy + math.cos(math.radians(hang)) * off_ * hs, 0, hs * pk_)
            if prop in ('tablet', 'tablet_back'):
                _prop(pc, prop, det, t, P)
                _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
                return
            _prop(pc, prop, det, t)
            _draw_hand(c, sp, 'grip', wx, wy, hs, hang, side, det, skin, sh, ring, press, t)
    else:
        _draw_hand(c, sp, hand_shape, wx, wy, hs, hang, side, det, skin, sh, ring, press, t)


def _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec):
    b = sp['body']
    feet = sp.get('feet', 'shoes')
    order = []
    fl, tip = B.floor, B.tip
    for side in (-1, 1):
        hip = np.array([side * b['hip'] * 0.46, B.y_hip + 8, 0.0])
        fwd = B.foot_fwd(side) + B.sit * 210.0 * (1.0 - fl) + fl * (262.0 + 22.0 * side)
        lift = B.foot_lift(side)
        kn = B.kneel
        fwd += (150.0 if side > 0 else -230.0) * kn
        ank = np.array([side * (b['hip'] * 0.46 + 6 + 30 * P.stance + 24 * fl), -38.0 - lift - 34.0 * tip + (18.0 * kn if side < 0 else 0.0), fwd])
        hipw = hip.copy(); hipw[1] -= 0  # legs do not lean
        pole = np.array([0.08 * side + 0.3 * side * fl, -0.15 - 0.85 * fl, 1.0])
        K, A = _ik(hipw + np.array([0, B.bob, 0]), ank, 206.0, 180.0, pole)
        order.append((B.p3(*(hipw + np.array([0, 0, 0])), upper=False), B.p3(K[0], K[1] - B.bob, K[2], upper=False),
                      B.p3(A[0], A[1] - B.bob, A[2], upper=False), side, A))
    order.sort(key=lambda o: (o[0][3] + o[2][3]))
    lw0, lw1 = b['leg']
    cl = sp['cloth']
    for hp, kp, ap, side, A in order:
        P2 = [(hp[0], hp[1]), (kp[0], kp[1]), (ap[0], ap[1])]
        widths = [lw0 * hp[2], (lw0 + lw1) / 2 * kp[2], lw1 * ap[2]]
        tp = _tube(P2, widths)
        # shoe (convex hull of a box); boots are taller, bare feet / socks smaller and rounder
        ax, ay, az = A
        pts = []
        box_ = {'boots': ((-23, -24), (23, -24), (-25, 60), (25, 60), (-19, 74), (19, 74)),
                'bare': ((-17, -16), (17, -16), (-19, 52), (19, 52), (-14, 64), (14, 64)),
                'socks': ((-19, -20), (19, -20), (-21, 54), (21, 54), (-15, 66), (15, 66)),
                'slippers': ((-24, -24), (24, -24), (-26, 56), (26, 56), (-20, 70), (20, 70))}.get(
            feet, ((-22, -24), (22, -24), (-24, 58), (24, 58), (-18, 72), (18, 72)))
        top_h = {'boots': -46.0, 'bare': -22.0, 'socks': -26.0, 'slippers': -30.0}.get(feet, -30.0)
        for (hx, hz) in box_:
            for hy in (0.0, top_h if hz < 40 else (top_h * 0.72 if feet != 'shoes' else -22.0)):
                toe = 34.0 * tip if hz > 40 else 0.0              # tiptoe: heel up, toes stay on the floor
                X, Y, s, Z = B.p3(ax + hx, ay + 38 + hy - B.bob + toe, az + hz, upper=False)
                pts.append((X, Y))
        shoe = smooth(_hull(pts), True, 0.6)
        if feet in ('bare', 'socks') or sp['outfit'] == 'robe':     # ankles: skin / sock between hem and foot
            pass
        c.fill(tp, legc)
        _cloth_shade(c, tp, legsh, 160, 1.0, 10)
        if sp['outfit'] == 'pajamas' and det >= 1:
            with c.clip(tp):
                ms = []
                for k in range(6):
                    u = (k + 0.5) / 6.0
                    x_ = P2[0][0] + (P2[2][0] - P2[0][0]) * u + (hash01(k, 3 + side) - 0.5) * widths[1] * 0.6
                    y_ = P2[0][1] + (P2[2][1] - P2[0][1]) * u
                    ms.append(minus(oval(x_, y_, 7), oval(x_ + 3.5, y_ - 2.5, 6)))
                c.fill(_multi(ms), cl.get('print_c', '#f1e2a2'), 200)
        c.line(tp, c.lw)
        if det >= 1 and sp['outfit'] in ('police', 'coat', 'hoodie', 'courier', 'flannel'):
            c.line(smooth([((P2[0][0] + P2[1][0]) / 2, (P2[0][1] + P2[1][1]) / 2), P2[1], ((P2[1][0] + P2[2][0]) / 2, (P2[1][1] + P2[2][1]) / 2 + 10)], False),
                   c.lw * 0.35, LINE, 120)
        bb = shoe.getBounds()
        if feet == 'bare':
            skin = _skin_cols(sp, P, None)[0]
            c.fill(shoe, skin); c.fill(_crescent(shoe, 6, -4), sp['skin_sh'], 120); c.line(shoe, c.lw)
            if det >= 1:
                for k in range(4):
                    tx = bb.left() + bb.width() * (0.24 + 0.17 * k)
                    c.line(smooth([(tx, bb.bottom() - 9), (tx + 1.5, bb.bottom() - 3), (tx + 3, bb.bottom() - 1)], False), c.lw * 0.4, sp['skin_dp'], 170)
            continue
        if feet == 'socks':
            sc = cl.get('socks', '#8d8f96'); ssh = cl.get('socks_sh', mix(sc, '#000000', 0.3))
            c.fill(shoe, sc); c.fill(_crescent(shoe, 7, -4), ssh, 150)
            if det >= 1:
                c.texture(shoe, 'fabric', 0.18, 0.5)
                c.line(poly([(bb.left() + 5, bb.top() + 6), (bb.right() - 5, bb.top() + 6)], False), c.lw * 0.4, ssh, 200)
            c.line(shoe, c.lw)
            continue
        if feet == 'slippers':
            sc = cl.get('shoes', '#8e7f86'); ssh = cl.get('shoes_sh', mix(sc, '#000000', 0.3))
            c.fill(shoe, sc); c.fill(_crescent(shoe, 6, -5), ssh, 150)
            if det >= 1:
                c.texture(shoe, 'fabric', 0.3, 0.35)
                c.line(smooth([(bb.left() + 4, bb.top() + bb.height() * 0.45), (bb.centerX(), bb.top() + bb.height() * 0.3),
                               (bb.right() - 4, bb.top() + bb.height() * 0.45)], False), c.lw * 0.5, ssh, 220)
            c.line(shoe, c.lw)
            continue
        c.fill(shoe, shoec)
        c.glow(bb.centerX() - bb.width() * 0.18, bb.top() + bb.height() * 0.32, bb.width() * 0.3, bb.height() * 0.13, '#ffffff',
               70 if shoec in ('#0c0c0f', '#111113') else 40)
        if feet == 'boots':
            c.fill(rect(bb.left() - 2, bb.bottom() - 9, bb.width() + 4, 9), mix(shoec, '#000000', 0.45))
            if det >= 1:
                c.line(_multi([poly([(bb.centerX() - 8, bb.top() + 8 + k * 8), (bb.centerX() + 8, bb.top() + 12 + k * 8)], False)
                               for k in range(3)]), c.lw * 0.35, '#8a7a62', 220)
        c.line(shoe, c.lw)
        if sp['outfit'] == 'hoodie' and det >= 1:
            c.line(poly([(bb.left() + 4, bb.bottom() - 7), (bb.right() - 4, bb.bottom() - 7)], False), c.lw * 0.5, '#8a8478')


def _pelvis(c, sp, B, rows, legc, legsh, det):
    b = sp['body']
    ys, ws, ds = rows
    yh = B.y_hip
    Lp = []
    for x0, y0 in ((-b['hip'], yh - 30), (b['hip'], yh - 30)):
        X, Y, v, s = B.surf(x0 * 0.999, y0, 0, False, rows); Lp.append((X, Y))
    X0, Y0, _, s0 = B.p3(0, B.y_cr + 12, 0, upper=False)
    hw = math.sqrt((b['hip'] * B.ct) ** 2 + (b['hip'] * 0.62 * B.st) ** 2)
    pel = smooth([(X0 - hw * s0, yh - 30 + B.bob), (X0 + hw * s0, yh - 30 + B.bob), (X0 + hw * 0.98 * s0, yh + 14 + B.bob),
                  (X0 + 10, B.y_cr + 26 + B.bob), (X0 - 10, B.y_cr + 26 + B.bob), (X0 - hw * 0.98 * s0, yh + 14 + B.bob)], True, 0.4)
    c.fill(pel, legc)
    _cloth_shade(c, pel, legsh, 140, 1.0, 18)
    if det >= 1 and abs(B.st) < 0.7:
        c.line(smooth([(X0 + 4, yh - 20 + B.bob), (X0 + 6, B.y_cr + 6 + B.bob), (X0 - 2, B.y_cr + 20 + B.bob)], False), c.lw * 0.4, LINE, 170)


def _skirt(c, sp, B, det, y_top, y_hem, w_top, w_hem, colr, colsh, slit=False, t=0.0, P=None):
    X0, Y0, s0, _ = B.p3(0, y_top, 0, upper=True)
    X1, Y1, s1, _ = B.p3(0, y_hem, 0, upper=False)
    ht = math.sqrt((w_top * B.ct) ** 2 + (w_top * 0.62 * B.st) ** 2) * s0
    hh_ = math.sqrt((w_hem * B.ct) ** 2 + (w_hem * 0.66 * B.st) ** 2) * s1
    sw = (P.sec_x * 10 if P else 0) - B.st * 8 * B.walk
    pts = [(X0 - ht, Y0), (X0 + ht, Y0), (X1 + hh_ + sw, Y1), (X1 + hh_ * 0.5 + sw, Y1 + 6), (X1 - hh_ * 0.5 + sw, Y1 + 6), (X1 - hh_ + sw, Y1)]
    p = smooth(pts, True, 0.35)
    c.fill(p, colr)
    _cloth_shade(c, p, colsh, 150, 1.0, 24)
    if det >= 1:
        c.texture(p, 'fabric', 0.12, 0.6)
        for k in (-0.5, 0.0, 0.5):
            c.line(poly([(X0 + k * ht * 0.6, Y0 + 40), (X1 + k * hh_ * 0.8 + sw, Y1 + 2)], False), c.lw * 0.35, LINE, 110)
    c.line(p, c.lw)
    return p


def _torso_path(B, rows):
    ys, ws, ds = rows
    L, R = B.rows(ys, ws, ds)
    neck_l, neck_r = L[0], R[0]
    pts = R + L[::-1]
    return smooth(pts, True, 0.85), L, R


def _figure(c, who, P, det, t, light=None, upper_only=False):
    """Whole character in body units on Ctx c (feet at y=0, crown at y=-1000)."""
    sp = CAST[who]
    B = Body(sp, P)
    skin, skin_sh, _ = _skin_cols(sp, P, light)
    sleeve, sleeve_sh, legc, legsh, shoec = _limb_cols(sp)
    rows = _torso_rows(sp, B)
    cl = sp['cloth']; o = sp['outfit']
    # arms: which are behind the torso
    arm_z = {}
    for side in (-1, 1):
        S, E, Wr = _arm_data(sp, B, P, side)
        zs = B.p3(*S)[3]; zh = B.p3(*Wr)[3]
        arm_z[side] = (zs, zh)
    behind = [s for s in (-1, 1) if arm_z[s][0] < -20 and arm_z[s][1] < 40]
    front = [s for s in (-1, 1) if s not in behind]
    front.sort(key=lambda s: arm_z[s][1])
    back_view = B.ct < -0.15
    # hood behind the neck
    for side in behind: _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    floor_late = B.floor > 0.5 and not upper_only          # sitting on the floor: knees up in front of the torso
    if not upper_only:
        if o not in ('cardigan', 'robe', 'gown'):
            if not floor_late: _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec)
            _pelvis(c, sp, B, rows, legc, legsh, det)
        elif not floor_late:
            _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec)
    elif o not in ('coat', 'robe', 'longcoat', 'gown'):
        _pelvis(c, sp, B, rows, legc, legsh, det)
    torso, L, R = _torso_path(B, rows)
    top = {'police': cl.get('shirt'), 'hoodie': cl.get('top'), 'coat': cl.get('coat'), 'cardigan': cl.get('top'),
           'courier': cl.get('shirt')}.get(o, cl.get('top'))
    topsh = {'police': cl.get('shirt_sh'), 'hoodie': cl.get('top_sh'), 'coat': cl.get('coat_sh'), 'cardigan': cl.get('top_sh'),
             'courier': cl.get('shirt_sh')}.get(o, cl.get('top_sh'))
    tophi = {'police': cl.get('shirt_hi'), 'hoodie': cl.get('top_hi'), 'coat': cl.get('coat_hi'), 'cardigan': cl.get('top_hi'),
             'courier': cl.get('shirt_hi')}.get(o, cl.get('top_hi'))
    if o == 'cardigan' and not upper_only:
        _skirt(c, sp, B, det, B.y_wa + 10, -175, sp['body']['hip'] * 0.98, sp['body']['hip'] * 1.12, cl['skirt'], cl['skirt_sh'], t=t, P=P)
    if o == 'robe' and not upper_only:
        _skirt(c, sp, B, det, B.y_wa + 10, -205 + 150 * B.floor, sp['body']['hip'] * 1.04, sp['body']['hip'] * 1.2 + 60 * B.floor,
               cl['top'], cl['top_sh'], t=t, P=P)
        _robe_skirt_front(c, sp, B, P, det, -205 + 150 * B.floor)
    if o == 'gown' and not upper_only:                    # hospital gown to the knee (sitting: over the thighs)
        gs = _skirt(c, sp, B, det, B.y_wa + 10, -300 + 120 * B.sit, sp['body']['hip'] * 1.08, sp['body']['hip'] * 1.18 + 50 * B.sit,
                    cl['top'], cl['top_sh'], t=t, P=P)
        _gown_print(c, B, rows, cl, det, gs)
    # neck (behind collar)
    nb = B.p3(0, B.y_sh - 34, 0); nt = B.p3(0, B.yc - 30, 0)
    nw = sp['body']['neck']
    neck = _tube([(nb[0], nb[1]), (nt[0], nt[1])], [nw * 2 * nb[2], nw * 1.9 * nt[2]])
    if o in ('hoodie', 'denim'):
        hood = smooth([(nb[0] - (nw + 46) * nb[2], nb[1] + 8), (nb[0] - (nw + 30) * nb[2], nb[1] - 42), (nb[0], nb[1] - 56 - 10 * (B.ct < 0)),
                       (nb[0] + (nw + 30) * nb[2], nb[1] - 42), (nb[0] + (nw + 46) * nb[2], nb[1] + 8)], True, 0.8)
        c.shape(hood, cl['hood_sh'] if o == 'denim' else cl['top_sh'])
    c.fill(neck, skin)
    with c.clip(neck):
        c.fill(moved_path(neck, 0, -30), skin_sh, 0)
        c.grad(neck, 0, nt[1] - 10, 0, nb[1], [(0, mix(skin_sh, '#000000', 0.2), 255), (0.6, skin_sh, 160), (1, skin, 0)])
    c.line(neck, c.lw)
    # torso
    if o == 'coat':
        if not upper_only:
            _skirt(c, sp, B, det, B.y_wa, -236, sp['body']['wa'] + 8, sp['body']['hip'] * 1.22, cl['coat'], cl['coat_sh'], t=t, P=P)
    if o == 'longcoat' and not upper_only:               # mom's coat to the knee (open a little at the front)
        cs = _skirt(c, sp, B, det, B.y_wa, -250 + 120 * B.sit, sp['body']['wa'] + 10, sp['body']['hip'] * 1.3 + 40 * B.sit,
                    cl['top'], cl['top_sh'], t=t, P=P)
        if not back_view and det >= 1:
            X0, Y0, _, _ = B.p3(0, B.y_wa, 0); X1, Y1, _, _ = B.p3(0, -250 + 120 * B.sit, 0, upper=False)
            for side in (-1, 1):
                fx = X0 + side * 34 * B.ct
                c.line(poly([(fx - 12, Y0 + 30), (X1 - 12 + side * 6, Y1)], False), c.lw * 0.6)
                c.line(smooth([(X0 + side * 62 * B.ct, Y0 + 70), (X0 + side * 112 * B.ct, Y0 + 66)], False), c.lw * 0.5)
    c.fill(torso, top)
    c.grad(torso, L[3][0] - 10, 0, R[3][0] + 10, 0, [(0, tophi, 90), (0.35, top, 0), (0.7, topsh, 60), (1, topsh, 200)])
    with c.clip(torso):
        c.grad(rect(-400, B.y_wa - 10, 800, 300), 0, B.y_wa - 60, 0, B.y_hip, [(0, topsh, 0), (1, topsh, 140)])
        if det >= 1: c.texture(torso, 'fabric' if o in ('robe', 'pajamas', 'flannel', 'usher', 'longcoat', 'cardi_m', 'gown') else 'grunge',
                               0.1 if o == 'robe' else 0.07, 0.7)
        if o == 'gown': _gown_print(c, B, rows, cl, det, torso)
        if o == 'denim' and det >= 1:                     # denim twill
            c.texture(torso, 'fabric', 0.1, 0.35)
        if o == 'flannel' and det >= 0: _plaid(c, torso, cl, B, det)
        if o == 'pajamas' and det >= 1: _moon_print(c, B, rows, cl, back_view)
        # armpit creases + blousing
        if det >= 1:
            for side in (-1, 1):
                for k in range(2):
                    p0 = B.surf(side * (sp['body']['ch'] * (0.78 - k * 0.1)), B.y_ch - 10 + k * 24, 1, back_view, rows)
                    p1 = B.surf(side * (sp['body']['ch'] * (0.5 - k * 0.08)), B.y_ch + 34 + k * 30, 1, back_view, rows)
                    c.line(smooth([(p0[0], p0[1]), ((p0[0] + p1[0]) / 2 + side * 4, (p0[1] + p1[1]) / 2), (p1[0], p1[1])], False), c.lw * 0.42, LINE, 130)
            if o in ('police', 'courier'):
                for k in range(-4, 5):
                    p0 = B.surf(k * 22, B.y_belt - 50, 1, back_view, rows); p1 = B.surf(k * 23 + 3, B.y_belt - 18, 1, back_view, rows)
                    if p0[2] > 0.1: c.line(smooth([(p0[0], p0[1]), (p1[0] + 2, (p0[1] + p1[1]) / 2), (p1[0], p1[1])], False), c.lw * 0.35, LINE, 110)
        if light and light.get('rim'):
            rs = light.get('side', 1)
            c.fill(_crescent(torso, -rs * 9, 0), light['rim'], light.get('rim_a', 70) * 0.8)
    c.line(torso, c.lw)
    if not back_view:
        if o == 'police': _police_front(c, sp, B, rows, P, det, t)
        elif o == 'hoodie': _hoodie_front(c, sp, B, rows, P, det, t)
        elif o == 'coat': _coat_front(c, sp, B, rows, P, det, t)
        elif o == 'cardigan': _cardigan_front(c, sp, B, rows, P, det, t)
        elif o == 'courier': _courier_front(c, sp, B, rows, P, det, t)
        elif o == 'robe': _robe_front(c, sp, B, rows, P, det, t)
        elif o == 'pajamas': _pajama_front(c, sp, B, rows, P, det, t)
        elif o == 'flannel': _flannel_front(c, sp, B, rows, P, det, t)
        elif o == 'usher': _usher_front(c, sp, B, rows, P, det, t)
        elif o == 'longcoat': _longcoat_front(c, sp, B, rows, P, det, t)
        elif o == 'denim': _denim_front(c, sp, B, rows, P, det, t)
        elif o == 'cardi_m': _cardi_m_front(c, sp, B, rows, P, det, t)
        elif o == 'gown': _gown_front(c, sp, B, rows, P, det, t)
        elif o == 'suit70': _suit70_front(c, sp, B, rows, P, det, t)
    elif o == 'usher':
        _usher_back(c, sp, B, rows, P, det, t)
    else:
        yy = B.y_sh + 30
        sm, v = _surf_poly(B, rows, [(-sp['body']['sh'] * 0.8, yy), (0, yy + 12), (sp['body']['sh'] * 0.8, yy)], back=True, dz=1)
        c.line(smooth(sm, False), c.lw * 0.4, LINE, 140)
    if o == 'police': _police_belt(c, sp, B, rows, P, det, back_view)
    elif o == 'courier': _courier_belt(c, sp, B, rows, P, det, back_view)
    elif o == 'robe': _robe_belt(c, sp, B, rows, P, det, back_view, t)
    if floor_late: _draw_legs(c, sp, B, P, det, t, legc, legsh, shoec)
    # head
    pv = B.p3(0, B.yc - 22 + P.h_dy, 0)
    hs = sp['hh'] / 240.0 * pv[2] * P.h_scale
    head_rot = P.tilt + P.h_tilt
    arm_ = (sp['hh'] / 2 - 22) * pv[2] * P.h_scale
    ra = math.radians(head_rot)
    hx = pv[0] + P.h_dx + math.sin(ra) * arm_
    hy = pv[1] - math.cos(ra) * arm_
    hc = c.sub(hx, hy, head_rot, hs)
    yaw = (P.turn + P.h_turn) * PI / 2
    draw_head_local(hc, who, P, yaw, P.h_nod * 0.6 + 0.0, det, t, light, sp)
    for side in front: _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)
    return B


# ====================================================================================================== public drawing
def _as_pose(pose):
    if pose is None: return Pose()
    if isinstance(pose, str): return Pose(pose)
    if isinstance(pose, dict): return Pose(**pose)
    return pose


def draw(pen, who, x, y_feet, height, pose=None, detail=None, light=None, t=None, aim=None):
    """Full body. height = feet-to-crown in design px. pose.dx (design px) shifts the figure (walks).
    aim=(x, y): as pose.approach goes 0 -> 1 the figure slides so its head reaches that point (put the lens axis
    here for lean_in toward a doorbell / peephole; pair it with Layer depth=acting.depth(base))."""
    P = _as_pose(pose); t = P.t if t is None else t
    s = height / 1000.0
    sp = CAST[who]
    head_px = sp['hh'] * s
    det = _auto_detail(pen, head_px) if detail is None else detail
    ox = oy = 0.0
    if aim is not None and P.approach > 0:
        k = ease_in_out(clamp(P.approach))
        ox = (aim[0] - (x + P.dx)) * k
        oy = (aim[1] - (y_feet + P.dy - (1000.0 - sp['hh'] / 2) * s)) * k
    oy += clamp(getattr(P, 'perch', 0.0)) * clamp(P.sit) * 222.0 * s       # perch: y_feet = the surface he sits on
    c = Ctx(pen, skia.Matrix(), _lw_for(head_px)).sub(x + P.dx + ox, y_feet + P.dy + oy, 0.0, s)
    rec = getattr(P, 'recline', 0.0)
    if abs(rec) > 1e-3:                   # recline (deg): the whole figure tips about its hips (cradled in someone's arms)
        hy = -422.0 + 170.0 * clamp(P.sit)
        c = c.sub(0.0, hy, rec).sub(0.0, -hy, 0.0)
    lie = getattr(P, 'lie', 0.0)
    if abs(lie) > 1e-3:                   # lying down: rotate about the hips, rest on the floor (lie 1 face down, -1 face up)
        a_ = math.radians(90.0 * lie)
        T_ = 422.0 * (1.0 - abs(lie)) + 62.0 * abs(lie)
        c = c.sub(-422.0 * math.sin(a_), -T_ + 422.0 * math.cos(a_), math.degrees(a_))
    return _figure(c, who, P, det, t, light)


def draw_bust(pen, who, cx, cy, scale=1.0, pose=None, detail=None, light=None, t=None):
    """Head-and-shoulders close-up. scale 1 = head 600 design px tall; (cx, cy) = rest head centre."""
    P = _as_pose(pose); t = P.t if t is None else t
    sp = CAST[who]
    k = 1.0 + 1.1 * clamp(P.approach)
    head_px = 600.0 * scale * k
    s = head_px / sp['hh']
    c0 = Ctx(pen, skia.Matrix(), _lw_for(head_px))
    yh = -1000 + sp['hh'] / 2
    ty = cy + 60.0 * scale * clamp(P.approach)
    ox_ = oy_ = 0.0
    if P.sit + P.crouch + getattr(P, 'floor', 0.0) + getattr(P, 'kneel', 0.0) > 0.03 or abs(P.lean) > 0.05 or P.hunch > 0.05:
        Q = P.copy(); Q.sit = Q.crouch = Q.lean = Q.hunch = 0.0; Q.floor = Q.kneel = Q.tiptoe = 0.0
        B1, B0 = Body(sp, P), Body(sp, Q)                 # dummy film: a seated / kneeling bust keeps its face in frame
        a1, b1 = B1.p3(0, B1.yc - 22, 0)[:2]; a0, b0 = B0.p3(0, B0.yc - 22, 0)[:2]
        ox_, oy_ = (a0 - a1) * s, (b0 - b1) * s
    c = c0.sub(cx + ox_, ty - yh * s + oy_, 0.0, s)
    det = _auto_detail(pen, head_px) if detail is None else detail
    return _figure(c, who, P, det, t, light, upper_only=True)


def draw_arm(pen, who, side=1, pose=None, x=None, y_feet=None, height=None, cx=None, cy=None, scale=None, light=None,
             detail=None, t=None):
    """Draw ONE arm (sleeve, cuff, hand and any held prop) exactly where draw() (x, y_feet, height) or draw_bust() (cx, cy,
    scale) puts it. For a figure clipped by a window frame, a sill or a car door whose reaching arm must come over the
    edge: draw the figure clipped, the sill, then draw_arm on top (Lily leaning out of her window to the tablet)."""
    P = _as_pose(pose); t = P.t if t is None else t
    sp = CAST[who]
    if cx is not None:
        k = 1.0 + 1.1 * clamp(P.approach)
        head_px = 600.0 * (scale or 1.0) * k
        s_ = head_px / sp['hh']
        c = Ctx(pen, skia.Matrix(), _lw_for(head_px)).sub(cx, cy + 60.0 * (scale or 1.0) * clamp(P.approach) - (-1000 + sp['hh'] / 2) * s_, 0.0, s_)
    else:
        s_ = height / 1000.0; head_px = sp['hh'] * s_
        py = clamp(getattr(P, 'perch', 0.0)) * clamp(P.sit) * 222.0 * s_          # perched: as draw() places him
        c = Ctx(pen, skia.Matrix(), _lw_for(head_px)).sub(x + P.dx, y_feet + P.dy + py, 0.0, s_)
    det = _auto_detail(pen, head_px) if detail is None else detail
    B = Body(sp, P)
    skin, skin_sh, _ = _skin_cols(sp, P, light)
    sleeve, sleeve_sh = _limb_cols(sp)[:2]
    _draw_arm(c, sp, B, P, side, det, t, skin, skin_sh, sleeve, sleeve_sh, light)


def hand_pos(who, pose, side=1, x=None, y_feet=None, height=None, cx=None, cy=None, scale=None):
    """Design-space (wrist, fingertip) of one hand as draw() (x, y_feet, height) or draw_bust() (cx, cy, scale) would place
    it (no aim / approach slide). Use it to pin a prop or a second character to a hand, e.g. the tablet under Lily's
    finger, or mom's wrist for 'you' to catch. side +1 = character's left hand."""
    P = _as_pose(pose); sp = CAST[who]
    B = Body(sp, P)
    S, E, W = _arm_data(sp, B, P, side)
    wx, wy, ws, _ = B.p3(*W)
    ex, ey, _, _ = B.p3(*E)
    L = math.hypot(wx - ex, wy - ey) or 1.0
    fx, fy = wx + (wx - ex) / L * 60.0 * ws, wy + (wy - ey) / L * 60.0 * ws
    up = getattr(P, ('hl_' if side > 0 else 'hr_') + 'up')
    if up > 0.5: fx, fy = wx, wy - 60.0 * ws
    if cx is not None:
        k = 1.0 + 1.1 * clamp(P.approach)
        s = 600.0 * (scale or 1.0) * k / sp['hh']
        ty = cy + 60.0 * (scale or 1.0) * clamp(P.approach)
        ox, oy = cx, ty - (-1000 + sp['hh'] / 2) * s
    else:
        s = height / 1000.0
        ox, oy = x + P.dx, y_feet + P.dy
    return (ox + wx * s, oy + wy * s), (ox + fx * s, oy + fy * s)


def draw_head(pen, who, cx, cy, size, pose=None, detail=2, light=None, t=None):
    """Head only. size = crown-to-chin height in design px, (cx, cy) = head centre."""
    P = _as_pose(pose); t = P.t if t is None else t
    s = size / 240.0
    c = Ctx(pen, skia.Matrix(), _lw_for(size)).sub(cx, cy, P.h_tilt, s)
    yaw = (P.turn + P.h_turn) * PI / 2; pitch = P.h_nod * 0.6
    return draw_head_local(c, who, P, yaw, pitch, detail, t, light)


def _place(who, P, x=None, y_feet=None, height=None, cx=None, cy=None, scale=None):
    """(origin x, origin y, design px per body unit) of a figure drawn by draw() / draw_bust() (perch included)."""
    sp = CAST[who]
    if cx is not None:
        k = 1.0 + 1.1 * clamp(P.approach)
        s = 600.0 * (scale or 1.0) * k / sp['hh']
        return cx, cy + 60.0 * (scale or 1.0) * clamp(P.approach) - (-1000 + sp['hh'] / 2) * s, s
    s = height / 1000.0
    return x + P.dx, y_feet + P.dy + clamp(getattr(P, 'perch', 0.0)) * clamp(P.sit) * 222.0 * s, s


def torch_pos(who, pose, side=1, x=None, y_feet=None, height=None, cx=None, cy=None, scale=None):
    """Design-space (lens x, lens y, beam angle deg) of the usher's flashlight in a hand (pose.torch_ang: 0 = up)."""
    P = _as_pose(pose); sp = CAST[who]
    B = Body(sp, P)
    S, E, W = _arm_data(sp, B, P, side)
    wx, wy, ws, wz = B.p3(*W); ex, ey, _, _ = B.p3(*E)
    ang = math.degrees(math.atan2(wy - ey, wx - ex)) - 90
    up = getattr(P, ('hl_' if side > 0 else 'hr_') + 'up')
    hang = ang * (1 - up) + 180.0 * up + getattr(P, ('hl_' if side > 0 else 'hr_') + 'rot')
    hs = clamp(900.0 / (900.0 - wz), 0.6, 3.0)
    fx = wx + math.sin(math.radians(-hang)) * 34 * hs; fy = wy + math.cos(math.radians(hang)) * 34 * hs
    k = hs * 1.15 * sp['body'].get('hand', 1.0)
    a = math.radians(P.torch_ang)
    lx, ly = fx + math.sin(a) * 38 * k, fy - math.cos(a) * 38 * k
    ox, oy, s = _place(who, P, x, y_feet, height, cx, cy, scale)
    return ox + lx * s, oy + ly * s, P.torch_ang


def draw_torch_beam(pen, x, y, ang, length=900.0, spread=13.0, a=1.0, t=0.0, colr='#fff1c8', lens=0.0):
    """The flashlight's beam from its lens at (x, y) (design px) toward ang (deg, 0 = up): a soft cone fading out with
    distance plus the hot glow at the lens; lens 0..1 = it points into the camera (a round glare with a star instead of
    a cone). Draw it on a light layer above the set (and, for the glare, above the figure)."""
    if a <= 0.01: return
    flick = 0.94 + 0.06 * noise1(t * 7.0, 3)
    if lens > 0.01:
        pen.glow(x, y, 240 * lens, colr, 190 * a * lens * flick)
        pen.glow(x, y, 70, '#ffffff', 255 * a * lens)
        for k, ln in ((0, 260), (90, 200), (45, 90), (135, 90)):
            r_ = math.radians(k)
            pen.line(poly([(x - math.cos(r_) * ln * lens, y - math.sin(r_) * ln * lens), (x + math.cos(r_) * ln * lens, y + math.sin(r_) * ln * lens)], False),
                     5.0, '#ffffff', 110 * a * lens)
        if lens > 0.95: return
    r = math.radians(ang)
    dx, dy = math.sin(r), -math.cos(r)
    w = math.tan(math.radians(spread)) * length
    ex, ey = x + dx * length, y + dy * length
    cone = poly([(x - dy * 6, y + dx * 6), (ex - dy * w, ey + dx * w), (ex + dy * w, ey - dx * w), (x + dy * 6, y - dx * 6)])
    pen.linear(cone, x, y, ex, ey, [(0, colr, int(150 * a * flick)), (0.35, colr, int(70 * a * flick)), (1, colr, 0)])
    pen.glow(x, y, 60, colr, 220 * a * flick)


def lap_anchor(who, pose, side=1, x=None, y_feet=None, height=None):
    """Design-space (x, y) of the top of `who`'s thigh at the knee on `side` (+1 the character's left), where a figure
    sitting on that knee rests (draw it there with perch on). Works for any view and sit amount."""
    P = _as_pose(pose); sp = CAST[who]; b = sp['body']
    B = Body(sp, P)
    hip = np.array([side * b['hip'] * 0.46, B.y_hip + 8, 0.0])
    fwd = B.sit * 210.0
    ank = np.array([side * (b['hip'] * 0.46 + 6 + 30 * P.stance), -38.0, fwd])
    K, A = _ik(hip + np.array([0, B.bob, 0]), ank, 206.0, 180.0, np.array([0.08 * side, -0.15, 1.0]))
    mid = hip + (K - np.array([0, B.bob, 0]) - hip) * 0.72
    X, Y, sc, _ = B.p3(mid[0], mid[1] - b['leg'][0] * 0.55, mid[2], upper=False)
    ox, oy, s = _place(who, P, x, y_feet, height)
    return ox + X * s, oy + Y * s


DUMMY_M = 0.85                                     # Mister Winks's length (m) for scaling him against people


def draw_lap(pen, who, x, y_feet, height, pose, dpose, side=1, m=1.75, light=None, dlight=None, free_arm=False, dummy='winks',
             dx=0.0, dy=0.0, lift=0.05, between=None, three_q=0.42, d_turn=0.4, arm_over=False):
    """A ventriloquist (or Owen) sitting with the dummy on the knee `side` and the other hand inside his back: draws the
    person, the dummy on the knee (perch), then the free arm over the dummy. m = the person's height in metres (the dummy
    is drawn to scale, 0.85 m). Give the person Acting.vent_pose (or set the arms) and the dummy sit_dummy / puppet.
    lift (x height) raises the knee he sits on (a vent's knee is up on a footrest / crossed leg); between(pen) draws
    something after the person and before the dummy (a hospital blanket over the legs). Stage the person in 3/4 turned
    front-on or a little toward the dummy's side (turn 0 .. +0.25 for side +1) so the figure sits beside the body;
    free_arm=True draws the other arm over him (vent_pose(free='dummy'): the hand on his knee).
    Returns (dummy x, dummy seat y, dummy height px)."""
    P = _as_pose(pose); D = _as_pose(dpose)
    if three_q:                           # staged in 3/4 (front-on, a seated person reads as standing and the figure as
        P = P.copy()                      # standing beside him): his body turns away from the knee the figure sits on, so
        old = P.turn                      # the thigh runs out under the figure and the arm goes round behind into his back;
        P.turn = -three_q * side          # the head keeps most of its direction
        P.h_turn += (old - P.turn) * 0.6
    draw(pen, who, x, y_feet, height, P, light=light)
    if between: between(pen)
    ax, ay = lap_anchor(who, P, side, x, y_feet, height)
    ay -= lift * height
    dh = height * DUMMY_M / m
    D = D.copy(); D.perch = 1.0
    if D.sit < 0.5: D.sit = 1.0
    if d_turn:                            # the figure's body sits along the thigh (3/4); his head keeps its own direction
        D.turn += -d_turn * side; D.h_turn -= -d_turn * side
    draw(pen, dummy, ax + dx, ay + dy, dh, D, light=dlight or light)
    if free_arm: draw_arm(pen, who, -side, P, x=x, y_feet=y_feet, height=height, light=light)
    if arm_over: draw_arm(pen, who, side, P, x=x, y_feet=y_feet, height=height, light=light)   # the hand is out of his back
    return ax + dx, ay + dy, dh


def draw_carry(pen, who, x, y_feet, height, pose, dpose, m=1.74, light=None, dlight=None, dummy='winks', dx=0.0, dy=0.0):
    """`who` holding the dummy in their arms at the waist (Acting.hold_dummy on the person, Acting.carried on him): draws
    the person, the dummy sitting on the forearms, then both arms again over him. Returns (dummy x, seat y, height px)."""
    P = _as_pose(pose); D = _as_pose(dpose)
    draw(pen, who, x, y_feet, height, P, light=light)
    (wl, _), (wr, _) = hand_pos(who, P, 1, x=x, y_feet=y_feet, height=height), hand_pos(who, P, -1, x=x, y_feet=y_feet, height=height)
    ax, ay = (wl[0] + wr[0]) / 2, (wl[1] + wr[1]) / 2 - 4.0
    dh = height * DUMMY_M / m
    D = D.copy(); D.perch = 1.0
    if D.sit < 0.5: D.sit = 0.85
    k_ = clamp(-getattr(D, 'recline', 0.0) / 60.0)          # cradled: slide him so his middle lies across your arms
    dx += 0.36 * dh * k_; dy += 0.1 * dh * k_
    draw(pen, dummy, ax + dx, ay + dy, dh, D, light=dlight or light)
    # the arm behind his back stays under him (his head rests in its crook); the arm under his knees comes over him
    draw_arm(pen, who, 1, P, x=x, y_feet=y_feet, height=height, light=light)
    return ax + dx, ay + dy, dh


def draw_hand(pen, who, x, y, size, shape='open', angle=0.0, side=1, pose=None, detail=2):
    """One hand. size = wrist-to-fingertip length in design px; angle 0 = fingers down, 180 = fingers up."""
    sp = CAST[who]; P = _as_pose(pose)
    skin, sh, _ = _skin_cols(sp, P, None)
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.5))
    _draw_hand(c, sp, shape, x, y, size / 66.0, angle, side, detail, skin, sh, sp['ring'] == side, 0.0, P.t)


def _hpt(x, y, ang, k, hx, hy):
    """Hand-coords point (hx, hy) of a hand drawn at (x, y), rotated ang deg, scaled k -> parent coords."""
    a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
    return x + (hx * ca - hy * sa) * k, y + (hx * sa + hy * ca) * k


def draw_hands_lap(pen, who, cx, cy, size, rub_phase=0.0, ring_side=None, t=0.0, detail=2, light=None, cuffs=True,
                   thread=False, rub_amp=12.0, rub=True, _lay=None):
    """v2.1 insert: two hands folded in the lap, seen from the front and above. size = one hand's wrist-to-fingertip
    length in design px (the group is about 2.4 x size wide), centred at (cx, cy).
    The lower hand lies across the lap, back up, fingers relaxed (it wears the ring when ring_side is +1/-1, the band on
    its ring finger with a glint); the other hand cradles it from below (its fingertips show under the knuckles) and its
    thumb lies over the base of the ring finger, rocking +-rub_amp deg about the base knuckle with rub_phase (radians:
    pass e.g. (t - t0) * 4.6). ring_side None = no ring (the lower hand is the character's left). Sleeve cuffs come in
    from the frame edges (coat / hoodie / uniform / cardigan colours). thread=True hangs a lit loose thread from the
    lower hand's cuff."""
    sp = CAST[who]
    P = Pose(t=t)
    skin, sh, _ = _skin_cols(sp, P, light)
    sleeve, sleeve_sh = _limb_cols(sp)[:2]
    k = size / 66.0
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.5)).sub(cx, cy, 0.0, k)
    sB = int(ring_side) if ring_side in (-1, 1) else 1
    sA = -sB
    hb = sp['body'].get('hand', 1.0)
    # placements (lap units, hand length 66)
    L_ = dict(bx=46.0, by=-30.0, bang=50.0, wa=(30.0, 4.0), da=-88.0, tl=27.0)
    if _lay: L_.update(_lay)
    bx, by, bang = sB * L_['bx'], L_['by'], L_['bang'] * sB
    kx, ky = _hpt(bx, by, bang, hb, 0.0, 30.0)                 # centre the clasp (the lower hand's knuckles)
    bx -= kx; by -= ky - 4.0
    thB = -sB
    # the cradling hand, palm up under the lower hand (drawn mirrored, so its thumb lies on top): wrist on the lower
    # hand's thumb side, forearm toward the other side of the frame, fingertips peeking past the little finger
    wa_b = (thB * L_['wa'][0], L_['wa'][1])
    ax, ay = _hpt(bx, by, bang, hb, *wa_b)
    aang = bang + L_['da'] * sB
    sAd = sB
    # sleeves + cuffs (behind the hands)
    if cuffs:
        for s_, (wx, wy, wa) in ((sB, (bx, by, bang)), (sA, (ax, ay, aang))):
            ex_, ey_ = _hpt(wx, wy, wa, hb, 0.0, -4.0)
            fx_, fy_ = _hpt(wx, wy, wa, hb, 0.0, -130.0)
            tube = _tube([(fx_, fy_), (ex_, ey_)], [50.0, 42.0])
            c.fill(tube, sleeve); c.fill(_crescent(tube, 0, 8), sleeve_sh, 170); c.line(tube, c.lw)
            cuff = c.sub(ex_, ey_, wa, 1.0)
            cp = rrect(-22.5, -14, 45, 14, 4)
            cuff.fill(cp, mix(sleeve, '#000000', 0.18)); cuff.line(cp, c.lw * 0.8)
            if sp['outfit'] == 'hoodie' and detail >= 1:
                cuff.line(_multi([poly([(q * 5.0, -12), (q * 5.0, -2)], False) for q in range(-4, 5)]), c.lw * 0.3, LINE, 140)
            if s_ == sB and thread:
                corners = [_hpt(wx, wy, wa, hb, q * 22.0, -14.0) for q in (-1, 1)]
                thread_p0 = max(corners, key=lambda q: q[1])
    # the cradling hand (under), without its thumb
    _draw_hand(c, sp, 'palm4', ax, ay, 1.0, aang, sAd, detail, skin, sh, False, 0.0, t)
    # the lower hand, relaxed, ring on its ring finger
    _draw_hand(c, sp, 'relaxed', bx, by, 1.0, bang, sB, detail, skin, sh, ring_side in (-1, 1), 0.0, t)
    # the rubbing thumb of the cradling hand: from beside the little finger to the base of the ring finger
    G = _hand_cached('relaxed', sB, 0.0)
    rx, ry, rang, rw = G['ring']
    tgt_b = (-thB * 4.8, 31.5)
    tb0 = _hpt(ax, ay, aang, hb, -sAd * 15.0, 10.0)
    tgt = _hpt(bx, by, bang, hb, *tgt_b)
    ang0 = math.atan2(tgt[0] - tb0[0], tgt[1] - tb0[1])
    da = math.radians(rub_amp * math.sin(rub_phase)) if (rub and rub_phase is not None) else 0.0
    L1 = L_['tl'] * 0.54 * hb; L2 = L_['tl'] * 0.46 * hb
    a1 = ang0 + da
    j = (tb0[0] + math.sin(a1) * L1, tb0[1] + math.cos(a1) * L1)
    a2 = a1 + math.radians(6.0 * sB) + da * 0.5
    tip = (j[0] + math.sin(a2) * L2, j[1] + math.cos(a2) * L2)
    if cuffs and thread:                                       # the loose thread hangs free from the lower cuff, lit
        p0 = thread_p0
        sw = 4.0 * math.sin(t * 2.3) + 2.0 * math.sin(t * 3.7 + 1)
        th_ = smooth([p0, (p0[0] + sw * 0.3 + 1, p0[1] + 12), (p0[0] + sw * 0.7 - 2, p0[1] + 26), (p0[0] + sw, p0[1] + 40)], False)
        c.line(th_, c.lw * 0.7, LINE, 210); c.line(th_, c.lw * 0.38, '#d6d9de', 255)
    pts = [tb0, j, tip]
    thumb = _tube(pts, [12.0 * hb, 10.6 * hb, 9.0 * hb], 0.9)
    c.fill(thumb, skin); c.fill(_crescent(thumb, -2.5, -2.5), sh, 150); c.line(thumb, c.lw * 0.9)
    if detail >= 1:
        dx, dy = tip[0] - j[0], tip[1] - j[1]; Ld = math.hypot(dx, dy) or 1.0
        nc = c.sub(tip[0], tip[1], -math.degrees(math.atan2(dx, dy)))
        nl = rrect(-3.0 * hb, -Ld * 0.66, 6.0 * hb, Ld * 0.52, 2.8 * hb)
        nc.fill(nl, mix(skin, '#ffffff', 0.38), 230); nc.line(nl, c.lw * 0.25, sp['skin_dp'], 200)
        jc = c.sub(j[0], j[1], -math.degrees(a1))
        jc.line(smooth([(-3.5, -1.0), (0, 1.2), (3.5, -1.0)], False), c.lw * 0.32, sp['skin_dp'], 170)
    if light and light.get('rim'):
        c.fill(_crescent(thumb, -light.get('side', 1) * 2.5, 0), light['rim'], light.get('rim_a', 70))
    return dict(ring=_hpt(bx, by, bang, hb, rx, ry) if ring_side in (-1, 1) else None, thumb_tip=tip, scale=k,
                ring_xy=(cx + _hpt(bx, by, bang, hb, rx, ry)[0] * k, cy + _hpt(bx, by, bang, hb, rx, ry)[1] * k))


def draw_palm_on_glass(pen, who, x, y, size, press=1.0, t=0.0, angle=0.0, side=1, alpha=1.0, halo=1.0, slide=0.0,
                       light=None, detail=2):
    """v2.1: an open hand pressed flat on glass, palm toward the viewer, FINGERS UP at angle 0 (unlike draw_hand, where
    angle 0 = fingers down), 5 spread fingers with flattened pale pads, a darker pressed rim and a soft condensation
    halo. size = wrist-to-fingertip in design px; (x, y) = the wrist; slide = extra y (design px) for a slow slide down
    the glass; alpha 0..1 fades the whole hand. Place it beside the face, not over it."""
    sp = CAST[who]
    P = Pose(t=t)
    skin, sh, _ = _skin_cols(sp, P, light)
    k = size / 66.0
    cv = pen.cv
    lay = alpha < 0.999
    if lay: cv.saveLayerAlpha(None, int(255 * clamp(alpha)))
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 3.5)).sub(x, y + slide, 180.0 + angle, k * sp['body'].get('hand', 1.0))
    G = _hand_cached('flat', side, round(clamp(press), 1))
    u = G['union']
    if halo > 0:
        c.glow(0, 30, 62, 58, '#dce8f4', 70 * halo)
        c.line(u, 9.0, '#e6eff8', 60 * halo)
        c.line(u, 4.5, '#eef4fb', 90 * halo)
    pskin = mix(skin, '#e8d6cf', 0.25 * press)
    c.fill(u, pskin)
    c.fill(G['shade'], sh, 110)
    c.line(u, c.lw * 1.7, mix(skin, '#7b5a52', 0.55), 130 * press)          # pressed rim
    if detail >= 1:
        if G['creases_p'] is not None: c.line(G['creases_p'], c.lw * 0.32, sp['skin_dp'], 160)
        if G['lines_p'] is not None: c.line(G['lines_p'], c.lw * 0.38, sp['skin_dp'], 160)
        if G['seps'] is not None: c.line(G['seps'], c.lw * 0.4, LINE, 140)
    for p in G['press']: c.fill(p, '#f3e8e2', 200 * press)
    c.line(u, c.lw * 0.9)
    if lay: cv.restore()


# ====================================================================================================== acting
import bisect as _bisect
import re as _re

VISEMES = {  # open, wide, round, teeth, press
    'A': (0.60, 0.15, 0.0, 0.45, 0.0), 'E': (0.34, 0.55, 0.0, 0.7, 0.0), 'I': (0.24, 0.75, 0.0, 0.8, 0.0),
    'O': (0.50, -0.2, 0.8, 0.15, 0.0), 'U': (0.20, -0.3, 1.0, 0.0, 0.0), 'M': (0.0, 0.0, 0.0, 0.0, 0.7),
    'F': (0.10, 0.25, 0.0, 0.9, 0.0), 'L': (0.30, 0.2, 0.0, 0.6, 0.0), 'rest': (0.04, 0.0, 0.0, 0.1, 0.1),
}


def _env(t, t0, t1=None, fin=0.3, fout=0.3, ein=ease_in_out, eout=ease_in_out):
    """Envelope: eases in over fin from t0, holds, eases out over fout from t1 (t1 None = hold forever)."""
    if t < t0: return 0.0
    a = ein(prog(t, t0, t0 + fin)) if fin > 0 else 1.0
    if t1 is None: return a
    if t >= t1 + fout: return 0.0
    b = 1.0 - eout(prog(t, t1, t1 + fout)) if fout > 0 else float(t < t1)
    return min(a, b)


def _syllables(word):
    w = word.lower().replace("'", '')
    groups = _re.findall(r'[^aeiouy]*[aeiouy]+', w)
    if not groups: return [(w, '')]
    out = []
    for g in groups:
        m = _re.match(r'([^aeiouy]*)([aeiouy]+)', g)
        out.append((m.group(1), m.group(2)))
    if len(out) > 1 and out[-1][1] == 'e' and not out[-1][0].endswith('l'): out = out[:-1]   # silent e
    return out


def _vowel_vis(v):
    if v.startswith(('ee', 'ea', 'ie', 'y', 'i')): return 'I'
    if v.startswith(('oo', 'u', 'ew')): return 'U'
    if v.startswith(('ou', 'ow', 'o', 'au', 'aw')): return 'O'
    if v.startswith(('ai', 'ay', 'e', 'ei')): return 'E'
    return 'A'


def _onset_vis(c):
    if not c: return None
    ch = c[-1]
    if ch in 'mbp': return 'M'
    if ch in 'fv': return 'F'
    if ch in 'w': return 'U'
    if ch in 'ltdn': return 'L'
    return None


# ------------------------------------------------------------------ voice envelope + word timing (lip sync, v2.1)
_SCR = os.path.join(_HERE, '_work')                      # this film's work dir W (Bunnyman Video/film/_work)
VOICE_WAV = os.environ.get('POV2_VOICE_WAV', os.path.join(_SCR, 'align', 'vo_en.wav'))
VOICE_WORDS = os.environ.get('POV2_VOICE_WORDS', os.path.join(_SCR, 'align', 'asr_cache.json'))
ENV_FPS = 100.0
_VENV, _VWORDS = {}, {}


def voice_envelope(path=None):
    """RMS envelope of the voice track in dBFS at 100 fps (30 ms window), as float32 np array, or None if the file is
    missing. Cached in memory and as .npy in W/cache (keyed by size and mtime), so render workers load it in ms."""
    path = path or VOICE_WAV
    if path in _VENV: return _VENV[path]
    env = None
    try:
        st = os.stat(path)
        cdir = os.path.join(_SCR, 'cache')
        cache = os.path.join(cdir, 'vo_env_%d_%d.npy' % (st.st_size, int(st.st_mtime)))
        if os.path.exists(cache):
            env = np.load(cache)
        else:
            import soundfile as sf
            y, sr = sf.read(path, dtype='float32', always_2d=True)
            y = y.mean(1)
            hop = int(round(sr / ENV_FPS)); n = len(y) // hop
            p = (y[:n * hop] ** 2).reshape(n, hop).mean(1)
            p = np.convolve(p, np.ones(3) / 3.0, 'same')
            env = (10.0 * np.log10(np.maximum(p, 1e-10))).astype(np.float32)
            try:
                os.makedirs(cdir, exist_ok=True); np.save(cache, env)
            except OSError:
                pass
    except Exception:
        env = None
    _VENV[path] = env
    return env


def voice_words(path=None):
    """[(word, t_start)] from the ASR cache (en_words), or [] when it is missing."""
    path = path or VOICE_WORDS
    if path in _VWORDS: return _VWORDS[path]
    out = []
    try:
        import json as _json
        out = [(str(w), float(t)) for w, t in _json.load(open(path))['en_words']]
    except Exception:
        out = []
    _VWORDS[path] = out
    return out


def _env_db(env, t):
    """Envelope value (dBFS) at time t, linearly interpolated (env: 100 fps array, or a callable t -> dBFS)."""
    if callable(env): return float(env(t))
    x = t * ENV_FPS
    i = int(math.floor(x))
    if i < 0 or i >= len(env) - 1: return -100.0
    u = x - i
    return float(env[i] * (1 - u) + env[i + 1] * u)


# ------------------------------------------------------------------ delivery: the driver's smile, stage by stage
# Every stage holds the same keys so stages blend cleanly. The eyes never smile (lock 1), the pupils shrink and the
# whites grow as the smile widens. 'off' = "his face is perfectly still" (435.8 s).
_STAGE_KEYS = ('smile', 'grin', 'teeth', 'gums', 'm_open', 'm_press', 'wide', 'pupil', 'bloodshot', 'brow_up', 'still', 'life')
DRIVER_STAGES = {         # fix 3: never a pleasant smile: from the first frame a fixed, uncanny grin (wider than the eyes, a line
    # of teeth, tiny pupils, no blinks) that only gets wider; the mouth talks through it (grin damps the jaw in talk())
    0: dict(smile=0.55, grin=0.30, teeth=0.60, gums=0.0, m_open=0.00, m_press=0.00, wide=0.30, pupil=0.46, bloodshot=0.20, brow_up=0.00, still=0.50, life=1.0),
    1: dict(smile=0.75, grin=0.42, teeth=0.85, gums=0.0, m_open=0.00, m_press=0.00, wide=0.34, pupil=0.43, bloodshot=0.25, brow_up=0.05, still=0.55, life=1.0),
    2: dict(smile=0.88, grin=0.52, teeth=0.95, gums=0.05, m_open=0.00, m_press=0.00, wide=0.38, pupil=0.41, bloodshot=0.32, brow_up=0.12, still=0.60, life=1.0),
    3: dict(smile=0.96, grin=0.64, teeth=1.00, gums=0.15, m_open=0.02, m_press=0.0, wide=0.45, pupil=0.38, bloodshot=0.42, brow_up=0.22, still=0.65, life=1.0),
    4: dict(smile=1.00, grin=0.80, teeth=1.00, gums=0.40, m_open=0.04, m_press=0.0, wide=0.52, pupil=0.35, bloodshot=0.52, brow_up=0.32, still=0.70, life=1.0),
    5: dict(smile=1.00, grin=1.15, teeth=1.00, gums=0.85, m_open=0.12, m_press=0.0, wide=0.60, pupil=0.32, bloodshot=0.65, brow_up=0.45, still=0.75, life=1.0),
    'off': dict(smile=0.0, grin=0.0, teeth=0.0, gums=0.0, m_open=0.0, m_press=0.55, wide=0.45, pupil=0.50, bloodshot=0.40, brow_up=0.10, still=1.0, life=0.12),
}
# (film time s, stage, transition s), from the delivery timeline tags: smile 66.24, 'Just finish it' ~139 (a minute before
# 'wider' at 196.5), 'Who's the lucky one' 184.8, leans close 340.9, no_smile 435.8, wider2 446.4.
DRIVER_ARC = [(-1e9, 0, 0.0), (66.24, 1, 1.8), (139.0, 2, 2.0), (184.82, 3, 2.2), (340.87, 4, 2.0), (435.84, 'off', 0.45),
              (446.44, 5, 2.4)]
CAST['driver']['arc'] = DRIVER_ARC


def driver_stage(t, arc=None):
    """Driver smile parameters at film time t (dict of _STAGE_KEYS), blending stage changes over their transition."""
    arc = DRIVER_ARC if arc is None else arc
    i = 0
    for k, a in enumerate(arc):
        if a[0] <= t: i = k
    st = DRIVER_STAGES[arc[i][1]]
    tr = arc[i][2] if len(arc[i]) > 2 else 1.5
    if i == 0 or tr <= 0 or t >= arc[i][0] + tr: return dict(st)
    pv = DRIVER_STAGES[arc[i - 1][1]]
    u = ease_in_out((t - arc[i][0]) / tr)
    return {k: pv[k] + (st[k] - pv[k]) * u for k in _STAGE_KEYS}


# ------------------------------------------------------------------ dummy film: Mister Winks's arc, stage by stage
# The painted grin widens and the stare hardens over the night (like the driver's smile). Every stage holds the same keys.
# 'show' = the cheerful 1974 TV figure; 'tape' = the real Walter crying inside him on the tape; 'owen' = Owen inside him at
# the end (the brows of a scared boy under the widest painted grin, wet eyes); 'asleep' = the same with the lids shut.
_WINKS_KEYS = ('grin_w', 'pupil', 'wide', 'brow_angry', 'brow_up', 'brow_sad', 'crack', 'desperate', 'lock', 'lid_l', 'lid_r', 'tears')
WINKS_STAGES = {
    0: dict(grin_w=0.00, pupil=0.62, wide=0.10, brow_angry=0.30, brow_up=0.05, brow_sad=0.0, crack=0.0, desperate=0.0, lock=1.0, lid_l=0.0, lid_r=0.0, tears=0.0),
    1: dict(grin_w=0.30, pupil=0.54, wide=0.16, brow_angry=0.42, brow_up=0.03, brow_sad=0.0, crack=0.17, desperate=0.0, lock=1.0, lid_l=0.0, lid_r=0.0, tears=0.0),
    2: dict(grin_w=0.58, pupil=0.46, wide=0.24, brow_angry=0.55, brow_up=0.0, brow_sad=0.0, crack=0.34, desperate=0.0, lock=1.0, lid_l=0.0, lid_r=0.0, tears=0.0),
    3: dict(grin_w=0.85, pupil=0.38, wide=0.32, brow_angry=0.68, brow_up=0.0, brow_sad=0.0, crack=0.5, desperate=0.0, lock=1.0, lid_l=0.0, lid_r=0.0, tears=0.0),
    4: dict(grin_w=1.10, pupil=0.31, wide=0.40, brow_angry=0.80, brow_up=0.0, brow_sad=0.0, crack=0.67, desperate=0.0, lock=1.0, lid_l=0.0, lid_r=0.0, tears=0.0),
    5: dict(grin_w=1.40, pupil=0.24, wide=0.48, brow_angry=0.92, brow_up=0.0, brow_sad=0.0, crack=0.84, desperate=0.0, lock=1.0, lid_l=0.0, lid_r=0.0, tears=0.0),
    'show': dict(grin_w=0.0, pupil=0.85, wide=0.0, brow_angry=0.12, brow_up=0.35, brow_sad=0.0, crack=0.0, desperate=0.0, lock=0.4, lid_l=0.0, lid_r=0.0, tears=0.0),
    'tape': dict(grin_w=0.0, pupil=1.05, wide=0.45, brow_angry=0.0, brow_up=0.3, brow_sad=1.0, crack=0.0, desperate=1.0, lock=1.0, lid_l=0.0, lid_r=0.0, tears=0.7),
    'owen': dict(grin_w=1.40, pupil=1.1, wide=0.5, brow_angry=0.0, brow_up=0.3, brow_sad=1.0, crack=0.84, desperate=1.0, lock=0.6, lid_l=0.0, lid_r=0.0, tears=0.35),
    'asleep': dict(grin_w=1.40, pupil=1.1, wide=0.5, brow_angry=0.0, brow_up=0.3, brow_sad=1.0, crack=0.84, desperate=1.0, lock=0.6, lid_l=1.0, lid_r=1.0, tears=0.0),
}
# (film time s, stage, transition s) from this film's timeline tags: in Grandpa's chair 173.97 ('in_chair'), the 180 head
# turn 250.39, stands on the chair 314.69, "smiles up at me" 401.93, Owen's lap 523.43, "Goodnight, Owen" -> Owen is in
# him and the lids are shut 567.06 ('eyes_close'), "opens his eyes" 655.47 (the lids open over 1.8 s, desperate)
WINKS_ARC = [(-1e9, 0, 0.0), (173.97, 1, 1.5), (250.39, 2, 1.2), (314.69, 3, 2.0), (401.93, 4, 1.4), (523.43, 5, 1.6),
             (567.06, 'asleep', 0.12), (655.6, 'owen', 1.8)]
WINKS_TAPE_ARC = [(-1e9, 'show', 0.0), (448.58, 'tape', 0.8)]     # the dummy on the 1974 tape (the real Walter inside)
CAST['winks']['arc'] = WINKS_ARC
CAST['winks']['stages'] = WINKS_STAGES
CAST['winks']['stage_keys'] = _WINKS_KEYS


def stage_at(t, arc, stages=None, keys=None):
    """Stage parameters at film time t for an arc [(t, stage, transition)], blending stage changes."""
    stages = DRIVER_STAGES if stages is None else stages
    keys = _STAGE_KEYS if keys is None else keys
    i = 0
    for k, a in enumerate(arc):
        if a[0] <= t: i = k
    st = stages[arc[i][1]]
    tr = arc[i][2] if len(arc[i]) > 2 else 1.5
    if i == 0 or tr <= 0 or t >= arc[i][0] + tr: return dict(st)
    pv = stages[arc[i - 1][1]]
    u = ease_in_out((t - arc[i][0]) / tr)
    return {k: pv[k] + (st[k] - pv[k]) * u for k in keys}


def winks_stage(t, arc=None):
    """Mister Winks's face parameters at film time t (dict of _WINKS_KEYS)."""
    return stage_at(t, WINKS_ARC if arc is None else arc, WINKS_STAGES, _WINKS_KEYS)


class Acting:
    """Timeline of acting clips for one character. See the module docstring for the clip vocabulary."""

    def __init__(self, who='officer', seed=0, height=700.0, expr='neutral', blink=None, life=1.0, arc=None):
        self.who, self.seed, self.height = who, int(seed), float(height)
        self._arc = CAST[who].get('arc') if arc is None else (arc or None)   # driver: the smile arc in film time
        self.life_k = float(life)
        if CAST[who].get('dummy') and life == 1.0: self.life_k = 0.0   # Mister Winks is dead still unless he acts (ticks: escalate)
        sp = CAST[who]
        self.sp = sp
        self.expr0 = expr
        self.blink_rate = sp['blink_rate'] if blink is None else (0.33 if blink is True else (0.0 if blink is False else float(blink)))
        self.micro = sp['micro']
        self.clips = []              # (t0, t1, fn, realtime)
        self.late = []               # clips that override everything else (snap_turn)
        self.freezes = []            # (t0, t1)
        self.events = []
        self._clacks = []            # dummy: jaw snaps (they end jaw_drop / jaw_hang)
        self.base = dict(lock=sp['lock'], pupil=1.0)
        rng = np.random.default_rng(900 + self.seed * 31 + len(who))
        # blink schedule
        self._blinks = []
        if self.blink_rate > 0:
            tt = rng.uniform(0.3, 2.0)
            while tt < 1500:
                self._blinks.append(tt)
                if rng.uniform() < 0.28:                           # nervous double blink
                    self._blinks.append(tt + rng.uniform(0.13, 0.2)); tt = self._blinks[-1]
                tt += max(0.6, rng.exponential(1.0 / self.blink_rate)) + 0.4
        # v2.1 idle life schedules: head re-settles (pose swaps), weight shifts, micro twitches (creepy cast)
        self.creepy = sp['lock'] >= 0.5
        def sched(lo, hi, n_t, f):
            ts, vs = [-1e9], [tuple(0.0 for _ in range(n_t))]
            tt = rng.uniform(0.2, hi)
            while tt < 1500:
                ts.append(tt); vs.append(f()); tt += rng.uniform(lo, hi)
            return ts, vs
        sgn = [1.0]
        def settle():
            sgn[0] = -sgn[0] if rng.uniform() < 0.7 else sgn[0]
            return (sgn[0] * rng.uniform(1.5, 4.5), rng.uniform(-0.035, 0.035), rng.uniform(-2.5, 2.5))
        self._set_t, self._set_v = sched(2.0, 3.6, 3, settle)
        self._nv_t, self._nv_v = sched(1.3, 2.6, 3, lambda: (rng.uniform(-4.0, 4.0), rng.uniform(-0.07, 0.07), rng.uniform(-0.045, 0.045)))
        self._ws_t, self._ws_v = sched(3.5, 6.5, 1, lambda: (rng.uniform(-6.0, 6.0),))
        self._tw_t, self._tw_v = sched(4.5, 8.5, 3, lambda: (rng.uniform(0.3, 0.55), 1.0 if rng.uniform() < 0.5 else -1.0, rng.uniform(-1, 1)))
        # saccade schedule for unlocked eyes
        self._sacc_t, self._sacc_xy = [-1e9], [(0.0, 0.0)]
        tt = 0.0
        while tt < 1500:
            tt += rng.uniform(0.7, 2.6)
            self._sacc_t.append(tt); self._sacc_xy.append((rng.uniform(-0.45, 0.45), rng.uniform(-0.25, 0.18)))

    # ------------------------------------------------------------------ core
    def _add(self, t0, t1, fn, real=False, late=False):
        (self.late if late else self.clips).append((t0, INF if t1 is None else t1, fn, real))
        return self

    def _ev(self, t, name, gain_db=0.0, pan=0.0, **params):
        e = dict(t=round(float(t), 4), name=name, gain_db=gain_db, pan=pan, params=params, who=self.who)
        self.events.append(e); return e

    def _tmap(self, t):
        for a, b in self.freezes:
            if a <= t <= b: return a
        return t

    def _blink_amt(self, t):
        if not self._blinks: return 0.0
        i = _bisect.bisect_right(self._blinks, t) - 1
        if i < 0: return 0.0
        dt = t - self._blinks[i]
        if dt < 0.017: return dt / 0.017
        if dt < 0.05: return 1.0
        if dt < 0.067: return 1.0 - (dt - 0.05) / 0.017
        return 0.0

    def _saccade(self, t):
        i = _bisect.bisect_right(self._sacc_t, t) - 1
        x1, y1 = self._sacc_xy[i]
        x0, y0 = self._sacc_xy[max(i - 1, 0)]
        u = ease_out_cubic(prog(t, self._sacc_t[i], self._sacc_t[i] + 0.06))
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u

    def _raw(self, t):
        tf = self._tmap(t)
        P = Pose()
        P.t = t
        P.mix(self.base); P.mix(EXPR[self.expr0])
        if self._arc: P.mix(stage_at(tf, self._arc, self.sp.get('stages'), self.sp.get('stage_keys')), 1.0)
        sd = self.seed * 7 + 3
        # idle: breathing, micro head motion, sway, wandering eyes
        P.breath = 0.5 + 0.45 * math.sin(2 * PI * tf / 3.9 + sd) + 0.08 * noise1(tf * 0.4, sd)
        for (t0, t1, fn, real) in (self.clips + self.late if self.late else self.clips):
            tt = t if real else tf
            if (t0 == -INF or t0 - 1.5 <= tt) and tt <= t1 + 1.5: fn(P, tt)
        m = self.micro * (1.0 - clamp(P.still))
        P.h_tilt += 1.7 * m * noise1(tf * 0.21, sd + 1)
        P.h_turn += 0.035 * m * noise1(tf * 0.16, sd + 2)
        P.h_nod += 0.03 * m * noise1(tf * 0.19, sd + 3)
        P.sway += 3.0 * m * noise1(tf * 0.3, sd + 4)
        P.tilt += 0.5 * m * noise1(tf * 0.13, sd + 5)
        lf = self.life_k * clamp(P.life)
        if P.still > 0: P.breath = lerp(P.breath, 0.5 + (0.15 + 0.17 * lf) * math.sin(2 * PI * tf / 4.6 + sd), clamp(P.still))
        if lf > 0.01: self._life(P, tf, lf, sd)
        sx, sy = self._saccade(tf)
        un = (1.0 - clamp(P.lock)) * (1.0 - clamp(P.still))
        P.look_x += sx * un; P.look_y += sy * un
        b = self._blink_amt(tf) * (1.0 - clamp(P.still)) * (1.0 - clamp(getattr(P, '_noblink', 0.0)))
        P.blink = max(P.blink, b)
        return P

    @staticmethod
    def _step(ts, vs, t, dur, fn=ease_out_cubic):
        """Value of a step schedule at t: eased move from the previous target to the current one over dur."""
        i = _bisect.bisect_right(ts, t) - 1
        if i <= 0: return vs[0]
        u = fn(prog(t, ts[i], ts[i] + dur))
        a, b = vs[i - 1], vs[i]
        return tuple(x + (y - x) * u for x, y in zip(a, b))

    def _life(self, P, tf, lf, sd):
        """v2.1 idle life, layered after the clips. Creepy cast (and anyone staring): very slow head drift, a head
        re-settle (pose swap) every 2-3.6 s, slow weight shifts, and (creepy cast) a small involuntary twitch every
        4.5-8.5 s. Scared cast (you, mum): quick nervous head re-orients every 1.3-2.6 s scaled by the fear in the face,
        and a shiver (8-12 Hz) with pose.tremble. Breathing never stops (only freeze() stops everything). No blinks."""
        st = clamp(P.still)
        if self.sp.get('dummy'):                       # a dummy: no breath, no drift; a hard little head tick now and then
            if lf > 0.01:
                a_, n_, x_ = self._step(self._set_t, self._set_v, tf, 0.05, lambda u: u)
                P.h_tilt += 0.9 * a_ * lf; P.h_nod += 0.5 * n_ * lf
            return
        k = lf * (1.0 if self.creepy else st)
        if k > 0.01:
            P.h_tilt += 3.2 * k * noise1(tf * 0.06, sd + 21)
            P.h_turn += 0.02 * k * noise1(tf * 0.05, sd + 22)
            a_, n_, x_ = self._step(self._set_t, self._set_v, tf, 0.32)
            P.h_tilt += a_ * k; P.h_nod += n_ * k; P.h_dx += x_ * k
            (w_,) = self._step(self._ws_t, self._ws_v, tf, 0.9, ease_in_out)
            P.sway += w_ * k; P.tilt += 0.22 * w_ * k
        if self.creepy and lf > 0.01:
            i = _bisect.bisect_right(self._tw_t, tf) - 1
            if i > 0:
                tau = tf - self._tw_t[i]
                if 0 <= tau < 0.6:
                    amp, d1, d2 = self._tw_v[i]
                    f = math.exp(-tau * 9.0) * math.sin(tau * 46.0) * amp * lf
                    P.h_tilt += 9.0 * f * d1; P.h_dx += 5.0 * f * d2; P.shrug += 0.2 * abs(f)
                    P.brow_asym += 0.5 * f * d1; P.m_side += 0.4 * f * d1
        if not self.creepy and lf > 0.01:
            # scared cast: quick nervous head re-orients (small glances, swallow dips) scaled by how afraid the face is
            fk = clamp(max(1.3 * P.tremble, 0.9 * P.brow_sad, P.sweat, 0.8 * P.wide)) * lf * (1.0 - 0.6 * clamp(P.lock))
            if fk > 0.05:
                a_, h_, n_ = self._step(self._nv_t, self._nv_v, tf, 0.18)
                P.h_tilt += a_ * fk; P.h_turn += h_ * fk; P.h_nod += n_ * fk
        if self.sp.get('child') and lf > 0.01:          # Lily: a child is never still (slow sway, head drift, glances)
            P.h_tilt += 5.0 * lf * noise1(tf * 0.27, sd + 41); P.sway += 5.0 * lf * noise1(tf * 0.22, sd + 42)
            P.h_turn += 0.06 * lf * noise1(tf * 0.18, sd + 43); P.tilt += 1.2 * lf * noise1(tf * 0.2, sd + 44)
            a_, h_, n_ = self._step(self._nv_t, self._nv_v, tf, 0.35, ease_in_out)
            P.h_tilt += 0.6 * a_ * lf; P.h_turn += 0.5 * h_ * lf; P.h_nod += 0.5 * n_ * lf
        tr = clamp(P.tremble) * (0.0 if self.creepy else 1.0) * lf
        if tr > 0.12:
            P.h_dx += 0.5 * tr * noise1(tf * 10.0, sd + 31)
            P.h_tilt += 0.8 * tr * noise1(tf * 9.0, sd + 32)
            P.shrug += 0.03 * tr * noise1(tf * 11.0, sd + 33)

    def at(self, t):
        """Pose at time t (seconds), with secondary motion (cord / hair / drawstring swing) from lagged motion."""
        P = self._raw(t)
        a = self._raw(t - 0.09); b = self._raw(t - 0.2)
        v = (a.h_tilt - P.h_tilt) * 0.05 + (b.h_tilt - a.h_tilt) * 0.03 + (a.turn + a.h_turn - P.turn - P.h_turn) * 1.2 + \
            (a.dx - P.dx) * 0.012 + (a.sway - P.sway) * 0.05 + (a.tilt - P.tilt) * 0.05
        P.sec_x = clamp(v, -1.5, 1.5)
        P.sec_y = clamp((a.lean - P.lean) * 2.0 + (a.bob - P.bob) * 0.02, -1, 1)
        return P

    __call__ = at

    def depth(self, base, k=0.55):
        """Layer depth function for lean_in: base * (1 - k * approach(t))."""
        return lambda t: base * (1.0 - k * clamp(self.at(t).approach))

    def cues(self):
        return sorted(self.events, key=lambda e: e['t'])

    # ------------------------------------------------------------------ expressions and looks
    def expr(self, name, t0, t1=None, fade=0.35):
        d = EXPR[name]
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))

    def set(self, t0, t1=None, fade=0.3, **params):
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(params, _env(t, t0, t1, fade, fade)))

    def idle(self, t0=0.0, t1=None):
        return self.set(t0, t1, 0.4, lock=0.0, still=0.0)

    def look(self, t0, x, y, dur=0.12, t1=None):
        return self.set(t0, t1, dur, look_x=x, look_y=y, lock=0.0)

    def stare(self, t0, t1=None, fade=0.4):
        d = dict(pupil=0.5, wide=0.5, brow_up=0.3, lock=1.0, still=1.0, bloodshot=0.45)
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))

    def creep_smile(self, t0, dur=4.0, t1=None, amount=1.0, fade=0.6):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            w = _env(t, t0, t1, 0.05, fade)
            if w <= 0: return
            P.mix(dict(smile=0.95 * amount * u, grin=0.5 * amount * ease_in_cubic(u), teeth=clamp((u - 0.35) / 0.4) * amount,
                       pupil=lerp(P.pupil, 0.55, u), wide=lerp(P.wide, 0.32, u), brow_up=lerp(P.brow_up, 0.3, u), lock=1.0,
                       still=u, bloodshot=0.35 * u), w)
            P.h_tilt += 5.0 * u * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def wide_grin(self, t0, t1=None, fade=0.6):
        d = EXPR['wide_grin']
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            P.mix(d, w)
            P.m_side += 0.12 * w * noise1(t * 3.0, self.seed + 40)
            P.still = max(P.still, w)
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    # ------------------------------------------------------------------ head
    def head_tilt(self, t0, angle=32.0, dur=1.6, t1=None, back='ease', back_dur=None):
        bd = back_dur or (0.3 if back == 'snap' else dur)
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            if t1 is not None and t >= t1:
                if back == 'snap': u = u * (1.0 - spring(t - t1, 3.2, 0.42))
                else: u = u * (1.0 - ease_in_out(prog(t, t1, t1 + bd)))
            a = angle * u
            P.h_tilt += a
            extra = max(0.0, abs(a) - 20.0) * (1 if a > 0 else -1)
            P.h_dx += -extra * 0.9
            P.h_dy += abs(extra) * 0.25
            P.tilt += a * 0.06
        return self._add(t0, None if t1 is None else t1 + bd + 1.0, fn)

    def snap_turn(self, t, frm=1.0, to=0.0, hold=0.6, body=0.35, until=None, release=0.5):
        """Head held at `frm` (from t-hold), snaps to `to` at t with a spring overshoot. Eyes lead by 50 ms, body follows.
        v2.1: the snap TAKES CONTROL of the yaw (it overrides earlier clips such as a held look-aside instead of adding to
        them) and holds `to` after the snap until `until` (None = for good), then releases over `release` s. It runs after
        the ordinary clips whatever the order they were added in. frm=None starts from the current head yaw."""
        def fn(P, tt):
            w_in = ease_in_out(prog(tt, t - hold, t - hold + 0.25))
            if until is not None and tt > until: w_in *= 1.0 - ease_in_out(prog(tt, until, until + release))
            if w_in <= 0: return
            body0 = 0.0
            f = (P.turn + P.h_turn) if frm is None else frm
            if tt < t:
                h = f
            else:
                h = to + (f - to) * (1.0 - spring(tt - t, 3.6, 0.5))
            bodyk = (1.0 - ease_out_cubic(prog(tt, t + 0.06, t + 0.5))) if tt >= t else 1.0
            b_des = body0 + (f - body0) * body * bodyk
            P.turn = lerp(P.turn, b_des, w_in)
            P.h_turn = lerp(P.h_turn, h - b_des, w_in)
            P.lock = lerp(P.lock, 1.0, prog(tt, t - 0.06, t - 0.01) * w_in)
            if tt >= t:
                P.look_x = lerp(P.look_x, 0.0, w_in); P.look_y = lerp(P.look_y, 0.0, w_in)
                k = math.exp(-(tt - t) * 6.0)
                P.h_tilt += 7.0 * math.sin((tt - t) * 26.0) * k
                P.wide += 0.35 * k; P.pupil *= 1.0 - 0.3 * k
        return self._add(t - hold - 0.3, (until + release) if until is not None else None, fn, late=True)

    def lean_in(self, t0, dur=2.5, t1=None, amount=1.0, back_dur=0.9):
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            if t1 is not None and t >= t1: u *= 1.0 - ease_in_out(prog(t, t1, t1 + back_dur))
            P.lean += 0.7 * amount * u
            P.approach += amount * u
            P.h_nod -= 0.1 * u
            P.lock = lerp(P.lock, 1.0, u)
        return self._add(t0, None if t1 is None else t1 + back_dur, fn)

    def head_down(self, t0, t1=None, amount=1.0, fade=0.8):
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            P.h_nod += 0.55 * amount * w
            P.h_dy += 8 * amount * w
            if P.lock < 0.5: P.look_y += 0.5 * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def turn(self, t0, to, dur=0.6):
        """Body + head yaw to `to` (quarter turns). The head leads, the body follows (overlapping action)."""
        def fn(P, t):
            base = P.turn
            wh = ease_in_out(prog(t, t0, t0 + dur * 0.6))
            wb = ease_in_out(prog(t, t0 + dur * 0.15, t0 + dur))
            P.turn = base + (to - base) * wb
            P.h_turn += (to - base) * (wh - wb)
        return self._add(t0, None, fn)

    def turn_back(self, t0, dur=0.45, side=1):
        return self.turn(t0, 2.0 * side, dur)

    # ------------------------------------------------------------------ body and hands
    def _arm(self, P, side, w, out, down, fwd, shape=None, up=None, prop=None, press=None, rot=None):
        pre = 'hl_' if side > 0 else 'hr_'
        d = {pre + 'out': out, pre + 'down': down, pre + 'fwd': fwd}
        if up is not None: d[pre + 'up'] = up
        if press is not None: d[pre + 'press'] = press
        if rot is not None: d[pre + 'rot'] = rot
        if shape is not None: d[pre + 'shape'] = shape
        if prop is not None or w >= 0.5: d[pre + 'prop'] = prop
        P.mix(d, w)

    def knock(self, t0, n=3, spacing=0.32, side=0.0, hand=None, strength=1.0, reach=0.72):
        """Fist knocks. Returns the knock_door events (one per hit).
        side +1/-1: the door slab is to screen right/left of the lens (a doorbell sits beside the door): the near arm
            (hand=None picks it) reaches out at shoulder height (`reach` x arm length, >= 0.6) with a forearm snap on every
            hit, the body rocks 2-4 deg into the knock and the head stays locked on the lens.
        side 0: knock on the lens itself (peephole / doorbell glass): the fist comes up to face height in front of the
            body and grows ~1.3x toward the lens on each hit (events carry params lens=True: pair them with a ~1.5% camera
            punch)."""
        first = t0 + 0.34
        hits = [first + i * spacing for i in range(n)]
        end = hits[-1] + 0.45
        hs = hand if hand is not None else (int(math.copysign(1, side)) if side else -1)
        b_ = self.sp['body']
        L = 348.0 * reach

        def pulse_at(t):
            pulse = 0.0
            for h in hits:
                d = t - h
                if -0.11 <= d < 0: pulse = max(pulse, ease_in_cubic(prog(d, -0.11, 0)))
                elif 0 <= d < 0.17: pulse = max(pulse, 1.0 - ease_out_cubic(d / 0.17))
            return pulse

        def fn(P, t):
            w = _env(t, t0, end - 0.3, 0.32, 0.42, ease)
            if w <= 0: return
            pulse = pulse_at(t) * w
            if side:
                out = L * 0.82 + 38.0 * pulse
                self._arm(P, hs, w, out, -14.0 + 8.0 * pulse, 70.0 + 20.0 * pulse, 'fist', up=0.08)
                P.tilt += (2.0 + 1.6 * strength) * pulse * (1 if hs > 0 else -1)
                P.lean += 0.02 * pulse * strength
                P.turn += 0.1 * side * w; P.h_turn -= 0.1 * side * w
            else:
                self._arm(P, hs, w, 55.0 - (b_['sh'] - 17), -46.0 + 12.0 * pulse, 290.0 + 160.0 * pulse * strength, 'fist', up=0.95)
                setattr(P, ('hl_' if hs > 0 else 'hr_') + 'scale', 1.0 + 0.16 * pulse * strength)
                P.lean += 0.045 * pulse * strength
                P.h_nod += 0.02 * pulse
            P.lock = lerp(P.lock, 1.0, w)
        self._add(t0, end + 0.5, fn)
        evp = dict(lens=True) if not side else {}
        return [self._ev(h, 'knock_door', 0.0 if i == 0 else -1.0, pan=0.0 if not side else 0.35 * side, n=1, strength=strength, **evp)
                for i, h in enumerate(hits)]

    def radio_to_mouth(self, t0, t1, side=1, tilt=13.0):
        """The hand brings the shoulder speaker-mic up beside the mouth (the coiled cord follows), the head tilts 12-15 deg
        into it with the eyes locked on the lens, and the thumb squashes the push-to-talk key on each click."""
        sp = self.sp; b = sp['body']; hh = sp['hh']
        clicks = [t0 + 0.38, t1 - 0.02]
        mouth = -hh / 2 + sp['mouth_y'] * hh / 240.0          # mouth relative to the chin line
        def fn(P, t):
            w = _env(t, t0, t1, 0.4, 0.4, ease)
            if w <= 0: return
            down = mouth + 46.0 - 64.0 + 26.0 * P.shrug
            out = (hh * 100.0 / 240.0) * 0.62 - (b['sh'] - 17)
            pr = 0.0
            for c_ in clicks:
                pr = max(pr, math.exp(-((t - c_) / 0.07) ** 2))
            self._arm(P, side, w, out, down, 78.0, 'grip', up=1.0, prop='mic', press=pr, rot=-side * 8.0)
            P.h_tilt += tilt * side * w; P.h_turn += 0.1 * side * w; P.h_nod += 0.08 * w
            P.lock = lerp(P.lock, 1.0, w)
            P.shrug += 0.1 * w
        self._add(t0, t1 + 0.4, fn)
        return [self._ev(clicks[0], 'radio_click', -3.0), self._ev(clicks[1], 'radio_click', -3.0),
                self._ev(t1 + 0.02, 'police_radio_squelch', -9.0)]

    def phone_to_ear(self, t0, t1=None, side=1, fade=0.5, tilt=6.0):
        """Phone held to the ear (busts and full body): wrist just below the ear, elbow forward and down, the dark back of
        the phone along the cheek, the hand wrapped round it; the head leans into it. side +1 = character's left hand."""
        pre = 'hl_' if side > 0 else 'hr_'
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            self._arm(P, side, w, 0.0, -20.0, 40.0, 'grip', up=1.0, prop='phone')
            setattr(P, pre + 'ear', max(getattr(P, pre + 'ear'), w))
            P.h_tilt += tilt * side * w
            P.shrug += 0.08 * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def press_bodycam(self, t, on=True, side=-1):
        b = self.sp['body']; press = t + 0.42
        def fn(P, tt):
            w = _env(tt, t, t + 0.6, 0.4, 0.42, ease)
            if w > 0:
                poke = 6.0 * math.exp(-((tt - press) / 0.06) ** 2)
                self._arm(P, side, w, -(b['sh'] - 17) + 12, 70.0, 92.0 - poke, 'point', up=0.92, rot=-12 * side)
                P.h_nod += 0.08 * w
            P.cam_on = (1.0 if on else 0.0) if tt >= press else (0.0 if on else 1.0)
        self._add(t - 1.0, None, fn)
        return [self._ev(press, 'bodycam_beep', -2.0)]

    def hold_up(self, prop, t0, t1, side=-1):
        def fn(P, t):
            w = _env(t, t0, t1, 0.5, 0.45, ease)
            if w <= 0: return
            bob = 3.0 * noise1(t * 1.3, self.seed + 9)
            self._arm(P, side, w, -(self.sp['body']['sh'] - 17) * 0.45, -105.0 + bob, 240.0, 'grip', up=1.0, prop=prop)
            P.h_nod += 0.04 * w
        self._add(t0, t1 + 0.5, fn)
        name = {'card': 'paper', 'notebook': 'paper', 'photo': 'paper', 'radio': 'radio_click', 'phone': 'ui_pop', 'pen': 'pen_click'}.get(prop)
        return [self._ev(t0 + 0.1, name, -6.0)] if name else []

    def hand_on_glass(self, t0, t1, side=1, reach=470.0):
        contact = t0 + 0.55
        def fn(P, t):
            w = _env(t, t0, t1, 0.55, 0.45, ease)
            if w <= 0: return
            pr = clamp((t - contact) / 0.12) * (1.0 - prog(t, t1, t1 + 0.15))
            slide = 4.0 * noise1(t * 0.8, self.seed + 21) * pr
            self._arm(P, side, w, -(self.sp['body']['sh'] - 17) * 0.6, -125.0 + slide, reach, 'flat', up=1.0, press=pr)
            P.lean += 0.12 * w; P.h_nod -= 0.04 * w
        self._add(t0, t1 + 0.5, fn)
        return [self._ev(contact, 'knock_door', -12.0, n=1, soft=True)]

    def point(self, t0, t1, side=-1, dx=1.0, dy=0.0):
        def fn(P, t):
            w = _env(t, t0, t1, 0.4, 0.4, ease)
            self._arm(P, side, w, 160.0 * dx * side if dx else 20.0, -40.0 + 200.0 * dy, 220.0, 'point', up=0.0,
                      rot=-90.0 * side)
        return self._add(t0, t1 + 0.4, fn)

    def sit(self, t0, t1=None, fade=0.6):
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            P.sit = lerp(P.sit, 1.0, w)
            for side in (-1, 1):
                self._arm(P, side, w, -48.0, 292.0, 150.0, 'mitt', up=0.0)
            P.thumb = math.sin(t * 5.5) * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def walk(self, t0, t1, x_from, x_to, facing=None, surface='porch', ramp=0.35):
        d = x_to - x_from
        units = abs(d) / (self.height / 1000.0)
        cycles = units / 440.0
        face = facing if facing is not None else (1.0 if d >= 0 else -1.0)
        dur = t1 - t0
        def u_of(t):
            # constant speed with short accelerations: integral of a trapezoid speed profile
            r = min(ramp, dur / 2)
            vmax = 1.0 / (dur - r)
            if t <= t0: return 0.0
            if t >= t1: return 1.0
            x = t - t0
            if x < r: return vmax * x * x / (2 * r)
            if x > dur - r: y = dur - x; return 1.0 - vmax * y * y / (2 * r)
            return vmax * (r / 2 + (x - r))
        def fn(P, t):
            u = u_of(t)
            w = _env(t, t0 - 0.35, t1, 0.45, 0.45, ease)
            P.dx = x_from + d * u
            P.walk_amt = max(P.walk_amt, clamp(_env(t, t0, t1, ramp, ramp)) * (1.0 if dur > 0 else 0))
            P.walk_ph = cycles * u
            P.turn = lerp(P.turn, face, w)
            P.lean += 0.05 * P.walk_amt
        if not getattr(self, '_walked', False):          # stand at the start point before the first walk
            self._walked = True
            self.clips.append((-INF, t0 - 0.5, lambda P, t: setattr(P, 'dx', x_from), False))
        self._add(t0 - 0.5, None, fn)
        # heel strikes at every half cycle
        evs = []
        ts = np.linspace(t0, t1, 600)
        us = np.array([u_of(x) for x in ts]) * cycles * 2.0
        for k in range(1, int(math.floor(cycles * 2.0)) + 1):
            i = int(np.searchsorted(us, k))
            if 0 < i < len(ts):
                evs.append(self._ev(float(ts[i]), 'footsteps_wood_inside' if surface == 'inside' else 'footsteps_porch', -2.0,
                                    pan=0.0, n=1, foot='L' if k % 2 else 'R'))
        return evs

    # ------------------------------------------------------------------ emotional beats
    def cry(self, t0, t1=None, smile=False, fade=1.2):
        d = EXPR['grin_cry' if smile else 'cry']
        rng = np.random.default_rng(self.seed + 555)
        sobs = []
        tt = t0 + 0.8
        end = (t1 if t1 is not None else t0 + 60.0)
        while tt < end:
            sobs.append(tt); tt += rng.uniform(1.1, 1.9)
        def fn(P, t):
            w = _env(t, t0, t1, fade, 0.8)
            if w <= 0: return
            tears = ease_in_out(prog(t, t0, t0 + 2.2))
            P.mix(d, w); P.tears = max(P.tears, tears * w)
            pulse = 0.0
            for s in sobs:
                if s - 0.1 <= t <= s + 0.6:
                    pulse = max(pulse, ease_out_cubic(prog(t, s - 0.1, s)) * (1 - ease_in_out(prog(t, s, s + 0.6))))
            P.shrug += 0.35 * pulse * w; P.h_nod += 0.07 * pulse * w; P.m_open += (0.0 if smile else 0.15) * pulse * w
            P.blink = max(P.blink, 0.4 * pulse * (0 if smile else 1))
        self._add(t0, None if t1 is None else t1 + 0.8, fn)
        return [self._ev(s, 'breath', -8.0, kind='sob') for s in sobs if t1 is None or s < t1]

    def scream(self, t0, t1, fade=0.12):
        d = EXPR['scream']
        def fn(P, t):
            w = _env(t, t0, t1, fade, 0.35, ease_out_cubic)
            if w <= 0: return
            P.mix(d, w)
            P.h_tilt += (3.5 * math.sin(t * 37.0) + 2.0 * noise1(t * 11, self.seed + 31)) * w
            P.h_dx += 2.5 * noise1(t * 19, self.seed + 32) * w
            P.shrug += 0.3 * w; P.lean -= 0.06 * w; P.jitter = w
        return self._add(t0, t1 + 0.4, fn)

    def _mouth_target(self, dx=0.0, dz=60.0, side=1):
        """(out, down) arm targets that put the hand at the mouth (+dx toward the hand side, body units)."""
        sp = self.sp; hh = sp['hh']; b = sp['body']
        mouth = -hh / 2 + sp['mouth_y'] * hh / 240.0
        return dx - (b['sh'] - 17), mouth + 30.0 - 64.0

    def hand_to_mouth(self, t0, t1=None, side=-1, fade=0.45, shock=True):
        """A hand comes up over the mouth (fingers up, back of the hand to the lens): shock, a stifled sob. The head
        dips into it, the eyes go wide. Works in busts and full body."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            out, down = self._mouth_target(6.0, side=side)
            self._arm(P, side, w, out, down + 30.0, 70.0, 'relaxed', up=1.0, rot=side * 6.0)
            P.h_nod += 0.06 * w; P.shrug += 0.12 * w
            if shock: P.wide = max(P.wide, 0.6 * w); P.brow_up = max(P.brow_up, 0.5 * w); P.pupil = min(P.pupil, 1.0 - 0.4 * w)
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def wipe_tears(self, t0, side=1, dur=1.3):
        """The back of the fingers wipes under one eye and out across the cheek, the head tilting into the hand."""
        def fn(P, t):
            w = _env(t, t0, t0 + dur - 0.4, 0.35, 0.4, ease)
            if w <= 0: return
            u = ease_in_out(prog(t, t0 + 0.35, t0 + dur - 0.4))
            out, down = self._mouth_target(0.0, side=side)
            hw = self.sp['hh'] * 100.0 / 240.0
            self._arm(P, side, w, out + hw * (0.15 + 0.55 * u), down - 34.0, 70.0, 'relaxed', up=1.0, rot=-side * (20.0 + 35.0 * u))
            P.h_tilt += 7.0 * side * w; P.h_nod += 0.05 * w
            P.blink = max(P.blink, 0.6 * w * (1 - u))
        return self._add(t0, t0 + dur + 0.2, fn)

    def glasses_off(self, t0, t1=None, side=1):
        """Takes the glasses off (mum): the hand goes to the temple, the glasses come away at t0 + 0.55 and stay held at
        chest height (t1 None = for good; at t1 they go back on). Pose.specs flags them on the face."""
        off = t0 + 0.55
        back = None if t1 is None else t1
        def fn(P, t):
            w_up = _env(t, t0, off, 0.4, 0.35, ease)
            on_face = t < off or (back is not None and t >= back + 0.45)
            P.specs = 1.0 if on_face else 0.0
            out, down = self._mouth_target(0.0, side=side)
            hw = self.sp['hh'] * 100.0 / 240.0
            if w_up > 0 and t < off + 0.35:
                self._arm(P, side, w_up, out + hw * 0.75, down - 52.0, 60.0, 'grip', up=1.0)
            if not on_face:
                w = _env(t, off, back, 0.45, 0.45, ease)
                self._arm(P, side, w, out + hw * 0.2, down + 120.0, 130.0, 'grip', up=0.9, prop='glasses' if w > 0.3 else None)
            if back is not None and back - 0.1 <= t < back + 0.6:
                w2 = _env(t, back, back + 0.2, 0.3, 0.3, ease)
                self._arm(P, side, w2, out + hw * 0.75, down - 52.0, 60.0, 'grip', up=1.0)
        return self._add(t0, None if t1 is None else t1 + 1.0, fn)

    def flinch(self, t, amp=1.0):
        """Startle on a hit / knock: the head jerks back and down, shoulders up, eyes squeeze shut for 2 frames, then a
        wide-eyed settle."""
        def fn(P, tt):
            tau = tt - t
            if tau < 0 or tau > 0.9: return
            k = math.exp(-tau * 6.5) * (1 - math.exp(-tau * 40.0))
            P.h_nod -= 0.12 * amp * k; P.h_dy += 6.0 * amp * k; P.shrug += 0.45 * amp * k; P.lean -= 0.05 * amp * k
            P.h_tilt += 4.0 * amp * k * (1 if hash01(int(t * 10), self.seed) > 0.5 else -1)
            if tau < 0.07: P.blink = max(P.blink, 1.0)
            P.wide = max(P.wide, 0.7 * amp * math.exp(-tau * 3.0)); P.pupil = min(P.pupil, 1.0 - 0.4 * amp * k)
        return self._add(t - 0.05, t + 1.0, fn, real=True)

    def creep(self, t0, t1, tilt=8.0, jerk_at=None, side=None, sway=5.0):
        """One-call weird beat for a held creepy shot: a slow over-long head tilt drifting over the whole shot (to `tilt`
        deg), a weight shift with sway, and a jerk at jerk_at (default 55 % through; None-able via jerk_at=False).
        Breathing continues. Typical: a.creep(s.t0, s.t1) on every officer door / peep shot."""
        sd = side if side is not None else (1.0 if hash01(int(t0 * 10), self.seed + 77) > 0.5 else -1.0)
        dur = max(0.5, t1 - t0)
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t1))
            w = _env(t, t0 - 0.2, t1, 0.3, 0.4)
            P.h_tilt += tilt * sd * u * w
            P.h_dx -= 0.25 * tilt * sd * u * w
            v = ease_in_out(prog(t, t0 + dur * 0.15, t0 + dur * 0.45))
            P.sway += sway * sd * v * w; P.tilt += 0.6 * sd * v * w
        self._add(t0 - 0.3, t1 + 0.5, fn)
        if jerk_at is not False:
            self.jerk(t0 + dur * 0.55 if jerk_at is None else jerk_at, 0.7)
        return self

    def impatient(self, t0, dur=2.6, side=1):
        """'He looks impatient': weight shift, a glance away toward the street (side), a sharp look back at the lens and a
        twitch on arrival."""
        g0, g1 = t0 + 0.5, t0 + dur * 0.62
        def fn(P, t):
            w = _env(t, t0, t0 + dur, 0.4, 0.4)
            if w <= 0: return
            P.sway += 6.0 * side * ease_in_out(prog(t, t0, t0 + 0.6)) * w
            gl = ease_out_cubic(prog(t, g0, g0 + 0.3)) * (1.0 - spring(t - g1, 3.4, 0.5) if t >= g1 else 1.0)
            P.h_turn += 0.55 * side * gl
            P.lock = lerp(P.lock, 0.0, gl); P.look_x += 0.7 * side * gl
            P.brow_angry += 0.3 * w; P.m_press += 0.4 * w
        self._add(t0 - 0.2, t0 + dur + 0.5, fn)
        self.twitch([g1 + 0.12], 0.8)
        return self

    def nervous_glance(self, t0, n=2, side=-1, dur=1.4):
        starts = [t0 + i * dur / n for i in range(n)]
        def fn(P, t):
            w = _env(t, t0, t0 + dur, 0.2, 0.3)
            if w <= 0: return
            g = 0.0
            for s in starts:
                g = max(g, ease_out_cubic(prog(t, s, s + 0.06)) * (1 - ease_in_out(prog(t, s + 0.42, s + 0.5))))
                b = t - (s + 0.5)
                if 0 <= b < 0.067: P.blink = max(P.blink, clamp(min(1.0, b / 0.017, (0.067 - b) / 0.017)))
            head = 0.0
            for s in starts:
                head = max(head, ease_in_out(prog(t, s + 0.08, s + 0.3)) * (1 - ease_in_out(prog(t, s + 0.45, s + 0.7))))
            P.lock = lerp(P.lock, 0.0, w)
            P.look_x = lerp(P.look_x, 0.85 * side, g); P.look_y = lerp(P.look_y, 0.05, g)
            P.h_turn += 0.16 * side * head
            P.mix(dict(brow_sad=0.6, m_press=0.5, pupil=0.85), w * 0.8)
        return self._add(t0 - 0.2, t0 + dur + 0.5, fn)

    def twitch(self, times, amp=1.0):
        times = [times] if isinstance(times, (int, float)) else list(times)
        dirs = [(1 if hash01(i, self.seed + 61) > 0.5 else -1, hash01(i, self.seed + 62) * 2 - 1) for i in range(len(times))]
        def fn(P, t):
            for (ti, (d1, d2)) in zip(times, dirs):
                tau = t - ti
                if 0 <= tau < 0.6:
                    f = math.exp(-tau * 9.0) * math.sin(tau * 46.0)
                    P.h_tilt += 11.0 * amp * f * d1
                    P.h_dx += 7.0 * amp * f * d2
                    P.shrug += 0.3 * amp * abs(f)
                    P.look_x += 0.25 * f * d2
                    P.brow_asym += 0.7 * f * d1
                    P.m_side += 0.7 * f * d1
                    P.blink = max(P.blink, clamp(1.0 - tau / 0.07) if tau < 0.07 else 0.0)
        return self._add(min(times) - 0.1, max(times) + 0.7, fn, real=True)

    def freeze(self, t0, t1):
        """Total stillness: every non-realtime clip, breathing and noise hold their t0 values until t1."""
        self.freezes.append((t0, t1))
        return self._add(t0, t1, lambda P, t: setattr(P, 'still', 1.0) if t0 <= P.t <= t1 else None, real=True)

    def jerk(self, t, amp=1.0):
        self.twitch([t], 1.8 * amp)
        def fn(P, tt):
            tau = tt - t
            if 0 <= tau < 0.8:
                k = math.exp(-tau * 7.0)
                P.h_nod += -0.12 * k * amp; P.wide += 0.5 * k; P.pupil *= 1 - 0.35 * k
        return self._add(t - 0.1, t + 0.9, fn, real=True)

    def blink(self, t, dur=0.067):
        """Forced blink: shut in 17 ms, held, open by t + dur (1-2 frames at 30 fps)."""
        def fn(P, tt):
            d = tt - t
            if 0 <= d <= dur:
                e = min(1.0, d / 0.017, (dur - d) / 0.017)
                P.blink = max(P.blink, clamp(e))
        return self._add(t - 0.05, t + dur + 0.05, fn, real=True)

    def blink_burst(self, t0, n=4, dur=1.0):
        """Nervous burst: n quick blinks inside dur seconds (hotel reference: 4 blinks in 1 s)."""
        for i in range(n): self.blink(t0 + i * dur / max(1, n))
        return self

    def life(self, t0, t1=None, amount=0.0, fade=0.3):
        """Scale the v2.1 idle life (drift, re-settles, weight shifts, micro twitches, shiver) over a window."""
        return self.set(t0, t1, fade, life=amount)

    # ------------------------------------------------------------------ delivery film clips
    def _shoulder_y(self):
        return -1000.0 + self.sp['hh'] + 44.0 + 20.0                      # shoulder joint (body units, feet = 0)

    def smile_stage(self, t0, stage, t1=None, fade=0.4):
        """Driver: hold a smile stage (DRIVER_STAGES key) over a window, on top of the film-time arc. Mister Winks: a
        WINKS_STAGES key (0..5, 'show', 'tape', 'owen', 'asleep')."""
        d = (self.sp.get('stages') or DRIVER_STAGES)[stage]
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))

    def smile_arc(self, arc=DRIVER_ARC):
        """Set (or with None switch off) the film-time smile arc that sits under every clip (the driver has it by default)."""
        self._arc = arc or None
        return self

    def eye_flash(self, t0, dur=0.5, peak=1.0):
        """Eyeshine: the pupils catch the porch light and shine white like an animal's (rise 60 ms, hold, fall 150 ms).
        Returns a 'stinger' event (params kind='eye_flash')."""
        def fn(P, t):
            if t < t0 or t > t0 + dur + 0.2: return
            u = min(prog(t, t0, t0 + 0.06), 1.0 - prog(t, t0 + dur - 0.05, t0 + dur + 0.15))
            P.eyeshine = max(P.eyeshine, peak * ease_out_cubic(u)); P.still = max(P.still, 0.9)
        self._add(t0 - 0.1, t0 + dur + 0.3, fn, real=True)
        return [self._ev(t0, 'stinger', -6.0, kind='eye_flash')]

    def reach(self, t0, t1=None, side=1, out=200.0, down=60.0, fwd=150.0, shape='grip', up=0.0, fade=0.45, prop=None, rot=None):
        """Generic reach: the hand goes to (out, down, fwd) body units from its shoulder (out away from the body, down from
        the shoulder, fwd toward the character's front) and holds until t1 (None = for good)."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w > 0: self._arm(P, side, w, out, down, fwd, shape, up=up, prop=prop, rot=rot)
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def carry_tablet(self, t0=-1e9, t1=None, side=1, fade=0.4):
        """Driver: the tablet held loosely at his side in one hand (its back to the lens)."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease) if t0 > -1e8 else (1.0 if t1 is None else _env(t, -1e9, t1, 0.0, fade))
            if w <= 0: return
            sw = 4.0 * noise1(t * 0.5, self.seed + 4)
            self._arm(P, side, w, 22.0, 292.0 + sw, 46.0, 'grip', up=0.0, prop='tablet_back')
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def hold_tablet_up(self, t0, t1, side=1, screen='sign', height=0.0):
        """Driver: raises the tablet to the lens, screen to the camera ("so you can see the empty line"); height > 0 lifts
        it toward eye level (default: the top edge at his chin, so the grin and the stare stay above the screen).
        pose.tablet_screen = screen while it is up. Returns a soft cloth rustle."""
        b = self.sp['body']
        def fn(P, t):
            w = _env(t, t0, t1, 0.55, 0.5, ease)
            if w <= 0: return
            bob = 3.0 * noise1(t * 1.1, self.seed + 9)
            self._arm(P, side, w, -(b['sh'] - 17) * 0.55, 135.0 - 150.0 * height + bob, 330.0, 'grip', up=1.0, prop='tablet')
            if w >= 0.5: P.tablet_screen = screen
            P.h_nod += 0.03 * w; P.lock = lerp(P.lock, 1.0, w)
        self._add(t0, t1 + 0.6, fn)
        return [self._ev(t0 + 0.08, 'cloth_rustle', -7.0), self._ev(t1 + 0.05, 'cloth_rustle', -9.0)]   # final mix: was -12 / -14, masked

    def ring_bell(self, t0, side=0.0, hand=None, hold=0.3):
        """Rings the doorbell. side 0: the bell is the doorbell camera itself: the index finger comes AT the lens from
        below (growing ~1.3x) and presses; side +-1: a button beside the door at shoulder height. Returns the
        doorbell_chime event (params kind='ding_dong') at the press."""
        hs = hand if hand is not None else (int(math.copysign(1, side)) if side else -1)
        b = self.sp['body']
        press = t0 + 0.45
        def fn(P, t):
            w = _env(t, t0, press + hold, 0.4, 0.4, ease)
            if w <= 0: return
            pk = math.exp(-((t - press) / 0.07) ** 2)
            if side:
                self._arm(P, hs, w, 300.0 * 0.82 + 20.0 * pk, -10.0, 70.0, 'point', up=0.1)
                P.turn += 0.08 * side * w; P.h_turn -= 0.08 * side * w
            else:                                   # the fingertip rises into the bottom of the doorbell frame, huge
                k = ease_in_out(prog(t, t0, press))
                self._arm(P, hs, w, 30.0 - (b['sh'] - 17), 150.0 - 40.0 * k, 360.0 + 60.0 * pk, 'point', up=0.95)
                setattr(P, ('hl_' if hs > 0 else 'hr_') + 'scale', 1.0 + 1.5 * k * w + 0.25 * pk)
                P.lean += 0.04 * w; P.h_nod += 0.06 * w
            P.lock = lerp(P.lock, 1.0, w)
        self._add(t0, press + hold + 0.5, fn)
        return [self._ev(press, 'doorbell_chime', 0.0, kind='ding_dong', pan=0.0)]

    def tap_label(self, t0, n=2, side=1, spacing=0.42, target=(250.0, 60.0, 80.0)):
        """Driver: index finger taps the box's shipping label (the box stands beside him on `side`). Returns box_tap events."""
        out, down, fwd = target
        taps = [t0 + 0.55 + i * spacing for i in range(n)]
        end = taps[-1] + 0.5
        def fn(P, t):
            w = _env(t, t0, end - 0.3, 0.45, 0.45, ease)
            if w <= 0: return
            pk = 0.0
            for h in taps:
                d = t - h
                if -0.1 <= d < 0: pk = max(pk, ease_in_cubic(prog(d, -0.1, 0)))
                elif 0 <= d < 0.16: pk = max(pk, 1.0 - ease_out_cubic(d / 0.16))
            self._arm(P, side, w, out + 16.0 * pk, down, fwd, 'point', up=0.15)
            P.turn += 0.12 * side * w; P.h_turn -= 0.1 * side * w; P.tilt += 1.5 * side * w
        self._add(t0, end + 0.5, fn)
        return [self._ev(h, 'box_tap', -8.0, pan=0.3 * side) for h in taps]

    def tilt_box(self, t0, t1, side=1, reach=(210.0, -95.0, 40.0)):
        """Driver: a hand on top of the box pulls it over so the label faces the camera (pair with BoxActing.tilt)."""
        out, down, fwd = reach
        def fn(P, t):
            w = _env(t, t0, t1, 0.45, 0.45, ease)
            if w <= 0: return
            u = ease_in_out(prog(t, t0 + 0.35, t0 + 1.0))
            self._arm(P, side, w, out - 30.0 * u, down + 10.0 * u, fwd, 'open', up=0.5, rot=-side * 70.0)
            P.tilt += 2.0 * side * w; P.turn += 0.1 * side * w; P.h_turn -= 0.1 * side * w
        self._add(t0, t1 + 0.5, fn)
        return [self._ev(t0 + 0.45, 'box_creak', -5.0, pan=0.3 * side)]                 # final mix: was -10, masked

    def lean_close(self, t0, dur=2.2, t1=None, tilt=7.0, side=1, amount=1.0):
        """Driver: leans right up to the lens ("he's talking to her now"), head tilted, stare locked (lean_in + tilt)."""
        self.lean_in(t0, dur, t1, amount)
        self.head_tilt(t0 + 0.3, tilt * side, dur * 1.3, t1)
        return self

    def listen_tilt(self, t0, t1=None, side=1, angle=24.0, dur=1.7):
        """Tilts his head like he's listening to a voice somewhere else; the eyes drift up and aside, everything stills."""
        self.head_tilt(t0, angle * side, dur, t1)
        def fn(P, t):
            w = _env(t, t0, t1, 0.8, 0.6)
            if w <= 0: return
            P.lock = lerp(P.lock, 0.35, w); P.look_x += 0.4 * side * w; P.look_y -= 0.25 * w
            P.still = max(P.still, w)
        return self._add(t0, None if t1 is None else t1 + 0.6, fn)

    def slow_look_side(self, t0, dur=3.2, side=1, back=None, amount=0.85):
        """His head turns slowly toward the side of the house (too slow, the body does not follow), eyes leading; at
        `back` it snaps back to the lens (snap_turn)."""
        def fn(P, t):
            u = ease_in_out(prog(t, t0, t0 + dur))
            if u <= 0: return
            ue = ease_out_cubic(prog(t, t0 - 0.2, t0 + 0.4))
            P.h_turn += amount * side * u; P.lock = lerp(P.lock, 0.0, ue)
            P.look_x += 0.6 * side * ue; P.still = max(P.still, 1.0)
        self._add(t0 - 0.3, None if back is None else back + 0.2, fn)
        if back is not None: self.snap_turn(back, None, 0.0, hold=0.1)
        return self

    def look_at_box(self, t0, t1, side=1):
        """Looks down at the box beside him (head nods and turns, eyes down), then back up at t1."""
        def fn(P, t):
            w = _env(t, t0, t1, 0.5, 0.45, ease)
            if w <= 0: return
            P.h_nod += 0.42 * w; P.h_turn += 0.28 * side * w; P.lock = lerp(P.lock, 0.0, w)
            P.look_y += 0.65 * w; P.look_x += 0.3 * side * w
        return self._add(t0, t1 + 0.5, fn)

    def set_box_down(self, t0, dur=1.8, side=1):
        """Driver: takes the tall box by its sides, dips at the knees and stands it against the door. Returns box_drop
        (soft thud) and box_scrape (across the welcome mat) events; pair with BoxActing.slide."""
        b = self.sp['body']
        def fn(P, t):
            w = _env(t, t0, t0 + dur, 0.45, 0.5, ease)
            if w <= 0: return
            u = prog(t, t0, t0 + dur)
            dip = math.sin(PI * clamp((u - 0.15) / 0.7))
            P.turn += 0.32 * side * w; P.lean += 0.18 * dip * w; P.crouch += 0.45 * dip * w
            self._arm(P, side, w, 170.0, 90.0 + 70.0 * dip, 150.0, 'open', up=0.0, rot=side * 70.0)
            self._arm(P, -side, w, -(b['sh'] - 17) * 1.75, 200.0 + 60.0 * dip, 230.0, 'open', up=0.0, rot=-side * 60.0)
            P.h_nod += 0.3 * dip * w; P.lock = lerp(P.lock, 0.0, dip * w)
        self._add(t0, t0 + dur + 0.5, fn)
        return [self._ev(t0 + dur * 0.62, 'box_drop', -4.0, pan=0.2 * side), self._ev(t0 + dur * 0.72, 'box_scrape', -6.0, dur=0.8)]

    def take_photo(self, t0, side=1, dur=1.6):
        """Driver: raises the tablet, its back camera toward the box / door, and takes a photo (the flash LED fires at us).
        pose.tablet_flash pulses. Returns a camera_shutter event."""
        b = self.sp['body']; snap = t0 + dur * 0.55
        def fn(P, t):
            w = _env(t, t0, t0 + dur, 0.45, 0.45, ease)
            if w <= 0: return
            self._arm(P, side, w, -(b['sh'] - 17) * 0.4, 120.0, 260.0, 'grip', up=1.0, prop='tablet_back')
            P.tablet_flash = max(P.tablet_flash, math.exp(-((t - snap) / 0.05) ** 2))
            P.h_nod += 0.18 * w; P.lock = lerp(P.lock, 0.0, w)
        self._add(t0, t0 + dur + 0.5, fn)
        return [self._ev(snap, 'camera_shutter', -4.0)]

    def walk_away(self, t0, t1, surface='porch', cadence=1.9, turn_dur=0.5):
        """Turns his back (0.5 s) and walks in place (the layer path moves him away). Returns footstep events."""
        n = max(2, int(round((t1 - t0) * cadence)))
        def fn(P, t):
            w = ease_in_out(prog(t, t0 - turn_dur, t0))
            P.turn = lerp(P.turn, 2.0, w)
            amt = _env(t, t0, t1, 0.3, 0.3)
            P.walk_amt = max(P.walk_amt, amt); P.walk_ph = (n / 2.0) * prog(t, t0, t1); P.lean += 0.05 * amt
        self._add(t0 - turn_dur - 0.2, None, fn)
        name = 'footsteps_wood_inside' if surface == 'inside' else 'footsteps_porch'
        return [self._ev(t0 + (t1 - t0) * (k - 0.5) / n, name, -4.0, n=1, foot='L' if k % 2 else 'R') for k in range(1, n + 1)]

    def climb_in(self, t0, dur=1.2):
        """Steps up into the van cab (back view): knee up, lean in, the body rises. Returns a step and the cab door."""
        def fn(P, t):
            u = prog(t, t0, t0 + dur)
            if u <= 0: return
            k = math.sin(PI * clamp(u / 0.6))
            P.walk_amt = max(P.walk_amt, 0.8 * k); P.walk_ph = 0.75
            P.lean += 0.25 * ease_in_out(u); P.bob -= 70.0 * ease_in_out(clamp((u - 0.3) / 0.6))
        self._add(t0, None, fn)
        return [self._ev(t0 + dur * 0.45, 'van_step', -6.0), self._ev(t0 + dur + 0.35, 'car_door_close', -3.0)]

    def reach_up(self, t0, t1=None, side=1, prop='tablet', stretch=0.0, grow=2.5, screen='sign', fade=0.6):
        """Holds the tablet up overhead to a high window (on tiptoe, head back, looking up). stretch > 0 lets the arm grow
        unnaturally long over `grow` seconds (1.0 = twice its length) to reach a second-floor sill."""
        b = self.sp['body']
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            st_ = stretch * ease_in_out(prog(t, t0 + 0.3, t0 + 0.3 + grow))
            L = 348.0 * b.get('arm_k', 1.0) * (1.0 + st_)
            setattr(P, ('hl_' if side > 0 else 'hr_') + 'stretch', st_ * w)
            self._arm(P, side, w, 40.0, -0.97 * L, 50.0, 'grip', up=1.0, prop=prop, rot=0.0)
            self._arm(P, -side, w * 0.8, 70.0, 250.0, 40.0, 'open', up=0.0)
            if w >= 0.5: P.tablet_screen = screen
            P.tiptoe = max(P.tiptoe, w); P.h_nod -= 0.38 * w; P.lock = lerp(P.lock, 0.0, w)
            P.look_y -= 0.85 * w; P.tilt += 2.0 * side * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    # --- mom
    def squint_light(self, t0, t1=None, fade=0.6):
        """Mom coming down the stairs: squinting at the light, half asleep."""
        d = dict(squint=0.75, brow_angry=0.15, brow_sad=0.3, eye_open=0.8, pupil=0.95, smile=-0.1)
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))

    def reach_chain(self, t0, t1=None, side=1, reach=(120.0, -110.0, 250.0), shake=0.7):
        """Mom's hand goes up to the door chain (grip at head height toward the door) and shakes; let go at t1. Returns
        chain rattles at the grab and the release."""
        out, down, fwd = reach
        grab = t0 + 0.6
        def fn(P, t):
            w = _env(t, t0, t1, 0.55, 0.5, ease)
            if w <= 0: return
            self._arm(P, side, w, out, down, fwd, 'grip', up=1.0)
            setattr(P, ('hl_' if side > 0 else 'hr_') + 'shake', max(getattr(P, ('hl_' if side > 0 else 'hr_') + 'shake'), shake * w))
            P.lean += 0.08 * w; P.turn += 0.15 * side * w
            P.lock = lerp(P.lock, 0.0, w); P.look_x += 0.5 * side * w; P.look_y -= 0.2 * w
        self._add(t0, None if t1 is None else t1 + 0.5, fn)
        ev = [self._ev(grab, 'chain_lock', -5.0, kind='rattle', pan=0.3 * side)]          # final mix: -10 / -14 were masked
        if t1 is not None: ev.append(self._ev(t1 + 0.05, 'chain_lock', -9.0, kind='rattle', pan=0.3 * side))
        return ev

    def hands_over_mouth(self, t0, t1=None, fade=0.4, sob=True):
        """Both hands pressed over her mouth (the box speaks with dad's voice): fingers up, one over the other, eyes wide
        and wet, shoulders up."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            for side, dx, dd in ((-1, 4.0, 26.0), (1, 16.0, 40.0)):
                out, down = self._mouth_target(dx, side=side)
                self._arm(P, side, w, out, down + dd, 74.0 + 6.0 * (side > 0), 'relaxed', up=1.0, rot=side * 10.0)
            P.h_nod += 0.08 * w; P.shrug += 0.22 * w
            P.wide = max(P.wide, 0.75 * w); P.brow_up = max(P.brow_up, 0.6 * w); P.brow_sad = max(P.brow_sad, 0.8 * w)
            P.pupil = min(P.pupil, 1.0 - 0.45 * w); P.wet = max(P.wet, w); P.tears = max(P.tears, 0.6 * w * prog(t, t0 + 0.6, t0 + 2.5))
        self._add(t0, None if t1 is None else t1 + fade, fn)
        return [self._ev(t0 + 0.25, 'breath', -8.0, kind='gasp')]

    def shaking_hand(self, t0, t1=None, side=1, amount=1.0, fade=0.3):
        """A hand that will not stop shaking (pose hl_shake / hr_shake)."""
        key = ('hl_' if side > 0 else 'hr_') + 'shake'
        return self._add(t0, None if t1 is None else t1 + fade,
                         lambda P, t: setattr(P, key, max(getattr(P, key), amount * _env(t, t0, t1, fade, fade))))

    def sit_floor(self, t0, t1=None, fade=1.0):
        """Sits on the hallway floor with her back to the wall, knees up, hands on the knees."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            if w <= 0: return
            P.floor = max(P.floor, w)
            for side in (-1, 1):
                self._arm(P, side, w, -10.0, 300.0, 250.0, 'relaxed', up=0.0)
            P.h_nod += 0.1 * w; P.shrug += 0.1 * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def tremble(self, t0, t1=None, amp=1.0):
        """Fear tremble: fast head jitter (8-12 Hz), shoulder shiver, nervous blink bursts (the film's police tremble)."""
        def fn(P, t):
            if t < t0 or (t1 is not None and t > t1): return
            P.h_dx += 1.2 * amp * math.sin(t * 61.0) + 0.8 * amp * noise1(t * 9.0, self.seed + 77)
            P.h_tilt += 0.9 * amp * math.sin(t * 47.0 + 1.0)
            P.shrug += 0.04 * amp * (1 + math.sin(t * 23.0))
            P.jitter = max(P.jitter, 0.35 * amp)
        self._add(t0 - 0.5, None if t1 is None else t1 + 0.5, fn, real=True)
        if self.blink_rate > 0:
            k = t0 + 0.35; end = t1 if t1 is not None else t0 + 30.0
            while k < end - 0.3:
                nb = 2 + int(hash01(int(k * 10), self.seed) * 3)
                self.blink_burst(k, nb, 0.12 * nb)
                k += 1.1 + 0.8 * float(hash01(int(k * 7), self.seed + 3))
        return self

    # --- Lily
    def lean_out(self, t0, t1=None, side=-1, reach_t=None, amount=1.0, fade=0.8):
        """Lily leans out of her open window toward someone below, one small hand reaching down to touch the tablet at
        reach_t (returns a touch_tap event there). Head bowed to look down, innocent."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            P.lean += 0.5 * amount * w; P.h_nod += 0.32 * w
            k = ease_in_out(prog(t, reach_t - 0.6, reach_t)) if reach_t is not None else 0.6
            self._arm(P, side, w, 50.0, 230.0 + 40.0 * k, 200.0 + 60.0 * k, 'point', up=0.0)
            self._arm(P, -side, w, 10.0, 190.0, 110.0, 'open', up=0.0, rot=side * 30.0)   # the other hand on the sill
            P.mix(dict(brow_sad=0.35, brow_up=0.25, smile=0.12, pupil=1.1, lock=0.0, look_y=0.6), 0.8 * w)
        self._add(t0, None if t1 is None else t1 + fade, fn)
        return [self._ev(reach_t, 'touch_tap', -10.0)] if reach_t is not None else []

    def sleepy(self, t0, t1=None, fade=0.6):
        d = dict(eye_open=0.6, brow_up=0.32, brow_sad=0.3, smile=0.1, pupil=1.15, h_nod=0.07)
        return self._add(t0, None if t1 is None else t1 + fade, lambda P, t: P.mix(d, _env(t, t0, t1, fade, fade)))

    # --- dad (memory)
    def sign(self, t0, t1, side=-1):
        """Signs on a tablet held in front of him with a stylus: small scribbling hand, head bowed over it. Returns a
        touch_tap and a stylus_scribble (params dur)."""
        def fn(P, t):
            w = _env(t, t0, t1, 0.45, 0.4, ease)
            if w <= 0: return
            sc = _env(t, t0 + 0.5, t1 - 0.2, 0.1, 0.1)
            dx = 14.0 * math.sin(t * 23.0) * sc; dy = 6.0 * math.sin(t * 31.0 + 1.0) * sc
            self._arm(P, side, w, -60.0 + dx, 170.0 + dy, 220.0, 'grip', up=0.6, prop='stylus')
            P.h_nod += 0.4 * w; P.lock = lerp(P.lock, 0.0, w); P.look_y += 0.75 * w
        self._add(t0, t1 + 0.5, fn)
        return [self._ev(t0 + 0.5, 'touch_tap', -10.0), self._ev(t0 + 0.55, 'stylus_scribble', -12.0, dur=max(0.2, t1 - t0 - 0.75))]

    def drop_keys(self, t0, side=1, release=0.6):
        """The keys in his hand go out over the bowl on the side table and drop at t0 + release (draw_keys_bowl with
        drop = t - (t0 + release)). Returns the keys_drop event at the impact (KEYS_DROP_IMPACT after release)."""
        tr = t0 + release
        def fn(P, t):
            w = _env(t, t0, tr + 0.3, 0.4, 0.5, ease)
            if w <= 0: return
            held = t < tr
            self._arm(P, side, w, 90.0, 190.0, 190.0, 'grip' if held else 'open', up=0.0, prop='keys_dad' if held else None)
            P.h_nod += 0.15 * w; P.h_turn += 0.15 * side * w
        self._add(t0, tr + 1.0, fn)
        return [self._ev(tr + KEYS_DROP_IMPACT, 'keys_drop', -3.0, surface='bowl')]

    # --- you
    def look_at_phone(self, t0, t1=None, side=1, fade=0.45):
        """Phone held in front of the chest, screen to the face, head bowed (light=dict(under='#bcd2ff') for its glow)."""
        b = self.sp['body']
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, ease)
            if w <= 0: return
            self._arm(P, side, w, -(b['sh'] - 17) * 0.45, 150.0, 190.0, 'grip', up=1.0, prop='phone_back')
            P.h_nod += 0.28 * w; P.lock = lerp(P.lock, 0.0, w); P.look_y += 0.7 * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def catch_wrist(self, t0, t1=None, side=1, reach=(200.0, -40.0, 200.0)):
        """Grabs someone's wrist (mom's hand on the chain): a quick reach that grips and holds. Returns a cloth grab."""
        self.reach(t0, t1, side, *reach, shape='grip', up=0.7, fade=0.22)
        return [self._ev(t0 + 0.2, 'cloth_rustle', -8.0, kind='grab')]

    def hold_close(self, t0, t1=None, side=1):
        """An arm round the person beside him (holding mom while the box talks)."""
        return self.reach(t0, t1, side, 120.0, 20.0, 160.0, 'relaxed', up=0.0, fade=0.6)

    def push_door(self, t0, side=1):
        """Pushes a door open with a flat hand. Returns door_creak."""
        self.reach(t0, t0 + 1.0, side, 30.0, 40.0, 300.0, 'flat', up=1.0, fade=0.3)
        return [self._ev(t0 + 0.35, 'door_creak', -6.0)]

    # ------------------------------------------------------------------ dummy film: Mister Winks
    def _alen(self):
        return 348.0 * self.sp['body'].get('arm_k', 1.0)

    def _hipsz(self):
        """Body units of the sitting drop (pose.perch: y_feet is the surface he sits on)."""
        return 222.0

    def jaw_drop(self, t0, amount=1.0, dur=0.16):
        """The jaw falls open (accelerating, a little bounce at the bottom) and hangs until the next clack(). Returns
        [dummy_jaw] (the hinge bottoming out: a dull wooden knock)."""
        def fn(P, t):
            if t < t0 or any(t0 < tc <= t for tc in self._clacks): return
            u = (t - t0) / dur
            v = ease_in_cubic(min(1.0, u)) if u < 1 else 1.0 + 0.1 * math.exp(-(t - t0 - dur) * 13.0) * math.sin((t - t0 - dur) * 38.0)
            P.jaw = amount * v
        self._add(t0, None, fn)
        return [self._ev(t0 + dur, 'dummy_jaw', -6.0, 0.0, kind='drop')]

    def jaw_hang(self, t0, amount=0.3, fade=0.25):
        """The jaw hangs a little open from t0 (eased) until the next clack()."""
        def fn(P, t):
            if t < t0 or any(t0 < tc <= t for tc in self._clacks): return
            P.jaw = max(P.jaw, amount * ease_in_out(prog(t, t0, t0 + fade)))
        return self._add(t0, None, fn)

    def clack(self, t, dur=0.07):
        """The jaw snaps shut at t (dur > 0.3: "it closes, very slowly. Clack." - a slow rise, then the snap). Overrides any
        hang / drop before it. Returns [dummy_clack]."""
        self._clacks.append(float(t))
        def fn(P, tt):
            if tt < t - dur or tt > t + 0.3: return
            if tt < t:
                u = (tt - (t - dur)) / dur
                k = ease_in_out(u) * 0.82 if dur > 0.3 else ease_in_cubic(u)
                if dur > 0.3 and u > 0.9: k = 0.82 + 0.18 * ease_in_cubic((u - 0.9) / 0.1)
                P.jaw = P.jaw * (1.0 - k)
            else:
                P.jaw = 0.0
                tau = tt - t
                P.h_nod += 0.025 * math.exp(-tau * 18.0) * math.sin(tau * 60.0)
        self._add(t - dur - 0.05, t + 0.35, fn, late=True)
        return [self._ev(t, 'dummy_clack', 0.0, 0.0, kind='snap')]

    def wink(self, t, side=1, hold=0.32):
        """A wooden lid clicks shut over one eye (side +1 = his left, the wink eye), holds, clicks open. Returns
        [eyelid_click x2]."""
        key = 'lid_l' if side > 0 else 'lid_r'
        def fn(P, tt):
            v = clamp((tt - t) / 0.05) * (1.0 - clamp((tt - t - 0.05 - hold) / 0.08))
            if v > 0: setattr(P, key, max(getattr(P, key), v))
        self._add(t - 0.1, t + hold + 0.3, fn, late=True)
        return [self._ev(t + 0.05, 'eyelid_click', -2.0, 0.0, kind='shut'), self._ev(t + 0.05 + hold + 0.08, 'eyelid_click', -8.0, 0.0, kind='open')]

    def blink_click(self, t, hold=0.14):
        """Both lids click shut and open (a doll's blink). Returns [eyelid_click x2]."""
        def fn(P, tt):
            v = clamp((tt - t) / 0.05) * (1.0 - clamp((tt - t - 0.05 - hold) / 0.07))
            if v > 0: P.lid_l = max(P.lid_l, v); P.lid_r = max(P.lid_r, v)
        self._add(t - 0.1, t + hold + 0.3, fn, late=True)
        return [self._ev(t + 0.05, 'eyelid_click', -3.0, 0.0, kind='shut'), self._ev(t + 0.05 + hold + 0.07, 'eyelid_click', -9.0, 0.0, kind='open')]

    def try_wink(self, t, gap=0.7, hold=1.2, reopen=0.9):
        """Owen inside the dummy tries to wink: his left lid clicks shut, then - he can't help it - the right one too
        ("Both of his eyelids close. Click, click."); they stay shut, then creep open. Returns [eyelid_click x2]."""
        def fn(P, tt):
            a = clamp((tt - t) / 0.05); b = clamp((tt - t - gap) / 0.05)
            r = 1.0 - ease_in_out(prog(tt, t + gap + hold, t + gap + hold + reopen))
            P.lid_l = max(P.lid_l, a * r); P.lid_r = max(P.lid_r, b * r)
            if t - 0.4 <= tt <= t + gap:                      # the effort: a tiny shudder of the head before each click
                P.h_tilt += 1.6 * math.sin(tt * 70.0) * clamp((tt - t + 0.4) / 0.4)
        self._add(t - 0.5, t + gap + hold + reopen + 0.2, fn, late=True)
        return [self._ev(t + 0.05, 'eyelid_click', 0.0, 0.0, kind='shut'), self._ev(t + gap + 0.05, 'eyelid_click', 0.0, 0.0, kind='shut')]

    def lids(self, t0, t1=None, amount=1.0, fade=0.06, side=0):
        """Hold the wooden lids at `amount` (side 0 both, +1 his left, -1 his right); fade 0.06 = a click."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade, lambda u: u, lambda u: u)
            if w <= 0: return
            if side >= 0: P.lid_l = lerp(P.lid_l, amount, w)
            if side <= 0: P.lid_r = lerp(P.lid_r, amount, w)
        return self._add(t0, None if t1 is None else t1 + fade, fn, late=True)

    def eyes_open(self, t0, dur=1.6):
        """Shut lids creep open over dur, ending on a click (In my arms, Mister Winks opens his eyes). Returns [eyelid_click]."""
        def fn(P, t):
            v = 1.0 - ease_in_out(prog(t, t0, t0 + dur))
            P.lid_l = v if t >= t0 else max(P.lid_l, 1.0); P.lid_r = P.lid_l
        self._add(t0 - 0.5, t0 + dur + 0.1, fn, late=True)
        return [self._ev(t0 + dur, 'eyelid_click', -6.0, 0.0, kind='open')]

    def doll_turn(self, t0, to, dur=1.0, steps=4, frm=None, until=None, body=False):
        """A jerky doll head turn: the head ratchets from `frm` (None = where it is) to `to` (quarter turns, +-2 = all the way
        round) in `steps` hard snaps with a tiny overshoot, dead still between them; holds `to` (until None = for good).
        body=True turns the whole figure instead. Returns [wood_creak per step]."""
        st_ = [t0 + dur * (k + 0.5) / steps for k in range(steps)]
        def fn(P, tt):
            if tt < t0 - 0.05: return
            if until is not None and tt > until + 0.3: return
            f = (P.turn + P.h_turn if body else P.h_turn) if frm is None else frm
            v = f
            for k, ts in enumerate(st_):
                if tt >= ts:
                    tau = tt - ts
                    a = f + (to - f) * k / steps; b = f + (to - f) * (k + 1) / steps
                    v = a + (b - a) * (clamp(tau / 0.05) + 0.12 * math.exp(-tau * 16.0) * math.sin(tau * 45.0) * (tau > 0.05))
            if body: P.turn = v - P.h_turn
            else: P.h_turn = v
            P.lock = max(P.lock, 0.0)
        self._add(t0 - 0.1, None if until is None else until + 0.3, fn, late=True)
        return [self._ev(ts, 'wood_creak', -11.0, 0.0, kind='tick', dur=0.12) for ts in st_]

    def head_turn_180(self, t0, dur=3.2, frm=0.0, to=-2.0, until=None):
        """The slow, smooth, impossible head turn (the body stays put; the eyes stay locked on you). Returns [wood_creak]
        with params dur (one long grinding creak)."""
        def fn(P, tt):
            if tt < t0 - 0.05 or (until is not None and tt > until): return
            u = ease_in_out(prog(tt, t0, t0 + dur))
            P.h_turn = frm + (to - frm) * u
            P.lock = 1.0
        self._add(t0 - 0.1, until, fn, late=True)
        return [self._ev(t0, 'wood_creak', -4.0, 0.0, kind='grind', dur=dur)]

    def head_snap(self, t, to, frm=None, until=None):
        """One hard doll snap of the head to `to` (quarter turns). Returns [wood_creak]."""
        return self.doll_turn(t - 0.03, to, 0.06, 1, frm, until)

    def tick(self, t, tilt=6.0, nod=0.0):
        """A single wooden tick of the head (held): the slightest move that says it is alive. Returns [wood_creak]."""
        def fn(P, tt):
            if tt >= t:
                k = clamp((tt - t) / 0.04) + 0.15 * math.exp(-(tt - t) * 18) * math.sin((tt - t) * 50) * (tt > t + 0.04)
                P.h_tilt += tilt * k; P.h_nod += nod * k
        self._add(t - 0.05, None, fn)
        return [self._ev(t, 'wood_creak', -14.0, 0.0, kind='tick', dur=0.08)]

    def sit_dummy(self, t0=-1e9, t1=None, fade=0.4, hands='knees', slump=0.0):
        """Mister Winks sitting (pose.perch: draw him with y_feet = the seat / lap / step / shelf he sits on; his legs
        dangle below it). hands 'knees' | 'table' (flat on a table in front) | 'limp'. slump tips him a little sideways."""
        L = self._alen()
        tab = {'knees': (-12.0, 0.66 * L, 0.5 * L, 'relaxed'), 'table': (-22.0, 0.42 * L, 0.78 * L, 'relaxed'),
               'limp': (8.0, 0.98 * L, 0.12 * L, 'relaxed')}[hands]
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            if w <= 0: return
            P.sit = lerp(P.sit, 1.0, w); P.perch = lerp(P.perch, 1.0, w)
            for sd in (-1, 1): self._arm(P, sd, w, tab[0], tab[1], tab[2], tab[3], up=0.0)
            P.tilt += 4.0 * slump * w; P.h_tilt += 8.0 * slump * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def glove_lift(self, t0, side=1, height=0.35, dur=1.4, steps=3):
        """One white glove lifts off the table in jerky steps (from the 'table' hands). Returns [wood_creak]."""
        L = self._alen()
        ts = [t0 + dur * (k + 0.3) / steps for k in range(steps)]
        def fn(P, t):
            if t < t0: return
            v = 0.0
            for k, tk in enumerate(ts):
                if t >= tk: v = (k + clamp((t - tk) / 0.07)) / steps
            self._arm(P, side, 1.0, -22.0 + 10.0 * v, (0.42 - height * v) * L, (0.78 - 0.15 * v) * L, 'relaxed', up=0.0, rot=-side * 20 * v)
        self._add(t0, None, fn)
        return [self._ev(ts[0], 'wood_creak', -10.0, 0.0, kind='tick', dur=0.15), self._ev(ts[0] + 0.05, 'cloth_rustle', -14.0, 0.0, kind='glove')]

    def fingers_curl(self, t, side=1):
        """The glove's fingers curl (relaxed -> grip -> fist in two clicks). Returns [wood_creak]."""
        pre = 'hl_' if side > 0 else 'hr_'
        def fn(P, tt):
            if tt >= t + 0.18: setattr(P, pre + 'shape', 'fist')
            elif tt >= t: setattr(P, pre + 'shape', 'grip')
        self._add(t, None, fn, late=True)
        return [self._ev(t, 'cloth_rustle', -14.0, 0.0, kind='glove')]

    def elbow_bend(self, t, side=1, amount=0.3):
        """A jerky bend of the elbow: the forearm comes up off the table. Returns [wood_creak]."""
        L = self._alen()
        def fn(P, tt):
            if tt < t: return
            k = clamp((tt - t) / 0.06) + 0.1 * math.exp(-(tt - t) * 14) * math.sin((tt - t) * 40) * (tt > t + 0.06)
            pre = 'hl_' if side > 0 else 'hr_'
            setattr(P, pre + 'down', getattr(P, pre + 'down') - amount * L * k)
            setattr(P, pre + 'fwd', getattr(P, pre + 'fwd') - 0.1 * L * k)
        self._add(t - 0.05, None, fn)
        return [self._ev(t, 'wood_creak', -10.0, 0.0, kind='tick', dur=0.15)]

    def stand_on_chair(self, t0, dur=1.7, steps=3):
        """Hands flat on the table, he pushes up and stands on the chair seat in jerky steps (draw him with y_feet = the
        seat and perch on: the perch drop follows the sit). Returns [wood_creak x steps, footstep_small]."""
        L = self._alen()
        ts = [t0 + dur * (k + 0.4) / steps for k in range(steps)]
        def fn(P, t):
            if t < t0: return
            v = 0.0
            for k, tk in enumerate(ts):
                if t >= tk: v = (k + ease_out_cubic(clamp((t - tk) / 0.12))) / steps
            P.sit = lerp(P.sit, 0.0, v); P.perch = 1.0
            P.lean += 0.25 * math.sin(PI * v)
            for sd in (-1, 1):
                self._arm(P, sd, 1.0, -22.0, (0.42 + 0.5 * v) * L, (0.78 - 0.55 * v) * L, 'flat' if v < 0.8 else 'relaxed', up=0.0)
        self._add(t0, None, fn)
        ev = [self._ev(tk, 'wood_creak', -8.0, 0.0, kind='tick', dur=0.2) for tk in ts]
        ev.append(self._ev(ts[-1] + 0.12, 'footsteps_wood_inside', -12.0, 0.0, n=1, kind='tiny'))
        return ev

    def torch_on(self, t, ang=0.0, side=1, t1=None, hold='side'):
        """The usher's flashlight clicks on in one glove; ang = beam direction (deg, 0 up, 90 his left / screen right in
        front view, 180 down). hold 'side' (low, beside him), 'up' (pointed at the ceiling), 'lens' (pointed at the
        camera: the glare), 'chin' (under his chin: light the face from below with light=dict(under=...)).
        Returns [flashlight_click]. Draw the beam with draw_torch_beam at torch_pos(...)."""
        L = self._alen()
        tgt = {'side': (12.0, 0.8 * L, 0.3 * L), 'up': (0.42 * L, 0.3 * L, 0.45 * L), 'lens': (-30.0, 0.45 * L, 0.85 * L),
               'chin': (-60.0, -0.05 * L, 0.45 * L)}[hold]
        def fn(P, tt):
            w = _env(tt, t - 0.6, t1, 0.4, 0.3)
            if w <= 0: return
            self._arm(P, side, w, tgt[0], tgt[1], tgt[2], 'grip', up=0.0, prop='flashlight')
            P.torch = 1.0 if (tt >= t and (t1 is None or tt < t1)) else 0.0
            P.torch_ang = ang; P.torch_lens = 1.0 if hold == 'lens' else 0.0
        self._add(t - 0.6, None if t1 is None else t1 + 0.3, fn)
        ev = [self._ev(t, 'flashlight_click', -6.0, 0.0, kind='on')]
        if t1 is not None: ev.append(self._ev(t1, 'flashlight_click', -9.0, 0.0, kind='off'))
        return ev

    def torch_sweep(self, t0, t1, a0, a1):
        """Swing the beam from a0 to a1 degrees (eased) over [t0, t1]."""
        def fn(P, t):
            if P.torch > 0 or getattr(P, 'hl_prop') == 'flashlight' or getattr(P, 'hr_prop') == 'flashlight':
                P.torch_ang = a0 + (a1 - a0) * ease_in_out(prog(t, t0, t1))
        return self._add(t0, None, fn, late=True)

    def puppet(self, t0, t1, look=1.0, rate=1.0, talk_bob=True):
        """Being worked on a lap (the hospital, the 1974 show, Owen's act): lively puppet head moves - turns between the
        operator (look -1/+1 = which side he sits) and the audience, nods, a cheeky tilt - every 0.6-1.4 s."""
        rng = np.random.default_rng(self.seed + 71)
        keys, tt = [(t0, 0.0, 0.0, 0.0)], t0
        while tt < t1:
            tt += rng.uniform(0.6, 1.4) / rate
            r = rng.uniform()
            keys.append((tt, look * 0.7 if r < 0.35 else rng.uniform(-0.25, 0.25), rng.uniform(-10, 12), rng.uniform(-0.12, 0.1)))
        kt = [k[0] for k in keys]
        def fn(P, t):
            w = _env(t, t0, t1, 0.3, 0.3)
            if w <= 0: return
            i = max(0, _bisect.bisect_right(kt, t) - 1)
            a = keys[max(0, i - 1)]; b = keys[i]
            u = ease_out_back(clamp((t - b[0]) / 0.22)) if i > 0 else 1.0
            P.h_turn += (a[1] + (b[1] - a[1]) * u) * w
            P.h_tilt += (a[2] + (b[2] - a[2]) * u) * w
            P.h_nod += (a[3] + (b[3] - a[3]) * u) * w
            P.lock = lerp(P.lock, 0.3, w)
        return self._add(t0, t1 + 0.3, fn)

    def carried(self, t0=-1e9, t1=None, fade=0.4, recline=-66.0, look_up=True):
        """Limp in someone's arms (draw with draw_carry): cradled, tipped back by `recline` degrees (0 = upright, held
        against the chest), legs dangling over the arm, arms hanging, the head lolling a little; look_up: the face tips
        up toward the one holding him."""
        L = self._alen()
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            if w <= 0: return
            P.sit = lerp(P.sit, 0.85, w); P.perch = lerp(P.perch, 1.0, w); P.recline = lerp(P.recline, recline, w)
            for sd in (-1, 1): self._arm(P, sd, w, 18.0, 0.95 * L, 0.1 * L, 'relaxed', up=0.0)
            P.h_tilt += (3.0 * math.sin(t * 1.3) + 4.0 * P.sec_x) * w
            if look_up: P.h_nod -= 0.25 * w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def fall_face_down(self, t0, dur=0.45):
        """He drops face down on the rug (pose.lie 0 -> 1 with a bounce). Returns [dummy_thud]."""
        def fn(P, t):
            if t < t0: return
            u = clamp((t - t0) / dur)
            P.lie = ease_in_cubic(u) + (0.04 * math.exp(-(t - t0 - dur) * 10) * math.sin((t - t0 - dur) * 30) if u >= 1 else 0.0)
            P.turn = lerp(P.turn, 1.0, ease_out_cubic(clamp(u * 2.2))); P.h_turn *= 1.0 - u; P.sit = 0.15 * (1 - u)
            L = self._alen()
            for sd in (-1, 1): self._arm(P, sd, 1.0, 10.0, 0.9 * L, 0.1 * L, 'relaxed', up=0.0)
        self._add(t0, None, fn, late=True)
        return [self._ev(t0 + dur, 'dummy_thud', 0.0, 0.0, kind='rug')]

    def face_down(self, t0=-1e9, t1=None):
        """Lying face down on the rug (pose.lie 1)."""
        L = self._alen()
        def fn(P, t):
            if t < t0 or (t1 is not None and t > t1): return
            P.lie = 1.0; P.turn = 1.0; P.h_turn = 0.0; P.sit = 0.0
            for sd in (-1, 1): self._arm(P, sd, 1.0, 10.0, 0.9 * L, 0.1 * L, 'relaxed', up=0.0)
        return self._add(t0, t1, fn, late=True)

    def paper_out(self, t0, dur=1.2):
        """The torn P.S. slides out of the slot in his back (pose.slot_paper; seen in back views). Returns [paper]."""
        self.set(t0, None, dur, slot_paper=1.0)
        return [self._ev(t0 + 0.1, 'paper', -8.0, 0.0, kind='slide', dur=dur)]

    # ------------------------------------------------------------------ dummy film: the family
    def open_latches(self, t0, side_gap=0.22):
        """Mom pops the case's two brass latches with her thumbs (hands forward at hip height). Returns [case_latch x2]."""
        L = self._alen()
        def fn(P, t):
            w = _env(t, t0 - 0.5, t0 + 1.2, 0.45, 0.6)
            if w <= 0: return
            for sd in (-1, 1):
                pop = math.exp(-max(0.0, t - (t0 + (0.0 if sd < 0 else side_gap))) * 12.0) * (t >= t0 + (0.0 if sd < 0 else side_gap))
                self._arm(P, sd, w, -40.0, 0.72 * L - 18 * pop, 0.5 * L, 'grip', up=0.0, rot=sd * 8.0 * pop)
            P.h_nod += 0.22 * w; P.lean += 0.12 * w
        self._add(t0 - 0.5, t0 + 1.9, fn)
        return [self._ev(t0, 'case_latch', -2.0, -0.15), self._ev(t0 + side_gap, 'case_latch', -2.0, 0.15)]

    def smell_mug(self, t0, t1=None, side=-1, pale_at=None):
        """Mom lifts the mug to her nose, breathes in; at pale_at (default t0 + 1.6) all the colour leaves her face."""
        L = self._alen(); pa = t0 + 1.6 if pale_at is None else pale_at
        def fn(P, t):
            w = _env(t, t0, t1, 0.6, 0.6)
            if w > 0:
                out, down = self._mouth_target(4.0, side=side)
                self._arm(P, side, w, out + 10.0, down + 6.0, 0.36 * L, 'grip', up=0.0, prop='mug')
                P.h_nod += 0.1 * w; P.squint = max(P.squint, 0.25 * w * (1 - clamp((t - pa) / 0.3)))
            k = ease_in_out(prog(t, pa, pa + 1.2))
            if k > 0: P.pale = max(P.pale, 0.85 * k); P.wide = max(P.wide, 0.6 * k); P.pupil = min(P.pupil, 1 - 0.45 * k); P.brow_up += 0.4 * k
        self._add(t0, None, fn)
        return [self._ev(t0 + 0.5, 'breath', -12.0, 0.0, kind='sniff'), self._ev(pa + 0.2, 'breath', -8.0, 0.0, kind='gasp')]

    def hold_mug(self, t0=-1e9, t1=None, side=1, sip=None):
        """A mug in one hand at chest height (the new Owen's coffee); sip = [t] mug to the mouth."""
        L = self._alen()
        def fn(P, t):
            w = _env(t, t0, t1, 0.4, 0.4)
            if w <= 0: return
            up_ = 0.0
            for ts in (sip or []):
                up_ = max(up_, _env(t, ts, ts + 1.3, 0.5, 0.5))
            out, down = self._mouth_target(2.0, side=side)
            self._arm(P, side, w, lerp(-20.0, out + 6.0, up_), lerp(0.62 * L, down + 8.0, up_), lerp(0.42 * L, 0.32 * L, up_), 'grip', up=0.0, prop='mug')
            P.h_nod += 0.08 * up_ * w
        self._add(t0, None if t1 is None else t1 + 0.4, fn)
        return [self._ev(ts + 0.6, 'sip', -12.0, 0.0) for ts in (sip or [])]

    def pull_dummy(self, t0, t1, pulls=3):
        """Mom grabs the dummy with both hands at chest height and pulls, leaning back in jerks (draw the dummy between her
        hands with lap_anchor / draw_lap). Returns [cloth_rustle per pull]."""
        L = self._alen()
        ts = [t0 + 0.4 + (t1 - t0 - 0.6) * k / max(1, pulls) for k in range(pulls)]
        def fn(P, t):
            w = _env(t, t0, t1, 0.3, 0.5)
            if w <= 0: return
            jerk = max([math.exp(-max(0.0, t - tk) * 5.0) * (t >= tk) for tk in ts] + [0.0])
            for sd in (-1, 1): self._arm(P, sd, w, -34.0 - 10 * jerk, (0.62 - 0.1 * jerk) * L, (0.78 - 0.2 * jerk) * L, 'grip', up=0.0)
            P.lean += (0.3 - 0.32 * jerk) * w; P.hunch += 0.25 * w; P.shrug += 0.2 * jerk * w
        self._add(t0, t1 + 0.5, fn)
        return [self._ev(tk, 'cloth_rustle', -6.0, 0.0, kind='grab') for tk in ts]

    def grab_keys(self, t0, side=1):
        """Mom snatches her keys off a side table (reach out and down, back to the chest). Returns [keys_jangle]."""
        L = self._alen()
        def fn(P, t):
            w_out = _env(t, t0, t0 + 0.35, 0.3, 0.35); w_back = ease_in_out(prog(t, t0 + 0.5, t0 + 0.9))
            if t < t0: return
            if t < t0 + 0.65: self._arm(P, side, w_out, 0.35 * L, 0.75 * L, 0.3 * L, 'grip', up=0.0)
            else: self._arm(P, side, w_back, -10.0, 0.62 * L, 0.32 * L, 'grip', up=0.0, prop='key')
        self._add(t0, None, fn)
        return [self._ev(t0 + 0.4, 'keys_drop', -8.0, 0.3 * side, kind='jangle')]

    def laugh_soft(self, t0, dur=1.6):
        """A tired little laugh (mom at the letter): a smile, a head shake, the shoulders bounce twice."""
        def fn(P, t):
            w = _env(t, t0, t0 + dur, 0.25, 0.6)
            if w <= 0: return
            P.mix(dict(smile=0.7, teeth=0.4, squint=0.35, brow_sad=0.3), w)
            P.h_turn += 0.06 * math.sin((t - t0) * 9.0) * w; P.shrug += 0.12 * abs(math.sin((t - t0) * 11.0)) * w
        return self._add(t0, t0 + dur + 0.6, fn)

    def snort(self, t):
        """Owen snorts at the joke - he can't help it, he's nine: head jerks, eyes squeeze, a hand flies to his nose.
        Returns [snort]."""
        def fn(P, tt):
            k = math.exp(-max(0.0, tt - t) * 4.0) * (tt >= t - 0.05)
            if k < 0.01: return
            P.h_nod += 0.18 * k; P.shrug += 0.3 * k
            P.mix(dict(smile=0.8, teeth=0.6, squint=0.8, blink=0.7, brow_up=0.3), clamp(k * 1.4))
        self._add(t - 0.1, t + 1.5, fn)
        self.hand_to_mouth(t + 0.08, t + 1.1, side=-1, fade=0.18, shock=False)
        return [self._ev(t, 'snort', 0.0, 0.0)]

    def try_wink_kid(self, t, hold=0.5):
        """Owen tries to wink: both eyes squeeze shut (the left a beat first), the cheek bunches, the mouth pulls sideways."""
        def fn(P, tt):
            a = _env(tt, t, t + hold, 0.06, 0.12); b = _env(tt, t + 0.05, t + hold, 0.08, 0.12)
            if a <= 0 and b <= 0: return
            P.lid_l = max(P.lid_l, a); P.lid_r = max(P.lid_r, b)
            P.squint = max(P.squint, 0.5 * a); P.m_side += 0.8 * a; P.smile = max(P.smile, 0.45 * a); P.brow_asym += 0.6 * a
        return self._add(t - 0.1, t + hold + 0.3, fn)

    def jump_hug(self, t0, side=0):
        """Owen jumps up out of the chair and throws his arms round Mom (arms up and forward, a hop). Returns [footsteps]."""
        L = self._alen()
        def fn(P, t):
            if t < t0: return
            u = prog(t, t0, t0 + 0.35)
            P.sit = lerp(P.sit, 0.0, ease_out_cubic(u))
            hop = math.sin(PI * clamp((t - t0 - 0.2) / 0.35)) * (t < t0 + 0.55)
            P.bob -= 40.0 * hop
            w = ease_out_cubic(prog(t, t0 + 0.2, t0 + 0.6))
            for sd in (-1, 1): self._arm(P, sd, w, 30.0, 0.18 * L, 0.75 * L, 'relaxed', up=0.0)
            P.mix(dict(smile=1.0, teeth=1.0, grin=0.25, brow_up=0.5), w)
        self._add(t0, None, fn)
        return [self._ev(t0 + 0.55, 'footsteps_wood_inside', -6.0, 0.0, n=1)]

    def wave(self, t0, t1, side=1, rate=2.4):
        """A hand up, waving side to side (Owen at the window as the van pulls away)."""
        L = self._alen()
        def fn(P, t):
            w = _env(t, t0, t1, 0.4, 0.5)
            if w <= 0: return
            self._arm(P, side, w, 0.2 * L + 0.12 * L * math.sin((t - t0) * rate * 2 * PI), -0.25 * L, 0.25 * L, 'open', up=1.0,
                      rot=side * 18.0 * math.sin((t - t0) * rate * 2 * PI))
        return self._add(t0, t1 + 0.5, fn)

    def doorway_smile(self, t0, dur=4.0):
        """The new Owen in your doorway: he looks at you a long time (no blink), then the smile comes, slow and too still."""
        def fn(P, t):
            if t < t0: return
            P.mix(dict(lock=1.0, pupil=0.62, still=0.9, wide=0.2), 1.0)
            k = ease_in_out(prog(t, t0 + dur * 0.55, t0 + dur))
            P.mix(dict(smile=1.0, grin=0.12, m_press=0.5, teeth=0.0, squint=0.0, brow_up=0.0, wide=0.3, pupil=0.55), k)
        return self._add(t0, None, fn)

    def kneel(self, t0, t1=None, fade=0.7):
        """You kneel down (crouch, one knee to the floor) in front of Owen's chair."""
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            if w > 0: P.crouch = lerp(P.crouch, 1.25, w); P.lean += 0.12 * w; P.kneel = w
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def grab_dummy(self, t0, t1=None, fade=0.25):
        """Both hands shoot out and grab the dummy in front, low (on the stairs). Returns [cloth_rustle]."""
        L = self._alen()
        self.reach(t0, t1, -1, -20.0, 0.62 * L, 0.72 * L, 'grip', fade=fade)
        self.reach(t0 + 0.04, t1, 1, -20.0, 0.62 * L, 0.72 * L, 'grip', fade=fade)
        self.set(t0, t1, fade, lean=0.25, h_nod=0.12)
        return [self._ev(t0 + fade, 'cloth_rustle', -4.0, 0.0, kind='grab')]

    def hand_inside(self, t0, t1=None, side=1, depth=1.0, fade=0.6):
        """Your hand pushes in through the slot in his back (the arm reaches forward and down; the dummy, drawn over it,
        hides the hand). Returns [cloth_rustle]."""
        L = self._alen()
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            if w <= 0: return
            push = ease_in_out(prog(t, t0, t0 + fade * 1.6))
            self._arm(P, side, w, -36.0, 0.55 * L, (0.42 + 0.22 * push * depth) * L, 'flat', up=0.0)
            P.lean += 0.1 * w
        self._add(t0, None if t1 is None else t1 + fade, fn)
        return [self._ev(t0 + fade * 0.8, 'cloth_rustle', -10.0, 0.0, kind='slot')]

    def squeezed(self, times):
        """Your reaction to each squeeze from inside: a small flinch through the arm and the face (three = I love you).
        Returns [hand_squeeze per time]."""
        times = [times] if isinstance(times, (int, float)) else list(times)
        def fn(P, t):
            for ti in times:
                tau = t - ti
                if 0 <= tau < 0.5:
                    k = math.exp(-tau * 9.0)
                    P.shrug += 0.12 * k; P.wide += 0.4 * k; P.h_nod -= 0.04 * k
        self._add(min(times) - 0.1, max(times) + 0.6, fn, real=True)
        return [self._ev(ti, 'hand_squeeze', -10.0, 0.0) for ti in times]

    def hold_dummy(self, t0=-1e9, t1=None, fade=0.5):
        """You hold the dummy cradled in your arms at the waist (draw him with draw_carry; he reclines along your arms):
        your right forearm under his knees, the left behind his back. Your head bows to look down at him."""
        L = self._alen()
        self.reach(t0, t1, -1, 0.05 * L, 0.5 * L, 0.42 * L, 'grip', fade=fade)
        self.reach(t0, t1, 1, -0.3 * L, 0.66 * L, 0.5 * L, 'relaxed', fade=fade)
        return self.set(t0, t1, fade, h_nod=0.32)

    def clamp_mouth(self, t0, t1=None, side=1, reach_x=0.6):
        """Your hand clamps over Owen's mouth beside you (reach across at his face height). Returns [cloth_rustle]."""
        L = self._alen()
        self.reach(t0, t1, side, reach_x * L, 0.28 * L, 0.3 * L, 'flat', up=1.0, fade=0.2)
        return [self._ev(t0 + 0.2, 'cloth_rustle', -8.0, 0.4 * side, kind='grab')]

    def spin_around(self, t0, to=2.0, dur=0.32):
        """You spin round (a fast whole-body turn with an overshoot). Returns [whoosh]."""
        def fn(P, t):
            if t < t0: return
            P.turn = to * ease_out_back(clamp((t - t0) / dur))
        self._add(t0, None, fn, late=True)
        return [self._ev(t0, 'whoosh', -8.0, 0.0, kind='soft')]

    def tuck_in(self, t0, t1=None):
        """Grandpa (memory) leans down over the bed, a hand on the blanket."""
        L = self._alen()
        self.reach(t0, t1, 1, -30.0, 0.85 * L, 0.55 * L, 'open', fade=0.8)
        return self.set(t0, t1, 0.8, lean=0.35, hunch=0.4, h_nod=0.2)

    def squeeze_hand(self, t0, n=3, gap=0.42, side=1):
        """Grandpa's hand squeezes three times (I love you): small grip pulses. Returns [hand_squeeze x n]."""
        ts = [t0 + k * gap for k in range(n)]
        pre = 'hl_' if side > 0 else 'hr_'
        def fn(P, t):
            for tk in ts:
                if tk <= t < tk + 0.18: setattr(P, pre + 'shape', 'fist')
        self._add(t0, ts[-1] + 0.3, fn, late=True)
        return [self._ev(tk, 'hand_squeeze', -12.0, 0.0) for tk in ts]

    def grab_wrist(self, t0, t1=None, side=1):
        """The real Walter grabs your wrist so hard it hurts: his hand shoots out from the bed. Returns [cloth_rustle]."""
        L = self._alen()
        self.reach(t0, t1, side, 0.15 * L, 0.42 * L, 0.78 * L, 'grip', fade=0.14)
        self.set(t0, t1, 0.2, lean=0.18, shrug=0.25)
        return [self._ev(t0 + 0.14, 'cloth_rustle', -2.0, 0.3 * side, kind='grab')]

    def in_bed(self, t0=-1e9, t1=None, fade=0.4):
        """Half sitting up against hospital pillows (the blanket is the set's: draw it over his legs)."""
        L = self._alen()
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            if w <= 0: return
            P.sit = lerp(P.sit, 1.0, w); P.lean = lerp(P.lean, -0.22, w)
            for sd in (-1, 1): self._arm(P, sd, w, -10.0, 0.75 * L, 0.38 * L, 'relaxed', up=0.0)
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def vent_pose(self, t0=-1e9, t1=None, side=1, fade=0.4, free='thigh'):
        """A ventriloquist sitting with the figure on his knee `side` (+1 his left): the hand on that side goes in at the
        figure's back (hidden by him), the other rests on his own thigh (free='thigh') or on the figure's knee
        (free='dummy': then draw_lap(..., free_arm=True) draws it over the figure). Draw them together with draw_lap."""
        L = self._alen()
        def fn(P, t):
            w = _env(t, t0, t1, fade, fade)
            if w <= 0: return
            P.sit = lerp(P.sit, 1.0, w); P.stance = lerp(P.stance, 1.3, w)
            self._arm(P, side, w, 0.05 * L, 0.5 * L, 0.3 * L, 'flat', up=0.0)               # inside the figure's back
            if free == 'dummy': self._arm(P, -side, w, -0.45 * L, 0.72 * L, 0.55 * L, 'relaxed', up=0.0)
            else: self._arm(P, -side, w, 0.0, 0.82 * L, 0.42 * L, 'relaxed', up=0.0)
        return self._add(t0, None if t1 is None else t1 + fade, fn)

    def showman(self, t0, t1, look=1.0):
        """Young Walter on the 1974 show: the big fixed TV smile, eyes on the camera, the head turning to the figure on
        his knee and back on the beats. His lips never move."""
        rng = np.random.default_rng(self.seed + 31)
        ks, tt = [], t0
        while tt < t1:
            tt += rng.uniform(1.2, 2.4); ks.append(tt)
        def fn(P, t):
            w = _env(t, t0, t1, 0.4, 0.4)
            if w <= 0: return
            P.mix(dict(smile=1.0, grin=0.5, teeth=1.0, brow_up=0.3, m_open=0.0, pupil=0.75, lock=0.8), w)
            look_ = 0.0
            for i, k in enumerate(ks):
                if i % 2 == 0: look_ = max(look_, _env(t, k, k + 0.9, 0.2, 0.25))
            P.h_turn += look * 0.45 * look_ * w; P.lock = lerp(P.lock, 1.0 - look_, w)
        return self._add(t0, t1 + 0.4, fn)

    # ------------------------------------------------------------------ speech
    def talk(self, intervals, text=None, intensity=1.0, env='auto', words='auto', lead=0.02, lag=None):
        """Mouth shapes for speech. intervals: [(t0, t1)] or [(t0, t1, text)]; text applies to a single interval.
        v2.1: the mouth opening follows the real voice: env='auto' samples the vo_en.wav RMS envelope (shut below
        -40 dBFS, opening rising with the level, normalised per line); words='auto' places each word's visemes inside its
        own ASR window (asr_cache en_words), so shapes land on the right syllables. env=None / words=None fall back to
        evenly spread syllables. During a grin the jaw drops on top of the grin (talks through the teeth); during
        shout/scream (m_open >= 0.5) the opening modulates around the base.
        Delivery: lag (s) delays the whole mouth behind the voice ("the words come first, the lips catch up"); None = the
        cast default (driver 0.2 s, everyone else 0)."""
        intensity = intensity * self.sp.get('talk', 1.0)
        lag = self.sp.get('talk_lag', 0.0) if lag is None else float(lag)
        E = voice_envelope() if (isinstance(env, str) and env == 'auto') else env
        W = voice_words() if (isinstance(words, str) and words == 'auto') else (words or [])
        wt = [w_[1] for w_ in W]
        keys, ivs = [], []
        for k, iv in enumerate(intervals):
            t0, t1 = float(iv[0]), float(iv[1])
            txt = iv[2] if len(iv) > 2 else (text if len(intervals) == 1 else None)
            segs = []
            if W:
                j0 = _bisect.bisect_left(wt, t0 - 0.08); j1 = _bisect.bisect_left(wt, t1 - 0.03)
                for j in range(j0, j1):
                    ws = W[j][1]; we = min(W[j + 1][1] if j + 1 < len(W) else t1, t1, ws + 0.85)
                    if we - ws > 0.04: segs.append((W[j][0], ws, we))
            keys.extend(self._visemes_timed(segs, k) if segs else self._visemes(t0, t1, txt, k))
            ref = None
            if E is not None and not callable(E):
                seg = E[max(0, int(t0 * ENV_FPS)):max(0, int(t1 * ENV_FPS))]
                if len(seg) > 3: ref = max(float(np.percentile(seg, 95)), -30.0)
            elif E is not None:
                ref = max(max(_env_db(E, t0 + (t1 - t0) * q / 12.0) for q in range(13)), -30.0)
            ivs.append((t0, t1, ref))
        keys.sort(key=lambda k_: k_[0])
        kt = [k_[0] for k_ in keys]
        ivs.sort(key=lambda v: v[0])
        it0 = [v[0] for v in ivs]
        lo = min((float(iv[0]) for iv in intervals), default=0.0); hi = max((float(iv[1]) for iv in intervals), default=0.0)
        FLOOR = -40.0
        dummy = bool(self.sp.get('dummy'))

        def fn(P, t):
            if not keys or t < kt[0] - 0.1 or t > kt[-1] + 0.2: return
            i = _bisect.bisect_right(kt, t) - 1
            if i < 0: a = b = keys[0]; u = 0.0
            elif i >= len(keys) - 1: a = b = keys[-1]; u = 0.0
            else:
                a, b = keys[i], keys[i + 1]
                u = ease((t - a[0]) / max(1e-3, b[0] - a[0]))
            ov = lerp(a[1], b[1], u); wd = lerp(a[2], b[2], u); rd = lerp(a[3], b[3], u)
            te = lerp(a[4], b[4], u); pr = lerp(a[5], b[5], u); acc = lerp(a[6], b[6], u)
            j = max(0, _bisect.bisect_right(it0, t + 0.06) - 1)
            t0_, t1_, ref = ivs[j]
            if ref is not None:
                gate = _env(t, t0_ - 0.06, t1_ + 0.02, 0.05, 0.12)
                if gate <= 0: on = 0.0
                else:
                    db = _env_db(E, t + lead)
                    on = clamp((db - FLOOR) / max(6.0, ref - FLOOR)) ** 1.35 * gate
                vf = clamp(ov / 0.6)
                o = on * (0.55 + 0.45 * vf) * 0.68 * intensity
                acc = max(acc * 0.5, clamp((on - 0.78) * 4.0))
                pr *= 1.0 - clamp(on * 3.0)
            else:
                o = ov * intensity; on = clamp(ov / 0.6)
            if dummy:                                                 # Mister Winks: the hinged jaw drops and snaps
                if ref is not None and not callable(E):
                    # syllable by syllable: open near each local peak of the voice, snap shut in each valley
                    tq = t + lead
                    i0 = max(0, int((tq - 0.11) * ENV_FPS)); i1 = max(i0 + 2, int((tq + 0.11) * ENV_FPS))
                    seg = E[i0:i1]
                    if len(seg) < 2: return
                    db = _env_db(E, tq)
                    loc = (db - float(seg.min())) / max(5.0, float(seg.max()) - float(seg.min()))
                    drive = clamp(on / 0.35) * clamp((loc - 0.42) / 0.3)
                else:
                    drive = clamp(ov / 0.55)
                jw = drive * drive * (3.0 - 2.0 * drive)
                P.jaw = max(P.jaw, jw * (0.62 + 0.38 * clamp(on)) * intensity)
                P.h_nod += 0.03 * acc
                return
            base = P.m_open; g = clamp(P.grin)
            if base >= 0.5:                                           # shout / scream: modulate around the base
                P.m_open = clamp(base - 0.27 * intensity * (1.0 - on) * (1.0 if ref is not None else 0.6), 0.0, 1.0)
            else:
                P.m_open = base + 0.34 * on * intensity * g + max(0.0, o - base) * (1.0 - g)
            kk = 1.0 - 0.6 * g
            P.m_round = lerp(P.m_round, rd, 0.85 * (1.0 - 0.7 * g))
            P.m_wide += wd * 0.6 * kk
            P.teeth = max(P.teeth, te * 0.8)
            P.m_press = max(P.m_press, pr)
            P.h_nod += 0.035 * acc; P.brow_up += 0.12 * acc
        if dummy and keys:                                             # every time the jaw snaps shut: a wooden clack
            prev, opened, last = 0.0, 0.0, -9.0
            for tt in np.arange(lo - 0.1, hi + 0.3, 1.0 / 120.0):
                Pq = Pose(); fn(Pq, float(tt)); j = Pq.jaw
                opened = max(opened, j)
                if prev >= 0.12 and j < 0.12 and opened > 0.45 and tt - last > 0.14:
                    self._ev(float(tt) + lag, 'dummy_clack', -14.0 + 6.0 * clamp((opened - 0.45) / 0.4), 0.0, kind='speech')
                    last = float(tt); opened = 0.0
                if j < 0.05: opened = min(opened, 0.0) if prev < 0.05 else opened
                prev = j
        if lag:
            return self._add(lo - 0.2 + lag, hi + 0.3 + lag, lambda P, t: fn(P, t - lag))
        return self._add(lo - 0.2, hi + 0.3, fn)

    def talk_lines(self, lines, who='O', intensity=1.0, fx=None):
        """Talk on every timeline.json line spoken by `who` (a code or a tuple of codes; fx: only lines with that fx), using
        each line's t, end and en text. Mister Winks: talk_lines(lines, ('K', 'U', 'R', 'G'), fx=...) as the shot needs."""
        codes = (who,) if isinstance(who, str) else tuple(who)
        iv = [(l['t'], l['end'], l.get('en')) for l in lines if l.get('who') in codes and l.get('end') and (fx is None or l.get('fx') == fx)]
        return self.talk(iv, intensity=intensity) if iv else self

    def _visemes_timed(self, segs, k):
        """Viseme keys from [(word, t_start, t_end)]: each word's syllables share its own window."""
        R = VISEMES['rest']
        keys = [(segs[0][1] - 0.06,) + R + (0.0,)]
        for wi, (wd, ws, we) in enumerate(segs):
            syl = _syllables(_re.sub(r"[^A-Za-z']", '', wd) or 'a')
            sl = []
            for si, (on, vo) in enumerate(syl):
                sl.append([1.0 + (0.35 if len(vo) > 1 else 0.0), _onset_vis(on), _vowel_vis(vo), 1.0 if (si == 0 and len(syl) > 1) else 0.0])
            tot = sum(x[0] for x in sl) or 1.0
            dur = max(0.05, we - ws - 0.02)
            tt = ws
            for i, (wgt, on, vo, st) in enumerate(sl):
                d = wgt * dur / tot
                amp = (0.8 + 0.3 * hash01(i + 7 * wi + 31 * k, self.seed + 3)) * (1.1 if st else 1.0)
                if on:
                    v = VISEMES[on]; keys.append((tt + 0.1 * d, v[0], v[1], v[2], v[3], v[4], st))
                v = VISEMES[vo]
                keys.append((tt + (0.45 if on else 0.3) * d, v[0] * amp, v[1], v[2], v[3], v[4], st))
                tt += d
            nxt = segs[wi + 1][1] if wi + 1 < len(segs) else None
            if nxt is None or nxt - we > 0.12:
                keys.append((min(we, ws + dur) + 0.02, R[0] + 0.05, R[1], R[2], R[3], 0.2, 0.0))
        keys.append((segs[-1][2] + 0.06,) + R + (0.0,))
        return keys

    def _visemes(self, t0, t1, txt, k):
        dur = max(0.05, t1 - t0)
        sl = []        # (weight, onset vis, vowel vis, stress, word_end)
        if txt:
            words = _re.findall(r"[A-Za-z']+", txt)
            for wi, wd in enumerate(words):
                syl = _syllables(wd)
                for si, (on, vo) in enumerate(syl):
                    wgt = 1.0 + (0.35 if len(vo) > 1 else 0.0)
                    sl.append([wgt, _onset_vis(on), _vowel_vis(vo), 1.0 if (si == 0 and len(syl) > 1) else 0.0, si == len(syl) - 1])
                if sl: sl[-1][0] += 0.3
        else:
            n = max(1, int(dur * 5.2))
            vs = ['A', 'E', 'O', 'I', 'U', 'A', 'E']
            for i in range(n):
                h = hash01(i + 97 * k, self.seed + 13)
                on = 'M' if hash01(i, self.seed + 14) < 0.18 else ('F' if hash01(i, self.seed + 15) < 0.1 else None)
                sl.append([1.0 + 0.4 * hash01(i, 5), on, vs[int(h * len(vs)) % len(vs)], 1.0 if hash01(i, 6) > 0.8 else 0.0,
                           hash01(i, 7) > 0.65])
        if not sl: return []
        tot = sum(s[0] for s in sl)
        a0 = t0 + 0.03; scale = (dur - 0.08) / tot
        keys = [(t0 - 0.06,) + VISEMES['rest'] + (0.0,)]
        tt = a0
        for i, (wgt, on, vo, st, wend) in enumerate(sl):
            d = wgt * scale
            amp = (0.78 + 0.32 * hash01(i + 11 * k, self.seed + 3)) * (1.12 if st else 1.0)
            if on:
                v = VISEMES[on]; keys.append((tt + 0.08 * d, v[0], v[1], v[2], v[3], v[4], st))
            v = VISEMES[vo]
            keys.append((tt + (0.42 if on else 0.3) * d, v[0] * amp, v[1], v[2], v[3], v[4], st))
            if wend:
                r = VISEMES['rest']; keys.append((tt + 0.92 * d, r[0] + 0.05, r[1], r[2], r[3], 0.2, 0.0))
            tt += d
        keys.append((t1 + 0.05,) + VISEMES['rest'] + (0.0,))
        return keys


# ====================================================================================================== delivery props
KEYS_DROP_IMPACT = 0.24          # s from the release to the keys hitting the bowl (draw_keys_bowl / Acting.drop_keys)


class BoxActing:
    """Timeline of the box (it is a prop, but it acts): knocks from inside that jolt it two-then-one, the driver tilting it
    so the label faces the camera, sliding it across the mat, the tape cut at sunrise.
        b = BoxActing(seed); ev = b.knock(t0)                    # two knocks, a pause, one more (dad's knock)
        ev = b.knock_loop(t0, t1, period=2.4, accel=0.25)        # 'two, then one' over and over, getting faster
        b.tilt(t0, t1, turn=0.6); ev = b.slide(t0, 0.8, dx=-60); b.cut(t)
        draw_box(pen, x, y, h, b.at(t), t=t)
    Events: box_knock (params n_in_pattern, strength; space should be 'outside' or 'doorbell_mic'), box_scrape."""

    def __init__(self, seed=0):
        self.seed = int(seed)
        self.hits = []               # (t, strength)
        self.tilts = []              # (t0, t1, angle, turn)
        self.slides = []             # (t0, dur, dx)
        self.cut_t = None
        self.events = []

    def _ev(self, t, name, gain_db=0.0, pan=0.0, **params):
        e = dict(t=round(float(t), 4), name=name, gain_db=gain_db, pan=pan, params=params, who='box')
        self.events.append(e); return e

    def knock(self, t0, pattern=(2, 1), gap=0.3, pause=0.72, strength=1.0):
        """Knocks from inside: groups separated by `pause` (default two, a pause, one). Returns box_knock events."""
        ev = []; t = t0
        for gi, n in enumerate(pattern):
            for k in range(n):
                st = strength * (1.0 if k == 0 else 0.92)
                self.hits.append((t, st))
                ev.append(self._ev(t, 'box_knock', 0.0 if gi == 0 and k == 0 else -1.0, n_in_pattern=k + 1, group=gi + 1,
                                   strength=st))
                t += gap
            t += pause - gap
        return ev

    def knock_loop(self, t0, t1, period=2.4, accel=0.0, strength=1.0, gap=0.3, pause=0.72):
        """'Two, then one' repeated from t0 to t1; accel 0..0.6 shrinks the period (and the gaps) every cycle."""
        ev = []; t = t0; k = 1.0
        while t < t1:
            ev += self.knock(t, (2, 1), gap * k, pause * k, strength)
            t += period * k; k *= (1.0 - accel * 0.25)
            k = max(k, 0.35)
        return ev

    def tilt(self, t0, t1, angle=7.0, turn=0.6, dur=0.7):
        """Tipped over by angle deg (screen rotation: negative = the top leans to screen left, toward a driver standing on the
        box's left) and turned so the label faces the camera (turn 0..1 of the side view)."""
        self.tilts.append((t0, t1, angle, turn, dur)); return self

    def slide(self, t0, dur=0.8, dx=-60.0):
        """Scraped across the welcome mat by dx design px (at the drawn height). Returns a box_scrape event."""
        self.slides.append((t0, dur, dx))
        return [self._ev(t0, 'box_scrape', -4.0, dur=dur)]

    def cut(self, t):
        self.cut_t = t; return self

    def at(self, t):
        """State dict for draw_box: jolt (rotation deg), bulge 0..1, dx, dy, tilt, turn, cut 0..1."""
        rot = 0.0; bulge = 0.0; dx = 0.0; dy = 0.0
        for (h, st) in self.hits:
            tau = t - h
            if -0.03 <= tau < 1.2:
                if tau < 0: bulge = max(bulge, st * 0.5 * (1 + tau / 0.03)); continue
                env_ = math.exp(-tau * 7.5)
                bulge = max(bulge, st * math.exp(-tau * 11.0))
                rot += st * 1.4 * env_ * math.sin(tau * 38.0 + 0.6) * (1 if hash01(int(h * 10), self.seed) > 0.5 else -1)
                dy -= st * 4.0 * math.exp(-tau * 18.0)
        tl = 0.0; tn = 0.0
        for (t0, t1, ang, turn, dur) in self.tilts:
            w = _env(t, t0, t1, dur, dur, ease_in_out)
            tl += ang * w; tn += turn * w
        for (t0, dur, d) in self.slides:
            u = prog(t, t0, t0 + dur)
            dx += d * (u * u * (3 - 2 * u)) + (1.2 * math.sin(t * 60.0) if 0 < u < 1 else 0.0)
        cut = 0.0 if self.cut_t is None else ease_out_cubic(prog(t, self.cut_t, self.cut_t + 0.6))
        return dict(rot=rot + tl, bulge=clamp(bulge), dx=dx, dy=dy, turn=tn, cut=cut)


def _label(c, x, y, w, h, det, to='', sender='RETURN', t=0.0):
    """The shipping label (box-local coords, top-left x, y)."""
    lab = rect(x, y, w, h)
    c.fill(lab, '#efece2'); c.grad(lab, x, y, x + w, y + h, [(0, '#ffffff', 60), (1, '#c9c2b0', 90)])
    c.fill(rect(x, y, w, h * 0.2), '#1b2236')
    c.fill(minus(oval(x + h * 0.11, y + h * 0.1, h * 0.065), oval(x + h * 0.14, y + h * 0.075, h * 0.058)), '#e9cf7e')
    if det >= 2:
        text(c.cv, 'NIGHTLINE DELIVERY', *c.pt(x + w * 0.56, y + h * 0.14), 900, h * 0.1 * c.s, '#e9cf7e', 255, 0.04, 'center')
        text(c.cv, 'FROM:', *c.pt(x + w * 0.06, y + h * 0.36), 800, h * 0.085 * c.s, '#5a5a5a', 255, 0.03, 'left')
        if sender.lower().startswith('lily'):                 # the next night: 'Lily' in a child's pencil, not print
            pth, _ = _strokes_path(HAND_STROKES['LILY'], x + w * 0.3, y + h * 0.22, w * 0.26, h * 0.17, 1.0, 1.0, 5, t)
            c.line(pth, max(1.4, c.lw * 0.6), '#3a56c8')
        else:
            text(c.cv, sender, *c.pt(x + w * 0.3, y + h * 0.37), 900, h * 0.12 * c.s, '#1d1f26', 255, 0.06, 'left')
        text(c.cv, 'TO:', *c.pt(x + w * 0.06, y + h * 0.58), 800, h * 0.085 * c.s, '#5a5a5a', 255, 0.03, 'left')
        if to:
            pth, _ = _strokes_path(HAND_STROKES['LILY'], x + w * 0.3, y + h * 0.43, w * 0.2, h * 0.16, 1.0, 1.0, 5, t)
            c.line(pth, max(1.2, c.lw * 0.5), '#1a2a6c')
        else:
            c.line(poly([(x + w * 0.27, y + h * 0.6), (x + w * 0.93, y + h * 0.6)], False), c.lw * 0.3, '#5a5a5a')
        c.fill(rrect(x + w * 0.58, y + h * 0.66, w * 0.38, h * 0.1, 2), '#b3262c', 230)
        text(c.cv, 'SIGNATURE REQUIRED', *c.pt(x + w * 0.77, y + h * 0.745), 900, h * 0.05 * c.s, '#ffffff', 255, 0.01, 'center')
    else:
        for k, (yy, ww) in enumerate(((0.33, 0.55), (0.55, 0.7))):
            c.fill(rect(x + w * 0.06, y + h * yy, w * ww, h * 0.07), '#55545a', 220)
        c.fill(rect(x + w * 0.58, y + h * 0.66, w * 0.38, h * 0.1), '#b3262c', 230)
    bars = []
    for k in range(26):
        if hash01(k, 77) > 0.35:
            bx = x + w * 0.06 + k * w * 0.019
            bars.append(rect(bx, y + h * 0.8, w * (0.009 + 0.008 * hash01(k, 78)), h * 0.15))
    c.fill(_multi(bars), '#1d1f26')
    c.line(lab, c.lw * 0.45)


def draw_box(pen, x, y, h, st=None, t=0.0, detail=None, light=None, view=0.45, label=True, to='', sender='RETURN',
             shadow=True, tape=1.0):
    """The tall narrow box from the porch: kraft cardboard almost as tall as the driver (1.6 m), mummified in brown packing
    tape, a Nightline shipping label (FROM: RETURN, the TO line blank). (x, y) = bottom centre on the floor, h = height in
    design px. st = BoxActing.at(t) (or a dict: rot, bulge, dx, dy, turn, cut). view 0..1 shows the right side face
    (doorbell angle), st['turn'] turns the label toward the camera. A knock from inside bulges the front at chest height
    with creases and jolts the whole box; cut 0..1 slits every tape band down the middle (sunrise). light = dict(key='#ffd9a0'
    warm porch light from above (default), rim=..., k=0..1)."""
    st = st or {}
    W = 0.36 * h; D = 0.27 * h
    view = clamp(view - 0.6 * st.get('turn', 0.0), -1, 1)
    fw = W * (1.0 - 0.12 * abs(view)); sd = D * view * 0.7
    det = detail if detail is not None else _auto_detail(pen, h * 0.4)
    c = Ctx(pen, skia.Matrix(), _lw_for(h * 0.45) * 0.9)
    lt = light or {}
    key = lt.get('key', '#ffd9a0'); kk = lt.get('k', 0.55)
    if shadow:
        c.glow(x + st.get('dx', 0) + sd * 0.5, y + 4, fw * 0.95 + abs(sd), h * 0.05, '#000000', 170)
    c = c.sub(x + st.get('dx', 0.0), y + st.get('dy', 0.0), st.get('rot', 0.0))
    b = st.get('bulge', 0.0); by = -0.62 * h
    # faces: front (x -fw/2..fw/2, y -h..0) and side (toward +x if view > 0)
    bw = fw * 0.075 * b
    def edge(xe, sgn):
        return [(xe, 0.0), (xe + sgn * bw * 0.3, by + h * 0.18), (xe + sgn * bw, by), (xe + sgn * bw * 0.3, by - h * 0.16), (xe, -h)]
    L = edge(-fw / 2, -1); R = edge(fw / 2, 1)
    front = smooth(R + L[::-1], True, 0.35)
    kraft, kraft_sh, kraft_dk = '#a8804f', '#7d5c37', '#5c4127'
    if abs(sd) > 1:
        xe = fw / 2 if sd > 0 else -fw / 2
        side = poly([(xe, 0), (xe + sd, -0.05 * abs(sd)), (xe + sd, -h - 0.05 * abs(sd)), (xe, -h)])
        c.fill(side, kraft_sh); c.grad(side, 0, -h, 0, 0, [(0, key, 40 * kk), (1, '#000000', 90)])
        if det >= 1: c.texture(side, 'paper', 0.12, 0.8)
    c.fill(front, kraft)
    c.grad(front, 0, -h, 0, 0, [(0, mix(kraft, key, 0.25 * kk), 255), (0.55, kraft, 0), (1, kraft_dk, 200)])
    if det >= 1:
        c.texture(front, 'paper', 0.14, 0.9)
        c.line(poly([(-fw / 2 + 6, -h + 0.06 * h), (fw / 2 - 6, -h + 0.06 * h)], False), c.lw * 0.35, kraft_dk, 150)   # flap seam
    if b > 0.02:                                              # knock bulge: a lit dome pushed out from inside, a dark ring, creases
        c.radial(front, 0, by + fw * 0.06, fw * 0.62, [(0, '#000000', 0), (0.55, '#000000', 0), (0.78, '#2a1a0c', 150 * b), (1, '#2a1a0c', 0)], sy=1.3)
        c.radial(front, -fw * 0.05, by - fw * 0.06, fw * 0.5, [(0, '#f6d9a8', 230 * b), (0.5, '#e8c48e', 120 * b), (1, kraft, 0)], sy=1.25)
        if det >= 1:
            cr = []
            for k in range(7):
                a_ = k * 2 * PI / 7 + 0.4
                r0, r1 = fw * 0.16, fw * (0.3 + 0.08 * hash01(k, 3))
                cr.append(smooth([(math.cos(a_) * r0, by + math.sin(a_) * r0 * 1.2),
                                  (math.cos(a_ + 0.12) * (r0 + r1) / 2, by + math.sin(a_ + 0.12) * (r0 + r1) / 2 * 1.2),
                                  (math.cos(a_) * r1, by + math.sin(a_) * r1 * 1.2)], False))
            c.line(_multi(cr), c.lw * 0.7, kraft_dk, 240 * b)
    # tape: wrapped bands (front + side), a vertical band, two diagonals
    if tape > 0:
        tc, th_, thi = '#8e5f2b', '#6a4520', '#d9a865'
        bands = [(-0.93, 0.0), (-0.81, 0.02), (-0.66, -0.03), (-0.49, 0.025), (-0.33, -0.02), (-0.18, 0.03), (-0.06, -0.01)]
        cut = st.get('cut', 0.0)
        fills, lines, hi = [], [], []
        for k, (yy, sl) in enumerate(bands):
            yc = yy * h; tw = 0.045 * h
            pts = [(-fw / 2 - 1, yc - tw / 2 - sl * fw / 2), (fw / 2 + 1, yc - tw / 2 + sl * fw / 2),
                   (fw / 2 + 1, yc + tw / 2 + sl * fw / 2), (-fw / 2 - 1, yc + tw / 2 - sl * fw / 2)]
            fills.append(poly(pts))
            hi.append(poly([(-fw / 2, yc - tw * 0.18 - sl * fw / 2), (fw / 2, yc - tw * 0.18 + sl * fw / 2)], False))
            if abs(sd) > 1:
                xe = fw / 2 if sd > 0 else -fw / 2; s_ = 1 if sd > 0 else -1
                y0 = yc + s_ * sl * fw / 2
                fills.append(poly([(xe, y0 - tw / 2), (xe + sd, y0 - tw / 2 - 0.05 * abs(sd)), (xe + sd, y0 + tw / 2 - 0.05 * abs(sd)), (xe, y0 + tw / 2)]))
        vb = poly([(-0.06 * fw, -h - 1), (0.06 * fw, -h - 1), (0.07 * fw, 1), (-0.05 * fw, 1)])
        fills.append(vb); hi.append(poly([(-0.02 * fw, -h), (-0.01 * fw, 0)], False))
        for sgn in (-1, 1):
            fills.append(poly([(sgn * fw * 0.5, -0.9 * h), (sgn * fw * 0.5, -0.84 * h), (-sgn * fw * 0.5, -0.4 * h), (-sgn * fw * 0.5, -0.46 * h)]))
        tp = _multi(fills)
        with c.clip(union(front, side) if abs(sd) > 1 else front):
            c.fill(tp, tc, 235 * tape)
            c.line(tp, c.lw * 0.3, th_, 200 * tape)
            c.line(_multi(hi), c.lw * 0.45, thi, 150 * tape)
            if det >= 1:
                wr = []
                for k in range(24):
                    wx = (hash01(k, 61) - 0.5) * fw * 0.95; wy = -h * hash01(k, 62)
                    wr.append(poly([(wx, wy), (wx + 6 + 6 * hash01(k, 63), wy + 3)], False))
                c.line(_multi(wr), c.lw * 0.25, thi, 110 * tape)
            if cut > 0.01:                                       # the tape slit down the middle: a dark open gap, edges curling
                gw = 0.022 * fw * cut
                gap = poly([(-gw, -h), (gw, -h), (gw * 0.7, -h + h * cut), (-gw * 0.7, -h + h * cut)])
                c.fill(gap, '#0d0805', 255); c.line(gap, c.lw * 0.5, '#000000', 255)
                for k, (yy, sl) in enumerate(bands):                 # every taped band: both cut ends lift and curl away
                    yc = yy * h
                    if -yc > h * (1 - cut): continue
                    for sd_ in (-1, 1):
                        flap = poly([(sd_ * gw, yc - 0.024 * h), (sd_ * (gw + 0.11 * fw), yc - 0.045 * h), (sd_ * (gw + 0.09 * fw), yc + 0.004 * h),
                                     (sd_ * gw, yc + 0.022 * h)])
                        c.fill(flap, thi, 240); c.line(flap, c.lw * 0.4, '#5a3a1a', 220)
                        c.fill(poly([(sd_ * gw, yc + 0.022 * h), (sd_ * (gw + 0.09 * fw), yc + 0.004 * h), (sd_ * (gw + 0.07 * fw), yc + 0.03 * h)]),
                               '#000000', 70)
    if label:
        lw_, lh_ = fw * 0.66, h * 0.17
        lc = c.sub(-lw_ * 0.48, -0.78 * h, -2.0)
        _label(lc, 0, 0, lw_, lh_, det, to, sender, t)
    if abs(sd) > 1:
        xe = fw / 2 if sd > 0 else -fw / 2
        c.line(poly([(xe, 0), (xe + sd, -0.05 * abs(sd)), (xe + sd, -h - 0.05 * abs(sd)), (xe, -h)]), c.lw)
    if lt.get('rim'):
        c.fill(_crescent(front, -9 * lt.get('side', 1), 0), lt['rim'], lt.get('rim_a', 70))
    c.line(front, c.lw)


def draw_box_inside(pen, cx, cy, size, t=0.0, flaps=1.0, keys=True, rust=1.0, light=None, detail=2):
    """Insert: looking down into the opened box at sunrise. The tall box is a deep dark well (walls converging to the
    bottom), the four flaps folded out with cut tape strands, and at the bottom only dad's rusted keys on the
    second-grade keychain, catching a sliver of morning light. size = width of the opening in design px."""
    lt = light or {}
    sun = lt.get('key', '#ffcf8f')
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 0.9) * 0.9).sub(cx, cy, 0.0, size / 400.0)
    ow, oh = 200.0, 150.0; iw, ih = 92.0, 68.0
    # flaps (open outward)
    fl = clamp(flaps)
    flp = [poly([(-ow, -oh), (ow, -oh), (ow * 0.92, -oh - 120 * fl), (-ow * 0.92, -oh - 120 * fl)]),
           poly([(-ow, oh), (ow, oh), (ow * 0.92, oh + 120 * fl), (-ow * 0.92, oh + 120 * fl)]),
           poly([(-ow, -oh), (-ow, oh), (-ow - 110 * fl, oh * 0.9), (-ow - 110 * fl, -oh * 0.9)]),
           poly([(ow, -oh), (ow, oh), (ow + 110 * fl, oh * 0.9), (ow + 110 * fl, -oh * 0.9)])]
    for k, f in enumerate(flp):
        c.fill(f, ('#9c7647', '#8c693f', '#a17a4a', '#7f5f39')[k]); c.texture(f, 'paper', 0.14, 0.9); c.line(f, c.lw)
    for k in range(6):                                         # cut tape strands hanging off the flap edges
        sx_ = -ow * 0.15 + k * 14 - 30
        c.fill(poly([(sx_, -oh - 2), (sx_ + 12, -oh - 2), (sx_ + 16 + 6 * hash01(k, 2), -oh - 34 - 20 * hash01(k, 3)), (sx_ + 2, -oh - 26)]),
               '#8e5f2b', 230)
        c.fill(poly([(sx_ + 6, oh + 2), (sx_ + 18, oh + 2), (sx_ + 20, oh + 30 + 18 * hash01(k, 4)), (sx_ + 4, oh + 22)]), '#8e5f2b', 230)
    # inner walls converging to the bottom
    walls = [(poly([(-ow, -oh), (ow, -oh), (iw, -ih), (-iw, -ih)]), '#3a2a19'), (poly([(-ow, oh), (ow, oh), (iw, ih), (-iw, ih)]), '#5a4128'),
             (poly([(-ow, -oh), (-ow, oh), (-iw, ih), (-iw, -ih)]), '#2c2014'), (poly([(ow, -oh), (ow, oh), (iw, ih), (iw, -ih)]), '#4a3520')]
    for p_, col_ in walls:
        c.fill(p_, col_); c.line(p_, c.lw * 0.6, '#140d07')
    bot = rect(-iw, -ih, iw * 2, ih * 2)
    c.fill(bot, '#20170e')
    c.radial(bot, -30, -10, 120, [(0, '#3a2a19', 255), (1, '#0e0a06', 255)])
    # a sliver of sunrise across one wall and the bottom
    c.fill(poly([(ow, -oh), (ow, -oh * 0.2), (iw, -ih * 0.1), (iw, -ih)]), sun, 60)
    c.fill(poly([(iw, -ih), (iw, -ih * 0.1), (-iw * 0.2, ih * 0.4), (-iw * 0.1, -ih)]), sun, 40)
    if keys:
        c.glow(4, 6, 80, 40, '#000000', 120)
        kc = c.sub(-28, -30, -58.0, 1.0)
        _keyring(kc, detail, t, rust)
        c.glow(-10, -20, 40, 16, sun, 110 * (0.6 + 0.4 * math.sin(t * 1.3)))
    c.line(rect(-ow, -oh, ow * 2, oh * 2), c.lw * 1.2)


def draw_keys_bowl(pen, x, y, size, drop=None, t=0.0, rust=0.0, hand=False, keys_in=True, light=None, detail=2):
    """The key bowl on the hall side table: a glazed ceramic bowl seen from a little above, dad's keys on the bead keychain
    lying in it. drop = seconds since the keys were released (None = resting; negative = not there yet): they fall in,
    hit at KEYS_DROP_IMPACT, bounce and jangle to rest. hand=True shows a pale grey hand letting go above (dad's, at
    3:11, fading). (x, y) = bowl foot, size = bowl width in design px."""
    lt = light or {}
    c = Ctx(pen, skia.Matrix(), _lw_for(size * 1.2) * 0.85).sub(x, y, 0.0, size / 200.0)
    rim_y = -70.0
    glaze, glaze_sh, inner = '#2f5664', '#1c3640', '#4f7f8b'
    body = smooth([(-100, rim_y), (-92, -30), (-62, -6), (-30, 0), (30, 0), (62, -6), (92, -30), (100, rim_y)], True, 0.7)
    rim = oval(0, rim_y, 100, 34)
    c.glow(0, 2, 110, 14, '#000000', 160)
    c.fill(body, glaze); c.grad(body, -100, 0, 100, 0, [(0, glaze_sh, 255), (0.35, glaze, 255), (0.6, mix(glaze, '#ffffff', 0.12), 255), (1, glaze_sh, 255)])
    c.line(body, c.lw)
    c.fill(rim, inner); c.radial(rim, 10, rim_y + 6, 100, [(0, mix(inner, '#000000', 0.3), 255), (1, inner, 255)], sy=0.3)
    # keys
    show = keys_in and (drop is None or drop >= 0)
    if show:
        if drop is None or drop >= KEYS_DROP_IMPACT:
            tau = 0.0 if drop is None else drop - KEYS_DROP_IMPACT
            bounce = 0.0 if drop is None else 10.0 * math.exp(-tau * 9.0) * abs(math.sin(tau * 18.0))
            jang = 0.0 if drop is None else math.exp(-tau * 3.0)
            kc = c.sub(-40, rim_y - 12 - bounce, -72.0 + 6.0 * jang * math.sin(tau * 14.0), 0.82, 0.7)
            with c.clip(union(oval(0, rim_y, 96, 31), rect(-200, -400, 400, 400 + rim_y))):
                _keyring(kc, detail, t, rust, jangle=jang)
        else:
            u = drop / KEYS_DROP_IMPACT
            kc = c.sub(-30 + 10 * (1 - u), rim_y - 12 - 230.0 * (1 - u * u), -10.0 - 62.0 * u, 0.82)
            _keyring(kc, detail, t, rust, spread=1.2)
    # the front lip of the bowl over the keys
    lip = minus(oval(0, rim_y, 100, 34), oval(0, rim_y - 6, 96, 30))
    c.fill(lip, mix(glaze, '#ffffff', 0.18)); c.line(oval(0, rim_y, 100, 34), c.lw)
    if detail >= 1: c.glow(-40, rim_y + 14, 26, 6, '#ffffff', 60)
    if hand and drop is not None and drop < 1.2:
        a_ = 1.0 - clamp((drop - 0.2) / 1.0)
        cv = pen.cv; cv.saveLayerAlpha(None, int(255 * 0.85 * a_))
        hc = Ctx(pen, skia.Matrix(), _lw_for(size * 1.2) * 0.85)
        hx, hy = x + 10 * size / 200.0, y - size * 1.25 - 20 * clamp(drop)
        _draw_hand(hc, CAST['dad'], 'open', hx, hy, size / 200.0 * 1.25, 0.0, 1, detail, '#b9b4b0', '#85807e', True, 0.0, t)
        cv.restore()


# ------------------------------------------------------------------ delivery: the acting arc over the film
DELIVERY_FEAR_ARC = {'you_police': [(215.74, 0.35), (353.24, 0.55), (497.79, 0.8)],   # the delivery film's (you / mom then)
                     'mom_delivery': [(287.97, 0.45), (377.96, 0.7), (497.79, 0.85)]}
# dummy film (film time): the case is empty 155.3, "kiddo" from the kitchen 243.5, the stairs 354.6, the bookcase 423.1,
# Mom screams 543.7; the new Owen is calm (owen_new: no tremble)
FEAR_ARC = {'you': [(155.33, 0.3), (243.48, 0.5), (354.61, 0.65), (423.12, 0.75), (543.73, 0.9), (567.06, 0.6)],
            'mom': [(184.4, 0.45), (247.11, 0.65), (420.57, 0.75), (543.73, 0.95), (575.48, 0.4)],
            'owen': [(155.33, 0.15), (290.16, 0.45), (543.73, 0.95)]}
FEAR_ARC.update(DELIVERY_FEAR_ARC)
# Mister Winks's wooden ticks over the night (from t: one tick every lo..hi s); none while he lies face down / sleeps
WINKS_TICKS = [(173.97, 5.0, 8.0), (314.69, 3.0, 5.0), (401.93, 2.0, 3.5)]
WINKS_QUIET = [(567.06, 655.6)]
DRIVER_TWITCH = [(196.51, 4.0, 6.0), (340.87, 2.2, 3.2), (446.44, 1.5, 2.5)]   # from t: a twitch / jerk every lo..hi s
DRIVER_STILL = (435.84, 446.44)                                               # "his face is perfectly still"


def escalate(a, t0, t1, kind=None):
    """The film's acting arc for one actor over a shot [t0, t1] in film time (call it from film.py's escalate, like the
    police film's). Dummy film: Mister Winks gets a hard wooden head tick every 5-8 s from 'in_chair' (174 s), 3-5 s from
    'stand' (315 s), 2-3.5 s from 'clack_shut' (402 s), none while he sleeps face down (567-656 s) or with kind='worked'
    (on a lap); you / mom / Owen get the FEAR_ARC tremble. Delivery film (below): Driver: the smile arc is automatic (DRIVER_ARC under every clip); this adds twitches and
    jerks, rarer at first (from 'wider' 196.5 s), then every 2.2-3.2 s once he leans in (340.9 s), every 1.5-2.5 s after
    he smiles again (446.4 s), none while his face is perfectly still. you / mom: fear tremble that builds (FEAR_ARC).
    Lily and dad: nothing (Lily is calm; dad is a memory). Rule cards (kind 'rule'): nothing."""
    if kind == 'rule' or t1 - t0 < 0.4: return a
    if a.who == 'winks':                       # dummy film: a hard little wooden tick of the head, more often as the night goes on
        rate = None
        for (ts, lo, hi) in WINKS_TICKS:
            if t0 >= ts: rate = (lo, hi)
        if rate and t1 - t0 > 1.0 and kind != 'worked':
            k = t0 + 0.6 + 0.9 * float(hash01(int(t0 * 10), 73)); n = 0
            while k < t1 - 0.2:
                if not any(q0 - 0.3 <= k <= q1 for q0, q1 in WINKS_QUIET):
                    sg = 1.0 if (n % 2 == 0) else -1.0
                    a.tick(k, tilt=sg * (3.0 + 3.0 * float(hash01(int(k * 10), 74))), nod=0.02 * sg); n += 1
                k += rate[0] + (rate[1] - rate[0]) * float(hash01(int(k * 10), 75))
        return a
    if a.who == 'driver':
        rate = None
        for (ts, lo, hi) in DRIVER_TWITCH:
            if t0 >= ts: rate = (lo, hi)
        if rate and t1 - t0 > 1.2:
            k = t0 + 0.5 + 0.8 * float(hash01(int(t0 * 10), 71)); ts_ = []
            while k < t1 - 0.25:
                if not (DRIVER_STILL[0] - 0.3 <= k <= DRIVER_STILL[1] + 0.3): ts_.append(k)
                k += rate[0] + (rate[1] - rate[0]) * float(hash01(int(k * 10), 72))
            if ts_:
                a.twitch(ts_[::2], 1.0)
                for tj in ts_[1::2]: a.jerk(tj, 0.5)
    elif a.who in FEAR_ARC:
        amp = 0.0
        for ts, am in FEAR_ARC[a.who]:
            if t0 >= ts: amp = am
        if amp > 0: a.tremble(t0, t1, amp)
    return a


# ====================================================================================================== HUD phone hand
def hud_phone_hand(pen, w, h, skin='#c9aa98', a=255, front=False, sleeve='#34443f'):
    """Drop-in for engine.hud._hand(pen, w, h, skin, a, front): a hand holding the phone in phone coords (the phone spans
    -w/2..w/2, -h/2..h/2). front=False draws the palm, wrist and hoodie cuff behind the phone; front=True the four
    fingertips wrapping the right edge and the thumb over the left edge. Install: hud._hand = characters.hud_phone_hand."""
    sh = mix(skin, '#6b5148', 0.42); dp = mix(skin, '#3a2a2a', 0.55); nail = mix(skin, '#ffffff', 0.35)
    lw = 7.0; k = a / 255.0
    c = Ctx(pen, skia.Matrix(), lw)
    if not front:
        palm = smooth([(-w * 0.64, h * 0.06), (-w * 0.6, h * 0.5), (-w * 0.24, h * 0.8), (w * 0.34, h * 0.78), (w * 0.62, h * 0.44),
                       (w * 0.66, h * 0.06), (w * 0.36, -h * 0.04), (-w * 0.36, -h * 0.03)], True, 0.8)
        wrist = poly([(-w * 0.31, h * 0.6), (w * 0.33, h * 0.6), (w * 0.42, h * 1.3), (-w * 0.38, h * 1.3)])
        body = union(palm, wrist)
        c.fill(body, skin, a); c.fill(_crescent(body, -w * 0.07, -h * 0.02), sh, 150 * k); c.line(body, lw, LINE, a)
        c.line(smooth([(-w * 0.42, h * 0.46), (-w * 0.2, h * 0.6), (w * 0.05, h * 0.62)], False), lw * 0.45, dp, 160 * k)
        cuff = rrect(-w * 0.5, h * 0.92, w * 1.02, h * 0.5, 36)
        c.fill(cuff, sleeve, a); c.fill(_crescent(cuff, -w * 0.08, 0), mix(sleeve, '#000000', 0.35), 160 * k); c.line(cuff, lw, LINE, a)
        c.line(_multi([poly([(-w * 0.4 + i * w * 0.1, h * 0.95), (-w * 0.4 + i * w * 0.1, h * 1.05)], False) for i in range(9)]),
               lw * 0.4, LINE, 150 * k)
        return
    # v2.1: four real fingertips curl round the right edge (staggered, tapering, nails out, a crease where they bend
    # over the edge); the thumb comes round the left edge with its nail showing
    for i in (3, 2, 1, 0):
        fy = -h * 0.07 + i * h * 0.112
        fw = h * (0.084 - 0.007 * i)
        tipx = w * (0.355 + 0.02 * i + (0.025 if i == 0 else 0.0))
        pts = [(w * 0.565, fy + h * 0.03), (w * 0.505, fy + h * 0.01), (tipx, fy)]
        f = _tube(pts, [fw * 0.98, fw * 0.95, fw * 0.82], 0.9)
        c.fill(f, skin, a); c.fill(_crescent(f, 0, -h * 0.02), sh, 140 * k); c.line(f, lw * 0.85, LINE, a)
        c.line(smooth([(w * 0.5, fy - fw * 0.36), (w * 0.485, fy), (w * 0.5, fy + fw * 0.36)], False), lw * 0.35, dp, 170 * k)
        nl = rrect(tipx - fw * 0.02, fy - fw * 0.3, fw * 0.62, fw * 0.6, fw * 0.28)
        c.fill(nl, nail, 230 * k); c.line(nl, lw * 0.3, dp, 190 * k)
    tp = [(-w * 0.7, h * 0.46), (-w * 0.56, h * 0.27), (-w * 0.4, h * 0.15)]
    th = _tube(tp, [w * 0.2, w * 0.165, w * 0.13], 0.9)
    c.fill(th, skin, a); c.fill(_crescent(th, w * 0.03, -h * 0.02), sh, 140 * k); c.line(th, lw * 0.85, LINE, a)
    c.line(smooth([(-w * 0.62, h * 0.24), (-w * 0.56, h * 0.29), (-w * 0.5, h * 0.27)], False), lw * 0.35, dp, 170 * k)
    nl = rrect(-w * 0.44, h * 0.13, w * 0.07, h * 0.045, w * 0.03)
    c.fill(nl, nail, 230 * k); c.line(nl, lw * 0.3, dp, 190 * k)


# ====================================================================================================== dummy film: Mister Winks's head
# Front-view head units as everywhere (crown -120, chin +120). The face is painted wood under varnish: hard-edged rosy
# cheeks, freckles, heavy arched painted brows, big round glass eyes (painted iris, hard highlight, painted lashes) under
# wooden lids, a button nose, a wide painted grin (red lips, a band of flat painted teeth) and the LOWER JAW BLOCK: cut
# along two deep marionette slot lines from the mouth corners straight down to the chin, it drops straight down (pose.jaw)
# and shows the black hollow behind the teeth. Painted red hair with a hard side part (carved grooves, varnish shine) and
# a burgundy pillbox cap with gold braid sit on top.

def _sph(hm, phi, y, grow=0.0):
    """Points on the head surface all the way round (phi 0 = front, +pi/2 = the character's left / screen right in a
    front view, +-pi = back) at height y -> projected X, Y and a visibility (> 0 = facing the camera)."""
    phi = np.asarray(phi, float); y = np.asarray(y, float)
    w = np.maximum(hm.W(np.clip(y, -119.9, 119.9)), 1.0) + grow
    c_, s_ = np.cos(phi), np.sin(phi)
    d = np.where(c_ > 0, hm.DF, hm.DB)
    px = w * s_; pz = d * w * c_
    y1 = hm.J(y) * hm.cp + pz * hm.spi
    z1 = pz * hm.cp - y * hm.spi
    X = px * hm.ct + z1 * hm.st
    vis = -s_ * d * hm.st + c_ * hm.ct
    return X, y1, vis


def _winks_mouth(sp, P):
    """Front-coords mouth of the dummy: (mw, cy, ym, yu, yl, ylo): half width, corner height and functions of x for the
    mouth line (the top edge of the jaw block: the seam of the tight painted grin), the bottom of the strip of painted
    upper teeth (seen only when the jaw is open), the top of the thin upper lip and the bottom of the thin lower lip (on
    the jaw block). pose.grin_w widens, lifts and tightens the grin in stages (0 .. 1.4)."""
    g = max(0.0, P.grin_w)
    mw = sp['mouth_w'] + 6.0 + 18.0 * g
    cy = sp['mouth_y'] - 16.0 - 8.0 * g
    y0 = sp['mouth_y'] + 5.0 + 3.0 * g
    tl = 4.0 - 0.8 * min(g, 1.4)                        # the lips thin out as the grin stretches
    def u(x): return np.clip(1.0 - (np.asarray(x, float) / mw) ** 2, 0.0, 1.0)
    def ym(x): return cy + (y0 - cy) * u(x) ** 0.6
    def yu(x): return ym(x) + 7.5 * u(x) ** 0.3
    def yl(x): return ym(x) - tl * u(x) ** 0.45 - 0.9
    def ylo(x): return ym(x) + (tl + 0.8) * u(x) ** 0.45 + 0.9
    return mw, cy, ym, yu, yl, ylo


def _winks_block(sp, P, mw, cy, ym):
    """Front-coords outline of the jaw block: the mouth line, the two slot lines down to the jaw line, the chin."""
    xs = np.linspace(-mw, mw, 17)
    top = list(zip(xs.tolist(), ym(xs).tolist()))
    xb = mw * 0.84
    jy = lambda x: min(119.0, _jaw_y(sp, x) + 0.5)     # noqa: E731
    right = [(mw - (mw - xb) * k / 4.0, cy + (jy(xb) - cy) * k / 4.0) for k in range(1, 5)]
    chin = [(x, jy(x)) for x in np.linspace(xb, -xb, 15)[1:-1].tolist()]
    left = [(-xb + (xb - mw) * k / 4.0, jy(xb) + (cy - jy(xb)) * k / 4.0) for k in range(0, 4)]
    return top + right + chin + left


def _fpath(hm, pts, dz=0.0, closed=True, k=0.9):
    X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], dz)
    return _pts_path(X, Y, closed, k), V


_WINKS_FRECKLES = None


def _winks_freckles():
    """A few faint painted dots high on each cheek (three a side)."""
    global _WINKS_FRECKLES
    if _WINKS_FRECKLES is None:
        pts = []
        for k in range(6):
            s = -1 if k % 2 else 1
            j = k // 2
            pts.append((s * (34.0 + 9.0 * j + 3.0 * hash01(k, 302)), 22.0 + 4.0 * hash01(k, 303) - 2.0 * j, 1.25 + 0.4 * hash01(k, 304)))
        _WINKS_FRECKLES = pts
    return _WINKS_FRECKLES


# hairline cracks in the varnish (front coords), revealed one by one as pose.crack rises
_WINKS_CRACKS = [
    [(-46, 44), (-58, 30), (-63, 31), (-72, 18)],                         # from the left slot line up the cheek
    [(30, -80), (22, -70), (26, -62), (18, -55)],                         # down from the hairline over the right brow
    [(54, 50), (66, 64), (64, 74), (74, 86)],                             # off the right slot line
    [(-20, -86), (-30, -74), (-26, -68), (-38, -60)],                     # forehead, left
    [(-62, 22), (-76, 26), (-82, 38)],                                    # under the left cheek, out to the jaw
    [(8, 96), (16, 104), (12, 112)],                                      # the chin
]
_WINKS_CRAZE = None


def _winks_craze():
    """Fine crazing of the old lacquer (front coords): short branching hairlines away from the eyes, nose and mouth,
    in reveal order (pose.crack shows the first crack * n). Each is a list of (x, y)."""
    global _WINKS_CRAZE
    if _WINKS_CRAZE is None:
        out, k = [], 0
        while len(out) < 34 and k < 400:
            x = -92.0 + 184.0 * hash01(k, 411); y = -74.0 + 184.0 * hash01(k, 412); k += 1
            ex = abs(x) - 41.0
            if (ex / 36.0) ** 2 + ((y + 14.0) / 36.0) ** 2 < 1.0: continue          # the eyes
            if abs(x) < 18 and -2 < y < 36: continue                                # the nose
            if abs(x) < 70 and 22 < y < 70: continue                                # the grin
            if abs(x) > 96 - 0.004 * y * y: continue
            pts = [(x, y)]
            a = hash01(k, 413) * 2 * PI
            for j in range(3 + int(hash01(k, 414) * 3)):
                a += (hash01(k * 7 + j, 415) - 0.5) * 1.6
                L = 4.0 + 4.5 * hash01(k * 7 + j, 416)
                pts.append((pts[-1][0] + L * math.cos(a), pts[-1][1] + L * math.sin(a)))
            out.append(pts)
            if hash01(k, 417) > 0.55:                                               # a branch off the middle
                b = pts[len(pts) // 2]; a2 = a + (1.2 if hash01(k, 418) > 0.5 else -1.2)
                out.append([b, (b[0] + 5.0 * math.cos(a2), b[1] + 5.0 * math.sin(a2)), (b[0] + 9.0 * math.cos(a2 + 0.4), b[1] + 9.0 * math.sin(a2 + 0.4))])
        _WINKS_CRAZE = out
    return _WINKS_CRAZE


# two chips knocked out of the paint (front coords x, y, size): the bare wood shows
_WINKS_CHIPS = [(-80.0, 46.0, 1.0), (79.0, -24.0, 0.75)]


def _winks_eye_shape(sp, P, side):
    """(r, droop, tilt) of one eye: radius, how far the resting upper lid hangs over the eyeball (0 = open .. 1), and
    the tilt of the lid edge (+ = lower toward the nose: the sly scowl; - = pleading)."""
    dsp = clamp(P.desperate); sad = clamp(P.brow_sad + dsp); ang = clamp(P.brow_angry) * (1.0 - sad)
    r = sp['eye_r'] * (1.0 + 0.08 * P.wide)
    droop = clamp(0.17 + 0.14 * ang - 0.3 * P.brow_up - 0.42 * dsp, 0.0, 0.5)
    return r, droop, 0.17 * ang - 0.12 * sad


def _winks_eye(c, hm, sp, P, side, det, t, skin, sh):
    """One glossy painted eyeball under a heavy wooden lid. side -1 = screen-left eye (character's right). Small,
    near-black irises with a hard pinpoint highlight, locked on the lens; the upper lid rests low (sizing you up) and
    slides shut for the wink / blink. Returns (X, Y, r, fs, glint) or None; glint = (x, y, rx, ry) of the visible
    pinpoint highlight or None."""
    ex0 = side * sp['eye_dx']; ey0 = sp['eye_y']
    X, Y, V = hm.map1(ex0, ey0, 3.0)
    if V < 0.1: return None
    fs = hm.sx(ex0, ey0)
    r, droop, tilt0 = _winks_eye_shape(sp, P, side)
    rx = r * fs
    dsp = clamp(P.desperate); ang = clamp(P.brow_angry) * (1.0 - clamp(P.brow_sad + dsp))
    # a deep-set socket and the faint grey-violet shadow under the eye
    c.glow(X, Y + 1.0, rx * 1.55, r * 1.45, '#33233a', 105 + 70 * ang + 40 * dsp)
    c.glow(X, Y + r * 1.0, rx * 1.1, r * 0.46, '#56436a', 105 + 50 * ang + 50 * dsp)
    white = oval(X, Y, rx, r)
    c.fill(white, '#f0e8d4')
    lidk = clamp(max(P.blink, P.lid_l if side > 0 else P.lid_r))
    lock = clamp(P.lock)
    lx = lerp(P.look_x, -math.sin(hm.yaw) * 0.8, lock)
    ly = lerp(P.look_y, -math.sin(hm.pitch) * 0.9 + 0.05, lock)
    if dsp > 0.02:                           # the one inside: the eyes shiver, searching for help
        lx += dsp * 0.06 * math.sin(t * 19.0 + 1.3 * side); ly += dsp * 0.04 * math.sin(t * 15.0 + 0.7)
    ir = r * (0.21 + 0.10 * P.pupil + 0.05 * dsp)
    pr = ir * (0.42 + 0.22 * dsp)
    reach = r - ir - 2.5
    px = X + lx * reach * fs; py = Y + ly * reach
    irc = sp.get('iris', '#2a1a12')
    e = ease_in_out(lidk)
    f = droop + (1.0 - droop) * e
    yc = Y - r * 1.04 + 2.1 * r * f                # lid edge: centre height, the dome's sag, the tilt to the nose
    sag = r * (0.14 + 0.1 * e)
    tilt = r * tilt0 * (1.0 - e)

    def edge_y(u): return yc - sag * u * u - tilt * side * u
    us = (-1.4, -1.0, -0.55, 0.0, 0.55, 1.0, 1.4)
    edge_pts = [(X + u * rx, edge_y(u)) for u in us]
    glint = None
    with c.clip(white):
        c.radial(white, X - rx * 0.2, Y - r * 0.1, r * 1.15, [(0, '#fffaf0', 0), (0.55, '#f0e8d4', 0), (0.85, '#c8b99c', 210), (1, '#86745e', 250)])
        iris = oval(px, py, ir * fs, ir)
        c.radial(iris, px + ir * 0.2 * fs, py + ir * 0.25, ir * 1.1, [(0, mix(irc, '#7a4a2a', 0.3), 255), (0.5, irc, 255), (1, mix(irc, '#000000', 0.6), 255)])
        c.line(iris, c.lw * 0.4, '#050303', 240)
        c.fill(oval(px, py, pr * fs, pr), '#020101')
        # the hard pinpoint highlight (+ a faint second spark), unless the lid is over it
        gx, gy = px - ir * 0.38 * fs, py - ir * 0.42
        gr = max(1.3, ir * 0.2)
        if gy - gr > edge_y((gx - X) / max(rx, 1e-3)) + 0.5:
            glint = (gx, gy, gr * fs, gr)
            c.fill(oval(gx, gy, gr * fs, gr), '#ffffff', 250)
        c.fill(oval(px + ir * 0.4 * fs, py + ir * 0.38, max(0.8, ir * 0.08) * fs, max(0.8, ir * 0.08)), '#ffffff', 150)
        if det >= 1:                          # glassy sheen on the lower eyeball
            c.line(smooth([(X - rx * 0.62, Y + r * 0.5), (X - rx * 0.2, Y + r * 0.72), (X + rx * 0.25, Y + r * 0.7)], False),
                   c.lw * 0.6, '#ffffff', 80 * P.gloss)
        if dsp > 0.02:                       # the one inside: wet, red-rimmed, a tear pooling on the lower lid
            c.fill(smooth([(X - rx, Y + r * 0.58), (X, Y + r * 0.8), (X + rx, Y + r * 0.58), (X, Y + r * 1.15)], True), '#bcd6f2', 140 * dsp)
            c.line(smooth([(X - rx * 0.7, Y + r * 0.76), (X, Y + r * 0.88), (X + rx * 0.7, Y + r * 0.76)], False), c.lw * 0.35, '#ffffff', 190 * dsp)
            c.line(white, c.lw * 1.6, '#a0384a', 120 * dsp)
        # the lid's shadow on the eyeball, the lid, its hard painted edge
        lid = smooth([(X - rx * 1.5, Y - r * 1.7), (X + rx * 1.5, Y - r * 1.7)] + edge_pts[::-1], True, 0.7)
        edge = smooth(edge_pts, False, 0.8)
        c.line(moved_path(edge, 0.0, r * 0.16), r * 0.32, '#2a1a1c', 85 - 40 * e)
        lc = mix(skin, sh, 0.3)
        c.fill(lid, lc)
        c.grad(lid, 0, Y - r, 0, yc + r * 0.05, [(0, mix(lc, '#ffffff', 0.12), 255), (0.65, lc, 255), (1, mix(lc, sp['skin_dp'], 0.45), 255)])
        if det >= 1:
            if f > 0.55:                     # the carved crease of the lid
                c.line(smooth([(X - rx * 0.8, Y - r * 0.55), (X, Y - r * 0.72), (X + rx * 0.8, Y - r * 0.55)], False), c.lw * 0.45, sp['skin_dp'], 160 * e)
            c.fill(oval(X - rx * 0.28, max(Y - r * 0.8, yc - r * 0.45), rx * 0.3, r * 0.08), '#ffffff', 110 * P.gloss)
        c.line(edge, c.lw * (1.5 + 0.3 * e), '#160c0a')
        if e > 0.75:                         # shut: the seam where the lid meets the lower rim
            c.line(smooth([(X - rx * 0.86, Y + r * 0.34), (X, Y + r * 0.6), (X + rx * 0.86, Y + r * 0.34)], False), c.lw * 1.2, '#160c0a',
                   255 * clamp((e - 0.75) / 0.2))
    c.line(white, c.lw * 0.9)
    return (X, Y, r, fs, glint)


def _winks_brow(c, hm, sp, P, side):
    """Heavy, sharply arched painted brow, angled down toward the nose (a sly scowl even while he grins): a blunt heavy
    head low by the nose, a pointed peak over the outer half of the eye, a tapering tail. brow_angry lowers and
    sharpens it; brow_sad / desperate lift the inner end (pleading)."""
    ex = sp['eye_dx']; r = sp['eye_r']; ey = sp['eye_y']
    up = P.brow_up; sad = clamp(P.brow_sad + P.desperate); ang = clamp(P.brow_angry) * (1 - sad)
    th = sp['brow_th'] * (1.0 + 0.1 * ang)
    xi, yi = side * (ex - 30.0), ey - r - 3.0 + 12.0 * ang - 19.0 * sad - 4.0 * up
    xp, yp = side * (ex + 9.0 - 13.0 * sad), ey - r - 21.0 - 4.0 * up + 2.0 * ang - 1.0 * sad
    xo, yo = side * (ex + 43.0), ey - r - 6.0 - 3.0 * ang + 11.0 * sad
    L = lambda a, b, k: a + (b - a) * k             # noqa: E731
    pts = [(xi, yi + th * 0.5), (xi + side * 1.5, yi - th * 0.52),
           (L(xi, xp, 0.5), L(yi, yp, 0.5) - th * 0.5 - 1.0), (xp, yp - th * 0.45),
           (L(xp, xo, 0.5), L(yp, yo, 0.5) - th * 0.14 - 0.8), (xo, yo),
           (L(xp, xo, 0.5), L(yp, yo, 0.5) + th * 0.24), (xp - side * 2.0, yp + th * 0.42),
           (L(xi, xp, 0.5), L(yi, yp, 0.5) + th * 0.5)]
    X, Y, V = hm.map([p[0] for p in pts], [p[1] for p in pts], 3.0)
    if V.mean() < 0.1: return
    p = _pts_path(X, Y, True, 0.45)
    c.fill(p, sp['brow_c']); c.line(p, c.lw * 0.4, mix(sp['brow_c'], '#000000', 0.5))
    if P.gloss > 0.05:                          # the lacquer catches the top of the arch
        q = [(L(xi, xp, 0.45), L(yi, yp, 0.45) - th * 0.25), (L(xi, xp, 0.85), L(yi, yp, 0.85) - th * 0.28), (xp + side * 3.0, yp - th * 0.12)]
        X2, Y2, V2 = hm.map([a[0] for a in q], [a[1] for a in q], 3.5)
        if V2.min() > 0.15: c.line(_pts_path(X2, Y2, False, 0.8), c.lw * 0.45, '#ffffff', 70 * P.gloss)


def _winks_cap(c, hm, sp, P, det, cl):
    """Burgundy pillbox cap with gold braid and a brass button, perched on the crown, tipped to his right."""
    x0, y0, z0 = -14.0, -116.0, -6.0
    y1 = y0 * hm.cp + z0 * hm.spi; z1 = z0 * hm.cp - y0 * hm.spi
    X = x0 * hm.ct + z1 * hm.st; Y = y1
    roll = -15.0 * hm.ct + 10.0 * hm.st
    e = clamp(0.2 + 0.78 * hm.spi + 0.05, 0.1, 0.88)
    R, Hc = 40.0, 31.0
    k = c.sub(X, Y + 4.0, roll)
    body = union(rect(-R, -Hc, 2 * R, Hc), oval(0, 0, R, R * e))
    k.fill(body, cl['cap'])
    k.grad(body, -R, 0, R, 0, [(0, mix(cl['cap'], '#ffffff', 0.18), 255), (0.32, cl['cap'], 255), (0.75, cl['cap_sh'], 255), (1, mix(cl['cap_sh'], '#000000', 0.3), 255)])
    if det >= 1: k.texture(body, 'fabric', 0.12, 0.45)
    top = oval(0, -Hc, R, R * e)
    k.fill(top, mix(cl['cap'], '#ffffff', 0.1))
    k.radial(top, -R * 0.3, -Hc - R * e * 0.3, R * 1.1, [(0, mix(cl['cap'], '#ffffff', 0.22), 255), (1, cl['cap'], 255)], sy=max(e, 0.15))
    k.line(body, c.lw)
    # gold braid round the base and the rim
    band = minus(union(rect(-R, -8.0, 2 * R, 8.0), oval(0, 0, R, R * e)), oval(0, -8.0, R, R * e))
    k.fill(band, cl['braid']); k.grad(band, -R, 0, R, 0, [(0, '#f6e3a0', 255), (0.4, cl['braid'], 255), (1, '#7d5f22', 255)])
    if det >= 1:
        ts = [poly([(x_, -7.0 + R * e * math.sqrt(max(0.0, 1 - (x_ / R) ** 2))), (x_ + 3.0, R * e * math.sqrt(max(0.0, 1 - (x_ / R) ** 2)))], False)
              for x_ in np.linspace(-R + 4, R - 6, 14).tolist()]
        k.line(_multi(ts), c.lw * 0.25, '#7d5f22', 200)
    k.line(band, c.lw * 0.5)
    k.line(top, c.lw * 0.8)
    rim = smooth([(-R, -Hc), (0, -Hc + R * e), (R, -Hc)], False)
    k.line(rim, c.lw * 0.9, cl['braid']); k.line(rim, c.lw * 0.3, '#7d5f22', 200)
    if hm.ct > -0.1:                         # the brass button on the front of the band
        bx = R * math.sin(hm.yaw) * 0.95; by = -12.0 + R * e * math.cos(hm.yaw) * 0.9
        br = 5.5 * (0.5 + 0.5 * max(0.0, hm.ct))
        k.fill(oval(bx, by, br, br), cl['brass']); k.line(oval(bx, by, br, br), c.lw * 0.35)
        k.fill(oval(bx - br * 0.3, by - br * 0.3, br * 0.32, br * 0.32), '#fff6c8', 230)


def _winks_hair(c, hm, sp, P, det, sil):
    """Painted, carved auburn hair: a hard side part on his left (phi ~ +0.42), the forelock swept across to his right,
    sculpted ridges (a dark groove with a lit ridge beside it) following the carving, a hard varnish shine; covers the
    back of the head down to the nape."""
    yf, grow = _hairline('painted', 1)
    X, Y = hm.arc_phi(yf, 120)
    if len(X) < 3: return None
    region = poly([(float(X[0]) - 300, -420.0)] + [(float(x), float(y)) for x, y in zip(X, Y)] + [(float(X[-1]) + 300, -420.0)], True)
    vol = hm.silhouette(grow=grow, y_top=-120 - grow * 0.5, y_bot=100)
    hair = inter(union(vol, sil), region)
    hc = sp['hair_c']; hsh = mix(hc, '#1a0603', 0.5); hhi = mix(hc, '#ffc08a', 0.38)
    # the forelock throws a shadow band on the forehead under the hairline
    if hm.map1(0, -60)[2] > 0.05:
        sh_ = inter(minus(moved_path(hair, 2.0, 8.0), hair), sil)
        c.fill(sh_, sp['skin_dp'], 130)
    c.fill(hair, hc)
    with c.clip(hair):
        c.radial(None, -40 + 30 * hm.st, -100, 170, [(0, hhi, 150), (0.45, hc, 0), (1, hsh, 235)], clip=False)
        if det >= 1:
            gr = []
            for k in range(6 if det >= 2 else 4):              # swept forelock: from the part across to his right temple
                ph = np.linspace(0.36, -1.62, 14)
                yy = (-121.0 + 8.5 * k) + (0.36 - ph) * (13.0 + 5.0 * k) - 7.0 * np.sin((0.36 - ph) * 1.4)
                Xg, Yg, Vg = _sph(hm, ph, np.minimum(yy, 66.0), 1.5)
                m = Vg > 0.02
                if m.sum() > 2: gr.append(_pts_path(Xg[m], Yg[m], False, 0.9))
            for k in range(4):                                  # the short side: combed down from the part
                ph = np.linspace(0.5, 1.75, 10)
                yy = (-118.0 + 9.0 * k) + (ph - 0.5) * (40.0 + 6.0 * k)
                Xg, Yg, Vg = _sph(hm, ph, yy, 1.5)
                m = Vg > 0.02
                if m.sum() > 2: gr.append(_pts_path(Xg[m], Yg[m], False, 0.9))
            for k in range(10):                                 # the back: combed down to the nape
                ph0 = 1.75 + k * 0.28
                ph0 = ph0 if ph0 <= PI else ph0 - 2 * PI
                ys = np.linspace(-112.0, 66.0, 10)
                ph = ph0 + 0.08 * np.sin((ys + 112.0) / 60.0)
                Xg, Yg, Vg = _sph(hm, ph, ys, 1.5)
                m = Vg > 0.02
                if m.sum() > 2: gr.append(_pts_path(Xg[m], Yg[m], False, 0.9))
            if gr:                                              # carved ridges: lit edge, then the groove
                q = _multi(gr)
                c.line(moved_path(q, -1.6, -2.0), c.lw * 0.9, hhi, 120)
                c.line(q, c.lw * 0.75, hsh, 235)
        # hard varnish shine along the crest of the swoop
        ph = np.linspace(0.25, -1.1, 10)
        Xs, Ys, Vs = _sph(hm, ph, -100.0 + (0.25 - ph) * 15.0, 2.0)
        m = Vs > 0.1
        if m.sum() > 2:
            sl = _pts_path(Xs[m], Ys[m], False, 0.9)
            c.line(sl, c.lw * 2.8, '#ffffff', 50 * P.gloss); c.line(sl, c.lw * 0.8, '#fff4e0', 200 * P.gloss)
    # the part: a hard groove from the hairline back over the crown
    ys = np.linspace(-96.0, -119.5, 7)
    Xp, Yp, Vp = _sph(hm, np.full(7, 0.42), ys, 1.0)
    m = Vp > 0.02
    if m.sum() > 2: c.line(_pts_path(Xp[m], Yp[m], False, 0.9), c.lw * 0.9, mix(hsh, '#000000', 0.4))
    c.line(hair, c.lw)
    return hair


def _winks_head(c, who, P, yaw, pitch, det, t, light=None, sp=None):
    """Mister Winks's head on Ctx c (origin = head centre, head units). Returns the HeadMap. Lacquered ivory wood:
    glossy staring eyes with small near-black irises under low heavy lids, heavy arched black-brown brows angled down
    to the nose, a tight wide grin in thin dark-red lips, the jaw block on two deep slot lines, faded rouge, crazed
    varnish and chips. The menace (shadows, scowl, crazing) builds with the stage arc."""
    sp = sp or CAST[who]
    cl = sp['cloth']
    hm = HeadMap(sp, yaw, pitch, 0.0, 0.0)
    skin, sh, dp = _skin_cols(sp, P, light)
    sil_full = hm.silhouette()
    cut = _nape_cut(hm, sp)
    sil = minus(sil_full, cut) if cut is not None else sil_full
    face_v = hm.map1(0, 0)[2]
    gl = clamp(P.gloss)
    dsp = clamp(P.desperate)
    men = clamp(0.3 + 0.5 * clamp(P.grin_w / 1.4) + 0.3 * clamp(P.brow_angry) - 0.3 * dsp)   # menace: deeper shadows
    for side in (-1, 1):                                       # far ear behind the skull
        if -side * hm.st < 0.25: _ear(c, hm, sp, side, skin, sh, det)
    # the jaw block, at rest and dropped
    mw, cy, ym, yu, yl, ylo = _winks_mouth(sp, P)
    J = 30.0 * clamp(P.jaw, 0.0, 1.2)
    blk_pts = _winks_block(sp, P, mw, cy, ym)
    B0, BV = _fpath(hm, blk_pts, 4.0, True, 0.55)
    front = face_v > -0.2 and float(np.max(BV)) > 0.02
    head = minus(sil, B0) if front else sil
    jdx, jdy = 0.0, J * hm.cp
    Bm = moved_path(B0, jdx, jdy) if front else None
    # skull fill and shading: painted wood under a hard varnish
    c.fill(head, skin)
    lsd = (light or {}).get('side', 1)
    c.radial(head, -35.0 * lsd + hm.st * 20, -40, 165, [(0, mix(skin, '#ffffff', 0.15), 130), (0.5, skin, 0), (0.84, sh, 110 + 50 * men), (1.0, sh, 200)], sy=1.1)
    c.fill(_crescent(head, -lsd * 26, 5), sh, 50 + 60 * men)
    if cut is not None: c.fill(head, sh, 110 * clamp((-hm.ct - 0.2) / 0.4))
    if det >= 2: c.texture(inter(head, rect(-130, -80, 260, 260)), 'paper', 0.05, 0.4)
    if light and light.get('under'):
        ua = light.get('under_a', 120)
        c.grad(head, 0, -125, 0, 40, [(0, '#07080d', 0.6 * ua), (1, '#07080d', 0)])
        c.radial(head, hm.st * 20, 150, 220, [(0, light['under'], ua), (0.55, light['under'], 0.45 * ua), (1, light['under'], 0)], sy=0.8)
    if light and light.get('rim'):
        c.fill(_crescent(sil, -lsd * 7, 3), light['rim'], light.get('rim_a', 70))
    eyes = {}
    if face_v > -0.35:
        with (c.clip(hm.silhouette(grow=1.0)) if abs(hm.st) > 0.2 or abs(P.h_nod) > 0.3 else _noop()):
            # small faded rouge circles, a few faint freckles, chips and crazing in the varnish
            for side in (-1, 1):
                bx_, by_, bv_ = hm.map1(side * 63, 18, 2)
                if bv_ > 0.08:
                    fs_ = hm.sx(side * 63, 18)
                    c.radial(oval(bx_, by_, 12 * fs_, 11.5), bx_, by_, 12, [(0, sp['blush'], 125), (0.7, sp['blush'], 105), (0.92, sp['blush'], 40),
                                                                         (1, sp['blush'], 0)], sy=11.5 / 12.0)
            if det >= 1:
                fr = _winks_freckles()
                X_, Y_, V_ = hm.map([f[0] for f in fr], [f[1] for f in fr], 2.0)
                dots = [oval(float(X_[i]), float(Y_[i]), fr[i][2] * hm.sx(fr[i][0], fr[i][1]), fr[i][2]) for i in range(len(fr)) if V_[i] > 0.1]
                if dots: c.fill(_multi(dots), '#8e5038', 95)
                for (x_, y_, s_) in _WINKS_CHIPS:
                    cx_, cy_, cv_ = hm.map1(x_, y_, 2)
                    if cv_ > 0.15:
                        f_ = s_ * max(0.4, hm.sx(x_, y_))
                        chip = poly([(cx_ - 4 * f_, cy_ - 3 * s_), (cx_ - 1 * f_, cy_ - 5 * s_), (cx_ + 3 * f_, cy_ - 4 * s_), (cx_ + 2 * f_, cy_ - 1 * s_),
                                     (cx_ + 4.5 * f_, cy_ + 2 * s_), (cx_, cy_ + 4 * s_), (cx_ - 3 * f_, cy_ + 2.5 * s_), (cx_ - 2 * f_, cy_)])
                        c.fill(chip, '#dcbf96')
                        with c.clip(chip): c.line(moved_path(chip, 1.0, 1.2), c.lw * 0.6, '#8a6040', 150)
                        c.line(chip, c.lw * 0.28, '#4e2e1c', 210)
                crs = []
                ncr = int(math.ceil(clamp(P.crack) * len(_WINKS_CRACKS) - 1e-6))
                for k in range(ncr):
                    pts = _WINKS_CRACKS[k]
                    X_, Y_, V_ = hm.map([p[0] for p in pts], [p[1] for p in pts], 2.5)
                    if V_.min() > 0.08: crs.append(_pts_path(X_, Y_, False, 0.3))
                if crs:
                    q = _multi(crs)
                    c.line(moved_path(q, 0.8, 0.8), c.lw * 0.3, '#fff1e2', 120); c.line(q, c.lw * 0.34, '#3a1a12', 230)
                if det >= 2 and P.crack > 0.01:            # the fine crazing spreads with the arc
                    cz = _winks_craze()
                    n = int(round(clamp(0.25 + 0.75 * clamp(P.crack)) * len(cz)))
                    flat = [p for s_ in cz[:n] for p in s_]
                    X_, Y_, V_ = hm.map([p[0] for p in flat], [p[1] for p in flat], 2.2)
                    i0, czp = 0, []
                    for s_ in cz[:n]:
                        i1 = i0 + len(s_)
                        if V_[i0:i1].min() > 0.12: czp.append(_pts_path(X_[i0:i1], Y_[i0:i1], False, 0.2))
                        i0 = i1
                    if czp:
                        q = _multi(czp)
                        c.line(moved_path(q, 0.6, 0.6), c.lw * 0.2, '#fff6ea', 70); c.line(q, c.lw * 0.2, '#4a2a20', 90 + 80 * clamp(P.crack))
            # the thin painted upper lip over the seam, and the painted creases that hook up from the corners
            xs = np.linspace(-mw, mw, 25)
            lpts = list(zip(xs.tolist(), yl(xs).tolist())) + list(zip(xs[::-1].tolist(), ym(xs[::-1]).tolist()))
            ulip, UV = _fpath(hm, lpts, 4.5, True, 0.7)
            if float(np.max(UV)) > 0.02:
                c.fill(ulip, sp['lip'])
                if det >= 1:
                    hx, hy, hv = hm.map1(-mw * 0.32, float(yl(-mw * 0.32)) + 1.5, 5.0)
                    if hv > 0.1: c.fill(oval(hx, hy, 5.5 * hm.sx(-mw * 0.3, 40), 1.1), '#ffffff', 150 * gl)
                c.line(ulip, c.lw * 0.45, mix(sp['lip'], '#000000', 0.55))
                cr = []
                for side in (-1, 1):
                    pts = [(side * (mw - 1.5), cy + 0.5), (side * (mw + 3.5), cy - 4.5), (side * (mw + 4.5), cy - 9.0 - 3.0 * clamp(P.grin_w))]
                    X_, Y_, V_ = hm.map([p[0] for p in pts], [p[1] for p in pts], 4.0)
                    if V_.min() > 0.05: cr.append(_pts_path(X_, Y_, False, 0.8))
                if cr: c.line(_multi(cr), c.lw * 0.85, mix(sp['lip'], '#000000', 0.6), 245)
            for side in (-1, 1):
                eyes[side] = _winks_eye(c, hm, sp, P, side, det, t, skin, sh)
                _winks_brow(c, hm, sp, P, side)
            # a tear from the one inside (pose.tears): a single wet streak down the painted cheek
            if P.tears > 0.02:
                for side in (-1, 1):
                    if eyes.get(side) is None: continue
                    x0 = side * (sp['eye_dx'] - 6); y0 = sp['eye_y'] + sp['eye_r'] * 0.95
                    L_ = 70.0 * clamp(P.tears * 1.2)
                    ys_ = np.linspace(y0, y0 + L_, 8); xs_ = x0 + side * 4.0 * np.sin((ys_ - y0) / 30.0)
                    Xt, Yt, Vt = hm.map(xs_, ys_, 3.0)
                    if Vt.min() > 0.1:
                        tp = _pts_path(Xt, Yt, False)
                        c.line(tp, c.lw * 1.1, '#a8c8f0', 200 * clamp(P.tears)); c.line(tp, c.lw * 0.3, '#ffffff', 200 * clamp(P.tears))
    c.line(head, c.lw)                      # (under the block: the dropped block covers the cut edges it slides over)
    # deep slot grooves: a dark shadow on the head side of each marionette line (under the block where it overlaps)
    if front and face_v > -0.35:
        xb = mw * 0.84
        g1, g2 = [], []
        for side in (-1, 1):
            for off, lst in ((3.2, g1), (1.4, g2)):
                pts = [(side * (mw + off), cy + 1), (side * (mw * 0.5 + xb * 0.5 + off), cy * 0.5 + _jaw_y(sp, xb) * 0.5),
                       (side * (xb + off), min(118.0, _jaw_y(sp, xb)) - 2)]
                X_, Y_, V_ = hm.map([p[0] for p in pts], [p[1] for p in pts], 3.0)
                if V_.min() > 0.05: lst.append(_pts_path(X_, Y_, False))
        if g1: c.line(_multi(g1), c.lw * 2.4, dp, 70 + 60 * men)
        if g2: c.line(_multi(g2), c.lw * 0.9, '#120607', 150 + 60 * men)
    # the open mouth: the black void with a dark-red rim and the strips of painted teeth, then the jaw block on top
    if front:
        if J > 0.3:
            hole = minus(B0, Bm)
            c.fill(hole, '#060102')
            ts = clamp(J / 12.0)
            with c.clip(hole):
                xs = np.linspace(-mw, mw, 21)                                   # the dark-red rim: the lips' inner edges
                rim, _ = _fpath(hm, list(zip(xs.tolist(), ym(xs).tolist())), 4.5, False, 0.8)
                c.line(_multi([rim, moved_path(rim, jdx, jdy)]), c.lw * 3.6, '#4e0a12', 255)
                xs = np.linspace(-mw * 0.97, mw * 0.97, 21)
                uu = np.clip(1.0 - (xs / mw) ** 2, 0.0, 1.0)
                tb = ym(xs) + ts * (yu(xs) - ym(xs))
                tpts = list(zip(xs.tolist(), (ym(xs) - 1.0).tolist())) + list(zip(xs[::-1].tolist(), tb[::-1].tolist()))
                teeth, TV = _fpath(hm, tpts, 4.6, True, 0.7)
                lb = ym(xs) - ts * 4.5 * uu ** 0.3
                lpts2 = list(zip(xs.tolist(), lb.tolist())) + list(zip(xs[::-1].tolist(), (ym(xs[::-1]) + 1.0).tolist()))
                lteeth = moved_path(_fpath(hm, lpts2, 4.6, True, 0.7)[0], jdx, jdy)
                c.fill(teeth, '#e4d9bf'); c.fill(lteeth, '#b9ad93')
                if det >= 1:
                    n = int(12 + 6 * max(0.0, P.grin_w))
                    seps, seps2 = [], []
                    for k in range(1, n):
                        x_ = -mw + 2 * mw * k / n
                        a0 = hm.map1(x_, float(ym(x_)), 4.7); a1 = hm.map1(x_ * 0.99, float(ym(x_) + ts * (yu(x_) - ym(x_))), 4.7)
                        if a0[2] > 0.02: seps.append(poly([(a0[0], a0[1]), (a1[0], a1[1])], False))
                        b0 = hm.map1(x_, float(ym(x_)), 4.7)
                        seps2.append(poly([(b0[0] + jdx, b0[1] + jdy), (b0[0] + jdx, b0[1] + jdy - ts * 4.0)], False))
                    if seps: c.line(_multi(seps), c.lw * 0.3, '#6e604c', 230)
                    if seps2: c.line(_multi(seps2), c.lw * 0.3, '#5a4e3c', 200)
                c.line(teeth, c.lw * 0.4, '#1a0a08', 220); c.line(lteeth, c.lw * 0.4, '#1a0a08', 220)
            c.line(hole, c.lw * 0.7)
        c.fill(Bm, skin)
        bb = Bm.getBounds()
        c.radial(Bm, -30.0 * lsd + hm.st * 20 + jdx, -40 + jdy, 165, [(0, skin, 0), (0.6, skin, 0), (0.88, sh, 120 + 40 * men), (1.0, sh, 190)], sy=1.1)
        c.grad(Bm, 0, bb.top() + bb.height() * 0.4, 0, bb.bottom(), [(0, dp, 0), (1, dp, 100 + 40 * men)])
        with c.clip(Bm):                                                         # the block's bevelled, shadowed edges
            c.line(Bm, c.lw * 3.0, dp, 70 + 40 * men)
        if light and light.get('under'):
            c.radial(Bm, hm.st * 20 + jdx, 150 + jdy, 220, [(0, light['under'], light.get('under_a', 120)), (1, light['under'], 0)], sy=0.8)
        if face_v > -0.35:
            xs = np.linspace(-mw, mw, 25)
            lpts = list(zip(xs.tolist(), ym(xs).tolist())) + list(zip(xs[::-1].tolist(), ylo(xs[::-1]).tolist()))
            llip, LV = _fpath(hm, lpts, 4.5, True, 0.7)
            llip = moved_path(llip, jdx, jdy)
            c.fill(llip, mix(sp['lip'], '#000000', 0.08))
            if det >= 1:
                hx, hy, hv = hm.map1(mw * 0.15, float(ylo(mw * 0.15)) - 2.0, 5.0)
                if hv > 0.1: c.fill(oval(hx + jdx, hy + jdy, 7 * hm.sx(mw * 0.15, 60), 1.4), '#ffffff', 170 * gl)
                ch_ = hm.map1(-6, 100, 4.0)
                if ch_[2] > 0.1: c.fill(oval(ch_[0] + jdx, ch_[1] + jdy, 9 * hm.sx(-6, 100), 3.2), '#ffffff', 110 * gl)
            c.line(llip, c.lw * 0.45, mix(sp['lip'], '#000000', 0.55))
            if det >= 1 and P.crack > 0.3:
                X_, Y_, V_ = hm.map([-30, -22, -26], [96, 104, 112], 2.5)
                if V_.min() > 0.08: c.line(moved_path(_pts_path(X_, Y_, False, 0.3), jdx, jdy), c.lw * 0.3, '#3a1a12', 210)
        c.line(Bm, c.lw * 1.1)
    if face_v > -0.35:
        # a small carved nose: a round tip, two nostrils, its shadow on the lip, a varnish spark
        nx, ny, nv = hm.map1(0, 20, 5.0)
        if nv > -0.4:
            fs_ = max(0.78, hm.sx(0, 20, 5.0))
            c.glow(nx + 2 * lsd * fs_, ny + 8, 13 * fs_, 5, dp, 80 + 40 * men)
            nose = oval(nx, ny, 9.0 * fs_, 8.0)
            c.fill(nose, mix(skin, sh, 0.12))
            c.radial(nose, nx - 3 * fs_, ny - 3, 12, [(0, mix(skin, '#ffffff', 0.2), 255), (0.65, mix(skin, sh, 0.12), 255), (1, sh, 255)])
            if abs(hm.st) < 0.55:
                for s2 in (-1, 1):
                    c.fill(oval(nx + s2 * 3.6 * fs_, ny + 4.8, 1.7 * fs_, 1.1), dp, 170)
            c.line(nose, c.lw * 0.65)
            c.fill(oval(nx - 3.0 * fs_, ny - 3.0, 2.3 * fs_, 1.6), '#ffffff', 220 * gl)
        # the hard lacquer highlights: one on the forehead, one on each cheekbone
        if gl > 0.02:
            fx, fy, fv = hm.map1(-2, -60, 2)
            if fv > 0.1:
                f_ = hm.sx(-2, -60)
                if det >= 1: c.glow(fx, fy, 18 * f_, 8, '#ffffff', 60 * gl)
                c.fill(smooth([(fx - 10 * f_, fy + 3.0), (fx - 2 * f_, fy - 1.8), (fx + 9 * f_, fy - 3.4), (fx + 2 * f_, fy + 1.2)], True, 0.8), '#ffffff', 200 * gl)
            for side in (-1, 1):
                hx, hy, hv = hm.map1(side * 55, 9, 2)
                if hv > 0.12:
                    f_ = hm.sx(side * 55, 9)
                    c.fill(oval(hx - 2 * f_, hy, 6.0 * f_, 2.4), '#ffffff', (175 if side * lsd < 0 else 120) * gl)
    hair = _winks_hair(c, hm, sp, P, det, sil_full)
    for side in (-1, 1):
        if -side * hm.st >= 0.25: _ear(c, hm, sp, side, skin, sh, det)
    _winks_cap(c, hm, sp, P, det, cl)
    if light and light.get('under'):                       # the flashlight under his chin: dark above, a hot glow below
        ua = light.get('under_a', 120)
        allp = union(sil_full, hair) if hair is not None else sil_full
        if front and Bm is not None: allp = union(allp, Bm)
        c.grad(allp, 0, -160, 0, 30 + J, [(0, '#05060a', 0.8 * ua), (0.6, '#05060a', 0.35 * ua), (1, '#05060a', 0)])
        c.radial(allp, hm.st * 20, 130 + J, 150, [(0, light['under'], 0.75 * ua), (0.5, light['under'], 0.3 * ua), (1, light['under'], 0)], sy=0.9)
        gls = [oval(g[0], g[1], g[2], g[3]) for g in (e_[4] for e_ in eyes.values() if e_ is not None) if g is not None]
        if gls: c.fill(_multi(gls), '#ffffff', 235)        # the glass still glints in the dark
    return hm


# ====================================================================================================== self-test
def _selftest():
    """python3 characters.py --selftest : acting regressions for the v2.1 fixes (prints and asserts)."""
    out = []
    # snap_turn overrides a held look-aside (critic: yaw must be < 0.05 at snap + 0.5 s), in either clip order
    for order in (0, 1):
        a = Acting('officer', seed=3); a.stare(-3)
        look = lambda: a.set(-2.0, None, 0.45, h_turn=0.9, lock=0.0, look_x=0.6)
        if order == 0: look(); a.snap_turn(0.15, 0.9, 0.0)
        else: a.snap_turn(0.15, 0.9, 0.0); look()
        P = a.at(0.65); yaw = P.turn + P.h_turn
        assert abs(yaw) < 0.05, ('snap_turn', order, yaw)
        P0 = a.at(-0.3); assert abs(P0.turn + P0.h_turn - 0.9) < 0.12, ('pre-snap yaw', P0.turn + P0.h_turn)
        out.append('snap order %d: yaw %.3f at snap+0.5 s, %.2f before' % (order, yaw, P0.turn + P0.h_turn))
    # blinks: shut (>0.5) for at most 2 frames at 30 fps
    a = Acting('you', seed=1)
    ts = np.arange(0, 40, 1 / 240.0); b = np.array([a._blink_amt(t) for t in ts]) > 0.5
    runs, r = [], 0
    for v in b:
        if v: r += 1
        elif r: runs.append(r); r = 0
    assert runs and max(runs) / 240.0 <= 0.067, ('blink', max(runs) / 240.0)
    out.append('blinks: %d, longest shut %.0f ms' % (len(runs), 1000 * max(runs) / 240.0))
    # phone at the ear: wrist ends up near the ear, not past the shoulder (no spike)
    for who in ('mum', 'you', 'officer', 'mom', 'dad', 'driver'):
        a = Acting(who, seed=2, arc=False); a.phone_to_ear(0.0, None, side=1)
        P = a.at(1.0); B = Body(CAST[who], P)
        S, E, W = _arm_data(CAST[who], B, P, 1)
        ear_y = B.yc - CAST[who]['hh'] / 2
        assert W[1] < B.y_sh and abs(W[1] - ear_y) < 0.6 * CAST[who]['hh'], ('phone_to_ear', who, W, ear_y)
        out.append('phone_to_ear %s: wrist %.0f above the shoulder, %.0f below the ear' % (who, B.y_sh - W[1], W[1] - ear_y))
    # lip sync follows the voice envelope (this film's narration): Owen's 'Look! I'm doing it! Grandpa said his mouth was
    # stuck.' (534.69-537.94 s); the driver's mouth (kept for the delivery cast) lags the voice by ~0.2 s on the same line
    env = voice_envelope()
    if env is not None:
        ts = np.arange(534.5, 538.2, 1 / 60.0)
        ev = np.array([10 ** (_env_db(env, t) / 20.0) for t in ts])
        iv = [(534.69, 535.09, 'Look'), (535.09, 535.86, "I'm doing it"), (536.05, 537.94, 'Grandpa said his mouth was stuck')]
        a = Acting('owen', seed=1); a.talk(iv)
        mo = np.array([a.at(t).m_open for t in ts])
        r = float(np.corrcoef(mo, ev)[0, 1])
        assert r > 0.5, ('lip sync', r)
        a2 = Acting('driver', seed=1, arc=False); a2.talk(iv)
        mo2 = np.array([a2.at(t).m_open for t in ts])
        best = max(range(0, 30), key=lambda k: np.corrcoef(mo2[k:], ev[:len(ev) - k])[0, 1] if k else np.corrcoef(mo2, ev)[0, 1])
        assert 0.12 <= best / 60.0 <= 0.3, ('mouth lag', best / 60.0)
        out.append('lip sync r = %.2f (Owen, 534.7 s); driver mouth lags the voice by %.2f s' % (r, best / 60.0))
        # Mister Winks's jaw: drops and snaps shut syllable by syllable on his joke (271.29-274.38 s), a clack each time
        ts = np.arange(271.0, 275.0, 0.01)
        ev = np.array([10 ** (_env_db(env, t) / 20.0) for t in ts])
        d = Acting('winks', seed=1); d.talk([(271.29, 274.38, "Why does a dummy always sit on the ventriloquist's knee")])
        jw = np.array([d.at(t).jaw for t in ts])
        rs = [float(np.corrcoef(jw[max(0, l):len(jw) + min(0, l)], ev[max(0, -l):len(ev) - max(0, l)])[0, 1]) for l in range(-8, 9)]
        cl = [e for e in d.events if e['name'] == 'dummy_clack']
        assert max(rs) > 0.65 and len(cl) >= 8 and jw.max() > 0.8 and np.mean(jw < 0.1) > 0.3, ('jaw sync', max(rs), len(cl))
        out.append('jaw sync r = %.2f (best lag %+.2f s), %d clacks on the joke' % (max(rs), (int(np.argmax(rs)) - 8) * 0.01, len(cl)))
    # the driver's smile widens stage by stage over the film, drops to nothing at 'no_smile', returns wider
    a = Acting('driver', seed=2)
    sm = [(tt, a.at(tt).smile, a.at(tt).grin) for tt in (30, 100, 160, 200, 345, 440, 460)]
    gr = [g for _, _, g in sm]
    assert gr[0] < gr[1] < gr[2] < gr[3] < gr[4] < gr[6] and sm[5][1] < 0.05, ('smile arc', sm)
    out.append('driver smile arc: ' + ', '.join('%.0fs %.2f/%.2f' % x for x in sm))
    ev = a.eye_flash(371.0, 0.5)
    assert a.at(371.2).eyeshine > 0.9 and a.at(371.8).eyeshine < 0.05 and ev[0]['name'] == 'stinger'
    # the box knocks two, then one (dad's knock)
    b = BoxActing(1); kv = b.knock(380.0)
    kt = [e['t'] for e in kv]
    assert len(kt) == 3 and abs((kt[1] - kt[0]) - 0.3) < 1e-6 and kt[2] - kt[1] > 0.6, kt
    assert b.at(kt[0] + 0.02)['bulge'] > 0.6 and b.at(kt[0] + 0.6)['bulge'] < 0.05
    out.append('box knock pattern %s' % ', '.join('%.2f' % x for x in kt))
    # escalate: mom trembles once the box knocks; the driver's face is still during DRIVER_STILL
    m = Acting('mom', seed=1); escalate(m, 380.0, 384.0)
    assert any(abs(m.at(t_).h_dx) > 0.5 for t_ in np.arange(380.2, 381.2, 0.05))
    d = Acting('driver', seed=1); escalate(d, 436.0, 446.0)
    assert d.at(441.0).smile < 0.05 and d.at(441.0).still > 0.95
    out.append('escalate: mom tremble at 380 s, driver still 436-446 s')
    # ---- dummy film
    # Mister Winks's arc: the grin widens and the pupils shrink stage by stage; asleep (lids shut) after "Goodnight, Owen"
    # until "he opens his eyes"; Owen inside = desperate brows
    w = Acting('winks', seed=2)
    g = [w.at(tt).grin_w for tt in (100, 178, 252, 318, 404, 530)]
    pu = [w.at(tt).pupil for tt in (100, 178, 252, 318, 404, 530)]
    assert all(g[i] < g[i + 1] for i in range(5)) and all(pu[i] > pu[i + 1] for i in range(5)), ('winks arc', g, pu)
    assert w.at(600.0).lid_l > 0.95 and w.at(658.5).lid_l < 0.05 and w.at(658.5).desperate > 0.95, 'winks asleep / awake'
    out.append('winks arc grin_w %s, asleep 567-656 s, Owen inside after' % ' '.join('%.2f' % x for x in g))
    # jaw: drop hangs, the slow close ends on a clack and stays shut; wink / try_wink lids; ticks from escalate
    w = Acting('winks', seed=3); ev = w.jaw_drop(1.0) + w.clack(3.0, 1.2)
    assert w.at(1.5).jaw > 0.95 and 0.05 < w.at(2.6).jaw < 0.9 and w.at(3.2).jaw < 0.01 and w.at(5.0).jaw < 0.01, 'jaw drop / clack'
    assert [e['name'] for e in ev] == ['dummy_jaw', 'dummy_clack']
    ev = w.wink(6.0)
    assert w.at(6.2).lid_l > 0.95 and w.at(6.2).lid_r < 0.05 and w.at(6.8).lid_l < 0.05 and len(ev) == 2
    ev = w.try_wink(8.0, gap=0.7)
    assert w.at(8.2).lid_l > 0.95 and w.at(8.2).lid_r < 0.05 and w.at(8.9).lid_r > 0.95, 'try_wink: both lids close'
    w2 = Acting('winks', seed=3); w2.sit_dummy(); escalate(w2, 405.0, 420.0)
    assert sum(1 for e in w2.events if e['name'] == 'wood_creak') >= 3, 'winks ticks'
    out.append('winks jaw drop / slow clack, wink, try_wink (both lids), %d ticks in 15 s at S4' % len(w2.events))
    # every new cast member draws in every view, full body and bust; composites draw
    set_render_size(480, 270)
    surf = skia.Surface(CFG.rw, CFG.rh); pen = Pen(surf.getCanvas()); surf.getCanvas().scale(CFG.k, CFG.k)
    for who in ('winks', 'grandpa', 'grandpa_bed', 'walter', 'walter74', 'mom', 'owen', 'owen_new', 'you'):
        for yaw in (0.0, 0.5, -0.5, 1.0, 2.0):
            draw(pen, who, 960, 1000, 700, Pose(turn=yaw, jaw=0.6, lid_l=0.5))
            draw_bust(pen, who, 960, 540, 0.6, Pose(h_turn=yaw, sit=0.5))
    d = Acting('winks', seed=1); d.sit_dummy(); o = Acting('owen', seed=1); o.vent_pose()
    draw_lap(pen, 'owen', 900, 1000, 600, o.at(1.0), d.at(1.0), side=1, m=1.32)
    y_ = Acting('you', seed=1); y_.hold_dummy(); d2 = Acting('winks', seed=1); d2.carried()
    draw_carry(pen, 'you', 900, 1000, 700, y_.at(1.0), d2.at(1.0))
    d3 = Acting('winks', seed=1); d3.face_down(); draw(pen, 'winks', 900, 1000, 400, d3.at(1.0))
    ax, ay = lap_anchor('owen', o.at(1.0), 1, 900, 1000, 600)
    assert 900 < ax < 1000 and 700 < ay < 900, ('lap anchor', ax, ay)
    out.append('all 9 dummy-film cast ids draw in 5 views (full + bust); draw_lap / draw_carry / face_down ok')
    for o_ in out: print(o_)
    print('characters self-test ok')


# ---------------------------------------------------------------------------------------- Bunnyman film additions
# The Bunnyman film's cast and staging tools live in characters_bunny.py, run here in this module's namespace (so they are
# part of `characters`, see BUNNY_API / CAST.md).
_BUNNY_SRC = os.path.join(_HERE, 'characters_bunny.py')
exec(compile(open(_BUNNY_SRC).read(), _BUNNY_SRC, 'exec'))


if __name__ == '__main__' and '--selftest' in sys.argv:
    _selftest()
