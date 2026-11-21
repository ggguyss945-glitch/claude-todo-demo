"""review_sfx.py: measure the owner's new Epidemic files for this film (the Bus film: W/samples/epidemic_bus, sfx/ and
music/; the Bunnyman film's verdicts below are kept for reference, BUS_DECISIONS are this film's) so each one
can be judged before it is used (use / process / reject: the decisions and reasons are in W/mix/sfx_review.md).

    python3 audio/review_sfx.py [--kind sfx|music|all] [--no-asr] [--only <substring>]      (from film/)

For every file (mono analysis unless noted):
    dur, LUFS (BS.1770, sfx.lufs_int), sample peak, true peak (4x), clipped samples (|x| >= 0.999) and the longest run
    noise floor = 5th percentile of the 50 ms RMS (dBFS), active level = its 95th percentile, their difference (SNR)
    spectrum over the active frames: centroid and 95 % roll-off medians, energy share < 250 Hz / 250 Hz-4 kHz / > 4 kHz,
    the codec's low-pass (highest frequency where the long-term spectrum is within 60 dB of its 1-5 kHz level)
    onsets per second; harmonic share (HPSS); tonal clarity (median of the chroma max / mean: a band or a tune is > 2.5)
    stereo: L/R correlation and side-minus-mid (dB)
    speech: Silero VAD share and the words Parakeet hears (crowds, voices, hospital ambiences; --no-asr skips it)
Draws one strip per file (log-frequency spectrogram 30 Hz-20 kHz with the 50 ms RMS envelope under it) into contact
sheets W/mix/review/sheet_<kind>_NN.png (6 files per sheet) and writes W/mix/review/review_measure.json.
    python3 audio/review_sfx.py --md      writes W/mix/sfx_review.md: the measurements with the verdicts of DECISIONS
                                          (USE / PROCESS / REJECT, the sfx.py names each file feeds, why), plus
                                          W/mix/sfx_review.md.notes (the free sounds and the synthesis) appended
"""
import json, os, re, sys, warnings
import numpy as np, soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx as SX                                            # noqa: E402

W = SX.W
SET = os.path.join(W, 'samples', 'epidemic_ice')     # THIS film: the Ice Cream film's new set
OUT = os.path.join(W, 'mix', 'review')
MODELS = '/tmp/claude-0/-home-user-claude-todo-demo/aa250ae7-a0b4-594f-9bc6-bd18b596cf27/scratchpad/models'
SR = 48000
ASR_WORDS = ('crowd', 'voices', 'hospital', 'ambience', 'fight', 'efforts', 'cheer', 'school', 'kids', 'announcement',
             'megaphone', 'walkie', 'pa_system')
# music: the recogniser also listens to every track (a song with vocals must never play under the narration)


def slug(f):
    import epidemic_catalog as EC
    return EC.slugify(os.path.splitext(f)[0])


def measure(path):
    x, sr = sf.read(path, dtype='float32', always_2d=True)
    if sr != SR:
        import soxr
        x = soxr.resample(x, sr, SR).astype(np.float32)
    full = len(x)
    x = x[:SR * 200]                                    # long takes: the first 200 s is enough (memory)
    st = x[:, :2] if x.shape[1] > 1 else np.repeat(x, 2, 1)
    m = st.mean(1)
    n = len(m)
    r = {'dur': round(full / SR, 2), 'channels': int(x.shape[1])}
    r['lufs'] = round(SX.lufs_int(st), 1) if n > SR * 0.4 else round(SX.mom_max(st), 1)
    r['peak_db'] = round(float(SX.db(np.abs(st).max())), 1)
    up = signal.resample_poly(st[:SR * 120], 4, 1, axis=0) if n > 0 else st
    r['true_peak_db'] = round(float(SX.db(np.abs(up).max())), 1)
    cl = np.abs(st).max(1) >= 0.999
    r['clipped'] = int(cl.sum())
    if cl.any():
        d = np.diff(np.concatenate([[0], cl.astype(int), [0]]))
        r['clip_run_max'] = int((np.flatnonzero(d == -1) - np.flatnonzero(d == 1)).max())
    k = int(0.05 * SR)
    nb = max(1, n // k)
    rms = np.sqrt((m[:nb * k].reshape(nb, k) ** 2).mean(1) + 1e-20)
    rdb = SX.db(rms)
    r['floor_db'] = round(float(np.percentile(rdb, 5)), 1)
    r['active_db'] = round(float(np.percentile(rdb, 95)), 1)
    r['snr_db'] = round(r['active_db'] - r['floor_db'], 1)
    f, t, Z = signal.stft(m, SR, nperseg=4096, noverlap=3072, boundary=None)
    P = np.abs(Z) ** 2
    fe = P.sum(0)
    act = fe > np.percentile(fe, 40)
    if act.sum() < 3:
        act = fe > 0
    Pa = P[:, act]
    cen = (f[:, None] * Pa).sum(0) / (Pa.sum(0) + 1e-20)
    cs = np.cumsum(Pa, 0) / (Pa.sum(0) + 1e-20)
    roll = f[np.argmax(cs >= 0.95, axis=0)]
    r['centroid_hz'] = int(np.median(cen))
    r['rolloff95_hz'] = int(np.median(roll))
    tot = Pa.sum() + 1e-20
    r['low_mid_high_pct'] = [round(100 * float(Pa[f < 250].sum() / tot), 1),
                             round(100 * float(Pa[(f >= 250) & (f < 4000)].sum() / tot), 1),
                             round(100 * float(Pa[f >= 4000].sum() / tot), 1)]
    lt = 10 * np.log10(Pa.mean(1) + 1e-30)
    ref = float(np.median(lt[(f > 1000) & (f < 5000)]))
    hi = np.flatnonzero(lt > ref - 60)
    r['codec_lowpass_hz'] = int(f[hi[-1]]) if len(hi) else None
    import librosa
    y22 = librosa.resample(m, orig_sr=SR, target_sr=22050)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        on = librosa.onset.onset_detect(y=y22, sr=22050, units='time')
        r['onsets_per_s'] = round(len(on) / max(0.5, n / SR), 2)
        Hs, Ps = librosa.decompose.hpss(np.abs(librosa.stft(y22[:22050 * 90], n_fft=2048, hop_length=512)) ** 2)
        r['harmonic_pct'] = round(100 * float(Hs.sum() / (Hs.sum() + Ps.sum() + 1e-20)), 1)
        ch = librosa.feature.chroma_stft(y=y22[:22050 * 90], sr=22050, hop_length=2048)
        cm = ch.max(0) / (ch.mean(0) + 1e-9)
        r['tonal_clarity'] = round(float(np.median(cm)), 2)
    if st.shape[1] == 2 and np.std(st[:, 0]) > 0 and np.std(st[:, 1]) > 0:
        r['lr_corr'] = round(float(np.corrcoef(st[:, 0], st[:, 1])[0, 1]), 2)
        s_ = (st[:, 0] - st[:, 1]) * 0.5
        r['side_minus_mid_db'] = round(float(10 * np.log10((s_ ** 2).mean() + 1e-20) - 10 * np.log10((m ** 2).mean() + 1e-20)), 1)
    return r, m, rdb


_ASR = None


def asr(m):
    """Speech share (Silero VAD) and the words Parakeet hears."""
    global _ASR
    import sherpa_onnx, soxr
    pk = os.path.join(MODELS, 'sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8')
    if _ASR is None:
        _ASR = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=f'{pk}/encoder.int8.onnx', decoder=f'{pk}/decoder.int8.onnx', joiner=f'{pk}/joiner.int8.onnx',
            tokens=f'{pk}/tokens.txt', model_type='nemo_transducer', num_threads=1)
    x16 = soxr.resample(m, SR, 16000).astype(np.float32)
    cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = os.path.join(MODELS, 'vad.onnx')
    cfg.silero_vad.threshold = 0.5; cfg.silero_vad.min_silence_duration = 0.3
    cfg.silero_vad.min_speech_duration = 0.25; cfg.silero_vad.max_speech_duration = 12; cfg.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=400)
    segs = []
    for i in range(0, len(x16), 512):
        vad.accept_waveform(x16[i:i + 512])
        while not vad.empty():
            segs.append((vad.front.start / 16000, len(vad.front.samples) / 16000)); vad.pop()
    vad.flush()
    while not vad.empty():
        segs.append((vad.front.start / 16000, len(vad.front.samples) / 16000)); vad.pop()
    words = []
    for a, d in segs[:40]:
        s = _ASR.create_stream(); s.accept_waveform(16000, x16[int(a * 16000):int((a + d) * 16000)])
        _ASR.decode_stream(s)
        if s.result.text.strip():
            words.append(f'{a:.1f}s: {s.result.text.strip()}')
    return round(100 * sum(d for _, d in segs) / (len(x16) / 16000), 1), words


