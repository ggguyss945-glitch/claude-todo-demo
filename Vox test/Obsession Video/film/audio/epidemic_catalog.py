"""Catalogue of the owner's Epidemic Sound downloads (licensed through the owner's subscription; never commit or copy
the audio out of the sample folders).

    python3 epidemic_catalog.py --obsession           THIS film ("If a Girl Is OBSESSED With Being Your Only Friend...
                                                      DON'T WRITE YOUR NAME"): writes audio/catalog_epidemic_obsession.json
                                                      from W/samples/epidemic_obsession (the owner's new set: ONE flat
                                                      folder, 70 effects + 20 tracks, music told apart by name) FIRST,
                                                      then every earlier set linked beside it (read only; rows of
                                                      unchanged files are reused from the ice / bus / doctor
                                                      catalogues). The film's source names are OBSESSION_MAP.

    python3 epidemic_catalog.py --ice                 THIS film ("If The Ice Cream Truck Plays Its Song In Winter...
                                                      DON'T GO OUTSIDE"): writes audio/catalog_epidemic_ice.json from
                                                      W/samples/epidemic_ice (the owner's new set: sfx/ 54 effects, music/
                                                      14 tracks) FIRST, then the bus, doctor, bunny, dummy, delivery,
                                                      police and mirror sets linked beside it (read only; rows of
                                                      unchanged files are reused from the bus catalogue). The film's
                                                      source names are ICE_MAP (sfx.py's ICE block draws on them).

    python3 epidemic_catalog.py --bus                 THIS film ("If The School Bus Stops At Midnight... DON'T GET ON"):
                                                      writes audio/catalog_epidemic_bus.json from W/samples/epidemic_bus
                                                      (the bus set: sfx/ 98 effects, music/ 11 tracks) FIRST, then the
                                                      doctor (W/samples/epidemic, flat), bunny, dummy, delivery, police
                                                      and mirror sets (read only; rows of unchanged files are reused
                                                      from the doctor / bunny / dummy / delivery catalogues). A music
                                                      file found in sfx/ is kept out of every name (stray: true).

    python3 epidemic_catalog.py --doctor              THIS film (the Doctor film): writes audio/catalog_epidemic_doctor.json
                                                      from W/samples/epidemic (the doctor set: ONE flat folder, 90
                                                      effects + 12 tracks, music told apart by name) then the bunny,
                                                      dummy, delivery, police and mirror sets (read only)
    python3 epidemic_catalog.py --bunny               the Bunnyman film: writes audio/catalog_epidemic_bunny.json
                                                      from all five sets, in this order (first set wins on duplicates):
                                                      W/samples/epidemic (the bunny set: 70 mp3 effects, parade crowds,
                                                      knuckle knocks, glass, door kick-ins, axes, fights, bones, fire,
                                                      plastic boxes, rings, coins, books, music boxes, owls, hospital
                                                      ambiences; 10 tracks), then epidemic_dummy, epidemic_delivery,
                                                      epidemic_police, epidemic_mirror (symlinks to the earlier films'
                                                      folders, read only). Rows of W/catalog_bunny_new.json (the first
                                                      analysis of the bunny set) and of audio/catalog_epidemic_dummy.json /
                                                      catalog_epidemic_delivery.json whose file is unchanged (same set,
                                                      slug and size) are reused, so a rebuild only recomputes `serves`
                                                      (--no-reuse analyses everything again)
    python3 epidemic_catalog.py --dummy               THIS film (the ventriloquist dummy): writes
                                                      audio/catalog_epidemic_dummy.json from all four sets, in this order
                                                      (first set wins on duplicates): W/samples/epidemic (the dummy set:
                                                      mp3, studio laughter, TV/VHS, spoon and mug, wooden clicks, voices,
                                                      heart monitor, 11 vintage tracks), epidemic_delivery, epidemic_police,
                                                      epidemic_mirror (symlinks to the earlier films' folders, read only).
                                                      Rows of audio/catalog_epidemic_delivery.json whose file is unchanged
                                                      (same set, slug and size) are reused, so only the new set is analysed
                                                      (--no-reuse analyses everything again)
    python3 epidemic_catalog.py --delivery            the delivery film: writes audio/catalog_epidemic_delivery.json from
                                                      W/samples/epidemic (new set), epidemic_police and epidemic_mirror
    python3 epidemic_catalog.py <out.json> <set>=<dir> [<set>=<dir> ...]     any list of sets (first set wins on duplicates)
    python3 epidemic_catalog.py <epidemic dir> <out catalog_epidemic.json>   the police form (one set, kept working)
    --sfx-only                                        skip the (slow, ~10 s per track) music analysis and keep the music
                                                      entries of an existing output file

Each set folder holds audio in <dir>/sfx and <dir>/music (music_unverified and _zips are ignored): 48 kHz WAVs in
the earlier sets, MP3 (48 kHz) in the dummy set; any of .wav .mp3 .flac .ogg is read (soundfile / libsndfile 1.2).
For every SFX: set, slug (lower-case words joined by '_', so 'Bells, Doorbell, Ding Dong, Single.wav' ->
'bells_doorbell_ding_dong_single'; the Epidemic download dressing 'ES_', ' - Epidemic Sound' and copy markers ' (1)'
are dropped, so 'ES_Wooden Pole, Hit Wood 02 - Epidemic Sound.mp3' -> 'wooden_pole_hit_wood_02'; the police files
keep their slugs), path (absolute, through W/samples), duration,
integrated loudness, sample peak, onset count, and `serves`: the SFX names in sfx.NAMES (police + delivery) it can
build. A file present in two sets (same slug, or same size and first megabyte) is listed once, under the first set,
with `also_in`.
For every music track: duration, loudness, a 2-second short-term loudness curve, a brightness curve (spectral
centroid), tempo and pulse clarity, tonal centre (chroma argmax), key and mode (Krumhansl profiles), bass root (lowest
octave chroma), loudness p10/p50/p90, centroid median, and section boundaries (agglomerative on MFCC + chroma) with
each section's mean loudness and brightness, so the score can cut and layer tracks to the film's intensity curve.
"""
import hashlib, json, os, re, sys
import numpy as np, soundfile as sf

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.normpath(os.path.join(HERE, '..', '_work'))
DELIVERY_SETS = [('delivery', os.path.join(W, 'samples', 'epidemic')),
                 ('police', os.path.join(W, 'samples', 'epidemic_police')),
                 ('mirror', os.path.join(W, 'samples', 'epidemic_mirror'))]
