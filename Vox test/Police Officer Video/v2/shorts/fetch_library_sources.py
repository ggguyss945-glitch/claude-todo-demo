"""Re-fetch the raw downloads that audio/build_library.py converts into the free sample library.

    python3 -I fetch_library_sources.py [--only SRC[,SRC]]     # download into $S/pov2/dl (see build_library.SOURCES)
    python3 -I ../audio/build_library.py --jobs 3               # convert to $S/pov2/samples, rewrite catalog.json
    python3 -I fetch_library_sources.py --clean                 # delete the raw downloads afterwards

GitHub sources: blobless depth-1 clones with an exact-file sparse checkout of only the files the ITEMS globs match and
catalog.json already lists (the previous build's subsets, so a restore reproduces the same library; an ITEMS entry with no
catalogued file fetches all its matches; --all-matches fetches everything the globs match), plus
each source's licence / readme / credit files (copied to samples/_licences, where build_library.credits_tables() reads
civitas_CREDITS.md, victor_CREDITS.md, sonicpi_samples_README.md and atomcut_packs.json). civitas and victor are raw single
files, copied flat to dl/raw/<src>/ as SOURCES expects. The OpenAIR rooms (openair2) come from the anidoodle sounds-v1 release tar,
checked against its index (whose sha256 is pinned in the repo's soundfetch.mjs) before unpacking with the safe tar filter.
"""
import argparse, glob, hashlib, json, os, re, shutil, subprocess, sys, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'audio'))
import build_library as B  # noqa: E402

DL, LIC = B.DL, B.LIC
GH = 'https://github.com/'
# source -> (clone dir under dl/, repository, path of the SOURCES root inside the repository)
GIT = {
    'vsco': ('vsco', 'sgossner/VSCO-2-CE', ''),
    'salamander': ('sfz_SalamanderGrandPiano', 'sfzinstruments/SalamanderGrandPiano', ''),
    'scarypiano': ('sfz_karoryfer.scarypiano', 'sfzinstruments/karoryfer.scarypiano', ''),
    'wartuba': ('sfz_karoryfer.war-tuba', 'sfzinstruments/karoryfer.war-tuba', ''),
    'bodyperc': ('sfz_body_percussion', 'sfzinstruments/body_percussion', ''),
    'dbass': ('sfz_dsmolken.double-bass', 'sfzinstruments/dsmolken.double-bass', ''),
    'celesta': ('celesta/r', 'Digital-Defiance/copyist-celesta', ''),
    'sonicpi': ('sonicpi', 'sonic-pi-net/sonic-pi', 'etc/samples'),
    'oculus': ('ir_probe/facebookincubator_Meta-open-sound', 'facebookincubator/Meta-open-sound', 'corpora/oculus-audio-pack/ogg'),
    'openair': ('ir_probe/usein-abilev_web-audio-fx', 'usein-abilev/web-audio-fx', 'static/impulse-responses'),
    'freesfx': ('Free-SFX', 'EternityForest/Free-SFX', ''),
    'atomcut': ('atomcut-library', 'novincode/atomcut-library', 'packs'),
    'kenney_rpg': ('sh', 'Nazarwadim/School-Hooligan', 'assets/kenney_rpgaudio/Audio'),
    'kenney_impact': ('lc', 'lunarcloud/ggj-2024-rail-shooter', 'addons/kenney impact sounds'),
    'kenney_ui': ('lc', 'lunarcloud/ggj-2024-rail-shooter', 'addons/kenney_interface_sounds'),
    'civitas': ('_git/civitas', 'reneodlt/civitas', 'packages/client/src/audio/files'),   # -> dl/raw/civitas
    'victor': ('_git/victor', 'victorrentea/victor-effects', 'starter-pack'),            # -> dl/raw/victor
}
# extra licence / credit files per source (repo path -> name in samples/_licences; None = <src>_<basename>)
EXTRA = {
    'sonicpi': {'etc/samples/README.md': 'sonicpi_samples_README.md'},
    'civitas': {'packages/client/src/audio/CREDITS.md': 'civitas_CREDITS.md', 'packages/client/src/audio/credits.json': None},
    'victor': {'starter-pack/CREDITS.md': 'victor_CREDITS.md'},
    'oculus': {'corpora/oculus-audio-pack/ATTRIBUTION.md': None, 'corpora/oculus-audio-pack/LICENSE': None,
               'corpora/oculus-audio-pack/README.md': None},
}
LIC_RE = re.compile(r'(licen[cs]e|readme|read me|credits?|attribution|copying)[^/]*$', re.I)
ALL_MATCHES = False  # --all-matches: every file the globs match, not only the catalogued ones
ANI_REPO, ANI_REL = 'alexgreensh/anidoodle', GH + 'alexgreensh/anidoodle/releases/download/sounds-v1/'


