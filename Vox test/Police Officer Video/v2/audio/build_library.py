"""Build the free recorded sample library (CC0 / CC-BY only) and its catalogue.

    python3 -I build_library.py [--jobs 3] [--only SRC[,SRC]] [--no-epidemic]

Reads the raw downloads in $S/pov2/dl/ (git sparse checkouts of GitHub-hosted libraries, see SOURCES; deleted after
conversion, so a re-run reuses the QC cache in samples/_qc and the licence copies in samples/_licences; to restore
them, e.g. after an environment reset, run shorts/fetch_library_sources.py, then this, then that script with --clean),
and writes:
  - $S/pov2/samples/<category>/<src>__<name>.flac  48 kHz FLAC (24-bit for 24-bit/float sources, else 16-bit),
    source channel count kept (B-format and M-S impulse responses are decoded to L/R stereo).
  - v2/audio/catalog.json      every sample (free library + the owner's Epidemic files) with path, category, tags,
    `serves` (required SFX names, ARCHITECTURE.md), licence, source URL, attribution, duration, peak, LUFS, noise floor,
    sample rate, pitch (instruments) and QC flags; plus the `coverage` table.
  - v2/audio/ATTRIBUTION.md    credits text for the video description (every CC-BY item, plus courtesy CC0 credits).
QC on every file: it decodes; clipping (runs of >= 3 samples at full scale) and noise floor (5th percentile of 20 ms
RMS) are measured; one-shots and instrument notes are trimmed (leading silence with a 5 ms pre-roll, tail cut where
the envelope falls below max(peak-75 dB, floor+3 dB), short fades). Files with heavy clipping or no signal are rejected
and listed in catalog.json `rejected`. Epidemic files are measured but never rewritten.
Use audio/library.py to query and load the result.
"""
import argparse, glob, hashlib, io, json, math, os, re, subprocess, sys, time
from multiprocessing import Pool
import numpy as np, soundfile as sf, soxr

S = '/home/user/claude-todo-demo/Vox test/Police Officer Video/v2/_work'
DL = f'{S}/pov2/dl'
OUT = f'{S}/pov2/samples'
LIC = f'{OUT}/_licences'  # licence/credit files copied from each source at download time
HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000

# ----------------------------------------------------------------------------------------------------------- sources
OA = 'https://www.openair.hosted.york.ac.uk/?page_id='
SOURCES = {
    'vsco': dict(root='vsco', licence='CC0-1.0', url='https://github.com/sgossner/VSCO-2-CE',
                 title='VS Chamber Orchestra: Community Edition', author='Versilian Studios (Sam Gossner, Simon Dalzell, Elan Hickler)'),
    'salamander': dict(root='sfz_SalamanderGrandPiano', licence='CC-BY-3.0', url='https://github.com/sfzinstruments/SalamanderGrandPiano',
                       title='Salamander Grand Piano V3', author='Alexander Holm'),
    'scarypiano': dict(root='sfz_karoryfer.scarypiano', licence='CC0-1.0', url='https://github.com/sfzinstruments/karoryfer.scarypiano',
                       title='Scary Piano', author='Karoryfer Samples'),
    'wartuba': dict(root='sfz_karoryfer.war-tuba', licence='CC0-1.0', url='https://github.com/sfzinstruments/karoryfer.war-tuba',
                    title='War Tuba', author='Karoryfer Samples'),
    'bodyperc': dict(root='sfz_body_percussion', licence='CC0-1.0', url='https://github.com/sfzinstruments/body_percussion',
                     title='Body Percussion', author='sfzinstruments'),
    'dbass': dict(root='sfz_dsmolken.double-bass', licence='CC0-1.0', url='https://github.com/sfzinstruments/dsmolken.double-bass',
                  title='Double Bass (noises)', author='D. Smolken'),
    'celesta': dict(root='celesta/r', licence='CC0-1.0', url='https://github.com/Digital-Defiance/copyist-celesta',
                    upstream='https://gitlab.com/Nbickford/a-sampled-celesta', title='A Sampled Celesta', author='Neil Bickford'),
    'sonicpi': dict(root='sonicpi/etc/samples', licence='CC0-1.0', url='https://github.com/sonic-pi-net/sonic-pi/tree/main/etc/samples',
                    title='Sonic Pi bundled samples', author='Freesound contributors / The Black Dog (see Sonic Pi samples README)'),
    'oculus': dict(root='ir_probe/facebookincubator_Meta-open-sound/corpora/oculus-audio-pack/ogg', licence='CC-BY-4.0',
                   url='https://github.com/facebookincubator/Meta-open-sound/tree/main/corpora/oculus-audio-pack',
                   upstream='https://developers.meta.com/vr/downloads/package/oculus-audio-pack-1/', title='Oculus Audio Pack 01',
                   author='Oculus VR, LLC', lossy=True,
                   attribution='"Oculus Audio Pack 01" by Oculus VR, LLC (https://developers.meta.com/vr/downloads/package/oculus-audio-pack-1/), licensed under CC BY 4.0.'),
    'openair': dict(root='ir_probe/usein-abilev_web-audio-fx/static/impulse-responses', licence='CC-BY-4.0',
                    url='https://github.com/usein-abilev/web-audio-fx/tree/main/static/impulse-responses',
                    title='OpenAIR impulse responses', author='OpenAIR, Audiolab, University of York'),
    'openair2': dict(root='rooms/x/rooms', licence='CC-BY-4.0', url='https://github.com/alexgreensh/anidoodle (release anidoodle-sounds-v1, rooms)',
                     title='OpenAIR impulse responses', author='OpenAIR, Audiolab, University of York'),
    'freesfx': dict(root='Free-SFX', licence='CC0-1.0', url='https://github.com/EternityForest/Free-SFX', lossy=True,
                    title='Free-SFX (public domain collection)', author='various (OpenGameArt / Freesound CC0 uploads)'),
    'atomcut': dict(root='atomcut-library/packs', licence='CC0-1.0', url='https://github.com/novincode/atomcut-library', lossy=True,
                    title='AtomCut library (OpenGameArt / Kenney CC0 packs)', author='various'),
    'kenney_rpg': dict(root='sh/assets/kenney_rpgaudio/Audio', licence='CC0-1.0', url='https://kenney.nl/assets/rpg-audio', lossy=True,
                       title='Kenney RPG Audio', author='Kenney (kenney.nl)'),
    'kenney_impact': dict(root='lc/addons/kenney impact sounds', licence='CC0-1.0', url='https://kenney.nl/assets/impact-sounds', lossy=True,
                          title='Kenney Impact Sounds', author='Kenney (kenney.nl)'),
    'kenney_ui': dict(root='lc/addons/kenney_interface_sounds', licence='CC0-1.0', url='https://kenney.nl/assets/interface-sounds',
                      title='Kenney Interface Sounds', author='Kenney (kenney.nl)'),
    'civitas': dict(root='raw/civitas', licence='CC0-1.0', url='https://github.com/reneodlt/civitas/tree/main/packages/client/src/audio',
                    title='civitas recordings (Freesound CC0)', author='Freesound contributors', lossy=True),
    'victor': dict(root='raw/victor', licence='CC0-1.0', url='https://github.com/victorrentea/victor-effects/tree/main/starter-pack',
                   title='victor-effects starter pack (Freesound CC0)', author='Freesound contributors', lossy=True),
}
OPENAIR_ROOMS = {  # file stem -> (room, page id, credit)
    '1st_baptist_nashville_balcony': ('1st Baptist Church Nashville', 406, 'Adam Townsell'),
    '1st_baptist_nashville_far_close': ('1st Baptist Church Nashville', 406, 'Adam Townsell'),
    'ir_centre_stalls': ('Central Hall, University of York', 435, 'Alexander Vilkaitis, Ilias Antonopoulos, Joska De Langen, Xuan Liu'),
    'ir_row_3l_centre_mid': ('Central Hall, University of York', 435, 'Alexander Vilkaitis, Ilias Antonopoulos, Joska De Langen, Xuan Liu'),
    'S1R1_MS': ('Abies Grandis Forest, Wheldrake Wood', 1293, 'www.openairlib.net'),
    'S2R2_MS': ('Abies Grandis Forest, Wheldrake Wood', 1293, 'www.openairlib.net'),
    'r1_ortf-48k': ('R1 Nuclear Reactor Hall, Stockholm', 626, 'Audiolab (University of York), Dr. Damian T. Murphy'),
    'small-room': ('Arthur Sykes Rymer Auditorium, University of York', 425, 'www.openairlib.net'),
    'recital-hall': ('Jack Lyons Concert Hall, University of York', 571, 'www.openairlib.net'),
    'live-room': ('Genesis 6 Studio live room, University of York', 483, 'www.openairlib.net'),
}