DELIVERY_OUT = os.path.join(HERE, 'catalog_epidemic_delivery.json')
DUMMY_SETS = [('dummy', os.path.join(W, 'samples', 'epidemic')),
              ('delivery', os.path.join(W, 'samples', 'epidemic_delivery')),
              ('police', os.path.join(W, 'samples', 'epidemic_police')),
              ('mirror', os.path.join(W, 'samples', 'epidemic_mirror'))]
DUMMY_OUT = os.path.join(HERE, 'catalog_epidemic_dummy.json')
BUNNY_SETS = [('bunny', os.path.join(W, 'samples', 'epidemic')),
              ('dummy', os.path.join(W, 'samples', 'epidemic_dummy')),
              ('delivery', os.path.join(W, 'samples', 'epidemic_delivery')),
              ('police', os.path.join(W, 'samples', 'epidemic_police')),
              ('mirror', os.path.join(W, 'samples', 'epidemic_mirror'))]
BUNNY_OUT = os.path.join(HERE, 'catalog_epidemic_bunny.json')
BUNNY_FIRST = os.path.join(W, 'catalog_bunny_new.json')          # the first analysis of the bunny set (reused)
# the Doctor film ("If Your Doctor Calls At 3 AM... DON'T ASK WHAT THEY FOUND"): the new set is ONE flat folder
# (effects and music side by side: a music file is "ES_<Title> - <Artist>.mp3", an effect ends "- Epidemic Sound")
DOCTOR_SETS = [('doctor', os.path.join(W, 'samples', 'epidemic')),
               ('bunny', os.path.join(W, 'samples', 'epidemic_bunny')),
               ('dummy', os.path.join(W, 'samples', 'epidemic_dummy')),
               ('delivery', os.path.join(W, 'samples', 'epidemic_delivery')),
               ('police', os.path.join(W, 'samples', 'epidemic_police')),
               ('mirror', os.path.join(W, 'samples', 'epidemic_mirror'))]
DOCTOR_OUT = os.path.join(HERE, 'catalog_epidemic_doctor.json')
# the Bus film: the owner's new set (sfx/ + music/) first, then every earlier set linked beside it
BUS_SETS = [('bus', os.path.join(W, 'samples', 'epidemic_bus')),
            ('doctor', os.path.join(W, 'samples', 'epidemic')),
            ('bunny', os.path.join(W, 'samples', 'epidemic_bunny')),
            ('dummy', os.path.join(W, 'samples', 'epidemic_dummy')),
            ('delivery', os.path.join(W, 'samples', 'epidemic_delivery')),
            ('police', os.path.join(W, 'samples', 'epidemic_police')),
            ('mirror', os.path.join(W, 'samples', 'epidemic_mirror'))]
BUS_OUT = os.path.join(HERE, 'catalog_epidemic_bus.json')
# the Ice Cream film: the owner's new set (sfx/ + music/) first, then every earlier set linked beside it
ICE_SETS = [('ice', os.path.join(W, 'samples', 'epidemic_ice')),
            ('bus', os.path.join(W, 'samples', 'epidemic_bus')),
            ('doctor', os.path.join(W, 'samples', 'epidemic_doctor')),
            ('bunny', os.path.join(W, 'samples', 'epidemic_bunny')),
            ('dummy', os.path.join(W, 'samples', 'epidemic_dummy')),
            ('delivery', os.path.join(W, 'samples', 'epidemic_delivery')),
            ('police', os.path.join(W, 'samples', 'epidemic_police')),
            ('mirror', os.path.join(W, 'samples', 'epidemic_mirror'))]
ICE_OUT = os.path.join(HERE, 'catalog_epidemic_ice.json')
# THIS film (Obsession): the owner's new flat set first, then every earlier set
OBSESSION_SETS = [('obsession', os.path.join(W, 'samples', 'epidemic_obsession'))] + ICE_SETS
OBSESSION_OUT = os.path.join(HERE, 'catalog_epidemic_obsession.json')
AUDIO_EXT = ('.wav', '.mp3', '.flac', '.ogg')
NOTES = 'C C# D D# E F F# G G# A A# B'.split()

