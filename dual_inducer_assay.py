from opentrons import protocol_api
from opentrons import simulate 
import json
# for simulation run
protocol = simulate.get_protocol_api('2.19')
metadata = {
    'protocolName': 'Dual Inducer Assay',
    'author': 'Agnes Cheung, Daniel Luo, Lihao Tao (Opentron Team 4)',
    'description': 'Opentrons 2025 Hackathon Team 4 Submission. Dual Inducer Assay Protocol with attached GUI for config generation',
    'apiLevel': '2.14'
}

with open('dilution_config.json', 'r') as f:
    config = json.load(f)
    
def validate_parameters(replicates, viscous_check):
    if replicates not in [1, 2, 3]:
        raise ValueError(f"Replicates must be 1, 2, or 3. Got: {replicates}")
    
    if not isinstance(viscous_check, bool):
        raise ValueError(f"Warning: 'viscous_check' expected bool, got {type(viscous_check)}")

REPLICATES = config.get("replicates") 
VISCOUS = config.get("viscous_check")
ASP_RATE = config.get("asp_rate")
DISP_RATE = config.get("disp_rate")
BLOW_RATE = config.get("blowout_rate")
LABWARE = {
    'tips': 'opentrons_96_tiprack_300ul', 
    'reservoir': 'corning_96_wellplate_360ul_flat', 
    'plate': 'corning_96_wellplate_360ul_flat' 
}

FLOW_RATES = {
    "p300m_asp":  ASP_RATE,
    "p300m_disp": DISP_RATE,
    "p300m_blow": BLOW_RATE,
    "p300s_asp":  ASP_RATE,
    "p300s_disp": DISP_RATE,
    "p300s_blow": BLOW_RATE
}

FLOW_VOL = {
    "asp_vol": 300,
    "disp_vol": 300,
    "mix_vol": 300,
    "pbs_max_well": 1200,
    'cell_transfer_high': 70,
    'cell_transfer_low': 40,
}
RATES = {
    'default': 1.0,
    'slow': 0.5,
}
PLATE_LAYOUT = {
    1: {
        'plate_slots': [8],
        'tip_slots':   [4, 7]
    },
    2: {
        'plate_slots': [8, 9],
        'tip_slots':   [2, 4, 7, 10]
    },
    3: {
        'plate_slots': [8, 9, 11],
        'tip_slots':   [1, 2, 4, 7, 10]
    }
}

validate_parameters(REPLICATES, VISCOUS)
current_config = PLATE_LAYOUT[REPLICATES]

# helper function for liquid moving 
def move_liquid(pipette: protocol_api.InstrumentContext, aspiration_vol: int, dispense_vol: int, in_location: protocol_api.labware.Well, out_location: protocol_api.labware.Well, rate:float = 1.0, mix_vol:int = 300, mix_reps:int = 0):
    """
    Helper function for aspirate/dispense with optional mixing and rate control.
    """
    pipette.aspirate(aspiration_vol, in_location, rate=rate)
    pipette.dispense(dispense_vol, out_location, rate=rate)
    if mix_reps > 0:
            # This prevents trying to mix 300ul when you only transferred 30ul.
            volume_to_mix = mix_vol if mix_vol else dispense_vol
            pipette.mix(mix_reps, volume_to_mix, out_location)
    pipette.blow_out(out_location.top())

def distribute_pbs(pipette: protocol_api.InstrumentContext, reservoir: protocol_api.labware.Labware, source_plate: protocol_api.labware.Labware, protocol: protocol_api.ProtocolContext, rate:float = 1.0):
    """Distributes PBS (Diluent) to the Source Plate."""
    target_cols_indices = list(range(0, 8)) + list(range(9, 11))
    
    # Logic to switch source well if volume runs low
    res_cols = [4, 5, 6, 7] # Reservoir columns available for PBS
    current_res_idx = 0
    current_vol_tracker = 0
    pipette.pick_up_tip()

    for col_idx in target_cols_indices:
        dest = source_plate.columns()[col_idx][0]
        source_well = reservoir.columns()[res_cols[current_res_idx]][0]
        
        # Switch reservoir well if we exceed limit
        if current_vol_tracker > FLOW_VOL['pbs_max_well']:
            current_res_idx += 1
            current_vol_tracker = 0
            source_well = reservoir.columns()[res_cols[current_res_idx]][0]
        move_liquid(pipette, FLOW_VOL['asp_vol'], FLOW_VOL['disp_vol'],source_well, dest, rate=rate)
        current_vol_tracker += FLOW_VOL['disp_vol']
        
    pipette.drop_tip()
    protocol.comment('INFO: PBS distribution complete')