# ------------------------------------------------------------------------------------------------------------- items
# (src, glob relative to the source root, category, tags, policy, serves, opts)
# policy: oneshot | loop (no trim) | inst (instrument note: trim + pitch) | ir (impulse response)
V = 'vsco'
ST = 'score/strings/'
ITEMS = [
    (V, 'Strings/Violin Section/susVib/*.wav', ST + 'violins_sustain', ['violins', 'ensemble', 'sustain', 'vibrato'], 'inst', [], {}),
    (V, 'Strings/Violin Section/Trem/*.wav', ST + 'violins_tremolo', ['violins', 'ensemble', 'tremolo'], 'inst', [], {}),
    (V, 'Strings/Violin Section/Pizz/*.wav', ST + 'violins_pizz', ['violins', 'ensemble', 'pizzicato'], 'inst', [], {}),
    (V, 'Strings/Viola Section/susvib/*.wav', ST + 'violas_sustain', ['violas', 'ensemble', 'sustain', 'vibrato'], 'inst', [], {}),
    (V, 'Strings/Viola Section/trem/*.wav', ST + 'violas_tremolo', ['violas', 'ensemble', 'tremolo'], 'inst', [], {}),
    (V, 'Strings/Cello Section/susvib/*.wav', ST + 'celli_sustain', ['celli', 'ensemble', 'sustain', 'vibrato'], 'inst', [], {}),
    (V, 'Strings/Cello Section/trem/*.wav', ST + 'celli_tremolo', ['celli', 'ensemble', 'tremolo'], 'inst', [], {}),
    (V, 'Strings/Cello Section/pizzT/*.wav', ST + 'celli_pizz', ['celli', 'ensemble', 'pizzicato'], 'inst', [], {}),
    (V, 'Strings/Solo Contrabass/SusNV/*.wav', ST + 'contrabass_sustain', ['contrabass', 'solo', 'sustain', 'non-vibrato'], 'inst', [], {}),
    (V, 'Strings/Solo Contrabass/Trem/*.wav', ST + 'contrabass_tremolo', ['contrabass', 'solo', 'tremolo'], 'inst', [], {}),
    (V, 'Strings/Solo Contrabass/Pizz/*.wav', ST + 'contrabass_pizz', ['contrabass', 'solo', 'pizzicato', 'pulse'], 'inst', [], {}),
    (V, 'Strings/Solo Violin/Arco Vib/*.wav', ST + 'solo_violin_sustain', ['violin', 'solo', 'sustain', 'vibrato'], 'inst', [], {}),
    (V, 'Strings/Solo Violin/Trem/*.wav', ST + 'solo_violin_tremolo', ['violin', 'solo', 'tremolo'], 'inst', [], {}),
    (V, 'Strings/Violin Section/Spic/*.wav', ST + 'violins_spiccato', ['violins', 'ensemble', 'spiccato', 'ostinato', 'pulse'], 'inst', [], {}),
    (V, 'Strings/Viola Section/spic/*.wav', ST + 'violas_spiccato', ['violas', 'ensemble', 'spiccato', 'ostinato', 'pulse'], 'inst', [], {}),
    (V, 'Strings/Viola Section/pizz/*.wav', ST + 'violas_pizz', ['violas', 'ensemble', 'pizzicato'], 'inst', [], {}),
    (V, 'Strings/Cello Section/spic/*.wav', ST + 'celli_spiccato', ['celli', 'ensemble', 'spiccato', 'ostinato', 'pulse'], 'inst', [], {}),
    (V, 'Strings/Solo Contrabass/Spic/*.wav', ST + 'contrabass_spiccato', ['contrabass', 'solo', 'spiccato', 'pulse'], 'inst', [], {}),
    (V, 'Strings/Solo Violin/spic/*.wav', ST + 'solo_violin_spiccato', ['violin', 'solo', 'spiccato'], 'inst', [], {}),
    (V, 'Strings/Solo Violin/Pizz/*.wav', ST + 'solo_violin_pizz', ['violin', 'solo', 'pizzicato'], 'inst', [], {}),
    (V, 'Percussion/Timpani/Rolls/*.wav', 'score/percussion/timpani', ['timpani', 'roll', 'swell'], 'inst', ['riser'], {'nopitch': 1}),
    (V, 'Strings/Harp/*.wav', 'score/harp', ['harp', 'plucked'], 'inst', [], {}),
    (V, 'Keys/Upright Piano/*.wav', 'score/piano/upright_vsco', ['piano', 'upright'], 'inst', [], {'piano_map': 1}),
    (V, 'Keys/Organ/Quiet/*.wav', 'score/organ', ['organ', 'pipe', 'quiet', 'drone'], 'inst', [], {'f0': 1}),
    (V, 'Percussion/Glock/*.wav', 'score/mallets/glockenspiel', ['glockenspiel', 'mallet', 'music_box_layer'], 'inst', [], {}),
    (V, 'Percussion/Timpani/*.wav', 'score/percussion/timpani', ['timpani', 'hit', 'pulse'], 'inst', ['impact_hit'], {'nopitch': 1}),
    (V, 'Percussion/Timpani*.wav', 'score/percussion/timpani', ['timpani', 'roll'], 'inst', [], {'nopitch': 1}),
    (V, 'Percussion/BDrumNewhit*.wav', 'score/percussion/bass_drum', ['bass_drum', 'hit', 'pulse'], 'oneshot', ['impact_hit'], {}),
    (V, 'Percussion/bassdrum*.wav', 'score/percussion/bass_drum', ['bass_drum', 'rub', 'roll'], 'oneshot', [], {}),
    (V, 'Percussion/gong*.wav', 'score/percussion/gong_tamtam', ['gong', 'tam-tam', 'hit', 'scrape'], 'oneshot', ['impact_hit', 'stinger'], {}),
    (V, 'Percussion/susCymb1-*.wav', 'score/percussion/cymbals', ['suspended_cymbal', 'bowed', 'crescendo', 'scrape'], 'oneshot', ['riser'], {}),
    (V, 'Percussion/cymbal-crash1*.wav', 'score/percussion/cymbals', ['crash_cymbal', 'hit'], 'oneshot', ['impact_hit'], {}),
    (V, 'Percussion/vibraring*.wav', 'score/percussion/metals', ['vibraphone', 'ring'], 'oneshot', [], {}),
    (V, 'Percussion/Anvil*.wav', 'score/percussion/metals', ['anvil', 'hit'], 'oneshot', ['impact_hit'], {}),
    (V, 'Percussion/BrakeDrum*.wav', 'score/percussion/metals', ['brake_drum', 'hit', 'bowed'], 'oneshot', [], {}),
    (V, 'Percussion/Ratchet*.wav', 'score/percussion/metals', ['ratchet'], 'oneshot', [], {}),
    (V, 'Percussion/alien*.wav', 'sfx/design', ['weird', 'alien', 'texture'], 'oneshot', ['stinger'], {}),
    (V, 'Percussion/zap*.wav', 'sfx/design', ['zap', 'texture'], 'oneshot', ['glitch'], {}),
    (V, 'VSCO 1 Percussion/varMetal/**/*.wav', 'score/percussion/bowed_metals', ['metal', 'gong', 'flexatone', 'bell_tree', 'cymbal'], 'oneshot', ['stinger'], {}),
    (V, 'Miscellania Raw/Misc 1/*.wav', 'sfx/design/vsco_misc', ['foley', 'texture', 'chain', 'scrape'], 'oneshot', [], {}),
    (V, 'Miscellania Raw/Misc 2/glock_glisses/*.wav', 'score/mallets/glock_glisses', ['glockenspiel', 'gliss'], 'oneshot', [], {}),
    (V, 'Miscellania Raw/Misc 2/NepaleseBells/*.wav', 'score/mallets/nepalese_bells', ['bells', 'hand_bells'], 'oneshot', [], {}),
    (V, 'Brass/F Horn/sus/*.wav', 'score/brass/horn_sustain', ['horn', 'sustain', 'braam_layer'], 'inst', ['braam'], {}),
    (V, 'Brass/F Horn/mute/*.wav', 'score/brass/horn_muted', ['horn', 'muted', 'sustain'], 'inst', [], {}),
    (V, 'Brass/Tenor Trombone/sus/*.wav', 'score/brass/trombone_sustain', ['trombone', 'sustain', 'braam_layer'], 'inst', ['braam'], {}),
    (V, 'Brass/Tuba/sus/*.wav', 'score/brass/tuba_sustain', ['tuba', 'sustain', 'braam_layer'], 'inst', ['braam'], {}),
    ('salamander', 'Samples/[A-G]*.flac', 'score/piano/grand_salamander', ['piano', 'grand'], 'inst', [], {}),
    ('salamander', 'Samples/harmL*.flac', 'score/piano/grand_salamander_resonance', ['piano', 'grand', 'string_resonance'], 'inst', [], {'strip': 'harmL'}),
    ('scarypiano', 'Samples/horror/piano soft/*.wav', 'score/piano/horror_soft', ['piano', 'horror', 'detuned', 'soft'], 'inst', [], {}),
    ('scarypiano', 'Samples/horror/piano loud/*.wav', 'score/piano/horror_loud', ['piano', 'horror', 'detuned', 'loud'], 'inst', ['stinger'], {}),
    ('scarypiano', 'Samples/horror/alt loud/*.wav', 'score/piano/horror_alt', ['piano', 'horror', 'detuned', 'loud'], 'inst', ['stinger'], {}),
    ('wartuba', 'Samples/*_s_*.wav', 'score/brass/war_tuba', ['tuba', 'staccato', 'low'], 'inst', [], {}),
    ('wartuba', 'Samples/woo_*.wav', 'score/brass/war_tuba_fx', ['tuba', 'fx', 'woo'], 'oneshot', [], {}),
    ('wartuba', 'Samples/breath_*.wav', 'sfx/vocal', ['breath', 'tuba_breath'], 'oneshot', [], {}),
    ('bodyperc', 'Samples/**/chestthump*.wav', 'score/percussion/body', ['body', 'chest', 'thump', 'heartbeat_layer'], 'oneshot', ['heartbeat'], {}),
    ('bodyperc', 'Samples/**/*.wav', 'score/percussion/body', ['body', 'percussion', 'clap', 'stomp', 'slap'], 'oneshot', [], {}),
    ('dbass', 'arco/noises/*.wav', 'sfx/creaks_scrapes', ['double_bass', 'creak', 'scrape', 'bow_noise'], 'oneshot', ['door_creak'], {}),
    ('dbass', 'pizz/noises/*.wav', 'sfx/creaks_scrapes', ['double_bass', 'knock', 'slap', 'string_noise'], 'oneshot', [], {}),
    ('celesta', 'samples/*.wav', 'score/mallets/celesta', ['celesta', 'mallet', 'music_box_layer'], 'inst', [], {'midi_prefix': 1}),
    ('sonicpi', 'ambi_*.flac', 'score/drones_pads', ['drone', 'ambient', 'pad'], 'loop', [], {}),
    ('sonicpi', 'tbd_*.flac', 'score/drones_pads', ['pad', 'texture'], 'loop', [], {}),
    ('sonicpi', 'glitch_*.flac', 'sfx/glitch', ['glitch', 'digital'], 'oneshot', ['glitch'], {}),
    ('sonicpi', 'mehackit_robot*.flac', 'sfx/glitch', ['glitch', 'robot', 'digital'], 'oneshot', ['glitch'], {}),
    ('sonicpi', 'vinyl_*.flac', 'sfx/glitch', ['vinyl', 'tape', 'rewind', 'hiss'], 'oneshot', ['glitch'], {}),
    ('sonicpi', 'elec_*.flac', 'sfx/ticks_blips', ['electronic', 'tick', 'blip'], 'oneshot', ['countdown_tick'], {}),
    ('sonicpi', 'mehackit_phone*.flac', 'sfx/phone', ['phone', 'electronic'], 'oneshot', [], {}),
    ('sonicpi', 'misc_cineboom.flac', 'sfx/impacts', ['boom', 'cinematic'], 'oneshot', ['impact_hit', 'sub_drop'], {}),
    ('sonicpi', 'bass_drop_c.flac', 'sfx/impacts', ['sub', 'drop'], 'oneshot', ['sub_drop'], {}),
    ('sonicpi', 'perc_impact*.flac', 'sfx/impacts', ['impact'], 'oneshot', ['impact_hit'], {}),
    ('sonicpi', 'perc_door.flac', 'sfx/foley/doors', ['door'], 'oneshot', [], {}),
    ('sonicpi', 'misc_crow.flac', 'sfx/ambience', ['crow', 'bird'], 'oneshot', ['ambience_night'], {}),
    ('oculus', 'AMBHome_RoomTone*.ogg', 'sfx/room_tone', ['room_tone', 'home', 'interior'], 'loop', ['room_tone'], {}),
    ('oculus', 'AMBInd_*.ogg', 'sfx/room_tone', ['room_tone', 'machine_room'], 'loop', ['room_tone'], {}),
    ('oculus', 'MACH*.ogg', 'sfx/room_tone', ['hum', 'fan', 'hvac', 'appliance'], 'auto', ['room_tone'], {}),
    ('oculus', 'CLOCK*.ogg', 'sfx/clock_tick', ['clock', 'tick', 'creepy'], 'oneshot', ['clock_tick', 'countdown_tick'], {}),
    ('oculus', 'CRWD*.ogg', 'sfx/crowd_whisper', ['crowd', 'murmur', 'restaurant', 'walla'], 'loop', ['crowd_whisper'], {}),
    ('oculus', 'AMBForst_Night*.ogg', 'sfx/ambience', ['night', 'forest', 'crickets'], 'loop', ['ambience_night'], {}),
    ('oculus', 'DOORWood_*.ogg', 'sfx/foley/doors', ['door', 'wood', 'open', 'close'], 'oneshot', ['door_creak'], {}),
    ('oculus', 'DOORHdwr_FrontDoor*.ogg', 'sfx/foley/locks', ['door', 'knob', 'lock'], 'oneshot', ['lock_turn'], {}),
    ('oculus', 'DOORKnck_*.ogg', 'sfx/foley/doors', ['knock', 'door'], 'oneshot', ['knock_door'], {}),
    ('oculus', 'DSGNDron_*.ogg', 'score/drones_pads', ['drone', 'creepy'], 'auto', [], {}),
    ('oculus', 'DSGNImpt_*.ogg', 'sfx/impacts', ['impact', 'creepy', 'reverb'], 'oneshot', ['impact_hit', 'stinger'], {}),
    ('oculus', 'MUSCKeyd_*.ogg', 'score/stingers', ['organ', 'creepy', 'sting'], 'oneshot', ['stinger'], {}),
    ('oculus', 'MUSCStr_*.ogg', 'score/stingers', ['strings', 'creepy', 'sting'], 'oneshot', ['stinger'], {}),
    ('oculus', 'MUSCChim_*.ogg', 'sfx/ambience', ['wind_chimes'], 'loop', ['ambience_night'], {}),
    ('oculus', 'VOX*.ogg', 'sfx/vocal', ['voice', 'creepy', 'groan', 'laugh'], 'oneshot', [], {}),
    ('oculus', 'HMNBrth_*.ogg', 'sfx/vocal', ['breath', 'breathing'], 'oneshot', ['breath'], {}),
    ('oculus', 'FEETHmn_ShoeWood*.ogg', 'sfx/footsteps', ['footsteps', 'shoe', 'wood'], 'oneshot', ['footsteps_wood_inside', 'footsteps_porch'], {}),
    ('oculus', 'FEETHmn_ShoeConcrete*.ogg', 'sfx/footsteps', ['footsteps', 'shoe', 'concrete'], 'oneshot', ['footsteps_porch'], {}),
    ('oculus', 'FEETHmn_ShoeDirt*.ogg', 'sfx/footsteps', ['footsteps', 'shoe', 'dirt', 'gravel'], 'oneshot', [], {}),
    ('oculus', 'MECHSwtch_*.ogg', 'sfx/clicks', ['switch', 'click', 'small'], 'oneshot', ['pen_click', 'tv_off', 'radio_click'], {}),
    ('oculus', 'MECHLock_*.ogg', 'sfx/foley/locks', ['key', 'lock', 'unlock'], 'oneshot', ['key_in_lock', 'lock_turn'], {}),
    ('oculus', 'PLASImpt_*.ogg', 'sfx/phone_pickup', ['plastic', 'handling', 'drop'], 'oneshot', ['phone_pickup'], {}),
    ('oculus', 'PAPR*.ogg', 'sfx/foley/paper', ['paper', 'crumple', 'tear'], 'oneshot', ['paper'], {}),
    ('openair', '1st-baptist-nashville/*.wav', 'ir', ['ir', 'church', 'large'], 'ir', [], {}),
    ('openair', 'central-hall-university-york/*.wav', 'ir', ['ir', 'hall', 'medium'], 'ir', [], {'bformat': 1}),
    ('openair', 'forest-in-wheldrakewood/*_MS.wav', 'ir', ['ir', 'outdoor', 'forest'], 'ir', [], {'ms': 1}),
    ('openair', 'r1-nuclear-reactor-hall/stereo/r1_ortf-48k.wav', 'ir', ['ir', 'huge', 'concrete', 'eerie'], 'ir', [], {}),
    ('openair2', '*.flac', 'ir', ['ir', 'room'], 'ir', [], {}),
    ('freesfx', 'Owlish/Sound Effects Pack/Ambience/loopable-ticking-clock.opus', 'sfx/clock_tick', ['clock', 'tick', 'loop'], 'loop', ['clock_tick'], {}),
    ('freesfx', 'Owlish/Sound Effects Pack/Ambience/night-crickets*.opus', 'sfx/ambience', ['night', 'crickets', 'rural'], 'loop', ['ambience_night'], {}),
    ('freesfx', 'Freesound/Mechanical/*stopwatch*.opus', 'sfx/countdown_tick', ['stopwatch', 'tick'], 'loop', ['countdown_tick', 'clock_tick'], {}),
    ('freesfx', 'Owlish/Sound Effects Pack/Human/*.opus', 'sfx/vocal', ['human', 'breath', 'gasp', 'shh'], 'oneshot', ['breath'], {}),
    ('freesfx', 'qubodup/Dummy/*Whipser*.opus', 'sfx/crowd_whisper', ['whisper', 'voice'], 'oneshot', ['crowd_whisper'], {}),
    ('freesfx', 'qubodup/Ghost Moans/*.opus', 'sfx/vocal', ['ghost', 'moan', 'creepy'], 'oneshot', [], {}),
    ('freesfx', 'Owlish/Sound Effects Pack/Technology/*.opus', 'sfx/phone', ['phone', 'technology', 'click', 'vibrate'], 'oneshot', ['phone_vibrate'], {}),
    ('freesfx', 'Owlish/Sound Effects Pack/Paper/*.opus', 'sfx/foley/paper', ['paper', 'pencil', 'page'], 'oneshot', ['paper'], {}),
    ('freesfx', 'Owlish/Sound Effects Pack/Footsteps/*.opus', 'sfx/footsteps', ['footsteps', 'hard', 'heel'], 'oneshot', ['footsteps_wood_inside'], {}),
    ('freesfx', 'Owlish/Sound Effects Pack/Cloth, Rustle/*.opus', 'sfx/foley/cloth', ['cloth', 'rustle', 'zipper'], 'oneshot', [], {}),
    ('freesfx', 'Electricity/*.opus', 'sfx/tv_off', ['electricity', 'powerdown', 'crackle', 'hum'], 'auto', ['tv_off'], {}),
    ('freesfx', 'Freesound/Stings/*.opus', 'score/stingers', ['horror', 'sting'], 'oneshot', ['stinger'], {}),
    ('freesfx', 'Freesound/Misc/*.opus', 'score/percussion/cymbals', ['cymbal', 'swell'], 'oneshot', ['riser'], {}),
    ('freesfx', 'Freesound/Animals/*critters*.opus', 'sfx/ambience', ['critters', 'creeping'], 'loop', [], {}),
    ('freesfx', 'Freesound/Animals/*owl*.opus', 'sfx/ambience', ['owl', 'night'], 'oneshot', ['ambience_night'], {}),
    ('freesfx', 'LokiF/Swamp/cricket*', 'sfx/ambience', ['crickets', 'night'], 'loop', ['ambience_night'], {}),
    ('atomcut', 'opengameart-keyboard-soundpack-1-typing-and-single-keystrokes/audio/*.m4a', 'sfx/typing', ['keyboard', 'typing', 'keystroke'], 'oneshot', ['typing'], {}),
    ('atomcut', 'opengameart-87-clickety-clips/audio/*.m4a', 'sfx/clicks', ['click', 'clip', 'mechanical'], 'oneshot', ['pen_click', 'radio_click'], {}),
    ('atomcut', 'opengameart-dialog-vocal-samples/audio/whisper*.m4a', 'sfx/crowd_whisper', ['whisper', 'voice', 'gibberish'], 'oneshot', ['crowd_whisper'], {}),
    ('atomcut', 'opengameart-dialog-vocal-samples/audio/demon*.m4a', 'sfx/vocal', ['demon', 'voice', 'gibberish'], 'oneshot', [], {}),
    ('atomcut', 'opengameart-door-open-door-close-set/audio/*.m4a', 'sfx/door_creak', ['door', 'creak', 'open', 'close'], 'oneshot', ['door_creak'], {}),
    ('atomcut', 'opengameart-door-open-door-close/audio/*.m4a', 'sfx/door_creak', ['door', 'creak', 'open', 'close'], 'oneshot', ['door_creak'], {}),
    ('atomcut', 'opengameart-100-cc0-metal-and-wood-sfx/audio/wood-squeak*.m4a', 'sfx/door_creak', ['wood', 'squeak', 'creak'], 'oneshot', ['door_creak'], {}),
    ('atomcut', 'opengameart-100-cc0-metal-and-wood-sfx/audio/door-open*.m4a', 'sfx/door_creak', ['door', 'open'], 'oneshot', ['door_creak'], {}),
    ('atomcut', 'opengameart-100-cc0-metal-and-wood-sfx/audio/keys*.m4a', 'sfx/foley/locks', ['keys', 'jingle'], 'oneshot', ['key_in_lock'], {}),
    ('atomcut', 'opengameart-100-cc0-metal-and-wood-sfx/audio/lock-open*.m4a', 'sfx/foley/locks', ['lock', 'open'], 'oneshot', ['lock_turn'], {}),
    ('atomcut', 'opengameart-100-cc0-metal-and-wood-sfx/audio/wood-cracking*.m4a', 'sfx/creaks_scrapes', ['wood', 'crack', 'creak'], 'oneshot', ['door_creak'], {}),
    ('atomcut', 'opengameart-30-weird-cc0-sfx/audio/*.m4a', 'sfx/design', ['weird', 'texture'], 'oneshot', ['glitch'], {}),
    ('atomcut', 'kenney-sci-fi-sounds/audio/computer-noise*.m4a', 'sfx/glitch', ['computer', 'noise', 'digital'], 'oneshot', ['glitch'], {}),
    ('atomcut', 'kenney-sci-fi-sounds/audio/force-field*.m4a', 'sfx/tv_off', ['hum', 'electric', 'force_field'], 'oneshot', ['tv_off'], {}),
    ('atomcut', 'kenney-ui-audio/audio/*.m4a', 'sfx/clicks', ['click', 'switch', 'ui'], 'oneshot', ['pen_click', 'radio_click', 'ui_pop'], {}),
    ('kenney_ui', 'glitch_*.wav', 'sfx/glitch', ['glitch', 'digital', 'ui'], 'oneshot', ['glitch'], {}),
    ('kenney_ui', 'tick_*.wav', 'sfx/countdown_tick', ['tick', 'ui'], 'oneshot', ['countdown_tick', 'clock_tick'], {}),
    ('kenney_ui', 'click_*.wav', 'sfx/clicks', ['click', 'ui'], 'oneshot', ['pen_click', 'ui_pop'], {}),
    ('kenney_ui', 'switch_*.wav', 'sfx/clicks', ['switch', 'ui'], 'oneshot', ['pen_click', 'tv_off'], {}),
    ('kenney_impact', 'footstep_wood*.ogg', 'sfx/footsteps', ['footsteps', 'wood'], 'oneshot', ['footsteps_wood_inside', 'footsteps_porch'], {}),
    ('kenney_impact', 'footstep_concrete*.ogg', 'sfx/footsteps', ['footsteps', 'concrete'], 'oneshot', ['footsteps_porch'], {}),
    ('kenney_impact', 'footstep_carpet*.ogg', 'sfx/footsteps', ['footsteps', 'carpet'], 'oneshot', ['footsteps_wood_inside'], {}),
    ('kenney_impact', 'impact_wood*.ogg', 'sfx/impacts', ['impact', 'wood'], 'oneshot', ['knock_door'], {}),
    ('kenney_impact', 'impact_plank*.ogg', 'sfx/impacts', ['impact', 'plank'], 'oneshot', ['knock_door'], {}),
    ('kenney_impact', 'impact_soft*.ogg', 'sfx/impacts', ['impact', 'soft', 'body'], 'oneshot', [], {}),
    ('kenney_rpg', 'creak*.ogg', 'sfx/door_creak', ['creak', 'wood', 'door'], 'oneshot', ['door_creak'], {}),
    ('kenney_rpg', 'door*.ogg', 'sfx/foley/doors', ['door', 'open', 'close'], 'oneshot', ['door_creak'], {}),
    ('kenney_rpg', 'metal*.ogg', 'sfx/foley/locks', ['metal', 'click', 'latch'], 'oneshot', ['lock_turn', 'pen_click'], {}),
    ('kenney_rpg', 'book*.ogg', 'sfx/foley/paper', ['book', 'page'], 'oneshot', ['paper'], {}),
    ('kenney_rpg', 'cloth*.ogg', 'sfx/foley/cloth', ['cloth'], 'oneshot', [], {}),
    ('civitas', 'crowd*.opus', 'sfx/crowd_whisper', ['crowd', 'murmur', 'indoor'], 'loop', ['crowd_whisper'], {}),
    ('civitas', 'talk*.opus', 'sfx/crowd_whisper', ['talk', 'voices'], 'loop', ['crowd_whisper'], {}),
    ('civitas', 'radio-window.opus', 'sfx/crowd_whisper', ['muffled', 'talking'], 'loop', ['crowd_whisper'], {}),
    ('civitas', 'wind*.opus', 'sfx/ambience', ['wind'], 'loop', ['ambience_night'], {}),
    ('civitas', 'gust*.opus', 'sfx/ambience', ['wind', 'gust'], 'oneshot', ['ambience_night'], {}),
    ('civitas', 'owl*.opus', 'sfx/ambience', ['owl', 'night'], 'oneshot', ['ambience_night'], {}),
    ('civitas', 'dog*.opus', 'sfx/ambience', ['dog', 'bark', 'distant'], 'oneshot', ['ambience_night'], {}),
    ('civitas', 'front-door*.opus', 'sfx/foley/doors', ['door', 'close', 'slam'], 'oneshot', [], {}),
    ('civitas', 'pass-car*.opus', 'sfx/vehicles', ['car', 'pass'], 'oneshot', ['car_pass'], {}),
    ('civitas', 'siren*.opus', 'sfx/vehicles', ['siren'], 'oneshot', ['siren_far'], {}),
    ('civitas', 'footsteps*.opus', 'sfx/footsteps', ['footsteps', 'concrete'], 'oneshot', ['footsteps_porch'], {}),
    ('victor', '13_heartbeat.mp3', 'sfx/vocal', ['heartbeat'], 'loop', ['heartbeat'], {}),
    ('victor', '12_cricket.mp3', 'sfx/ambience', ['crickets', 'night'], 'loop', ['ambience_night'], {}),
    ('victor', '10_red_phone.mp3', 'sfx/phone', ['phone', 'landline', 'ring'], 'oneshot', ['phone_ring'], {}),
    ('victor', '86_doorbell.mp3', 'sfx/foley/doors', ['doorbell'], 'oneshot', ['doorbell_chime'], {}),
    ('victor', '02_siren.mp3', 'sfx/vehicles', ['siren'], 'oneshot', ['siren_far'], {}),
]

