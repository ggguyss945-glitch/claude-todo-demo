#!/bin/bash
# Picture + mixes -> deliverables:
#   If_A_Police_Officer_Knocks_EN_1440p60.mp4      English audio, English captions
#   If_A_Police_Officer_Knocks_RU_dub.m4a / .wav  the Russian dub, same timeline (for YouTube multi-language audio)
#   If_A_Police_Officer_Knocks_EN+RU_1440p60.mp4   one file carrying both audio tracks (English default)
# The render slices are near-lossless (~80 Mbps); the picture is encoded once more to ~28 Mbps (above YouTube's
# 1440p60 recommendation) while muxing the English mix, and the two-track file reuses that video stream.
# usage: finish.sh <work dir with timeline.json, mix_en.wav, mix_ru.wav> <picture dir> <out dir>
set -e
W=$1; PIC=$2; OUT=$3
mkdir -p "$OUT"
ls "$PIC"/slice_*.mp4 | sort | sed "s/^/file '/; s/$/'/" > "$PIC/list.txt"
DUR=$(python3 -c "import json; print(json.load(open('$W/timeline.json'))['duration_en'] + 2.0)")
EN="$OUT/If_A_Police_Officer_Knocks_EN_1440p60.mp4"
ffmpeg -v error -stats -y -f concat -safe 0 -i "$PIC/list.txt" -i "$W/mix_en.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset veryfast -crf 19 -maxrate 28M -bufsize 56M -pix_fmt yuv420p -profile:v high -g 120 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 320k -ar 48000 \
  -metadata:s:a:0 language=eng -metadata:s:a:0 title=English -t "$DUR" -movflags +faststart "$EN"
ffmpeg -v error -y -i "$W/mix_ru.wav" -t "$DUR" -c:a aac -b:a 320k -ar 48000 -metadata:s:a:0 language=rus "$OUT/If_A_Police_Officer_Knocks_RU_dub.m4a"
ffmpeg -v error -y -i "$W/mix_ru.wav" -t "$DUR" -c:a pcm_s24le "$OUT/If_A_Police_Officer_Knocks_RU_dub.wav"
ffmpeg -v error -y -i "$EN" -i "$OUT/If_A_Police_Officer_Knocks_RU_dub.m4a" -map 0:v -map 0:a -map 1:a -c copy \
  -metadata:s:a:0 language=eng -metadata:s:a:0 title=English -metadata:s:a:1 language=rus -metadata:s:a:1 title=Русский \
  -disposition:a:0 default -disposition:a:1 0 -movflags +faststart "$OUT/If_A_Police_Officer_Knocks_EN+RU_1440p60.mp4"
# a single-file copy under 400 MiB (HEVC keeps the film grain best at this size, ~4.3 Mbps), for transfers with a size limit
ffmpeg -v error -stats -y -f concat -safe 0 -i "$PIC/list.txt" -i "$W/mix_en.wav" -map 0:v -map 1:a \
  -c:v libx265 -preset fast -b:v 4000k -x265-params log-level=error:vbv-maxrate=8000:vbv-bufsize=16000:keyint=120 \
  -pix_fmt yuv420p -tag:v hvc1 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 160k -ar 48000 \
  -metadata:s:a:0 language=eng -t "$DUR" -movflags +faststart "$OUT/If_A_Police_Officer_Knocks_EN_1440p60_HEVC.mp4"
ls -la "$OUT"
