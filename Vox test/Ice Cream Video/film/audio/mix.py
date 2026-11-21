"""Final mix for "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE" (police v2 pipeline; the Bunnyman film, built on the dummy and delivery films' mix): narration with line voicing, the SFX
from sfx_cues.json, and the score stems from music_cues.json, mixed to the reference measurements in
analysis/AUDIO_SPEC.md.

CLI
    python3 mix.py <timeline.json> <vo_en.wav> <vo_ru_dub.wav | -> <cues dir> <out dir>
                   [--t0 S --t1 S]  render only a window (tests)     [--langs en]  (en,ru when a dub exists)
                   [--strict]       stop on a failed SFX cue instead of falling back (see "Never crashes" below)
                   [--who-fx X=hall,...]  voice FX for every line of a speaker that has no fx in the timeline
                                    (default X=hall: the hallway voice; --who-fx '' turns it off)
                   [--plan auto|off]  auto (default): a music_cues.json with no track_map gets the music map of
                                    audio/music_plan.py (film.py writes none); a sheet with no 'show' / 'winks' events
                                    gets the plan's IDENTITY (the show theme on the TV, Mister Winks's theme, the music
                                    box; film.py 'theme' cues inside those spans are dropped, the others play as Winks
                                    phrases); a sheet with no events also gets the plan's events and intensity.
                                    Windowed renders shift the map with the window.
                   [--score-stems]  also write the raw score stems of the window (stems/score_<stem>.wav; tests)
                   [--fallback]     force the placeholder drone instead of audio/score.py
                   [--bed-p50 -16]  target bed (music + SFX) 3 s short-term median, LU rel voice (true K-weighting)
                   [--bed-rel -13]  reference integrated bed level; the bed is capped at bed_rel + 1.5
                   [--voice-plr 11.5] narration peak-to-loudness ratio after the voice peak limiter
                   [--music-width 0.7] [--no-stems]
Reads <cues>/sfx_cues.json (list of {t, name, gain_db, pan, params, space}) and <cues>/music_cues.json
({duration, intensity, events}). Writes to <out>:
    mix_en.wav, mix_ru.wav        48 kHz 24-bit stereo, -14 LUFS integrated, true peak <= -1.5 dBTP
    stems/voice_en.wav, stems/voice_ru.wav, stems/sfx.wav, stems/music.wav   float32 at the final gain, after the bus
                                  processing and before the limiter (voice_xx + sfx + music = mix before limiting;
                                  the EN ducking is baked into sfx/music)
    mix_report.json               measured loudness, levels relative to the voice, events per minute, limiter use,
                                  cues_sha1 (sha1 of both cue sheets: `mix.py --check <cues> <out>` exits 1 when stale)

Line voicing (timeline line `fx`; LINE_FX below; each processed line is loudness-matched to the dry line)
  THIS film, the Ice Cream film (place = TAG_FX by line tag, then TEXT_FX by the line's words, then the line's own fx,
  then --who-fx; 'a+b' chains a then b; an unknown fx is left dry with a warning, never a crash):
    his         Mister Shiver's own voice: dry, too close, no breath (proximity lift, presence, breaths expanded down)
    radio       the two-way radio on channel three: 300 Hz-3 kHz, AGC and drive, gated hiss, squelch on and off
    mimic       his copies: the copied voice, a faint wrong double and HIS BELLS (chime_ice) under it; chained with
                the place: 'mimic+radio' (the fake Dad), 'mimic+door' (the fake Mom), 'mimic+truck' (the copied boy)
    door        through the front door and its clear glass strip (the porch behind, the hall around us)
    truck       his voice from the pink serving window: a little speaker horn, the cold street ('truck_far': across
                the street)
    memory      1958 (warm, far, a slow wow and a faint crackle); whisper (close and dry)
  THIS film, the Bus film (script/lines.py fx codes, placed by TAG_FX per line tag first; 'a+b' chains a then b;
  speaker W with no fx gets --who-fx W=his):
    tv          the 1994 Channel 6 tape on a school TV cart: VHS wow / flutter, the CRT speaker 160 Hz-5.8 kHz, hiss, buzz
    his         Mister Whistlestop in the room: tape hiss, 110 Hz-9 kHz (his warble is baked by tools/vo_voices.py)
    loudspeaker his bus PA horn: 430 Hz-3.5 kHz, driven, slap-back off the houses, a feedback ring on loud syllables
    door        through the front door with its frosted glass (wood boom, a glass leak of consonants, porch + hall)
    walkie      a kid's walkie: 300 Hz-3 kHz, clipped AGC, gated hiss, a squelch tail
    radio       bus 9's dash radio: 350 Hz-3.2 kHz, driven, static crackle, hum
    phone       the 911 operator on a cell phone: narrowband, light codec grain, gentle (the landline: 'landline')
    his_bus     a voice from inside his bus heard from the steps (Mina's voice imitated)
    mimic / mimic_slide  an imitation's wrong double + wobble / the slowing-tape slide (for a line that arrives
                unbaked; vo_voices.py already bakes both into this film's imitations, so TAG_FX gives them places only)
    memory, whisper  as below
  this film, the Bunnyman (script/lines.py fx codes; the character voices themselves are baked into vo_en.wav by
  tools/vo_voices.py, these only put them in their place):
    door       through the shut bathroom door (the girl under the door, Mom from the hall): 2.4 kHz top, the panel's
               220 Hz boom, the crack under the door leaking the consonants, the hallway behind, the tiled bathroom
               around us (-3 LU)
    slot       through the brass mail slot: 300 Hz-3.8 kHz, the slot's 1.1 kHz channel resonance and 3.6 ms comb, the
               porch behind, the hall around us (-1.5 LU)
    memory     Grandma remembered: warm (+2.5 dB at 260 Hz), the top softened, a small warm room, a faint wow (-1.5 LU)
    whisper    a close whisper: dry, 120 Hz high-pass, the breath's air and presence lifted, gentle 2:1 (0 LU)
    (no default fx for any speaker: --who-fx is empty; an unknown fx is left dry with a warning, never a crash)
  the dummy film (kept):
    tv         the real Walter crying on the 1974 tape, through the old console TV across the living room: 220 Hz-4.2 kHz,
               the cabinet's 330 Hz box, a 1.6 kHz cone peak, tape wow (0.5 Hz) and flutter (6 Hz), light saturation,
               tape hiss and mains hum under it, the room's first reflections (-1 LU)
    dummy      Mister Winks speaking in the room (Grandpa's voice, Mom's voice, the joke): a touch boxy and wooden (the
               hollow head: 480 Hz and 950 Hz resonances, a 2.2 ms comb from the carved cavity), a little of the room
               around him, top end eased (-1 LU)
    letter     the narrator reading Grandpa's letter: DRY (no change)
    memory     the hospital / bedtime memories (Grandpa's whisper, "See you in the morning, kiddo"): slightly distant,
               a little duller (150 Hz-6 kHz), a soft room, a very slow wow (-1.5 LU)
    upstairs   the voices calling from upstairs (Mom's, then yours): through the ceiling and down the stairwell, dull
               (3.2 kHz) with the stairwell's boom (250 Hz) and its reverb, still intelligible (-3 LU)
  earlier films (kept):
    doorbell   the driver through the doorbell camera's two-way audio, played by your phone: 260 Hz-6 kHz, camera
               presence, porch slap-back, light compression and grit, a faint camera hiss (-1 LU)
    box        a voice from INSIDE the cardboard box: dull (2.4 kHz), boxy cavity resonances (190 / 430 Hz), the tiny
               carton IR, and a hollow double 3 semitones down, 25 ms late, under it (-1.5 LU)
    phone      (the Doctor film) the old landline: 320-3300 Hz, carbon grit, 1 kHz honk, line hiss (-1 LU); the delivery
               film's 'phone' was dry app text
    recording  (the Doctor film) the phone system's recorded lady: telephone band, compressed, a voicemail grain (-1 LU)
    rooms      (the Doctor film) "It can wait." from every room: delayed, darker, wetter copies in the mono voice plus
               a wide stereo wash on the events bus (rooms_wash) (-1 LU)
    phone_call the police film's phone line (was 'phone'); phone_far; radio (police film)
    hall       a voice behind you in the hallway (short hall reverb, a little dull); not in the script's fx, offered for
               the X lines ("Hey, buddy"): mix.py's default --who-fx X=hall (lines with their own fx, the box
               lines, keep it)
    any other fx -> dry, with a warning (also an fx that is not a string, and an fx whose processing fails)
Never crashes on cue data: an SFX name is resolved by sfx.resolve() (aliases, then a keyword guess with a warning);
    a name nothing fits is skipped with a warning; an unknown space falls back to the name's default space with a
    warning; a cue whose recipe raises is retried with default params and space, then skipped with a warning (--strict
    restores the police behaviour: stop); a cue with no usable time, or a gain / pan that is not a number, is skipped or
    defaulted with a warning. Every fallback is listed in mix_report.json `sfx_fallbacks`.
    hazard_ticks (sfx.TIMED) gets cue_t = the cue's film time so the relay ticks lock to the drawn flashers.

Signal flow
    voice  -> v1 radio/phone line FX (kept from ../src/mix.py; radio drive 1.8; each processed line loudness-matched
              to the dry line, radio -2 LU, phone -1, phone_far -2) -> -14 LUFS -> 2.5:1 compression on the loudest
              syllables -> true-peak limiter at PLR 11.5 dB (the EN narration arrives at PLR 15.6 dB)
    sfx    -> sfx.render_event per cue (seeded by cue order, so renders repeat) -> gain/pan -> 3 buses:
              beds (ambience, room tone, static...), events, hits
    music  -> audio/score.py render(cues, duration) stems (placeholder D-A drone if score.py is missing or fails)
    bed bus = music + SFX beds + events + hits:
        - silence events in music_cues: SFX beds drop 6 dB (80 ms out, 400 ms back; score.py silences the music)
        - pre-hit dip: music and beds dip 8 dB over the 0.4 s before each SFX hit/stinger/braam/sub_drop/knock
          (score.py ducks its own hits; SFX beds also dip for the score's hits)
        - score bus: bounded auto tilt EQ toward the AUDIO_SPEC octave tilt, width 0.7, slow two-way leveler
        - dynamic bell cut at 1-4.5 kHz keyed by the voice (music/beds up to -5 dB, events -2 dB, hits 0)
        - sidechain duck from the voice envelope: music/beds -4.5 dB (0.25 s release), events -1.5 dB,
          hits (SFX hits bus + score hits stem) -6 dB (20 ms attack, 250 ms release), so reveal lines stay clear
        - foley dip: the music dips 2.5 dB under the SFX events bus (footsteps, keys, paper read over the score)
        - glue compressor 2:1 on the whole bed bus (slow, RMS, ~1-3 dB)
        - the Bunnyman's final mix: the voice always clear: while a line is spoken the bed (music + SFX) stays
          CLARITY_MARGIN_LU (6) under the narration's own 400 ms K-weighted level; the excess is cut (at most
          CLARITY_MAX_CUT_DB, over the whole block, 150 ms ramps); the hits' spare windows are left alone. The music /
          beds duck holds DUCK_HOLD_S (0.12 s) after each syllable. True silences (plan silences at level >= 0.95:
          "Then nothing.", the cut on "Seven.") also cut the SFX events and hits buses (no hit tail rings into them).
          The score renders from SCORE_SEED (fixed: a cue change no longer re-rolls every random choice of the score).
          Boosted hits: the hardest (boost >= 3.5: the face reveal, the swap) get the whole +6 dB boosted ceiling of
          the hits limiter, the other boosted hits +3 dB.
        - music gain solved so the bed's 3 s short-term median = voice - 16 LU and its integrated <= voice - 11.5 LU.
          These are the references re-measured with true per-channel K-weighting (bed integrated -12.5/-12.8/-13.4,
          short-term p10/p50/p90 about -20.8/-16.0/-9.2, LRA 12.8). AUDIO_SPEC's short-term numbers come from
          analysis/measure.py, whose kweight() runs lfilter along the channel axis of [n, 2] arrays (no frequency
          weighting, channels mixed), so they are biased by 3-6 dB depending on spectrum and L/R correlation.
    master = voice + bed -> loudness to -14 LUFS -> look-ahead true-peak limiter (4x oversampled, ceiling -1.7 dBTP),
             iterated until integrated is -14 +- 0.1 and TP <= -1.5
"""
import argparse, json, os, sys, time, traceback
import numpy as np, soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX

SR = 48000
TARGET = -14.0


def log(*a):
    print('[mix]', *a, flush=True)


# ============================================================================ voice FX (v1 logic, kept)
def band(x, lo, hi, order=4):
    return signal.sosfilt(signal.butter(order, [lo, hi], 'bandpass', fs=SR, output='sos'), x).astype(np.float32)


LINE_FX_LU = {'radio': -2.0, 'phone_call': -1.0, 'phone_far': -2.0, 'doorbell': -1.0, 'box': -1.5, 'hall': -1.0,
              'tv': -1.0, 'dummy': -1.0, 'memory': -1.5, 'upstairs': -3.0,
              'door': -3.0, 'through_door': -3.0, 'slot': -1.5, 'mail_slot': -1.5, 'whisper': 0.0, 'whispered': 0.0,
              'grandma': -1.5, 'phone': -1.0, 'recording': -1.0, 'rooms': -1.0, 'phone_system': -1.0,
              'every_room': -1.0, 'landline': -1.0}
# processed line vs the same line dry (K-weighted)


def radio_fx(x):
    y = band(x, 380, 3200); y = np.tanh(y * 1.8) / np.tanh(1.8)
    return (y + band(np.random.default_rng(1).normal(0, 1, len(y)).astype(np.float32), 1500, 6000) * 0.006) * 1.1


def phone_fx(x, far=False):
    y = band(x, 320, 3300, 6); y = np.tanh(y * 1.6) / np.tanh(1.6)
    if far: y = band(y, 300, 1500, 4) * 0.8
    return y * 1.05


def doorbell_fx(x):
    """The driver through the doorbell camera (porch mic -> app -> phone speaker); stays intelligible."""
    y = SX.lp(SX.hp(x, 260, 4), 6000, 4)                  # a camera mic and a phone speaker: no chest, no air
    y = SX.eq(y, ('peak', 2700, 3.0, 1.1), ('peak', 900, -1.5, 1.0), ('peak', 350, 1.5, 1.0))
    sl = np.zeros_like(y)                                   # porch slap-back (door, siding)
    for d, g in ((0.011, 0.12), (0.019, 0.08), (0.033, 0.04)):
        k = int(d * SR); sl[k:] += y[:-k] * g
    y = y + SX.lp(sl, 3500, 2)
    pk = float(np.abs(y).max()) + 1e-9
    y = SX.compress(y, SX.db(pk) - 14, 3.0, 0.003, 0.08)
    y = np.tanh(y / (np.abs(y).max() + 1e-9) * 1.4) / np.tanh(1.4) * pk
    hiss = band(np.random.default_rng(3).normal(0, 1, len(y)).astype(np.float32), 2000, 8000) * pk * 0.004
    return (y + hiss).astype(np.float32)


def box_fx(x):
    """A voice from inside the cardboard box: dull, boxy, close, with a hollow double a minor third down."""
    d = SX.eq(SX.lp(x, 2400, 4), ('peak', 190, 5.0, 1.2), ('peak', 430, 3.0, 1.4), ('peak', 950, -3.0, 1.0),
              ('ls', 120, 2.0, 0.7))
    w = SX.mono(SX.reverb(d, 'box', 0.5))[:len(x)]
    try:
        import librosa, warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            dn = librosa.effects.pitch_shift(x.astype(np.float32), sr=SR, n_steps=-3.0)
        dn = np.nan_to_num(dn)
        dn = SX.lp(dn, 1000, 2) * 0.2
        k = int(0.025 * SR); dd = np.zeros_like(w); dd[k:] = dn[:len(w) - k]
        w = w + dd
    except Exception as e:                                  # the double is a garnish: never fail the line on it
        log('box voice double skipped:', repr(e)[:80])
    pk = float(np.abs(w).max()) + 1e-9
    return (np.tanh(w / pk * 1.2) / np.tanh(1.2) * pk).astype(np.float32)


def hall_fx(x):
    """A voice behind you in the hallway."""
    d = SX.eq(SX.lp(x, 7000, 2), ('hs', 3000, -2.5, 0.7))
    return SX.mono(SX.reverb(d, 'hallway', 0.32))[:len(x)].astype(np.float32)


def _wow(x, depth=0.0025, hz=0.5, fl_depth=0.0006, fl_hz=6.2, seed=0):
    """Tape speed wobble: wow (slow) + flutter (fast), a variable-rate read (linear interpolation, no length change)."""
    n = len(x); rng = np.random.default_rng(seed)
    t = np.arange(n) / SR
    r = 1 + depth * np.sin(2 * np.pi * hz * t + rng.uniform(0, 6)) + fl_depth * np.sin(2 * np.pi * fl_hz * t + rng.uniform(0, 6))
    pos = np.clip(np.cumsum(r) - r[0], 0, n - 2); i = pos.astype(np.int64); f = (pos - i).astype(np.float32)
    return (x[i] * (1 - f) + x[i + 1] * f).astype(np.float32)


