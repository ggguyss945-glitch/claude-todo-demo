# Hook API sheet

The exact APIs the phase-1 builders delivered, copied from their reports. Engine details: engine/anim/README.md. Shot plan: docs/HOOK_BOARD.md.

## Audio library (audio/lib.py, sfx_map.json, music_map.json)

### API

Python (import sys; sys.path.insert(0,'/home/user/claude-todo-demo/whatif-settings/audio'); import lib). Run any script that reads the scratch media with python3 -I (set PYTHONDONTWRITEBYTECODE=1 if you like).
- lib.SR = 48000; lib.REF_LUFS = -18.0; lib.PEAK_CEIL_DB = -1.0; lib.CACHE (override with env WHATIF_EPIDEMIC_CACHE); lib.CACHE_MAX_S = 12.0 (longer beds are sliced from an in-process decode, not cached on disk).
- lib.load_sfx(name:str, variant:int=0, apply_gain:bool=True) -> np.float32 (n,2) at 48 kHz. Returns the trimmed clip with raised-cosine fades (fade_in_ms/fade_out_ms from the entry) and gain_db applied. variant is taken modulo the number of variants, so cycling i gives a different sound per repeat.
- lib.load_music(track_key:str, t0:float|None=None, t1:float|None=None, fade_ms:float=0.0) -> np.float32 (n,2) at 48 kHz. Times are seconds on the decoded clock. No gain is applied. Values can exceed 1.0 (MP3 overs up to +1.3 dBFS), so apply gain before any clipping stage.
- lib.info(name) -> a sfx_map entry (each variant gets 'src' library metadata), a music_map track, or a library.json file entry.
- Also available: lib.sfx_names(), lib.variants(name), lib.library(), lib.sfx_map(), lib.music_map(), lib.decode(path)->(n,ch) float32 via ffmpeg, lib.to_stereo(x), lib.loudness(x)->{i,m_max,w200_max,ungated}, lib.true_peak_db(x), lib.peak_db(x), lib.prune_cache()->int, lib.selftest(verbose)->{sfx_ok,sfx_fail,music_ok,music_fail}.

sfx_map.json: {_meta:{ref_lufs,peak_ceiling_dbtp,gain_rule,times,...}, <name>:{desc, hook:bool, n, variants:[{file:<library key>, take:int|[i,j]|null, t0, t1 (s in source), fade_in_ms, fade_out_ms, dur_ms, onset_ms, peak_ms, tail_ms, sync:'onset'|'peak', sync_ms, lufs_200, lufs_i, true_peak_dbtp, gain_db, peak_limited, loop:bool, glide?:{f_start,f_mid,f_end,octaves,shape}, notes?, src_name}]}}.
Names (75): ui_tap ui_select ui_confirm ui_back slider_tick slider_drag toggle notif_ping success_chime error_buzz popup_whoosh glitch phone_vibrate typing low_battery data_loop countdown_beep padlock stamp power_down whoosh_short whoosh_long swish sub_boom impact_hit bass_drop riser reverse_cymbal record_scratch tape_stop fast_forward vhs_rewind glass_crack glass_break bonk boing slide_whistle_up slide_whistle_down cartoon_pop zip magic_shimmer fanfare siren alarm_tone clock_tick clock_tick_loop crickets_night morning_birds yawn snore footsteps door_slam crowd_gasp cheer duck_quack cat_meow cat_purr fridge_open mug_down spoon_bowl cereal_pour kitchen_amb cafeteria_amb school_bell alarm_clock_ring chalk pencil_scribble bubbles splash sad_trombone villain_sting tension_sting crowd_panic freeze_crackle march_band.
Placement rule: put sync_ms on the picture frame (start the clip at frame_time - sync_ms/1000).

music_map.json: {_meta:{methods...}, hook:{a_cold_open|b_bedroom_213am|c_welcome_brightness|d_day1_slam: {lines, first:{track,use:[t0,t1],why,edit}, alternates:[{track,use,why}], tradeoff?}}, slots:{1_cold_open_flash_forward..9_ending_and_twist, unused}, tracks:{<key>:{file,title,artist,duration_s,n_samples,tags{genre,mood,bpm_tag,energy,isrc},bpm,bpm_tag,bpm_feel,beat_period_s,grid_t0_s,grid_resid_ms,grid_on_frac,meter,bar_s,downbeat_t0_s,downbeats_grid[],beats_tracked[],key,key_r,key_alt,lufs_i,true_peak_dbtp,loud_median_lufs05,loudness_05s[] (one value per 0.5 s),intro_quiet_until_s,outro_quiet_from_s,sound_ends_s,sections[{t0,t1,dur,bars,lufs,lufs_rel,centroid_hz,onsets_per_s,pulse,key,key_r}],novelty_peaks,energy_jumps[{t,delta_db,kind}],hits[{t,strength,onset_z,jump_db,low,lufs_after}],stops[{t,gap_s,depth_db,reenter}],loops[{bars,t0,t1,seam_sim,level_diff_db}],timbre{...},character,notes,edit_points{name:[onset,peak]|t},unused}}}.
Track keys: power_pulse alleyways_of_seoul conquerors_of_space gotta_catch_that_unicorn mr_payne our_last_stand an_afternoon_at_the_versailles buster fat_and_muscles gavotte_des_papillons loser no_dessert take_me_to_prom tree_house_story 12_o_clock_magic average_duck_face college_dropout national_anthem_germany_christmas_version trapped_outside unfettered_and_unchained.