# SFX name -> filename keyword alternatives (every word of one alternative must appear in the slug). Police names first
# (unchanged), then the delivery film's names (sfx.py DELIVERY_NAMES).
MAP = {
    'knock_door': [['knock', 'wood'], ['knock', 'glass_panel'], ['knock', 'metal_garage']],
    'doorbell_chime': [['doorbell']],
    'footsteps_porch': [['footsteps', 'porch'], ['footsteps', 'creaky']],
    'footsteps_wood_inside': [['footsteps', 'creaky'], ['footsteps', 'barn'], ['footsteps', 'cabin'],
                              ['footsteps', 'barefoot']],
    'car_pass': [['car_pass']],
    'car_idle': [['idle']],
    'car_door_open': [['door_car']],
    'car_door_close': [['door_car']],
    'siren_far': [['siren']],
    'police_radio_squelch': [['walkie_talkie'], ['static_radio']],
    'radio_static': [['static']],
    'radio_click': [['ui_buttons_confirm'], ['click', 'pops']],     # (was ['click']: keeps the dummy set's wood clicks out)
    'bodycam_beep': [['camera', 'focus']],
    'phone_ring': [['phone_ringing']],
    'phone_busy': [['busy_tone']],
    'phone_vibrate': [['vibration']],
    'mail_slot': [['mailbox']],
    'paper': [['paper']],
    'key_in_lock': [['keys_jingle'], ['keys_car_keys'], ['deadbolt']],
    'lock_turn': [['deadbolt'], ['mortise_lock'], ['lock_entrance']],
    'chain_lock': [['security_chain'], ['chains', 'padlock']],
    'door_creak': [['doors_creak']],
    'breath': [['breath']],
    'heartbeat': [['heartbeat']],
    'whoosh': [['whoosh']],
    'riser': [['riser']],
    'braam': [['braam']],
    'impact_hit': [['stinger'], ['hit', 'impact']],
    'stinger': [['stinger']],
    'sub_drop': [['bass_drop'], ['bass_dive']],
    'ui_pop': [['menu_ui'], ['pops'], ['ui_buttons']],
    'tinnitus': [['tinnitus']],
    'ambience_night': [['ambience', 'suburban']],        # suburban streets only (not the mirror set's cabin / lake / tropical)
    'room_tone': [['room_tone']],
    'clock_tick': [['clocks', 'tick']],
    'crowd_whisper': [['whisper']],
    # ---- delivery film
    'doorbell_dingdong': [['doorbell', 'ding_dong'], ['doorbell_doorbell_0'], ['doorbell', 'ring_old']],
    'doorbell_cam_chime': [['notification'], ['text_message'], ['doorbell', 'ding_dong']],
    'phone_notify': [['notification'], ['text_message']],
    'box_knock': [['cardboard', 'impact'], ['cardboard', 'punch'], ['knock', 'wood']],
    'box_tap': [['cardboard', 'impact'], ['cardboard', 'lid'], ['cardboard', 'remove']],
    'box_creak': [['cardboard', 'rummage'], ['cardboard', 'lid'], ['cardboard_box_open']],
    'box_drop': [['cardboard', 'impact'], ['cardboard', 'lid']],
    'box_scrape': [['cardboard', 'drag'], ['box', 'drag'], ['box', 'scrape']],
    'box_open': [['cardboard_box_open'], ['cardboard', 'remove'], ['cardboard', 'rummage']],
    'box_voice': [['cardboard', 'rummage'], ['whisper'], ['breath', 'calm']],
    'tape_rip': [['tape', 'rip'], ['tape', 'tear']],     # (was ['tape']: keeps the dummy set's videotape out)
    'hazard_ticks': [['hazard']],
    'van_door_slide': [['van', 'sliding'], ['doors_sliding']],
    'van_idle': [['diesel', 'idle'], ['idle']],
    'van_pull_away': [['idle'], ['car_pass']],
    'van_step': [['footsteps', 'porch'], ['metal', 'impact']],
    'keys_drop': [['keys', 'drop'], ['glass', 'tap'], ['vase', 'tap']],
    'window_slide': [['windows', 'sliding'], ['doors_sliding']],
    'curtain_flutter': [['cloth', 'flap']],
    'cloth_rustle': [['cloth', 'handle'], ['cloth', 'wipe'], ['cloth_flap_towel']],
    'touch_tap': [['touch_screen'], ['touchscreen']],
    'stylus_scribble': [['glass', 'friction'], ['touch_screen']],
    'camera_shutter': [['camera']],
    'footsteps_stairs': [['stairs'], ['footsteps', 'barefoot']],
    'footsteps_hall': [['footsteps', 'barefoot'], ['footsteps', 'creaky']],
    'mom_breath': [['breath', 'calm'], ['breath', 'anxious'], ['whisper', 'female']],
    'mom_sob': [['breath', 'calm'], ['breath', 'anxious'], ['whisper', 'female']],
    'ambience_suburb': [['ambience', 'suburban']],
    'ambience_dawn': [['dawn'], ['birdsong', 'morning']],
    'room_tone_house': [['room_tone']],
    'flashlight_click': [['flashlight']],
    'bed_creak': [['bed', 'creak'], ['bunk_bed']],
    # ---- the dummy film (sfx.py DUMMY_NAMES): the dummy set first, the earlier sets as extra layers
    'case_latch': [['flightcase', 'latch'], ['metal_click'], ['briefcase', 'open']],
    'case_lid': [['briefcase', 'open'], ['wooden_box', 'lid'], ['shoe_box', 'lid']],
    'velvet': [['cloth', 'wipe'], ['couch', 'wipe'], ['cloth', 'handle']],
    'spoon_stir': [['spoon', 'stir']],
    'spoon_clink': [['spoon', 'clink'], ['single_glass_clink'], ['ramekins', 'clink'], ['spoon_stiring', 'placing']],
    'mug_set': [['spoon_stiring', 'placing'], ['ramekins', 'clink'], ['wooden_block', 'place']],
    'sip': [['breath', 'calm']],
    'dummy_clack': [['wooden_pole', 'hit'], ['wooden_block'], ['click', 'woody'], ['wooden_box', 'lid']],
    'dummy_jaw': [['wooden_box', 'lid'], ['wooden_block'], ['wooden_pole', 'hit']],
    'eyelid_click': [['click', 'woody'], ['metal_click'], ['wooden_block']],
    'wood_creak': [['bunk_bed'], ['bed', 'creak'], ['friction', 'wood'], ['doors_creak', 'wooden']],
    'wood_knock': [['wooden_block'], ['wooden_pole', 'hit'], ['wooden_box', 'lid'], ['knock', 'wood']],
    'tiny_steps': [['wooden_block'], ['click', 'woody'], ['wooden_pole', 'hit']],
    'glove_lift': [['cloth', 'handle'], ['cloth', 'wipe'], ['couch', 'wipe']],
    'hand_slot': [['cloth', 'handle'], ['couch', 'wipe'], ['wooden_box', 'lid']],
    'hand_squeeze': [['cloth', 'handle'], ['couch', 'wipe']],
    'dummy_thud': [['cloth', 'impact'], ['wooden_block'], ['bunk_bed', 'jump']],
    'tv_on': [['hifi', 'turn_on'], ['radio', 'turn_on']],
    'vcr': [['vhs']],
    'tape_hiss': [['vhs', 'rewind'], ['static_analog']],
    'studio_laugh': [['crowds', 'laughter']],
    'applause': [['laughter', 'applause']],
    'lamp_flicker': [['static_analog', 'buzz'], ['radio', 'scramble']],
    'lamp_out': [['metal_click'], ['ui_buttons_confirm']],
    'flashlight_hum': [['tinnitus', 'dirty']],
    'heart_monitor': [['heart_monitor']],
    'monitor_flatline': [['heart_monitor']],
    'mom_scream': [['scream', 'female']],
    'snort': [['laugh', 'child', 'boy'], ['child', 'boy', 'laughing']],
    'owen_giggle': [['child', 'boy']],
    'owen_cry': [['child', 'boy'], ['breath', 'calm']],
    'winks_laugh': [['laugh', 'male']],
    'goodnight_hit': [['bass_drop'], ['braam', 'washed']],
    'old_clock': [['clocks', 'tick']],
    'hospital_tone': [['room_tone']],
    'museum_tone': [['room_tone']],
    'keys_jangle': [['keys_jingle'], ['keys', 'jingle']],
    # ---- the Bunnyman film (sfx.py BUNNY_NAMES): the bunny set first (W/samples/epidemic), the earlier sets as layers.
    # Files the review rejected (_work/mix/sfx_review.md: the toddler boy crying, the metal-staircase body falls, the
    # horse-racing crowd with its PA music, the metal valve door) are mapped to no bunny name.
    'ambience_woods': [['tawny_owl'], ['ambience', 'suburban', 'night', 'crickets'], ['ambience', 'rural', 'night'],
                       ['forest', 'night', 'crickets']],
    'owl_hoot': [['tawny_owl']],
    'crowd_parade': [['crowds', 'norwegian_constitution_day'], ['crowds', 'cheltenham', 'parade_ring'],
                     ['crowds', 'children', 'cheering'], ['laughter', 'applause']],
    'hospital_corridor': [['hospital', 'corridor']],
    'hospital_room': [['hospital', 'corridor', 'walla_doors'], ['room_tone']],
    'burn_barrel': [['fire', 'crackle'], ['fire', 'burst']],
    'plastic_melt': [['fire', 'sizzling'], ['fire', 'burst'], ['fire', 'crackle', 'embers']],
    'egg_tap': [['knock', 'knuckles'], ['plastic_box', 'small', 'open']],
    'egg_set': [['egg', 'take_out'], ['plastic_box', 'small'], ['plastic', 'food_box']],
    'egg_rattle': [['plastic_lunch_box'], ['plastic', 'food_box'], ['ring', 'drop']],
    'egg_open': [['plastic_box', 'small', 'open'], ['plastic_lunch_box'], ['thermometer', 'plastic_case'],
                 ['plastic', 'food_box'], ['egg', 'take_out']],
    'ring_roll': [['coin', 'roll_on_glass']],
    'ring_drop': [['ring', 'drop'], ['shell', 'drop'], ['coin', 'roll_on_glass']],
    'ring_hand': [['ring', 'drop'], ['keys', 'jingle'], ['cloth', 'handle']],
    'oven_mitt': [['cloth', 'handle'], ['cloth', 'wipe'], ['couch', 'wipe']],
    'knock_family': [['knock', 'knuckles']],
    'slot_flap': [['mailbox'], ['metal_click'], ['flightcase', 'latch']],
    'attic_door': [['doors_creak', 'wooden'], ['cabinet', 'door_impact'], ['doors', 'wood', 'impact', 'light_door']],
    'bulb': [['metal_click'], ['flashlight', 'switch'], ['static_analog', 'buzz']],
    'chest_lid': [['wooden_box', 'lid'], ['briefcase', 'open'], ['doors_creak', 'wooden'], ['shoe_box', 'lid']],
    'page_flip': [['book', 'flip_page'], ['paper', 'handle']],
    'diary_lock': [['plastic_box', 'small', 'open'], ['thermometer', 'plastic_case'], ['metal_click']],
    'window_smash': [['glass', 'break']],
    'door_crash': [['doors', 'wood', 'kick'], ['cabinet', 'door_impact'], ['doors', 'wood', 'impact', 'light_door']],
    'wet_drag': [['chair', 'drag'], ['furniture', 'chair', 'drag'], ['cardboard', 'drag'], ['plastic_tub', 'drag']],
    'hatchet_step': [['axe', 'scrape'], ['wood', 'chopping'], ['hand_axe', 'hit'], ['footsteps', 'creaky'],
                     ['footsteps', 'wood', 'heavy']],
    'doorknob': [['mortise_lock'], ['deadbolt'], ['lock_entrance']],
    'paper_under_door': [['paper', 'handle'], ['paper', 'rustl']],
    'struggle': [['fight', 'grab', 'punch'], ['cabinet', 'door_impact'], ['bone_break_heavy'], ['bone_crack_bone_cracking'],
                 ['doors', 'wood', 'impact', 'light_door'], ['kick_out_03'], ['kick_open_internal'],
                 ['blade_impact_05']],
    'bone_crack': [['bone_break_heavy'], ['bone_crack_bone_cracking']],
    'key_outside': [['deadbolt'], ['mortise_lock'], ['lock_entrance'], ['keys', 'jingle']],
    'sirens_arrive': [['siren']],
    'vhs_pause': [['vhs']],
    'light_switch': [['flashlight', 'switch'], ['metal_click'], ['ui_buttons_confirm']],
    'music_box_wind': [['music_box', 'winding_up']],
    'flash_pop': [['camera']],
    'dogs_search': [['dog_barks']],
    'body_fall_stairs': [['cloth', 'impact'], ['cabinet', 'door_impact'], ['doors', 'wood', 'impact', 'light_door']],
    'fridge_paper': [['tape', 'rip'], ['paper', 'handle']],
    'curtain_close': [['cloth', 'flap'], ['cloth', 'handle']],
    'peephole': [['metal_click'], ['flightcase', 'latch']],
    # ---- the Doctor film (sfx.py DOCTOR_NAMES): the doctor set first (W/samples/epidemic, flat), the earlier sets
    # as layers. Files the review rejected (_work/mix/sfx_review.md) are vetoed in NOT or simply matched by no name.
    'landline_ring': [['bells', 'doorbell', 'classic', 'electric'], ['alarms', 'bell', 'school_bell']],
    'receiver_up': [['telephone', 'old', 'reciever', 'lift'], ['telephone', 'pick_up', 'hang_up'],
                    ['intercom_handset']],
    'receiver_down': [['telephone', 'pick_up', 'hang_up'], ['intercom_handset']],
    'rotary_dial': [['telephone', 'old', 'dial']],
    'dial_tone': [['telephone', 'dial_tone']],
    'busy_tone': [['busy_tone']],
    'line_hiss': [['walkie_talkie', 'white_noise']],
    'pen_click': [['ballpoint_pen', 'click'], ['pen', 'retractable'], ['pen', 'click', 'open']],
    'pen_scratch': [['pen_on_paper'], ['pen', 'write_on_paper']],
    'clipboard': [['crocodile_clip']],
    'typewriter': [['typewriter']],
    'medicine_cabinet': [['medicine_cabinet']],
    'kitchen_cabinet': [['cabinet_doors', 'kitchen']],
    'fridge_hum': [['fridge', 'hum'], ['refrigerator', 'low_hum']],
    'fluorescent': [['electricity', 'buzz_hum', 'buzz_hum'], ['electricity', 'buzz_hum', 'interference']],
    'match_strike': [['ignite', 'match']],
    'paper_burn': [['burning', 'paper']],
    'ticket_tear': [['cinema_ticket']],
    'paper_tear': [['paper_bag', 'tear'], ['tear_08'], ['tear_11']],
    'tape_peel': [['masking_tape', 'peel'], ['sticky_tape', 'peel'], ['sticky_tape', 'rip'], ['tape', 'rip', 'long']],
    'now_serving': [['pings', 'tings']],
    'waiting_room': [['hospital', 'waiting', 'room'], ['waiting_room', 'walla']],
    'heart_monitor_er': [['heart_monitor'], ['beeps', 'medical', 'heart']],
    'er_doors': [['automatic', 'glass', 'slide']],
    'gurney': [['gurney']],
    'wheelchair': [['wheelchair', 'int']],
    'halverson_car': [['car', 'start', 'idle', 'external']],
    'drive_rain': [['interior', 'fast_driving'], ['interior', 'car', 'driving_steady']],
    'rain_car': [['rain', 'car', 'roof'], ['rain', 'windshield']],
    'chair_creak': [['chair', 'creak'], ['wooden_creak', 'rock'], ['wood', 'friction', 'creak']],
    'sit_down': [['person_sit_down']],
    'phone_connect': [['speed_dial_tone'], ['telephone', 'device', 'grab', 'button']],
    # ---- the Bus film (sfx.py BUS_NAMES): the bus set first (W/samples/epidemic_bus/sfx), the earlier sets as
    # layers. The verdicts on every new file are in W/mix/sfx_review.md; rejected files match no name (or NOT vetoes).
    'suburb_night': [['suburban', 'night', 'crickets'], ['night', 'crickets']],
    'dog_far': [['dog_barks_distant']],
    'bus_air_brake': [['bus', 'air_brake']],
    'bus_idle': [['bus', 'engine', 'idle'], ['bus', 'standing_still_idle'], ['bus', 'slowly_stops_idle']],
    'bus_door': [['bus', 'door', 'open', 'close']],
    'pa_crackle': [['microphone', 'feedback'], ['megaphone', 'feedback'], ['spring_feedback']],
    'bus_pull_away': [['bus', 'start', 'drive_away'], ['bus', 'pass_by']],
    'bus_horn': [['horn', 'bus']],
    'bus9_drive': [['bus', 'on_board_driving'], ['bus', 'double_decker'], ['bus', 'start', 'drive_away']],
    'bus_fast_night': [['interior', 'fast_driving'], ['bus', 'pass_by', 'fast']],
    'tire_screech': [['skid'], ['tire', 'screech']],
    'metal_scrape': [['metal', 'scrape']],
    'glass_break': [['glass_break', 'car_window']],
    'dash_radio': [['static_radio'], ['radio', 'station_search']],
    'whistle': [['referee_whistle']],
    'ticket_punch': [['hole_punch'], ['hole_puncher']],
    'deadbolt': [['deadbolt'], ['mortise_lock']],
    'walkie': [['transceiver', 'walkie_talkie'], ['walkie_talkie', 'squelch_beep']],
    'power_flicker': [['fluorescent_light', 'light_switch']],
    'bare_feet': [['barefoot'], ['running_over_wood_stairs']],
    'run_asphalt': [['asphalt', 'running']],
    'cat_rumble': [['cat_wild']],
    'glove_squeak': [['latex', 'glove'], ['surgical_glove']],
    'tape_skip': [['glitch_glitch'], ['user_interface_glitch'], ['tape_play_stop']],
    'crt_on': [['crt_monitor'], ['hifi', 'old', 'turn_on']],
    'vhs': [['videotape', 'vhs']],
    'tape_ff': [['tape_hand_camera', 'fast_forward'], ['master_tape'], ['vhs_rewind']],
    'vinyl_crackle': [['vinyl', 'crackle']],
    'seatbelt': [['seat_belt']],
    'flag_rope': [['cable_clanking', 'flag'], ['rope_clanking']],
    'broom_bend': [['bendy_pole'], ['plywood', 'bend']],
    'broom_crack': [['wood_break', 'snap'], ['plywood', 'splinter']],
    'cloth_rip': [['cloth_rip']],
    'school_bell': [['school_bell']],
    'kids_chatter': [['school', 'children_talking'], ['school', 'big_crowd_of_kids']],
    'unscrew': [['flashlight', 'unscrew']],
    'ticket_slide': [['cinema_ticket']],
    'phone_911': [['telephone_digital_grab_handset'], ['speed_dial_tone'], ['digital_phone_ringing']],
}
# name -> slug words that veto a match (the bunny set's sword whooshes are blade hits, not air; the metal valve door and
# the battle-axe shield hits are clangs, not the film's impacts; the metal-staircase body falls never land in this
# wooden house; the toddler boy's crying is not a little girl)
NOT = {'whoosh': ['blade', 'sword', 'axe'], 'impact_hit': ['valve', 'shield', 'axe'], 'van_step': ['valve'],
       'box_knock': ['knuckles'], 'wood_knock': ['knuckles'], 'struggle': ['metal_plate', 'staircase'],
       'crowd_parade': ['horse', 'fight'], 'hospital_room': ['speakerphone'], 'owen_cry': ['crying_boy'],
       'snort': ['crying'], 'owen_giggle': ['crying'],
       # the Doctor film: the lighters are not a match; the bicycle bell / small buzzer are not the landline;
       # the pedal-FX hum is a guitar pedal (a musical drone, not a lamp); the multiple fast clicks are a frantic pen
       'match_strike': ['lighter'], 'landline_ring': ['bicycle', 'buzzer'], 'fluorescent': ['pedal'],
       'chair_creak': ['office_chair', 'bed_old_rock'], 'wheelchair': ['scooter'],
       # the review's rejects (W/mix/sfx_review.md): the clipped 15.5 kHz pen click, the phone-notification ting,
       # the cellphone busy tone
       'pen_click': ['pen_ballpoint_pen_click'], 'now_serving': ['notification'], 'busy_tone': ['cellphone']}
