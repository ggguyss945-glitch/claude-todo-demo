# Zombie series: drawing engine and series bible

- `engine/lib.js` — SVG drawing library in the Nobody Gets In-like style: hero and zombie rigs, crowds, HUD themes, captions, grades, paper grain.
- `engine/scenes.js` — style frames: character sheet, supermarket (day, night, exterior, close-up), mall, park, POV, motion-graphics cards.
- `tools/render.js` — renders scenes to PNG with Playwright: `NODE_PATH=$(npm root -g) node tools/render.js supermarket_night mall@0`.
- `docs/` — series bible page and the rendered style frames.
