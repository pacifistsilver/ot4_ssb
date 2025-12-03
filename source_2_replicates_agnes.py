from opentrons import protocol_api
from opentrons import simulate 
protocol = simulate.get_protocol_api('2.19')
metadata = {
    'protocolName': 'Dual inducer assay',
    'author': 'OT4',
    'apiLevel': '2.14'
}
#Define labware
#Stimulation only
source = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)
reservior = protocol.load_labware('usascientific_12_reservoir_22ml', 4)
p300_tip = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
p300_multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[p300_tip])
p300_single = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[p300_tip])
#Actual run with customised labwares
#source = protocol.load_labware('ccostar3370flatbottomtransparent_96_wellplate_200ul', 1)
#reservior = protocol.load_labware('4ti0136_96_wellplate_2200ul', 4)
#p300_tip = protocol.load_labware('opentrons_96_tiprack_300ul', 2)
#p300_multi = protocol.load_instrument('p300_multi_gen2', 'left', tip_racks=[p300_tip])
#p300_single = protocol.load_instrument('p300_single_gen2', 'right', tip_racks=[p300_tip])

#Define flow rates
p300_multi.flow_rate.aspirate = 50
p300_multi.flow_rate.dispense = 100
p300_multi.flow_rate.blow_out = 150
p300_single.flow_rate.aspirate = 50
p300_single.flow_rate.dispense = 100
p300_single.flow_rate.blow_out = 150

#Step 1: Distribute PBS (diluent) to col 1-8 and 10-11 of source plate
p300_multi.pick_up_tip()
for col in list(range(0, 8)) + list(range(9, 11)):
    dest = source.columns()[col]
    p300_multi.aspirate(100, reservior.wells()[0])
    p300_multi.dispense(100, dest[0])
    p300_multi.blow_out(dest[0])
p300_multi.drop_tip()
protocol.comment('PBS added')

#Step 2: Inducer A serial dilution
p300_multi.pick_up_tip()
p300_multi.aspirate(100, reservior.wells()[1])
p300_multi.dispense(100, source.columns()[7][0])
p300_multi.mix(3, 150, source.columns()[7][0])
p300_multi.blow_out(source.columns()[7][0])
for col in range(7, 0, -1):
    source1 = source.columns()[col][0]
    dest = source.columns()[col-1][0]
    p300_multi.aspirate(100, source1)
    p300_multi.dispense(100, dest)
    p300_multi.mix(3, 150, dest)
    p300_multi.blow_out(dest)
p300_multi.aspirate(100, source.columns()[0][0]) #remove 100ul from col 1
p300_multi.drop_tip()
protocol.comment('Inducer A serial dilution complete')

#Step 3: Inducer B serial dilution
for col in range(9, 11):
    p300_single.pick_up_tip()
    p300_single.aspirate(100, reservior.wells()[2])
    p300_single.dispense(100, source.columns()[col][7])
    p300_single.mix(3, 150, source.columns()[col][7])
    p300_single.blow_out(source.columns()[col][7])
    for row in range(7, 0, -1):
        source1 = source.columns()[col][row]
        dest = source.columns()[col][row-1]
        p300_single.aspirate(100, source1)
        p300_single.dispense(100, dest)
        p300_single.mix(3, 150, dest)
        p300_single.blow_out(dest)
    p300_single.drop_tip()
protocol.comment('Inducer B serial dilution complete')
protocol.comment('After completion of this protocol, replace p300 single channel pipette ' \
'with p20 multi channel pipette and start the subsequent protocol.')

for line in protocol.commands(): 
        print(line)