REQUIRED = ('knock_door doorbell_chime footsteps_porch footsteps_wood_inside car_pass car_idle car_door_open car_door_close '
            'siren_far police_radio_squelch radio_click radio_static bodycam_beep phone_ring phone_busy phone_vibrate '
            'phone_pickup mail_slot paper pen_click key_in_lock lock_turn chain_lock door_creak breath heartbeat whoosh riser '
            'braam impact_hit sub_drop stinger glitch ui_pop typing tinnitus ambience_night room_tone clock_tick '
            'countdown_tick tv_off crowd_whisper').split()
# how sfx.py should treat each name that the Epidemic files do not serve (free recordings + synthesis)
PLAN = {
    'room_tone': 'recorded: Oculus home room tones and HVAC/fan/fridge-like hums (loops); layer 2, EQ per room',
    'clock_tick': 'recorded: Oculus creepy clock ticks + loopable mechanical clock (Owlish); pitch/space per shot',
    'countdown_tick': 'recorded: stopwatch loop, Kenney UI ticks, clock ticks; tight, dry, close',
    'tv_off': 'synthesis + layers: CRT collapse (HF whine sweep down, degauss thump, static pop) synthesized; recorded switch clicks, '
              'electric powerdown/crackle and Epidemic radio static as layers',
    'crowd_whisper': 'recorded layers: whisper grains (OGA, qubodup), shh/breaths, indoor murmur and restaurant walla; '
                     'stack 8-20 time/pitch-shifted copies, band-limit, pan wide',
    'typing': 'recorded: 50 keystrokes / typing takes (OGA keyboard soundpack)',
    'door_creak': 'recorded: door open/close creaks (qubodup sets, Kenney RPG creaks, OGA wood squeaks, Oculus wood doors) '
                  '+ CC0 double-bass bow creaks for slow horror creaks',
    'glitch': 'recorded: Sonic Pi glitch/robot, Kenney interface glitches, sci-fi computer noise; plus synthesized bit-crush stutters',
    'pen_click': 'recorded layers: small plastic/mechanical clicks (Oculus switches, clickety clips, Kenney); pair two clicks 60-90 ms apart',
    'phone_pickup': 'recorded layers + synthesis: plastic handling (Oculus plastic drops), switch clicks and cloth; '
                    'line-open click and noise floor synthesized',
}
SCORE_NEEDS = {  # score layer -> categories that cover it (or 'synth')
    'piano (motifs)': ['score/piano/grand_salamander', 'score/piano/upright_vsco', 'score/piano/horror_soft', 'score/piano/horror_loud', 'score/piano/horror_alt'],
    'music box (motif)': ['score/mallets/celesta', 'score/mallets/glockenspiel'],
    'celesta': ['score/mallets/celesta'],
    'glockenspiel': ['score/mallets/glockenspiel', 'score/mallets/glock_glisses'],
    'bells / chimes': ['score/mallets/nepalese_bells', 'score/percussion/metals'],
    'strings sustain / clusters': [ST + x for x in ('violins_sustain', 'violas_sustain', 'celli_sustain', 'contrabass_sustain', 'solo_violin_sustain')],
    'strings tremolo swells': [ST + x for x in ('violins_tremolo', 'violas_tremolo', 'celli_tremolo', 'contrabass_tremolo', 'solo_violin_tremolo')],
    'strings pizzicato (pulse / ostinato)': [ST + x for x in ('violins_pizz', 'violas_pizz', 'celli_pizz', 'contrabass_pizz', 'solo_violin_pizz')],
    'strings spiccato (ostinato)': [ST + x for x in ('violins_spiccato', 'violas_spiccato', 'celli_spiccato', 'contrabass_spiccato', 'solo_violin_spiccato')],
    'strings harmonics / sul ponticello / col legno': [],
    'harp': ['score/harp'],
    'organ': ['score/organ'],
    'low brass (braam layer)': ['score/brass/horn_sustain', 'score/brass/horn_muted', 'score/brass/trombone_sustain', 'score/brass/tuba_sustain', 'score/brass/war_tuba'],
    'timpani / bass drum (hits, pulse)': ['score/percussion/timpani', 'score/percussion/bass_drum', 'score/percussion/body'],
    'gong / tam-tam': ['score/percussion/gong_tamtam', 'score/percussion/bowed_metals'],
    'cymbals (bowed, crescendo risers)': ['score/percussion/cymbals'],
    'bowed metals / flexatone (texture)': ['score/percussion/bowed_metals', 'score/percussion/metals'],
    'drones / pads': ['score/drones_pads', 'score/organ'],
    'stingers': ['score/stingers'],
    'impulse responses': ['ir'],
}