# the Bus film (W/mix/sfx_review.md): the kids' playground take ends in a scream (no library screams); the guitar
# feedback is an instrument; the Aztec death whistles are a cheesy human scream; the toy whistle is a slide whistle;
# the AI "hitech" walkie carries a robot voice; the reversing beeps are a modern truck alarm; the velcro is not cloth
NOT.update({'kids_chatter': ['scream', 'playground'], 'pa_crackle': ['guitar'], 'whistle': ['aztec', 'toy'],
            'walkie': ['voices_futzed_ai'], 'bus_pull_away': ['reverse_beeps'], 'cloth_rip': ['velcro'],
            'tape_skip': ['sega'], 'kids_chatter_': []})
# the Ice Cream film: source names (sfx_ice.py recipes draw on these through sfx._has / src); the bus film's keys
# above stay for the older recipes only. Verdicts and reasons: W/mix/sfx_review.md (audio/review_sfx.py ICE_DECISIONS)
ICE_MAP = {
    'ice_wind': [['wind', 'winter']],
    'ice_creaks': [['eerie_wood_creaks'], ['abandoned_wooden_house', 'creaks']],
    'ice_snow_walk': [['footsteps', 'snow', 'walk'], ['boots_snow_walk']],
    'ice_snow_run': [['footsteps', 'snow', 'run']],
    'ice_snow_scuff': [['snow_scuff']],
    'ice_shovel_scrape': [['manual_snow_plow', 'metal'], ['manual_snow_plow_plastic']],
    'ice_shovel_dig': [['shovel_dig_in_snow']],
    'ice_metal_scrape': [['metal_friction_scrape']],
    'ice_lorry': [['freight_truck_lorry_moving'], ['truck_passby']],
    'ice_air_horn': [['air_horn']],
    'ice_van_idle': [['van', 'idle']],
    'ice_serving_window': [['plastic_sliding_window']],
    'ice_house_window': [['windows_wood']],
    'ice_glass_break': [['glass_break']],
    'ice_ice_break': [['ice_break']],
    'ice_ice_crackle': [['ice_friction'], ['ice_movement_ice_crackle'], ['ice_cracking_push']],
    'ice_furnace': [['wall_heater_furnace'], ['hvac_boiler']],
    'ice_power_down': [['power_down']],
    'ice_light_switch': [['light_switch']],
    'ice_static': [['static_radio_station_search'], ['walkie_talkie_white_noise_hiss']],
    'ice_squelch': [['walkie_talkie_squelch_stuttering'], ['walkie_talkie_engage'], ['radio_device_turn_on']],
    'ice_bone': [['gore', 'bone']],
    'ice_hatch': [['wood_hatch'], ['metal_hatch']],
    'ice_towel': [['towel']],
    'ice_cloth': [['cloth_movement'], ['cloth_misc_scrape'], ['cloth_flap_towel'], ['fight_grab_punch_cloth']],
    'ice_cloth_rip': [['cloth_rip']],
    'ice_siren': [['siren_ambulance']],
    'ice_mug': [['cup_mug'], ['teacup'], ['tea_cup']],
    'ice_door_creak': [['doors_creak']],
    'ice_metal_click': [['mechanical_click_metal'], ['crocodile_clip'], ['seat_belt_click']],
    'ice_door_kick': [['doors_wood_kick_open_internal'], ['doors_wood_impact_light_door']],
    'ice_fridge_hum': [['refrigerator_low_hum'], ['fridge_hum']],
}
MAP.update(ICE_MAP)
# THIS film (Obsession, sfx_obsession.py OBSESSION_NAMES): the obsession set first (W/samples/epidemic_obsession, flat)
OBSESSION_MAP = {
    'ob_chalk_board': [['chalk', 'board'], ['chalk', 'blackboard']],
    'ob_chalk_stroke': [['chalk_stick', 'single_stroke']],
    'ob_stub_drop': [['eraser', 'drop_on_desk'], ['marker', 'drop_on_floor'], ['dice', 'drop_onto_table']],
    'ob_letterbox': [['letterbox', 'flap'], ['metal_mail_slot'], ['mailbox', 'spring_open_close'],
                     ['mailbox_2', 'open_close']],
    'ob_swing_chain': [['playground_swing']],
    'ob_locker': [['metal', 'keys_in_locker'], ['medicine_locker'], ['doors_metal_open_close_slam'],
                  ['doors_metal_slam_hall_distant']],
    'ob_bucket_down': [['bucket', 'set_down_on_concrete'], ['bucket', 'put_down_on_ground']],
    'ob_water': [['water', 'bucket'], ['water_pour', 'basin'], ['water_drip', 'metal_bucket']],
    'ob_scrub': [['brush', 'scrub'], ['brush_scub'], ['scrubbing_floor']],
    'ob_paint_roller': [['paint_roller'], ['roller_painting']],
    'ob_cafeteria': [['cafeteria']],
    'ob_drawer': [['drawers', 'metal']],
    'ob_fork_plate': [['cutlery', 'plate'], ['knife', 'china_plate']],
    'ob_car_idle': [['interior', 'car', 'idle']],
    'ob_indicator': [['turn_indicator'], ['turn_signal'], ['indicator', 'hazard']],
    'ob_fluorescent': [['fluorescent_light']],
    'ob_switch': [['light_switch'], ['switch_lamp'], ['pull_switch']],
    'ob_dust': [['sand_trickling'], ['swoosh_light']],
    'ob_whoosh': [['swoosh_light'], ['swoosh_wide']],
    'ob_sneaker': [['sneakers', 'squeak'], ['shoe_squeaks']],
    'ob_shoebox': [['shoe_box', 'lid'], ['cardboard_box', 'lid']],
    'ob_cloth': [['hoodie'], ['arm_into_sleeve'], ['arm_slide_into_sleeve'], ['windbreaker'], ['coat_jacket_thick']],
}
MAP.update(OBSESSION_MAP)
# the Ice Cream film's rejects (W/mix/sfx_review.md): the skip lorry's reverse tone is a modern beeper; the rural
# ambience carries cicadas (summer insects on a minus-thirty night); the 'scifi' power-down is a laser-gun sweep
NOT.update({'ice_lorry': ['reverse_tone'], 'ice_creaks': ['cicadas'], 'ice_power_down': ['scifi'],
            'ice_cloth': ['hugging']})
