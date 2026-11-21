# Sound credits

Paste the block below into the video description. CC BY items require it; the CC0 credits are courtesy.
The owner's Epidemic Sound tracks and effects are licensed through the channel's subscription and need no credit.

## This film: "If The Ice Cream Truck Plays Its Song In Winter... DON'T GO OUTSIDE"

Epidemic Sound (the owner's subscription; catalogued in audio/catalog_epidemic_ice.json, never copied out of
_work/samples, never committed). The new set (_work/samples/epidemic_ice: 54 effects, 14 tracks, each judged in
_work/mix/sfx_review.md) first, then the bus, doctor, bunny, dummy, delivery, police and mirror sets through the
symlinks in _work/samples. Keep the channel connected in the Epidemic account so Content ID does not claim the tracks:
Throbbing Anxiety and I'm the Villain (Dream Cave), The Haunted and Sleep Forever (Luella Gren), Unvaried (Elin Piel),
Impossible Theory (Rachel Sandy), Escalation (Jon Bjork), Redeemed (Blue Saga), Lullaby before Christmas and A Heart
Full of Spring (Franz Gordon), With the Dawn and Peaceful Melody (Megan Wofford), and the earlier sets' Turning Stones
(Stefan Ekstrom), Are You Alone (Victor Lundberg), All Exits Closed (Guy Copeland), When the Sun Sets (Anna
Landstrom), Can They See Us (Experia), Come Closer and Don't Look (Belladonna Strings), The Forgotten Memories (Luella
Gren), Irene (Kevin Dailey), Dark Forebodings (Ethan Sloan). Rejected: Tears of a Shadow and City of Light (Eva
Hummingbird: voice-like fragments heard by the recogniser; never under the narration), and five effects (cicadas
under a winter wind, a reverse beeper, two synthetic power-downs, a cotton-jacket hug).

HIS CHIME (audio/chime_ice.py) is an ORIGINAL melody composed for this film (no existing song or jingle), synthesised
(music-box tines, a string pad) with the free library's celesta and soft piano samples (VSCO-2-CE / A Sampled Celesta,
CC0; Salamander grand, CC-BY: credited in the shared block below).

