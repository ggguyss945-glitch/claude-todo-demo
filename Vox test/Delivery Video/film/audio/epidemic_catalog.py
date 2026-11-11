"""Catalogue of the owner's Epidemic Sound downloads (licensed through the owner's subscription; never commit or copy
the audio out of the sample folders).

    python3 epidemic_catalog.py --delivery            the delivery film: writes audio/catalog_epidemic_delivery.json from
                                                      W/samples/epidemic (new set), epidemic_police and epidemic_mirror
    python3 epidemic_catalog.py <out.json> <set>=<dir> [<set>=<dir> ...]     any list of sets (first set wins on duplicates)
    python3 epidemic_catalog.py <epidemic dir> <out catalog_epidemic.json>   the police form (one set, kept working)
    --sfx-only                                        skip the (slow, ~10 s per track) music analysis and keep the music
                                                      entries of an existing output file

Each set folder holds 48 kHz WAVs in <dir>/sfx and <dir>/music (music_unverified and _zips are ignored).
For every SFX: set, slug (lower-case words joined by '_', so 'Bells, Doorbell, Ding Dong, Single.wav' ->
'bells_doorbell_ding_dong_single'; the police files keep their slugs), path (absolute, through W/samples), duration,
integrated loudness, sample peak, onset count, and `serves`: the SFX names in sfx.NAMES (police + delivery) it can
build. A file present in two sets (same slug, or same size and first megabyte) is listed once, under the first set,
with `also_in`.
For every music track: duration, loudness, a 2-second short-term loudness curve, a brightness curve (spectral
centroid), tempo and pulse clarity, tonal centre (chroma argmax), key and mode (Krumhansl profiles), bass root (lowest
octave chroma), loudness p10/p50/p90, centroid median, and section boundaries (agglomerative on MFCC + chroma) with
each section's mean loudness and brightness, so the score can cut and layer tracks to the film's intensity curve.
"""
import hashlib, json, os, re, sys
import numpy as np, soundfile as sf

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
DELIVERY_SETS = [('delivery', os.path.join(W, 'samples', 'epidemic')),
                 ('police', os.path.join(W, 'samples', 'epidemic_police')),
                 ('mirror', os.path.join(W, 'samples', 'epidemic_mirror'))]
DELIVERY_OUT = os.path.join(HERE, 'catalog_epidemic_delivery.json')
NOTES = 'C C# D D# E F F# G G# A A# B'.split()

# SFX name -> filename keyword alternatives (every word of one alternative must appear in the slug). Police names first
# (unchanged), then the delivery film's names (sfx.py DELIVERY_NAMES).
MAP = {
    'knock_door': [['knock', 'wood'], ['knock', 'glass_panel'], ['knock', 'metal_garage']],
    'doorbell_chime': [['doorbell']],
    'footsteps_porch': [['footsteps', 'porch'], ['footsteps', 'creaky']],
    'footsteps_wood_inside': [['footsteps', 'creaky'], ['footsteps', 'barn'], ['footsteps', 'cabin'],
                              ['footsteps', 'barefoot']],
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
    'key_in_lock': [['keys_jingle'], ['keys_car_keys'], ['deadbolt']],
    'lock_turn': [['deadbolt'], ['mortise_lock'], ['lock_entrance']],
    'chain_lock': [['security_chain'], ['chains', 'padlock']],
    'door_creak': [['doors_creak']],
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
    'ambience_night': [['ambience', 'suburban']],        # suburban streets only (not the mirror set's cabin / lake / tropical)
    'room_tone': [['room_tone']],
    'clock_tick': [['clocks', 'tick']],
    'crowd_whisper': [['whisper']],
    # ---- delivery film
    'doorbell_dingdong': [['doorbell', 'ding_dong'], ['doorbell_doorbell_0'], ['doorbell', 'ring_old']],
    'doorbell_cam_chime': [['notification'], ['text_message'], ['doorbell', 'ding_dong']],
    'phone_notify': [['notification'], ['text_message']],
    'box_knock': [['cardboard', 'impact'], ['cardboard', 'punch'], ['knock', 'wood']],
    'box_tap': [['cardboard', 'impact'], ['cardboard', 'lid'], ['cardboard', 'remove']],
    'box_creak': [['cardboard', 'rummage'], ['cardboard', 'lid'], ['cardboard_box_open']],
    'box_drop': [['cardboard', 'impact'], ['cardboard', 'lid']],
    'box_scrape': [['cardboard', 'drag'], ['box', 'drag'], ['box', 'scrape']],
    'box_open': [['cardboard_box_open'], ['cardboard', 'remove'], ['cardboard', 'rummage']],
    'box_voice': [['cardboard', 'rummage'], ['whisper'], ['breath', 'calm']],
    'tape_rip': [['tape']],
    'hazard_ticks': [['hazard']],
    'van_door_slide': [['van', 'sliding'], ['doors_sliding']],
    'van_idle': [['diesel', 'idle'], ['idle']],
    'van_pull_away': [['idle'], ['car_pass']],
    'van_step': [['footsteps', 'porch'], ['metal', 'impact']],
    'keys_drop': [['keys', 'drop'], ['glass', 'tap'], ['vase', 'tap']],
    'window_slide': [['windows', 'sliding'], ['doors_sliding']],
    'curtain_flutter': [['cloth', 'flap']],
    'cloth_rustle': [['cloth', 'handle'], ['cloth', 'wipe'], ['cloth_flap_towel']],
    'touch_tap': [['touch_screen'], ['touchscreen']],
    'stylus_scribble': [['glass', 'friction'], ['touch_screen']],
    'camera_shutter': [['camera']],
    'footsteps_stairs': [['stairs'], ['footsteps', 'barefoot']],
    'footsteps_hall': [['footsteps', 'barefoot'], ['footsteps', 'creaky']],
    'mom_breath': [['breath', 'calm'], ['breath', 'anxious'], ['whisper', 'female']],
    'mom_sob': [['breath', 'calm'], ['breath', 'anxious'], ['whisper', 'female']],
    'ambience_suburb': [['ambience', 'suburban']],
    'ambience_dawn': [['dawn'], ['birdsong', 'morning']],
    'room_tone_house': [['room_tone']],
    'flashlight_click': [['flashlight']],
    'bed_creak': [['bed', 'creak'], ['bunk_bed']],
}