def run(cmd, cwd=None, inp=None):
    p = subprocess.run(cmd, cwd=cwd, input=inp, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f'{" ".join(cmd[:4])}: {p.stderr.strip()[:400]}')
    return p.stdout


def tree_clone(repo, dest):
    if not os.path.isdir(os.path.join(dest, '.git')):
        shutil.rmtree(dest, ignore_errors=True)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        run(['git', 'clone', '-q', '--filter=blob:none', '--no-checkout', '--depth', '1', GH + repo, dest])
    return [p for p in run(['git', '-C', dest, 'ls-tree', '-r', '-z', '--name-only', 'HEAD']).split('\0') if p]


def pat(path):  # exact, anchored gitignore-style pattern for one file
    return '/' + re.sub(r'([\\*?\[\]!# ])', r'\\\1', path)


_LISTED = None


def catalog_files(src):
    """Files of `src` (paths relative to its SOURCES root) that catalog.json lists, accepted or rejected."""
    global _LISTED
    if _LISTED is None:
        _LISTED = {}
        p = os.path.join(B.HERE, 'catalog.json')
        c = json.load(open(p)) if os.path.exists(p) and not ALL_MATCHES else {}
        for r in c.get('samples', []) + c.get('rejected', []):
            s = r.get('source')
            if s in B.SOURCES and r.get('orig', '').startswith(B.SOURCES[s]['root'] + '/'):
                _LISTED.setdefault(s, set()).add(r['orig'][len(B.SOURCES[s]['root']) + 1:])
    return _LISTED.get(src, set())


def wanted(src, files):
    """Repo paths matched by the ITEMS globs of `src` (same rules as build_library.expand) + licence files."""
    prefix = GIT[src][2]
    pre = (prefix + '/') if prefix else ''
    out, listed = set(), catalog_files(src)
    for it in B.ITEMS:
        if it[0] != src:
            continue
        rx = re.compile(glob.translate(glob.escape(pre) + it[1], recursive=True, include_hidden=False))
        m = {f for f in files if rx.match(f) and f.rsplit('.', 1)[-1].lower() in ('wav', 'flac', 'ogg', 'opus', 'm4a', 'mp3')}
        keep = {f for f in m if os.path.relpath(f, prefix or '.') in listed or os.path.basename(f) in listed}
        out |= keep or m  # the catalogued subset (same files as the last build); an item new since then: all matches
    lic = {}
    dirs = {'', prefix, os.path.dirname(prefix)}
    for f in files:
        if os.path.dirname(f) in dirs and LIC_RE.search(os.path.basename(f)):
            lic[f] = f'{src}_{os.path.basename(f)}'.replace(' ', '_')
    for f, name in EXTRA.get(src, {}).items():
        if f in files:
            lic[f] = name or f'{src}_{os.path.basename(f)}'.replace(' ', '_')
    if src == 'atomcut':  # one pack.json per pack used -> atomcut_packs.json
        for p in {f.split('/')[1] for f in out}:
            lic[f'packs/{p}/pack.json'] = None
    return out, lic