Where each SFX name of this film (audio/sfx_ice.py ICE_NAMES) comes from (source names: epidemic_catalog.ICE_MAP):
| name | source (Epidemic set: file) | processing / synthesis |
|---|---|---|
| cold_night, frozen_still, house_cold | ice: Wind General Winter Wind 02/05, Wind Designed Storm Winter 08/09; ice: Doors Creak Designed Eerie Wood Creaks; ice: Ice Friction / Ice Break | wind low/high-passed, the designed wind high-passed as a whistle; creaks cut to singles, far; ice ticks thinned |
| house_hum, power_cut | doctor: Machines Appliance Fridge Hum / Refrigerator Low Hum; ice: Wall Heater Furnace Pinging Hiss; ice: Light Switch | power_cut: the hum varispeeded down to a stop; mains clunk synthesised |
| furnace_die, furnace_start | ice: Wall Heater Furnace (run down); ice: HVAC Boiler Start | relay click and cooling tick synthesised (modal) |
| snow_walk, snow_run, snow_deep, snow_scuff | ice: Footsteps Boots Snow Walk, Snow Walk 03/04, Snow Run 04/10/11, Running Pass By, Boots Snow Scuff | single steps cut out; deep: slowed 0.8-0.88x, low shelf, scuff drag |
| mitten_drop, cone_set | ice: Snow Walk (crunch grain), Ice Friction Subtle | woollen pat and wrapper whisper synthesised (filtered noise) |
| boot_stuck, boot_rip | ice: Ice Friction Crunchy; ice: Ice Break; ice: Cloth Misc Scrape | slowed strain; groan modes synthesised |
| shovel_scrape, shovel_morning | ice: Snow Manual Snow Plow Metal 01/03, Plastic; ice: Shovel Dig In Snow 02/03/09 | blade-knock synthesised; three shovels placed left / centre / right |
| plow_pass, plow_horn | ice: Freight Truck Lorry Moving, Truck Passby 02; bus: Metal Friction Scrape (blade); ice: Fire Truck Air Horn Blaring, Truck Air Horn Three Honks | doppler pass and pan synthesised; blade slowed 0.7x |
| truck_idle, truck_glide | ice: Van Idle Exterior Rear Loop 02, Van Mercedes Diesel Idle | idle slowed 0.92x; glide: engine only (no tire noise), doppler synthesised |
| serving_window, window_crack | ice: Plastic Sliding Window Small; ice: Windows Wood Sliding Open/Close, Hotel Vertical Sliding Window | frost-seal crackle and air hiss layered |
| truck_speaker | synthesised (pop, mains hum, crackle through the horn band) | |
| door_tap, door_slam, door_open_street | earlier sets' knocks (knock_door recipe); bunny: Doors Wood Impact Light Door; mirror: Doors Creak Wooden Door Creaks | frame boom and latch synthesised |
| cone_shatter | bus / bunny: Glass Break (smash grains); ice: Ice Break | floor knock and skittering shards synthesised |
| frost_creep, doorknob_frost, frost_wipe | ice: Ice Friction Subtle Pressure Cracks 01/02, Ice Crackle Squeeze Whoosh 03/13, Crunchy; ice: Cloth Misc Scrape | high-passed fizz; brass ping synthesised |
| radio_squelch, radio_static, radio_bells, radio_clean | bus: Walkie Talkie Engage, Squelch Stuttering; bus: Static Radio Station Search; doctor: Walkie Talkie White Noise Hiss; dummy: Radio Device Turn On | radio band and drive; HIS BELLS from chime_ice.bells (original) |
| skin_stretch | bus: Rubber Friction Latex Glove Pull (glove_squeak); ice: Eerie Wood Creaks | an octave down, low-passed: no wetness |
| bone_crack, jaw_drop | ice: Gore Bone Crack Cracking, Broken Bone Twist Dislocate 01; bunny: Gore Bone Break Heavy / Snap 04 | dry crack transients only (<= 0.3 s, high-passed); jaw pop sub and hinge creak synthesised / slowed |
| uniform_tear, leg_punch, leg_spear_coat | bus: Cloth Rip Shorts / T-Shirt / Tear 02; ice: Cloth Misc Scrape; bunny: Fight Grab Punch Cloth | leg swish and chitin clicks synthesised |
| leg_click, leg_stab_snow, scuttle, attic_crawl, leg_tip_tile | bus: Seat Belt Click Lock; doctor: Crocodile Clip; dummy: Mechanical Click Metal; ice: Snow Walk, Ice Break; bus: Metal Friction Scrape | chitin modes and surface bodies (metal, wood, ice, tile, snow) synthesised; attic: through the ceiling |
| hatch_drop | ice: Doors Wood Hatch Open Close; ice: Boats Metal Hatch Open | bang and grit synthesised |
| blanket_yank, towel_jam | ice: Cloth Flap Towel, Towel Drying Back | slowed, low shelf; snag click synthesised |
| porch_light, street_wakes | ice: Fluorescent Light Switch On/Off (3 files); mirror: Door Creaks | street distance and bulb ping synthesised |
| ambulance | doctor: Siren Ambulance 70s Distant / In Motion / Wailing | approach level, final wind-down varispeed |
| cocoa_mug, curtain_yank | dummy: Cup Mug Teaspoon, Tea Cup Placing (mug_set recipe); earlier curtain_close recipe | |

## The Bus film: "If The School Bus Stops At Midnight... DON'T GET ON"

