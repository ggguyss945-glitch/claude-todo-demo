"""Catalogue of the owner's Epidemic Sound downloads (licensed through the owner's subscription; never commit the audio).

    python3 epidemic_catalog.py <epidemic dir> <out.json> [--film police|mirror]

    police:  $S/pov2/samples/epidemic -> catalog_epidemic.json (the police film's 74 SFX + 6 tracks; unchanged logic)
    mirror:  film/_work/samples/epidemic -> catalog_epidemic_mirror.json (default when the dir is the mirror film's)
             python3 audio/epidemic_catalog.py "_work/samples/epidemic" audio/catalog_epidemic_mirror.json --film mirror

Files are 48 kHz WAVs in <dir>/sfx and <dir>/music (Epidemic's own names, e.g. "Bells, Handbell, Small, ... Ring.wav";
<dir>/music_unverified is never read). library.py loads the mirror catalogue FIRST, so these files win every pick.

SFX entry: path (absolute), file, slug, serves (the SFX names it can build, see MAP / MAP_MIRROR), tags, dur, lufs,
    peak_db, onsets, centroid_hz (median spectral centroid), floor_db, events (onset count / s).
Music entry: path, file, slug, title, artist, dur, lufs, peak_db, tempo, pulse (0..1 beat clarity: autocorrelation
    peak of the onset envelope), key (Krumhansl-Kessler: 'D minor'), key_r (correlation), tonal_centre (pitch class
    name), bass_root (dominant bass pitch class, 28-130 Hz chroma), loudness_2s (short-term LUFS, 3 s window every 2 s),
    centroid_2s (Hz every 2 s), onset_rate_10s (onsets / s every 10 s), sections ([{t0, t1, lufs, centroid, key,
    bass_root, pulse}], boundaries from MFCC+chroma agglomerative clustering, merged to >= 8 s), lra (LU), mood
    (measured descriptor: dark/bright, pulsed/unpulsed, quiet/loud, rising/flat).
"""
import json, os, re, sys
import numpy as np, soundfile as sf, librosa, pyloudnorm