# ----------------------------------------------------------------------------------------------------------- helpers
NOTE_PC = {'c': 0, 'd': 2, 'e': 4, 'f': 5, 'g': 7, 'a': 9, 'b': 11}
NOTE_RE = re.compile(r'(?<![A-Za-z])([A-Ga-g])(#|s|b)?(-?\d)(?![\d])')


def parse_note(base, opts):
    if opts.get('midi_prefix'):
        m = re.match(r'(\d{2,3})_', base)
        return int(m.group(1)) if m else None
    if opts.get('piano_map'):
        m = re.search(r'_(\d{3})$', base)
        if m:
            i = int(m.group(1))
            return 108 if i >= 44 else 21 + 2 * i
        return None
    if opts.get('strip'):
        base = base.replace(opts['strip'], '_')
    m = NOTE_RE.search(base)
    if not m:
        return None
    pc = NOTE_PC[m.group(1).lower()] + {'#': 1, 's': 1, 'b': -1, None: 0}[m.group(2)]
    return 12 * (int(m.group(3)) + 1) + pc


def parse_layer(base):
    out = {}
    m = re.search(r'(?:^|[_\-\d])(?:v|vl|dyn)(\d+)', base)
    if m:
        out['vel'] = int(m.group(1))
    m = re.search(r'-(\d+)-(\d+)_', base)
    if m:
        out['vel_range'] = [int(m.group(1)), int(m.group(2))]
    m = re.search(r'rr(\d+)', base)
    if m:
        out['rr'] = int(m.group(1))
    return out