def tv_fx(x):
    """The real Walter's voice on the 1974 tape, through the old console TV across the room. Stays intelligible: the
    1-4 kHz band is kept, the lows and the air are gone."""
    y = _wow(x, 0.0025, 0.5, 0.0006, 6.2, 11)
    y = SX.lp(SX.hp(y, 220, 4), 4200, 4)
    y = SX.eq(y, ('peak', 1600, 3.0, 1.0), ('peak', 330, 2.0, 2.0), ('peak', 900, -1.0, 1.2))
    pk = float(np.abs(y).max()) + 1e-9
    y = (np.tanh(y / pk * 1.5) / np.tanh(1.5) * pk).astype(np.float32)
    sl = np.zeros_like(y)                                   # the room: TV cabinet -> walls -> you
    for d, g in ((0.006, 0.16), (0.013, 0.1), (0.024, 0.05)):
        k = int(d * SR); sl[k:] += y[:-k] * g
    y = y + SX.lp(sl, 3000, 2)
    rng = np.random.default_rng(12); t = np.arange(len(y)) / SR
    hiss = band(rng.normal(0, 1, len(y)).astype(np.float32), 1800, 8000) * pk * 0.006
    hum = (np.sin(2 * np.pi * 60 * t) + 0.4 * np.sin(2 * np.pi * 180 * t)).astype(np.float32) * pk * 0.004
    return (y + hiss + hum).astype(np.float32)


def dummy_fx(x):
    """Mister Winks speaking (any voice he does): a touch boxy and wooden, close, in the room."""
    y = SX.eq(SX.lp(x, 9500, 2), ('peak', 480, 2.5, 1.6), ('peak', 950, 1.5, 2.0), ('peak', 2300, 1.0, 1.0),
              ('ls', 140, -2.0, 0.7))
    k = int(0.0022 * SR); c = np.zeros_like(y); c[k:] = y[:-k] * 0.15         # the carved hollow: a short comb
    y = y + c
    return SX.mono(SX.reverb(y, 'living', 0.1))[:len(x)].astype(np.float32)


def memory_voice_fx(x):
    """Grandma remembered ("This is our family knock"): warm and a little distant. The low-mids warmed (+2.5 dB at
    260 Hz), the top softened (-3.5 dB from 3 kHz, 6.5 kHz low-pass), her kitchen around her (a small warm room,
    18 %, 12 ms early), the faintest slow wow of an old memory; every word stays clear (-1.5 LU)."""
    y = _wow(x, 0.0010, 0.3, 0.0, 6.0, 13)
    y = SX.eq(SX.lp(SX.hp(y, 110, 2), 6500, 2), ('peak', 260, 2.5, 0.9), ('hs', 3000, -3.5, 0.7), ('peak', 1200, 0.8, 1.0))
    y = SX.mono(SX.reverb(y, 'living', 0.18, 0.012))[:len(x)]
    return SX.mono(SX.reverb(y, 'hall', 0.06, 0.02, hpf=250))[:len(x)].astype(np.float32)


def door_fx(x):
    """A voice from the other side of the shut bathroom door (the little girl's "Don't let her do the trick", Mom's
    "GET OUT OF MY HOUSE", "It's over, sweetheart", "It's sunrise, babies"): the solid-core door takes the top off
    (2.4 kHz, a 5 dB high shelf down from 1.5 kHz) and gives its panel boom (220 Hz); the crack under the door leaks
    a little air (1.5-5 kHz, 9 %, so the consonants survive); the hallway behind it; the small tiled bathroom we
    hear it in. Intelligible but unmistakably through a door (-3 LU)."""
    d = SX.eq(SX.lp(x, 2400, 2), ('peak', 220, 4.0, 1.1), ('peak', 520, 1.5, 1.3), ('hs', 1500, -5.0, 0.7))
    gap = band(x, 1500, 5000, 2) * 0.09
    y = SX.mono(SX.reverb(d + gap, 'hallway', 0.3, 0.004))[:len(x)]
    return SX.mono(SX.reverb(y, 'bathroom', 0.16, 0.001))[:len(x)].astype(np.float32)


def slot_fx(x):
    """The voice through the brass mail slot ("Mama?", "Is she humming?"): close to the opening but squeezed
    through it: 300 Hz-3.8 kHz, the slot's narrow channel resonating (+5 dB at 1.1 kHz), a 3.6 ms comb from its
    depth, the porch outside behind the voice, the front hall around us (-1.5 LU)."""
    y = SX.eq(band(x, 300, 3800, 2), ('peak', 1100, 5.0, 1.4), ('peak', 2400, 2.0, 2.0), ('ls', 300, -2.0, 0.7))
    k = int(0.0036 * SR); c = np.zeros_like(y); c[k:] = y[:-k] * 0.35
    y = y + c
    y = SX.mono(SX.reverb(y, 'porch', 0.12, 0.0))[:len(x)]
    return SX.mono(SX.reverb(y, 'hallway', 0.18, 0.002))[:len(x)].astype(np.float32)


def whisper_fx(x):
    """A whisper close to the ear (June at the window, the counts, "I know it's you", the old body's question):
    intimate and dry: below 120 Hz removed (no handling rumble), the breath's air lifted (+2.5 dB from 4 kHz) and the
    presence (+1.5 dB at 2.5 kHz), gentle 2:1 compression so every whispered consonant reads, no room."""
    y = SX.eq(SX.hp(x, 120, 2), ('hs', 4000, 2.5, 0.7), ('peak', 2500, 1.5, 1.0), ('peak', 300, -1.0, 1.0))
    pk = float(np.abs(y).max()) + 1e-9
    return SX.compress(y, SX.db(pk) - 12, 2.0, 0.004, 0.1).astype(np.float32)


def upstairs_fx(x):
    """A voice calling from upstairs: through the ceiling and down the stairwell (dull, boomy, reverberant), but every
    word still clear."""
    y = SX.eq(SX.lp(x, 3800, 2), ('peak', 250, 3.0, 1.0), ('hs', 1800, -3.0, 0.7), ('peak', 1100, 1.5, 1.2))
    return SX.mono(SX.reverb(y, 'hallway', 0.45, 0.006))[:len(x)].astype(np.float32)


# ---- the Doctor film's voice FX (script/lines.py fx codes: phone, recording, rooms; door, whisper, memory as above)
def phone_line_fx(x):
    """'phone': a voice on the old landline (Doctor Halverson at 3 AM, the calm voice of 1979): telephone band
    320-3300 Hz, the carbon earpiece's small grit and 1 kHz honk, line hiss under it. Intelligible (-1 LU)."""
    y = band(x, 320, 3300, 6)
    y = SX.eq(y, ('peak', 1000, 3.0, 1.0), ('peak', 2300, 1.5, 1.4))
    pk = float(np.abs(y).max()) + 1e-9
    y = np.tanh(y / pk * 1.8) / np.tanh(1.8) * pk
    hiss = band(np.random.default_rng(5).normal(0, 1, len(y)).astype(np.float32), 400, 3300, 2) * pk * 0.006
    return (y + hiss).astype(np.float32)


def recording_fx(x):
    """'recording': the phone system's recorded lady ("Your call is important to us. Please hold."): the telephone
    band, a produced, compressed, slightly too-clean voice (tight 3:1, presence at 1.8 kHz), a faint digital
    graininess (light companding), no room at all (-1 LU)."""
    y = band(x, 300, 3400, 6)
    y = SX.eq(y, ('peak', 1800, 2.5, 1.0), ('peak', 500, -1.5, 1.0))
    pk = float(np.abs(y).max()) + 1e-9
    y = SX.compress(y, SX.db(pk) - 16, 3.0, 0.002, 0.06)
    mu = 255.0; q = 64.0                                   # mu-law with a coarse step: the voicemail grain
    c = np.sign(y) * np.log1p(mu * np.abs(y) / (np.abs(y).max() + 1e-9)) / np.log1p(mu)
    c = np.round(c * q) / q
    y = np.sign(c) * (np.expm1(np.abs(c) * np.log1p(mu)) / mu) * (np.abs(y).max() + 1e-9)
    return y.astype(np.float32)


def rooms_fx(x):
    """'rooms': the Waiting Man's "It can wait." from every room of the house at once: the line itself a little
    back, and three more of it from the hallway, the living room and Grandpa's chair (37 / 81 / 133 ms late, each
    darker and wetter: further away). The mono voice carries the sum; mix.py adds rooms_wash() (the same copies
    spread wide in stereo) on the events bus so it surrounds the listener (-1 LU)."""
    y = x * 0.6
    for d, lp_hz, ir, wet, g in ((0.037, 3200, 'hallway', 0.6, 0.45), (0.081, 2300, 'living', 0.7, 0.4),
                                 (0.133, 1700, 'hall', 0.85, 0.35)):
        k = int(d * SR); c = np.zeros_like(x); c[k:] = x[:-k]
        c = SX.mono(SX.reverb(SX.lp(c, lp_hz, 2), ir, wet, 0.004))[:len(x)]
        y = y + c * g
    return y.astype(np.float32)


def rooms_wash(y):
    """The stereo garnish of a 'rooms' line: three decorrelated copies of the processed line panned hard left,
    hard right and far centre, delayed and darkened (the house speaking from everywhere)."""
    out = np.zeros((len(y) + int(0.4 * SR), 2), np.float32)
    for d, p, lp_hz, g in ((0.051, -0.95, 2600, 0.5), (0.097, 0.95, 2200, 0.5), (0.17, 0.0, 1500, 0.35)):
        k = int(d * SR)
        c = SX.mono(SX.reverb(SX.lp(y, lp_hz, 2), 'hall', 0.8, 0.01))
        c = SX.st(SX.pan(c, p))
        n = min(len(c), len(out) - k); out[k:k + n] += c[:n] * g
    return out


ROOMS_WASH = []                                      # (start sample, stereo) collected by apply_line_fx


# ---- the Bus film's voice FX (script/lines.py fx codes: tv, loudspeaker, door, mimic, whisper, memory, phone; plus
# walkie, radio and the per-line places in TAG_FX). Chains: an fx 'a+b' runs a then b (e.g. 'mimic+door').
def tv1994_fx(x):
    """'tv': Mister Whistlestop on the 1994 Channel 6 tape, played off a school TV cart (and in the hook): a VHS
    linear track (wow 0.35 % at 0.45 Hz, flutter at 6.5 Hz), the CRT's small speaker (160 Hz-5.8 kHz, a 1.5 kHz
    cone peak, a 420 Hz box), soft tape saturation, tape hiss and the 60 Hz head-switch buzz under it (-1 LU)."""
    y = _wow(x, 0.0035, 0.45, 0.0008, 6.5, 21)
    y = SX.lp(SX.hp(y, 160, 4), 5800, 4)
    y = SX.eq(y, ('peak', 1500, 3.0, 1.0), ('peak', 420, 2.0, 1.6), ('peak', 3200, -1.5, 1.0))
    pk = float(np.abs(y).max()) + 1e-9
    y = (np.tanh(y / pk * 1.6) / np.tanh(1.6) * pk).astype(np.float32)
    rng = np.random.default_rng(22); t = np.arange(len(y)) / SR
    hiss = band(rng.normal(0, 1, len(y)).astype(np.float32), 1800, 7500) * pk * 0.008
    buzz = (np.sign(np.sin(2 * np.pi * 59.94 * t)) * 0.3 + np.sin(2 * np.pi * 59.94 * t)).astype(np.float32)
    return (y + hiss + SX.lp(buzz, 400, 2) * pk * 0.004).astype(np.float32)


def his_fx(x):
    """'his': Mister Whistlestop speaking in the room (the default for W lines with no fx: "Last stop! Everybody
    counted?", the aisle speech, the lure, the taunt): his bright 1994 voice still on tape: a breath of hiss under
    it, slightly band-limited (110 Hz-9 kHz), never so dirty that a word goes; the warble itself is baked into the
    voice by tools/vo_voices.py (W: wow 0.3 %), so none is added here (-0.5 LU)."""
    y = SX.eq(SX.lp(SX.hp(x, 110, 2), 9000, 2), ('peak', 1700, 1.5, 1.0))   # (tools/vo_voices.py bakes his wow)
    pk = float(np.abs(y).max()) + 1e-9
    hiss = band(np.random.default_rng(24).normal(0, 1, len(y)).astype(np.float32), 2500, 8000) * pk * 0.004
    return (y + hiss).astype(np.float32)


def loudspeaker_fx(x):
    """'loudspeaker': his bus PA horn at the curb ("Sami. First grade...", "Great smile, Mina!", "Seat's saved"):
    the horn's narrow band (430 Hz-3.5 kHz, a 1.9 kHz honk), driven hard, slap-back off the house fronts (58 / 131 ms),
    the street around it, and a touch of feedback: a 2.35 kHz ring that follows the loudest syllables (-1.5 LU)."""
    y = SX.eq(band(x, 430, 3500, 4), ('peak', 1900, 6.0, 1.3), ('peak', 850, 2.0, 1.0))
    pk = float(np.abs(y).max()) + 1e-9
    y = (np.tanh(y / pk * 2.4) / np.tanh(2.4) * pk).astype(np.float32)
    env = SX.follow(np.abs(y), SX.coef(0.01), SX.coef(0.25))
    t = np.arange(len(y)) / SR
    ring = np.sin(2 * np.pi * 2350 * t * (1 + 0.003 * np.sin(2 * np.pi * 2.5 * t))).astype(np.float32)
    y = y + ring * np.clip(env / (env.max() + 1e-9) - 0.6, 0, 1) * pk * 0.25
    sl = np.zeros_like(y)
    for d, g in ((0.058, 0.3), (0.131, 0.18), (0.22, 0.08)):
        k = int(d * SR); sl[k:] += y[:-k] * g
    y = y + SX.lp(sl, 2600, 2)
    return SX.mono(SX.reverb(y, 'street', 0.28, 0.01))[:len(x)].astype(np.float32)


def front_door_fx(x):
    """'door': a voice on the porch heard through the front door with its frosted-glass panel (the roll call,
    "Almost.", the fake Grandma): the wood takes the top (2.6 kHz, -4 dB shelf from 1.6 kHz) and booms (230 Hz), the
    glass panel leaks a thin band of consonants (1.6-4.5 kHz, 14 %), the porch's air behind the voice, the front hall
    around us. Clearly outside, every word clear (-2.5 LU)."""
    d = SX.eq(SX.lp(x, 2600, 2), ('peak', 230, 3.5, 1.1), ('peak', 560, 1.5, 1.3), ('hs', 1600, -4.0, 0.7))
    glass = band(x, 1600, 4500, 2) * 0.14
    y = SX.mono(SX.reverb(d + glass, 'porch', 0.22, 0.002))[:len(x)]
    return SX.mono(SX.reverb(y, 'hallway', 0.22, 0.002))[:len(x)].astype(np.float32)


def front_door_clear_fx(x):
    """'door_clear' (sound fix round 3): the front door for the scare words ("Almost.", the roll call's "Mina?",
    "...Clever."): the same wood and porch, but a softer top cut (4.2 kHz, -2 dB shelf from 2.5 kHz), the glass panel's
    consonants louder (1.6-4.5 kHz, 35 %) and +3 dB presence at 3 kHz, so the recogniser reads the word under the hit."""
    d = SX.eq(SX.lp(x, 4200, 2), ('peak', 230, 2.5, 1.1), ('peak', 3000, 3.0, 1.0), ('hs', 2500, -2.0, 0.7))
    glass = band(x, 1600, 4500, 2) * 0.35
    y = SX.mono(SX.reverb(d + glass, 'porch', 0.16, 0.002))[:len(x)]
    return SX.mono(SX.reverb(y, 'hallway', 0.14, 0.002))[:len(x)].astype(np.float32)


def walkie_fx(x):
    """'walkie': a kid's walkie-talkie: 300 Hz-3 kHz, hard-clipped through a little AGC, the channel's hiss gated
    with the voice, a squelch tail after the last word (-1 LU)."""
    y = band(x, 300, 3000, 6)
    pk = float(np.abs(y).max()) + 1e-9
    y = SX.compress(y, SX.db(pk) - 18, 4.0, 0.002, 0.08)
    pk = float(np.abs(y).max()) + 1e-9
    y = np.clip(y / pk * 2.2, -1, 1) * pk * 0.7
    env = SX.follow(np.abs(y), SX.coef(0.005), SX.coef(0.12))
    rng = np.random.default_rng(25)
    hiss = band(rng.normal(0, 1, len(y)).astype(np.float32), 500, 3500) * pk * 0.03 * (env / (env.max() + 1e-9) > 0.05)
    y = (y + hiss).astype(np.float32)
    k = min(len(y), int(0.16 * SR))
    tail = band(rng.normal(0, 1, k).astype(np.float32), 600, 4000) * pk * 0.25 * np.exp(-np.arange(k) / (0.05 * SR))
    last = int(np.flatnonzero(env > env.max() * 0.05)[-1]) if (env > env.max() * 0.05).any() else len(y) - k
    a = min(last, len(y) - k); y[a:a + k] += tail.astype(np.float32)[:len(y) - a]
    return y


