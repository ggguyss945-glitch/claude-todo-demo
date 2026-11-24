"""beats.py: the script's "Tik." and "Ping." beats as SFX cues ("If Your Mom's Eyes Turn Into Buttons... DON'T KEEP
HER SECRET"). The voice edit removed them from the narrator (they are sounds); W/align/beats.json lists each one
({kind tik|ping, t = where the sound starts in narration_en.wav time, line = the timeline line it follows, tag}).

    load(path=None) -> list of beats
    cues(beats=None) -> sfx cue dicts {t, name, gain_db, pan, params, space, seed, src: 'beats'}: every tik a little
                        different (its own seed: the jar's pitch, the bounces, the rattle), the last two (the buttons
                        Mom drops in her jar) a hair apart in pan; pings from the tablet in Owen's hand
    merge(sfx_cues, beats=None, window=0.35) -> (new list, log): adds each beat the picture's sheet does not already
                        carry (a tik / ping cue of the same kind within `window` s of it wins: the picture's frame)
mix.py calls merge() on the picture's SFX sheet before mixing; film.py may also emit its own tik / ping cues at the
same beats (they win).

CLI: python3 audio/beats.py [--cues W/cues/sfx_cues.json]   prints the cues and what a merge would add
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
BEATS = os.path.join(W, 'align', 'beats.json')
# per-tag tweaks: (params, gain_db, pan)
TWEAK = {
    'loose_buttons_went': ({'kind': 'jar'}, 0.0, 0.25),      # the jar on the windowsill: introduced, clean
    'two_black_buttons': ({'kind': 'tap'}, -1.0, 0.0),      # buttons clicking onto the grey face (the tablet)
    'empty': ({'kind': 'jar'}, -1.0, 0.0),                   # the coat sagging empty in the closet
    'my_fingers_rose': ({'kind': 'jar'}, -2.0, 0.0),        # his fingers rising to the top button: small, close
}


def load(path=None):
    p = path or BEATS
    if not os.path.exists(p):
        return []
    return [b for b in json.load(open(p)).get('beats', []) if b.get('kind') in ('tik', 'ping')]


def cues(beats=None):
    bs = load() if beats is None else beats
    out = []
    for i, b in enumerate(bs):
        params, g, pn = TWEAK.get(b.get('tag'), ({'kind': 'jar'} if b['kind'] == 'tik' else {}, 0.0, 0.0))
        if b.get('tag') == 'she_dropped_them':               # two buttons into Mom's jar: Tik. Tik.
            pn = -0.1 if i % 2 else 0.1
        out.append({'t': round(float(b['t']), 3), 'name': b['kind'], 'gain_db': g, 'pan': pn, 'params': dict(params),
                    'space': 'close', 'seed': 700 + i, 'src': 'beats', 'tag': b.get('tag')})
    return out


def merge(sfx_cues, beats=None, window=0.35):
    """The picture's sheet + the beats it does not carry. Never fails: a bad sheet entry is left as it is."""
    sheet = list(sfx_cues) if isinstance(sfx_cues, list) else []
    have = {}
    for c in sheet:
        if isinstance(c, dict) and c.get('name') in ('tik', 'ping'):
            try:
                have.setdefault(c['name'], []).append(float(c['t']))
            except (KeyError, TypeError, ValueError):
                pass
    log, out = [], list(sheet)
    for c in cues(beats):
        near = [t for t in have.get(c['name'], []) if abs(t - c['t']) <= window]
        if near:
            log.append(f"beat {c['name']} {c['t']:.2f} ({c['tag']}): the picture's cue at {near[0]:.2f} wins")
            continue
        out.append(c)
        log.append(f"beat {c['name']} {c['t']:.2f} ({c['tag']}): added")
    return out, log


if __name__ == '__main__':
    cp = sys.argv[sys.argv.index('--cues') + 1] if '--cues' in sys.argv else os.path.join(W, 'cues', 'sfx_cues.json')
    sheet = json.load(open(cp)) if os.path.exists(cp) else []
    for c in cues():
        print(json.dumps(c))
    _, lg = merge(sheet)
    print('\n'.join(lg))
