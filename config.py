
#Channel Settings (cr1 = Crate #1)
cr1Chs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
cr2Chs = []
allChs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
module1Chs = [0, 1, 2, 3, 4, 5, 6, 7]
module2Chs = []
module3Chs = []
module4Chs = []
module5Chs = []
module6Chs = []
module7Chs = []
module8Chs = []
unusedCHs = [8, 9, 10, 11]
numOfChannels = len(allChs)
totalAmountOfOutputs = 79


# Connection Settings
baud_rate = 4800
shortDelay = 0.55
longDelay = 0.85
serial_addr = '/dev/ttyS0'

can_Read_File = '/home/g2uol/Desktop/HV_GUI/HV_GUI_V2/can_read.txt'

# File Names
output_file_name = '/home/g2uol/Desktop/HV_GUI/HV_GUI_V2/HV_Data_3.txt'
#HV_DATA_FILE_NAME = 'HV_Data.txt'
HV_DATA_FILE_NAME = '/home/g2uol/Desktop/HV_GUI/HV_GUI_V2/HV_Data_3.txt'




#limits  Max CHs| Max V | Max I | MAX RUP | MAX RDN | Max Trip Time | Power State (unused)
# limits  =  80 |  1500 |   1   |   10    |    20   |       0       |         4
limits = [80,1500,1,10,20,0,4]
change_titles = ["CH", "V0", "I0", "RUP" , "RDN" , "TRIP_TIME", "POWER"]
units         = [ "0", "V" , "uA", "V/s" , "V/s" , "ms" , "ON/OFF"]