def strip(ax, ax2, m, rdb, title):
    f, t, S = signal.spectrogram(m, SR, nperseg=2048, noverlap=1536)
    S = 10 * np.log10(S + 1e-14)
    vmax = np.percentile(S, 99.5)
    ax.pcolormesh(t, f, S, shading='auto', cmap='magma', vmin=vmax - 80, vmax=vmax, rasterized=True)
    ax.set_yscale('log'); ax.set_ylim(30, 20000)
    ax.set_yticks([50, 100, 250, 1000, 4000, 16000]); ax.set_yticklabels(['50', '100', '250', '1k', '4k', '16k'], fontsize=6)
    ax.tick_params(axis='x', labelsize=6)
    ax.set_title(title, fontsize=7, loc='left')
    tt = np.arange(len(rdb)) * 0.05
    ax2.plot(tt, rdb, lw=0.6, color='k'); ax2.set_ylim(-90, 0); ax2.set_xlim(0, max(tt[-1], 0.1))
    ax2.set_yticks([-80, -40, 0]); ax2.tick_params(labelsize=6); ax2.grid(alpha=0.3)
    ax.set_xlim(0, max(tt[-1], 0.1))


# ------------------------------------------------------------------------------------------------ the verdicts
# slug -> (verdict, sfx.py names it feeds, reason). USE = as recorded (cut into grains, levelled, placed in a space);
# PROCESS = only after the processing named; REJECT = never used (mapped to no bunny name, vetoed in
# epidemic_catalog.NOT where an older name would have picked it up).
DECISIONS = {
    # ambiences
    'ambience_celebration_marching_band_street': ('REJECT', '-', 'a brass band plays its own tune for all 177 s (tonal '
        'clarity 3.1, harmonic 66 %): under the parade it would fight the Pemberton\'s jingle in another key'),
    'ambience_hospital_corridor_walla_doors_different_distances_01': ('USE', 'hospital_room, hospital_corridor',
        'a quiet corridor (-39 LUFS, centroid 195 Hz: HVAC and far walla, doors); the English walla is masked by a '
        '2.6 kHz low-pass through the room door'),
    'ambience_hospital_hospital_corridor_voices_speakerphone_beeping_phones_ring_walla_poland': ('PROCESS',
        'hospital_corridor', 'Polish speech, a speakerphone, beeps and phones: the corridor\'s life, low-passed at '
        '3.2 kHz and kept 6 dB under the quiet corridor; never in the room'),
    'birds_bird_of_prey_tawny_owl_song_male_forest_night': ('USE', 'ambience_woods, owl_hoot', 'the owl calls and a '
        'forest bed; two 1 s digital drop-outs (29 s, 119 s) are skipped by the excerpt picker'),
    'birds_bird_of_prey_tawny_owl_song_male_forest_night_02': ('USE', 'ambience_woods', 'mostly the night forest bed '
        '(SNR 4.8 dB): the quiet layer under the crickets'),
    'crowds_celebration_norwegian_constitution_day_children_marching_band_passing_snare_drum_close_01': ('PROCESS',
        'crowd_parade', 'children and a snare-drum cadence passing (harmonic 17 %: no tune): the parade going by, '
        'low-passed and 10 dB down, only where the jingle is not playing (its tempo would fight the jingle\'s)'),
    'crowds_celebration_norwegian_constitution_day_walla_distant_marching_band_kids_cheering_close': ('USE',
        'crowd_parade', 'kids cheering close over walla: the 1987 parade crowd (the distant band is under the cheers)'),
    'crowds_cheering_cheltenham_festival_following_horse_crowd_cheering_music_united_kingdom': ('REJECT', '-',
        'a racecourse roar with PA music in it (tonal lines 250 Hz-1 kHz all through): adults at a horse race'),
    'crowds_cheering_cheltenham_festival_parade_ring_united_kingdom': ('PROCESS', 'crowd_parade', 'an adult cheer for '
        '20 s, then walla: the distant crowd bed, low-passed at 2.5 kHz, 9 dB under the kids (the first 2 s, an '
        'announcer, skipped)'),
    'crowds_cheering_cheltenham_festival_walking_with_winner_horse_cheering_parade_ring_united_kingdom': ('PROCESS',
        'crowd_parade', 'applause and cheering: the swell as the last float passes, low-passed, under the kids'),
    'crowds_children_primary_school_fight_crowds_cheering_on': ('REJECT', '-', 'children egging on a playground fight: '
        'chanted, aggressive shouting (the file\'s own name); the wrong emotion for an Easter parade'),
    # doors and knocks
    'doors_cabinet_wood_shelf_door_impact': ('USE', 'struggle, door_crash, body_fall_stairs', 'three heavy wooden '
        'slams with shelf rattles: bodies against the hallway walls, the frames rattling'),
    'doors_knock_old_wooden_door_knuckles_short_varied_speed_variations': ('USE', 'knock_family, egg_tap',
        '16 knuckle knocks with the door\'s low boom (96 % < 250 Hz): the front door heard from inside'),
    'doors_knock_wooden_door_knuckles_fast_short_variations_01': ('USE', 'knock_family, knock_door',
        'clean single knocks (digital silence between groups): re-sequenced into the 2-3-2 family knock'),
    'doors_knock_wooden_door_knuckles_fast_short_variations_02': ('USE', 'knock_family, knock_door', 'as 01'),
    'doors_metal_valve_door_open_close_big_hit_impact_01_ambix': ('REJECT', '-', 'a metal ship\'s valve door: clangs '
        'and a hollow steel room; an AmbiX file read as stereo'),
    'doors_wood_70_s_aggressive_kick_out_01': ('USE', 'door_crash', 'four door kick-ins with long wooden decays: the '
        'back door crashing open'),
    'doors_wood_70_s_aggressive_kick_out_03': ('PROCESS', 'struggle', 'three very boomy kicks (centroid 19 Hz): '
        'something slamming into the bathroom door from the hall side, low-passed at 1.8 kHz, the sub kept'),
    'doors_wood_70_s_kick_out': ('USE', 'door_crash', 'a kick and the door hitting the wall 0.45 s later'),
    'doors_wood_impact_light_door': ('USE', 'struggle, attic_door', 'light door thumps and rattles: the bathroom '
        'door shaking in its frame, the attic door closing'),
    'doors_wood_kick_open_internal': ('USE', 'struggle, door_crash', 'an internal door kicked: the slam\'s attack'),
    # fights and bodies
    'fight_bodyfall_metal_plate_metal_sheet_staircase_rolling_fall_01': ('REJECT', '-', 'a body down a METAL '
        'staircase: the sheet metal rings at 250 Hz-1 kHz in every fall; this house\'s stairs are wood'),
    'fight_bodyfall_metal_plate_metal_sheet_staircase_rolling_fall_02': ('REJECT', '-', 'as 01'),
    'fight_bodyfall_metal_plate_metal_sheet_staircase_rolling_fall_04': ('REJECT', '-', 'as 01'),
    'fight_grab_punch_cloth_01': ('USE', 'struggle', '13 grabs and blows in cloth, no voice: the fight in the hall, '
        'low-passed through the bathroom door'),
    'fight_grab_push_shove_cloth_leather_details_grunts_angry': ('REJECT', '-', 'male grunts on every shove: the '
        'family\'s voices are the narration\'s, and the Bunnyman speaks with a little girl\'s voice'),
    'voices_efforts_male_fight_dark_grunts_hits': ('REJECT', '-', 'male grunts (see above)'),
    'voices_efforts_male_fight_grunts_roar': ('REJECT', '-', 'male grunts and roars (see above)'),
    'gore_bone_bone_crack_bone_cracking': ('PROCESS', 'struggle, bone_crack', 'eight cracks: one, low-passed at '
        '2.2 kHz and tucked under a body thud, for "a wet, heavy crack" (restrained, not a cartoon snap)'),
    'gore_bone_break_heavy': ('USE', 'struggle, bone_crack', 'a heavy crunch: the body of the crack'),
    'gore_bone_break_snap_04': ('REJECT', '-', 'a dry, sharp snap (0.67 s, all attack): too cartoonish for the line'),
    'weapon_sword_axe_heavy_whoosh_blade_impact_03': ('REJECT', '-', 'a sword swing into a blade hit: nobody swings in '
        'the script, and the metal ring of the blade at the end reads as a sword'),
    'weapon_sword_axe_heavy_whoosh_blade_impact_05': ('PROCESS', 'struggle', 'the low whoosh body only (low-passed at '
        '900 Hz, 10 dB under the door impact): weight before the slam on the bathroom door'),
    'weapon_sword_axe_heavy_whoosh_blade_impact_07': ('REJECT', '-', 'as 03'),
    'weapons_axe_battle_axe_hitting_shield_boss_impact': ('REJECT', '-', 'an axe on a metal shield boss: a clang'),
    'weapons_axe_hand_axe_hit_shield_edge_impact': ('PROCESS', 'hatchet_step', 'an axe head on a wooden shield edge: '
        'the hatchet knocking the step, low-passed at 3.5 kHz, the shield\'s ring cut after 60 ms'),
    'wood_impact_wood_chopping_pick_axe': ('USE', 'hatchet_step', 'six chops into wood: "Thunk." (the main hit of each '
        'step)'),
    'axe_scrape_head_on_concrete_02': ('PROCESS', 'hatchet_step', 'the head scraping (67 % > 4 kHz: concrete grit): '
        '0.15-0.3 s pieces, low-passed at 3 kHz, as the head drags over each stair nosing'),
    'tools_hand_axe_scrape_head_on_concrete': ('PROCESS', 'hatchet_step', 'as above'),
    # glass, fire
    'glass_break_smash_window_or_large_object': ('PROCESS', 'window_smash', 'the biggest smash; its two clipped '
        'samples (+0.3 dBFS) are rounded off by the peak cap'),
    'glass_break_window_large_smash': ('USE', 'window_smash', 'a window smash with a long debris tail'),
    'glass_break_window_smash': ('USE', 'window_smash', 'eight smashes: the variations'),
    'fire_burst_spray_burn': ('USE', 'burn_barrel', 'two whoomps: the barrel catching (Mom sets it on fire)'),
    'fire_crackle_burning_carbon_crackling_embers': ('USE', 'burn_barrel, plastic_melt', 'dense small crackle '
        '(58 % > 4 kHz): the embers in the barrel'),
    'fire_crackle_heavy_crackling_windy_large_flame_sizzling_fire': ('PROCESS', 'burn_barrel, plastic_melt',
        'a big windy flame: low-passed and cut in level so it is a barrel, not a bonfire; its sizzle feeds the '
        'melting plastic'),
    # eggs, plastic, rings, coins
    'food_drink_ingredients_egg_take_out_of_egg_box': ('PROCESS', 'egg_set', 'a real egg out of a cardboard box: only '
        'the 60 ms hand contact, -12 dB, under the plastic'),
    'food_drink_misc_egg_box_carton_squash_eggs_crack_break_01': ('REJECT', '-', 'real eggshells crushing: the Easter '
        'egg is pink plastic'),
    'hospital_thermometer_plastic_case_open': ('USE', 'egg_open, diary_lock', 'two small plastic snaps: the halves '
        'popping apart, the diary\'s little lock'),
    'objects_container_plastic_box_small_open_lid': ('USE', 'egg_open', 'one plastic lid pop: the egg opening'),
    'objects_container_plastic_lunch_box_open_close_01': ('USE', 'egg_open, egg_rattle, egg_set', 'plastic handling and '
        'snaps: grains for the egg'),
    'objects_container_plastic_lunch_box_open_close_02': ('USE', 'egg_open, egg_rattle, egg_set', 'as 01'),
    'objects_container_plastic_lunch_box_open_close_squeaky_plastic': ('USE', 'egg_open, egg_rattle', 'squeaky plastic '
        'handling: the old, sun-faded shell'),
    'objects_container_plastic_food_box_close_open_x4': ('USE', 'egg_set, egg_open', 'four plastic closes (one clipped '
        'sample, capped)'),
    'objects_coin_money_coins_multiple_in_jar_roll_concrete_01': ('REJECT', '-', 'many coins in a GLASS jar: too many '
        'objects and glassy (57 % > 4 kHz); the egg holds one ring'),
    'objects_coin_money_coins_multiple_in_jar_roll_concrete_02': ('REJECT', '-', 'as 01 (86 % > 4 kHz)'),
    'objects_coin_money_roll_on_glass_01': ('PROCESS', 'ring_roll', 'one coin rolling: the ring rolling around inside '
        'the egg half, the glass\'s brightness taken down (high shelf -8 dB) and the plastic shell\'s modes added'),
    'objects_coin_money_roll_on_glass_02': ('PROCESS', 'ring_roll', 'as 01'),
    'bullets_shell_single_drop_on_stone_floor_ring_out_01': ('PROCESS', 'ring_drop', 'a small metal object bouncing '
        'with a clear ring: pitched down 4 semitones, the stone thuds low-passed: the ring falling'),
    'objects_jewelry_ring_drop_into_glass_jar': ('PROCESS', 'ring_drop, ring_hand', 'only the first 40 ms (the '
        'ring\'s own tick); the glass jar\'s ring is gated out'),
    'ring_drop_into_glass_jar_02': ('PROCESS', 'ring_hand', 'as above: tiny metal ticks'),
    # wood drags, books, music boxes
    'chair_stool_drag_hard_floor_03': ('PROCESS', 'wet_drag', 'a stool scraping: slowed 0.7x and low-passed under a '
        'wet cloth layer: something heavy dragged over the kitchen floor'),
    'chair_wooden_drag_hard_floor_06': ('PROCESS', 'wet_drag', 'a short scrape grain (as above)'),
    'objects_furniture_chair_wooden_drag_hard_floor': ('PROCESS', 'wet_drag', 'a groaning chair drag: low-passed'),
    'objects_furniture_chair_wooden_with_floor_protectors_drag_on_wood_floor_02': ('USE', 'wet_drag', 'a soft, heavy '
        'drag on wood (88 % < 250 Hz): the main body of the drag'),
    'objects_book_flip_page': ('USE', 'page_flip', 'one page'),
    'objects_book_small_book_flip_page': ('USE', 'page_flip', 'eight page flips of a small book: the diary'),
    'musical_toy_music_box_winding_up_several_times': ('USE', 'music_box_wind', 'the winding ratchet'),
    'clocks_chime_antique_music_box_melody': ('REJECT', '-', 'a music box playing another melody: in this film every '
        'music box plays the Pemberton\'s jingle (synthesised in audio/jingle.py; this file was its timbre reference)'),
    'toys_mechanical_wind_up_music_box': ('REJECT', '-', 'a toy mechanism playing another tune (97 % > 4 kHz)'),
    # voices
    'voices_crying_boy_3_years_old_cry_02': ('REJECT', '-', 'a three-year-old BOY: the owner said so; the girl\'s '
        'crying through the door is built from the voiceover\'s own girl voice (sfx.py girl_cry)'),
    # ---- music
    'break_the_fast_vision_heat': ('REJECT', '-', 'a funk groove at 112 bpm in F# (I-IV vamp), mastered hot (3,859 '
        'clipped samples, true peak +2.2 dB): the parade\'s music is the Pemberton\'s jingle from the float\'s PA, and '
        'a second tune in another key under it fights it'),
    'el_matador_harley_rain': ('REJECT', '-', 'a Spanish-flavoured vamp (B-F#-E-A, 103 bpm), 213 clipped samples: no '
        'scene for it'),
    'the_king_of_prince_street_vision_heat': ('REJECT', '-', 'a beat track at 129 bpm (G#/F# vamp), 1,531 clipped '
        'samples: no 1987 small-town sound, and it would fight the jingle'),
    'the_squad_flickering': ('REJECT', '-', 'an action track at 161 bpm in A minor, 3,471 clipped samples (runs of 13)'),
    'mary_had_a_little_lamb_lil_y': ('USE', 'music_plan IDENTITY (nursery)', 'a music-box nursery tune (98 % '
        'harmonic, centroid 750 Hz): the real Laurie\'s crayon diary ("I love Mama. I love my dog Biscuit."), '
        'varispeeded F -> D (0.84x), dragged to a halt on "And the handwriting changes."'),
    'mr_otter_s_rainy_day_lil_y': ('USE', 'music_plan IDENTITY (nursery)', 'a gentle children\'s tune in A (the '
        'film\'s second centre): June at her window ("That\'s Mister Bunny... He\'s sad."), low and soft; its MP3 '
        'stops at 16.7 kHz, fine that quiet'),
    'mermaid_s_story_jerry_lacey': ('USE', 'music_plan TRACK_MAP (outro)', 'a calm, regular harp lullaby (C major, '
        'pulse 0.92): the outro ("Okay. Breathe."), varispeeded C -> D (+2) so the jingle\'s outro follows in key'),
    'sleep_forever_luella_gren': ('USE', 'music_plan TRACK_MAP (climax)', 'a sinister lullaby (G# -> A, +1): Mom with '
        'the yellow dress ("Happy Easter, bunny...") and the hospital ending'),
    'the_cursed_path_of_everlasting_loneliness_polar_nights': ('USE', 'music_plan TRACK_MAP (reveal)', 'a slow, '
        'aching build (G major, 92 % harmonic): the real Laurie\'s thirty-six years in the woods and the recap'),
    'the_haunted_luella_gren': ('USE', 'music_plan TRACK_MAP (rules 2 and 5)', 'sparse dark piano over a thin high '
        'drone (G# minor -> A minor, +1): the egg and the attic'),
}