def decode(path):
    """-> (float32 [n, ch], sr, subtype, lossy)"""
    ext = path.rsplit('.', 1)[-1].lower()
    if ext in ('wav', 'flac', 'aif', 'aiff'):
        x, sr = sf.read(path, dtype='float32', always_2d=True)
        return x, sr, sf.info(path).subtype, False
    p = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', path, '-vn', '-f', 'wav', '-acodec', 'pcm_f32le', '-'],
                       capture_output=True, timeout=300)
    if p.returncode or not p.stdout:
        raise RuntimeError('ffmpeg: ' + p.stderr.decode(errors='replace')[:200])
    x, sr = sf.read(io.BytesIO(p.stdout), dtype='float32', always_2d=True)
    return x, sr, 'PCM_16', True


def clip_runs(x, thr=0.999, minrun=3):
    n = 0
    for c in range(x.shape[1]):
        m = np.abs(x[:, c]) >= thr
        if not m.any():
            continue
        d = np.diff(np.concatenate(([0], m.astype(np.int8), [0])))
        st, en = np.where(d == 1)[0], np.where(d == -1)[0]
        n += int(np.sum((en - st) >= minrun))
    return n


def env_db(x, sr, win=0.02, hop=None):
    hop = hop or int(sr * 0.005)
    w = int(sr * win)
    p = np.mean(x.astype(np.float64) ** 2, axis=1)
    if len(p) < w:
        return np.array([10 * np.log10(np.mean(p) + 1e-20)]), hop
    c = np.concatenate(([0.0], np.cumsum(p)))
    idx = np.arange(0, len(p) - w + 1, hop)
    return 10 * np.log10((c[idx + w] - c[idx]) / w + 1e-20), hop


