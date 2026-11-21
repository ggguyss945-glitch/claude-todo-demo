#!/bin/bash
# Final deliverables for "If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN" (English only).
#   <out>/If_An_Eighth_Step_Appears_MASTER_1440p60.mov       near-lossless H.264 picture (stream copy) + 24-bit PCM English mix
#   <out>/parts/...MASTER_1440p60.mov.001, .002 ...           the master split into 390 MB pieces (+ SHA256, join notes)
#   <out>/If_An_Eighth_Step_Appears_EN_1440p60_HEVC.mp4      one file under 400 MiB for transfers with a size limit
# usage: tools/deliver.sh <picture.mp4> <mix.wav> <out dir>
#   e.g. tools/deliver.sh _work/picture/picture.mp4 _work/mix/final/mix.wav _work/deliver
# The picture is kept (the police film's script deleted it; this one does not).
set -e
PIC=$(realpath "$1"); MIX=$(realpath "$2"); OUT=$(realpath -m "$3")
mkdir -p "$OUT/parts"
B=If_An_Eighth_Step_Appears
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$PIC")
ADUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MIX")
echo "picture ${DUR}s, mix ${ADUR}s"
M="$OUT/${B}_MASTER_1440p60.mov"
ffmpeg -v error -y -i "$PIC" -i "$MIX" -map 0:v -map 1:a -c:v copy -c:a pcm_s24le -ar 48000 \
  -metadata:s:a:0 language=eng -metadata title="If An Eighth Step Appears On Your Mirror... WIPE THE GLASS CLEAN" \
  -t "$DUR" "$M"
# the master in 390 MB pieces: 7-Zip "Combine files" on .001, or the copy /b line in JOIN.txt
rm -f "$OUT/parts/$(basename "$M")".*
( cd "$OUT/parts" && split -b 390M --numeric-suffixes=1 -a 3 "$M" "$(basename "$M")." )
SUM=$(sha256sum "$M" | cut -d' ' -f1)
N=$(ls "$OUT/parts" | grep -c '\.mov\.[0-9]')
LIST=$(ls "$OUT/parts" | grep '\.mov\.[0-9]' | sort | sed 's/.*/"&"/' | paste -sd+)
cat > "$OUT/parts/JOIN.txt" <<EOF
$(basename "$M") was split into $N pieces of 390 MB.

Join with 7-Zip: put all pieces in one folder, right-click the .001 file, 7-Zip > Combine files.
Or in Windows PowerShell, inside that folder:
  cmd /c copy /b $LIST "$(basename "$M")"
Check it (the hash must match):
  Get-FileHash "$(basename "$M")" -Algorithm SHA256
SHA256: $SUM
EOF
# one file under 400 MiB: HEVC at 4 Mb/s (700 s -> about 350 MB with the audio)
ffmpeg -v error -stats -y -i "$M" -map 0:v -map 0:a -c:v libx265 -preset faster -b:v 4000k \
  -x265-params log-level=error:vbv-maxrate=8000:vbv-bufsize=16000:keyint=120 -pix_fmt yuv420p -tag:v hvc1 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -af alimiter=limit=0.708:attack=1:release=60:level=false -c:a aac -b:a 160k -ar 48000 \
  -metadata:s:a:0 language=eng -movflags +faststart "$OUT/${B}_EN_1440p60_HEVC.mp4"
ls -la "$OUT" "$OUT/parts"