def slugify(name):
    s = re.sub(r'[^0-9a-z]+', '_', name.lower()).strip('_')
    return re.sub(r'_+', '_', s)


def serves(slug):
    return sorted(k for k, alts in MAP.items() if any(all(w in slug for w in alt) for alt in alts))


def _fingerprint(p):
    with open(p, 'rb') as f:
        return f'{os.path.getsize(p)}:{hashlib.md5(f.read(1 << 20)).hexdigest()}'


# Krumhansl-Kessler key profiles
_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def key_of(chroma_mean):
    best = (-2, 0, 'minor')
    for r in range(12):
        for prof, mode in ((_MAJ, 'major'), (_MIN, 'minor')):
            c = float(np.corrcoef(np.roll(prof, r), chroma_mean)[0, 1])
            if c > best[0]:
                best = (c, r, mode)
    return NOTES[best[1]], best[2], round(best[0], 3)


def sfx_entry(meter, p, set_name, slug):
    import librosa
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    m = x.mean(1)
    lufs = meter.integrated_loudness(x[:, :2] if x.shape[1] > 1 else x[:, 0]) if len(x) > sr * 0.4 else None
    on = librosa.onset.onset_detect(y=librosa.resample(m, orig_sr=sr, target_sr=22050), sr=22050, units='time')
    return {'path': p, 'set': set_name, 'slug': slug, 'serves': serves(slug), 'dur': round(len(x) / sr, 2), 'sr': sr,
            'lufs': None if lufs is None or not np.isfinite(lufs) else round(float(lufs), 1),
            'peak_db': round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1), 'onsets': len(on)}


