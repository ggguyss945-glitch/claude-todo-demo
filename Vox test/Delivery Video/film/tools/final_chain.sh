#!/bin/bash
# Final render + delivery + checks for the delivery film, in one chain (run from film/, in the background).
#   bash tools/final_chain.sh            -> _work/picture/picture.mp4, _work/deliver/If_A_Delivery_Driver_Rings_EN_1440p60_HEVC.mp4
# Re-running resumes: finished render slices (.done) are skipped; a finished picture.mp4 is not rendered again.
set -e
cd "$(dirname "$0")/.."
W=_work
echo "== render start $(date -u +%H:%M)"
if [ ! -s $W/picture/picture.mp4 ]; then
  python3 render.py --workers 3
fi
echo "== render done $(date -u +%H:%M)"
NF=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 $W/picture/picture.mp4)
PD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/picture/picture.mp4)
MD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/mix/final/mix_en.wav)
echo "== picture frames $NF duration $PD (mix $MD)"
python3 - "$NF" "$MD" <<'EOF'
import sys
nf, md = int(sys.argv[1]), float(sys.argv[2])
exp = round(md * 60)
print(f'== expected about {exp} frames from the mix length; picture has {nf}')
if nf < exp - 90: print('== PICTURE TOO SHORT'); sys.exit(2)
EOF
rm -f $W/picture/slice_*.mp4
echo "== deliver start $(date -u +%H:%M)"
bash tools/deliver.sh $W/picture/picture.mp4 $W/mix/final $W/deliver
H=$W/deliver/If_A_Delivery_Driver_Rings_EN_1440p60_HEVC.mp4
echo "== deliver done $(date -u +%H:%M)"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate -of compact "$H"
echo "== HEVC frames $(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 "$H")"
ffmpeg -nostats -i "$H" -map 0:a -af ebur128=peak=true -f null - 2>&1 | grep -A12 Summary | grep -E "I:|Peak:|LRA:"
echo "== ALL DONE $(date -u +%H:%M)"