SR = 48000
NOTES = 'C C# D D# E F F# G G# A A# B'.split()
# required SFX name -> filename keywords (all words must appear in the file slug)   [police film]
MAP = {
    'knock_door': [['knock', 'wood'], ['knock', 'glass_panel'], ['knock', 'metal_garage']],
    'doorbell_chime': [['doorbell']],
    'footsteps_porch': [['footsteps', 'porch'], ['footsteps', 'creaky']],
    'footsteps_wood_inside': [['footsteps', 'creaky'], ['footsteps', 'barn'], ['footsteps', 'cabin']],
    'car_pass': [['car_pass']],
    'car_idle': [['idle']],
    'car_door_open': [['door_car']],
    'car_door_close': [['door_car']],
    'siren_far': [['siren']],
    'police_radio_squelch': [['walkie_talkie'], ['static_radio']],
    'radio_static': [['static']],
    'radio_click': [['ui_buttons_confirm'], ['click']],
    'bodycam_beep': [['camera', 'focus']],
    'phone_ring': [['phone_ringing']],
    'phone_busy': [['busy_tone']],
    'phone_vibrate': [['vibration']],
    'mail_slot': [['mailbox']],
    'paper': [['paper']],
    'key_in_lock': [['keys'], ['deadbolt']],
    'lock_turn': [['deadbolt'], ['mortise_lock']],
    'chain_lock': [['security_chain']],
    'breath': [['breath']],
    'heartbeat': [['heartbeat']],
    'whoosh': [['whoosh']],
    'riser': [['riser']],
    'braam': [['braam']],
    'impact_hit': [['stinger'], ['hit', 'impact']],
    'stinger': [['stinger']],
    'sub_drop': [['bass_drop'], ['bass_dive']],
    'ui_pop': [['menu_ui'], ['pops'], ['ui_buttons']],
    'tinnitus': [['tinnitus']],
    'ambience_night': [['ambience', 'night']],
}
# mirror film: SFX name -> slug keyword alternatives (sound_plan.names). A file may serve several names.
MAP_MIRROR = {
    'ambience_dawn': [['birdsong', 'dawn']],
    'ambience_memory': [['birdsong', 'dawn'], ['lake', 'birdsong']],
    'ambience_camp_night': [['lake', 'frogs', 'night'], ['forest', 'night', 'crickets']],
    'room_tone': [['room_tone', 'wooden_cabin']],
    'bed_creak': [['mattress', 'creak'], ['bunk_bed', 'movement'], ['bunk_bed', 'jump']],
    'wood_thud': [['bunk_bed', 'jump']],
    'body_fall': [['bunk_bed', 'jump'], ['throw_clothes', 'floor']],
    'bell_cracked': [['handbell'], ['hand_bell']],
    'bell_clean': [['handbell'], ['temple', 'ring'], ['small', 'decorative_bell']],
    'gate_chain': [['chains', 'gate']],
    'padlock': [['chains', 'padlock'], ['lock', 'unlock'], ['padlock', 'combination']],
    'clock_tick': [['clocks', 'tick']],
    'clock_tick_backward': [['clocks', 'tick']],
    'towel_cloth': [['cloth', 'towel'], ['cloth', 'throw'], ['cloth', 'flap']],
    'towel_drop': [['throw_clothes', 'floor'], ['cloth', 'towel']],
    'cloth_grab': [['cloth', 'handle'], ['cloth', 'throw']],
    'cloth_press': [['cloth', 'wipe'], ['couch', 'fabric']],
    'jacket_cloth': [['cloth', 'throw'], ['cloth', 'handle']],
    'lace_pull': [['cloth', 'handle']],
    'glass_wipe': [['cloth', 'wipe'], ['couch', 'wipe'], ['glass', 'friction']],
    'lipstick_smear': [['glass', 'friction']],
    'lipstick_draw': [['glass', 'friction']],
    'glass_tap': [['glass', 'tap'], ['press_jug', 'tap']],
    'nail_click_glass': [['nail_tap'], ['glass_tap', 'small']],
    'glass_resonance': [['vase', 'tonal'], ['temple', 'ring']],
    'phone_ring': [['telephone', 'handset']],
    'phone_pickup': [['telephone', 'handset']],
    'phone_message': [['text_message']],
    'door_creak': [['wooden_door', 'creaks']],
    'screen_door': [['dryer_door', 'squeak'], ['wooden_door', 'creaks']],
    'crate_creak': [['wooden_door', 'creaks'], ['wood', 'break', 'bend']],
    'mirror_handle': [['wooden_door', 'creaks']],
    'gate_creak': [['gate', 'metal']],
    'flashlight_click': [['flashlight']],
    'bare_foot_step': [['footsteps', 'barefoot']],
    'wet_footstep': [['footsteps', 'barefoot']],
    'footsteps_run': [['running', 'wood_stairs']],
    'breath': [['breath']],
    'queen_presence': [['magic', 'shimmer'], ['whisper']],
    'crowd_whisper': [['whisper']],
    'candy_wrapper': [['candy'], ['wrapper']],
    'crate_break': [['wood', 'break']],
    'water_drip': [['water', 'drip']],
    'drop_reverse': [['water', 'drip']],
    'sprinkler_spit': [['sprinklers']],
    'impact_metal': [['metal', 'clang']],
    'portal': [['portal'], ['scifi', 'door']],
    'rain_porch': [['rain', 'porch']],
}


def slug(s):
    s = s.replace('#', 's').lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')


def serves(sl, table):
    return sorted(k for k, alts in table.items() if any(all(w in sl for w in alt) for alt in alts))


KK_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def kk_key(ch):
    """Krumhansl-Kessler key from a 12-bin chroma vector -> (name, r, root pc, mode +1/-1)."""
    best = (-2, 0, 1)
    for r in range(12):
        for prof, mode in ((KK_MAJ, 1), (KK_MIN, -1)):
            c = float(np.corrcoef(ch, np.roll(prof, r))[0, 1])
            if c > best[0]:
                best = (c, r, mode)
    c, r, mode = best
    return f"{NOTES[r]} {'major' if mode > 0 else 'minor'}", round(c, 3), r, mode


def pulse_clarity(oenv, sr_env):
    """Peak of the normalised onset-envelope autocorrelation at beat lags 0.3-1.5 s (0 = no pulse, ~1 = metronome)."""
    o = oenv - oenv.mean()
    if len(o) < 64 or not np.any(o):
        return 0.0
    ac = np.correlate(o, o, 'full')[len(o) - 1:]
    ac = ac / (ac[0] + 1e-12)
    a, b = int(0.3 * sr_env), min(len(ac) - 1, int(1.5 * sr_env))
    return round(float(max(0.0, ac[a:b].max())), 3) if b > a else 0.0


