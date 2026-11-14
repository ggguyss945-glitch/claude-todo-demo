# Render "Too Much Gold" on a Windows gaming laptop (GPU)

The cloud session has no graphics card, so it renders on the CPU (about 5 hours for this video).
On a laptop with an NVIDIA or AMD GPU the same render should take minutes instead of hours.

## 1. Install once

Open **PowerShell** and run:

```
winget install OpenJS.NodeJS.LTS
winget install Git.Git
winget install Gyan.FFmpeg
```

Close PowerShell and open it again, so it finds the new programs.

Plug the laptop into its charger. On battery, Windows slows the GPU down.

## 2. Get only this project

The repository holds gigabytes of older videos. These commands download only this folder:

```
cd $HOME
git clone --filter=blob:none --sparse -b claude/vox-test-video-recreation-oh0z7p https://github.com/ggguyss945-glitch/claude-todo-demo.git
cd claude-todo-demo
git sparse-checkout set "Vox test/Too Much Gold V1"
cd "Vox test/Too Much Gold V1"
npm install
npx playwright install chromium
```

## 3. Test one frame first

```
node render.js --app app --version gpu --gl gpu --scale 1 --stills 11.2 --out stills
```

A browser window opens for a moment, and the command prints how long the frame took.
In the cloud the same frame takes 40–60 seconds. On your GPU it should take about one second or less.
Open `stills\gpu_11.20.png` to check the picture.

If it takes more than about 10 seconds, Windows is using the weak built-in graphics instead of the NVIDIA one:
open **Settings → System → Display → Graphics**, add the browser
`%LOCALAPPDATA%\ms-playwright\chromium-1194\chrome-win\chrome.exe` (the number may differ),
set it to **High performance**, and run the test again.

## 4. Render the whole video

```
.\render_win.cmd --app app --version tmg --gl gpu --fps 60 --workers 2 --chunk 60 --crf 14 --audio audio\Too_Much_Gold_mix.flac --video out\Too_Much_Gold_V1_1440p60.mp4
```

- Two browser windows open and render side by side. Leave them open; you can put other windows over them.
- Progress prints every 30 seconds (`frames … fps … eta … min`).
- If you stop it or the laptop sleeps, run the same command again: finished seconds are kept and it continues.
- When it finishes, the video with sound is `out\Too_Much_Gold_V1_1440p60.mp4` (1440×2560, 60 fps).
