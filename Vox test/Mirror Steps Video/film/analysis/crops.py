"""Extract reference crops (<=640 px) to refcrops dir. Args: ref_dir out_dir"""
import subprocess, sys, numpy as np, cv2
ref, out = sys.argv[1], sys.argv[2]
F = None
C = [
 ('face_fire_peephole_calm_smirk','fire',72,(340,0,940,600)),('face_fire_peephole_shout','fire',351.5,(340,0,940,600)),
 ('face_fire_peephole_nervous','fire',414,(340,0,940,600)),('face_fire_peephole_still_stare','fire',432,(340,0,940,600)),
 ('face_fire_window_listening','fire',144,(0,0,1100,640)),('face_fire_you_redlit_sweat','fire',441,(290,0,990,640)),
 ('face_hotel_receptionist_grin_tears','hotel',58,(240,0,1040,640)),('face_hotel_receptionist_grin_mid','hotel',48,(240,0,1040,640)),
 ('face_hotel_receptionist_tracking_tags','hotel',53,F),('face_hotel_guest_crying_bubble','hotel',166,F),
 ('face_hotel_man_shout_bubble','hotel',88,F),('face_hotel_housekeeper_shock','hotel',538,F),
 ('face_class_girl_scream_tears_dof','class',194,F),('face_class_girl_trembling','class',192,F),
 ('face_class_man_scream_redtag','class',205,F),('face_class_boy_closeup_bigeye','class',456,F),('face_class_blonde_dof','class',91,F),
 ('body_fire_firefighter_points_neighbor','fire',198,(300,60,900,720)),('ui_hotel_red_cross_over_guest','hotel',9,F),
 ('body_hotel_doorway_stretcher','hotel',313,F),('body_class_tall_creature','class',559,F),('body_hotel_family_elevator','hotel',430,F),
 ('body_fire_you_back_hallway','fire',31.5,F),
 ('peephole_fire_wide_truck','fire',25,F),('peephole_fire_walk_in','fire',345.3,F),('peephole_fire_back_turn','fire',54,F),('peephole_hotel_door','hotel',283,F),
 ('set_fire_night_house_truck','fire',27,F),('set_fire_porch_light_neighbor','fire',45,F),('set_fire_house_figures_in_windows','fire',90,F),
 ('set_fire_livingroom_tv','fire',117,F),('set_fire_red_smoke_room','fire',370,F),('set_fire_redblue_door','fire',457,F),
 ('set_fire_sirens_street','fire',406,F),('set_hotel_lobby_reception','hotel',176,F),('set_hotel_red_carpet_corridor','hotel',401,F),
 ('set_class_classroom_wide','class',22,F),('set_class_hallway_lockers','class',490,F),
 ('prop_fire_notebook_checklist','fire',15.2,(300,0,980,640)),('prop_fire_smoke_detector','fire',189,F),('prop_fire_chalk_number','fire',108,F),
 ('prop_hotel_clock_dial','hotel',19,F),('prop_hotel_digital_clock','hotel',381,F),
 ('ui_fire_never_open_up','fire',9.2,F),('ui_fire_rule_card_05','fire',298.3,F),('ui_fire_floorplan_panel','fire',153,F),
 ('ui_fire_911_phone_dispatch','fire',272,F),('ui_fire_waveform_panels','fire',333,F),('ui_fire_hall_tag_no_smoke','fire',131.5,F),
 ('ui_fire_window_scene_panel','fire',152,F),('ui_hotel_phone_unknown_call','hotel',361,F),('ui_class_chat_phone','class',513,F),
 ('ui_class_seating_map','class',171,F),('ui_hotel_rule_card','hotel',234,F),('ui_fire_static_glitch','fire',62.7,F),
]
for name, v, t, box in C:
    raw = subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',f'{ref}/{v}.mp4','-frames:v','1','-pix_fmt','bgr24','-f','rawvideo','-'],capture_output=True).stdout
    im = np.frombuffer(raw, np.uint8).reshape(720,1280,3)
    if box: x0,y0,x1,y1 = box; im = im[y0:y1, x0:x1]
    h, w = im.shape[:2]; s = 640 / max(h, w)
    if s < 1: im = cv2.resize(im, (round(w*s), round(h*s)), interpolation=cv2.INTER_AREA)
    tag = f'{v}_{t:g}s'.replace('.', 'p')
    cv2.imwrite(f'{out}/{name}__{tag}.png', im)
print(len(C))
