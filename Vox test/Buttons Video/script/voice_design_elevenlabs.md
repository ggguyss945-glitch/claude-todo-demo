# Buttons film: ElevenLabs Voice Design for every voice

This film needs only three new voices: Mom, Mr. Dunn and Officer Mensah. The narrator is the voice you already made for the Walls film.

For each new voice:

1. Paste the DESCRIPTION into "Describe the voice" and the PREVIEW into the text box.
2. Use the newest Voice Design model.
3. Set guidance high (about 8 to 12).
4. Generate a few rounds and save the best preview.
5. Then generate that voice's lines from its file in `script/voices_v4/` with the Eleven v4 model. If there is a stability setting, start with Natural. Keep speed normal and leave pauses as they are: we clean, cut and place everything ourselves.

The descriptions ask for clean studio audio. We add the phone, radio, chat and creepy effects ourselves.

| Voice | Use this voice | Lines file (`voices_v4/`; plain copy with the same name in `voices/`) |
|---|---|---|
| Narrator (Owen, grown up) | Our narrator voice from the Walls film | `narrator_part1.txt` ... `narrator_part7.txt`, in that order (169 paragraphs) |
| Mom (Nadia) | New design (section 2) | `mom.txt` (13 lines; two are sung: the song, and its last line at the end) |
| The Blank | Mom's voice | `blank.txt` (20 lines) |
| Mr. Dunn, crossing guard | New design (section 3) | `dunn.txt` (2 lines; the second is into his radio) |
| Officer Mensah | New design (section 4) | `mensah.txt` (1 line) |
| Owen, 11, and his son, 10 | Our narrator voice | `kids_adult_take.txt` (8 lines: Owen's 6 first, then the son's 2) |

- **Owen and his son:** ElevenLabs does not design child voices, so we make Owen and his son ourselves from this one adult take, like Theo and Sam in the Walls film.
- **The Blank:** she is a copy of Mom and must sound exactly like her (in the car the viewer must not hear any difference), so she uses Mom's voice, and we add her creepy effects ourselves.

Each line in a lines file is separated by an empty line. Generate them all in one go, or one line at a time if a line comes out wrong.

---

## 1. Narrator (Owen, grown up): full, steady, energetic voice; no breathiness, no breaths

Use the same narrator voice as the Walls film. It is already in your account.

Only if you lost it: design it again with this DESCRIPTION (the same as the Walls film) and this new PREVIEW.

DESCRIPTION
```
Male narrator in his late twenties to early thirties, General American accent. A light baritone, mid-to-high for a man, with a clear, bright, fully voiced tone: no breathiness, no audible breaths, no rasp. An energetic, confident YouTube horror storyteller who grabs you from the first word: projected, punchy and animated, always at a full, steady speaking level, never quiet and never whispering. The opening hook is delivered with raised pitch and urgency. Very expressive, wide pitch movement and strong emphasis on key words; tension comes from intensity, pace and sharp pauses, not from dropping the volume. Brisk pace, around 160 words per minute. Turns warm, sincere and kind when giving advice at the end. Clear diction, crisp consonants. Not an announcer or movie-trailer voice, no growl, no cartoon acting. Studio-quality recording, perfect audio quality: dry, clean, no reverb, no background noise, no music.
```
PREVIEW
```
If someone online says, "Your mom doesn't even see you"... don't answer. If a present says don't tell your mom, and at three a.m. it stands up in your closet... don't keep quiet. Your real mom is in the kitchen. Talking to the police. Midnight. My birthday. Behind the fridge, something unfolded. Up, and up, until her head bent along the ceiling. A smile far too wide. Okay. Breathe. You can turn a light on now. Feel uneasy? Say no, get away, tell a grown-up you trust. If they don't help, tell another. It's never your fault. Real love never asks for secrets. And it never says you can't come home.
```

## 2. Mom (Nadia): also the voice of the Blank

DESCRIPTION
```
A woman in her late thirties, General American accent. A warm, slightly low mid-range voice, a little tired: a single mom who works long help-line shifts at her kitchen table, and loving underneath everything. On calls she is soothing, slow and endlessly patient, a voice that makes strangers feel heard. With her son she is kind but distracted, her mind still on the call. When she is scared and searching for him, her voice turns raw and cracks with tears. She can sing a simple lullaby softly and in tune. The same voice can also go perfectly sweet, smooth and calm, almost too calm, and it can drop to a close, intimate whisper. Natural and sincere, not theatrical. Clear voice, no breathiness in normal speech. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise, no music.
```
PREVIEW
```
Thank you for calling. I'm listening. One minute. It says delivered. On the mat. Get in, sweetheart. I got off early. Pancakes? Baby? I'm at the table. Where are you? No... I can't see him anywhere. He's eleven. Green coat. Broken zip. It's his birthday. There you are. None of this is your fault. You can always come home.
```

## 3. Mr. Dunn, the crossing guard

DESCRIPTION
```
A school crossing guard, a man in his late sixties, General American accent. A warm, steady, slightly weathered baritone with a kind, grandfatherly calm. With a scared kid he is unhurried, gentle and sure: simple words that make you feel safe. Into his radio he turns quick, clipped and firm, fully in control, never shouting. Natural and plain, not a caricature. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise, no music.
```
PREVIEW
```
Morning, kiddo. Wait for my sign. Okay, walk. You did right. You checked. Stand with me. Silver car. Dented bumper. Now. You're safe here. Stay right by my sign. Your mom's on her way, and we'll wait for her together.
```

## 4. Officer Mensah

DESCRIPTION
```
A police officer, a man in his forties, General American accent. A calm, warm, mid-low voice, professional and steady: someone used to long, tense nights. Gentle and patient with a frightened parent. When he notices something important he turns quietly urgent: low, quick and focused, never loud. No drama. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise, no music.
```
PREVIEW
```
Ma'am, I'm Officer Mensah. Take your time. A silver car, dented bumper. Got it. We have cars out looking right now, and I'm staying right here with you. Tell me everything you remember. Ma'am. The board.
```

---

## Eleven v4 versions of the lines (`voices_v4/`)

The same words as `voices/`, with Eleven v4 audio tags: short directions in square brackets at the start of a paragraph. The model follows them; it does not read them aloud.

- Generate with the Eleven v4 model. If there is a stability setting, start with Natural.
- The narrator has delivery tags only, and none of them makes him quiet: like our earlier films, he stays at a full, steady level the whole time and is at his most energetic in the opening hook. Tension comes from intensity, pace and pauses. There is no whispering, no sighs and no breaths. He turns warm and sincere for the advice at the end.
- There are no sound-effect tags. We add every sound ourselves (the tik, the ping, the music box, the radio).
- The narrator is in 7 parts, each under 2,400 characters. Generate them in order with the same voice.
- If a tag is ever read out loud or makes a line sound wrong, delete that tag and generate the line again.
- The kids' take: use the narrator voice and read it like a kid would; the tags say how. We make Owen's and his son's child voices ourselves.
- The Blank: use Mom's voice. Her chat messages are whispered, close and soft. The car line ("Get in, sweetheart. I got off early. Pancakes?") must sound exactly like Mom. Her other lines are a shade too sweet, too smooth and too calm. We add the creepy effects ourselves (doubling, slowing, detuning for her tall form at midnight).

---

Note: each designed voice is new and belongs to your account; none of them copies a real person.