# every REJECT of W/mix/sfx_review.md stays out of every name, older names included
for _k in MAP:
    NOT.setdefault(_k, [])
    NOT[_k] = list(NOT[_k]) + ['sweeter_clean_version', 'deep_down_in_the_caverns', 'aztec_death_whistle',
                                'electric_screwdriver', 'jail_pa_system', 'voices_futzed_ai_hitech', 'sega_saturn',
                                'guitar_electric_od', 'velcro_tear', 'kids_walk_by_scream', 'cd_case_drop',
                                'wooden_blow_single_note', 'toy_blow_long', 'reverse_beeps',
                                # the Ice Cream film's rejects
                                'reverse_tone', 'cicadas', 'designed_synthetic_power_down', 'scifi_machine_power_down',
                                'cloth_movement_hugging']


def slugify(name):
    """'ES_Wooden Pole, Hit Wood 02 - Epidemic Sound (1)' -> 'wooden_pole_hit_wood_02' (download dressing dropped)."""
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    name = re.sub(r'^ES_', '', name)
    name = re.sub(r'\s*-\s*Epidemic Sound\s*$', '', name, flags=re.I)
    s = re.sub(r'[^0-9a-z]+', '_', name.lower()).strip('_')
    return re.sub(r'_+', '_', s)


def _is_music(fname):
    """A flat set's music file: 'ES_<Title> - <Artist>.mp3' (effects end '- Epidemic Sound')."""
    return 'epidemic sound' not in fname.lower()


