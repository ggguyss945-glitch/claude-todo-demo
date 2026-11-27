# Obsession film: ElevenLabs Voice Design for every voice

This film needs only three new voices: Evie, Mom and Mrs. Rahman. The narrator is the voice you already made for the Walls film (the same one as in the Buttons film).

For each new voice:

1. Paste the DESCRIPTION into "Describe the voice" and the PREVIEW into the text box.
2. Use the newest Voice Design model.
3. Set guidance high (about 8 to 12).
4. Generate a few rounds and save the best preview.
5. Then generate that voice's lines from its file in `script/voices_v4/` with the Eleven v4 model. If there is a stability setting, start with Natural. Keep speed normal and leave pauses as they are: we clean, cut and place everything ourselves.

The descriptions ask for clean studio audio. We add the phone, letterbox, chalk and creepy effects ourselves.

| Voice | Use this voice | Lines file (`voices_v4/`; plain copy with the same name in `voices/`) |
|---|---|---|
| Narrator (Adam, grown up) | Our narrator voice from the Walls film | `narrator_part1.txt` ... `narrator_part7.txt`, in that order (182 paragraphs) |
| Evie, the chalk girl | New design (section 2) | `evie.txt` (16 lines, in story order; the last one is sung) |
| Lina, 7, Adam's sister | Evie's voice | `lina.txt` (3 lines; the last one is sung) |
| Mom | New design (section 3) | `mom.txt` (6 lines) |
| Mrs. Rahman, the counsellor | New design (section 4) | `rahman.txt` (2 lines) |
| Adam, 7 and 12 | Our narrator voice | `kids_adult_take.txt` (9 lines: the song at 7 first, then 8 lines at 12) |
| Danny, 12 | Our narrator voice | `danny.txt` (5 lines) |

- **Adam and Danny:** ElevenLabs does not design child voices, so both boys are read with our narrator voice, and we make their child voices ourselves, like Owen and his son in the Buttons film.
- **Evie:** we design her as a young woman in her early twenties, with a light, bright, youthful voice, and we shift it younger ourselves. One voice covers all her forms: sweet, too sweet and wrong.
- **Lina:** like the boys, she gets no design of her own. She uses Evie's voice, read plain and honest, never creepy, and we shift her higher and younger than Evie so the two never sound alike. If she still sounds like Evie, read her lines with the narrator voice, like the boys.

Each line in a lines file is separated by an empty line. Generate them all in one go, or one line at a time if a line comes out wrong.

---

## 1. Narrator (Adam, grown up): full, steady, energetic voice; no breathiness, no breaths

Use the same narrator voice as the Walls and Buttons films. It is already in your account.

Only if you lost it: design it again with this DESCRIPTION (the same as the Walls film) and this new PREVIEW.

DESCRIPTION
```
Male narrator in his late twenties to early thirties, General American accent. A light baritone, mid-to-high for a man, with a clear, bright, fully voiced tone: no breathiness, no audible breaths, no rasp. An energetic, confident YouTube horror storyteller who grabs you from the first word: projected, punchy and animated, always at a full, steady speaking level, never quiet and never whispering. The opening hook is delivered with raised pitch and urgency. Very expressive, wide pitch movement and strong emphasis on key words; tension comes from intensity, pace and sharp pauses, not from dropping the volume. Brisk pace, around 160 words per minute. Turns warm, sincere and kind when giving advice at the end. Clear diction, crisp consonants. Not an announcer or movie-trailer voice, no growl, no cartoon acting. Studio-quality recording, perfect audio quality: dry, clean, no reverb, no background noise, no music.
```
PREVIEW
```
If someone you met three days ago says you're their favourite person in the whole world... don't say it back. Especially if she doesn't blink. And if you look down at midnight, and someone at your front door is smiling up, two words chalked at their feet... don't go down. Wake a grown-up. Two a.m. Her dot was on our house. Then inside it. Then in my room. I swung my torch. Nobody. Just one white chalk fingerprint... on the inside of my window. Okay. Breathe. You can turn a light on now. The monster is made up. The warning signs are real. Your passwords are yours. You can say no, and saying no isn't cruel. Don't keep it secret. Tell a grown-up you trust. If they don't listen, tell another. Keep telling.
```

## 2. Evie, the chalk girl: also the voice of Lina