def short_term(meter, x, hop_s=2.0, win_s=3.0):
    hop = int(hop_s * SR); out = []
    for i in range(0, max(1, len(x) - hop), hop):
        seg = x[i:i + int(win_s * SR)]
        v = meter.integrated_loudness(seg) if len(seg) > SR else -70
        out.append(round(float(v) if np.isfinite(v) else -70.0, 1))
    return out


def sfx_entry(meter, p, table):
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    m = x.mean(1)
    lufs = meter.integrated_loudness(x[:, :2] if x.shape[1] >= 2 else x) if len(x) > sr * 0.4 else None
    y = librosa.resample(m, orig_sr=sr, target_sr=22050)
    on = librosa.onset.onset_detect(y=y, sr=22050, units='time')
    cent = librosa.feature.spectral_centroid(y=y, sr=22050, hop_length=1024)[0]
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=1024)[0]
    live = rms > rms.max() * 0.05
    sl = slug(os.path.splitext(os.path.basename(p))[0])
    dur = len(x) / sr
    return {'path': p, 'file': os.path.basename(p), 'slug': sl, 'serves': serves(sl, table),
            'tags': [w for w in sl.split('_') if len(w) > 1][:16], 'dur': round(dur, 2), 'sr': sr, 'channels': x.shape[1],
            'lufs': None if lufs is None or not np.isfinite(lufs) else round(float(lufs), 1),
            'peak_db': round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1), 'onsets': len(on),
            'events': round(len(on) / max(dur, 0.1), 2),
            'centroid_hz': int(np.median(cent[live])) if live.any() else 0,
            'floor_db': round(float(20 * np.log10(np.percentile(rms, 5) + 1e-9)), 1)}


def music_entry(meter, p):
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    x = x[:, :2] if x.shape[1] >= 2 else np.repeat(x, 2, 1)
    m = x.mean(1)
    y = librosa.resample(m, orig_sr=sr, target_sr=22050)
    hop = 2048
    oenv = librosa.onset.onset_strength(y=y, sr=22050, hop_length=512)
    tempo = float(np.atleast_1d(librosa.beat.beat_track(onset_envelope=oenv, sr=22050, hop_length=512)[0])[0])
    chroma = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=hop, fmin=librosa.note_to_hz('C1'), n_octaves=7)
    bass = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=hop, fmin=librosa.note_to_hz('A0'), n_octaves=2,
                                      bins_per_octave=36)
    key, kr, root, mode = kk_key(chroma.mean(1))
    st = short_term(meter, x)
    cent = librosa.feature.spectral_centroid(y=y, sr=22050, hop_length=22050 * 2)[0]
    feats = librosa.feature.mfcc(y=y, sr=22050, hop_length=hop, n_mfcc=13)
    dur = len(x) / sr
    k = max(3, min(10, int(dur / 22)))
    bounds = librosa.frames_to_time(librosa.segment.agglomerative(np.vstack([feats, chroma]), k), sr=22050, hop_length=hop)
    bounds = sorted(set([0.0] + [float(b) for b in bounds if b > 0.5] + [dur]))
    merged = [bounds[0]]
    for b in bounds[1:]:
        if b - merged[-1] >= 8 or b == dur:
            if b == dur and dur - merged[-1] < 8 and len(merged) > 1:
                merged[-1] = dur
            else:
                merged.append(b)
    fps = 22050 / hop; fpo = 22050 / 512
    sects = []
    for a, b in zip(merged[:-1], merged[1:]):
        seg = x[int(a * sr):int(b * sr)]
        L = meter.integrated_loudness(seg) if len(seg) > sr else -70
        ia, ib = int(a * fps), max(int(a * fps) + 1, int(b * fps))
        kn, _, _, _ = kk_key(chroma[:, ia:ib].mean(1))
        c2 = cent[int(a / 2):max(int(a / 2) + 1, int(b / 2))]
        sects.append({'t0': round(a, 1), 't1': round(b, 1), 'lufs': round(float(L) if np.isfinite(L) else -70, 1),
                      'centroid': int(np.mean(c2)) if len(c2) else 0, 'key': kn,
                      'bass_root': NOTES[int(bass[:, ia:ib].mean(1).argmax())],
                      'pulse': pulse_clarity(oenv[int(a * fpo):int(b * fpo)], fpo)})
    on = librosa.onset.onset_detect(onset_envelope=oenv, sr=22050, hop_length=512, units='time')
    rate10 = [round(float(((on >= t) & (on < t + 10)).sum() / 10), 2) for t in np.arange(0, dur - 1, 10)]
    lufs = float(meter.integrated_loudness(x))
    live = np.array([v for v in st if v > -60])
    lra = float(np.percentile(live, 95) - np.percentile(live, 10)) if len(live) > 4 else 0.0
    pc = pulse_clarity(oenv, fpo)
    cm = float(np.median(cent))
    third = len(st) // 3
    rise = (np.mean(st[-third:]) - np.mean(st[:third])) if third else 0
    mood = ', '.join([('dark' if cm < 1300 else 'mid' if cm < 2200 else 'bright'),
                      ('unpulsed' if pc < 0.25 else 'light pulse' if pc < 0.45 else 'pulsed'),
                      ('quiet' if lufs < -24 else 'moderate' if lufs < -17 else 'loud'),
                      ('rising' if rise > 4 else 'falling' if rise < -4 else 'flat arc')])
    base = os.path.splitext(os.path.basename(p))[0]
    title, _, artist = base.partition(' - ')
    return {'path': p, 'file': os.path.basename(p), 'slug': slug(base), 'title': title.replace('_', "'"),
            'artist': artist, 'dur': round(dur, 2), 'lufs': round(lufs, 1),
            'peak_db': round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1), 'tempo': round(tempo, 1), 'pulse': pc,
            'key': key, 'key_r': kr, 'tonal_centre': NOTES[root],
            'bass_root': NOTES[int(bass.mean(1).argmax())], 'lra': round(lra, 1), 'centroid_median': int(cm),
            'mood': mood, 'loudness_2s': st, 'centroid_2s': [int(c) for c in cent], 'onset_rate_10s': rate10,
            'sections': sects}