def serves(slug):
    return sorted(k for k, alts in MAP.items() if any(all(w in slug for w in alt) for alt in alts)
                  and not any(w in slug for w in NOT.get(k, ())))


def _fingerprint(p):
    with open(p, 'rb') as f:
        return f'{os.path.getsize(p)}:{hashlib.md5(f.read(1 << 20)).hexdigest()}'


# Krumhansl-Kessler key profiles
_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def key_of(chroma_mean):
    best = (-2, 0, 'minor')
    for r in range(12):
        for prof, mode in ((_MAJ, 'major'), (_MIN, 'minor')):
            c = float(np.corrcoef(np.roll(prof, r), chroma_mean)[0, 1])
            if c > best[0]:
                best = (c, r, mode)
    return NOTES[best[1]], best[2], round(best[0], 3)


def sfx_entry(meter, p, set_name, slug):
    import librosa
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    m = x.mean(1)
    lufs = meter.integrated_loudness(x[:, :2] if x.shape[1] > 1 else x[:, 0]) if len(x) > sr * 0.4 else None
    on = librosa.onset.onset_detect(y=librosa.resample(m, orig_sr=sr, target_sr=22050), sr=22050, units='time')
    return {'path': p, 'set': set_name, 'slug': slug, 'serves': serves(slug), 'dur': round(len(x) / sr, 2), 'sr': sr,
            'lufs': None if lufs is None or not np.isfinite(lufs) else round(float(lufs), 1),
            'peak_db': round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 1), 'onsets': len(on)}


