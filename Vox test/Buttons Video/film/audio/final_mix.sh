#!/bin/bash
# Rebuild the final mix after picture changes ("If Your Mom's Eyes Turn Into Buttons... DON'T KEEP HER SECRET"),
# from any directory:
#   bash "Vox test/Buttons Video/film/audio/final_mix.sh"          cues -> mix -> measure -> preview_mix.mp4
# Prepared once (sound prep, already done; re-run only when the owner's packs change):
#   (no new Epidemic set for this film: the linked sets of _work/samples, audio/catalog_epidemic_ice.json)
#   python3 audio/review_sfx.py --md                _work/mix/sfx_review.md (verdicts on the new files)
#   python3 audio/motif_buttons.py measure          Mom's sung notes vs the tune -> _work/mix/motif/mom_notes.json
#   python3 audio/motif_buttons.py                  THE BUTTON SONG's versions -> _work/mix/motif (checks, sheet)
#   python3 audio/music_plan.py --table             the music map (word-anchored on _work/align/timeline.json)
#   python3 audio/sfx_tests_buttons.py              8 test sounds -> _work/mix/tests + the owner's per-event check
#   ... final_mix.sh --no-preview                                        skip the preview mux
# Steps (each one is also fine to run by hand from film/):
#   1. python3 film.py --cues                       cue sheets from the picture -> _work/cues/{sfx,music}_cues.json
#                                                    (skipped with --no-cues: the sheets already match the picture)
#   2. python3 audio/mix.py ... _work/mix/final      the police mix (about 14 min, peaks at 12 GB: no render running);
#                        the voice track has every character voice and place-effect BAKED in (timeline fx_baked):
#                        mix.py adds no voice effect; no --who-fx
#        --plan full     the score follows audio/music_plan.py (word-anchored tension events, snapped to the picture's
#                        hit frames; film.py's own music events are replaced) and audio/sfx_plan.py refines the
#                        picture's SFX sheet (PICTURE: film.py's names onto this film's recipes, the identity layer's
#                        hums / jingles / count thumps dropped from the SFX sheet; EDIT: re-levels; ADD: off-screen and
#                        foley additions, deduplicated by sound family); both sheets as mixed go to
#                        _work/mix/final/cues_used/
#        --bed-p50 -14   (kept from the Bus film; re-check on this film's first mix) the Bus film's bed target (sound prep tests: at -16 the music was present only 42-85 %
#                        of each window; at -14, 70-73 % with the bed integrated -11.7..-13.7 LU)
#        --hits-db 6     the score's hits stem +6 dB (fix round 1: +4 -> +6) (the boost path's broadband speech duck keeps the words after every boosted hit 7 LU over the bed)
#        --voice-ride 1  a slow 4:1 ride on the narration's loudest phrases (> +1 LU; fix round 1: at 2 / 3:1 the
#                        narration's loudest lines still reached +5 LU momentary over the mix), so the scares top the film
#   3. mix.wav = hard link of mix_en.wav            (render.py / deliver.sh read mix_en.wav, the job names mix.wav)
#   4. python3 audio/measure_mix.py _work/mix/final  loudness, voice clarity, music presence, every SFX cue re-checked
#   5. python3 audio/mix_scenes.py _work/mix/final   one sheet per scene (spectrogram, cues, score events, stem levels)
#                                                    -> _work/mix/final/scenes/NN_name.png
#   6. ffmpeg: the mix onto the low-res preview     -> _work/preview/preview_mix.mp4 (re-render the preview first when the
#                                                    picture changed: README, Sound: the final mix)
set -euo pipefail
FILM="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FILM"
W=_work; FINAL=$W/mix/final
# disk (about 0.4 GB free on /): the whole mix is rendered in RAM (/dev/shm/buttons, tmpfs) and only the 24-bit FLAC,
# the reports and the cue sheets as mixed come back to _work/mix/final; the RAM copy is deleted at the end
RAM=${MIX_RAM:-/dev/shm/buttons_mix}; OUT=$RAM/final      # its own tmpfs folder (teammates clear /dev/shm/buttons)
mkdir -p "$FINAL" "$OUT/stems"
echo 1000 > /proc/self/oom_score_adj 2>/dev/null || true
case " $* " in *" --no-cues "*) ;; *) python3 film.py --cues ;; esac
export MIX_SCORE_CACHE=${MIX_SCORE_CACHE:-$RAM/score_cache}
rm -rf "$MIX_SCORE_CACHE"; trap 'rm -rf "$MIX_SCORE_CACHE"' EXIT
MIXARGS="../$W/align/timeline.json ../$W/align/vo_en.wav - ../$W/cues $OUT --langs en --plan full --hits-db 6 --voice-ride 1.0 --bed-p50 -14 --write-cues"
( cd audio && python3 mix.py $MIXARGS --score-only ) 2>&1 | tee "$OUT/score.log"
( cd audio && python3 mix.py $MIXARGS ) 2>&1 | tee "$OUT/mix.log"
rm -rf "$MIX_SCORE_CACHE"
# the end card (818.78-822.98, the last word ends at 818.38): the music tail dies away by the last frame, never cut
python3 audio/end_fade.py "$OUT" 818.9 0.15
ln -f "$OUT/mix_en.wav" "$OUT/mix.wav"
python3 audio/measure_mix.py "$OUT" | tee "$OUT/measure.txt"
python3 audio/mk_events.py "$OUT/cues_used/sfx_cues.json" "$OUT/events.json" && python3 audio/measure_mix.py --events "$OUT/events.json" --voice "$OUT/stems/voice_en.wav" > "$OUT/events.txt" || true
ffmpeg -v error -y -i "$OUT/mix_en.wav" -c:a flac -sample_fmt s32 -bits_per_raw_sample 24 "$FINAL/mix_en.flac"
cp -r "$OUT"/*.json "$OUT"/*.txt "$OUT"/*.log "$OUT/cues_used" "$FINAL"/ 2>/dev/null || true
if [ "${1:-}" != "--no-preview" ] && [ -f "$W/preview/preview.mp4" ]; then
  ffmpeg -v error -y -i "$W/preview/preview.mp4" -i "$OUT/mix_en.wav" -map 0:v -map 1:a -c:v copy \
    -c:a aac -b:a 192k -ar 48000 -af apad -shortest -movflags +faststart "$W/preview/preview_mix.mp4"
  echo "preview: $FILM/$W/preview/preview_mix.mp4"
fi
[ -n "${KEEP_RAM:-}" ] || rm -rf "$OUT"