def perform_serial_dilution(pipette: protocol_api.InstrumentContext, wells: list[protocol_api.labware.Well], rate:float = 1.0, mix_reps: int = 3, mix_vol: int = 0):
    """
    Performs serial dilution across a list of opentron Well objects.
    Moves from wells[0] -> wells[1], then wells[1] -> wells[2], etc...
    """
    # Iterate through the list of wells in pairs
    for i in range(len(wells) - 1):
        source = wells[i]
        dest = wells[i+1]
        
        move_liquid(pipette, FLOW_VOL['asp_vol'], FLOW_VOL['disp_vol'], source, dest, rate=rate, mix_reps=mix_reps, mix_vol=mix_vol)

def run(protocol: protocol_api.ProtocolContext):
    ### A. Setup Dilutions
    ## 1. Define Labware Setup
    # Define tip box position and destination plate position 
    dest_plates = [protocol.load_labware(LABWARE['plate'], slot) for slot in current_config['plate_slots']]
    tips_300 = [protocol.load_labware(LABWARE['tips'], slot) for slot in current_config['tip_slots']]
    # Define pipette selection
    p300_multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=tips_300)
    p300_single = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=tips_300)    
    
    # Define reservoir (PBS, Cells, Dyes) and source (cocentration gradient)    
    reservoir = protocol.load_labware(LABWARE['reservoir'], 5)
    source_plate = protocol.load_labware(LABWARE['reservoir'], 6) 

    protocol.comment("INFO: Labware Definitions Defined.")
    # Dye A source
    res_A_source = reservoir.wells_by_name()['A2']
    # Dye B source
    res_B_source = reservoir.wells_by_name()['A3']
    # Cell source
    res_cell_source = reservoir.wells_by_name()['A4']
    
    # Define flow rates
    if VISCOUS == True: 
        rate_multiplier = RATES['slow']
        protocol.comment(f"INFO: Viscosity setting set to True. Rate multiplier set to {rate_multiplier}")
    else: 
        rate_multiplier = RATES['default']
        protocol.comment(f"INFO: Viscosity setting set to False. Rate multiplier set to {rate_multiplier}")
    p300_multi.flow_rate.aspirate = FLOW_RATES["p300m_asp"]
    p300_multi.flow_rate.dispense = FLOW_RATES["p300m_disp"]
    p300_multi.flow_rate.blow_out = FLOW_RATES["p300m_blow"]
    p300_single.flow_rate.aspirate = FLOW_RATES["p300s_asp"]
    p300_single.flow_rate.dispense = FLOW_RATES["p300s_disp"]
    p300_single.flow_rate.blow_out = FLOW_RATES["p300s_blow"]
    protocol.comment("INFO: Flow rates defined.")

    ## 2. Add PBS to source plate to begin serial dilution
    distribute_pbs(p300_multi, reservoir, source_plate, protocol)
    ## 3. Add Inducer A and start dilution.
    protocol.comment("INFO: Starting Inducer A dilution.")
    p300_multi.pick_up_tip()
    move_liquid(p300_multi, FLOW_VOL['asp_vol'], FLOW_VOL['disp_vol'], reservoir.columns()[1][0], source_plate.columns()[7][0], rate=rate_multiplier, mix_reps=3)
    # Dilute backwards from Col 8 down to 1
    # We grab the top well of each column for the multi-channel
    dilution_path_A = [source_plate.columns()[i][0] for i in range(7, -1, -1)]
    perform_serial_dilution(p300_multi, dilution_path_A, mix_reps=3, rate=rate_multiplier)
    protocol.comment("INFO: Inducer A dilution completed.")
    # Discard last volume
    p300_multi.aspirate(FLOW_VOL['asp_vol'], source_plate.columns()[0][0])
    p300_multi.drop_tip()
    
    ## 4. Inducer B Serial Dilution (Single-channel)
    protocol.comment(f"INFO: Starting Inducer B Dilution on last {REPLICATES} columns.")
    target_columns = source_plate.columns()[-REPLICATES:]
    
    for col in target_columns:
        p300_single.pick_up_tip()
        # Initial transfer Reservoir -> Top of column (Row H / index 7)
        move_liquid(p300_single, FLOW_VOL["asp_vol"], FLOW_VOL["disp_vol"], reservoir.columns()[2][0], col[7], mix_reps=3, rate=rate_multiplier)
        protocol.comment(f"INFO: Liquid moved from {reservoir.columns()[2][0]} to {col[7]}")
        # Define path: Row 7 down to Row 0 within this specific column
        dilution_path_B = [col[i] for i in range(7, -1, -1)]
        perform_serial_dilution(p300_single, dilution_path_B, mix_reps=3, mix_vol=300, rate=rate_multiplier)
        protocol.comment(f"INFO: Inducer B dilution complete for {col} in {target_columns}")
        # Discard last volume
        p300_single.aspirate(FLOW_VOL['asp_vol'], col[0])
        p300_single.drop_tip()
    protocol.comment(f"INFO: Inducer B dilution complete.")
    if REPLICATES > 3:
        raise ValueError("replicates > 3. Maximum of 3 replicates and minimum of 1 replicate can be executed in each run. PLEASE ENTER AGAIN.")
    
    ### B. Setup Final Destination Plate
    ## 1. Distribute Reagents (PBS, A, B) to Dest Plates
    # Using 'distribute' is cleaner than manual loops for simple dispensing
    for dest_plate in dest_plates:
        cols = dest_plate.columns()
        
        # Distribute PBS to Col 1
        p300_multi.distribute(30, res_A_source, cols[0], new_tip='once') 
        
        # Distribute Inducer A to Col 2 & 4
        p300_multi.distribute(30, res_A_source, [cols[1], cols[3]], new_tip='once')
        
        # Distribute Inducer B to Col 3 & 4
        p300_multi.distribute(30, res_B_source, [cols[2], cols[3]], new_tip='once')


    ## 2. Transfer Gradient A & B and Cells
    for i, dest in enumerate(dest_plates):
        protocol.comment(f"INFO: Transferring Gradient for Plate {i+1}")
        
        p300_multi.pick_up_tip()
        # Transfer Gradient A (Col 8-1 -> Col 12-5)
        for offset in range(8):
            source_well = source_plate.columns()[7 - offset][0]
            dest_well = dest.columns()[11 - offset][0]
            move_liquid(p300_multi, 30, 30, source_well, dest_well, mix_vol=10, mix_reps=1, rate=rate_multiplier)            
        p300_multi.drop_tip()
        
        # Transfer B (Specific Source Cols -> Dest Cols 12-5)
        b_source_idx = 9 + i
        b_source_well = source_plate.columns()[b_source_idx][0]
        
        # Target: Columns 12 down to 5 (Indices 11 to 4)
        targets_B = [dest.columns()[11-k][0] for k in range(8)]
        
        p300_multi.distribute(30, b_source_well, targets_B, new_tip='always') 

        # Add Cells
        # Group wells by volume
        cols = dest.columns()
        wells_70 = [cols[0][0], cols[1][0], cols[2][0]] # A1, A2, A3
        wells_40 = [cols[3][0]] + [cols[k][0] for k in range(4, 12)] # A4 + A5-A12
        
        for w in wells_70:
            p300_multi.pick_up_tip()
            move_liquid(p300_multi, 70, 70, res_cell_source, w, mix_vol=50, mix_reps=3)
            p300_multi.drop_tip()
        for w in wells_40:
            p300_multi.pick_up_tip()
            move_liquid(p300_multi, 40, 40, res_cell_source, w, mix_vol=50, mix_reps=3)
            p300_multi.drop_tip()
        protocol.comment(f"INFO: Substrate/Cells added to plate {i} cols 1–12")        
        for cmd in protocol.commands():
            print(cmd)