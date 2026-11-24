"""sfx_tests_walls.py: the Walls film's SFX test renders. Eight of this film's new sounds rendered as mix.py renders them
(sfx.render_event: recipe, space, level, the owner's edge fades) at their places in the script (music_plan anchors on
the timeline), written to W/mix/tests/<name>.wav (16-bit) with W/mix/tests/tests.json, then measured by the owner's
per-event check (audio/measure_mix.py --events: first / last 10 ms against the peak, momentary loudness against the
voice at that moment).

    python3 audio/sfx_tests_walls.py            (from film/)
"""
import json, os, sys
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX                                   # noqa: E402
import music_plan as MP                            # noqa: E402
import measure_mix as MM                           # noqa: E402

OUT = os.path.join(SX.W, 'mix', 'tests')
# (name, anchor: where the cue sits, params, space or None = the name's default)
TESTS = [
    ('deadbolt_slow', 'Click. -0.15', {'dur': 2.2}, None),                             # the click just before "Click."
    ('bread_bag', 'end:The bag, folded neatly, twisted shut again +0.1', {'kind': 'twist', 'dur': 1.4}, None),
    ('chewing', 'Inside the pantry wall -0.2', {'dur': 4.5}, None),
    ('wall_crawl', 'And then it was gone#crawling', {'dur': 3.0, 'speed': 1.3, 'travel': [-0.7, 0.8]}, None),
    ('snore', 'I heard my dad snore#snore +0.25', {'n': 1}, None),
    ('closet_slide', 'I heard the back wall of my closet slide#slide -0.5', {'action': 'open', 'speed': 0.9}, None),
    ('vent_rattle', 'Then the vent by the floor rattled#rattled -0.1', {'dur': 1.2}, None),
    ('wall_scratch', 'Scratching, inside the bedroom wall', {'dur': 3.5, 'travel': [-0.8, 0.2]}, None),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    lines, _ = MP.load_lines()
    rows = []
    for k, (name, anchor, params, space) in enumerate(TESTS):
        t = MP.resolve(anchor, lines)
        y, pre = SX.render_event(name, seed=k, space=space, **params)
        sf.write(os.path.join(OUT, name + '.wav'), np.clip(y, -1, 1), SX.SR, subtype='PCM_16')
        rows.append(dict(file=name + '.wav', label=name, t=round(t, 3), pre=round(pre, 3), anchor=anchor,
                         params=params, space=space or SX.DEFAULT_SPACE[name]))
    pj = os.path.join(OUT, 'tests.json')
    json.dump(rows, open(pj, 'w'), indent=1)
    MM.events_main(pj)


if __name__ == '__main__':
    main()
