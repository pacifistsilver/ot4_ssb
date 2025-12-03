from opentrons import protocol_api
from opentrons import simulate

metadata = {
    'apiLevel': '2.19',
    'protocolName': 'Team4_S5_coursework_2025',
    'description': 'two_inducers_response',
}

# user configs
replicates = 3 

# for simulation only
protocol = simulate.get_protocol_api('2.19')


def run(protocol: protocol_api.ProtocolContext):

    # labware for simulation
    reservoir = protocol.load_labware('corning_96_wellplate_360ul_flat', 4)
    source = protocol.load_labware('corning_96_wellplate_360ul_flat', 5)

    dest_1 = protocol.load_labware('corning_96_wellplate_360ul_flat', 7)
    dest_2 = protocol.load_labware('corning_96_wellplate_360ul_flat', 8)
    #dest_3 = protocol.load_labware('corning_96_wellplate_360ul_flat', 9)

    # labware 
    #reservoir = protocol.load_labware('4ti0131_12_reservoir_21000ul', 4)
    #source = protocol.load_labware('costar3370flatbottomtransparent_96_wellplate_200ul', 5)

    #dest_1 = protocol.load_labware('costar3370flatbottomtransparent_96_wellplate_200ul', 7)
    #dest_2 = protocol.load_labware('costar3370flatbottomtransparent_96_wellplate_200ul', 8)
    #dest_3 = protocol.load_labware('costar3370flatbottomtransparent_96_wellplate_200ul', 9)

    #remember to add a correct number of destination plates
    dest_list = [dest_1, dest_2][:replicates]

    p300_tip_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    p300_tip_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 10)
    #p300_tip_3 = protocol.load_labware('opentrons_96_tiprack_300ul', 11)

    p20_tip_1 = protocol.load_labware('opentrons_96_tiprack_20ul', 1)
    p20_tip_2 = protocol.load_labware('opentrons_96_tiprack_20ul', 2)

    # pipettes setting
    # remember to add enough tips
    p300_multi = protocol.load_instrument('p300_multi_gen2', mount='left', tip_racks=[p300_tip_1, p300_tip_2])
    p20_multi = protocol.load_instrument('p20_multi_gen2', mount='right', tip_racks=[p20_tip_1, p20_tip_2])

    # flow rates
    p300_multi.flow_rate.aspirate = 50
    p300_multi.flow_rate.dispense = 150
    p300_multi.flow_rate.blow_out = 300

    p20_multi.flow_rate.aspirate = 50
    p20_multi.flow_rate.dispense = 150
    p20_multi.flow_rate.blow_out = 300

    # sources in the reservoir 
    PBS_source = reservoir.wells_by_name()['A1']   # col 1
    stock_A = reservoir.wells_by_name()['A2']      # col 2
    stock_B = reservoir.wells_by_name()['A3']      # col 3
    cell_source = reservoir.wells_by_name()['A4']  # col 4

    # pre check -- ensure the replicates do not exceed 3
    if replicates > 3:
        raise ValueError("replicates > 3. Maximum of 3 replicates and minimum of 1 replicate can be executed in each run. PLEASE ENTER AGAIN.")

    # destination plate setup -- repeat for the number of replicates (default as 3)
    for plate_idx, dest in enumerate(dest_list, start=1):

        # 1. add 10 ul PBS to destination plate col 1
        p20_multi.pick_up_tip()
        dest_col_PBS = dest.wells_by_name()['A1']
        p20_multi.aspirate(12, PBS_source) # aspirate a bit more to ensure an accurate amount when dispensing 
        p20_multi.dispense(10, dest_col_PBS)
        p20_multi.drop_tip()
        protocol.comment(f'''PBS added to plate {plate_idx}, column 1''')

        # 2. add 10 ul stock A to destination plate col 2 (only-A) and col 4 (positive control)
        p20_multi.pick_up_tip()
        dest_col_A_only = dest.wells_by_name()['A2']
        dest_col_positive = dest.wells_by_name()['A4']

        p20_multi.aspirate(12, stock_A)
        p20_multi.dispense(10, dest_col_A_only)

        p20_multi.aspirate(12, stock_A)
        p20_multi.dispense(10, dest_col_positive)

        p20_multi.drop_tip()
        protocol.comment(f'''Inducer A added to plate {plate_idx} (only-A col 2, positive col 4)''')

        # 3. add 10 ul stock B to destination plate col 3 (only-B) and col 4 (positive control)
        p20_multi.pick_up_tip()
        dest_col_B_only = dest.wells_by_name()['A3']

        p20_multi.aspirate(12, stock_B)
        p20_multi.dispense(10, dest_col_B_only)

        p20_multi.aspirate(12, stock_B)
        p20_multi.dispense(10, dest_col_positive)

        p20_multi.drop_tip()
        protocol.comment(f'''Inducer B added to plate {plate_idx} (only-B col 3, positive col 4)''')

        # 4. add 10 ul prepared A to each designed col, from source 8-1 to dest 12-5 (highest to lowest concentration)
        p20_multi.pick_up_tip()
        for offset in range(8):            
            source_col_index = 7 - offset   # 7-0 = col 8-1
            dest_col_index = 11 - offset    # 11-4 = col 12-5

            A_source_well = source.columns()[source_col_index][0]
            dest_A_well = dest.columns()[dest_col_index][0]

            p20_multi.aspirate(10, A_source_well)
            p20_multi.dispense(10, dest_A_well)
            p20_multi.blow_out(dest_A_well.bottom())

        p20_multi.drop_tip()
        protocol.comment(f'''Prepared A gradient added to plate {plate_idx} (dest cols 5–12)''')

        # 5. add 10 ul prepared B to each designed col, from source col 10 to dest 12-5, different replicate use different B source from source col 10-12
        # plate 1 -> source col 10, 2 -> col 11, 3 -> col 12
        B_source_col_idx = 9 + (plate_idx - 1)  # 9,10,11
        B_source_well = source.columns()[B_source_col_idx][0]

        p20_multi.pick_up_tip()
        for offset in range(8):            
            dest_col_idx = 11 - offset
            dest_B_well = dest.columns()[dest_col_idx][0]

            p20_multi.aspirate(10, B_source_well)
            p20_multi.dispense(10, dest_B_well.top()) 
            p20_multi.blow_out(dest_B_well.top())

        p20_multi.drop_tip()
        protocol.comment(
            f'''Prepared B from source col {B_source_col_idx + 1} '''
            f'''added on top to plate {plate_idx} (dest cols 5–12)'''
        )
        
        
        # 6. Add cells (water mimic) to make a 100 ul system for each well
        cell_dict = {
            dest_col_PBS: 90,
            dest_col_A_only: 90,
            dest_col_B_only: 90,
            dest_col_positive: 80,
        }

        # add 80 ul water to destination plate col 5–12 (col index 4–11)
        for i in range(4, 12):
            cell_well = dest.columns()[i][0]
            cell_dict[cell_well] = 80

        for dest_well, vol in cell_dict.items():
            p300_multi.pick_up_tip()                     
            p300_multi.aspirate(100, cell_source)         
            p300_multi.dispense(vol, dest_well)       
            p300_multi.mix(3, 50, dest_well)             
            p300_multi.blow_out(dest_well.top())         
            p300_multi.drop_tip()                         
        protocol.comment(f"Cells (water mimic) added to plate {plate_idx} cols 1–12")

    for cmd in protocol.commands():
        print(cmd)


# for simulation only
run(protocol)