# ------------------------------------------------------------------------------------------------ the Bus film verdicts
# slug -> (verdict, sfx.py names / music_plan role, reason). Measured by this tool (review_measure.json) and judged by
# name; REJECT = mapped to no Bus name (epidemic_catalog.NOT vetoes the ones an older name would pick up).
BUS_DECISIONS = {
    'air_burst_bus_air_brake_compressor_no_engine': ('USE', 'bus_air_brake', 'a clean stationary release, 40 dB SNR, 75 % above 4 kHz: the hiss itself'),
    'vehicles_bus_air_brake_compressor_no_engine': ('USE', 'bus_air_brake', 'the same release, louder take (-19 LUFS), 40 dB SNR'),
    'vehicles_bus_air_brake_pass_by_slow_microphone_whip': ('PROCESS', 'bus_air_brake (reserve)', 'a passing bus with a brake squeal and a mic whip (47 % low): only its hiss phrase, never the whip'),
    'vehicles_bus_reversing_pass_by_slow_stops_air_brake': ('PROCESS', 'bus_air_brake (reserve)', 'reversing and stopping: the final brake release only'),
    'air_burst_bus_door_open_close_compressor_air': ('USE', 'bus_door', 'the door valve: a sharp air burst (centroid 6 kHz), 35 dB SNR'),
    'vehicles_bus_door_open_close_no_engine_01': ('USE', 'bus_door', 'two clean phrases (open, close), 45 dB SNR, no engine under it'),
    'vehicles_bus_door_open_close_no_engine_03': ('USE', 'bus_door', 'several open / close cycles on true silence (floor -200 dB: edited)'),
    'vehicles_bus_door_open_close_no_engine_04': ('USE', 'bus_door', 'a brighter folding-leaf take (3 kHz centroid)'),
    'vehicles_bus_interior_door_open_close_no_passengers': ('PROCESS', 'bus_door', '146 s from inside a running bus (89 % < 250 Hz, SNR 14): door phrases only, high-passed by the grain cutter'),
    'vehicles_bus_engine_idle_engine_off': ('USE', 'bus_idle', 'a steady diesel idle (150 s, harmonic 85 %); the engine-off tail is skipped'),
    'vehicles_bus_engine_perspective_idle_engine_off': ('USE', 'bus_idle', 'the idle from the engine side (893 Hz centroid: more clatter): his sick bus'),
    'vehicles_bus_long_journey_part_03_standing_still_idle': ('USE', 'bus_idle', 'standing still, idling (a low, continuous take: SNR 4 because it is all engine)'),
    'vehicles_bus_onboard_exterior_slowly_stops_idle_engine_perspective': ('PROCESS', 'bus_idle (reserve)', 'stops then idles: the idle part only'),
    'vehicles_bus_engine_start_drive_away_fade_out': ('USE', 'bus9_start, bus_pull_away, bus9_drive', 'the starter, the diesel catching, then the bus driving away (38 dB SNR)'),
    'vehicles_bus_interior_on_board_driving': ('USE', 'bus9_drive, morning_bus', 'inside a moving bus (95 % < 250 Hz): bus 9 on the road'),
    'vehicles_bus_interior_double_decker_ride_variying_speed_stops_doors_open_close_heavy_rattle_berlin': ('PROCESS', 'bus9_drive (rattle layer)', 'a Berlin double-decker (113 s): only as a low-passed rattle layer 7 LU under the drive; its doors and stops are never heard'),
    'vehicles_bus_reverse_beeps_back_up_pull_out_back_up_again_engine_off_engine_bus_at_the_end_in_background': ('REJECT', '-', 'a modern reversing alarm beeping (not in the story; it dates the bus wrong)'),
    'vehicles_generic_by_bus_pass_by_fast_asphalt_02': ('USE', 'bus_pull_away, bus_rewind', 'a fast pass-by (82 % mid band): reversed for the rewind'),
    'vehicles_generic_by_bus_pass_by_fast_asphalt_03': ('USE', 'bus_pull_away, bus_rewind', 'a shorter fast pass-by, 37 dB SNR'),
    'vehicles_generic_by_bus_pass_by_medium_speed_asphalt': ('USE', 'bus_pull_away, bus_rewind', 'a slower pass (84 % low): his bus going off down Larch Street'),
    'vehicles_horn_bus_close_long': ('USE', 'bus_horn', 'one long close blast, 72 dB SNR'),
    'vehicles_horn_bus_many_short': ('USE', 'bus_horn', 'short blasts (kind short)'),
    'vehicles_horn_bus_very_long': ('PROCESS', 'bus_horn', 'a 22 s blast (SNR 1.2: all horn); cut to length'),
    'car_brake_tire_skid_05': ('USE', 'tire_screech, bus_swerve', 'a hard skid (-10.5 LUFS, tonal 5.1: the tyre squeal); band-limited 16 kHz, fine'),
    'vehicles_skid_car_drive_depart_slip_tire_drift_screech_far': ('USE', 'tire_screech', 'a far screech (perspective for his bus)'),
    'vehicles_skid_peugeot_drive_accelerate_depart_slip_tire_drift_screech_02': ('PROCESS', 'tire_screech', 'a car accelerating while it drifts: 2 st down (a heavier vehicle), the engine kept low'),
    'vehicles_skid_peugeot_drive_accelerate_depart_slip_tire_drift_screech_03': ('PROCESS', 'tire_screech', 'as 02'),
    'metal_friction_scrape_large_loud_01': ('USE', 'mirror_rip', 'a big loud scrape, 51 dB SNR: the bumper on the mirror arm'),
    'metal_friction_scrape_large_loud_03': ('USE', 'mirror_rip', 'as 01, more tonal (2.1)'),
    'metal_friction_scrape_plate_or_panel': ('USE', 'mirror_rip (layer)', 'a lighter panel scrape'),
    'glass_break_car_window_hit_repeatedly_until_break_smash_mkh_50_02': ('PROCESS', 'mirror_rip', 'the repeated hits before the break are cut away (grains): only the smash; 3 clipped samples, inaudible'),
    'glass_break_car_window_hit_repeatedly_until_break_smash_sanken_01': ('PROCESS', 'mirror_rip', 'as above, the second mic'),
    'glass_break_car_window_break_in_smash_remove_edges_debris_interior_sanken': ('PROCESS', 'mirror_rip (debris)', 'the smash and debris; the edge-clearing (a person at work) never used; 7 clipped samples on the smash'),
    'communications_static_radio_station_search_crackling_wrong_frequency_02': ('USE', 'dash_radio', 'radio static between stations (177 s, 96 % mid band): bus 9\'s dash speaker'),
    'whistles_mechanical_sport_referee_whistle_01': ('USE', 'whistle', 'one short pea-whistle blast (2.9 kHz, 61 dB SNR): "Fweet", tuned to A7'),
    'whistles_mechanical_sport_referee_whistle_02': ('USE', 'whistle', 'blasts incl. a longer one (the long blast is looped from it)'),
    'whistles_mechanical_sport_referee_whistle_10_metres_distance': ('USE', 'whistle (far=True)', 'the whistle from 10 m'),
    'whistles_mechanical_wooden_blow_single_note_long': ('REJECT', '-', 'a wooden whistle: a flute / train tone (tonal 8.6) with a noisy floor (SNR 8.7), not his silver whistle'),
    'whistles_misc_aztec_death_whistle_blow_04': ('REJECT', '-', 'the Aztec death whistle is a human scream imitation: a cheesy library scream (brief: no cheesy screams)'),
    'whistles_misc_aztec_death_whistle_blow_05': ('REJECT', '-', 'as 04'),
    'whistles_misc_toy_blow_long': ('REJECT', '-', 'a toy slide whistle (tonal 9.1, -2.6 LUFS): comic, not his'),
    'objects_office_office_supplies_hole_punch_single': ('USE', 'ticket_punch', 'a clean punch (53 dB SNR): the click'),
    'office_supplies_hole_punch_single_02': ('USE', 'ticket_punch', 'a second punch: the clack (2 st up)'),
    'objects_office_office_supplies_hole_punch_through_multiple_pages_of_paper': ('USE', 'ticket_punch', 'through pages: a heavier click'),
    'kanex_250_paper_hole_puncher_02': ('USE', 'ticket_punch', 'a desk puncher, 69 dB SNR'),
    'paper_rip_cinema_ticket_perforated_01': ('PROCESS', 'ticket_slide (reserve)', 'a perforated ticket tearing: reserve for the yellow ticket'),
    'communications_transceiver_walkie_talkie_engage': ('USE', 'walkie (engage)', 'the PTT key, edited on silence'),
    'communications_transceiver_walkie_talkie_squelch_stuttering_glitchy_long': ('USE', 'walkie (glitch)', 'a stuttering glitchy squelch (13 kHz top): his voice on the walkie'),
    'communications_transceiver_walkie_talkie_squelch_stuttering_glitchy_short': ('USE', 'walkie (squelch, glitch)', 'short squelches'),
    'voices_futzed_ai_hitech_radio_walkie_talkie_squelch_beep': ('REJECT', '-', 'a "hi-tech AI" radio texture (6.2 kHz band, digital): modern sci-fi, wrong for 1990s kids\' walkies; the roger beep is synthesised'),
    'voices_futzed_announcement_jail_pa_system_close': ('REJECT', '-', 'a man\'s PA announcement: the recogniser hears "2609... check in at the speaker" (34 % speech): a stray voice'),
    'voices_futzed_breath_megaphone_feedback': ('PROCESS', 'pa_crackle', 'megaphone breath and feedback: the feedback phrases only (one "uh" at 42.8 s is never cut in)'),
    'communications_microphone_feedback_single': ('USE', 'pa_crackle', 'one feedback ring (tonal 8.5): band-passed into the horn'),
    'communications_microphone_speaker_feedback_resonance_tonal_harsh': ('USE', 'pa_crackle (feedback)', 'a harsh resonance, 52 dB SNR'),
    'electricity_misc_long_spring_feedback': ('PROCESS', 'pa_crackle (reserve)', 'a 91 s spring feedback drone: only a band-passed second if the PA needs more'),
    'electricity_misc_bursts_long_spring_feedback': ('PROCESS', 'pa_crackle (reserve)', 'as above, in bursts'),
    'communications_phonograph_vinyl_crackle_authentic': ('USE', 'pa_crackle (crackle)', 'crackle, high-passed 900 Hz'),
    'communications_phonograph_vinyl_crackle_01': ('PROCESS', 'pa_crackle', '98 % below 250 Hz (rumble) and 5 clipped samples: only above 900 Hz'),
    'musical_plucked_guitar_electric_od_amplified_feedback_short_pitch_bend_to_feedback': ('REJECT', '-', 'an electric guitar (an instrument, tonal 7.6): it would be heard as music in the wrong key'),
    'electricity_buzz_hum_fluorescent_light_buzz_short_power_up_light_switch_on_off': ('USE', 'power_down, power_up', 'switch, tink and buzz edges, 38 dB SNR'),
    'electricity_buzz_hum_fluorescent_light_buzz_short_soft_power_up_light_switch_on_off': ('USE', 'power_down, power_up', 'a softer take'),
    'footsteps_human_asphalt_sneaker_running': ('USE', 'run_asphalt', 'running on asphalt, 51 dB SNR'),
    'footsteps_human_asphalt_male_sneakers_running': ('PROCESS', 'run_asphalt', 'quiet (-41 LUFS) and heavy (a man): levelled, used as the second voice of the pool'),
    'animals_cat_wild_lion_growling_low_rumble_bubbly_02': ('PROCESS', 'cat_rumble', 'a lion\'s low rumble: a fourth down, low-passed 350 Hz, barely there'),
    'animals_cat_wild_lion_growling_low_rumble_bubbly_03': ('PROCESS', 'cat_rumble', 'as 02'),
    'animals_cat_wild_tiger_defensive_growling_deep_rumble': ('PROCESS', 'cat_rumble', 'deep (96 % < 250 Hz); its snarls stay under the 350 Hz low-pass'),
    'rubber_friction_latex_glove_pull_stretch_squeak': ('USE', 'glove_squeak', 'latex stretch and squeak, edited on silence'),
    'rubber_handle_surgical_glove_pull_off_stretch_squeak_slap': ('PROCESS', 'glove_squeak', 'the stretch and squeak phrases; the final slap is a grain the pool may pick (kept quiet)'),
    'user_interface_glitch_glitch_crackle_03': ('USE', 'tape_skip', 'a crackle glitch: the stutter source'),
    'user_interface_glitch_glitch_databend_04': ('USE', 'tape_skip', 'a databend (36 % > 4 kHz): sliced to 42 ms'),
    'user_interface_glitch_glitches': ('USE', 'tape_skip', 'glitch bursts'),
    'communications_audio_visual_tape_play_stop_electrical_hum_static': ('USE', 'tape_skip', 'a tape play / stop with hum and static (87 % harmonic hum)'),
    'computers_hard_drive_vintage_crt_monitor_commodore_1084s_power_on_off': ('PROCESS', 'crt_on', '98 % of the energy is the 15.7 kHz line whine (centroid 15.5 kHz): the power-on phrase only, low-passed 9 kHz; the whine is resynthesised quietly'),
    'communications_audio_visual_hifi_old_turn_on_fan_whir_turn_off': ('USE', 'crt_on (fallback)', 'an old set\'s power-on and fan'),
    'communications_audio_visual_videotape_vhs_eject': ('USE', 'vhs_tape (eject)', 'a VHS eject, 33 dB SNR'),
    'communications_audio_visual_tape_hand_camera_fast_forward_edit_mode_stop': ('USE', 'tape_ff', 'the FF whine and the stop (the owner\'s pick in the brief)'),
    'communications_audio_visual_master_tape_studer_a820_master_tape_playback': ('PROCESS', 'tape_ff (reserve)', 'a studio reel deck (SNR 3, 4 clipped samples): reserve, the hand camera is used first'),
    'communications_audio_visual_cd_case_drop_on_carpet': ('REJECT', '-', 'a CD case on carpet: wrong object and surface for the clipboard on asphalt (built instead)'),
    'games_video_sega_saturn_turn_on_loading_laser_turn_off': ('REJECT', '-', 'a game console\'s laser and loading (centroid 6.4 kHz): the TV cart is a CRT and a VCR'),
    'vehicles_mechanism_car_seat_belt_click_into_lock': ('USE', 'seatbelt', 'a belt clicked into the lock (1 clipped sample on the click: inaudible after the level)'),
    'vehicles_mechanism_car_seat_belt_click_lock_01': ('USE', 'seatbelt', 'as above (2 clipped samples)'),
    'vehicles_mechanism_car_seat_belt_click_lock_03': ('USE', 'seatbelt', 'a clean click, 67 dB SNR'),
    'metal_movement_cable_clanking_post_flag_flapping_02': ('PROCESS', 'flag_rope, school_night', 'the flag cable on the pole (120 s); its flag-flap rumble (96 % < 250 Hz) is high-passed at 200 Hz'),
    'boats_sailboat_rope_clanking_mast': ('USE', 'flag_rope', 'a halyard clinking on a mast: the "flag rope, clinking"'),
    'bendy_pole_light_stretch_bend_creak_03': ('PROCESS', 'broom_bend, his_unfold', 'a pole bending and creaking (54 dB SNR): a fourth down for the broom handle, a fifth down per segment for his unfolding'),
    'wood_break_stick_branch_snap_in_two': ('USE', 'broom_crack', 'a stick snapping in two'),
    'wood_break_snapping_branches_trees_sticks': ('USE', 'broom_crack', 'snaps (edited on silence)'),
    'wood_break_panel_plywood_bend_splinter_snap_03': ('PROCESS', 'broom_crack (reserve)', 'plywood bending and splintering: too sheet-like for a broom handle; reserve'),
    'cloth_rip_t_shirt_tear': ('USE', 'cloth_rip', 'a T-shirt tearing, 0.5 s, clean: Sami\'s pajamas'),
    'cloth_rip_shorts_thin_material_tear_02': ('USE', 'cloth_rip', 'thin fabric tear'),
    'cloth_rip_tear_02': ('USE', 'cloth_rip', 'a longer tear (cut to 0.55 s)'),
    'cloth_rip_velcro_tear_long': ('REJECT', '-', 'velcro (5.8 kHz centroid, 14 s): not cloth'),
    'ambience_school_school_children_talking_shouting': ('PROCESS', 'kids_chatter (morning_bus)', 'school walla (no words heard: VAD 0 %): low-passed 4.5 kHz, under the morning bus'),
    'ambience_school_few_close_big_crowd_of_kids_background_walla': ('PROCESS', 'kids_chatter (morning_bus)', 'as above'),
    'ambience_school_kids_playground_group_of_kids_walk_by_scream': ('REJECT', '-', 'ends in a child\'s scream (brief: no library screams; a scream in a bus-safety film for kids reads wrong)'),
    'equipment_tactical_flashlight_torch_small_head_cap_unscrew': ('USE', 'mailbox_unscrew', 'a small cap unscrewing by hand (82 dB SNR): the mailbox letters\' screws'),
    'tools_power_electric_screwdriver_unscrew_screw': ('REJECT', '-', 'an electric screwdriver\'s motor whine (5 kHz centroid): Grandma unscrews by hand at midnight'),
    'deep_down_in_the_caverns_trailer_worx': ('REJECT', '-', 'a STRAY: a trailer music track (60 s, -10.3 LUFS, CLIP 156) inside the effects zip; flagged stray in the catalogue, never an SFX'),
    # music
    'through_the_portal_anthony_earls': ('USE', 'music_plan: the hook', 'dark, pulsing (bass G, pulse 0.84), no vocals (VAD 0 %): dread from the first line'),
    'terra_firma_dream_cave': ('USE', 'music_plan: rule 1', 'C# minor -> D minor (+1), 91 % < 250 Hz, steady pulse'),
    'can_they_see_us_experia': ('USE', 'music_plan: rules 3 and 7', 'dark (bass D# -> D, -1), percussive (harmonic 71 %); 64 clipped samples on decode: levelled down'),
    'chronometer_guy_copeland': ('USE', 'music_plan: 2:58 -> 3:00', 'a ticking build (pulse 0.885), E minor -> D minor (-2)'),
    'all_exits_closed_guy_copeland': ('USE', 'music_plan: the chase', 'D, driving (pulse 0.87); its 68-81 s drop is skipped (offset 32 s)'),
    'the_last_horizon_aerian': ('USE', 'music_plan: the warm turn', 'D major (0.93), quiet start then a swell at 48 s placed on the porch light; 294 clipped samples: levelled'),
    'at_first_light_gavin_luke': ('USE', 'music_plan: the morning', 'A major, gentle (-18 LUFS), no vocals'),
    'a_sky_unveiled_megan_wofford': ('USE', 'music_plan: rule eight', 'F major -> D major (-3), warm; 32 clipped samples'),
    'wait_for_me_on_the_other_side_instrumental_version_clngr': ('PROCESS', 'music_plan: the outro tips', 'G major, bright and loud (-9.5 LUFS, 2.4 kHz centroid, 2306 clipped samples on decode): -6 dB and flattened so it never sits on the voice; VAD 3.7 % = no words recognised (instrumental)'),
    'just_a_little_sunshine_instrumental_version_staffan_carlen': ('PROCESS', 'music_plan: the short outro', 'D major, bright (-9 LUFS, 2.3 kHz centroid, 5377 clipped samples): -7 dB, under the call to action only; no vocals'),
    'sweeter_clean_version_blood_harmony': ('REJECT', '-', 'a SONG WITH VOCALS: the recogniser hears its lyrics (84.7 % speech: "You\'re driving me mad...") -- music with vocals never plays under the narration'),
}
DECISIONS = BUS_DECISIONS