def main(d, out, film=None):
    film = film or ('mirror' if 'Mirror Steps' in os.path.abspath(d) else 'police')
    table = MAP_MIRROR if film == 'mirror' else MAP
    meter = pyloudnorm.Meter(SR)
    cat = {'film': film,
           'licence': 'Epidemic Sound, through the channel owner\'s subscription. Keep the channel connected in the '
                      'Epidemic account to avoid Content ID claims. Do not redistribute or commit the files.',
           'dir': os.path.abspath(d), 'sfx': [], 'music': []}
    for f in sorted(os.listdir(os.path.join(d, 'sfx'))):
        if f.lower().endswith(('.wav', '.flac', '.aif', '.aiff')):
            cat['sfx'].append(sfx_entry(meter, os.path.abspath(os.path.join(d, 'sfx', f)), table))
    for f in sorted(os.listdir(os.path.join(d, 'music'))):
        if f.lower().endswith(('.wav', '.flac', '.aif', '.aiff')):
            cat['music'].append(music_entry(meter, os.path.abspath(os.path.join(d, 'music', f))))
            print('music', f, flush=True)
    json.dump(cat, open(out, 'w'), indent=1)
    cov = sorted({s for e in cat['sfx'] for s in e['serves']})
    print(f"{len(cat['sfx'])} sfx, {len(cat['music'])} music; covers {len(cov)} names: {', '.join(cov)}")
    print('unmapped:', [e['slug'] for e in cat['sfx'] if not e['serves']])
    for mu in cat['music']:
        print(f"{mu['slug']}: {mu['dur']:.0f}s {mu['lufs']} LUFS lra {mu['lra']} tempo {mu['tempo']} pulse {mu['pulse']} "
              f"key {mu['key']} ({mu['key_r']}) bass {mu['bass_root']} cent {mu['centroid_median']} | {mu['mood']}")
        print('   ', ' | '.join(f"{s['t0']:.0f}-{s['t1']:.0f} {s['lufs']} {s['key']} b{s['bass_root']} p{s['pulse']}"
                                for s in mu['sections']))


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    fl = sys.argv[sys.argv.index('--film') + 1] if '--film' in sys.argv else None
    if fl:
        a = [x for x in a if x != fl]
    main(a[0], a[1], fl)