DESCRIPTION
```
A young woman in her early twenties, General American accent. A light, bright, high and youthful voice, sweet and clear, with a smile you can hear in every word: cheerful, eager and sing-song, the friendliest new face in the room. The same voice also goes wrong while it stays sweet: too sweet and too calm, slow, every word smiling, vowels held a little too long; a flat, pleased tone that never changes; a close, soft, flat whisper; a short, clipped giggle; a simple sing-song rhyme sung in tune, which she can stretch slow and thin. Her cheer never drops. She never shouts, growls or sounds angry: she is creepy because she stays so sweet and so calm. The same voice can also speak plainly and honestly, with no edge at all. Natural acting, not a cartoon voice. Clear voice, no breathiness in normal speech. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise, no music.
```
PREVIEW
```
Hi! I'm Evie. Like forever. I saved you a seat. I already know your favourite crisps! You're my favourite person in the whole world. Are you awake? Why aren't you answering? I can see your light's still on. I made it myself. For you. Only me? Best friends share passwords. Don't you trust me? There. Now it's only me. You asked for someone who'd never leave. Here I am. After everything I gave you. If you leave, it's your fault. I'll stand here forever. Write your name? Everywhere you go, I'm near. Only me. I'm here, I'm here.
```

## 3. Mom

DESCRIPTION
```
A woman in her mid-forties, General American accent. A warm, steady, slightly low voice, a little tired and never shrill: a mom who has been up every night all week quietly fixing a hard problem, and who means every word she says. With her son she is light and watchful at first, then soft and patient, holding the door open for him to talk. On the phone she is quiet, serious and grateful. When he finally tells her everything, there is no anger in her at all, only warmth. Standing up for him at the front door, she is calm, firm and final, never loud. Natural and sincere, not theatrical. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise, no music.
```
PREVIEW
```
Anything you want to tell me? I know. I'll talk to him. Thank you for telling me. Adam, your dinner's getting cold. Anything you want to tell me? I'm right here. I'm not going anywhere. Thank you for telling me. Danny was right to say no. And you're not bad. We'll save every message, and on Monday you tell Mrs. Rahman too. He said no.
```

## 4. Mrs. Rahman, the school counsellor

DESCRIPTION
```
A school counsellor, a woman in her fifties, General American accent. A calm, low, unhurried voice, kind and impossible to shock, with a smile you can hear. When she checks in on a student in the hall she is easy and light, with no pressure at all. When a student owns up to something hard, she is warm, steady and proud of him, and makes it feel safe to keep talking. Natural and plain, not theatrical. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise, no music.
```
PREVIEW
```
Just checking in, Adam. My door's open. Come in, sit wherever you like. There's no rush. That was brave. Caring isn't owning. We'll work on it together. You can come back tomorrow, and the day after that. My door stays open.
```

---

## Eleven v4 versions of the lines (`voices_v4/`)

The same words as `voices/`, with Eleven v4 audio tags: short directions in square brackets at the start of a paragraph. The model follows them; it does not read them aloud.

- Generate with the Eleven v4 model. If there is a stability setting, start with Natural.
- The narrator has delivery tags only, and none of them makes him quiet: like our earlier films, he stays at a full, steady level the whole time and is at his most energetic in the opening hook. Tension comes from intensity, pace and pauses. The reveals ("I was." "From me." "It was me.") land hard and slow, still at full level. There is no whispering, no sighs and no breaths. He turns warm and sincere for the advice at the end.
- There are no sound-effect tags. We add every sound ourselves (the pings, the clank, the letterbox, the chalk).
- The narrator is in 7 parts, each under 2,400 characters with the tags. Generate them in order with the same voice.
- If a tag is ever read out loud or makes a line sound wrong, delete that tag and generate the line again.
- The kids' lines (`kids_adult_take.txt` and `danny.txt`): use the narrator voice and read them like a kid would; the tags say how. Adam's song at seven is sung sweetly and simply. We make Adam's and Danny's child voices ourselves.
- Evie: one voice for all her forms. The tags set each line: sweet, then too sweet and too calm, then wrong (flat, close, a whisper, a clipped giggle). "Write your name?" on the doormat is bright and sweet again: the trap. Her last line is sung, stretched thin and cut off. We add her creepy effects ourselves (the chalk scrape, slowing, detuning).
- Lina: Evie's voice, plain and honest, never creepy; her song at the end is simple and happy. We make her younger ourselves.

---

Note: each designed voice is new and belongs to your account; none of them copies a real person.
