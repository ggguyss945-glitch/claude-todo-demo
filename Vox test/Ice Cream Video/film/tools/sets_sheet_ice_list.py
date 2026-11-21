# The ice cream film's variants for tools/sets_sheet_ice.py (exec'd there: ST, G, II, math in scope).
# (name, builder, t, note)
ICE = [
    ('ext_house', G(lambda: ST.ic_street('house', win=dict(liv=0.9, kitchen=0.5))), 0.5, 'our house from across the lane, the truck at A'),
    ('ext_kessler', G(lambda: ST.ic_street('kessler')), 0.5, "Kessler's house from our yard: his dark window, no chimney smoke"),
    ('ext_lane', G(lambda: ST.ic_street('lane', win=dict(liv=0.9))), 0.5, 'down Birch Lane from the west'),
    ('ext_truck', G(lambda: ST.ic_street('truck')), 0.5, 'the truck at A from our walk'),
    ('ext_window_close', G(lambda: ST.ic_street('window_close', truck_open=1.0)), 0.5, 'the serving window close'),
]
STAGE_ICE = []