def dash_radio_fx(x):
    """'radio': bus 9's dash radio to the depot (his voice in Grandma's voice: "The third was a boy in the back."):
    an AM-ish band 350-3200 Hz, a 1.3 kHz cone peak, driven, the static crackling under it and a soft 120 Hz hum
    (-2 LU)."""
    y = SX.eq(band(x, 350, 3200, 4), ('peak', 1300, 3.0, 1.0))
    pk = float(np.abs(y).max()) + 1e-9
    y = (np.tanh(y / pk * 2.0) / np.tanh(2.0) * pk).astype(np.float32)
    rng = np.random.default_rng(26); t = np.arange(len(y)) / SR
    st_ = band(rng.normal(0, 1, len(y)).astype(np.float32), 800, 4000) * pk * 0.02
    cr = np.zeros(len(y), np.float32)
    for i in rng.integers(0, len(y), int(len(y) / SR * 25)):
        cr[i:i + 40] += rng.uniform(-1, 1) * pk * 0.15
    hum = (np.sin(2 * np.pi * 120 * t) * pk * 0.01).astype(np.float32)
    return (y + st_ + band(cr, 1000, 5000, 2) + hum).astype(np.float32)


def cell_fx(x):
    """'phone': the 911 operator on Grandma's cell phone, held at Mina's ear ("Officers are on the way."): a clean
    narrowband call (300-3400 Hz), light codec grain, a gentle 2:1: warm and competent, never harsh (-1 LU)."""
    y = SX.eq(band(x, 300, 3400, 6), ('peak', 1200, 1.5, 1.0), ('peak', 2600, 1.0, 1.4))
    pk = float(np.abs(y).max()) + 1e-9
    y = SX.compress(y, SX.db(pk) - 14, 2.0, 0.004, 0.1)
    mu = 255.0; q = 96.0
    a = np.abs(y).max() + 1e-9
    c = np.sign(y) * np.log1p(mu * np.abs(y) / a) / np.log1p(mu)
    c = np.round(c * q) / q
    return (np.sign(c) * (np.expm1(np.abs(c) * np.log1p(mu)) / mu) * a).astype(np.float32)


def _pitch(x, semis):
    try:
        import librosa, warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return np.nan_to_num(librosa.effects.pitch_shift(x.astype(np.float32), sr=SR, n_steps=semis)).astype(np.float32)
    except Exception as e:
        log('pitch shift skipped:', repr(e)[:80]); return None


def mimic_fx(x):
    """'mimic': his imitations (Sami's "Here!", Grandma at the door, "It's me, sweetheart.", Mina's "Sami! Back
    here!"): the imitated voice almost perfect, with a faint WRONG double (the same words 0.45 semitone sharp, 14 ms
    late, 15 dB down: two mouths not quite agreeing) and a slight tape wobble (0.3 % at 0.8 Hz) (-0.5 LU)."""
    y = _wow(x, 0.003, 0.8, 0.0004, 5.5, 27)
    d = _pitch(x, 0.45)
    if d is not None:
        k = int(0.014 * SR); dd = np.zeros_like(y); dd[k:] = d[:len(y) - k]
        y = y + SX.lp(dd, 6000, 2) * 0.18
    return y.astype(np.float32)


MIMIC_SLIDE_EXTRA = 0.55                     # s the slide may run past the line's end (the gap before the next line)


def mimic_slide_fx(x):
    """'mimic_slide': "...Clever.": the imitation ends and the voice slides down like a slowing tape: the first 15 %
    at speed, then the tape decelerates to half speed (an octave down) by the end, so the word stretches (the output
    is longer than the line, up to MIMIC_SLIDE_EXTRA s into the gap after it), with the mimic's wobble (-0.5 LU)."""
    y = mimic_fx(x)
    n_in = len(y)
    n_out = int(n_in * 1.32)
    u = np.linspace(0, 1, n_out)
    r = 1.0 - 0.5 * np.clip((u - 0.15) / 0.85, 0, 1) ** 1.2
    pos = np.cumsum(r); pos = pos / pos[-1] * (n_in - 2)
    i = pos.astype(np.int64); f = (pos - i).astype(np.float32)
    z = y[i] * (1 - f) + y[i + 1] * f
    z = SX.lp(z, 9000, 2)
    w = np.ones(len(z), np.float32); k = int(0.08 * SR); w[-k:] = np.linspace(1, 0, k)
    return (z * w).astype(np.float32)


def his_bus_fx(x):
    """'his_bus': a voice from inside his bus, heard from the steps (Mina's voice from inside: "Sami! Back here!",
    "Don't answer her."): a small hard metal box (the car IR, 26 %), a little dull, his tape's hiss (-1 LU)."""
    y = SX.eq(SX.lp(x, 7500, 2), ('peak', 320, 1.5, 1.2))
    y = SX.mono(SX.reverb(y, 'car', 0.26, 0.001))[:len(x)]
    pk = float(np.abs(y).max()) + 1e-9
    return (y + band(np.random.default_rng(28).normal(0, 1, len(y)).astype(np.float32), 2500, 8000) * pk * 0.003).astype(np.float32)


# TAG_FX: the timeline's line tags -> the place each line is heard in (lines.py gives the voice's kind). The
# imitations' "wrong" second voice, warble and sag, and the "...Clever." tape slide, are BAKED into the voice by
# tools/vo_voices.py (W_della_*, W_sami_*, W_mina_*, W_della_clever: _WRONG and tape=(0.40, 0.60)), so the imitation
# lines get only their place here; mix.py's own 'mimic' / 'mimic_slide' stay for a line that arrives unbaked.
TAG_FX = {
    'mimic_sami_here': 'door', 'mimic_della_door': 'door', 'mimic_della_no_time': 'door',
    'mimic_della_clever': 'door_clear', 'mimic_della_sweetheart': 'door', 'mimic_della_lighthouse': 'door',
    'mimic_della_radio': 'radio', 'mimic_mina_back_here': 'his_bus', 'mimic_mina_dont_answer': 'his_bus',
    'smart_one': 'whisper+door',
    'roll_della': 'his+door', 'roll_mina': 'his+door_clear', 'roll_sami': 'his+door', 'almost': 'his+door_clear',
    'reads_post': 'his+loudspeaker', 'great_smile_mina': 'his+loudspeaker', 'know_your_name_bus': 'his+loudspeaker',
    'seats_saved': 'his+loudspeaker', 'officers': 'phone', 'hook_voice': 'tv', 'tape_card': 'tv',
    'tape_ride_right': 'tv'}


LINE_FX = {'radio': radio_fx, 'phone_call': phone_fx, 'phone_far': lambda x: phone_fx(x, True), 'doorbell': doorbell_fx,
           'box': box_fx, 'hall': hall_fx, 'phone': None, 'dry': None, 'none': None,
           'tv': tv_fx, 'dummy': dummy_fx, 'memory': memory_voice_fx, 'upstairs': upstairs_fx, 'letter': None,
           'television': tv_fx, 'tape': tv_fx, 'flashback': memory_voice_fx, 'ceiling': upstairs_fx,
           # the Bunnyman film (script/lines.py fx codes)
           'door': door_fx, 'slot': slot_fx, 'whisper': whisper_fx, 'mail_slot': slot_fx, 'through_door': door_fx,
           'grandma': memory_voice_fx, 'whispered': whisper_fx,
           # the Doctor film: 'phone' is a real phone line again (the delivery film's 'phone' was dry app text)
           'phone': phone_line_fx, 'recording': recording_fx, 'rooms': rooms_fx, 'phone_system': recording_fx,
           'every_room': rooms_fx, 'landline': phone_line_fx}
# the Bus film: 'tv' is the 1994 tape, 'door' the front door with its frosted glass, 'radio' bus 9's dash radio,
# 'phone' the 911 call on a cell phone (the landline stays reachable as 'landline'); 'his' is W's default
LINE_FX.update({'tv': tv1994_fx, 'tape': tv1994_fx, 'television': tv1994_fx, 'his': his_fx,
                'loudspeaker': loudspeaker_fx, 'pa': loudspeaker_fx, 'speaker_horn': loudspeaker_fx,
                'door': front_door_fx, 'door_clear': front_door_clear_fx, 'front_door': front_door_fx, 'through_door': front_door_fx,
                'walkie': walkie_fx, 'walkie_talkie': walkie_fx, 'radio': dash_radio_fx, 'dash_radio': dash_radio_fx,
                'police_radio': radio_fx, 'phone': cell_fx, 'cell': cell_fx, '911': cell_fx, 'mimic': mimic_fx,
                'mimic_slide': mimic_slide_fx, 'slide': mimic_slide_fx, 'his_bus': his_bus_fx})
LINE_FX_LU.update({'tv': -1.0, 'his': -0.5, 'loudspeaker': -1.5, 'pa': -1.5, 'door': -2.5, 'door_clear': -1.5, 'front_door': -2.5,
                   'walkie': -1.0, 'radio': -2.0, 'dash_radio': -2.0, 'phone': -1.0, 'cell': -1.0, 'mimic': -0.5,
                   'mimic_slide': -0.5, 'slide': -0.5, 'his_bus': -1.0})


# ==================================================================================== THIS film: the Ice Cream film
def _expander(y, below_db=-30.0, ratio=3.0, att=0.002, rel=0.06):
    """Downward expander under below_db (rel the peak): breaths and mouth noise between words sink, words untouched."""
    pk = float(np.abs(y).max()) + 1e-9
    env = SX.follow(np.abs(y), SX.coef(att), SX.coef(rel))
    lv = 20 * np.log10(env / pk + 1e-9)
    g = np.where(lv < below_db, 10 ** ((lv - below_db) * (ratio - 1) / 20), 1.0)
    return (y * np.maximum(g, 10 ** (-24 / 20))).astype(np.float32)


def his_ice_fx(x):
    """'his': Mister Shiver's own voice (the default for his lines with no place): DRY, TOO CLOSE and with NO BREATH:
    a proximity lift (+3 dB at 140 Hz), presence (+2 dB at 3.2 kHz), a sugary sheen (+1.5 dB from 7 kHz), no room at
    all, and every breath / mouth noise between words pushed down (a 3:1 expander under -30 dB): he never breathes
    (-0.5 LU)."""
    y = SX.eq(SX.hp(x, 70, 2), ('peak', 140, 3.0, 0.8), ('peak', 3200, 2.0, 1.0), ('hs', 7000, 1.5, 0.7))
    return _expander(y, -30.0, 3.0)


def twoway_radio_fx(x):
    """'radio': the two-way radio on channel three (the real Dad, and the fake one inside 'mimic+radio'): 300 Hz-3 kHz,
    a little AGC and drive, the channel hiss gated with the voice, the squelch OPENING (a key-up click and a burst
    of hiss) before the first word and the squelch tail after the last (-2 LU)."""
    y = band(x, 300, 3000, 6)
    pk = float(np.abs(y).max()) + 1e-9
    y = SX.compress(y, SX.db(pk) - 16, 3.0, 0.002, 0.08)
    pk = float(np.abs(y).max()) + 1e-9
    y = (np.tanh(1.8 * y / pk) / np.tanh(1.8) * pk * 0.8).astype(np.float32)
    env = SX.follow(np.abs(y), SX.coef(0.005), SX.coef(0.15))
    rng = np.random.default_rng(31)
    on = env / (env.max() + 1e-9) > 0.04
    hiss = band(rng.normal(0, 1, len(y)).astype(np.float32), 500, 3500) * pk * 0.025 * on
    y = (y + hiss).astype(np.float32)
    act = np.flatnonzero(on)
    if len(act):
        k = min(int(0.09 * SR), len(y))                    # key-up: a click and a short burst before the first word
        a = max(0, int(act[0]) - k)
        burst = band(rng.normal(0, 1, k).astype(np.float32), 700, 3800) * pk * 0.18 * np.linspace(1, 0.2, k)
        burst[:int(0.004 * SR)] += pk * 0.4 * np.hanning(int(0.004 * SR))
        y[a:a + k] += burst[:len(y) - a]
        k2 = min(int(0.16 * SR), len(y))                   # the squelch tail after the last word
        b = min(int(act[-1]), len(y) - k2)
        tail = band(rng.normal(0, 1, k2).astype(np.float32), 600, 4000) * pk * 0.22 * np.exp(-np.arange(k2) / (0.05 * SR))
        y[b:b + k2] += tail
    return y.astype(np.float32)


_BELLS = {}


def _bells_for(n, seed=5):
    """His bells (audio/chime_ice.py bells) as a mono signal of n samples, peak 1."""
    k = (n, seed)
    if k not in _BELLS:
        try:
            import chime_ice as CH
            b = SX.mono(CH.bells(n / SR + 0.5, seed))[:n]
        except Exception as e:
            log('WARNING: chime bells unavailable for mimic (%s)' % repr(e)[:60]); b = np.zeros(n, np.float32)
        b = np.pad(b, (0, max(0, n - len(b))))
        _BELLS[k] = (b / (np.abs(b).max() + 1e-9)).astype(np.float32)
    return _BELLS[k]


MIMIC_BELLS_DB = -24.0     # the bells under a copy, rel the copied voice's peak: faint (a fair-play tell, audio only)


def mimic_ice_fx(x):
    """'mimic': his copies (the fake Dad on the radio, the fake Mom at the door, the copied little boy): the copied
    voice almost perfect, a faint WRONG double (the same words 0.4 semitone sharp, 16 ms late, 17 dB down: two mouths
    not quite agreeing) and HIS BELLS under it (chime_ice bells, MIMIC_BELLS_DB under the voice's peak), so the
    place chained after it ('mimic+radio', 'mimic+door', 'mimic+truck') carries the bells too (-0.5 LU)."""
    y = _wow(x, 0.002, 0.7, 0.0003, 5.5, 29)
    d = _pitch(x, 0.4)
    if d is not None:
        k = int(0.016 * SR); dd = np.zeros_like(y); dd[k:] = d[:len(y) - k]
        y = y + SX.lp(dd, 6000, 2) * 0.14
    pk = float(np.abs(x).max()) + 1e-9
    env = SX.follow(np.abs(x), SX.coef(0.05), SX.coef(0.6))
    gate = np.clip(env / (env.max() + 1e-9) * 4, 0, 1)        # the bells only while the copy speaks (and a moment after)
    y = y + _bells_for(len(y)) * pk * 10 ** (MIMIC_BELLS_DB / 20) * gate
    return y.astype(np.float32)


def ice_door_fx(x):
    """'door': through Adam's front door with its clear strip of glass (the fake Mom): the wood takes the top (2.8 kHz)
    and booms (230 Hz), the glass strip leaks the consonants (1.6-4.5 kHz, 18 %), the porch's cold air behind her,
    the front hall around us (-2.5 LU)."""
    d = SX.eq(SX.lp(x, 2800, 2), ('peak', 230, 3.5, 1.1), ('hs', 1700, -4.0, 0.7))
    glass = band(x, 1600, 4500, 2) * 0.18
    y = SX.mono(SX.reverb(d + glass, 'porch', 0.2, 0.002))[:len(x)]
    return SX.mono(SX.reverb(y, 'hallway', 0.2, 0.002))[:len(x)].astype(np.float32)


def truck_fx(x, far=False):
    """'truck': his voice from the pink serving window: a little of the roof speaker horn in it (220 Hz-6.5 kHz, a
    1.6 kHz honk, light drive), the cold street's air and a short slap off the houses; 'truck_far': across the street
    (heard from the bathroom window / Kessler's porch): duller, wetter (-1 / -3 LU)."""
    y = SX.eq(band(x, 220, 6500 if not far else 4200, 2), ('peak', 1600, 3.0, 1.3), ('peak', 900, 1.0, 1.0))
    pk = float(np.abs(y).max()) + 1e-9
    y = (np.tanh(1.4 * y / pk) / np.tanh(1.4) * pk).astype(np.float32)
    y = SX.mono(SX.reverb(y, 'street', 0.16 if not far else 0.42, 0.006 if not far else 0.03))[:len(x)]
    air = band(np.random.default_rng(33).normal(0, 1, len(y)).astype(np.float32), 900, 5000) * pk * 0.006
    return (y + air).astype(np.float32)


def memory1958_fx(x):
    """'memory': 1958 (a voice remembered from the flashback): warm and far, 160 Hz-5.5 kHz, a slow wow, a faint
    crackle, a small room (-1.5 LU)."""
    y = _wow(x, 0.0015, 0.35, 0.0002, 6.0, 37)
    y = SX.eq(SX.lp(SX.hp(y, 160, 2), 5500, 2), ('peak', 300, 2.0, 0.9))
    y = SX.mono(SX.reverb(y, 'living', 0.2, 0.012))[:len(x)]
    rng = np.random.default_rng(38)
    cr = (rng.uniform(0, 1, len(y)) > 0.9993).astype(np.float32) * rng.normal(0, 1, len(y)).astype(np.float32)
    return (y + band(cr, 1500, 6000, 2) * float(np.abs(y).max()) * 0.05).astype(np.float32)


LINE_FX.update({'his': his_ice_fx, 'radio': twoway_radio_fx, 'two_way': twoway_radio_fx, 'radio_clean': twoway_radio_fx,
                'channel3': twoway_radio_fx, 'mimic': mimic_ice_fx, 'copy': mimic_ice_fx, 'door': ice_door_fx,
                'front_door': ice_door_fx, 'through_door': ice_door_fx, 'truck': truck_fx,
                'truck_far': lambda x: truck_fx(x, True), 'window': truck_fx, 'serving_window': truck_fx,
                'memory': memory1958_fx, '1958': memory1958_fx, 'flashback': memory1958_fx, 'whisper': whisper_fx})
