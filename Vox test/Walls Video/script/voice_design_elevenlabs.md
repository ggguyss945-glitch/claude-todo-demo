# Night Policy narrator: ElevenLabs Voice Design

Goal: a new, original narrator voice (designed from a text description, not cloned) as close as possible to the voice of our earlier films.

## What we measured on the current narrator (Ice Cream film, raw voiceover)

- Male voice: formants F1 491 Hz, F2 1497 Hz, F3 2641 Hz, F4 3404 Hz.
- Pitch: a light baritone, middle-high for a man (median 166 Hz, from 115 to 228 Hz).
- Very expressive: about 15 semitones of range.
- Texture: breathy and slightly husky (HNR 7.9 dB, with a little rasp) and close to the mic. Crisp, airy highs (spectral centroid about 3 kHz).
- Pace: brisk, about 160 words per minute including pauses, with about a quarter of the time in pauses.
- Accent: we cannot measure it. Assumed General American; change that word if ours is different.

## Voice description (paste into "Describe the voice")

Male narrator in his late twenties to early thirties, General American accent. A light baritone, mid-to-high for a man, with a warm, slightly husky, breathy texture, recorded very close to the microphone so quiet words feel spoken right next to your ear. An intimate late-night storyteller telling a true scary story to one friend: sincere, uneasy, never theatrical. Wide, natural pitch movement: drops to a soft, tense near-whisper on creepy lines, tightens and speeds up with real fear when things go wrong, then turns warm, calm and kind when giving advice. Brisk conversational pace with deliberate pauses before reveals. Clear diction, crisp consonants. Not an announcer, not a movie-trailer voice, no growl, no exaggerated acting. Studio-quality recording, perfect audio quality: dry, clean, no reverb, no background noise, no music.

## Preview text (paste into the text box)

If you hear scratching inside your walls at night... don't knock back. My dad said it was the old house settling. Mice, maybe. Pipes. But mice don't breathe. And pipes don't stop when you stop. I pressed my ear to the wall above my bed... and something on the other side pressed back. Okay. Breathe. You can turn a light on now. If something in your home feels wrong, say it out loud to someone you trust. And keep saying it, until someone listens.

## How to pick the voice

1. Use the newest Voice Design model offered (v3 if available). Leave loudness at its default; we level the voice in the mix.
2. If there is a guidance or prompt-strength slider, set it high (about 8 to 12) so the result follows the description closely.
3. Every generation gives several previews. Generate a few rounds and compare each preview, by ear, with our reference clip `film/_work/ref/current_narrator_reference_40s.m4a`. Check four things: how deep it is, how breathy, the whisper on the scary lines, and the warmth on the last two sentences.
4. If one is close but off in one way, use Remix on it with a short note at medium strength, for example:
   - "slightly deeper and calmer"
   - "more breathy and closer to the mic"
   - "less bright, softer s sounds"
   - "faster, more urgent"
5. Save the best one and give it a name (for example "Night Policy Narrator"). Use only this voice for every part of the film.
6. When you generate the narration, keep speed at normal. We remove breaths, clicks and long gaps ourselves, so do not edit them out.

Note: Voice Design creates a new synthetic voice that belongs to your account. It sounds like ours in style but is not a copy. A near-identical copy would need cloning, and cloning the current TTS voice could break that voice's terms. The designed voice is the safer, original choice.
