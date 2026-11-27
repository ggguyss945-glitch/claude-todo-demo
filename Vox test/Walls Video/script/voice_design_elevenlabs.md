# Walls film: ElevenLabs Voice Design for every voice

For each voice:

1. Paste the DESCRIPTION into "Describe the voice" and the PREVIEW into the text box.
2. Use the newest Voice Design model.
3. Set guidance high (about 8 to 12).
4. Generate a few rounds and save the best preview.
5. Then generate that voice's lines from its file in `script/voices/`. Keep speed normal and leave pauses as they are: we clean, cut and place everything ourselves.

The descriptions ask for clean studio audio. We add the phone, wall, vent and mask effects ourselves.

| Voice | Lines file |
|---|---|
| Narrator (Sam, grown up) | `voices/narrator_part1.txt` ... `narrator_part5.txt`, in that order |
| Dad | `voices/dad.txt` (11 lines, includes reading Mr. Pell's note aloud) |
| Mom | `voices/mom.txt` (2 lines) |
| Theo, 6 | `voices/theo.txt` (5 lines; the address lines are sung) |
| Sam, 12 | `voices/sam.txt` (4 lines) |
| Mrs. Dabrowski | `voices/dabrowski.txt` (2 lines) |
| Mr. Pell / "Hushabye" | `voices/pell.txt` (8 lines) |
| 911 dispatcher | `voices/dispatcher.txt` (3 lines) |
| Officer Reyes | `voices/officer.txt` (1 line) |

Each line in a lines file is separated by an empty line. Generate them all in one go, or one line at a time if a line comes out wrong.

---

## 1. Narrator (Sam, grown up): full, steady, energetic voice; no breathiness, no breaths

DESCRIPTION
```
Male narrator in his late twenties to early thirties, General American accent. A light baritone, mid-to-high for a man, with a clear, bright, fully voiced tone: no breathiness, no audible breaths, no rasp. An energetic, confident YouTube horror storyteller who grabs you from the first word: projected, punchy and animated, always at a full, steady speaking level, never quiet and never whispering. The opening hook is delivered with raised pitch and urgency. Very expressive, wide pitch movement and strong emphasis on key words; tension comes from intensity, pace and sharp pauses, not from dropping the volume. Brisk pace, around 160 words per minute. Turns warm, sincere and kind when giving advice at the end. Clear diction, crisp consonants. Not an announcer or movie-trailer voice, no growl, no cartoon acting. Studio-quality recording, perfect audio quality: dry, clean, no reverb, no background noise, no music.
```
PREVIEW
```
If you hear scratching inside your walls at night... don't knock back. My dad said it was the old house settling. Mice, maybe. Pipes. But mice don't breathe. And pipes don't stop when you stop. I pressed my ear to the wall above my bed... and something on the other side pressed back. Okay. Breathe. You can turn a light on now. If something in your home feels wrong, say it out loud to someone you trust. And keep saying it, until someone listens.
```

## 2. Dad

DESCRIPTION
```
A man in his early forties, General American accent. A warm, easygoing baritone with a relaxed, friendly smile in his voice: a practical, cheerful dad who always has a sensible explanation and wants everyone to calm down. Casual, reassuring, a little amused, gently teasing his kids, never angry. In his last line he has just been woken up and is starting to worry. Natural and conversational, not theatrical. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
Handy. Well, that's every noise explained. It's a nightmare, buddy. The mask is in the garage. Taped shut. Mice. The note said. Vent's right under it. Old wiring, Sam. Go back to bed, champ, I'll check it in the morning.
```

## 3. Mom

DESCRIPTION
```
A woman in her late thirties, General American accent. A clear, warm mid-range voice, organized and practical, a little tired after a long move but kind. Speaks plainly and politely, slightly puzzled when something does not add up. Natural and conversational, no theatrical acting, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
We don't have an attic light. It's sealed. Front door, back door, garage door, all locked. Theo, you checked behind me, right? Good. Okay, everybody, lights out.
```

## 4. Theo, six years old

DESCRIPTION
```
A six-year-old boy, General American accent. A small, high, bright child's voice, sweet and earnest. He says strange things in a matter-of-fact way, as if they are obvious. When he sings his made-up address song it is simple and sing-song, a little off-key, like a kindergartner. Natural child timing, short phrases. A real child, not a cartoon voice and not an adult imitating a child. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
He lives in the wall. He sings hush-a-bye, hush-a-bye. He has a sad dog face. Fourteen Larkspur Lane. Maple Falls. That's my house. That's my name.
```

## 5. Sam, twelve years old

DESCRIPTION
```
A twelve-year-old boy, General American accent. A clear young voice just before it breaks, mid-high pitch, smart and observant. Speaks quietly and seriously, trying hard to stay brave; in his last line he is scared but firm and very clear. A believable real kid, not a cartoon and not an adult imitating a child. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
Night, Dad. Mice don't twist the bread bag shut. Dad. Your shirt is upstairs. He's wearing it. I'm not dreaming. I saw his eye in the wall.
```

## 6. Mrs. Dabrowski, the neighbour across the street

DESCRIPTION
```
A woman in her late sixties, General American accent. Friendly, chatty and a bit nosy: a bright, slightly reedy older voice with a smile in it, gossiping over a pie dish. Unhurried, warm, a little conspiratorial, as if she is telling you something you really should know. Natural, not a caricature. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
Welcome to the street! I brought you a cherry pie. Your attic light's on every night, you know. Right around two. I see it from my kitchen window.
```

## 7. Mr. Pell, "Hushabye" (the man in the walls)

DESCRIPTION
```
An old man in his late sixties, General American accent. A soft, gentle, very slow voice that is unsettlingly tender, like someone singing a lullaby to a child who is not his. Low and close, mostly hushed and murmured, patient and polite, with long pauses; he never shouts and never growls. Creepy because he is so calm and so kind. In his last two lines, unmasked, he sounds tired, plain and lonely. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
Off. Hush-a-bye. Shhh. Just the pipes. Old houses settle. It's only mice. Go back to sleep. Fourteen Larkspur Lane... that's my house. That was my room. When I was a boy.
```

## 8. 911 dispatcher

DESCRIPTION
```
A 911 dispatcher, a woman in her forties, General American accent. Calm, steady, warm and completely in control: clear, firm and quick without sounding rushed, every word easy to understand. A reassuring authority that makes a scared family feel safe. Natural and professional, not robotic. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
Nine-one-one, what's the address of your emergency? Okay. Stay in that room. Keep the door locked. Officers are two minutes away. Stay on the line with me.
```

## 9. Officer Reyes

DESCRIPTION
```
A police officer, a woman in her thirties, General American accent. Confident, steady and matter-of-fact, kind with children, the calm voice of someone used to tense nights. Clear, mid-low pitch, no drama. Clear voice, no breathiness. Studio-quality recording, perfect audio quality: dry, no reverb, no background noise.
```
PREVIEW
```
Lawrence Pell. You're safe now, all of you. You did everything right. You stayed in the room, you kept the door locked, and you called. That's exactly how it's done.
```

---

Note: each designed voice is new and belongs to your account; none of them copies a real person. If a child voice comes out sounding too old, generate again; if it still does, we can fix the pitch in post.

---

## Eleven v4 versions of the lines (`voices_v4/`)

The same words as `voices/`, with Eleven v4 audio tags: short directions in square brackets at the start of a paragraph or line. The model follows them; it does not read them aloud.

- Generate with the Eleven v4 model. If there is a stability setting, start with Natural.
- The narrator has delivery tags only, and none of them makes him quiet: like our earlier films, he stays at a full, steady level the whole time and is at his most energetic in the opening. Tension comes from intensity, pace and pauses. There is no whispering, no sighs and no breaths. Mr. Pell is the only voice that whispers.
- There are no sound-effect tags. We add every sound ourselves.
- The narrator is in 6 parts, each under 2,400 characters. Generate them in order with the same voice.
- If a tag is ever read out loud or makes a line sound wrong, delete that tag and generate the line again.