def write_md(res):
    """W/mix/sfx_review.md from the measurements and DECISIONS."""
    out = ['# The owner\'s new Epidemic files (the Bus film): review', '',
           'Every file of `_work/samples/epidemic_bus` (the bus set: 98 effects, 11 tracks; the earlier sets were '
           'judged in their own films) was measured by '
           '`audio/review_sfx.py` (loudness, peaks and clipping, noise floor, spectrum, codec low-pass, onsets, '
           'harmonic share, tonal clarity, stereo, and for crowds / voices / hospital ambiences the speech share and '
           'what a recogniser hears) and looked at as a spectrogram with its envelope (`_work/mix/review/sheet_*.png`). '
           'Verdicts: **USE** as recorded (cut into grains, levelled, placed in a space), **PROCESS** only after the '
           'processing named, **REJECT** never used (mapped to no Bus SFX name; `epidemic_catalog.NOT` also keeps the '
           'older names from picking a rejected file up). Licence: the owner\'s Epidemic subscription (the files stay '
           'in `_work/samples`, never copied or committed).', '']
    for kd, title in (('sfx', 'Effects'), ('music', 'Music')):
        rows = [(k.split(':', 1)[1], v) for k, v in res.items() if v.get('kind') == kd]
        n = {d: sum(1 for s, _ in rows if DECISIONS.get(s, ('?',))[0] == d) for d in ('USE', 'PROCESS', 'REJECT')}
        out += [f'## {title}: {len(rows)} files, {n["USE"]} use, {n["PROCESS"]} process, {n["REJECT"]} reject', '',
                '| file (slug) | verdict | feeds | measured | why |', '|---|---|---|---|---|']
        order = {'USE': 0, 'PROCESS': 1, 'REJECT': 2}
        for s, v in sorted(rows, key=lambda r: (order.get(DECISIONS.get(r[0], ('?',))[0], 3), r[0])):
            d, feeds, why = DECISIONS.get(s, ('UNDECIDED', '-', 'not reviewed'))
            meas = (f"{v['dur']} s, {v['lufs']} LUFS, pk {v['peak_db']}, floor {v['floor_db']}, cen {v['centroid_hz']} Hz, "
                    f"L/M/H {'/'.join(str(round(x)) for x in v['low_mid_high_pct'])} %, tonal {v['tonal_clarity']}"
                    + (f", clip {v['clipped']}" if v.get('clipped') else '')
                    + (f", speech {v['speech_pct']} %" if 'speech_pct' in v else ''))
            out.append(f'| `{s}` | **{d}** | {feeds} | {meas} | {why} |')
        out.append('')
    return '\n'.join(out) + '\n'