def music_entry(meter, p, set_name, slug):
    import librosa
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    x = x[:, :2]
    m = x.mean(1)
    y = librosa.resample(m, orig_sr=sr, target_sr=22050)
    oenv = librosa.onset.onset_strength(y=y, sr=22050)
    tempo = float(np.atleast_1d(librosa.beat.beat_track(onset_envelope=oenv, sr=22050)[0])[0])
    ac = librosa.autocorrelate(oenv - oenv.mean(), max_size=int(22050 / 512 * 2.5))
    lo = int(22050 / 512 * 0.3)
    pulse = float(ac[lo:].max() / (ac[0] + 1e-9)) if len(ac) > lo else 0.0
    chroma = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=2048)
    cm = chroma.mean(1)
    centre = NOTES[int(cm.argmax())]
    k, mode, kc = key_of(cm)
    bass = librosa.feature.chroma_cqt(y=y, sr=22050, hop_length=2048, fmin=librosa.note_to_hz('A0'), n_octaves=2)
    bass_root = NOTES[int(bass.mean(1).argmax())]
    hop = 2 * sr
    st = []
    for i in range(0, len(x) - hop, hop):                 # short-term loudness, 3 s window every 2 s
        seg = x[i:i + int(1.5 * hop)]
        v = meter.integrated_loudness(seg) if len(seg) > sr else -70
        st.append(round(float(v) if np.isfinite(v) else -70.0, 1))
    cent = librosa.feature.spectral_centroid(y=y, sr=22050, hop_length=22050 * 2)[0]
    feats = librosa.feature.mfcc(y=y, sr=22050, hop_length=2048, n_mfcc=13)
    kk = max(3, min(10, int(len(y) / 22050 / 25)))
    bounds = librosa.frames_to_time(librosa.segment.agglomerative(np.vstack([feats, chroma]), kk), sr=22050,
                                    hop_length=2048)
    bounds = sorted(set([0.0] + [round(float(b), 1) for b in bounds]))
    dur = len(x) / sr
    stv = np.array(st) if st else np.array([-70.0])
    secs = []
    for a, b in zip(bounds, bounds[1:] + [dur]):
        i0, i1 = int(a / 2), max(int(a / 2) + 1, int(b / 2))
        L = stv[i0:i1]; C = np.asarray(cent[i0:i1])
        secs.append({'t0': round(a, 1), 't1': round(b, 1),
                     'lufs_st': round(float(np.median(L)), 1) if len(L) else None,
                     'centroid': int(np.median(C)) if len(C) else None})
    live = stv[stv > -60]
    return {'path': p, 'set': set_name, 'slug': slug, 'dur': round(dur, 2),
            'lufs': round(float(meter.integrated_loudness(x)), 1), 'tempo': round(tempo, 1),
            'pulse_clarity': round(pulse, 3), 'tonal_centre': centre, 'key': k, 'mode': mode, 'key_corr': kc,
            'bass_root': bass_root,
            'loud_p10_p50_p90': [round(float(np.percentile(live, q)), 1) for q in (10, 50, 90)] if len(live) else None,
            'centroid_median': int(np.median(cent)),
            'loudness_2s': st, 'centroid_2s': [int(c) for c in cent], 'sections': [b for b in bounds if b > 0],
            'section_stats': secs}


