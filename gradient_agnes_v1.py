from opentrons import protocol_api
from opentrons import simulate 
import json

protocol = simulate.get_protocol_api('2.19')

metadata = {
    'protocolName': 'General Compound Gradient with Cells',
    'author': 'Team 4',
    'apiLevel': '2.14'
}

#def run(protocol: protocol_api.ProtocolContext):
    # Load Config
with open('/Users/agnescheung/Desktop/SSB/Config.json', 'r') as f:
    cfg = json.load(f)

#Define parameters from config
total_vol = cfg['total_vol_uL']
diluent_vol = cfg['diluent_vol_uL']
stock_vol = cfg['stock_vol_uL']
final_conc = cfg['final_conc_uM']

#Define labware
#Stimulation only
plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)
source = protocol.load_labware('usascientific_12_reservoir_22ml', 4)
tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack_1])
#Actual run with customised labwares
#plate = protocol.load_labware('costar3370flatbottomtransparent_96_wellplate_200ul', 4)
#source = protocol.load_labware('4ti0136_96_wellplate_2200ul', 1)
#tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
#p300 = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[tiprack_1])
#p20 = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack_2])

#Define source wells
diluent = source.wells()[0]
stock = source.wells()[1]
cells = source.wells()[2]

#Define flow rates
p300.flow_rate.aspirate = 50
p300.flow_rate.dispense = 100
p300.flow_rate.blow_out = 150

#Step 1: Add diluent to all wells in row A without changing tips
p300.pick_up_tip()
for i in range(len(final_conc)-1):
    dest = plate.columns()[i]
    p300.aspirate(diluent_vol[i], diluent)
    p300.dispense(diluent_vol[i], dest[0])
    p300.blow_out(dest[0])
p300.drop_tip()

protocol.comment('Dilutent added')

#Step 2: Add solute to create gradient without changing tips
p300.pick_up_tip()
for i in range(1, len(final_conc)):
    dest = plate.columns()[i]
    p300.aspirate(stock_vol[i], stock)
    p300.dispense(stock_vol[i], dest[0])
    p300.mix(3, 80, dest[0])
    p300.blow_out(dest[0])
p300.drop_tip()

protocol.comment('Greadient created')

#Step 3: Add cells
for i in range(len(final_conc)):
    p300.pick_up_tip()
    dest = plate.columns()[i]
    p300.aspirate(total_vol, cells)
    p300.dispense(total_vol, dest[0])
    for mix in range(3):
        p300.aspirate(80, dest[0], rate=0.8) #Slower aspirate to prevent bubbles
        p300.dispense(80, dest[0], rate=0.8) #Slower dispense to prevent bubbles
    p300.blow_out(dest[0])
    p300.drop_tip()

protocol.comment('Cells added')
protocol.comment("Move plate to plate reader")

for line in protocol.commands(): 
    print(line)