LINE_FX_LU.update({'his': -0.5, 'radio': -2.0, 'two_way': -2.0, 'radio_clean': -2.0, 'channel3': -2.0, 'mimic': -0.5,
                   'copy': -0.5, 'door': -2.5, 'front_door': -2.5, 'through_door': -2.5, 'truck': -1.0,
                   'truck_far': -3.0, 'window': -1.0, 'serving_window': -1.0, 'memory': -1.5, '1958': -1.5,
                   'flashback': -1.5, 'whisper': 0.0})
# TAG_FX: this film's line tags -> place (script/lines.py is written by the voice teammate; empty until a tag needs to
# override). TEXT_FX: the character lines by their words (found in the timeline's line text, case and punctuation
# ignored), so the right place follows the line whatever its tag: the fake Dad through the radio with bells, the
# fake Mom through the door with bells, the copied boy from the window with bells, the real Dad clean on the radio.
TAG_FX = {}
NARRATOR_FX = ('whisper',)          # the only place a narrator (who 'N') line may take
TEXT_FX = [
    ("who's cold who wants a free one", 'his+truck'),
    ("who's the coldest you are", 'his+truck'),
    ('walter look who s been waiting', 'his+truck_far'), ("walter look who's been waiting", 'his+truck_far'),
    ("see you when it's this cold again", 'his+truck'),
    ('inside children rule seven', 'his'),
    ("walter i'm cold come to the window", 'mimic+truck'),
    ('adam do not go to kessler', 'mimic+radio'), ('then keep her warm kiddo', 'mimic+radio'),
    ("adam it's mom", 'mimic+door'), ('let me in baby', 'mimic+door'),
    ('hearing a song out on elm', 'radio'), ('passing our street all good', 'radio'),
    ("told you what i've been out on route 9", 'radio'), ('say again adam', 'radio'),
    ("two minutes out he can't wait", 'radio'),
    ("good i whisper", 'whisper'), ("shivering means you're fighting", 'whisper'), ('bye benny', 'whisper'),
]


def _tnorm(s):
    import re as _re
    s = str(s).lower().replace('\u2019', "'").replace('mr.', 'mister')
    return _re.sub(r'\s+', ' ', _re.sub(r"[^a-z0-9' ]", ' ', s)).strip()


def text_fx(line):
    t = _tnorm(line.get('en') or line.get('text') or '')
    for k, fx in TEXT_FX:
        if _tnorm(k) in t:
            return fx
    return None


_FX_WARNED = set()


def _chain(keys):
    """'a+b' -> one function running a then b (unknown parts are skipped with a warning); None if nothing is left."""
    fs = []
    for k in keys:
        f = LINE_FX.get(k, 'unknown')
        if f == 'unknown':
            if k not in _FX_WARNED:
                _FX_WARNED.add(k); log(f'WARNING: unknown line fx part {k!r}: skipped')
            continue
        if f is not None:
            fs.append(f)
    if not fs:
        return None
    def run(x):
        for f in fs:
            y = np.asarray(f(x), np.float32)
            x = y if len(y) >= len(x) else np.pad(y, (0, len(x) - len(y)))
        return x
    return run


def apply_line_fx(vo, spans):
    """spans: list of (start s, end s, kind). Replace those stretches of the voice with the processed version."""
    out = vo.copy()
    for a, b, kind in spans:
        key = str(kind).strip().lower() if isinstance(kind, (str, int, float)) else repr(kind)
        fx = _chain(key.split('+')) if '+' in key else LINE_FX.get(key, 'unknown')
        lu_key = key.split('+')[-1] if '+' in key else key
        if fx == 'unknown':
            if key not in _FX_WARNED:
                _FX_WARNED.add(key); log(f'WARNING: unknown line fx {kind!r}: left dry')
            continue
        if fx is None:
            continue
        try:
            a, b = float(a), float(b)
        except (TypeError, ValueError):
            log(f'WARNING: line fx {key!r} span {a!r}-{b!r} is not a time: left dry'); continue
        i0, i1 = max(0, int((a - 0.05) * SR)), min(len(vo), int((b + 0.15) * SR))
        seg = vo[i0:i1]
        if len(seg) < 100: continue
        try:
            y = np.asarray(fx(seg), np.float32)
            if not np.all(np.isfinite(y)):
                raise ValueError('non-finite output')
        except Exception as e:                           # a voicing must never cost the line: leave it dry
            log(f'WARNING: line fx {key!r} failed at {a:.2f} s ({repr(e)[:80]}): left dry'); continue
        if len(y) < len(seg):                    # a reverb FX trims its silent tail: pad back to the segment
            y = np.pad(y, (0, len(seg) - len(y)))
        # loudness-match: band-limiting + saturation made these lines 2.6-6.5 LU hotter than the narration (critic)
        Ls, Ly = SX.lufs_int(seg), SX.lufs_int(y[:len(seg)])
        if Ls > -70 and Ly > -70:
            y = y * np.float32(10 ** ((Ls + LINE_FX_LU.get(lu_key, -1.0) - Ly) / 20))
        f = int(0.01 * SR); w = np.ones(len(seg), np.float32); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
        out[i0:i1] = seg * (1 - w) + y[:len(seg)] * w
        if len(y) > len(seg) and 'slide' in key:          # the slowing tape runs on into the gap after the line
            ex = y[len(seg):len(seg) + int(MIMIC_SLIDE_EXTRA * SR)]
            ex = ex[:max(0, len(out) - i1)].copy()
            loud = np.flatnonzero(np.abs(out[i1:i1 + len(ex)]) > 0.03 * (np.abs(seg).max() + 1e-9))
            if len(loud):                                   # never over the next words: stop where they begin
                ex = ex[:max(0, int(loud[0]) - int(0.02 * SR))]
                if len(ex) > 64:
                    ex[-min(len(ex), int(0.03 * SR)):] *= np.linspace(1, 0, min(len(ex), int(0.03 * SR)))
            if len(ex):
                out[i1:i1 + len(ex)] = out[i1:i1 + len(ex)] * 0.0 + ex
        if fx is rooms_fx:
            try:
                ROOMS_WASH.append((i0, rooms_wash(y[:len(seg)])))
            except Exception as e:
                log(f'WARNING: rooms wash at {a:.2f} s failed ({repr(e)[:60]})')
    return out


def load_vo(path, n):
    x, sr = sf.read(path, dtype='float32')
    if x.ndim > 1: x = x.mean(1)
    if sr != SR: x = signal.resample_poly(x, SR, sr).astype(np.float32)
    y = np.zeros(n, np.float32); y[:min(n, len(x))] = x[:n]
    return y


def voice_tracks(tl, vo_en, vo_ru, n_full, langs, who_fx=None):
    L = tl['lines']
    who_fx = who_fx or {}
    # the Ice Cream film: TAG_FX, then the line's words (TEXT_FX), then the line's own fx, then --who-fx
    # The NARRATOR's voice is never changed (only cleaned): a narrator line keeps only NARRATOR_FX ('whisper': Adam's
    # own "Good," I whisper); lines.py's 'memory' on the 1958 narration is left dry
    def fx_of(l):
        fx = TAG_FX.get(l.get('tag')) or text_fx(l) or l.get('fx') or who_fx.get(l.get('who'))
        if fx and l.get('who', 'N') == 'N' and str(fx) not in NARRATOR_FX:
            return None
        return fx
    en_spans = [(l['t'], l['end'], fx_of(l)) for l in L if fx_of(l) and l.get('found_en', True)]
    ru_start = {}
    for g in tl.get('dub', []):
        i, j = g['lines']; ru_start[i] = g['ru_start']
    ru_spans = []
    for l in (L if 'ru' in langs else []):
        if not fx_of(l): continue
        a = ru_start.get(l['i'], l['t'])
        d = l['ru_src'][1] - l['ru_src'][0] if l.get('ru_src') else l['end'] - l['t']
        ru_spans.append((a, a + max(0.4, d), fx_of(l)))
    out = {}
    if 'en' in langs:
        out['en'] = apply_line_fx(load_vo(vo_en, n_full), en_spans)
        for l in L:                                       # per-line level (LINE_TAG_DB), 10 ms ramps
            g_db = LINE_TAG_DB.get(l.get('tag'))
            if not g_db: continue
            i0, i1 = max(0, int((l['t'] - 0.05) * SR)), min(n_full, int((l['end'] + 0.15) * SR))
            w = np.full(i1 - i0, 10 ** (g_db / 20), np.float32); f = min(int(0.01 * SR), len(w) // 2)
            w[:f] = np.linspace(1, w[f], f); w[-f:] = np.linspace(w[f], 1, f)
            out['en'][i0:i1] *= w
            log(f'line {l["i"]} ({l.get("tag")}) {g_db:+.1f} dB')
    if 'ru' in langs: out['ru'] = apply_line_fx(load_vo(vo_ru, n_full), ru_spans)
    return out


# ============================================================================ placeholder score
def placeholder_score(cues, dur):
    """D-A drone with an Eb rub, following the intensity curve; hits, risers and silences from the events. Only for
    testing the mix while audio/score.py is missing."""
    n = int(dur * SR); t = np.arange(n) / SR
    iv = np.array(cues.get('intensity') or [[0, 0.4], [dur, 0.4]], float)
    I = np.interp(t, iv[:, 0], iv[:, 1]).astype(np.float32)
    rng = np.random.default_rng(5)
    def saw(f, det=0.0):
        ph = np.cumsum(np.full(n, f * (1 + det))) / SR
        return sum(np.sin(2 * np.pi * k * ph + rng.uniform(0, 6)) / k for k in range(1, 9)).astype(np.float32)
    pad = (saw(73.42) + saw(73.42, 0.004) + 0.8 * saw(110.0, -0.003) + 0.5 * saw(146.83, 0.002)) * 0.25
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * t / 23.0)
    # crude time-varying low-pass by crossfading two fixed filters
    dark, bright = SX.lp(pad, 260, 2), SX.lp(pad, 900, 2)
    x = dark * (1 - I) + bright * I
    sub = (np.sin(2 * np.pi * 36.71 * t) * 0.5).astype(np.float32)
    rub = (saw(77.78) * 0.12 * np.clip((I - 0.55) / 0.3, 0, 1)).astype(np.float32)
    rub = SX.lp(rub, 400, 2)
    g = (10 ** ((-14 + 14 * I + 2 * lfo) / 20)).astype(np.float32)
    drone = (x + sub + rub) * g
    st = np.stack([drone * 0.95, np.roll(drone, 240) * 0.95], 1)
    hits = np.zeros((n, 2), np.float32); env = np.ones(n, np.float32)
    for e in cues.get('events', []):
        i = int(e['t'] * SR); lv = float(e.get('level', 0.7))
        if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop', 'rule'):
            b = SX.st(SX.sub_boom(60, 30, 2.0, 0.2)) * lv
            b = SX.reverb(b, 'church', 0.3)
            SX.place(hits, b * 2.0, i)
        elif e['type'] == 'riser':
            L = float(e.get('len', 4.0)); m = int(L * SR)
            r = SX.sweep_bp(SX.noise(L, abs(i)), 200, 3000, 1.5) * np.linspace(0, 1, m) ** 2 * lv
            SX.place(hits, SX.st(r) * 0.6, i - m)
        elif e['type'] == 'silence':
            a, b = i, i + int(float(e.get('len', 1.7)) * SR)
            env[a:b] = 0.03
    env = SX.lp(env, 8, 1)
    return {'drone': st * env[:, None], 'hits': hits}


def score_stems(cues, dur, force_fallback=False):
    if not force_fallback:
        try:
            import importlib
            score = importlib.import_module('score')
            st = score.render(cues, dur, seed=SCORE_SEED)
            if isinstance(st, dict) and st:
                log('score.py stems:', ', '.join(st))
                return st, 'score.py'
            log('score.py returned nothing; using placeholder')
        except Exception as e:
            log('score.py unavailable or failed (%s); using placeholder drone' % repr(e)[:200])
            traceback.print_exc(limit=2)
    return placeholder_score(cues, dur), 'placeholder'


# ============================================================================ bus helpers
def fit(y, n):
    y = SX.st(np.asarray(y, np.float32))
    return y[:n] if len(y) >= n else np.pad(y, ((0, n - len(y)), (0, 0)))