def fetch_git(srcs):
    by_dir = {}
    for s in srcs:
        by_dir.setdefault(GIT[s][0], []).append(s)
    for d, ss in by_dir.items():
        dest = os.path.join(DL, d)
        files = set(tree_clone(GIT[ss[0]][1], dest))
        need, lic = set(), {}
        for s in ss:
            n, l = wanted(s, files)
            need |= n
            lic.update({f: (s, name) for f, name in l.items()})
            print(f'{s}: {len(n)} audio files, {len(l)} licence/credit files', flush=True)
        run(['git', '-C', dest, 'sparse-checkout', 'set', '--no-cone', '--stdin'],
            inp='\n'.join(pat(f) for f in sorted(need | set(lic))) + '\n')
        run(['git', '-C', dest, 'checkout', '-q'])
        miss = [f for f in need | set(lic) if not os.path.isfile(os.path.join(dest, f))]
        if miss:
            raise RuntimeError(f'{d}: {len(miss)} files not checked out, e.g. {miss[:3]}')
        os.makedirs(LIC, exist_ok=True)
        packs = {}
        for f, (s, name) in lic.items():
            if s == 'atomcut' and f.endswith('/pack.json'):
                d_ = json.load(open(os.path.join(dest, f)))
                packs[f.split('/')[1]] = {k: d_.get(k) for k in ('id', 'title', 'license', 'attribution', 'publisher', 'homepage')}
            else:
                shutil.copyfile(os.path.join(dest, f), os.path.join(LIC, name))
        if packs:
            json.dump(packs, open(os.path.join(LIC, 'atomcut_packs.json'), 'w'), indent=1)
        for s in ss:
            root = os.path.join(DL, B.SOURCES[s]['root'])
            src_root = os.path.join(dest, GIT[s][2])
            if os.path.normpath(root) != os.path.normpath(src_root):  # civitas / victor: flat copy to dl/raw/<src>
                os.makedirs(root, exist_ok=True)
                for f in need:
                    if f.startswith(GIT[s][2] + '/'):
                        shutil.copyfile(os.path.join(dest, f), os.path.join(root, os.path.relpath(f, GIT[s][2])))
        if d.startswith('_git/'):
            shutil.rmtree(dest)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def fetch_openair2():
    work = os.path.join(DL, '_git', 'anidoodle')
    tree_clone(ANI_REPO, work)
    js = run(['git', '-C', work, 'show', 'HEAD:skills/anidoodle/engine/tools/soundfetch.mjs'])
    pin = re.search(r'INDEX_SHA256\s*=\s*"([0-9a-f]{64})"', js).group(1)
    idx = os.path.join(work, 'index.json')
    run(['curl', '-sSLf', '-o', idx, ANI_REL + 'anidoodle-sounds-v1.json'])
    if sha256(idx) != pin:
        raise RuntimeError('anidoodle index sha256 does not match the pinned value')
    ix = json.load(open(idx))
    arc = next(a for a in ix['archives'] if a['file'].endswith('-rooms.tar'))
    tar = os.path.join(work, arc['file'])
    run(['curl', '-sSLf', '-o', tar, ANI_REL + arc['file']])
    if os.path.getsize(tar) != arc['bytes'] or sha256(tar) != arc['sha256']:
        raise RuntimeError('rooms tar size/sha256 mismatch')
    dest = os.path.join(DL, 'rooms', 'x')
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    with tarfile.open(tar) as t:
        t.extractall(dest, filter='data')
    os.makedirs(LIC, exist_ok=True)
    open(os.path.join(LIC, 'openair2_LICENSES.md'), 'w').write(ix.get('licenses') or '')
    for f in glob.glob(os.path.join(dest, '**', '*'), recursive=True):
        if os.path.isfile(f) and LIC_RE.search(os.path.basename(f)):
            shutil.copyfile(f, os.path.join(LIC, 'openair2_' + os.path.basename(f)))
    n = len(glob.glob(os.path.join(DL, B.SOURCES['openair2']['root'], '*.flac')))
    print(f'openair2: {n} room IRs from {arc["file"]} (sha256 ok)', flush=True)
    shutil.rmtree(work)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--clean', action='store_true', help='delete the raw downloads (dl/) after build_library.py ran')
    ap.add_argument('--all-matches', action='store_true', help='fetch every file the ITEMS globs match, not only the '
                    'files catalog.json lists (the last build used chosen subsets, e.g. 4 of 16 Salamander layers)')
    a = ap.parse_args()
    global ALL_MATCHES
    ALL_MATCHES = a.all_matches
    if a.clean:
        shutil.rmtree(DL, ignore_errors=True)
        print('removed', DL)
        return
    only = [s for s in a.only.split(',') if s] or list(B.SOURCES)
    fetch_git([s for s in only if s in GIT])
    if 'openair2' in only:
        fetch_openair2()
    for s in only:
        n = len(glob.glob(os.path.join(glob.escape(os.path.join(DL, B.SOURCES[s]['root'])), '**', '*.*'), recursive=True))
        print(f'  {s:14s} {n:5d} files under dl/{B.SOURCES[s]["root"]}')


if __name__ == '__main__':
    main()
