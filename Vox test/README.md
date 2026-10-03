# Vox test: "How the Eye In The Sky works"

Three procedural rebuilds of a 79-second vertical short, plus a side-by-side comparison.
Every frame is generated from code (vector drawing or real-time 3D). No footage from the
original is traced, copied or composited. The original's audio track (voice-over and
music) is the only thing reused.

| File | What it is | Resolution |
|------|------------|------------|
| `V1_transcript_edit.mp4` | Edit built from the transcript alone, before any frame of the original was viewed. It uses a Vox-style motion-graphics language: paper texture, highlighter, cut-out illustrations, a HUD and word-synced captions. | 1440×2560, 30 fps |
| `V2_recreation.mp4` | A 1:1 recreation of the original's look: a low-poly 3D casino, painted "photo" faces, first-person shots, CCTV feeds, bloom and a sharpened, saturated grade. It follows the original's ~32 shots and their cut points to the frame. | 1440×2560, 30 fps |
| `V3_final.mp4` | V2 with far more detail and checked shot by shot against the original. Characters gain fingers, hair volume, blinking, breathing and real lapels and shoes. The sets gain architecture, light shafts, dust, background players, a bartender and clutter. Rendering adds 4× MSAA, 3-sample motion blur, contact shadows and 4K shadow maps. | 1440×2560, 30 fps |
| `Comparison_V1_V2_V3.mp4` | All three versions playing in sync, with labels. | 3840×2160 |

## How it was made

* **Transcript**: speech-to-text with NVIDIA Parakeet-TDT and Whisper (via sherpa-onnx), run locally, with word-level timestamps. The two models were cross-checked against each other. The result is in `transcript/`.
* **V1** (`src/`): Python + [skia-python](https://github.com/kyamagu/skia-python). `mg.py` is a small motion-graphics toolkit (easing, type, paper and grain textures, path trimming). `v1_transcript.py` holds the scenes. `render.py` renders the frames in parallel and encodes them.
* **V2 / V3** (`src3d/`): [three.js](https://threejs.org) runs in headless Chromium (Playwright). Rendering uses ANGLE→EGL on Mesa llvmpipe, which turned out ~7× faster than SwiftShader. `render.js` drives the page and streams frames into ffmpeg.
  * `v2/`: the code exactly as it rendered V2.
  * `app/`: the V3 code, which is V2 plus `detail.js` and the upgraded character, face and render pipeline.
  * All textures are drawn on canvases: felt layouts, wheel, chips, carpet, wallpaper, faces, clothing, CRT feeds and mugshot sheets.

### Rebuild

```bash
# V1
pip install skia-python numpy
VOX_AUDIO=original.mp4 python3 src/v1_transcript.py --out V1_transcript_edit.mp4

# V2 / V3 (needs Mesa llvmpipe: apt install libgl1-mesa-dri libegl-mesa0)
cd src3d && npm install three@0.170.0 playwright
node render.js --app v2 --version v2 --gl egl --workers 4 --lpthreads 1 --video ../V2_recreation.mp4 --audio original.mp4
node render.js --app app --version v3 --gl egl --workers 4 --lpthreads 1 --video ../V3_final.mp4 --audio original.mp4
# quick stills for checking: --stills 4.5,14.6,26 --scale 0.5

# comparison
./make_comparison.sh
```