def music_entry(meter, p, set_name, slug):
    import librosa
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    x = x[:, :2]
    m = x.mean(1)
    y = librosa.resample(m, orig_sr=sr, target_sr=22050)
    oenv = librosa.onset.onset_strength(y=y, sr=22050)
    tempo = float(np.atleast_1d(librosa.beat.beat_track(onset_envelope=oenv, sr=22050)[0])[0])
    ac = librosa.autocorrelate(oenv - oenv.mean(), max_size=int(22050 / 512 * 2.5))
    lo = int(22050 / 512 * 0.3)
    pulse = float(ac[lo:].max() / (ac[0] + 1e-9)) if len(ac) > lo else 0.0
    chroma = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=2048)
    cm = chroma.mean(1)
    centre = NOTES[int(cm.argmax())]
    k, mode, kc = key_of(cm)
    bass = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=2048, fmin=librosa.note_to_hz('A0'), n_octaves=2)
    bass_root = NOTES[int(bass.mean(1).argmax())]
    hop = 2 * sr
    st = []
    for i in range(0, len(x) - hop, hop):                 # short-term loudness, 3 s window every 2 s
        seg = x[i:i + int(1.5 * hop)]
        v = meter.integrated_loudness(seg) if len(seg) > sr else -70
        st.append(round(float(v) if np.isfinite(v) else -70.0, 1))
    cent = librosa.feature.spectral_centroid(y=y, sr=22050, hop_length=22050 * 2)[0]
    feats = librosa.feature.mfcc(y=y, sr=22050, hop_length=2048, n_mfcc=13)
    kk = max(3, min(10, int(len(y) / 22050 / 25)))
    bounds = librosa.frames_to_time(librosa.segment.agglomerative(np.vstack([feats, chroma]), kk), sr=22050,
                                    hop_length=2048)
    bounds = sorted(set([0.0] + [round(float(b), 1) for b in bounds]))
    dur = len(x) / sr
    stv = np.array(st) if st else np.array([-70.0])
    secs = []
    for a, b in zip(bounds, bounds[1:] + [dur]):
        i0, i1 = int(a / 2), max(int(a / 2) + 1, int(b / 2))
        L = stv[i0:i1]; C = np.asarray(cent[i0:i1])
        secs.append({'t0': round(a, 1), 't1': round(b, 1),
                     'lufs_st': round(float(np.median(L)), 1) if len(L) else None,
                     'centroid': int(np.median(C)) if len(C) else None})
    live = stv[stv > -60]
    return {'path': p, 'set': set_name, 'slug': slug, 'dur': round(dur, 2),
            'lufs': round(float(meter.integrated_loudness(x)), 1), 'tempo': round(tempo, 1),
            'pulse_clarity': round(pulse, 3), 'tonal_centre': centre, 'key': k, 'mode': mode, 'key_corr': kc,
            'bass_root': bass_root,
            'loud_p10_p50_p90': [round(float(np.percentile(live, q)), 1) for q in (10, 50, 90)] if len(live) else None,
            'centroid_median': int(np.median(cent)),
            'loudness_2s': st, 'centroid_2s': [int(c) for c in cent], 'sections': [b for b in bounds if b > 0],
            'section_stats': secs}


def build(sets, out, sfx_only=False):
    import pyloudnorm
    meter = pyloudnorm.Meter(SR)
    old = json.load(open(out)) if sfx_only and os.path.exists(out) else None
    cat = {'licence': "Epidemic Sound, through the channel owner's subscription. Keep the channel connected in the "
                      "Epidemic account to avoid Content ID claims. Do not redistribute, copy or commit the files.",
           'sets': {s: d for s, d in sets}, 'sfx': [], 'music': []}
    seen_slug, seen_fp = {}, {}
    for kind in ('sfx', 'music'):
        if kind == 'music' and old is not None:
            cat['music'] = old.get('music', [])
            continue
        for set_name, d in sets:
            sub = os.path.join(d, kind)
            if not os.path.isdir(sub):
                continue
            for f in sorted(os.listdir(sub)):
                if not f.lower().endswith('.wav'):
                    continue
                p = os.path.join(sub, f)
                slug = slugify(f[:-4])
                fp = _fingerprint(p)
                dup = seen_slug.get((kind, slug)) or seen_fp.get((kind, fp))
                if dup is not None:
                    dup.setdefault('also_in', []).append(set_name)
                    continue
                print(f'  {kind} {set_name}: {f}', flush=True)
                e = (sfx_entry if kind == 'sfx' else music_entry)(meter, p, set_name, slug)
                cat[kind].append(e)
                seen_slug[(kind, slug)] = e; seen_fp[(kind, fp)] = e
    tmp = out + '.tmp'
    json.dump(cat, open(tmp, 'w'), indent=1)
    os.replace(tmp, out)
    cov = sorted({s for e in cat['sfx'] for s in e['serves']})
    print(f"{len(cat['sfx'])} sfx, {len(cat['music'])} music; serves {len(cov)} names: {', '.join(cov)}")
    print('missing:', sorted(set(MAP) - set(cov)))
    print('unmapped:', [e['slug'] for e in cat['sfx'] if not e['serves']])
    for mu in cat['music']:
        print(f"{mu['set']:8s} {mu['slug'][:40]:40s} {mu['dur']:5.0f}s {mu['lufs']:6.1f} LUFS key {mu.get('key')} "
              f"{mu.get('mode')} ({mu.get('key_corr')}) bass {mu.get('bass_root')} centroid {mu.get('centroid_median')} "
              f"pulse {mu.get('pulse_clarity')}")
    return cat


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    so = '--sfx-only' in sys.argv
    if '--delivery' in sys.argv:
        build(DELIVERY_SETS, DELIVERY_OUT, so)
    elif args and '=' in args[-1]:
        build([tuple(a.split('=', 1)) for a in args[1:]], args[0], so)
    else:
        build([('police', args[0])], args[1], so)
