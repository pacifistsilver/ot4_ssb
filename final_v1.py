from opentrons import protocol_api
from opentrons import simulate 
protocol = simulate.get_protocol_api('2.19')
metadata = {
    'protocolName': 'Dual inducer assay',
    'author': 'OT4',
    'apiLevel': '2.14'
}

replicates = 2 
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

# helper function for dilution 
def move_liquid(pipette, aspiration_vol: int, dispense_vol: int, in_location, out_location, **kwargs):
    pipette.aspirate(aspiration_vol, in_location)
    pipette.dispense(dispense_vol, out_location)
    if kwargs:
        if mix_opt is True:
            pipette.mix(mix_reps, mix_vol, out_location)
    pipette.blow_out(out_location)

def run(protocol: protocol_api.ProtocolContext):
        #Define labware
    #Stimulation only
    #source = protocol.load_labware('corning_96_wellplate_360ul_flat', 6)
    #dest_1 = protocol.load_labware('corning_96_wellplate_360ul_flat', 8)
    #dest_2 = protocol.load_labware('corning_96_wellplate_360ul_flat', 9)
    p300_tip_1 = protocol.load_labware(LABWARE[0], 1)
    p300_tip_2 = protocol.load_labware(LABWARE[0], 2)
    #p300_tip_3 = protocol.load_labware('opentrons_96_tiprack_300ul', 11)
    p300_tip_3 = protocol.load_labware(LABWARE[0], 3)
    p300_tip_4 = protocol.load_labware(LABWARE[0], 4)
    #reservoir = protocol.load_labware('corning_96_wellplate_360ul_flat', 5)
    p300_multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[p300_tip_2, p300_tip_3, p300_tip_4])
    p300_single = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[p300_tip_1])
    #Actual run with customised labwares
    source = protocol.load_labware(LABWARE[1], 6)
    reservoir = protocol.load_labware(LABWARE[1], 5)
    dest_1 = protocol.load_labware(LABWARE[2], 8)
    dest_2 = protocol.load_labware(LABWARE[2], 9)
    #dest_3 = protocol.load_labware('costar3370flatbottomtransparent_96_wellplate_200ul', 7)

    dest_list = [dest_1, dest_2][:replicates]
    

    #Define flow rates
    p300_multi.flow_rate.aspirate = FLOW_RATES["p300m_asp"]
    p300_multi.flow_rate.dispense = FLOW_RATES["p300m_disp"]
    p300_multi.flow_rate.blow_out = FLOW_RATES["p300m_blow"]
    p300_single.flow_rate.aspirate = FLOW_RATES["p300s_asp"]
    p300_single.flow_rate.dispense = FLOW_RATES["p300s_disp"]
    p300_single.flow_rate.blow_out = FLOW_RATES["p300s_blow"]

    # sources in the reservoir 
    PBS_source = reservoir.wells_by_name()['A7']   # col 1
    PBS_source_array = [reservoir.columns()[6], reservoir.columns()[7], reservoir.columns()[8]]
    stock_A = reservoir.wells_by_name()['A2']      # col 2
    stock_B = reservoir.wells_by_name()['A3']      # col 3
    cell_source = reservoir.wells_by_name()['A4']  # col 4

    move_liquid_args = {
        p300_multi_nomix = [p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[current_well_column][0], dest[0]],
        p300_multi_mix = [p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[current_well_column][0], dest[0], mix_opt = True, mix_reps = 3, mix_vol = FLOW_VOL["mix_vol"]],
    }

    mix_option_args = [mix_opt=True, mix_reps = 3, mix_vol = FLOW_VOL["mix_vol"]]
    #Step 1: Distribute PBS (diluent) to col 1-8 and 10-11 of source plate
    p300_multi.pick_up_tip()
    pbs_well_volume: int = 0
    current_well_column: int = 5
    for col in list(range(0, 8)) + list(range(9, 11)):
        dest = source.columns()[col]
        if pbs_well_volume > 1200:
            pbs_well_volume: int = 0 
            current_well_column += 1
        #pipette, aspiration_vol, dispense_vol, in_location, out_location
        move_liquid(p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[current_well_column][0], dest[0])
        pbs_well_volume += FLOW_VOL["disp_vol"]

    p300_multi.drop_tip()
    protocol.comment('PBS added')

    #Step 2: Inducer A serial dilution
    p300_multi.pick_up_tip()
    move_liquid(p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[1][0], source.columns()[7][0], mix_option_args)
    for col in range(7, 0, -1):
        source1 = source.columns()[col][0]
        dest = source.columns()[col-1][0]
        move_liquid(p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[current_well_column][0], dest[0], mix_option_args)
    p300_multi.aspirate(FLOW_VOL["asp_vol"], source.columns()[0][0]) #remove 100ul from col 1
    p300_multi.drop_tip()
    protocol.comment('Inducer A serial dilution complete')
    #Step 3: Inducer B serial dilution
    for col in range(9, 11):
        p300_single.pick_up_tip()
        move_liquid(p300_multi, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[current_well_column][0], dest[0], mix_option_args)

        p300_single.aspirate(FLOW_VOL["asp_vol"], reservoir.columns()[2][0])
        p300_single.dispense(FLOW_VOL["disp_vol"], source.columns()[col][7])
        p300_single.mix(3, FLOW_VOL["mix_vol"], source.columns()[col][7])
        p300_single.blow_out(source.columns()[col][7])
        for row in range(7, 0, -1):
            source1 = source.columns()[col][row]
            dest = source.columns()[col][row-1]
            p300_single.aspirate(FLOW_VOL["asp_vol"], source1)
            p300_single.dispense(FLOW_VOL["disp_vol"], dest)
            p300_single.mix(3, FLOW_VOL["mix_vol"], dest)
        p300_single.blow_out(dest)
        p300_single.aspirate(FLOW_VOL["asp_vol"], source.columns()[col][0])
        p300_single.drop_tip()

    protocol.comment('Inducer B serial dilution complete')

    # pre check -- ensure the replicates do not exceed 3
    if replicates > 3:
        raise ValueError("replicates > 3. Maximum of 3 replicates and minimum of 1 replicate can be executed in each run. PLEASE ENTER AGAIN.")

    
    # 1. add 10 ul PBS to destination plate col 1
    p300_multi.pick_up_tip()
    dest1_col_PBS = dest_1.wells_by_name()['A1']
    dest2_col_PBS = dest_2.wells_by_name()['A1']
    p300_multi.aspirate(70, PBS_source) # aspirate a bit more to ensure an accurate amount when dispensing 
    p300_multi.dispense(30, dest1_col_PBS)
    p300_multi.dispense(30, dest2_col_PBS)
    protocol.comment(f'''PBS added to plate, column 1''')
    p300_multi.drop_tip()

    # 2. add 10 ul stock A to destination plate col 2 (only-A) and col 4 (positive control)
    p300_multi.pick_up_tip()
    dest1_col_A_only = dest_1.wells_by_name()['A2']
    dest2_col_A_only = dest_2.wells_by_name()['A2']
    dest1_col_positive = dest_1.wells_by_name()['A4']
    dest2_col_positive = dest_2.wells_by_name()['A4']

    p300_multi.aspirate(150, stock_A)
    p300_multi.dispense(30, dest1_col_A_only)
    p300_multi.dispense(30, dest2_col_A_only)
    p300_multi.dispense(30, dest1_col_positive)
    p300_multi.dispense(30, dest2_col_positive)
    p300_multi.drop_tip()

    protocol.comment(f'''Inducer A added to plate (only-A col 2, positive col 4)''')
    
    # 3. add 10 ul stock B to destination plate col 3 (only-B) and col 4 (positive control)
    p300_multi.pick_up_tip()
    dest1_col_B_only = dest_1.wells_by_name()['A3']
    dest2_col_B_only = dest_2.wells_by_name()['A3']

    p300_multi.aspirate(150, stock_B)
    p300_multi.dispense(30, dest1_col_B_only)
    p300_multi.dispense(30, dest2_col_B_only)
    p300_multi.dispense(30, dest1_col_positive)
    p300_multi.dispense(30, dest2_col_positive)
    p300_multi.drop_tip()

    protocol.comment(f'''Inducer B added to plate (only-B col 3, positive col 4)''')

    # destination plate setup -- repeat for the number of replicates (default as 3)
    for plate_idx, dest in enumerate(dest_list, start=1):
        dest_col_PBS = dest.wells_by_name()['A1']
        dest_col_A_only = dest.wells_by_name()['A2']
        dest_col_positive = dest.wells_by_name()['A4']
        dest_col_B_only = dest.wells_by_name()['A3']

        # 4. add 10 ul prepared A to each designed col, from source 8-1 to dest 12-5 (highest to lowest concentration)
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

        # 5. add 10 ul prepared B to each designed col, from source col 10 to dest 12-5, different replicate use different B source from source col 10-12
        # plate 1 -> source col 10, 2 -> col 11, 3 -> col 12
        B_source_col_idx = 9 + (plate_idx - 1)  # 9,10,11
        B_source_well = source.columns()[B_source_col_idx][0]

        p300_multi.pick_up_tip()
        for offset in range(8):            
            dest_col_idx = 11 - offset
            dest_B_well = dest.columns()[dest_col_idx][0]

            p300_multi.aspirate(30, B_source_well)
            p300_multi.dispense(30, dest_B_well.top()) 
            p300_multi.blow_out(dest_B_well.top())

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