def voice_activity(v, att=0.04, rel=0.35, hold=0.0):
    """0..1 activity from the voice's envelope (10 ms RMS), for ducking and the dynamic EQ. hold (s): the envelope is
    held at its peak that long before it releases (the Bunnyman's final mix: the duck stays on through the commas and
    word gaps of a phrase instead of letting the score swell up under the last syllable of every phrase)."""
    a = np.abs(v).astype(np.float64)
    e = SX.follow(a, SX.coef(att), SX.coef(rel))
    if hold > 0:
        # trailing max over `hold` (the envelope's own release then runs from the end of the hold), with a 30 ms
        # smoothing of the step where the hold lets go (a second full release here would double the release time:
        # the first try kept the bed only 0.9 LU up in the gaps instead of ~2.5 LU)
        h = max(1, int(hold * SR))
        e = SX.follow(maximum_filter1d(e, size=h, origin=(h - 1) // 2), 0.0, SX.coef(0.03))
    edb = SX.db(e)
    ref = np.percentile(edb[edb > -70], 90) if (edb > -70).any() else -20
    return np.clip((edb - (ref - 26)) / 14, 0, 1).astype(np.float32)


_BPV = None


def dyn_cut(x, act, depth_db):
    """Bell cut centred ~2.1 kHz (1-4.5 kHz), depth follows the voice activity: x + (g-1) * BP(x)."""
    global _BPV
    if depth_db == 0:
        return x
    if _BPV is None:
        _BPV = signal.butter(1, [1000, 4500], 'bandpass', fs=SR, output='sos')
    b = signal.sosfilt(_BPV, x, axis=0).astype(np.float32)
    b *= (10 ** (-depth_db * act / 20) - 1).astype(np.float32)[:, None]
    b += x
    return b


def gain_env(n, segs):
    """segs: [(t0, t1, dB, fade_in, fade_out)] -> multiplicative envelope (minimum of the dips)."""
    e = np.zeros(n, np.float32)
    for a, b, d, fi, fo in segs:
        i0, i1 = int(a * SR), int(b * SR)
        ia, ib = int((a - fi) * SR), int((b + fo) * SR)
        t = np.arange(max(0, ia), min(n, ib))
        if not len(t): continue
        w = np.ones(len(t), np.float32)
        up = t < i0; w[up] = np.clip((t[up] - ia) / max(1, i0 - ia), 0, 1)
        dn = t > i1; w[dn] = np.clip(1 - (t[dn] - i1) / max(1, ib - i1), 0, 1)
        w = np.sin(w * np.pi / 2) ** 2
        e[t] = np.minimum(e[t], d * w)
    return (10 ** (e / 20)).astype(np.float32)


def glue(x, thr_rel=0.0, ratio=2.0, free=None):
    """Slow RMS glue compressor on the bed bus (30 ms attack lets hit transients through). Threshold = p95 of the
    bed's 50 ms RMS + thr_rel; gain reduction capped at 3 dB; none where `free` (bool per sample) is set."""
    p = (x[:, 0] * x[:, 0] + x[:, 1] * x[:, 1]) * 0.5
    k = int(0.05 * SR); r = np.sqrt(np.maximum(uniform_filter1d(p, k), 0)).astype(np.float32); del p
    rdb = SX.db(r); live = rdb > -60
    if not live.any():
        return x, 0.0, np.ones(len(x), np.float32)
    thr = np.percentile(rdb[live], 95) + thr_rel
    env = SX.follow(r, SX.coef(0.03), SX.coef(0.3))
    over = (20 * np.log10(np.maximum(env, 1e-9)) - thr).astype(np.float32); del env; knee = 6.0
    gr = np.where(over <= -knee / 2, 0, np.where(over >= knee / 2, over * (1 - 1 / ratio),
                                                 (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee))).astype(np.float32)
    del over
    gr = np.minimum(gr, 3.0)
    if free is not None:                     # bool, or a 0..1 weight (fix round 2: the shaped boosted windows)
        if free.dtype == bool: gr[free] = 0.0
        else: gr *= (1.0 - np.clip(free, 0.0, 1.0)).astype(np.float32)
    g = (10 ** (-gr / 20)).astype(np.float32)
    return x * g[:, None], float(np.percentile(gr[live], 95)), g


def true_peak(y, os_=4, chunk=SR * 20):
    m = 0.0
    for a in range(0, len(y), chunk):
        u = signal.resample_poly(y[max(0, a - 64):a + chunk + 64].astype(np.float32), os_, 1, axis=0)
        m = max(m, float(np.abs(u).max()))
    return 20 * np.log10(m + 1e-12)


def tp_limit(y, ceiling_db=-1.7, look=0.005, rel=0.08, os_=4, chunk=SR * 20):
    """Look-ahead limiter on the 4x-oversampled peak: gain = backward moving average of the forward-looking minimum of
    the required gain (so it is fully down at each peak), then instant-attack / exponential release."""
    c = 10 ** (ceiling_db / 20); n = len(y); req = np.ones(n, np.float32)
    for a in range(0, n, chunk):
        lo = max(0, a - 64); seg = y[lo:a + chunk + 64].astype(np.float32)
        u = np.abs(signal.resample_poly(seg, os_, 1, axis=0)).max(1)
        m = len(seg); u = u[:m * os_].reshape(m, os_).max(1)
        # also take the neighbours (inter-sample peaks between i-1 and i)
        u = np.maximum(u, np.concatenate([[0], u[:-1]]))
        r = np.minimum(1.0, c / np.maximum(u, 1e-9))
        req[a:a + chunk] = r[a - lo:a - lo + min(chunk, n - a)]
    L = max(1, int(look * SR))
    gmin = minimum_filter1d(req, size=2 * L + 1, origin=-L)        # min over [i, i + 2L]
    gs = uniform_filter1d(gmin, size=L, origin=(L - 1) // 2)       # mean over [i - L + 1, i]
    gs = np.minimum(gs, gmin)
    gr = SX.follow((1.0 - gs).astype(np.float32), 0.0, SX.coef(rel)); del gmin
    g = (1.0 - gr).astype(np.float32)
    return y * g[:, None], float(-20 * np.log10(max(float(g.min()), 1e-6))), float((g < 10 ** (-1 / 20)).mean())


def voice_ride(v, over_lu=2.5, ratio=3.0):
    """A slow fader ride on the narration's loudest phrases: where the 400 ms K-weighted loudness goes more than
    over_lu above the integrated level, take it down (ratio 3:1), smoothed (no pumping: 0.25 s rise, 0.6 s fall).
    Final mix: the narration's own peaks reached +4.5 LU momentary over the mix (the loudest moments of the film were
    words); the ride caps them near +3 so the three hardest scares sit clearly above every line. Returns (v, max dB)."""
    L0 = SX.lufs_int(v)
    hop = 0.05
    Lb = -0.691 + 10 * np.log10(SX._blocks(v, 0.4, hop) + 1e-20)
    gdb = -np.maximum(0.0, Lb - (L0 + over_lu)) * (1 - 1 / ratio)
    k = int(0.3 / hop)                                  # hold the cut over the block's span, then smooth
    gdb = minimum_filter1d(gdb, size=k, mode='nearest')
    gdb = uniform_filter1d(gdb, size=int(0.25 / hop), mode='nearest')
    tb = np.arange(len(gdb)) * hop + 0.2
    g = np.interp(np.arange(len(v)) / SR, tb, gdb).astype(np.float32)
    return (v * (10 ** (g / 20))).astype(np.float32), float(-gdb.min()) if len(gdb) else 0.0


VOICE_CAP_LU = 2.3   # fix round 1 (critic 3 M6): no 400 ms block of the narration more than this over its integrated
                     # level (the mix's own loudest moments were ordinary lines at +5 LU; the ride's smoothing let them
                     # through at +4.3). A loudness limiter on whole words: the cut covers the block, 150 ms ramps; about
                     # 1 % of the blocks move, by at most a few dB; the narrator's voice itself is untouched


def voice_cap(v, cap_lu=VOICE_CAP_LU, hop=0.05):
    """Keep every 400 ms K-weighted block of v within cap_lu of its integrated level (returns v, max cut dB)."""
    worst = 0.0
    for _ in range(4):
        L0 = SX.lufs_int(v)
        Lb = -0.691 + 10 * np.log10(SX._blocks(v, 0.4, hop) + 1e-20)
        cut = np.clip(Lb - (L0 + cap_lu) + 0.15, 0.0, 8.0)
        if cut.max() < 0.2:
            break
        cut = maximum_filter1d(cut, size=int(0.4 / hop) + 1, mode='nearest')     # the whole block (+-0.2 s)
        cut = uniform_filter1d(cut, size=3, mode='nearest')
        worst = max(worst, float(cut.max()))
        tb = np.arange(len(cut)) * hop + 0.2
        g = np.interp(np.arange(len(v)) / SR, tb, -cut).astype(np.float32)
        v = (v * 10 ** (g / 20)).astype(np.float32)
        v = (v * 10 ** ((TARGET - SX.lufs_int(v)) / 20)).astype(np.float32)
    return v, worst


def voice_chain(v, plr=11.0, ride_lu=None):
    """Narration bus: loudness to -14 LUFS, gentle 2.5:1 compression on the loudest syllables, then a transparent
    true-peak limiter so the voice's peak-to-loudness ratio is <= plr dB (EN narration arrives at PLR 15.6 dB, which
    would otherwise make the master limiter pump on every plosive). Returns (voice, stats)."""
    L0 = SX.lufs_int(v)
    if L0 <= -70:
        return v, {}
    v = v * 10 ** ((TARGET - L0) / 20)
    e = SX.follow(np.abs(v).astype(np.float64), SX.coef(0.003), SX.coef(0.06)); edb = SX.db(e)
    thr = float(np.percentile(edb[edb > -60], 97))
    v = SX.compress(v, thr, 2.5, 0.003, 0.06, knee=6.0)
    v = v * 10 ** ((TARGET - SX.lufs_int(v)) / 20)
    ride = 0.0
    if ride_lu is not None:
        v, ride = voice_ride(v, ride_lu, RIDE_RATIO)
        v = v * 10 ** ((TARGET - SX.lufs_int(v)) / 20)
    capd = 0.0
    if ride_lu is not None and VOICE_CAP_LU is not None:
        v, capd = voice_cap(v)
    y, gr, frac = tp_limit(np.stack([v, v], 1), TARGET + plr, look=0.003, rel=0.05)
    v = y[:, 0]
    v = (v * 10 ** ((TARGET - SX.lufs_int(v)) / 20)).astype(np.float32)
    if ride_lu is not None and VOICE_CAP_LU is not None:      # again: the limiter's make-up lifted the capped blocks
        v, c2 = voice_cap(v); capd = max(capd, c2)
    return v, {'plr': round(true_peak(np.stack([v, v], 1)) - TARGET, 1), 'limit_gr_max': round(gr, 1), 'ride_max_db': round(ride, 1),
               'limit_over_1dB_pct': round(100 * frac, 2), 'cap_max_db': round(capd, 1)}


TILT = {63: 8.0, 125: 3.0, 250: 4.0, 500: 4.0, 2000: -7.0, 4000: -10.0, 8000: -14.0}   # AUDIO_SPEC sec. 2, rel 1 kHz


def match_tilt(m, amount=0.8, lo=-6.0, hi=2.0, probe=None):
    """Bounded auto-EQ for the score bus: measures its octave levels (rel 1 kHz) and moves them `amount` of the way
    toward the reference tilt with one-octave peaking bells, each limited to lo..hi dB (cuts only from 2 kHz up, so
    the score never brightens into the voice band). `probe`: the same music after
    the voice-keyed bell cut, so the tilt is measured as it will be heard. Returns (music, {Hz: dB})."""
    x = (m if probe is None else probe).mean(1)
    if len(x) > 240 * SR:
        x = x[::max(1, len(x) // (240 * SR))]
    f, P = signal.welch(x, SR, nperseg=8192)
    lev = lambda c: 10 * np.log10(P[(f >= c / 1.414) & (f < c * 1.414)].sum() + 1e-30)
    ref = lev(1000)
    # the 63 Hz bell only cuts (critic: the score is sub-heavy, 36 % sub vs 28 %, and a +2 dB boost ate limiter headroom)
    corr = {c: float(np.clip(amount * (t - (lev(c) - ref)), lo, hi if 63 < c < 2000 else 0.0)) for c, t in TILT.items()}
    bands = [('peak', c, g, 1.41) for c, g in corr.items() if abs(g) > 0.3]
    return (SX.eq(m, *bands) if bands else m), {c: round(g, 1) for c, g in corr.items()}


def level_music(m, sil, up_max=9.0, lo_rel=-4.5, hi_rel=6.5, r_up=0.7, r_dn=0.5):
    """Slow two-way leveler for the score bus (non-causal 2 s smoothing, so no pumping): passages more than 4.5 LU
    under the score's own median are lifted (70%, at most +9 dB), passages more than 6.5 LU over it are compressed 2:1.
    Near-silence (< median - 30 LU) and the authored silences (plus 4 s after, where the music must come back quieter)
    are never lifted. Returns (music, gain curve dB at 20 Hz)."""
    hop = 0.05
    b = SX._blocks(m, 1.0, hop); l = -0.691 + 10 * np.log10(b + 1e-20)
    live = l > -70
    if not live.any():
        return m, np.zeros(1)
    med = float(np.median(l[live]))
    g = np.where(l < med + lo_rel, np.minimum(up_max, (med + lo_rel - l) * r_up), 0.0)
    g = np.where(l < med - 30, 0.0, g)
    g = np.where(l > med + hi_rel, -(l - med - hi_rel) * r_dn, g)
    tb = np.arange(len(l)) * hop + 0.5
    for a, e in sil:
        k = (tb > a - 0.3) & (tb < e + 4.0)
        g[k] = np.minimum(g[k], 0.0)
    g = uniform_filter1d(g, size=int(2.0 / hop))
    gs = np.interp(np.arange(len(m)) / SR, tb, g).astype(np.float32)
    return m * (10 ** (gs / 20))[:, None], g


DUCK_DB = 4.5        # music + SFX beds under the voice (critic: 3 -> 4.5 dB, so the bed sits ~-13 LU under speech)
HIT_DUCK_DB = 6.0    # hits bus (SFX + score hits) under the voice: the reveal line stays clear of the hit's tail
HIT_DUCK_HI_DB = 10.0   # final mix v2: the hits above 150 Hz duck 10 dB under a line (the sub body is not ducked)
HIT_CUT_DB = 3.0     # final mix: the hits bus also gets the voice-keyed 1-4.5 kHz bell cut (the hit's body is low: the
                     # cut keeps the next words readable while the hits come up --hits-db)
FOLEY_DIP_DB = 2.5   # music dips under foley events (footsteps, keys, paper...) so they read
DUCK_HOLD_S = 0.12   # the Bunnyman's final mix: the music / beds duck holds 0.12 s after each syllable, then releases as
                     # before (0.25 s), so the dips inside words and the shortest commas do not pump the score while the
                     # sentence gaps still breathe (a 0.35 s hold kept the duck on 97 % of the film and the bed came up
                     # only 0.6 LU in the gaps; the references come up 2.5-3 LU)
CLARITY_MARGIN_LU = 6.0   # the voice always clear: while a line is spoken the bed stays this far under the narration's own
CLARITY_MAX_CUT_DB = 10.0  # 400 ms level (measure_mix.py flags < 4 LU); the excess is cut, at most this much
SCORE_SEED = 1987    # score.py's random choices (track offsets, voicings, jitter) from a fixed seed: by default the seed was
                     # the hash of the cue sheets, so any cue change re-rolled the whole score and moved every weak spot
# fix round 1 (critic 3 M6: the scares never got louder than the narration's own loudest lines, +5 LU): the boosted
# scares' spare windows let the hits bus up to near full scale (an absolute ceiling, -1 .. -2 dBFS by grade, instead of
# the voice's p99.9 peak + 6 dB) and drive it BOOST_DRIVE_DB into its look-ahead limiter there (a denser body: a lower crest factor, so the 400 ms loudness rises,
# not just the transient); the glue compressor leaves those windows alone. Grade by the plan's boost: >= 3.5 (the face
# reveal, the swap) 1.0, >= 2.5 (the window, the back door, the crack, the doorway, GET OUT) 0.75, else 0.5
BOOST_DRIVE_DB = 10.0
BOOST_SPARE_S = 0.4   # a boosted scare's spare window lasts at least this long (the next word's onset ended it after 0.15 s)
# fix round 2 (verify r1, major 2: the boosted windows were rectangular, so at each window's end the hits bus fell 7-14 dB
# in 20 ms and the scares' tails were chopped): every boosted window now has a raised-cosine attack (BOOST_ATT_S) and
# release (BOOST_REL_S) on its drive, its ceiling (blended in dB), the glue's exemption and the bed statistics' mask
BOOST_ATT_S, BOOST_REL_S = 0.010, 0.75   # sound fix r3: 0.35 s read as a hard-edged block (critic M1: 0.6-1.2 s)
# fix round 2 (verify r1, major 1 / critic 3 M6: the scares only reached +4.3 LU momentary, about 1 LU over the loudest
# narration, because the hits limiter pinned them at its ceiling with a crest factor of about 8 dB): inside a boosted
# window the hits bus is scaled so its peak meets the ceiling up to BOOST_SAT_DB over it and soft-clipped (tanh) to the
# ceiling: a denser body (crest about 4-5 dB). The drive is the largest (0.5 dB steps) whose loudest 400 ms in the window
# stays under BOOST_TARGET_LU (by grade, LU over the voice's integrated level; a fixed drive turned the sustained swap on
# "Seven." into a +17 LU square wave), and a window already over its target comes down to it. The saturation's harmonics
# in 1-4.5 kHz are cut BOOST_VCUT_DB under the voice (keyed to it), so the words the scares ride over still read
BOOST_SAT_DB = 14.0
BOOST_TARGET_LU = {1.0: 10.0, 0.75: 9.0, 0.5: 8.0}
BOOST_VCUT_DB = 16.0  # Bus final mix: 8 dB left 'Almost.', '...Clever.', the hand, the doors and 'Two of me.' 4-13 dB
                      # under the scare in 1-4.5 kHz; the cut now also sits inside the drive search (the loudness target
                      # is met with the cut in place)
RIDE_RATIO = 4.0     # the narration's ride above --voice-ride LU (was 3:1 above +2: its loudest lines reached +5 LU)
LINE_TAG_DB = {}                # THIS film: none yet (the Bus film's 'please' +4 dB is gone); per line tag, dB
_LINE_TAG_DB_BUS = {'please': 4.0}   # (the Bus film) the girl's "Please." through the door sat 6.9 dB under the
                                # narration with the bed 7.9 dB under it (critic 3 m11)
NOTCH_DB = 6.0       # a plan hit with 'notch': s cuts 1-4.5 kHz of the hits and SFX events by this much for that long
                     # from the hit (the window smash on "explodes": the word stays readable under the boosted hit)
# fix round 1 (critic 3 M7: the planned rule-by-rule build reached the mix almost flat, -14.2 .. -13.4 LU, the cold
# open as loud as rule 6): the bed in the GAPS between lines (400 ms K-weighted blocks where the narration is silent),
# rel the voice's integrated level, is steered to rise rule by rule; each rule's section of the music bus gets the
# offset it needs (closed loop on the mix itself, clamped to +-ARC_MAX_DB, 2 s crossfades), then the music gain is
# solved again. (first line of the section, target LU); the section ends at the next row; rule 7 (false relief) and
# everything else are left alone
# the rule-by-rule arc, by line index of each 'Rule number N.' line (sound fix round, M2: the old indices were the
# Bunnyman's and drifted a rule; rules 3 and 4 measured under rule 2). (92: the comment prompt; 303: the rescue)
# Bus film (final mix): the rows name the timeline's line TAGS (resolved at run time, so a re-paced or re-cut voice
# edit needs no change here); the Doctor film's line indices had been left in and steered the wrong stretches.
# rule 1 .. rule 7 rise; the comment prompt ('cta') and everything from the 3:00 bell on are left alone
# THIS film (the Ice Cream film): the rows name a line TAG or a script PHRASE (music_plan.line_index finds it in the
# timeline's text), so nothing depends on lines.py's tags; the comment prompt and everything from the plow's arrival
# (the warm turn) are left alone; the climax's crossing is the loudest gap bed
ARC_TARGETS = [('Rule number one', -19.0), ('Stop. His song is playing', None), ('Rule number two', -17.5),
               ('Rule number three', -16.5), ('Rule number four', -15.0), ('Rule number five', -13.5),
               ('Rule number six', -12.5), ('Then the song moves', -14.0), ('Rule number seven', -11.5),
               ("Mr. Kessler is halfway to the window", -9.5), ("Dad's plow roars", None)]
ARC_MAX_DB = 8.0     # Bus final mix: 6 dB clamped rules 1 and 6 short of the rule-by-rule rise
# sound fix round (M1): the old landline's bell sat 5-10 dB under the voice peaks in the speech band and level with the
# voice between syllables: each ring dips this much while the narration speaks (voice-keyed, 10 ms attack, 0.12 s hold)
RING_DUCK_DB = 9.0
RING_DUCK_NAMES = ('landline_ring', 'phone_ring')
TRUE_SILENCE_LEVEL = 0.95   # silence events at or over this level are true silences: the SFX events and hits buses
                            # (hit tails, the swap's ring) are cut with the score, the room tone (beds) stays at -6 dB


def event_activity(e, att=0.01, rel=0.25, lo=-52.0, span=12.0):
    """0..1 activity of the foley events bus (absolute: the SFX are calibrated to a -14 LUFS voice)."""
    a = np.abs(e).max(1).astype(np.float64)
    env = SX.follow(a, SX.coef(att), SX.coef(rel))
    return np.clip((SX.db(env) - lo) / span, 0, 1).astype(np.float32)


def cue_hashes(cues_dir):
    import hashlib
    out = {}
    for f in ('sfx_cues.json', 'music_cues.json'):
        p = os.path.join(cues_dir, f)
        out[f] = hashlib.sha1(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else None
    return out


def stale(cues_dir, out_dir):
    """True when out_dir/mix_report.json was not rendered from the current cue sheets (render.py --audio guard)."""
    p = os.path.join(out_dir, 'mix_report.json')
    if not os.path.exists(p):
        return True
    return json.load(open(p)).get('cues_sha1') != cue_hashes(cues_dir)


SNAP_TYPES = ('hit', 'stinger', 'braam', 'sub_drop', 'rule')


def picture_hits(mcues, sfx_cues):
    """The picture's hit frames: film.py's impact SFX and its music hit / stinger / braam / sub_drop / rule events
    (both retimed onto the reveal cuts by film.py's polish pass)."""
    out = set()
    for c in sfx_cues or []:
        if isinstance(c, dict) and c.get('name') in ('impact_hit', 'stinger', 'braam', 'sub_drop'):
            try: out.add(round(float(c['t']), 3))
            except (KeyError, TypeError, ValueError): pass
    for e in mcues.get('events') or []:
        if isinstance(e, dict) and e.get('type') in SNAP_TYPES:
            try: out.add(round(float(e['t']), 3))
            except (KeyError, TypeError, ValueError): pass
    return sorted(out)


def full_plan(mcues, tl, sfx_cues, tol=0.35):
    """--plan full (the final mix): the score follows audio/music_plan.py entirely (track map, intensity curve, tension
    events anchored to the narration's words, the film's identity layer); film.py's own music events are replaced (the
    full-length checks: its generic swells every ~20 s, braams on reveal lines and its intensity curve made the second
    quarter louder than the first and put a braam 23 LU over the narration at 454 s). The picture still decides the
    sync: a plan hit / stinger / braam / sub drop / rule sting within `tol` s of one of the picture's hit frames moves
    onto that frame (unless it carries nosnap). Keeps film.py's duration. Returns (cues, snapped list)."""
    import music_plan as MP
    lines = tl['lines']
    dur = float(mcues.get('duration') or tl['duration_en'] + 2.5)
    ph = picture_hits(mcues, sfx_cues)
    ev, snapped = [], []
    for e in MP.events(lines):
        e = dict(e)
        if e['type'] in SNAP_TYPES + ('riser',) and not e.pop('nosnap', False) and ph:   # a riser ends on its hit
            near = min(ph, key=lambda h: abs(h - e['t']))
            if 0.002 < abs(near - e['t']) <= tol:
                snapped.append((e['type'], e['t'], near)); e['t'] = near
        else:
            e.pop('nosnap', None)
        ev.append(e)
    ev += MP.identity_events(lines)
    out = {'duration': dur, 'intensity': MP.intensity(lines, dur), 'track_map': MP.track_map(lines),
           'events': sorted(ev, key=lambda e: float(e.get('t', 0))), 'plan': 'full'}
    return out, snapped


def with_plan(mcues, tl):
    """The music map (audio/music_plan.py) for a cue sheet that has none: film.py writes intensity and events from the
    picture but no track_map, so score.py would otherwise pick tracks by itself. The film's own sound (music_plan
    IDENTITY: the show theme on the TV, Mister Winks's theme, the music box) is added when the sheet has no 'show' /
    'winks' events of its own. A sheet with no events at all also gets the plan's intensity curve and events. Never
    fails the mix: on any error the sheet is used as it is."""
    try:
        import music_plan as MP
        lines = tl['lines']
        out = dict(mcues)
        what = []
        if not mcues.get('track_map'):
            out['track_map'] = MP.track_map(lines)
            what.append('track_map')
        ev = list(mcues.get('events') or [])
        if not ev:
            ev = MP.events(lines)
            out['intensity'] = MP.intensity(lines, float(mcues.get('duration') or tl['duration_en'] + 2.5))
            what.append('events + intensity')
        if hasattr(MP, 'identity_events') and not any(e.get('type') in ('show', 'winks', 'jingle', 'hold') for e in ev):
            idt = MP.identity_events(lines)
            have_motif = any(e.get('type') == 'motif' for e in ev)
            add = [e for e in idt if not (have_motif and e['type'] == 'motif')]
            spans = [(e['t'] - 1.0, e['t'] + float(e.get('len', 0)) + 1.0) for e in add
                     if e['type'] in ('show', 'winks', 'jingle')]
            # film.py's own 'theme' cues that fall inside a planned show / Winks theme would play the same tune twice
            # at once: the plan's arrangement takes over there; the others stay (score.py plays them as Winks phrases)
            drop = [e for e in ev if e.get('type') == 'theme' and any(a <= float(e.get('t', 0)) <= b for a, b in spans)]
            ev = [e for e in ev if not any(e is d for d in drop)] + add
            what.append('identity (jingle / show / winks%s%s)' % ('' if have_motif else ' / motif',
                                                          f', {len(drop)} overlapping film.py theme cues dropped' if drop else ''))
        out['events'] = sorted(ev, key=lambda e: float(e.get('t', 0)))
        if what:
            log(f'music plan: {" + ".join(what)} from music_plan.py ({len(out.get("track_map") or [])} sections)')
        return out
    except Exception as e:
        log('WARNING: music_plan.py failed (%s); score.py arranges the tracks itself' % repr(e)[:160])
        return mcues


def window_track_map(tm, ts, sdur):
    """track_map in window time (film time - ts): a section already playing at ts starts at 0 with its track offset
    advanced by the time it has played; sections that end before ts or start after the window are dropped."""
    tm = sorted((dict(x) for x in tm), key=lambda x: float(x.get('t0', 0)))
    out = []
    for k, x in enumerate(tm):
        a = float(x.get('t0', 0)); b = float(tm[k + 1]['t0']) if k + 1 < len(tm) else 1e12
        if b <= ts or a - ts >= sdur:
            continue
        if a < ts:
            x['off'] = float(x.get('off', 0.0)) + (ts - a); x['t0'] = 0.0
        else:
            x['t0'] = a - ts
        out.append(x)
    return out


def short_term_rel(x, ref, win=0.4, hop=0.1):
    return -0.691 + 10 * np.log10(SX._blocks(x, win, hop) + 1e-20) - ref


# ============================================================================ main
def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--check':          # mix.py --check <cues dir> <out dir>
        st_ = stale(sys.argv[2], sys.argv[3])
        print('STALE: the mix was not rendered from the current cues' if st_ else 'ok: mix matches the cues')
        sys.exit(1 if st_ else 0)
    ap = argparse.ArgumentParser()
    ap.add_argument('timeline'); ap.add_argument('vo_en'); ap.add_argument('vo_ru'); ap.add_argument('cues')
    ap.add_argument('out')
    ap.add_argument('--t0', type=float, default=0.0); ap.add_argument('--t1', type=float, default=None)
    ap.add_argument('--langs', default='en'); ap.add_argument('--fallback', action='store_true')
    ap.add_argument('--strict', action='store_true', help='stop on a failed SFX cue (police behaviour)')
    ap.add_argument('--who-fx', default='',
                    help='line fx for a speaker whose lines have none, e.g. S=his (default none: this film places its '
                         'character lines by TAG_FX, TEXT_FX and the lines\' own fx)')
    ap.add_argument('--plan', default='auto', choices=('auto', 'full', 'off'),
                    help='auto: a music_cues.json without track_map gets music_plan.py\'s arrangement (and its '
                         'intensity / events when the sheet has none); full (the final mix, final_mix.sh): the score '
                         'follows music_plan.py entirely (snapped to the picture\'s hit frames) and audio/sfx_plan.py '
                         'refines the picture\'s SFX sheet; off: score.py arranges by itself')
    ap.add_argument('--bed-rel', type=float, default=-13.0, help='reference integrated bed level (report and cap)')
    ap.add_argument('--bed-p50', type=float, default=-16.0, help='target bed 3 s short-term median, LU rel voice')
    ap.add_argument('--no-stems', action='store_true')
    ap.add_argument('--write-cues', action='store_true', help='write the cue sheets as mixed to <out>/cues_used '
                                                               '(always with --plan full)')
    ap.add_argument('--score-stems', action='store_true',
                    help='also write the raw score stems (tracks, drones, pulse, melodic, strings, show, hits) of the window '
                         'at the music and master gain, before the music bus processing: stems/score_<stem>.wav (tests)')
    ap.add_argument('--voice-plr', type=float, default=11.5)
    ap.add_argument('--voice-ride', type=float, default=None,
                    help='LU over the narration\'s integrated level where a slow 3:1 ride starts on its loudest '
                         'phrases (final_mix.sh: 2.5; default off)')
    ap.add_argument('--hits-db', type=float, default=0.0,
                    help='gain on the score\'s hits stem (final_mix.sh: +4; the full-length checks measured the hits '
                         'p50 7 LU under the voice, the references +2)')
    ap.add_argument('--music-width', type=float, default=0.7)
    A = ap.parse_args()
    T0 = time.time()
    langs = [s for s in A.langs.split(',') if s]
    os.makedirs(A.out, exist_ok=True)
    tl = json.load(open(A.timeline))
    hashes = cue_hashes(A.cues)               # taken now: film.py may rewrite the sheets while the mix runs
    sfx_cues = json.load(open(os.path.join(A.cues, 'sfx_cues.json')))
    mpath = os.path.join(A.cues, 'music_cues.json')
    mcues = json.load(open(mpath)) if os.path.exists(mpath) else {'duration': tl['duration_en'] + 2.5, 'intensity': [],
                                                                  'events': []}
    if A.plan == 'auto':
        mcues = with_plan(mcues, tl)
    elif A.plan == 'full':
        try:
            mcues, snapped = full_plan(mcues, tl, sfx_cues)
        except Exception as e:                       # never fail the mix on the plan: film.py's sheet + the auto plan
            log('WARNING: music_plan.py full plan failed (%s): --plan auto' % repr(e)[:160])
            mcues, snapped = with_plan(mcues, tl), []
        log(f'music plan FULL: {len(mcues["events"])} events from music_plan.py, {len(snapped)} snapped to the '
            f'picture\'s hit frames: ' + ', '.join(f'{ty} {a:.2f}->{b:.2f}' for ty, a, b in snapped))
        try:
            import sfx_plan as SP
            sfx_cues, slog = SP.apply(sfx_cues if isinstance(sfx_cues, list) else [], tl['lines'])
            for ln_ in slog:
                log('  sfx plan:', ln_)
        except Exception as e:                       # the picture's sheet as it is: never fail the mix on the pass
            log('WARNING: sfx_plan.py failed (%s): the picture\'s SFX sheet as it is' % repr(e)[:160])
    if A.plan == 'full' or A.write_cues:               # what was mixed, for measure_mix.py (the picture's sheets stay)
        ud = os.path.join(A.out, 'cues_used'); os.makedirs(ud, exist_ok=True)
        json.dump(sfx_cues, open(os.path.join(ud, 'sfx_cues.json'), 'w'), indent=0)
        json.dump(mcues, open(os.path.join(ud, 'music_cues.json'), 'w'), indent=0)
    full = float(mcues.get('duration') or 0) or tl['duration_en'] + 2.5     # fix 3: exactly the picture's length (film.py)
    t0 = A.t0; t1 = min(full, A.t1) if A.t1 else full
    dur = t1 - t0; N = int(round(dur * SR)); i0 = int(round(t0 * SR))
    log(f'window {t0:.1f}-{t1:.1f} s ({dur:.1f} s), {len(sfx_cues)} sfx cues, langs {langs}')

    # ---------------- voice
    nfull = int(round(full * SR)) + SR
    who_fx = dict(kv.split('=', 1) for kv in A.who_fx.split(',') if '=' in kv)
    if 'ru' in langs and (A.vo_ru in ('-', '') or not os.path.exists(A.vo_ru)):
        log('WARNING: no RU dub file; rendering en only'); langs = [l for l in langs if l != 'ru'] or ['en']
    vo = voice_tracks(tl, A.vo_en, A.vo_ru, nfull, langs, who_fx)
    vstats = {}
    for k in vo:
        v = vo[k][i0:i0 + N]; v = np.pad(v, (0, N - len(v)))
        vo[k], vstats[k] = voice_chain(v, A.voice_plr, A.voice_ride)
    log('voice chain:', vstats)
    key = vo['en'] if 'en' in vo else vo[langs[0]]

    # ---------------- SFX
    SX.reset()
    buses = {b: np.zeros((N, 2), np.float32) for b in ('beds', 'events', 'hits', 'knocks')}
    ring_act = None
    for j0, wash in ROOMS_WASH:                      # the Doctor film: "It can wait." from every room (stereo)
        a = j0 - i0
        if a < N and a + len(wash) > 0:
            lo = max(0, -a); hi = min(len(wash), N - a)
            buses['events'][a + lo:a + hi] += wash[lo:hi]
    hit_times = []; knock_times = []; counts = {'hits': 0, 'events': 0, 'beds': 0}; skipped = []; fallbacks = {}
    def fb(key, what):
        fallbacks.setdefault(key, {'what': what, 'n': 0})['n'] += 1
        if fallbacks[key]['n'] == 1: log('WARNING:', what)
    def _tkey(k):                                   # a cue with no usable time sorts last (and is skipped below)
        try:
            return (float(sfx_cues[k]['t']), k)
        except (KeyError, TypeError, ValueError):
            return (float('inf'), k)
    if not isinstance(sfx_cues, list):
        log('WARNING: sfx_cues.json is not a list: no SFX'); sfx_cues = []
    sfx_cues = [c if isinstance(c, dict) else {'name': repr(c)} for c in sfx_cues]
    order = sorted(range(len(sfx_cues)), key=_tkey)
    tsfx = time.time()
    for rank, k in enumerate(order):
        c = sfx_cues[k]; name0 = c.get('name', '?')
        try:
            c_t = float(c['t'])
        except (KeyError, TypeError, ValueError):
            fb('bad_t:' + str(name0), f'cue {name0!r} has no usable time ({c.get("t")!r}): skipped'); continue
        if c.get('params') is not None and not isinstance(c.get('params'), dict):
            fb('params:' + str(name0), f'cue {name0!r}: params {c.get("params")!r} is not a dict: defaults used')
        name, params, note = SX.resolve(name0, c.get('params') if isinstance(c.get('params'), dict) else {})
        if name is None:
            skipped.append(name0); fb('name:' + str(name0), note); continue
        if note and note != 'alias':
            fb('name:' + str(name0), note)
        space = c.get('space') or params.pop('space', None)
        params.pop('space', None)
        if space is not None:
            sp2 = SX.resolve_space(space, name)
            if sp2 != space and str(space).lower() not in SX.SPACE_ALIAS and str(space).lower() not in SX.SPACE_LU:
                fb(f'space:{name}:{space}', f'unknown space {space!r} for {name!r}: using {sp2!r}')
            space = sp2
        if name in SX.TIMED:
            params.setdefault('cue_t', c_t)
        try:
            dur_hint = float(params.get('dur', 0) or 0)
        except (TypeError, ValueError):
            fb(f'dur:{name}', f'{name}: dur {params.get("dur")!r} is not a number: dropped'); params.pop('dur', None)
            dur_hint = 0.0
        tt = c_t - t0
        if dur_hint and tt + dur_hint > dur + 2 and name in SX.BEDS:      # window renders: no need for the rest
            params['dur'] = max(1.0, min(dur_hint, dur + 2 - tt))
        if tt > dur + 0.5 or tt + max(dur_hint, 30.0) < 0:
            continue
        try:
            y, pre = SX.render_event(name, seed=int(c.get('seed', rank)), space=space, **params)
        except Exception as e:                  # police: stop. Here: retry with defaults, then skip (both reported)
            log('SFX failed', name, c_t, repr(e)[:160])
            if A.strict:
                raise
            try:
                keep = {kk: params[kk] for kk in ('dur', 'cue_t') if kk in params}
                y, pre = SX.render_event(name, seed=int(c.get('seed', rank)), **keep)
                fb(f'retry:{name}', f'{name} failed with its params/space ({repr(e)[:80]}); rendered with defaults')
            except Exception as e2:
                skipped.append(name0); fb(f'fail:{name}', f'{name} failed twice ({repr(e2)[:80]}); skipped'); continue
        try:
            gdb = float(c.get('gain_db', 0.0) or 0.0)
        except (TypeError, ValueError):
            gdb = 0.0; fb(f'gain:{name}', f'{name}: gain_db {c.get("gain_db")!r} is not a number: 0 dB')
        y = y * 10 ** (gdb / 20)
        try:
            if c.get('pan'):
                y = SX.pan(y, float(c['pan']))
        except (TypeError, ValueError):
            fb(f'pan:{name}', f'{name}: pan {c.get("pan")!r} is not a number: centred')
        if name in RING_DUCK_NAMES and RING_DUCK_DB > 0:   # sound fix round (M1): the landline's bell dips under the words
            if ring_act is None:
                ring_act = voice_activity(key if key.ndim == 1 else key.mean(1), att=0.01, rel=0.12, hold=0.12)
            i_ = int(round((tt - pre) * SR)); j_ = max(0, i_); k_ = min(N, i_ + len(y))
            if k_ > j_:
                y = y.copy()
                y[j_ - i_:k_ - i_] *= (10 ** (-RING_DUCK_DB * ring_act[j_:k_] / 20)).astype(np.float32)[:, None] \
                    if y.ndim == 2 else (10 ** (-RING_DUCK_DB * ring_act[j_:k_] / 20)).astype(np.float32)
        knock = name in ('knock_door', 'box_knock')
        b = 'hits' if name in SX.HITS else 'beds' if name in getattr(SX, 'BED_BUS', SX.BEDS) else 'knocks' if knock else 'events'
        SX.place(buses[b], y, int(round((tt - pre) * SR)))
        if 0 <= tt <= dur:
            counts['events' if knock else b] += 1
            if name in SX.HITS:
                hit_times.append(tt)
            elif knock:
                knock_times.append(tt)
    log(f'sfx rendered in {time.time() - tsfx:.1f} s: {counts}' + (f', skipped {sorted(set(skipped))}' if skipped else ''))

    # ---------------- music
    # windowed renders: the score starts at a pre-roll (up to 30 s before t0) so swells and tails that began before
    # the window are there, and only events at t >= 0 are passed; the pre-roll is cut off afterwards
    ts = max(0.0, t0 - 30.0) if t0 > 0 else 0.0
    sdur = t1 - ts; npre = int(round((t0 - ts) * SR))
    mc = dict(mcues)
    mc['duration'] = sdur
    if mcues.get('intensity'):
        iv = np.array(mcues['intensity'], float)
        mc['intensity'] = [[0.0, float(np.interp(ts, iv[:, 0], iv[:, 1]))]] + \
                          [[p[0] - ts, p[1]] for p in mcues['intensity'] if 0 < p[0] - ts < sdur] + \
                          [[sdur, float(np.interp(t1, iv[:, 0], iv[:, 1]))]]
    mc['events'] = [dict(e, t=e['t'] - ts) for e in mcues.get('events', []) if 0 <= e['t'] - ts < sdur]
    if mcues.get('track_map'):
        mc['track_map'] = window_track_map(mcues['track_map'], ts, sdur)
    tm = time.time()
    stems, score_src = score_stems(mc, sdur, A.fallback)
    stem_names = list(stems)
    music = np.zeros((N, 2), np.float32); mhits = np.zeros((N, 2), np.float32)
    raw_stems = {}
    for k in list(stems):
        s = fit(stems.pop(k), npre + N)[npre:]
        if A.score_stems:
            raw_stems[k] = s.copy()
        if k == 'hits':
            mhits += s                       # music hits: never ducked or EQ'd
        else:
            music += s
        del s
    del stems
    mc['events'] = [dict(e, t=e['t'] - (t0 - ts)) for e in mc['events']]   # back to window time
    log(f'music ({score_src}) in {time.time() - tm:.1f} s, stems {stem_names}')

    # ---------------- bed automation shared by both languages
    # score.py already applies silences and pre-hit ducks for its own events; the placeholder does silences only.
    # So: music gets pre-hit dips for SFX-cue hits; SFX beds get silences + dips for every hit.
    # final mix: the SFX beds (room tone, the night outside, the house settling) dip 6 dB in the drop-outs (was 9: the
    # 3 s drop-out before "Click, click." read as dead air; the house must stay audible when the music goes)
    # (sound fix round: the true silences before the big scares take the room tone down 15 dB: the buzz and the rain
    # kept the drop-outs only 8-10 LU under the scene)
    sil = [(e['t'], e['t'] + float(e.get('len', 1.7)), -15.0 if float(e.get('level') or 0.0) >= TRUE_SILENCE_LEVEL else -6.0,
            0.08, 0.4) for e in mc['events'] if e['type'] == 'silence']
    mus_hits = [e['t'] for e in mc['events'] if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop', 'rule')]
    dip = lambda ts: [(h - 0.05, h, -8.0, 0.4, 0.6) for h in ts]
    kt = sorted(set(round(x, 3) for x in knock_times))
    k_first = [x for i_, x in enumerate(kt) if i_ == 0 or x - kt[i_ - 1] > 1.5]          # the first knock of each group only
    kdip = [(h - 0.05, h, -2.0, 0.25, 0.4) for h in k_first]
    autom = gain_env(N, dip(hit_times) + kdip)
    autom_b = gain_env(N, sil + dip(hit_times + mus_hits) + kdip)
    # true silences ("Then nothing.", the cut on "Seven."): the hits and events buses go out with the score (40 ms), so
    # no hit tail or swap ring is left in them; the room tone stays (beds -6 dB, above)
    deep = [(e['t'], e['t'] + float(e.get('len', 1.7)), -60.0, 0.04, 0.5) for e in mc['events']
            if e['type'] == 'silence' and float(e.get('level') or 0.0) >= TRUE_SILENCE_LEVEL]
    autom_cut = gain_env(N, deep) if deep else None
    if deep:
        log('true silences (hits + events cut):', [round(d[0], 2) for d in deep])
    # score bus: corrective EQ toward the AUDIO_SPEC octave tilt (less 100-160 Hz mud), moderate width, leveler
    music, tilt = match_tilt(music, probe=dyn_cut(music, voice_activity(key), 5.0))
    log('score tilt EQ (dB):', tilt)
    music = SX.width(music, A.music_width); mhits = SX.width(mhits, min(1.0, A.music_width + 0.2))
    music, lev = level_music(music, [(a, b) for a, b, *_ in sil])
    log(f'music leveler: gain p5/p50/p95 {np.percentile(lev, 5):+.1f} / {np.percentile(lev, 50):+.1f} / {np.percentile(lev, 95):+.1f} dB')
    n_sil = sum(1 for e in mc['events'] if e['type'] == 'silence' and 0 <= e['t'] <= dur)

    foley_dip = (10 ** (-FOLEY_DIP_DB * event_activity(buses['events']) / 20)).astype(np.float32)
    buses['events'] += buses.pop('knocks')        # knocks join the events bus after the foley-dip key is taken
    # the hit duck spares each hit's first 0.15 s (0.3 s for the three hardest scares: the transient lands on the cut),
    # but never past the next word: the spare window ends at the next voice onset - 20 ms, and the duck is fully on
    # 60 ms later (review: "Owen can't wink." / "Owen's eyes close." / "And the studio audience..." started 0.10-0.28 s
    # after the boosted hits and were buried under a fixed 0.3 s spare + 0.7 s ramp)
    act_key = voice_activity(key, rel=0.25, hold=DUCK_HOLD_S)
    acth_key = voice_activity(key, att=0.02, rel=0.25)
    von = acth_key > 0.5
    onsets = (np.flatnonzero(von[1:] & ~von[:-1]) + 1) / SR
    spare = np.ones(N, np.float32)
    bwin = np.zeros(N, np.float32)          # the three boosted scares' spare windows (the hits limiter lets them up)
    bwins = []                              # (a, b, grade) per boosted window, samples
    big = [e['t'] for e in mc['events'] if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop') and float(e.get('boost') or 0) > 0]
    # the Bunnyman: the hierarchy of the boosted scares: the face reveal and the swap (boost >= 3.5) are the hardest and
    # get the whole +6 dB of the hits limiter's boosted ceiling; Mom in the doorway, "Back to bed", GET OUT and the
    # narrator's swap get +3 dB, so the two hardest stand out over them
    _grade = lambda b: 1.0 if b >= 3.5 else (0.75 if b >= 2.5 else 0.5)
    bgrade = {round(float(e['t']), 3): _grade(float(e.get('boost') or 0)) for e in mc['events']
              if e['type'] in ('hit', 'stinger', 'braam', 'sub_drop') and float(e.get('boost') or 0) > 0}
    # the Bunnyman: a planned hit may carry 'spare' (s): its spare window is that long even past the next word (the face
    # reveal lands on the cut, 0.1 s before "It's a man.": the transient and body ride over "It's", "man" stays clear)
    forced = {round(float(e['t']), 3): float(e['spare']) for e in mc['events'] if e.get('spare')}
    for h in hit_times + mus_hits:
        long_ = any(abs(h - x) < 0.01 for x in big)
        k_ = np.searchsorted(onsets, h + 0.01)
        nxt = onsets[k_] if k_ < len(onsets) else 1e9
        te = min(h + (0.3 if long_ else 0.15), max(h + 0.02, nxt - 0.02))
        fs = next((v for k, v in forced.items() if abs(k - h) < 0.01), None)
        if fs:
            te = h + fs
        elif long_:                                  # fix round 1: a boosted scare keeps its body for BOOST_SPARE_S even
            te = max(te, h + BOOST_SPARE_S)          # over the next syllables (the 1-4.5 kHz cut keyed to the voice stays)
        tr = 0.06 if nxt - te < 0.5 else (0.4 if long_ else 0.2)
        a = int((h - 0.03) * SR); b = int(te * SR); c = int((te + tr) * SR)
        if b <= 0 or a >= N: continue
        spare[max(0, a):min(N, b)] = 0.0
        if long_:
            bwin[max(0, a):min(N, b)] = next((v for k, v in bgrade.items() if abs(k - h) < 0.01), 1.0)
            bwins.append((a, b, float(bwin[min(N - 1, max(0, a))])))
        if c > b:
            r = np.linspace(0, 1, c - b, dtype=np.float32)[:max(0, min(N, c) - b)]
            spare[b:b + len(r)] = np.minimum(spare[b:b + len(r)], r)
    # fix round 2: the shaped boost (bshape 0..1 with raised-cosine attack / release, bgr the grade carried through the
    # release); the long spare windows' duck also returns over at least 0.25 s (it came back in 60 ms)
    bshape = np.zeros(N, np.float32); bgr = np.zeros(N, np.float32)
    na_, nr_ = int(BOOST_ATT_S * SR), int(BOOST_REL_S * SR)
    for a, b, gd in bwins:
        a0, b1 = max(0, a - na_), min(N, b + nr_)
        if b1 <= a0: continue
        tt = np.arange(a0, b1)
        w = np.ones(len(tt), np.float32)
        up = tt < a; w[up] = np.clip((tt[up] - (a - na_)) / max(1, na_), 0, 1)
        dn = tt >= b; w[dn] = np.clip(1 - (tt[dn] - b) / max(1, nr_), 0, 1)
        w = (np.sin(w * np.pi / 2) ** 2).astype(np.float32)
        bshape[a0:b1] = np.maximum(bshape[a0:b1], w)
        bgr[a0:b1] = np.where(w > 0, np.maximum(bgr[a0:b1], gd), bgr[a0:b1])
        r_ = min(N, b + int(0.6 * SR)) - b          # sound fix r3: 0.25 -> 0.6 s (a smooth release)
        if r_ > 0:
            spare[b:b + r_] = np.minimum(spare[b:b + r_], np.linspace(0, 1, r_, dtype=np.float32) ** 1.5)
    if bwins:
        log(f'boosted windows: {len(bwins)}, attack {BOOST_ATT_S * 1000:.0f} ms, release {BOOST_REL_S * 1000:.0f} ms, '
            f'saturation {BOOST_SAT_DB:.0f} dB x grade, voice-keyed cut {BOOST_VCUT_DB:.0f} dB')
    # the voice always clear (the Bunnyman's final mix): while a line is spoken the bed (music + SFX) stays
    # CLARITY_MARGIN_LU under the narration's own 400 ms level (K-weighted blocks every 50 ms, as measure_mix.py reads
    # them); where it does not (a swell peaking on a line's last word, a loud bar of a track under a quiet word, a hit's
    # tail), the bed is pulled down by the excess (at most CLARITY_MAX_CUT_DB), over the whole block, smoothed. The hits'
    # spare windows (the scares that ride over a line by design) are left alone.
    clar = None
    if CLARITY_MARGIN_LU is not None:
        hb_, wb_ = 0.05, 0.4
        kb_ = int(round(wb_ / hb_)); seg_ = int(round(hb_ * SR))
        vbl = -0.691 + 10 * np.log10(SX._blocks(key, wb_, hb_) + 1e-20)
        Lk = SX.lufs_int(key)
        nb_ = len(vbl); tb_ = np.arange(nb_) * hb_ + wb_ / 2 + t0           # block centres, film time
        inl = np.zeros(nb_, bool)
        for l_ in tl['lines']:
            inl |= (tb_ >= float(l_['t']) + 0.1) & (tb_ <= float(l_['end']) - 0.1)
        ns_ = N // seg_
        sp_seg = spare[:ns_ * seg_].reshape(ns_, seg_).min(1)
        sp_blk = np.ones(nb_, np.float32)
        for k_ in range(kb_):
            sl_ = sp_seg[k_:k_ + nb_]
            sp_blk[:len(sl_)] = np.minimum(sp_blk[:len(sl_)], sl_)
        clar = dict(vbl=vbl, speech=inl & (vbl > Lk - 18.0) & (sp_blk > 0.99), kb=kb_, seg=seg_)
        log(f'clarity: {int(clar["speech"].sum())} of {nb_} blocks are speech the bed must stay '
            f'{CLARITY_MARGIN_LU:.0f} LU under')

    def clarity_gain(bed):
        """Per-sample gain that keeps the bed CLARITY_MARGIN_LU under the narration while it speaks (see above)."""
        bbl = -0.691 + 10 * np.log10(SX._blocks(bed, 0.4, 0.05) + 1e-20)
        n_ = min(len(bbl), len(clar['vbl']))
        over = bbl[:n_] - (clar['vbl'][:n_] - CLARITY_MARGIN_LU) + 0.5
        cut = np.where(clar['speech'][:n_], np.clip(over, 0.0, CLARITY_MAX_CUT_DB), 0.0)
        kb = clar['kb']
        cs = maximum_filter1d(np.concatenate([cut, np.zeros(kb - 1)]), size=kb, origin=(kb - 1) // 2, mode='constant')
        cs = uniform_filter1d(maximum_filter1d(cs, size=3), size=3)       # 150 ms ramps into and out of each cut
        ts = (np.arange(len(cs)) + 0.5) * 0.05; gs = 10 ** (-cs / 20)
        g = np.empty(N, np.float32); step = SR * 20                       # in 20 s chunks (no full-length float64)
        for a_ in range(0, N, step):
            b_ = min(N, a_ + step)
            g[a_:b_] = np.interp(np.arange(a_, b_) / SR, ts, gs)
        return g, float(cut.max()) if len(cut) else 0.0, float((cut > 0.5).mean()) if len(cut) else 0.0

    # the hits split at 150 Hz: the duck (HIT_DUCK_HI_DB) and the voice-keyed bell take only the part above it; the sub
    # body is never ducked (the weight stays) but the whole hits bus is pre-limited under a ceiling that drops while the
    # narration speaks, so the master limiter never pulls a line down under a hit's tail
    _xo = signal.butter(4, 150.0, 'lowpass', fs=SR, output='sos')
    mh_lo = signal.sosfiltfilt(_xo, mhits, axis=0).astype(np.float32); mh_hi = mhits - mh_lo
    sh_lo = signal.sosfiltfilt(_xo, buses['hits'], axis=0).astype(np.float32); sh_hi = buses.pop('hits') - sh_lo
    # a planned hit with 'notch' (s): its 1-4.5 kHz cut NOTCH_DB for that long from the hit on the hits and the SFX
    # events (the window smash under "explodes"), 20 ms ramps, processed locally
    for e_ in mc['events']:
        nl = float(e_.get('notch') or 0.0)
        if nl <= 0: continue
        a_ = int((e_['t'] - 0.15) * SR); b_ = int((e_['t'] + nl + 0.15) * SR)
        if b_ <= 0 or a_ >= N: continue
        a_ = max(0, a_); b_ = min(N, b_)
        tt_ = np.arange(a_, b_) / SR
        act_n = np.clip(np.minimum((tt_ - (e_['t'] - 0.02)) / 0.02, (e_['t'] + nl + 0.02 - tt_) / 0.02), 0, 1).astype(np.float32)
        for X_ in (mh_hi, sh_hi, buses['events']):
            X_[a_:b_] = dyn_cut(X_[a_:b_], act_n, NOTCH_DB)
        log(f'notch {NOTCH_DB:.0f} dB 1-4.5 kHz at {e_["t"]:.2f} s for {nl:.2f} s')
    vpk = float(np.percentile(np.abs(key[np.abs(key) > 1e-4]), 99.9)) if (np.abs(key) > 1e-4).any() else 0.3
    log(f'voice p99.9 peak {20 * np.log10(vpk):.1f} dBFS (the hits limiter\'s reference)')

    Lv_b = SX.lufs_int(key)                 # fix round 2: the boosted scares' loudness targets are set against the voice
    boost_log = []

    def hits_limit(hx, act_h):
        """Variable-ceiling look-ahead peak limiter on the hits bus: ceiling = voice p99.9 - 3 dB in the gaps, - 9 dB more
        while a line is spoken (outside each hit's spare window), + BOOST_CEIL_DB x grade inside the boosted scares'
        spare windows, where the bus is also driven BOOST_DRIVE_DB x grade into the limiter (fix round 1: a denser
        body, so the scares' 400 ms loudness tops the narration; v2.1: at -3 dB the scares' transients were capped and
        the film's loudest moments became narration phrases)."""
        ceil = (vpk * 10 ** ((-3.0 - 9.0 * act_h * spare) / 20)).astype(np.float32)
        boost_log.clear()
        if bwins:
            # inside a boosted scare's spare window the ceiling is absolute, near full scale (the master limiter takes
            # the rest): -1 dBFS for the hardest, -1.5 / -2 for the others (relative to the voice's p99.9 peak, about
            # -12 dBFS, the scares were capped under the narration's own loudness); fix round 2: blended in dB by the
            # shaped window, so the ceiling and the drive come down over BOOST_REL_S after the window, not in 20 ms
            hx = hx * (10 ** (BOOST_DRIVE_DB * bgr * bshape / 20)).astype(np.float32)[:, None]
            cdb = 20 * np.log10(np.maximum(ceil, 1e-9))
            cbd = -1.0 - 2.0 * (1.0 - bgr)
            ceil = (10 ** ((cdb + bshape * np.maximum(cbd - cdb, 0.0)) / 20)).astype(np.float32)
            # fix round 2: density (see BOOST_SAT_DB): per window, scale the bus so its peak sits BOOST_SAT_DB x grade
            # over the ceiling, soft-clip to the ceiling (tanh), cut the clip's 1-4.5 kHz under the voice; all faded by
            # the shaped window, processed locally
            na_, nr_ = int(BOOST_ATT_S * SR), int(BOOST_REL_S * SR)
            for a, b, gd in bwins:
                a0, b1 = max(0, a - na_), min(N, b + nr_)
                if b1 - a0 < 64: continue
                seg = hx[a0:b1]
                w = bshape[a0:b1]
                cl = 10 ** ((-1.0 - 2.0 * (1.0 - gd)) / 20)
                pk_in = float(np.abs(hx[max(0, a):min(N, b)]).max()) if b > a else 0.0
                if pk_in <= 1e-6: continue
                tgt = Lv_b + next((v for k, v in sorted(BOOST_TARGET_LU.items()) if gd <= k + 1e-6), 8.5)
                ca, cb_ = max(0, a) - a0, max(min(N, b), min(N, a + int(0.45 * SR))) - a0
                def _sat(d):
                    pre = (cl * 10 ** (d / 20)) / pk_in
                    gp = (10 ** (w * 20 * np.log10(pre) / 20)).astype(np.float32)[:, None]
                    return dyn_cut((cl * np.tanh(seg * gp / cl)).astype(np.float32), act_h[a0:b1], BOOST_VCUT_DB)
                def _loud(y):
                    yc = y[ca:cb_] * w[ca:cb_, None]
                    return float(-0.691 + 10 * np.log10(SX._blocks(yc, 0.4, 0.05).max() + 1e-20))
                d_ok, l_ok = 0.0, None
                for d in np.arange(0.0, BOOST_SAT_DB + 0.01, 0.5):
                    l_ = _loud(_sat(d))
                    if l_ > tgt and d > 0: break
                    d_ok, l_ok = d, l_
                sat = _sat(d_ok)
                if l_ok is not None and l_ok > tgt:                  # already over its target at no drive: down to it
                    sat *= np.float32(10 ** ((tgt - l_ok) / 20))
                hx[a0:b1] = seg * (1.0 - w)[:, None] + sat * w[:, None]
                if boost_log is not None:
                    boost_log.append((round((a + int(0.03 * SR)) / SR + t0, 2), gd, d_ok, round(l_ok - Lv_b, 1) if l_ok else None,
                                      round(tgt - Lv_b, 1)))
        pk = np.abs(hx).max(1)
        req = np.minimum(1.0, ceil / np.maximum(pk, 1e-9)).astype(np.float32)
        L = int(0.004 * SR)
        g = minimum_filter1d(req, size=2 * L + 1, origin=-L)
        g = np.minimum(uniform_filter1d(g, size=L), g)
        gr = SX.follow((1.0 - g).astype(np.float32), 0.0, SX.coef(0.12))
        return hx * (1.0 - gr)[:, None]

    def bed_for(act, gm, act_h):
        dm = (10 ** (-DUCK_DB * act / 20)).astype(np.float32)
        hd = (10 ** (-HIT_DUCK_HI_DB * act_h * spare / 20)).astype(np.float32)
        m = dyn_cut(music, act, 5.0); m *= (dm * autom * foley_dip * np.float32(gm))[:, None]
        gh = np.float32(gm * 10 ** (A.hits_db / 20))
        hb = dyn_cut(mh_hi, act, HIT_CUT_DB) * (hd * gh)[:, None] + mh_lo * gh
        hb += dyn_cut(sh_hi, act, HIT_CUT_DB) * hd[:, None] + sh_lo; del hd
        hb = hits_limit(hb, act_h)
        if autom_cut is not None:
            hb *= autom_cut[:, None]
        s = dyn_cut(buses['beds'], act, 5.0); s *= (dm * autom_b)[:, None]; del dm
        e = dyn_cut(buses['events'], act, 2.0); e *= (10 ** (-1.5 * act / 20)).astype(np.float32)[:, None]
        if autom_cut is not None:
            e *= autom_cut[:, None]
        s += e; del e
        # the score's hits count as music in the stems (as before), the SFX hits as SFX
        mfrac = np.abs(mh_lo * gh + mh_hi * gh).max(1); sfrac = np.abs(sh_lo + sh_hi).max(1)
        wm = (mfrac / np.maximum(mfrac + sfrac, 1e-9)).astype(np.float32); del mfrac, sfrac
        m += hb * wm[:, None]; s += hb * (1.0 - wm)[:, None]; del hb, wm
        bed, gr, gg = glue(m + s, free=bshape if bwins else None)
        m *= gg[:, None]; s *= gg[:, None]; del gg
        if clar is not None:
            cg, cmax, cfrac = clarity_gain(bed)
            bed *= cg[:, None]; m *= cg[:, None]; s *= cg[:, None]; del cg
            clar['stat'] = (cmax, cfrac)
        return bed, m, s, gr

    # ---------------- solve the music gain on the EN key so the bed sits at voice + bed_rel
    # Target: the bed's typical level, its 3 s short-term median, at voice + bed_p50 (-16 LU: the three references
    # re-measured with true per-channel K-weighting give -15.3 / -16.1 / -16.5; AUDIO_SPEC's short-term numbers come
    # from analysis/measure.py, whose kweight() filters across channels, so they read about 4 dB hot), while the
    # integrated bed stays at or under voice + bed_rel + 1.5 (references: -12.5 / -12.8 / -13.4).
    Lv = SX.lufs_int(key)
    # fix round 1: the boosted scares' spare windows are left out of the bed's statistics (their hits now top the
    # narration by design; counted in, a rule 6 window measured the bed's integrated level 3 LU hot and the solver
    # pulled the whole score down 8 dB under them)
    nbw = (bshape <= 1e-3).astype(np.float32) if bwins else None
    def bstat(b):
        if nbw is not None:
            b = b * nbw[:, None]
        st3 = -0.691 + 10 * np.log10(SX._blocks(b, 3.0, 1.0) + 1e-20)
        return SX.lufs_int(b) - Lv, float(np.median(st3[st3 > -70])) - Lv if (st3 > -70).any() else -70.0
    Lm0 = SX.lufs_int(music + mhits)
    gm = 10 ** ((Lv + A.bed_rel - 1.0 - Lm0) / 20) if Lm0 > -70 else 1.0
    # the rule-by-rule arc (ARC_TARGETS): sections of the music bus, their bed in the gaps steered to the targets in the
    # same loop as the music gain (each pass measures the bed once)
    vbl_g = -0.691 + 10 * np.log10(SX._blocks(key, 0.4, 0.1) + 1e-20)
    arc_secs = []
    _tagi = {l.get('tag'): j for j, l in enumerate(tl['lines'])}

    def _li(a):                                      # a tag, a script phrase (music_plan.line_index) or an index
        if not isinstance(a, str):
            return a
        if a in _tagi:
            return _tagi[a]
        try:
            import music_plan as _MP
            return _MP.line_index(a, tl['lines'])
        except Exception:
            return None
    _arc = [(i_, g) for i_, g in ((_li(a), g) for a, g in ARC_TARGETS) if i_ is not None]
    _arc.sort(key=lambda r: r[0])
    for k_, (li, tgt) in enumerate(_arc[:-1]):
        if tgt is None or li >= len(tl['lines']): continue
        a_ = float(tl['lines'][li]['t']); b_ = float(tl['lines'][_arc[k_ + 1][0]]['t'])
        if b_ > t0 and a_ < t1: arc_secs.append([a_ - t0, b_ - t0, tgt, 0.0])        # window time, target, offset dB

    def gap_levels(bed):
        if nbw is not None:
            bed = bed * nbw[:, None]
        bl = -0.691 + 10 * np.log10(SX._blocks(bed, 0.4, 0.1) + 1e-20)
        n_ = min(len(bl), len(vbl_g)); tb = np.arange(n_) * 0.1 + 0.2
        gap = (vbl_g[:n_] < Lv - 20) & (bl[:n_] > Lv - 60)
        out = []
        for a_, b_, tgt, off in arc_secs:
            sel = gap & (tb >= a_ + 0.5) & (tb < b_ - 0.5)
            # Bus film: the tight voice edit leaves few >= 0.4 s gaps; 0.6 s of them is enough for a median
            out.append(float(np.median(bl[:n_][sel])) - Lv if sel.sum() >= 6 else None)
        return out

    def arc_env(secs):
        env = np.zeros(N, np.float32); xf = int(1.0 * SR)
        for a_, b_, tgt, off in secs:
            ia, ib = max(0, int(a_ * SR)), min(N, int(b_ * SR))
            if ib <= ia or off == 0: continue
            w = np.ones(ib - ia, np.float32)
            r = min(xf, (ib - ia) // 2)
            if r > 1:
                ramp = (np.sin(np.linspace(0, np.pi / 2, r)) ** 2).astype(np.float32)
                w[:r] = ramp; w[-r:] = ramp[::-1]
            env[ia:ib] += np.float32(off) * w
        return env

    music_base = music
    for it in range(7):
        bed, _m, _s, gr = bed_for(act_key, gm, acth_key); del _m, _s
        Li, P50 = bstat(bed)
        gl = gap_levels(bed) if arc_secs else []; del bed
        err = min(A.bed_p50 - P50, (A.bed_rel + 1.5) - Li)
        aerr = [(sec[2] - g) if g is not None else None for sec, g in zip(arc_secs, gl)]
        # a section with no measurable gaps keeps the shape's mean (it was 0.0, and the shape step then pushed every
        # unmeasured rule to -6 dB, so rules 5 and 6 played quieter than 3 and 4)
        _known = [x for x in aerr if x is not None]
        aerr = [x if x is not None else (float(np.mean(_known)) if _known else 0.0) for x in aerr]
        log(f'  music gain iter {it}: music {20 * np.log10(gm):+.1f} dB, bed integrated {Li:+.2f} LU, p50 {P50:+.2f} LU rel voice'
            + ('; bed in gaps by rule ' + ' '.join('%+.1f' % g if g is not None else '-' for g in gl) +
               ' (arc offsets ' + ' '.join('%+.1f' % sec[3] for sec in arc_secs) + ' dB)' if arc_secs else ''))
        mean_e = float(np.mean(aerr)) if aerr else 0.0
        arc_done = all(abs(x - mean_e) < 0.6 for x in aerr) or it >= 5     # the shape (the music gain takes the mean)
        if abs(err) < 0.2 and arc_done:
            break
        if abs(err) >= 0.2:
            gm *= 10 ** (err * 1.1 / 20)
        if not arc_done:
            for sec, x in zip(arc_secs, aerr):              # the shape only (the music gain takes the mean)
                sec[3] = float(np.clip(sec[3] + 0.9 * (x - mean_e), -ARC_MAX_DB, ARC_MAX_DB))
            music = music_base * (10 ** (arc_env(arc_secs) / 20)).astype(np.float32)[:, None]
    del music_base
    # keep the music clearly present: music alone, as heard (after the ducks), within voice -17 .. -10 LU (v2.1: was
    # measured before the ducks, which with the 4.5 dB duck pulled the whole bed 2 dB under the target)
    _b, _m, _s, _g = bed_for(act_key, gm, acth_key); del _b, _s
    Lm = SX.lufs_int(_m) - Lv; del _m
    if Lm < -17: gm *= 10 ** ((-17 - Lm) / 20)
    if Lm > -10: gm *= 10 ** ((-10 - Lm) / 20)

    report = {'cues_sha1': hashes, 'window': [t0, t1], 'score': score_src,
              'arc': [{'t': round(a_ + t0, 2), 'target_gap_lu': tgt, 'offset_db': round(off, 2)} for a_, b_, tgt, off in arc_secs],
              'music_gain_db': round(20 * np.log10(gm), 2), 'hits_db': A.hits_db, 'plan': A.plan,
              'sfx_counts': counts, 'silences': n_sil, 'langs': {},
              'sfx_fallbacks': [dict(key=k, **v) for k, v in fallbacks.items()], 'sfx_skipped': sorted(set(skipped)),
              'boosts': [dict(t=t_, grade=g_, sat_db=float(d_), loud_lu_rel_voice=l_, target_lu=tg_)
                         for t_, g_, d_, l_, tg_ in boost_log]}
    for t_, g_, d_, l_, tg_ in boost_log:
        log(f'boosted scare {t_:8.2f} s grade {g_:.2f}: saturation {d_:.1f} dB, loudest 400 ms {l_} LU over the voice (target {tg_})')
    stem_dir = os.path.join(A.out, 'stems'); os.makedirs(stem_dir, exist_ok=True)
    for lang in langs:
        v = vo[lang]
        if lang == langs[0] and lang == 'en':
            act, act_h = act_key, acth_key
        else:
            act, act_h = voice_activity(v, rel=0.25), voice_activity(v, att=0.02, rel=0.25)
        bed, m_out, s_out, gr = bed_for(act, gm, act_h)
        vst = np.stack([v, v], 1)
        mix = vst + bed
        if t1 >= full - 0.01:                     # fix 3: master fade to silence at the end (the cut to black); the
            nf = min(N, int(0.6 * SR))            # Bunnyman: 0.6 s (1.5 s cut the outro song's last hum, ~1088.4 s)
            mix[N - nf:] *= np.linspace(1.0, 0.0, nf, dtype=np.float32)[:, None] ** 2
        gdb = TARGET - SX.lufs_int(mix); ceiling = -1.7; y = None
        for it in range(6):
            y = None
            y, lim_db, lim_frac = tp_limit(mix * np.float32(10 ** (gdb / 20)), ceiling)
            Lo = SX.lufs_int(y); tp = true_peak(y)
            if tp > -1.5 and it < 5:
                ceiling -= (tp + 1.5) + 0.05; continue
            if abs(Lo - TARGET) <= 0.1 or it == 5:
                break
            gdb += TARGET - Lo
        del mix
        g = np.float32(10 ** (gdb / 20))
        sf.write(os.path.join(A.out, f'mix_{lang}.wav'), y, SR, subtype='PCM_24'); del y
        # loudness is measured unscaled and shifted by the master gain (no full-length temporaries)
        Lv0 = SX.lufs_int(vst); Lvv = Lv0 + gdb
        vb = short_term_rel(vst, Lv0); bb = short_term_rel(bed, Lv0)
        speech = vb > -20
        st3 = short_term_rel(bed, Lv0, 3.0, 0.1)
        r = {'mix_lufs': round(Lo, 2), 'true_peak_dbtp': round(tp, 2), 'voice_lufs': round(Lvv, 2),
             'voice_rel_mix': round(Lvv - Lo, 2), 'bed_rel_voice': round(SX.lufs_int(bed) - Lv0, 2),
             'music_rel_voice': round(SX.lufs_int(m_out) - Lv0, 2),
             'sfx_rel_voice': round(SX.lufs_int(s_out) - Lv0, 2),
             'bed_speech_median': round(float(np.median(bb[speech])), 1) if speech.any() else None,
             'bed_gap_median': round(float(np.median(bb[~speech])), 1) if (~speech).any() else None,
             'bed_st3s_p10_p50_p90_K': [round(float(np.percentile(st3, q)), 1) for q in (10, 50, 90)],
             'bed_lra_K': round(float(np.percentile(st3[st3 > -60], 95) - np.percentile(st3[st3 > -60], 10)), 1),
             'music_present_pct': round(100 * float((short_term_rel(m_out, Lv0) > -20).mean()), 1),
             'glue_gr_p95_db': round(gr, 2), 'limiter_max_gr_db': round(lim_db, 2),
             'limiter_over_1dB_pct': round(100 * lim_frac, 2), 'master_gain_db': round(float(gdb), 2)}
        if clar is not None and 'stat' in clar:
            r['clarity_cut_max_db'] = round(clar['stat'][0], 1)
            r['clarity_blocks_cut_pct'] = round(100 * clar['stat'][1], 2)
        del bed
        report['langs'][lang] = r
        log(lang, json.dumps(r))
        if not A.no_stems:
            vst *= g; sf.write(os.path.join(stem_dir, f'voice_{lang}.wav'), vst, SR, subtype='FLOAT')
            if lang == langs[0]:
                m_out *= g; sf.write(os.path.join(stem_dir, 'music.wav'), m_out, SR, subtype='FLOAT')
                s_out *= g; sf.write(os.path.join(stem_dir, 'sfx.wav'), s_out, SR, subtype='FLOAT')
                for k, x in raw_stems.items():
                    sf.write(os.path.join(stem_dir, f'score_{k}.wav'), x * np.float32(gm) * g, SR, subtype='FLOAT')
                raw_stems = {}
        del vst, m_out, s_out
    mins = dur / 60
    report['per_min'] = {'hits': round((counts['hits'] + sum(1 for e in mc['events'] if e['type'] in ('hit', 'stinger', 'braam')
                                                              and 0 <= e['t'] <= dur)) / mins, 2),
                         'sfx_events': round(counts['events'] / mins, 2), 'silences': round(n_sil / mins, 2)}
    report['seconds'] = round(time.time() - T0, 1)
    import resource
    report['peak_rss_mb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    json.dump(report, open(os.path.join(A.out, 'mix_report.json'), 'w'), indent=1)
    log('done in %.1f s, peak RSS %d MB' % (report['seconds'], report['peak_rss_mb']))


if __name__ == '__main__':
    main()