def main():
    if '--md' in sys.argv:
        res = json.load(open(os.path.join(OUT, 'review_measure.json')))
        p = os.path.join(W, 'mix', 'sfx_review.md')
        extra = open(p + '.notes').read() if os.path.exists(p + '.notes') else ''
        open(p, 'w').write(write_md(res) + extra)
        print('wrote', p); return
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    kind = 'all'
    if '--kind' in sys.argv:
        kind = sys.argv[sys.argv.index('--kind') + 1]
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    do_asr = '--no-asr' not in sys.argv
    os.makedirs(OUT, exist_ok=True)
    pj = os.path.join(OUT, 'review_measure.json')
    res = json.load(open(pj)) if os.path.exists(pj) else {}
    for kd in (('sfx', 'music') if kind == 'all' else (kind,)):
        files = sorted(f for f in os.listdir(os.path.join(SET, kd)) if f.lower().endswith(('.mp3', '.wav')))
        if only:
            files = [f for f in files if only in slug(f)]
        per = 6
        for si in range(0, len(files), per):
            fig = plt.figure(figsize=(16, 2.0 * per), dpi=100)
            gs = fig.add_gridspec(per * 3, 1, hspace=0.9)
            todo = files[si:si + per]
            if '--resume' in sys.argv and all(f'{kd}:{slug(f)}' in res for f in todo):
                plt.close(fig); continue
            for j, fn in enumerate(todo):
                sl = slug(fn)
                r, m, rdb = measure(os.path.join(SET, kd, fn))
                if do_asr and (kd == 'music' or any(w in sl for w in ASR_WORDS) or 'epidemic sound' not in fn.lower()):
                    r['speech_pct'], r['asr'] = asr(m if kd == 'sfx' else m[:SR * 150])
                res[f'{kd}:{sl}'] = dict(r, file=fn, kind=kd)
                print(kd, sl, json.dumps({k: v for k, v in r.items() if k != 'asr'}), flush=True)
                if r.get('asr'):
                    print('    ASR:', ' | '.join(r['asr'])[:600], flush=True)
                ax = fig.add_subplot(gs[j * 3:j * 3 + 2, 0]); ax2 = fig.add_subplot(gs[j * 3 + 2, 0])
                strip(ax, ax2, m if kd == 'sfx' else m[:SR * 240], rdb if kd == 'sfx' else rdb[:20 * 240],
                      f"{sl[:110]}  |  {r['dur']} s, {r['lufs']} LUFS, pk {r['peak_db']} (TP {r['true_peak_db']}), floor "
                      f"{r['floor_db']} SNR {r['snr_db']}, cen {r['centroid_hz']} Hz, L/M/H {r['low_mid_high_pct']}, "
                      f"lp {r['codec_lowpass_hz']}, tonal {r['tonal_clarity']}, harm {r['harmonic_pct']}%"
                      + (f", speech {r['speech_pct']}%" if 'speech_pct' in r else '') + (f", CLIP {r['clipped']}" if r['clipped'] else ''))
            fig.savefig(os.path.join(OUT, f'sheet_{kd}_{si // per + 1:02d}.png'), bbox_inches='tight')
            plt.close(fig)
            json.dump(res, open(pj, 'w'), indent=1)
    print('wrote', pj)


if __name__ == '__main__':
    main()