library.json: {_meta:{...}, files:{'<folder>/<slug>': {key,name,path(abs, scratch raw/),rel,zip,kind,category,descriptors[],title,md5,duplicate_of,codec,bitrate,sample_rate,channels,duration_s,duration_probe_s,n_samples,lufs_i,lufs_m_max,lufs_200_max,true_peak_dbtp,sample_peak_dbfs,clip_runs,noise_floor_db,first_onset_s,main_peak_s,tail_s,end_of_sound_s,centroid_hz,cls(music|one_shot|multi_take|bed), [sfx:] active_frac,seg_thresholds_db,n_takes,takes[{i,t0,t1,t1_tail,dur_ms,peak_db,lufs_200,lufs_ung,peak_s,centroid_hz,glide?}],takes_truncated,take_spacing_median_s,dropouts[[t0,t1]], [music:] artist,tags}}}.

### Open issues and notes from the builder

- No stems in the music downloads, so the planned 'drop a layer on punchlines' cannot be done. Drops are hard cuts of the full mix, with slam-backs on grid downbeats.
- Missing for the hook (details and substitutes are in docs/CUE_PICKS.md): paper page flip and riffle, dog bark/growl, sun-flare or camera-flash 'whoomp', shockwave whoosh, a true tape stop, counter-roll ticks, sweat-drop bloop, space air/drone, a kid yawn (the library yawns are adult male), and the cartoon dizzy birds the bible asks for after bonks. Recommendation: the owner downloads 'small dog bark' and 'big dog woof' from Epidemic. The rest can be synthesized by the SFX/mixer owner.
- Missing for the rest of the video: leaf blower, light wind/snow, a real quirky bassoon/tuba march (the march_band SFX or Trapped Outside stand in), and an eerie synth sting (12 O'Clock Magic reprise or the tension_sting SFX stand in).
- Trade-off: hook slot (c) uses the chiptune Gotta Catch That Unicorn, so Day 5 must use Alleyways of Seoul or Conquerors of Space. If the orchestrator prefers acoustic comedy for (c), the measured alternate is Tree House Story 10.6-32.5 (entry at 11.11).
- 12 of the 20 music masters decode with inter-sample overs above 1.0 in float (no flat-top clipping). The mixer must apply music gain before any clip or limit stage.
- library.json paths and the decoded cache are absolute paths into the scratch folder (raw/ 140 MB, cache/ 130 MB, qa/ 49 MB; about 320 MB in total, under the 600 MB budget). If scratch is wiped, re-extract the zips into raw/<folder> exactly as before (sfx_a, sfx_a_ui for the nested zip, sfx_b, mus_a, mus_b, mus_c). Folder names and keys must match; ingest.py and build_sfx_map.py regenerate everything else.
- The analysis and builder scripts live in scratch, because I only own the listed repo files. To make this reproducible, the orchestrator may want to copy scratchpad/settings/epidemic/scripts/{ingest,music_an,build_sfx_map,build_music_map,gridfit,hits}.py into the repo (e.g. whatif-settings/tools/epidemic/).
- Downbeat phase was hand-verified only on the picked cue regions: Our Last Stand, Gotta Catch That Unicorn and Average Duck Face, where hits land on grid downbeats. Gavotte des Papillons is rubato (56% of beats on the grid) and Unfettered sits at 80%, so follow beats_tracked for those two.
- Some loops cut from continuous beds contain natural pauses: the typing beds have about 0.3 s dips, and footsteps run on stairs. The vhs_rewind beds are a steady whirr; for an accelerating scroll-back, the mixer should pitch them up or add a whoosh.
- One Epidemic snore file's name mentions a cartoon character (sfx_map snore variant 3). Prefer the human snore variants 0-2.
- Nobody has listened to any of this. All picks rest on measurements, Epidemic's own tags and my visual inspection of spectrograms.

### Metrics

Library: 201 files = 181 SFX (33 mono) + 20 music, about 4816 s of audio, all MP3 at 48 kHz. ffmpeg gapless decode is 24-47 ms shorter than the MP3 header duration. Ingest takes 126 s; music analysis takes 10-20 s per track. Class counts: one_shot 55, multi_take 85, bed 41, music 20.
SFX map: 75 names (56 flagged for the hook), 276 variants. lib.selftest: 276/276 SFX OK and 20/20 music OK in 32 s. Every clip lands at -18.0 LUFS on its loudest 200 ms (or integrated for loops), with true peak at or below -1 dBTP. Cache is 130 MB (24-bit WAV, native channels, clips up to 12 s).
Tempo: the grid fit matches the Epidemic tag within 0.02 BPM on 18/20 tracks (e.g. Our Last Stand 130.010, Average Duck Face 120.014, Gotta Catch 149.995, 12 O'Clock Magic 64.987). Grid rms deviation is 6-20 ms.
Keys: Our Last Stand D minor (r 0.71), 12 O'Clock Magic C minor (0.80), Gotta Catch E major (0.91), Average Duck Face C major (0.81).
Music loudness (integrated): -9.1 (Gotta Catch) to -15.6 LUFS (Loser).
Hook edit points [onset, peak] in seconds: Our Last Stand hits [0.80, 0.875], [6.425, 6.495], [7.38, 7.455], [8.28, 8.355]; cut to drone 15.60; riser 18.78-19.35; slam [19.395, 19.455]. 12 O'Clock Magic first note 0.315, layer enters 15.145. Gotta Catch groove downbeat 2.392. Average Duck Face downbeat 8.87. Unfettered hits every 2.775 s from 27.685.

## Animation engine (engine/anim, tools/render.js) - full API in engine/anim/README.md

### API

Full contract: /home/user/claude-todo-demo/whatif-settings/engine/anim/README.md. Key points:
TIMELINE T = {fps:60, dur, bg?, modules:['shots/hook.js'] (relative to engine/; every exported fn not starting with _ is registered under its name), shots:[{name, use?, start, end, p?, capY?:'mid'|'face'|'pov'|px, tin?|tout?:{type:'cut'|'whip'|'flash'|'glitch'|'zoomThrough'|'dipBlack'|'cardSlam', dur, dir?, rect?, ...}}], voice:{lines:[{id, role, start(global s), dur, file, text, words:[{w,t,d}|{w,t0,t1}], visemes?:[[t,'v_A'|'A'|...|null]]}]} (times relative to line start = audio/voice_lines.json entries plus `start`; no visemes -> autoVisemes from spelling), captions:[{t0,t1,markup:'..{WORD|orange}..', mode?:'normal'|'type'|'scream'|'quote', y?, size?, cps?}], overlays?:[{t0,t1,use:'flash'|fnName,p}]}.
SHOT: export function name(ctx) -> svg string (screen space, must accept t outside 0..dur). ctx = {t,u,dur,gt,fps,frame,p,shot,name,start,end,T,W,H, line(id)->{start,end,words:[{w,t0,t1}],visemes,word(k,n),at(k,n)} (local s), lines(role), mouth(who,t?), talking(who,t?), word(who,t?), cam(o), actor(id,o), actorState(id,o), rng(s), rand(a,b), noise(x,s), seg(a,b), at(v), memo(key,fn), portal([x,y,w,h,r]), cue(name, atLocal, o?), bake(...)}.
ACTOR o: x,y,s,facing (FACINGS names or deg), pose (object | pose keys [[t,{armR..},ease='outBack',dur=6f]]; anticPose(t,from,to) from anim/actor.js), face (preset | object | step keys [[t,face,accent?]] with 3-frame squash accent), talk (role|line id), look|lookAt, blink (default on, 4-6 frames, global time), saccade, nervous, panic, idle, overlap, squash [[t,amt]], lurch [[t,k]], ground, add, props, opacity, seed.
CAMERA ctx.cam({keys:[[t,{x,y,z,r},ease]], push, drift, dolly, punch:[{t,k,at,in,settle,keep}], shake:[{t,amp,decay,freq,rot}], blur:'auto'|false, ghost:'auto'|false|N}) -> cam.set(set,{insert:[{after:'mid'|'light'|..., svg, depth}], only, skip, bake}), cam.layer(svg,depth), cam.render(layers), cam.screen(svg,{shake}), cam.toScreen/toWorld, cam.state. Snap zoom = hold key then a key 6-8 frames later with 'outExpo'. frameOn([x,y], z, [sx,sy]) in camera.js.
CAPTIONS (timeline builder): captionsFromLine(line{start global, dur, words}, markupText, {lead:3 frames, maxWords:3, tail:0.25, mode, y, until}) in anim/captions.js.
PAGE: engine/anim.html?timeline=<url>&px=WxH -> window.renderAt(t) (async, returns error text or ''), window.svgAt(t), window.cues(), window.__ready, window.__error.
CLI: node tools/render.js <timeline.json> <out.mp4> [fps=60] [workers=4] [scale=1.3333333|2] [from=s] [to=s] [chunk=300] [crf=15] [preset=medium] [audio=wav] [bake=1] [keep=1] [errors=ignore]  (work dir <out>.parts with progress.json; re-run resumes); stills: node tools/render.js <tl> <out_dir> times=1.2,3.4|times.json [scale=0.5] [ext=png]; cues: node tools/render.js <tl> <cues.json> cues=1 -> [{t,cue,shot,...}]; sheet: python3 -I tools/sheet.py <tl> <video|frames_dir|render> <out.jpg> [--times a,b] [--cols 3] [--width 640] [--shots a,b].

### Open issues and notes from the builder

- Encoding is the bottleneck at the required settings (x264 preset medium, crf 15, 1440p): drawing alone runs at 13-15 fps, but the whole render only reaches about 5 fps. For quick previews use preset=fast or scale=0.5.
- Static-layer baking (bake=1 plus cam.set(set,{bake})) works but is slower on our sets: 206 vs 77 ms/frame, and slightly softer (mean difference 1.1 levels). It is off by default. Keep it for future layers with heavy filters only.
- Whip transitions are still quite blurred at peak speed. The reference's bell-shaped c2 whips have crisp art plus speed lines; use tin {type:'whip', blur:false} for those.
- The ghost and blur thresholds (25 px/frame on the frame corners for zooms, 30 px/frame at the centre for pans) are eyeballed, not measured on the reference.
- Blinks follow the task's 4-6 frames, not the bible's 3. Blinks are on by default, also on deadpan 'half' eyes; set blink:false where a stare must not blink.
- The voice task's audio/voice_lines.json entries need a global `start` added when the phase-2 timeline builder puts them on the timeline. Their {w,t,d} words and null-terminated visemes are supported as they are.
- zoomThrough has only been tested with an explicit tin.rect. A shot that wants it to follow a prop (for example the phone screen) must call ctx.portal(rect) in screen space.
- ctx.cue() is collected by drawing each shot once at its start, so call it unconditionally (not inside if(t > x)).
- No files outside my ownership were changed. The orchestrator's checkpoint commit d41b75a already holds part of this run's edits. The rest are uncommitted: README.md (untracked), captions.js, frame.js, transitions.js, render.js, sheet.py.

### Metrics

JS per frame: 3.5 ms; SVG average 138 KB. toon(): sam 1.28 ms, lily 1.04, mom 1.16, dad 0.82, pickles 0.27. Set build: kitchen 3.4 ms, street 4.3, bedroom 1.4 (memoise).
Demo at 2560x1440 60 fps, 4 workers, 408 frames (6.8 s): drawing 30.7 s (75 ms/frame wall, 13.3 fps); total with encoding 78 s (about 5.2 fps). Projected 60 s hook (3,600 frames): about 12 min. Single-worker capture: street 221 ms, whip 376 ms, kitchen 115 ms per frame, of which JPEG encoding is about 50-70 ms.
Baking: 206 vs 77 ms/frame (street range). Frames: about 546 KB JPEG q95 at 1440p, so a 300-frame chunk is about 160 MB and at most about 330 MB of frames sit on disk. Video: demo.mp4 14.0 MB for 6.8 s (crf 15, High, yuv420p, BT.709, 408 frames). 4K: scale=2 gives 3840x2160 (checked on a still).
Determinism: node 12/12 out-of-order re-renders identical, page vs page 7/7, page vs node 7/7.
Motion scan: 0 still frames; diff spikes only at f57 (face swap), f124 (ONE punch/lurch), f291 (champ punch), f331-335 (snap zoom), f355/f363 (card slam and white hit).
Resume after SIGTERM: 408 frames, within 0.1-0.3 levels of the full render (encoder noise).
Scratch disk used: 31 MB of the 700 MB budget; 3.4 GB free.

## Cast (engine/cast.js etc.)

### API

toon(id, {x, y, s, facing, pose, face, look, add, props, shadow,  // unchanged
  outfit:'pyjamas' (dad), mannequin:0..1 | variant:'default', legs:false,
  tint:{color, k, mode?:'multiply'|'screen'|'mix'}  // default mode: screen if color L>0.8, else multiply
  light:{color='#CFE8FF', k, from:'below'|'phone'|'left'|'right'|'above'|'front'|[x,y], r?}, lod? (dog)})
These keys also work inside add:{} (e.g. add:{mannequin:1, light:{k:.8, from:'phone'}, legs:false}), so actor.js can pass them today.
Presets used in the QA sheet: night {tint:{color:'#5562A4',k:0.55}, light:{color:'#CFE8FF',k:0.85,from:'phone'}, props:{R:'phoneBack'}}; sun {tint:{color:'#FFF3DC',k:0.16}, light:{color:'#FFF8E0',k:0.5,from:'left'}}.
Lip-sync: face:{preset:'scared', mouth:'v_A'} (v_closed v_small v_E v_A v_O). Eyes, brows and add-ons come from the preset; the preset's m/mouthDX/DY/Tilt are dropped. Works in every facing, during morphs too, and with actor's resolved faces.
Morph: face:{preset:'starstruck', to:'scared', k:0..1}; k may come from a time function via actor face:(t)=>({...}).
New face presets: squint, ish, forcedGrin, shout, blank. Sweat: add:{sweat:1, sweatK:0..1 (slide 20 + grow x1.4), sweatSize}. Tongue: face.tongue or pose.tongue (0..1.5).
Exports from cast.js: CAST_IDS (adds 'tiny'), HUMANS, DOG_FACES, wag(t, hz=2.5, amp=1), posePreset(name, id, o) for 'shrug'(o.k) | 'shieldEyes'(o.side) | 'phoneUp' | 'phoneChest' | 'phoneLap' | 'bedSit' | 'yawnStretch' | 'yawnCover' | 'pointUp', POSE_NAMES, reach(id, 'L'|'R', [x,y], {facing, shrug, elbow:'out'|'in'}) -> {arm, fore}, headPoint(id, [hx,hy]), toonHipY(id), toonHeadY(id, {posture, facing, pose}).
New prop: 'phoneBack'. New human pose key: shrug 0..1.
Tiny: toon('tiny', {posture:'sit'|'stand' (default sit; or pose.sit 0/1), facing, face, pose:{wag, tail, ears|earL|earR, flop, tongue, head, headTurn, pawL, pawR, legFL, legFR, legHL, legHR, lean, bob}, lod}). Reads as a small dog at about 0.8x a human's s.
Bed placement: toon('sam', {legs:false, y: hipLine - toonHipY('sam')*s, pose: posePreset('bedSit','sam'), props:{R:'phoneBack'}, ...night}).
style.js (new): withFx, noFx, fxTint, fxMannequin, fxLightMask, fxDef, fxColor, composeFx, mannequinColor, MANNEQUIN, LINE_COLORS, isLineColor. tone(), stroke() and oklch() are now memoised (same output).
Render: node tools/render_still.js sheets/hook_cast.js renders/hook_cast.png 2; sheets/hook_visemes.js the same way.

### Open issues and notes from the builder

- Requests for the engine owner (engine/anim/actor.js, which I do not own): (a) pass outfit, mannequin, variant, tint, light, legs and lod through to toon() as top-level options, evaluated with val() or stepOrVal(); today they only work inside add:{}. (b) Add an idle tail wag for Tiny next to the pickles line, e.g. if (id === 'tiny') pose.wag = (pose.wag || 0) + idle * 0.5 * Math.sin(2*Math.PI*2.2*gt + ph(5)). (c) BLINKABLE already covers squint, so the new 'squint' and 'ish' presets blink fine.
- The orchestrator's checkpoint commit eb81f5d included my scratch sheets engine/sheets/_wip.js, _wip2.js and _wip3.js. I have deleted them from the working tree; please commit the deletions.
- For the sets owner: the bedroom blanket should cover Sam from about 20 px below his hip line (y = hipLine - toonHipY('sam')*s) up to the chest. legs:false draws no legs and no contact shadow. The night grade on characters is meant to be the tint preset {color:'#5562A4', k:0.55}, the same family as the bible's #3A4C70 / #5562A4 violet night.
- For the UI owner: the Day 7 'DEFAULT' tags are not drawn by cast.js. Anchor them to toonHeadY(id)*s above the feet.
- Known look limits: the sun-blow-out Dad is pale by design; phone light lights the face evenly (no modelling); Tiny's collar is a front-facing band even in profile; standing-front Tiny shows little body under the big head. Back facing is not modelled for Tiny (it clamps to side).
- hook_visemes.png is 3 MB and stays in scratch (qa/), not in renders/. Copy it to renders/ if the team wants it as a reference sheet.

### Metrics

toon() ms per call (node, warm mean of 300, cold first call in brackets): sam 0.91 (8.7, JIT), lily 0.53, mom 0.53, dad 0.33, pickles 0.13, briggs 0.32, kevin 0.35, tiny sit 0.17, tiny stand 0.19, tiny s6 0.22, mom mannequin 0.61, dad mannequin 0.5 0.35, dad pyjamas shield 0.41, sam night-lit (tint + light mask) 1.08, sam morph 0.58, sam viseme side 0.36. Before this work Sam warm was 1.68 ms. Regression: 7 old renders re-rendered, 0 px differing from HEAD-code renders. Output is deterministic (identical strings on repeat), and mannequin:0 equals the plain build. hook_cast.png 3840x2160, 2.9 MB. Disk use: about 3 MB in renders/ and 17 MB scratch QA (budget 200 MB).

## Voices (audio/voice_lines.json, voice_lab.py, voice_ingest.py)

### API

voice_lines.json: a list sorted by id. Each entry is {id, role, tag, text, file (absolute path of the 48 kHz mono 24-bit wav), dur (s), approach (text), words:[{w, t, d}], visemes:[[t, name]], metrics:{...}}. Times are seconds from the file start. w is the script spelling without punctuation.

Visemes are names from engine/face.js VISEMES: v_closed, v_small, v_E, v_A, v_O. Only change points are listed. null means leave the word window and fall back to the expression mouth; every list ends with null. Word windows less than 0.12 s apart are merged. Each shape is held 3-8 frames at 60 fps.

Selected metrics:
- asr, word_acc, asr_hits (1-2 word lines only);
- f0_med, f0_p10, f0_p90, std_st, range_st, move_st, tail_st, fry_tail, f0_jumps;
- wpm_voiced, wpm_span, speech_s, span_s, pauses;
- lufs, peak_dbfs, clipped, click_frames;
- hnr_db, jitter_pct, shimmer_pct, F1-F4, formant_dF, dnsmos_ovrl, dnsmos_sig, dnsmos_bak;
- spk_sim_role, spk_sim_reg;
- lab_score {register, movement, rate, quality, intel, artifact_pen, gate, consistency, total}, lab_alternatives {approach: score}.

CLI (run as python3 -I from /home/user/claude-todo-demo/whatif-settings):
- `audio/voice_lab.py --hook` re-renders the 24 hook lines with RECIPE. `--ids S00-L006,S00-L021` re-renders chosen lines. `--scene S01` renders every line of a scene whose role has a recipe, using the role/register defaults.
- `--lab --ids ... [--lab-json f] [--approaches a1,b_psola,...]` builds and scores every candidate. `--merge a.json,b.json` re-scores and re-picks over merged lab files. `--finalize` writes the picks as final wavs and json.
- `--plots ID,ID` writes pitch-contour PNGs; `--reel` writes the audition reel; `--say "text" --role N --tag HYPE [--variant mild|mid|strong] --out x.wav` renders an ad-hoc line.
- `audio/voice_ingest.py <wav|mp3> --id ID --role ROLE --tag TAG --text "..." [--update] [--out f.wav] [--no-conform]` conforms any take (48 kHz, 30 ms handles, -20 LUFS, peak ≤ -1 dBFS), measures it, computes words and visemes, and with --update replaces that id's entry in voice_lines.json. This is how an owner's Fish Audio file drops in.

Determinism: VOICE_THREADS=1 (the default) plus the fixed Praat seed gives sample-identical re-renders.

### Open issues and notes from the builder

- Synthetic timbre remains: DNSMOS median 3.03 (range 1.98-3.47). Dad's shout is a high, strained-EQ read, not a real yell, and Sam's yawn is a pitch glide, not a yawn sound; a yawn SFX layer would help in the mix.
- S00-L008 "Ish.": only a PSOLA take at 191 Hz without Sam's formant shift was intelligible to speech recognition (6/6 decodes). Every native-prosody render and every formant-shifted render failed, so this line's timbre and pitch differ from Sam's other two lines (Sam consistency 0.69, the lowest role).
- The S00-L017 SYS cheerful line moves 5.0 st, against 1.75 st for the reference's flatter system voice. If it sounds sing-song in the mix, re-render it with --variant mild.
- The S00-L001 question rise on "menu?" did not render (the end stays flat at about 190 Hz). A fall is natural for a "what if" question, so it was left.
- The narrator's hype median is 213 Hz against the reference's 233; the register targets were kept at 205 Hz.
- 5 of the 24 takes are PSOLA and 1 is WORLD (L006). PSOLA texture on long raised vowels is not caught by our artifact proxies (HNR, clicks, F0 jumps), so check those lines first by ear.
- For the animation owner: viseme word windows less than 0.12 s apart are merged, so a closure between two words can show v_small rather than v_closed. Word edges are good to about ±40 ms (80 ms ASR time steps).
- voice_lines.json stores absolute scratch paths in 'file'. If the scratch directory moves, set VOICE_DIR and re-run --finalize.
- Untested in this lab: Supertonic (OpenRAIL-M weights), Piper libritts_r and ZipVoice (non-commercial). Pocket TTS was measured but never picked; it scored worst on every axis.
- Nobody has listened to any take; every quality claim comes from measurement. A Fish Audio pass (VOICE_LAB.md section 9) would add breath, vocal effort, a real child voice and natural high-pitch hype.

### Metrics

Lines: 24/24 delivered and pass the deliverable checks (48 kHz mono, 30 ms handles, peak ≤ -1 dBFS, -20 LUFS ±0.5, holds 3-8 frames). 103 words; 38.9 s of speech; 44.0 s of files.

Pace: 159 wpm over speech (narrator 164); 151 wpm over line spans (narrator 156). Reference: 156 while voiced, 174 inside sentences.

Pitch and quality per voice, plain Kokoro → chosen take (reference in brackets):

| voice | F0 median Hz | pitch sd st | DNSMOS | speaker consistency |
|---|---|---|---|---|
| N hype (11 lines) | 121 → 213 (233) | 2.69 → 3.70 (3.54) | 2.94 | 0.76 |
| N deadpan (6) | 120 → 115 (121) | 2.91 → 2.08 (2.00) | 3.15 | 0.71 |
| SYS (3) | 209 | 1.80 (1.75) | 3.31 | 0.83 |
| SAM (3) | 283 (330); formant spacing ~1310 Hz on the nervous line (reference kid 1392) | 4.94 (2.20) | 2.48 | 0.69 |
| DAD (1) | 263 | 4.15 | 2.66 | - |

Gates: 0 hype lines under 2 st; speech recognition word-perfect 24/24; 0 F0 jumps; 0 clipped samples.

Approaches picked: e (native) 18 lines, b_psola 5, b_world 1. Mean lab score for N hype: e_mid 0.92, b_psola 0.84, plain 0.66, Pocket 0.55.

Disk: scratch voice dir 39 MB; no models downloaded.

## Sets (engine/sets.js, sets2.js)

### API

Every set returns {w, h, layers:[{name, depth, svg}], svg}; layers[0] is 'defs'. Per-frame helpers return insert layers [{name, after, depth, svg}] that drop straight into cam.set(set, {insert:[...]}). Inserts that share an `after` are drawn in array order.

**sets.js — street**
- `street(o)`: o = {sky, cam, split, liveTree:'left'|'sam'|'kevin', night:0..1}.
  - Default layers: sky .08, far .3, mid .75, near 1 (unchanged).
  - With split: 'yard' (.75) comes right after 'mid'.
  - With night: also 'light' (.75, screen, keep live) after mid/yard, and 'grade' (0) at the end.
- `STREET` = {base 704, lawnY 698, walkY 806, curbY 864, roadY 880,
  - tiny: {x 1372, y 792, s0 0.5, s1 2.0, depth .75},
  - trees: {left|sam|kevin: {x, base, s, seed, leaf}},
  - samHouse {x 60, w 410, base 704, top 276, cx 265, cy 500},
  - kevinHouse {x 1120, w 500, top 350, cx 1370, cy 540},
  - samWindow {x 100, y 494, w 110, h 96, cx 155, cy 542},
  - lamp {x 666, y 368}}.
- Tiny: toon('tiny', {x 1372, y 792, s 0.5..2.0}), inserted {after:'mid', depth:0.75} on street({split:true}).
- `flipTree({...STREET.trees.kevin, angle:0..180, hop:px, roots:0..1, soil:seconds since roots came up, ground})` -> string with its own defs. Insert {after:'mid', depth:0.75} and pass liveTree:'kevin'.
- `nightColor(hex, k)` and `nightify(svg, k, tag)` are exported.
- SETS adds streetTiny, streetNight and bedroomSit.
- Night wide framing: cam {x -120, y -40}. House front: cam {x -660, y -30, z 1.75}.

**sets.js — streetReset**
- `streetReset(o)`: o.pct 0..100 (floored in the text), o.tint 0..1 (red grade strength, default 1), o.t, o.glitch.
- For animation: memoise streetReset({glitch:false}), skip ['sky','grade'] and insert `resetSky({pct, t})` {after:'defs2', depth:0.08} and `resetGrade({t, tint})` {after:'near', depth:0}. Apply fx.glitch in the shot, keeping blend layers out of it.
- `RESET` = {mom {x 800, y 872, s 1.04}, dad {x 1120, y 872, s 1.04} (insert after 'near'), pill {x 960, y 420, w 320, h 84} (screen box under the bar), bar {x -60, y 60, w 2040, h 290}}.

**sets.js — bedroom**
- `bedroom(o)`: o = {blanket:'sit', blanketTop, blanketX, birds: true | state, sun:0..1, clock:'2:13', phone:{x, y}}.
  - Layers: far .3, mid .75, [blanket .75 when sit], light .75, phone .75 (new, holds the phone glow), near 1, grade 0.
  - Shots baking this set should pass live: ['light','phone','grade'].
- `BEDROOM` = {sam {x 830, y 926, s 1.55, hipY 740, chestY 668, phone [839, 647]}, ceilY -70, floorEnd 1600, window {x 1250, y 110, w 470, h 420}, moon {x 1595, y 220, r 62}, birds [[1322,400,1], [1400,400,1], [1572,395,-1]] (feet, dir), clock {x 325, y 609}, bed {x 470, w 720, top 470, mattressY 720}}.
- Sam in bed: toon('sam', {x 830, y 926, s 1.55, legs:false, pose: posePreset('bedSit','sam')}) inserted {after:'mid', depth:0.75}. The general rule is y = hipY - toonHipY('sam') * s, with toonHipY('sam') = -120.12. The 'blanket' layer then covers him to the chest.
- `bedBlanket({cx, top})` is the per-frame blanket: skip 'blanket' and insert it after 'mid', after Sam. Raise top toward the chin (about 560) for "under the blanket".
- Widest clean framing is zoom 0.7, which shows about 190 px of ceiling. Pages stacking up pass y -70.
- `bedroomSun(sun)` -> [windowSun {after:'far', depth .3}, sunlight {after:'near', depth .75}, sunGrade {after:'near', depth 0}]. Use skip ['grade'].
- `bedroomBirds(state, sun)` -> [birds {after:'far', depth .3}]. List it after windowSun.
- `birdState(sun)` -> {awake, sing, flap:[...], notes}.
- `bird(x, y, flap, {s, dir, color, belly, awake, sing, notes:t, night, seed})` -> string.

**sets2.js**
- `hallway({sun, door:0..1 default 0.22})`: layers far (end wall + Sam's door), mid, light (screen, live), near (plant), grade. All depths are 1.
  - `HALL` = {vp [960,480], zEnd 4.2, dad {x 755, y 852, s 1.7, Z 2.9}, door {x 844, y 287, w 232, h 450}, gap {x 1040, y 520}, switch {x 523, y 462}}.
  - Dad: toon('dad', {x 755, y 852, s 1.7, outfit:'pyjamas', facing:'tq-right', pose: posePreset('shieldEyes','dad',{facing:'tq-right'})}), inserted after 'mid' and AFTER the sunBack insert.
  - `hallPt([X, Y, Z])` and `hallUnit(Z)` place things in the hall: X -1..1, floor Y 1, ceiling -1.25.
- `hallwaySun(sun, {door})` -> [doorSun {after:'far'}, sunBack {after:'mid'}, sunlight {after:'near'}, sunGrade {after:'near', depth 0}]. Use skip ['grade'].
- `space({glow})`: layers sky .08, far .3 (moon), mid 1 (Earth), grade 0.
  - `SPACE` = {earth {x 860, y 610, r 390}, house {x 700, y 418} (start of the zoom-out and centre of the glow), moon {x 1610, y 250, r 96}}.
  - `spaceGlow(glow, {t})` -> [earthGlow {after:'mid', depth 1}].
- SETS2 = {hallway, space}.

**QA stills**
- node tools/render_ui_still.js stills/set_hook.js <out.png> <scale> <arg>
- arg is one of: tiny, tiny_small, tree, night, night_house, bedroom_sit, bedroom_sun (3-up), bedroom_sun5, bedroom_sun1, bedroom_wide, hallway (3-up), hallway_night, hallway_sun, hallway_sun1, space, space_0, space_zoom, reset.

### Open issues and notes from the builder

- Engine owner: camera.js defaults live: ['light', 'grade']. The new blend layers 'phone' (bedroom) and 'light' (night street, hallway) need adding to that list when bake=1, and the night street's 'near' layer contains a screen-blended lamp glow. Inserted sun layers are never baked, so they are fine.
- Shot authors: when a per-frame insert has the same after as an actor, order the insert array as windowSun, birds, then Sam for the bedroom, and doorSun/sunBack before Dad for the hallway. Pass skip: ['grade'] whenever a sunGrade insert is used.
- Sun 1 in the bedroom and hallway comes out pink-white rather than pure warm white: the dodge ramp on purple walls drifts pink. This can be tuned in bedroomSun()/hallwaySun() if the reference demands it.
- streetReset applies no glitch in cam.set (it uses layers, not set.svg). Shots must call fx.glitch themselves and keep blend layers out of it, as before.
- Not done: no dedicated close-up house-front set. The night house front is street({night:1}) framed at zoom 1.75 (outlines scale to about 5 px). Ripple anchors: STREET.samWindow, BEDROOM.sam.phone.
- The cast's posePreset('shieldEyes') hand sits near the ear rather than on the brow at facing tq-right (cast owner, cosmetic).
- QA images are kept in scratchpad settings/sets_qa (19 MB). The orchestrator can delete them after review. Disk free is 3.3 GB; my new repo renders add about 20 MB.

### Metrics

Build time per call (node): street day 8.9 ms, street night 7.7 ms, streetReset 6.9 ms, bedroom sit 4.5 ms, hallway 1.7 ms, space 1.6 ms. Per-frame helpers: flipTree 0.40 ms (14 kB), bedroomSun 0.46 ms (13 kB), bedroomBirds 0.49 ms, hallwaySun 0.14 ms, spaceGlow 0.10 ms, resetSky 0.12 ms, resetGrade 0.02 ms. Regression against the baselines: street, streetReset, kitchen, classroom and frame_kitchen have max diff 0; default bedroom differs in 5 px (max 9). Renders: set_street_tiny 3840x2160 (1.3 MB), set_street_night 3840x2160 (2.5 MB), set_bedroom_sun 7840x1700 (5.7 MB), set_hallway 7840x1700 (about 4.8 MB), set_space 3840x2160 (6.2 MB).

## UI / FX / captions (engine/ui.js, ui2.js, fx.js, caption.js)

### API

All functions return SVG strings (1920x1080 space) unless noted. p = 0..1 entry pop (omitted = settled). t = seconds. Deterministic.

engine/ui2.js (import * as U2 from '../ui2.js'):
- SCREEN {w:720,h:1480,r:88} portrait screen space (origin top-left); PHONE {w:800,h:1560,r:128,bezel:40,body:'#2E3458'}; SKIN = PAL.skinCool; CATS2 = extra categories (dog, trees, sun, bedtime, homework, birds, mondays).
- phone({x,y,s=0.6,rot,screen:svg in SCREEN space,bg:'app'|'none'|colour,glow 0..1,glowColor,glare 0..1,thumb:{x,y (SCREEN coords),press 0..1,bend,hide}|false,hand:true|false,handShift:[dx,dy],shake:px|{amp,t,freq,rot},buzz:false,crack 0..1,crackAt:[sx,sy],seed,t}). Body 800x1560 px at s=1; s 0.58-0.63 fills a frame.
- phonePoint(o,sx,sy) -> [fx,fy] frame point of a screen point. phoneScreenRect(o) -> {x,y,w,h,r} (zoomThrough portal).
- appBg(w,h,{top,bot,glow,rot,watermark}); statusBar(w,{time,k,y,color}); appHeader(w,{y,crumb,logoRot}); appScreen({time,crumb,content,header,status,bg}) (SCREEN space).
- homeScreen({time,newApp 0..1,wiggle:{t,amp},badge,glow,t}) (SCREEN space; the REALITY SETTINGS icon is the 12th slot).
- insideApp(content,{t,time,edge 0..1,glare,header,crumb,logoRot,status,bg}) full-frame "inside the app" framing.
- bigSlider({x,y(rail centre),w,v,iconL,iconR,iconLs,iconRs,color,color2,knobR=54,railH=40,endR=40,bubble,bubbleK,bubbleSize,stops,stopSize,grab 0..1,knob:'gear'|'sun',rot,ticks}); bigSliderKnob(o)->[x,y].
- settingCard({x,y,w,cat,label,icon,color,value,sub,selected,...bigSlider opts},p) h 380 (+44 with sub); settingCardKnob(o)->[x,y].
- dogSizeScreen({v,grab,bubble,treeValue}) -> {svg (SCREEN space, below the header), knob:[x,y]}; brightnessScreen({v,grab,t,night}) -> {svg,knob}.
- brightnessFull({v,t,wash,label,sub,grab}) full frame; washes white above v .7.
- appIcon({cx,cy,size,rot,spin,t,glow,badge,label,labelSize,labelColor,shine 0..1}); stays crisp at size 1500+.
- notifyCard({x,y,w=860,title,sub,note,time,rattle 0..1,t,press,badge},p) h 200.
- undoButton({cx,cy,w=460,h=156,label,tone,crack 0..1,fall 0..1,fallDist=1100,rot=38,press,seed,scale}).
- undoHistory({x,y,w=760,h=920,scroll (items, 0..418),speed (items/s),seed,sub},p); historyItems(seed) (419 items: 7 day headers + 412 changes, newest first, HIST_DAY_COUNTS=[12,40,55,60,70,95,80]); historyDayAt(day) -> scroll index of that day's header.
- counter({x,y (top-left),value (float),digits=3,label,speed (units/s)},p); counterSize(o)->{w,h:276}.
- fanMontage({cx,p,count=16,seed,spread,scale=0.78,pivotY=1560}).
- pageStack({cx,base (floor y),n,w,th=0.25 px/page,wobble 0..1,t,seed,depth}).
- agreeButton({cx,cy,w=640,h=184,label,press,ripple 0..1,R=1500,glow,t,tap},p).
- welcomeToast({x,y,title,sub,glow,t,slide 0..1,life},p); welcomeToastWidth(o).
- daySlam({cx,cy,day=1,p (0..1 over ~0.6 s, hit at .3),t,scale,burst,burstColor,flash,seed}).
- re-exported: termsPage, defaultTag.

engine/ui.js additions (old calls unchanged):
- dayCard({...,flip 0..1,next,nextColor,nextIcon}): split-flap turn from day to next.
- terms({...,page,flick 0..1,finePrint,highlight 0..1,sticker:false,agreeLabel,agreeTone}); page counts up automatically when flick is set.
- termsPage({x,y,w,h,page,of,highlight,sheet,size,items}) readable fine-print page (font auto-fits); FINE_PRINT; wrapText(str,size,maxW,font).
- timerPill({...,frac 0..1,shake:px|{amp,t}}).
- nameTag({variant:'default',cx,y (string anchor),name,sub,string=70,swing deg,size,flicker 0..1},p) = defaultTag(o,p).

engine/fx.js additions:
- ripple({cx,cy,R,rings=3,color,squash,fill},p).
- sunFlare({cx,cy,r,k 0..1,t,rays,ghosts,color}).
- whiteout({cx,cy,color,tint},k).
- crackedGlass({cx,cy,r,k,seed,box:[x,y,w,h],color}).
- scrollStreaks({x,y,w,h,speed px/frame,seed,t,color,count,dir:'v'|'h'}).
- boxBlur(svg,{x,y,w,h,sdx,sdy}).

engine/caption.js additions:
- KW_DICT; autoKeywords(text, extra) wraps CAPS words by meaning.
- captionsFromWords(words:[{w,t0,t1}] or {word,start,end}, {maxWords=3, lead=3 frames, fps=60, tail=0.25, markup, auto=true, mode, minFrames=4}) -> [{t0,t1,markup,mode?,cps?}].

Stills:
- node tools/render_ui_still.js stills/ui_hook_kit.js out.png 1.5   (UI sheet; arg 'fx' gives the fx sheet)
- node tools/render_ui_still.js stills/ui_phone_pov.js out.png 2 ['cap'|'v0.4'|'night']

### Open issues and notes from the builder

- Only the right hand is drawn. A left-hand or two-hand grip would need a mirrored handFront/handBack.
- When the thumb targets the top of the screen, the auto grip shift moves the palm and thenar over the right edge of the screen. Shots that tap high up should place the phone lower, or pass handShift.
- undoHistory with speed > ~2.5 items/s uses a feGaussianBlur whose filter region is the list viewport. Keep it out of fx.glitch() and out of <use> copies (Chromium caveat). Every other new component uses gradients only.
- engine/anim/captions.js (engine task) already has captionsFromLine(). caption.captionsFromWords() is the lower-level equivalent (plus auto keyword colouring and min-hold merging). The engine owner may want captionsFromLine to call it so there is one chunker.
- Components do not emit SFX cues. Each visual event needs a cue added in the shots: thumb press, slider tick per step, notify buzz, crack/shatter, UNDO halves landing, odometer ticks (rate = counter speed), page flick whoosh, I AGREE sub boom, toast chime, card flip, DAY slam.
- The phone POV still composes sets.street + cast.toon('tiny') itself, with the dog moved to x 1090 and drawn after the 'yard' layer, and a 1.8 px blur on the background. A shot would do the same through cam.set inserts.
- Not done: a mannequin flicker effect on the cast (cast task). Only the DEFAULT tag is drawn here.

### Metrics

SVG build cost in node, per frame: phone with Dog size screen 1.6 ms (43 KB), undoHistory at speed 1.2 ms (40 KB), fanMontage 1.5 ms (80 KB), daySlam 0.7 ms, dayCard flip 0.4 ms, terms flick 0.3 ms, counter 0.2 ms. Each still renders in about 1-2 s including the Chromium launch. Output sizes: ui_hook_kit.png 3840x2160 3.7 MB, ui_hook_fx.png 3840x2160 3.2 MB, ui_phone_pov.png 3840x2160 2.8 MB. Regression check: ui_kit / fx_caption_kit / style_frame_ui / frame_kitchen re-renders differ by max 0. New disk use is about 10 MB in renders/; the scratch QA folder was deleted.