Epidemic Sound (the owner's subscription; catalogued in audio/catalog_epidemic_bus.json, never copied out of
_work/samples, never committed). The bus set (_work/samples/epidemic_bus: 98 effects, 11 tracks, each judged in
_work/mix/sfx_review.md) first, then the doctor, bunny, dummy, delivery, police and mirror sets through the symlinks
in _work/samples. Keep the channel connected in the Epidemic account so Content ID does not claim the tracks:
Through the Portal (Anthony Earls), The Last Horizon (Aerian), At First Light (Gavin Luke), A Sky Unveiled (Megan
Wofford), Terra Firma (Dream Cave), Chronometer and All Exits Closed (Guy Copeland), Can They See Us (Experia), Wait
for Me on the Other Side (Instrumental, CLNGR), Just a Little Sunshine (Instrumental, Staffan Carlen), and the
earlier sets' Afterthoughts, End of Rain, The Haunted, Midnight Wanderer, Dark Tunnels, Dark Forebodings, Annihilated,
Come Closer, Don't Look, Escalation, Irene, Code of Violence. Rejected: Sweeter (Blood Harmony: a song with vocals)
and Deep Down in the Caverns (a trailer track found in the effects zip).

Where each SFX name of this film (audio/sfx.py BUS_NAMES) comes from:
| name | source (Epidemic set: file) | processing / synthesis |
|---|---|---|
| suburb_night | police: Ambience Suburban Night (crickets, distant traffic / train), police: suburban night with distant dog barks | low/high-passed; inside=True darkened through the glass |
| dog_far | police: the distant dog barks | grains, low-passed, street reverb |
| street_flicker | doctor: Electricity Buzz Hum, Interference Buzz | gated drop-outs; starter ticks and ballast thunk synthesised |
| bus_air_brake | bus: Air Burst Bus Air Brake Compressor; Vehicles Bus Air Brake Compressor | longest hiss grain; chassis thump synthesised |
| bus_idle, his_bus_interior | bus: Bus Engine Idle; Engine Perspective Idle; Long Journey Standing Still Idle | looped; his: 1.5 st down, loping miss, synthesised panel rattle; interior: ballast hum and tape hiss synthesised |
| bus_door | bus: Bus Door Open Close No Engine 01/03/04; Interior Door Open Close; Air Burst Door | first phrase = open, last = close; rubber and sheet-metal slap synthesised |
| his_unfold | bus: Bendy Pole Light Stretch Bend Creak 03 | a fifth down, rising per segment; latch clicks synthesised |
| pa_crackle | bus: Microphone Feedback Single; Speaker Feedback Resonance; Megaphone Feedback; Phonograph Vinyl Crackle (authentic) | band-passed to the horn; pops synthesised |
| bus_pull_away, bus_rewind | bus: Bus Engine Start Drive Away; Generic By Bus Pass By (fast / medium); dummy: Videotape VHS Rewind | rewind: reversed, varispeed 0.8-3x, tape-skip tail |
| bus_horn | bus: Horn Bus Close Long; Many Short; Very Long | grains |
| bus9_start, bus9_drive, bus_fast_night, morning_bus | bus: Engine Start Drive Away; Interior On Board Driving; Double Decker Ride (rattle); doctor: Car Interior Fast Driving at night; bus: School Children Talking / Big Crowd of Kids walla | layered, low-passed |
| tire_screech, bus_swerve | bus: Car Brake Tire Skid 05; Skid Peugeot / Far | 2 st down; lurch and rattle synthesised |
| mirror_rip | bus: Metal Friction Scrape Large Loud 01/03; Glass Break Car Window (MKH 50 / Sanken) | housing crack and sub boom synthesised |
| dash_radio | bus: Static Radio Station Search Crackling | band-limited; squelch pops synthesised |
| whistle | bus: Referee Whistle 01, 02, 10 Metres Distance | each blast tuned to A7 (the jingle's hook); long blast looped |
| ticket_punch | bus: Office Supplies Hole Punch Single (x2), Hole Punch Through Pages, Kanex Paper Hole Puncher | click + clack grains; metal ring synthesised |
| deadbolt | police: Door Deadbolt Open Close Turn; Mortise Lock Turn | grains |
| walkie | bus: Transceiver Walkie Talkie Engage; Squelch Stuttering Glitchy (short / long) | roger beep synthesised |
| power_down, power_up | bus: Fluorescent Light Buzz Short Power Up Light Switch (2 takes) | the mains hum dive and thunk synthesised |
| run_asphalt | bus: Footsteps Asphalt Sneaker Running (2 takes) | grains |
| cat_rumble | bus: Cat Wild Lion Growling Low Rumble 02/03; Tiger Defensive Growling Deep Rumble | a fourth down, low-passed 350 Hz |
| glove_squeak | bus: Rubber Latex Glove Pull Stretch Squeak; Surgical Glove Pull Off Stretch Squeak Slap | knuckle pops synthesised |
| tape_skip | bus: UI Glitch Crackle 03, Databend 04, Glitches; Tape Play Stop Electrical Hum Static | 42 ms stutter; tracking tear synthesised |
| crt_on | bus: Vintage CRT Monitor Commodore 1084S Power On Off (power-on phrase, low-passed 9 kHz); Hifi Old Turn On | degauss and 15.7 kHz whine synthesised |
| vhs_tape, tape_ff | bus: Videotape VHS Eject; Tape Hand Camera Fast Forward Edit Mode Stop; dummy: Videotape Into VHS | stop clunk synthesised |
| tape_slide | synthesised (hiss and hum diving half a speed) | |
| seatbelt | bus: Car Seat Belt Click Into Lock; Click Lock 01/03 | grains |
| flag_rope, school_night | bus: Cable Clanking Post Flag Flapping 02; Sailboat Rope Clanking Mast; police crickets | |
| broom_bend, broom_crack | bus: Bendy Pole Creak (a fourth down); Wood Break Stick Branch Snap In Two; Snapping Branches | thump synthesised |
| cloth_rip | bus: Cloth Rip T Shirt Tear; Shorts Thin Material Tear 02; Tear 02 | cut to 0.55 s |
| school_bell | doctor: Alarms Bell School Bell Classic Ringing | low-passed 7 kHz, schoolyard space |
| clipboard_drop | doctor: crocodile clip | board bounces and asphalt grit synthesised |
| mailbox_unscrew | bus: Flashlight Torch Small Head Cap Unscrew | tin letter tink synthesised |
| dial_911 | synthesised (DTMF 9-1-1, US ring-back 440+480 Hz, the error tones) | |
| porch light, peephole, knocks, ticket under the door, bare feet on the stairs, running on grass, tape hiss | the earlier films' recipes (light_switch, peephole, knock_door, paper_under_door, footsteps_stairs (mirror: barefoot walk, wood stairs), footsteps_grass, tape_hiss) | |

Our own material (no licence needed): the "Ride Right with Mister Whistlestop!" PSA jingle (audio/jingle_bus.py) is an
ORIGINAL 8-bar tune written for this film (no melody of any existing song): its FM synth brass, pea whistle, toy piano,
music box, tine e-piano, synth bass, drums, string pad and flute tone are synthesised; its glockenspiel (VS Chamber
Orchestra CE), celesta (A Sampled Celesta), hand claps (Body Percussion) and soft piano (Scary Piano) are CC0 samples
already in the library (credits below). The voice FX (mix.py: tv, his, loudspeaker, door, walkie, radio, phone,
mimic, mimic_slide) are processing only.

## The Doctor film (kept for reference)

This film ("If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND") uses six Epidemic sets (catalogued in
audio/catalog_epidemic_doctor.json, never copied out of _work/samples, never committed): the doctor set
(_work/samples/epidemic: 90 effects and 12 tracks, each judged in _work/mix/sfx_review.md: 52 effects used, 15 used
only after processing, 22 rejected; 8 tracks used, 2 in reserve, 2 rejected), and the bunny, dummy, delivery, police
and mirror sets through the symlinks in _work/samples. Keep the channel connected in the Epidemic account so Content
ID does not claim the tracks (The Forgotten Memories, It's Late, Lens Flare 3, Beauty Lives in Me, Prosper, In Those
Hazel Eyes, Follow Your Feet, and the earlier sets' dark tracks: Are You Alone, Haunted Mind, When the Sun Sets, Dark
Tunnels, In Continuum, Irene, The Haunted, Come Closer, Escalation, Turning Stones, A Massive Mist, Don't Look, Dark
Forebodings, End of Rain).

Our own material (no licence needed): the HOLD MUSIC (audio/hold.py: an original 8-bar lounge melody written for this
film, every version synthesised: vibraphone, tine e-piano, synth bass, brushes, pad; no melody of any existing song;
the celesta doubling in its warm version is the CC0 "A Sampled Celesta" below) and Grandma humming it (audio/voicesynth.py:
the narrator's own recording resynthesised in the cast's 'G' voice). Synthesised sound (sfx.py): the landline bell's
gongs, the fluorescent ballast hum, the dead TV, the dial tone, the wipers, the ring-back, and the modal bodies.
The Bunnyman film's notes follow.

No new third-party sound was downloaded for this film: the free hosts (Freesound, OpenGameArt, Wikimedia Commons) are
not reachable from the work machine, and nothing the film needed was missing. What the recordings could not give is
made here and owes nobody a credit:
- The Pemberton's Department Store jingle is an ORIGINAL tune written for this film (audio/jingle.py: melody,
  harmony, arrangement); its toy piano, music box, e-piano, bass, kick and shaker are synthesised; its glockenspiel
  (VS Chamber Orchestra CE), celesta (A Sampled Celesta), hand claps (Body Percussion) and low piano (Scary Piano)
  are CC0 samples already in the library.
