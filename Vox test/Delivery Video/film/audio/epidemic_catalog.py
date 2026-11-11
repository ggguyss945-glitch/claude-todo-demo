"""Catalogue of the owner's Epidemic Sound downloads (licensed through the owner's subscription; never commit the audio).
    python3 epidemic_catalog.py <epidemic dir> <out catalog_epidemic.json>
Files are 48 kHz stereo WAVs in <dir>/sfx and <dir>/music. For every SFX: duration, integrated loudness, sample peak,
onset count and the required SFX names (ARCHITECTURE.md) it can serve. For every music track: duration, loudness, a
2-second short-term loudness curve, a brightness curve (spectral centroid), tempo, tonal centre, and section boundaries,
so the score can cut and layer tracks to the film's intensity curve.
"""
import json, os, sys
import numpy as np, soundfile as sf, librosa, pyloudnorm

SR = 48000
NOTES = 'C C# D D# E F F# G G# A A# B'.split()
# required SFX name -> filename keywords (all words must appear in the file slug)
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


def serves(slug):
    return sorted(k for k, alts in MAP.items() if any(all(w in slug for w in alt) for alt in alts))


def main(d, out):
    meter = pyloudnorm.Meter(SR)
    cat = {'licence': 'Epidemic Sound, through the channel owner\'s subscription. Keep the channel connected in the '
                      'Epidemic account to avoid Content ID claims. Do not redistribute or commit the files.',
           'sfx': [], 'music': []}
    for f in sorted(os.listdir(os.path.join(d, 'sfx'))):
        p = os.path.join(d, 'sfx', f); x, sr = sf.read(p, dtype='float32'); m = x.mean(1)
        lufs = meter.integrated_loudness(x) if len(x) > SR * 0.4 else None
        on = librosa.onset.onset_detect(y=librosa.resample(m, orig_sr=SR, target_sr=22050), sr=22050, units='time')
        slug = f[:-4]
        cat['sfx'].append({'path': p, 'slug': slug, 'serves': serves(slug), 'dur': round(len(x) / SR, 2),
                           'lufs': None if lufs is None or not np.isfinite(lufs) else round(float(lufs), 1),
                           'peak_db': round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1), 'onsets': len(on)})
    for f in sorted(os.listdir(os.path.join(d, 'music'))):
        p = os.path.join(d, 'music', f); x, sr = sf.read(p, dtype='float32'); m = x.mean(1)
        y = librosa.resample(m, orig_sr=SR, target_sr=22050)
        tempo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=22050)[0])[0])
        chroma = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=2048)
        key = NOTES[int(chroma.mean(1).argmax())]
        hop = 2 * SR; st = []
        for i in range(0, len(x) - hop, hop):                 # short-term loudness, 3 s window every 2 s
            seg = x[i:i + int(1.5 * hop)]
            v = meter.integrated_loudness(seg) if len(seg) > SR else -70
            st.append(round(float(v) if np.isfinite(v) else -70.0, 1))
        cent = librosa.feature.spectral_centroid(y=y, sr=22050, hop_length=22050 * 2)[0]
        feats = librosa.feature.mfcc(y=y, sr=22050, hop_length=2048, n_mfcc=13)
        k = max(3, min(10, int(len(y) / 22050 / 25)))
        bounds = librosa.frames_to_time(librosa.segment.agglomerative(np.vstack([feats, chroma]), k), sr=22050, hop_length=2048)
        cat['music'].append({'path': p, 'slug': f[:-4], 'dur': round(len(x) / SR, 2),
                             'lufs': round(float(meter.integrated_loudness(x)), 1), 'tempo': round(tempo, 1), 'tonal_centre': key,
                             'loudness_2s': st, 'centroid_2s': [int(c) for c in cent], 'sections': [round(float(b), 1) for b in bounds]})
    json.dump(cat, open(out, 'w'), indent=1)
    cov = sorted({s for e in cat['sfx'] for s in e['serves']})
    print(f"{len(cat['sfx'])} sfx, {len(cat['music'])} music; covers {len(cov)} required names: {', '.join(cov)}")
    print('unmapped:', [e['slug'] for e in cat['sfx'] if not e['serves']])
    for mu in cat['music']:
        print(f"{mu['slug']}: {mu['dur']:.0f}s {mu['lufs']} LUFS tempo {mu['tempo']} centre {mu['tonal_centre']} sections {mu['sections']}")


if __name__ == '__main__':
    main(*sys.argv[1:3])
