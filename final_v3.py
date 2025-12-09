from opentrons import protocol_api
from opentrons import simulate 

# for simulation run
protocol = simulate.get_protocol_api('2.19')
metadata = {
    'protocolName': 'Dual inducer assay',
    'author': 'OT4',
    'apiLevel': '2.14'
}
CONFIG = {
    "labware": {
        "tips_300": "opentrons_96_tiprack_300ul",
        "plate": "nest_96_wellplate_200ul_flat",
        "reservoir": "nest_12_reservoir_15ml"
    },
    "pipettes": {
        "multi_loc": "left",
        "single_loc": "right",
        "multi_model": "p300_multi_gen2",
        "single_model": "p300_single_gen2"
    },
    "flow_rates": {
        "p300m_asp": 50,
        "p300m_disp": 150,
        "p300m_blow":  150, 
        "p300s_asp": 50, 
        "p300s_disp": 100,
        "p300s_blow": 150
    },
    "volumes": {
        "asp_vol": 300,
        "disp_vol": 300,
        "mix_vol": 300
    },
    "replicates": 1
    
}
replicates = 1
LABWARE = [
    "opentrons_96_tiprack_300ul",
    "4ti0136_96_wellplate_2200ul",
    "costar3370flatbottomtransparent_96_wellplate_200ul",
]
FLOW_RATES = {
    "p300m_asp": 50,
    "p300m_disp": 150,
    "p300m_blow":  150, 
    "p300s_asp": 50, 
    "p300s_disp": 100,
    "p300s_blow": 150
}
FLOW_VOL = {
    "asp_vol": 300,
    "disp_vol": 300,
    "mix_vol": 300

}

# labware layout scenarios for 0, 1, and 2 replicates.
## 2 replicates + original run -- this script takes 1 replicate as input, giving only 1x destination plate then.
# 1x source plate, 1x reservoir plate, up to 3x destination plates -- the number of destination plate can be edit by users.
# 2x tip boxes would there be enough for 1x destination plate senario -- each destination plate setup takes around 1.5x tip boxes
#
# 1 boxes of tips per run therefore: 
# 1: 2 boxes of tips
# 2: 3 boxes
# 3: 5 boxes

labware_layout = {
    1: {"pipette_tips": []},
    2: [],
    3: []
}


# handle mixing argument for helper function
# handle multiple replicates and adjust plate count and position > map replicate count to labware definitions?
# load config data
"""
issues: air bubbles in dye? maybe manual error (pbs)
some dye remains in the tip after mixing > change blow out rate? (inducer a)
picking up single tips > which tip do i choose
flow rate for inducer pick up
for viscous liquids, change flow rates for dispense and aspiration to prevent liquid sticking within the tip 
make sure when aspirating pbs and the dye to the plate ensure that it scales with the number of replicates rather than aspirating 70 blindly > viscosity factor/checkbox
set blow out height higher? 

"""


# helper function for liquid moving 
def move_liquid(pipette: protocol_api.InstrumentContext, aspiration_vol: int, dispense_vol: int, in_location: protocol_api.labware.Well, out_location: protocol_api.labware.Well, rate:float = 1.0, mix_vol:int = 300, mix_reps:int = 0):
    pipette.aspirate(aspiration_vol, in_location, rate=rate)
    pipette.dispense(dispense_vol, out_location, rate=rate)
    if mix_reps > 0:
            # This prevents trying to mix 300ul when you only transferred 30ul.
            volume_to_mix = mix_vol if mix_vol else dispense_vol
            pipette.mix(mix_reps, volume_to_mix, out_location)
    pipette.blow_out(out_location.top())

