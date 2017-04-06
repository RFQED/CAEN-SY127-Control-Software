#Channel Settings (cr1 = Crate #1)
#Enter in the channel numbers in each crate
# Crate 1 goes from CH00 to CH79
# Crate 2 goes from CH80 to CH159
#cr1Chs = [0, 1, 2, 3, 20, 21, 22, 23, 24, 25, 26, 27]
#cr2Chs = []
#allChs = [0, 1, 2, 3, 20, 21, 22, 23, 24, 25, 26, 27]

cr1Chs = [0, 1, 2, 3 ]
cr2Chs = [40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71]
allChs = [0, 1, 2, 3, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71 ]


module1Chs = []
module2Chs = []
module3Chs = []
module4Chs = []
module5Chs = []
module6Chs = []
module7Chs = []
module8Chs = []
unusedCHs = []
numOfChannels = len(allChs)
totalAmountOfOutputs = 80

numChsTotal = len(allChs)
numCr1Chs = len(cr1Chs)
numCr2Chs = len(cr2Chs)


'''
CH00: M0V0, CH01: M0V1, CH02: M0V2, CH03: M0V3 
CH08: M0U0, CH09: M0U1, CH10: M0U2, CH17: M0U3
CH18: M1V0, CH25: M1V1, CH27: M1V2, CH32: M1V3
CH33: M1U0, CH34: M1U1, CH35: M1U2, CH36: M1U3 
'''

# Connection Settings
baud_rate = 4800
shortDelay = 0.55
longDelay = 0.85
serial_addr = '/dev/ttyUSB1'

# File Names : add _1 to denote this for the modules in "tracker 1"
output_file_name = '/home/daq/tracker/online/gm2trackerdaq/software/SlowControls/HV/HV_Monitor_Only_Test/CAEN-SY127-Control-Software/output.txt'
HV_DATA_FILE_NAME = '/home/daq/tracker/online/gm2trackerdaq/software/SlowControls/HV/HV_Monitor_Only_Test/CAEN-SY127-Control-Software/HV_Data.txt'

#limits  Max CHs| Max V | Max I | MAX RUP | MAX RDN | Max Trip Time | Power State (unused)
# limits  =  80 |  1500 |   1   |   10    |    20   |       0       |         4
limits = [80,1600,1,10,20,0,4]
change_titles = ["CH", "V0", "I0", "RUP" , "RDN" , "TRIP_TIME", "POWER"]
units         = [ "0", "V" , "uA", "V/s" , "V/s" , "ms" , "ON/OFF"]