def fade(x, n_in, n_out):
    if n_in > 0:
        x[:n_in] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n_in)))[:, None]
    if n_out > 0:
        x[-n_out:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, n_out)))[:, None]
    return x


def trim(x, sr, policy, floor_db):
    e, hop = env_db(x, sr, 0.005, int(sr * 0.0025))
    pk = float(e.max())
    fl = floor_db if floor_db is not None else -120
    if policy == 'ir':
        a = np.abs(x).max(axis=1)
        start = max(0, int(np.argmax(a >= a.max() * 10 ** (-30 / 20))) - int(0.0005 * sr))
        thr_t = max(pk - 90, min(fl + 3, pk - 50), -110)
    else:
        thr_l = max(pk - 50, min(fl + 6, pk - 30), -70)
        i = int(np.argmax(e > thr_l))
        start = max(0, i * hop - int(0.005 * sr))
        thr_t = max(pk - 75, min(fl + 3, pk - 40), -85)
    above = np.where(e > thr_t)[0]
    end = len(x) if not len(above) else min(len(x), (above[-1] + 1) * hop + int(0.005 * sr) + int(0.03 * sr))
    y = x[start:end].copy()
    n_out = min(int(0.04 * sr), len(y) // 10) if end < len(x) else min(int(0.003 * sr), len(y) // 10)
    return fade(y, int(0.002 * sr) if start > 0 else 0, n_out), start, len(x) - end


def lufs(x):
    if len(x) < int(0.4 * SR):
        return None
    import pyloudnorm
    v = pyloudnorm.Meter(SR).integrated_loudness(x if x.shape[1] > 1 else x[:, 0])
    return None if not np.isfinite(v) else round(float(v), 1)


def f0_est(x):
    import librosa
    y = x.mean(axis=1)[: int(3 * SR)]
    if len(y) < 8192:
        return None
    f = librosa.yin(y, fmin=27.0, fmax=4200.0, sr=SR, frame_length=8192, hop_length=2048)
    r = librosa.feature.rms(y=y, frame_length=8192, hop_length=2048)[0][: len(f)]
    f = f[r > r.max() * 0.1]
    return round(float(np.median(f)), 2) if len(f) else None


def slug(s):
    s = s.replace('#', 's').lower()
    return re.sub(r'[^a-z0-9]+', '_', s).strip('_')


# ----------------------------------------------------------------------------------------------------------- worker
def process(job):
    src, rel, cat, tags, policy, serves, opts = job
    meta = SOURCES[src]
    path = os.path.join(DL, meta['root'], rel)
    base = os.path.splitext(os.path.basename(rel))[0]
    stem = slug(os.path.splitext(rel)[0])[-110:]
    out = os.path.join(OUT, cat, f'{src}__{stem}.flac')
    cache = os.path.join(OUT, '_qc', hashlib.sha1(out.encode()).hexdigest()[:16] + '.json')
    if os.path.exists(cache) and os.path.exists(out):
        try:
            r = json.load(open(cache))
            r.update(tags=list(tags), serves=list(serves))  # item specs may change without re-decoding
            return r
        except Exception:
            pass
    rec = dict(path=out, category=cat, tags=list(tags), serves=list(serves), source=src, orig=f'{meta["root"]}/{rel}')
    try:
        x, sr, subtype, lossy = decode(path)
    except Exception as e:
        return dict(rec, rejected=f'decode failed: {e}'[:200])
    if not np.isfinite(x).all():
        x = np.nan_to_num(x)
    qc = []
    cr = clip_runs(x)
    if opts.get('bformat') and x.shape[1] == 4:  # W X Y Z -> L = W + Y, R = W - Y
        x = np.stack([x[:, 0] + x[:, 2], x[:, 0] - x[:, 2]], axis=1)
        qc.append('bformat_decoded')
    if opts.get('ms') and x.shape[1] == 2:
        x = np.stack([x[:, 0] + x[:, 1], x[:, 0] - x[:, 1]], axis=1) * 0.5
        qc.append('ms_decoded')
    if sr != SR:
        x = soxr.resample(x, sr, SR, quality='VHQ').astype(np.float32)
    e, _ = env_db(x, SR)
    floor = round(float(np.percentile(e, 5)), 1) if len(e) > 10 else None
    top = float(np.percentile(e, 99))
    if top < (-85 if policy == 'inst' else -65):
        return dict(rec, rejected=f'no signal (99th pct 20 ms RMS {top:.1f} dBFS)')
    if cr >= 8 or cr > len(x) / SR * 4:
        return dict(rec, rejected=f'clipped ({cr} runs of >=3 full-scale samples)')
    if cr:
        qc.append(f'clip_runs_{cr}')
    pol = policy
    if pol == 'auto':
        pol = 'loop' if ('LOOP' in rel or 'loop' in base.lower() or len(x) > 8 * SR) else 'oneshot'
    t0 = t1 = 0
    if pol in ('oneshot', 'inst', 'ir'):
        x, t0, t1 = trim(x, SR, pol, floor)
    if len(x) < int(0.01 * SR):
        return dict(rec, rejected='empty after trim')
    peak = float(np.abs(x).max())
    gain_db = 0.0
    if peak > 0.999:
        gain_db = 20 * math.log10(0.999 / peak)
        x = x * (0.999 / peak)
        qc.append(f'gain_{gain_db:.2f}dB_to_avoid_overs')
    snr = round(top - floor, 1) if floor is not None else None
    if pol in ('oneshot', 'inst') and floor is not None and floor > -50 and (snr or 0) < 35 and len(e) > 40:
        tail = e[-max(10, len(e) // 4):]  # a steady bed at the floor = noise; a falling tail = natural decay
        if float(np.std(tail)) < 2.0 and float(tail.max() - tail.min()) < 8:
            qc.append('noise_floor_high')
    if lossy or meta.get('lossy'):
        qc.append('lossy_source')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    st = 'PCM_24' if subtype in ('PCM_24', 'PCM_32', 'FLOAT', 'DOUBLE') else 'PCM_16'
    tmp = out + '.part'
    sf.write(tmp, x, SR, subtype=st, format='FLAC')
    os.replace(tmp, out)
    rec.update(dur=round(len(x) / SR, 3), sr=SR, channels=int(x.shape[1]), bit_depth=24 if st == 'PCM_24' else 16,
               peak_db=round(20 * math.log10(max(float(np.abs(x).max()), 1e-9)), 2), lufs=lufs(x),
               rms_db=round(10 * math.log10(float(np.mean(x.astype(np.float64) ** 2)) + 1e-20), 1),
               floor_db=floor, snr_db=snr, trimmed_s=[round(t0 / SR, 3), round(t1 / SR, 3)], policy=pol, qc=qc,
               orig_sr=sr)
    if pol == 'inst':
        n = None if opts.get('f0') else parse_note(base, opts)
        if n is not None:
            rec['midi'] = n
        if not opts.get('nopitch'):
            f0 = f0_est(x)
            if f0:
                rec['f0_hz'] = f0
                rec['midi_est'] = round(69 + 12 * math.log2(f0 / 440.0), 2)
        rec.update(parse_layer(base))
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    json.dump(rec, open(cache, 'w'))
    return rec


def epidemic_qc(job):
    kind, e = job
    rec = dict(path=e['path'], category=f'epidemic/{kind}', tags=e['slug'].split('_')[:12], serves=e.get('serves', []),
               source='epidemic', licence='Epidemic Sound (owner subscription)', attribution=None)
    try:
        info = sf.info(e['path'])
        x, sr = sf.read(e['path'], dtype='float32', always_2d=True)
    except Exception as ex:
        return dict(rec, rejected=f'decode failed: {ex}'[:200])
    ev, _ = env_db(x, sr)
    cr = clip_runs(x)
    rec.update(dur=round(len(x) / sr, 3), sr=sr, channels=info.channels, bit_depth={'PCM_16': 16, 'PCM_24': 24}.get(info.subtype, 32),
               peak_db=round(20 * math.log10(max(float(np.abs(x).max()), 1e-9)), 2), lufs=e.get('lufs'),
               floor_db=round(float(np.percentile(ev, 5)), 1), policy='as_supplied',
               qc=([f'clip_runs_{cr}'] if cr else []))
    if kind == 'music':
        rec.update(tempo=e.get('tempo'), tonal_centre=e.get('tonal_centre'))
    return rec


# ------------------------------------------------------------------------------------------------------------- main
def expand(only):
    jobs, seen = [], set()
    for it in ITEMS:
        src = it[0]
        if only and src not in only:
            continue
        root = os.path.join(DL, SOURCES[src]['root'])
        for p in sorted(glob.glob(os.path.join(glob.escape(root), it[1]), recursive=True)):
            if not os.path.isfile(p) or p.rsplit('.', 1)[-1].lower() not in ('wav', 'flac', 'ogg', 'opus', 'm4a', 'mp3'):
                continue
            rel = os.path.relpath(p, root)
            if (src, rel) in seen:
                continue
            seen.add((src, rel))
            jobs.append((src, rel) + tuple(it[2:]))
    return jobs


def credits_tables():
    """Per-file upstream credits for civitas / victor / Sonic Pi / atomcut packs."""
    out = {}
    m = os.path.join(LIC, 'civitas_CREDITS.md')
    for line in open(m, encoding='utf8') if os.path.exists(m) else []:
        c = [s.strip() for s in line.split('|')]
        if len(c) > 7 and c[2].endswith('.opus'):
            u = re.search(r'\((https?://[^)]+)\)', c[3]); a = re.search(r'\[([^\]]+)\]', c[5])
            out[('civitas', c[2])] = dict(upstream=u.group(1) if u else None, author=a.group(1) if a else None, title=c[4], lic=c[6])
    m = os.path.join(LIC, 'victor_CREDITS.md')
    for line in open(m, encoding='utf8') if os.path.exists(m) else []:
        c = [s.strip() for s in line.split('|')]
        if len(c) > 5 and c[1].startswith('`'):
            u = re.search(r'\((https?://[^)]+)\)', c[2]); t = re.search(r'\[([^\]]+)\]', c[2])
            out[('victor', c[1].strip('`'))] = dict(upstream=u.group(1) if u else None, author=c[3], title=t.group(1) if t else None, lic=c[4])
    m = os.path.join(LIC, 'sonicpi_samples_README.md')
    for line in open(m, encoding='utf8') if os.path.exists(m) else []:
        r = re.match(r'\* `:?([a-z0-9_]+)`\s+-\s+(.*)', line.strip())
        if r:
            u = re.search(r'(https?://\S+)', r.group(2))
            name = re.sub(r'_(\d)$', r'\1', r.group(1))
            out[('sonicpi', name + '.flac')] = dict(upstream=u.group(1) if u else None, credit=r.group(2)[:160])
    m = os.path.join(LIC, 'atomcut_packs.json')
    for k, d in (json.load(open(m)).items() if os.path.exists(m) else []):
        out[('atomcut', k)] = dict(upstream=d.get('homepage'), author=(d.get('attribution') or '').split(' · ')[0] or None,
                                   attribution=d.get('attribution'), lic=d.get('license'))
    return out


def attach_licence(rec, cred):
    src = rec['source']
    meta = SOURCES[src]
    rec['licence'] = meta['licence']
    rec['source_url'] = meta['url']
    rec['upstream_url'] = meta.get('upstream')
    rec['author'] = meta['author']
    rel = rec['orig'][len(meta['root']) + 1:]
    fname = os.path.basename(rel)
    c = cred.get((src, fname)) or (cred.get((src, rel.split('/')[0])) if src == 'atomcut' else None)
    if c:
        rec['upstream_url'] = c.get('upstream') or rec['upstream_url']
        rec['author'] = c.get('author') or rec['author']
        if c.get('lic') and c['lic'] not in ('CC0', 'CC0-1.0', 'PD', 'own-CC0'):
            rec['licence'] = c['lic']
    if src in ('openair', 'openair2'):
        stem = os.path.splitext(fname)[0]
        room, pid, who = OPENAIR_ROOMS.get(stem, ('OpenAIR room', None, 'www.openairlib.net'))
        rec['upstream_url'] = OA + str(pid) if pid else None
        rec['room'] = room
        by = '' if who == 'www.openairlib.net' else f', recorded by {who}'
        rec['attribution'] = (f'Impulse response "{room}" from the OpenAIR library (www.openairlib.net), Audiolab, '
                              f'University of York{by}, licensed under CC BY 4.0.')
    elif src == 'oculus':
        rec['attribution'] = meta['attribution']
    elif src == 'salamander':
        rec['attribution'] = ('"Salamander Grand Piano" samples by Alexander Holm (sfz remap by kinwie, '
                              'https://github.com/sfzinstruments/SalamanderGrandPiano), licensed under CC BY 3.0.')
    else:
        rec['attribution'] = None  # CC0 / public domain: no attribution required
        rec['courtesy_credit'] = f'{meta["title"]}: {rec["author"]} (CC0)'
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', type=int, default=3)
    ap.add_argument('--only', default='')
    ap.add_argument('--no-epidemic', action='store_true')
    a = ap.parse_args()
    only = set(filter(None, a.only.split(',')))
    jobs = expand(only)
    print(f'{len(jobs)} files to process', flush=True)
    t = time.time()
    recs = []
    with Pool(a.jobs) as pool:
        for i, r in enumerate(pool.imap_unordered(process, jobs, chunksize=4)):
            recs.append(r)
            if (i + 1) % 200 == 0:
                print(f'  {i + 1}/{len(jobs)}  {time.time() - t:.0f}s', flush=True)
    # files whose raw download was deleted after conversion: keep their converted output from the QC cache
    done_paths = {r['path'] for r in recs}
    gone = set()
    for f in glob.glob(os.path.join(OUT, '_qc', '[0-9a-f]*.json')):
        r = json.load(open(f))
        if (r.get('path') not in done_paths and os.path.exists(r.get('path', '')) and (not only or r['source'] in only)
                and not os.path.exists(os.path.join(DL, r['orig']))):
            recs.append(r)
            gone.add(r['source'])
    print(f'reused {sum(1 for r in recs if r.get("path") not in done_paths)} cached files of deleted downloads')
    cred = credits_tables()
    ok = [attach_licence(r, cred) for r in recs if 'rejected' not in r]
    rej = [dict(source=r['source'], orig=r['orig'], reason=r['rejected']) for r in recs if 'rejected' in r]
    rq = os.path.join(OUT, '_qc', '_rejected.json')
    old = json.load(open(rq)) if os.path.exists(rq) else []
    rej += [r for r in old if not os.path.exists(os.path.join(DL, r['orig'])) and r['orig'] not in {x['orig'] for x in rej}]
    os.makedirs(os.path.dirname(rq), exist_ok=True)
    json.dump(rej, open(rq, 'w'), indent=1)
    epi = []
    ecat = os.path.join(HERE, 'catalog_epidemic.json')
    if not a.no_epidemic and os.path.exists(ecat):
        ed = json.load(open(ecat))
        with Pool(a.jobs) as pool:
            epi = pool.map(epidemic_qc, [('sfx', e) for e in ed['sfx']] + [('music', e) for e in ed['music']])
    fix_octaves(ok)
    for r in epi:
        if r.get('peak_db', -99) >= -0.01:
            r['qc'].append('peak_0dBFS')
    allr = sorted(ok, key=lambda r: r['path']) + epi
    for r in allr:
        r['id'] = os.path.splitext(os.path.basename(r['path']))[0]
        r['path'] = os.path.relpath(r['path'], OUT)
    cov = coverage(allr)
    cat = dict(
        root=OUT,
        note='Paths are relative to `root`. All free files are 48 kHz FLAC. Load with audio/library.py. '
             'Licences: CC0-1.0 needs nothing; CC-BY items need the line in ATTRIBUTION.md in the video description. '
             'Epidemic files: owner subscription, never commit or redistribute.',
        built=time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()),
        sources={k: dict(licence=v['licence'], url=v['url'], title=v['title'], author=v['author'], upstream=v.get('upstream'))
                 for k, v in SOURCES.items()},
        coverage=cov, samples=allr, rejected=rej)
    json.dump(cat, open(os.path.join(HERE, 'catalog.json'), 'w'), indent=1)
    write_attribution(ok)
    tot = sum(os.path.getsize(os.path.join(OUT, r['path'])) for r in ok if os.path.exists(os.path.join(OUT, r['path'])))
    print(f'done: {len(ok)} free files ({tot / 1e9:.2f} GB), {len(epi)} epidemic, {len(rej)} rejected, {time.time() - t:.0f}s')


def fix_octaves(recs):
    """Libraries disagree on octave numbering (VSCO and Karoryfer name middle C 'C3'; a glockenspiel sounds an octave
    above its written note). Per category, shift the filename note by the whole octaves the measured pitch shows."""
    g = {}
    for r in recs:
        if r.get('midi') is not None and r.get('midi_est') is not None:
            g.setdefault(r['category'], []).append(r['midi_est'] - r['midi'])
    for c, v in g.items():
        med = float(np.median(v))
        k = 12 * round(med / 12)
        if k and abs(med - k) < 0.5:
            for r in recs:
                if r['category'] == c and r.get('midi') is not None:
                    r['midi'] += k
                    r['midi_octave_fix'] = k


def coverage(allr):
    sfx = []
    for n in REQUIRED:
        e = [r['id'] for r in allr if r['source'] == 'epidemic' and n in r['serves']]
        f = [r for r in allr if r['source'] != 'epidemic' and n in r['serves']]
        cats = sorted({r['category'] for r in f})
        if e:
            st = 'epidemic' + (' + free layers' if f else '')
        elif n in PLAN:
            st = PLAN[n].split(':')[0]
        else:
            st = 'recorded (free)' if f else 'synthesis'
        sfx.append(dict(name=n, status=st, epidemic=len(e), free=len(f), free_categories=cats,
                        epidemic_ids=e[:6], plan=PLAN.get(n)))
    score = []
    for k, cats in SCORE_NEEDS.items():
        n = sum(1 for r in allr if r['category'] in cats)
        score.append(dict(layer=k, files=n, categories=cats, status='recorded' if n else 'synthesis / derived'))
    score.append(dict(layer='score backbone', files=sum(1 for r in allr if r['category'] == 'epidemic/music'),
                      categories=['epidemic/music'], status='epidemic (6 tracks)'))
    return dict(sfx=sfx, score=score)


def write_attribution(ok):
    by = {}
    for r in ok:
        if r['licence'].startswith('CC-BY'):
            by.setdefault(r['attribution'], 0)
            by[r['attribution']] += 1
    cc0 = sorted({(SOURCES[r['source']]['title'], SOURCES[r['source']]['url']) for r in ok if r['licence'] == 'CC0-1.0'})
    up = sorted({(r['author'], r.get('upstream_url') or '') for r in ok if r['source'] in ('atomcut', 'freesfx', 'civitas', 'victor')
                 and r.get('author')})
    L = ['# Sound credits', '',
         'Paste the block below into the video description. CC BY items require it; the CC0 credits are courtesy.',
         'The owner\'s Epidemic Sound tracks and effects are licensed through the channel\'s subscription and need no credit.',
         'A line whose files the final mix does not use may be dropped; keeping every line is always safe.', '',
         '```', 'Sound credits:']
    for a in sorted(by):
        L.append(f'- {a}')
    L += ['Additional public-domain (CC0) sounds and instruments: ' +
          '; '.join(t for t, _ in cc0) + '.', '```', '', '## CC BY items in the library', '']
    for a, n in sorted(by.items()):
        L.append(f'- {n} file(s): {a}')
    L += ['', '## CC0 sources (no attribution required)', '']
    for t, u in cc0:
        L.append(f'- {t}: {u}')
    L += ['', '## Upstream authors of the CC0 effects (courtesy)', '', ', '.join(sorted({a for a, _ in up})) + '.', '']
    open(os.path.join(HERE, 'ATTRIBUTION.md'), 'w').write('\n'.join(L))


if __name__ == '__main__':
    main()