def run(protocol: protocol_api.ProtocolContext):
    # labware definitions
    # please add more tip boxes if more replicated are designed
    p300_tip_1 = protocol.load_labware(LABWARE[0], 1)
    p300_tip_2 = protocol.load_labware(LABWARE[0], 4)
    p300_tip_3 = protocol.load_labware(LABWARE[0], 7)
    p300_multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[p300_tip_1, p300_tip_2])
    p300_single = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[p300_tip_2])
    # load map labware replicate scenarios
    source = protocol.load_labware(LABWARE[1], 6)
    reservoir = protocol.load_labware(LABWARE[1], 5)
    dest_1 = protocol.load_labware(LABWARE[2], 8)
    # please add corresponding destination plates here if more than 1 replicate is designed
    # dest_2 = protocol.load_labware(LABWARE[2], 9)

    dest_list = [dest_1][:replicates]
    

    # define flow rates
    p300_multi.flow_rate.aspirate = FLOW_RATES["p300m_asp"]
    p300_multi.flow_rate.dispense = FLOW_RATES["p300m_disp"]
    p300_multi.flow_rate.blow_out = FLOW_RATES["p300m_blow"]
    p300_single.flow_rate.aspirate = FLOW_RATES["p300s_asp"]
    p300_single.flow_rate.dispense = FLOW_RATES["p300s_disp"]
    p300_single.flow_rate.blow_out = FLOW_RATES["p300s_blow"]

    # sources in the reservoir 
    PBS_source = reservoir.wells_by_name()['A6']   # col 1 in reservoir 
    PBS_source_array = [reservoir.columns()[6], reservoir.columns()[7]] # col 5 and 6 in resrvoir 
    A_source = reservoir.wells_by_name()['A2']      # col 2
    B_source = reservoir.wells_by_name()['A3']      # col 3
    cell_source = reservoir.wells_by_name()['A4']  # col 4

    # source plate setup
    # 1. distribute PBS (diluent) to source plate col 1-8 (for inducer A serial dilution) and 10-11 (for inducer B serial dilution)
    p300_multi.pick_up_tip()
    pbs_well_volume: int = 0
    current_well_column: int = 4
    for col in list(range(0, 8)) + list(range(9, 11)):
        dest = source.columns()[col]
        if pbs_well_volume > 1200:
            pbs_well_volume: int = 0 
            current_well_column += 1
        #pipette, aspiration_vol, dispense_vol, in_location, out_location
        move_liquid(p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[current_well_column][0], dest[0])
        pbs_well_volume += FLOW_VOL["disp_vol"]
        protocol.comment(f'Moving Inducer A from {reservoir.columns()[current_well_column][0]} to {dest[0]}')

    p300_multi.drop_tip()
    protocol.comment('PBS destination plate distribution complete')

    # 2. inducer A serial dilution
    p300_multi.pick_up_tip()
    move_liquid(p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[1][0], source.columns()[7][0], rate=0.6,mix_reps=3)
    for col in range(7, 0, -1):
        source1 = source.columns()[col][0]
        dest = source.columns()[col-1][0]
        move_liquid(p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], source1, dest, rate=0.4,mix_reps=3)
        protocol.comment(f'Moving Inducer A from {source1} to {dest}')
    # discard from col 1
    p300_multi.aspirate(FLOW_VOL["asp_vol"], source.columns()[0][0]) 
    protocol.comment('Inducer A serial dilution complete')
 

    # 3. inducer B serial dilution
    target_columns = source.columns()[-replicates:]
    protocol.comment(f'Starting Inducer B dilution on last {replicates} columns.')

    for col in target_columns:
        p300_single.pick_up_tip()
        
        top_well_H = col[7] 
        bottom_well_A = col[0]

        move_liquid(p300_single, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[2][0], top_well_H, mix_reps=3)
        
        for row_index in range(7, 0, -1):
            source_well = col[row_index]
            dest_well = col[row_index - 1]
                        
            move_liquid(p300_single, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], source_well, dest_well, mix_vol=300, mix_reps=3)

        p300_single.aspirate(FLOW_VOL["asp_vol"], bottom_well_A)
        p300_single.drop_tip()
        
    protocol.comment('Inducer B serial dilution complete')

    # destination plate setup
    # pre check -- ensure the replicates do not exceed 3
    if replicates > 3:
        raise ValueError("replicates > 3. Maximum of 3 replicates and minimum of 1 replicate can be executed in each run. PLEASE ENTER AGAIN.")

    pbs_targets = []
    inducer_a_targets = []
    inducer_b_targets = []
    
    for dest_plate in dest_list:
        cols = dest_plate.columns()
        pbs_targets.append(cols[0])           # Col 1
        inducer_a_targets.extend([cols[1], cols[3]]) # Col 2 & 4
        inducer_b_targets.extend([cols[2], cols[3]]) # Col 3 & 4
    
    p300_multi.distribute(30, PBS_source, pbs_targets, disposal_volume=10, new_tip='once')
    protocol.comment(f"PBS added to Column 1 of {len(dest_list)} plates.")
    
    p300_multi.distribute(30, A_source, inducer_a_targets, disposal_volume=10, new_tip='once')
    protocol.comment("Inducer A added to Columns 2 & 4.")
    
    p300_multi.distribute(30, B_source, inducer_b_targets, disposal_volume=10, new_tip='once')
    protocol.comment("Inducer B added to Columns 3 & 4.")
    
    protocol.comment(f'''Inducer B added to plate (only-B col 3, positive col 4)''')

    # destination plate setup -- repeat for the number of replicates (default as 3)
    for plate_idx, dest in enumerate(dest_list, start=1):
        dest_col_PBS = dest.wells_by_name()['A1']
        dest_col_A_only = dest.wells_by_name()['A2']
        dest_col_positive = dest.wells_by_name()['A4']
        dest_col_B_only = dest.wells_by_name()['A3']

        # 4. add prepared A to each designed col, from source 8-1 to dest 12-5 (highest to lowest concentration)
        p300_multi.well_bottom_clearance.aspirate = 0.1
        p300_multi.pick_up_tip()
        for offset in range(8):            
            source_col_index = 7 - offset   # 7-0 = col 8-1
            dest_col_index = 11 - offset    # 11-4 = col 12-5

            A_source_well = source.columns()[source_col_index][0]
            dest_A_well = dest.columns()[dest_col_index][0]
            
            p300_multi.aspirate(30, A_source_well)
            p300_multi.dispense(30, dest_A_well)
            p300_multi.blow_out(dest_A_well.bottom())

        p300_multi.drop_tip()
        protocol.comment(f'''Prepared A gradient added to plate {plate_idx} (dest cols 5–12)''')
     
        # 5. add prepared B to each designed col, from source col 10 to dest 12-5, different replicate use different B source from source col 10-12
        # plate 1 -> source col 10, 2 -> col 11, 3 -> col 12
        B_source_col_idx = 11 + (plate_idx - 1)  # 9,10,11
        B_source_well = source.columns()[B_source_col_idx][0]

        p300_multi.pick_up_tip()
        for offset in range(2):            
            dest_col_idx = 5 - offset
            dest_B_well = dest.columns()[dest_col_idx][0]

            p300_multi.aspirate(30, B_source_well.bottom())
            p300_multi.dispense(30, dest_B_well.top()) 
            p300_multi.blow_out(dest_B_well.top())
        p300_multi.well_bottom_clearance.aspirate = 1
        p300_multi.drop_tip()
        protocol.comment(
            f'''Prepared B from source col {B_source_col_idx + 1} '''
            f'''added on top to plate {plate_idx} (dest cols 5–12)'''
        )


        # 6. Add cells (water mimic) to make a 100 ul system for each well
        cell_dict_1 = {
            dest_col_PBS: 70,
            dest_col_A_only: 70,
            dest_col_B_only: 70,
        }

        cell_dict_2 = {
            dest_col_positive: 40,
        }

        # add 80 ul water to destination plate col 5–12 (col index 4–11)
        for i in range(4, 12):
            cell_well = dest.columns()[i][0]
            cell_dict_2[cell_well] = 40

        for dest_well, vol in cell_dict_1.items():
            p300_multi.pick_up_tip()                     
            p300_multi.aspirate(70, cell_source)         
            p300_multi.dispense(vol, dest_well)       
            p300_multi.mix(3, 50, dest_well)             
            p300_multi.blow_out(dest_well.top())         
            p300_multi.drop_tip()        

        for dest_well, vol in cell_dict_2.items():
            p300_multi.pick_up_tip()                     
            p300_multi.aspirate(40, cell_source)         
            p300_multi.dispense(vol, dest_well)       
            p300_multi.mix(3, 50, dest_well)             
            p300_multi.blow_out(dest_well.top())         
            p300_multi.drop_tip()    

        protocol.comment(f"Cells (water mimic) added to plate {plate_idx} cols 1–12")

    for cmd in protocol.commands():
        print(cmd)