def _reuse_table(paths):
    """(kind, set, slug) -> entry of earlier catalogues (only used when the file size is unchanged)."""
    tab = {}
    for p in paths:
        if not p or not os.path.exists(p):
            continue
        c = json.load(open(p))
        for kind in ('sfx', 'music'):
            for e in c.get(kind, []):
                tab.setdefault((kind, e.get('set'), e.get('slug')), e)
    return tab


def build(sets, out, sfx_only=False, reuse=()):
    import pyloudnorm
    meter = pyloudnorm.Meter(SR)
    old = json.load(open(out)) if sfx_only and os.path.exists(out) else None
    prev = _reuse_table(reuse)
    n_reused = 0
    cat = {'licence': "Epidemic Sound, through the channel owner's subscription. Keep the channel connected in the "
                      "Epidemic account to avoid Content ID claims. Do not redistribute, copy or commit the files.",
           'sets': {s: d for s, d in sets}, 'sfx': [], 'music': []}
    seen_slug, seen_fp = {}, {}
    for kind in ('sfx', 'music'):
        if kind == 'music' and old is not None:
            cat['music'] = old.get('music', [])
            continue
        for set_name, d in sets:
            sub = os.path.join(d, kind)
            if os.path.isdir(sub):
                files = sorted(os.listdir(sub))
            elif os.path.isdir(d) and not os.path.isdir(os.path.join(d, 'sfx')):      # a flat set (the doctor set)
                sub = d
                files = [f for f in sorted(os.listdir(d)) if (kind == 'music') == _is_music(f)]
            else:
                continue
            for f in files:
                stem, ext = os.path.splitext(f)
                if ext.lower() not in AUDIO_EXT:
                    continue
                p = os.path.join(sub, f)
                slug = slugify(stem)
                fp = _fingerprint(p)
                dup = seen_slug.get((kind, slug)) or seen_fp.get((kind, fp))
                if dup is not None:
                    if set_name != dup['set']:
                        dup.setdefault('also_in', []).append(set_name)
                    continue
                r = prev.get((kind, set_name, slug))
                if r is not None and os.path.exists(r.get('path', '')) and os.path.getsize(r['path']) == os.path.getsize(p):
                    e = dict(r, path=p, set=set_name)          # unchanged file: keep its analysis, path through W/samples
                    e.pop('also_in', None); e.pop('stray', None)
                    if kind == 'sfx':
                        e['serves'] = serves(slug)
                    n_reused += 1
                else:
                    print(f'  {kind} {set_name}: {f}', flush=True)
                    e = (sfx_entry if kind == 'sfx' else music_entry)(meter, p, set_name, slug)
                if kind == 'sfx' and set_name in ('bus', 'ice', 'obsession') and _is_music(f):
                    e['stray'] = 'a music track in the effects folder'; e['serves'] = []   # never an SFX
                cat[kind].append(e)
                seen_slug[(kind, slug)] = e; seen_fp[(kind, fp)] = e
    if n_reused:
        print(f'{n_reused} rows reused from {", ".join(os.path.basename(r) for r in reuse)} (same set, slug and size)')
    tmp = out + '.tmp'
    json.dump(cat, open(tmp, 'w'), indent=1)
    os.replace(tmp, out)
    cov = sorted({s for e in cat['sfx'] for s in e['serves']})
    print(f"{len(cat['sfx'])} sfx, {len(cat['music'])} music; serves {len(cov)} names: {', '.join(cov)}")
    print('missing:', sorted(set(MAP) - set(cov)))
    print('unmapped:', [e['slug'] for e in cat['sfx'] if not e['serves']])
    for mu in cat['music']:
        print(f"{mu['set']:8s} {mu['slug'][:40]:40s} {mu['dur']:5.0f}s {mu['lufs']:6.1f} LUFS key {mu.get('key')} "
              f"{mu.get('mode')} ({mu.get('key_corr')}) bass {mu.get('bass_root')} centroid {mu.get('centroid_median')} "
              f"pulse {mu.get('pulse_clarity')}")
    return cat


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    so = '--sfx-only' in sys.argv
    if '--obsession' in sys.argv:
        build(OBSESSION_SETS, OBSESSION_OUT, so, reuse=() if '--no-reuse' in sys.argv else (
            OBSESSION_OUT, ICE_OUT, BUS_OUT, DOCTOR_OUT))
    elif '--ice' in sys.argv:
        build(ICE_SETS, ICE_OUT, so, reuse=() if '--no-reuse' in sys.argv else (ICE_OUT, BUS_OUT, DOCTOR_OUT))
    elif '--bus' in sys.argv:
        build(BUS_SETS, BUS_OUT, so, reuse=() if '--no-reuse' in sys.argv else (
            BUS_OUT, DOCTOR_OUT, os.path.join(HERE, 'catalog_epidemic_bunny.json'), DUMMY_OUT, DELIVERY_OUT))
    elif '--doctor' in sys.argv:
        build(DOCTOR_SETS, DOCTOR_OUT, so, reuse=() if '--no-reuse' in sys.argv else (
            DOCTOR_OUT, os.path.join(HERE, 'catalog_epidemic_bunny.json'), DUMMY_OUT, DELIVERY_OUT))
    elif '--bunny' in sys.argv:
        build(BUNNY_SETS, BUNNY_OUT, so, reuse=() if '--no-reuse' in sys.argv else (BUNNY_OUT, BUNNY_FIRST, DUMMY_OUT,
                                                                                     DELIVERY_OUT))
    elif '--dummy' in sys.argv:
        build(DUMMY_SETS, DUMMY_OUT, so, reuse=() if '--no-reuse' in sys.argv else (DUMMY_OUT, DELIVERY_OUT))
    elif '--delivery' in sys.argv:
        build(DELIVERY_SETS, DELIVERY_OUT, so)
    elif args and '=' in args[-1]:
        build([tuple(a.split('=', 1)) for a in args[1:]], args[0], so)
    else:
        build([('police', args[0])], args[1], so)