- The hums, the real Laurie's broken singing and her crying are the film's own narration (the owner's voiceover)
  re-synthesised with the WORLD vocoder in the cast's voices (audio/voicesynth.py, tools/vo_voices.py): no library
  voice. The bunny set's crying file (a three-year-old boy) is rejected.
- The plastic egg's shell, the ring's ring, the brass mail-slot flap, the barrel's steel ticks, the bare bulb, the
  zipper, the curtain rings and the VHS pause are synthesised layers over the recordings named in sfx.py.
- Final mix (sfx.py FINAL_NAMES, for the picture's own cue names): the trade under the hand ('swap': a reversed
  swell into a thump and a glassy C#), the felt marker striking HOLLOWAY out, Mom's running kitchen tap, the creek
  under the railroad bridge and the fridge magnet's clack are synthesised; the steps on grass are the Free-SFX
  collection's CC0 grassy footsteps (owlishmedia), the gusts in the trees the civitas CC0 gusts, the patrol cars' radio
  the police set's Epidemic walkie recording (band-limited). All three sources are already in the credits below.
A line whose files the final mix does not use may be dropped; keeping every line is always safe.

```
Sound credits:
- "Oculus Audio Pack 01" by Oculus VR, LLC (https://developers.meta.com/vr/downloads/package/oculus-audio-pack-1/), licensed under CC BY 4.0.
- "Salamander Grand Piano" samples by Alexander Holm (sfz remap by kinwie, https://github.com/sfzinstruments/SalamanderGrandPiano), licensed under CC BY 3.0.
- Impulse response "1st Baptist Church Nashville" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, recorded by Adam Townsell, licensed under CC BY 4.0.
- Impulse response "Abies Grandis Forest, Wheldrake Wood" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- Impulse response "Arthur Sykes Rymer Auditorium, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- Impulse response "Central Hall, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, recorded by Alexander Vilkaitis, Ilias Antonopoulos, Joska De Langen, Xuan Liu, licensed under CC BY 4.0.
- Impulse response "Genesis 6 Studio live room, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- Impulse response "Jack Lyons Concert Hall, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- Impulse response "R1 Nuclear Reactor Hall, Stockholm" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, recorded by Audiolab (University of York), Dr. Damian T. Murphy, licensed under CC BY 4.0.
Additional public-domain (CC0) sounds and instruments: A Sampled Celesta; AtomCut library (OpenGameArt / Kenney CC0 packs); Body Percussion; Double Bass (noises); Free-SFX (public domain collection); Kenney Impact Sounds; Kenney Interface Sounds; Kenney RPG Audio; Scary Piano; Sonic Pi bundled samples; VS Chamber Orchestra: Community Edition; War Tuba; civitas recordings (Freesound CC0); victor-effects starter pack (Freesound CC0).
```

## CC BY items in the library

- 71 file(s): "Oculus Audio Pack 01" by Oculus VR, LLC (https://developers.meta.com/vr/downloads/package/oculus-audio-pack-1/), licensed under CC BY 4.0.
- 143 file(s): "Salamander Grand Piano" samples by Alexander Holm (sfz remap by kinwie, https://github.com/sfzinstruments/SalamanderGrandPiano), licensed under CC BY 3.0.
- 2 file(s): Impulse response "1st Baptist Church Nashville" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, recorded by Adam Townsell, licensed under CC BY 4.0.
- 2 file(s): Impulse response "Abies Grandis Forest, Wheldrake Wood" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- 1 file(s): Impulse response "Arthur Sykes Rymer Auditorium, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- 2 file(s): Impulse response "Central Hall, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, recorded by Alexander Vilkaitis, Ilias Antonopoulos, Joska De Langen, Xuan Liu, licensed under CC BY 4.0.
- 1 file(s): Impulse response "Genesis 6 Studio live room, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- 1 file(s): Impulse response "Jack Lyons Concert Hall, University of York" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, licensed under CC BY 4.0.
- 1 file(s): Impulse response "R1 Nuclear Reactor Hall, Stockholm" from the OpenAIR library (www.openairlib.net), Audiolab, University of York, recorded by Audiolab (University of York), Dr. Damian T. Murphy, licensed under CC BY 4.0.

## CC0 sources (no attribution required)

- A Sampled Celesta: https://github.com/Digital-Defiance/copyist-celesta
- AtomCut library (OpenGameArt / Kenney CC0 packs): https://github.com/novincode/atomcut-library
- Body Percussion: https://github.com/sfzinstruments/body_percussion
- Double Bass (noises): https://github.com/sfzinstruments/dsmolken.double-bass
- Free-SFX (public domain collection): https://github.com/EternityForest/Free-SFX
- Kenney Impact Sounds: https://kenney.nl/assets/impact-sounds
- Kenney Interface Sounds: https://kenney.nl/assets/interface-sounds
- Kenney RPG Audio: https://kenney.nl/assets/rpg-audio
- Scary Piano: https://github.com/sfzinstruments/karoryfer.scarypiano
- Sonic Pi bundled samples: https://github.com/sonic-pi-net/sonic-pi/tree/main/etc/samples
- VS Chamber Orchestra: Community Edition: https://github.com/sgossner/VSCO-2-CE
- War Tuba: https://github.com/sfzinstruments/karoryfer.war-tuba
- civitas recordings (Freesound CC0): https://github.com/reneodlt/civitas/tree/main/packages/client/src/audio
- victor-effects starter pack (Freesound CC0): https://github.com/victorrentea/victor-effects/tree/main/starter-pack

## Upstream authors of the CC0 effects (courtesy)

Anthousai, Breviceps, Dashman71, Donmann, Framefive, IENBA, Kenney, Manicciola, PuplPndaHimwx, SecureSubset, SpliceSound, TiesWijnen, TitanKaempfer, Tony B kksm, Weak_Hero, abhisheky948, felix.blume, ftpalad, hyderpotter, jwheeler91, loudernoises, mirceakitsune, mireia_af, owlishmedia, patchytherat, qubodup, robotjay, rubberduck, sengjinn, sofialomba, sqeeeek, thegoosington, unicaegames, various (OpenGameArt / Freesound CC0 uploads), wjtaylor.
