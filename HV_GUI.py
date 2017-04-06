import sys
from PyQt4 import QtCore, QtGui
import time
import HV_GUI_UI_NoChanges
import serial # so we can talk over serial
from config import *
from datetime import datetime, timedelta
from itertools import islice
import os, signal #signal needed for killing PID for Listener

from dateutil.relativedelta import relativedelta
#https://pypi.python.org/pypi/python-dateutil/2.5.3

global Elements,  minheight, maxheight, height,  width, errorsignal, config, old_date, PID, currentTimeDate, time_read
minheight = 750 #hardcoded, change UI before changing these values 
maxheight = 900
height = minheight #starts with debug box hidden
width = 1000 
errorsignal = 0 #errorsignal is used to pass a signal back to MainWindow from ErrorWindow to detect which button has been pressed 
old_date = 0
curr_time = 0
currentTimeDate = datetime.now()
time_read = 0

ser = serial.Serial(serial_addr, baud_rate, timeout=3, parity=serial.PARITY_EVEN)
ser.setDTR(False)  #toggle Data Terminal Ready - makes sure all serial data is passed back

class ConnectThread(QtCore.QThread): # connect thread. so we can constantly read data
    data_downloaded = QtCore.pyqtSignal(object , object) #passing back two objects 
                                                                  #HV_Data and HV_ENABLE status
    def __init__(self, url):
        QtCore.QThread.__init__(self)
        self.url = url
        print(url) 

    def run(self):
        global RUN, old_date 
        HV_DATA = []
        output_file = open(HV_DATA_FILE_NAME, 'a', os.O_NONBLOCK) #none blocking so can write in one file and read from another

        #we are now in create 1 and will loop over checking the values of the supplys (both cr1 and cr2)
        while (RUN == 1): # loop forever

	    ## BEFORE STARTING THE MONITORING LOOP
            ## check what crate we are talking to - need to start on cr1 
            crateCheck = False
            while crateCheck == False:
                ser.write("1") #make sure supply is on top menu
                ser.read(9000) #if you dont do something with the serial data waiting on the line it will stay there
                time.sleep(shortDelay)
	
                ser.write("1") #make sure supply is on top menu
                crateNumberCheck = ser.read(9000) #if you dont do something with the serial data waiting on the line it will stay there
                time.sleep(shortDelay)

                if "CRATE #[1]" in crateNumberCheck:
                    print("In crate 1 - continue...")
                    crateCheck = True
                elif "CRATE #[2]" in crateNumberCheck:
                    print("In crate 2 - changing to to #1...")
                    ser.write("i")
                    time.sleep(shortDelay)
                    ser.write("1")
                    time.sleep(shortDelay)
                    ser.write("\r")
                    time.sleep(shortDelay)
                    ser.write("\r")
                    time.sleep(shortDelay)
                    ser.write("1")
                    crateNumberCheck = ser.read()
                else:
                    print("No crate number found - Error!")
                    print("Sending CTRL-C to try and fix - Please Wait ")
                    ser.write("\x03".encode('ASCII'))  #send ctrl-c
                    ser.write("1")
                    time.sleep(5)

	    try:
	        output_file = open(HV_DATA_FILE_NAME, 'a', os.O_NONBLOCK) #none blocking so can write in one file and read from another
	    except IOError:
	        print("Can not open HV Data file to save to")
	    
	    ser.write("1") #make sure supply is on top menu
	    ser.read(9000) #if you dont do something with the serial data waiting on the line it will stay there
	    time.sleep(shortDelay)
	
	    ser.write("1") #make sure supply is on top menu
	    ser.read(9000) #if you dont do something with the serial data waiting on the line it will stay there
	    time.sleep(shortDelay)

	    ser.write("A") #change to the display params window
	    serialInput = ser.read(8192).strip().split('\n') # read 8192 bytes or until timeout (set to 3)
            #TODO put try catch around above line?
	    
	    HV_ENABLE = serialInput[22].split(" ")
	    try:
	        HV_ENABLE_val = HV_ENABLE[26].strip('\r')
	    except IndexError:
	        print("Can't find HV_ENABLE in data coming back")
	
	    if HV_ENABLE_val not in ["ON","OFF"]:
	        print("HV ENABLE STRING NOT FOUND")
            else:
                print("HV Enable Setting found - HV is " + str(HV_ENABLE_val))
	        
	    for i in range(0,26):
	        serialInput.pop(0) #kills the formatting lines
	        
	    serialInput.pop()#kills the escape sequence chars (not checked this after changing pop(10) to pop() which gets last entry. 
	    
	    serialDataTmp=[]
	    HVData=[]
	    
            if len(cr1Chs) < 10:
                for i in range(0,len(cr1Chs)):
                    serialDataTmp.append([j for j in serialInput[i].split(' ') if j != ''])#strips empty ,'', from channel vars
                    HVData.append([j for j in serialDataTmp[i] if j != '\r'])     #strips ,'\r', from channel vars list
	    else:
                for i in range(0,10):
                    serialDataTmp.append([j for j in serialInput[i].split(' ') if j != ''])#strips empty ,'', from channel vars
                    HVData.append([j for j in serialDataTmp[i] if j != '\r'])     #strips ,'\r', from channel vars list

            del serialDataTmp[:]
            #now here we see if the number of elements (channels) in HVData is = number of channels present.
            #if not we press 'p' to go to the next page then there should be number of chans - 9 on this page. 
	        
	    print("Number of channels present in crate 1 is  " + str(numCr1Chs) + " and amount of channels in HVData is currently " + str(len(HVData)) + "...")	    

	    while numCr1Chs > len(HVData): #if number of channels in config is > num of channels read, press p to go to next page of channels
	         #and get the data from these ones too, save these to end of the HVData list. 
	        print("Number of channels in use is greater than the amount of channels read so far. Pressing P to go to next page...")
	        ser.write("p") #go to next page of channels  
	        serialInput_P = ser.read(8192).strip().split('\n') # read 8192 bytes or until timeout (set to 3)
	        
	        for i in range(0,26):
	            serialInput_P.pop(0) #kills the formatting lines
	    
	        serialInput_P.pop()#kills the escape sequence chars (not checked this after changing pop(10) to pop() which gets last entry. 
	    
	        serialDataTmp_P=[]
	        
	        for i in range(0,len(serialInput_P)):
	            serialDataTmp_P.append([j for j in serialInput_P[i].split(' ') if j != ''])#strips empty ,'', from channel vars
	            HVData.append([j for j in serialDataTmp_P[i] if j != '\r'])#strips ,'\r', from channel vars list
	            
                print("length of HVData is now" + str(len(HVData)) )
	        for i in range(0,len(HVData)):
	            print(str(HVData[i]))

                print("..........")
	        #done with extra channels pressing p (should have check to see if got all channels yet)

                del serialDataTmp_P[:]

      	    print("Number of channels present in crate 1 is  " + str(numCr1Chs) + " and amount of channels in HVData is currently " + str(len(HVData)) + "... Finished Reading from Crate #1")	    
	    
            ##################################################################
            ####
            ####                Going to crate #2
            ####
            ##################################################################

	    if (len(cr2Chs) != 0):
                print("Channels are present in Crate #2 - going to get them now...")
	        crateCheck = False
	        while crateCheck == False:
	            ser.write("1") #make sure supply is on top menu
	            ser.read(9000) #if you dont do something with the serial data waiting on the line it will stay there
	            time.sleep(shortDelay)
		
	            ser.write("1") #make sure supply is on top menu
	            crateNumberCheck = ser.read(9000) #if you dont do something with the serial data waiting on the line it will stay there
	            time.sleep(shortDelay)
	
		    if "CRATE #[2]" in crateNumberCheck:
		        print("In crate 2 - continue...")
		        crateCheck = True
		    elif "CRATE #[1]" in crateNumberCheck:
		        print("In crate 1 - changing to to #2...")
		        ser.write("i")
		        time.sleep(shortDelay)
		        ser.write("2")
		        time.sleep(shortDelay)
		        ser.write("\r")
		        time.sleep(shortDelay)
		        ser.write("\r")
		        time.sleep(shortDelay)
		        ser.write("1")
		        crateNumberCheck = ser.read()
		    else:
		        print("No crate number found - Error!")
		        print("Sending CTRL-C to try and fix - Please Wait ")
	                ser.write("\x03".encode('ASCII'))  #send ctrl-c
		        ser.write("1")
		        time.sleep(5)

                #should now be in crate #2 - loop over the menus until all channels are read
                ser.write("1")
                ser.read(9000)
                ser.write("A") #display params
                serialInput = ser.read(8192).strip().split('\n') # read 8192 bytes or until timeout (set to 3)

                for i in range(0,26):
                    serialInput.pop(0) #kills the formatting lines
	                
                serialInput.pop()#kills the escape sequence chars (not checked this after changing pop(10) to pop() which gets last entry. 
	    
                serialDataTmp=[]
	                
                for i in range(0,10):
                    serialDataTmp.append([j for j in serialInput[i].split(' ') if j != ''])#strips empty ,'', from channel vars
                    HVData.append([j for j in serialDataTmp[i] if j != '\r'])#strips ,'\r', from channel vars list

                for i in range(0,len(HVData)):
                    print(str(HVData[i]))

                print("Number of channels present in crate 2 is  " + str(numCr2Chs) + " and amount of channels in HVData is currently " + str(len(HVData)) + "...")	    

                while len(HVData) < numOfChannels: #if number of channels in config is > num of channels read, press p to go to next page of channels
	                #and get the data from these ones too, save these to end of the HVData list. 
                    print("Number of channels in use is greater than the amount of channels read so far. Pressing P to go to next page...")
                    ser.write("p") #go to next page of channels  
                    serialInput_P = ser.read(8192).strip().split('\n') # read 8192 bytes or until timeout (set to 3)
	        
                    for i in range(0,26):
	                serialInput_P.pop(0) #kills the formatting lines
	    
                    serialInput_P.pop()#kills the escape sequence chars (not checked this after changing pop(10) to pop() which gets last entry. 
	    
                    serialDataTmp_P=[]
	        
                    for i in range(0,len(serialInput_P)):
	                serialDataTmp_P.append([j for j in serialInput_P[i].split(' ') if j != ''])#strips empty ,'', from channel vars
                        HVData.append([j for j in serialDataTmp_P[i] if j != '\r'])#strips ,'\r', from channel vars list
	            
                    del serialDataTmp_P[:]
                    del serialInput_P[:]

                    for i in range(0,len(HVData)):
                        print(str(HVData[i]))

                    print("..........")
	            #done with extra channels pressing p (should have check to see if got all channels yet)


	    if numChsTotal <= len(HVData):
	        print("got all the channels data")
	        currentTimeOnly = time.strftime("%H:%M:%S")
	        currentDateOnly = time.strftime("%d/%m/%Y")
                currentDateTime = time.strftime("%d/%m/%Y %H:%M:%S")

	        currentUTC      = int(time.time())

                oldTimeDate = time.strftime("%H:%M:%S %d/%m/%Y")

	        opStr = "TIME %d %s %s" % (currentUTC,currentDateTime,str(HV_ENABLE_val)) 
	        output_file.write(opStr + "\n")
	        
	        for i in range(0,numChsTotal):
	            if HVData[i][10]=='TRIP':   #TRIP MESSAGE MAY BE DIFFERENT THAN THIS 'OVC', 'OVV' check. 
	                print(HVData[i][0] + " has TRIPPED") 
	                #send err to MIDAS
	    
	        for ch in HVData:
	            for elem in ch:
	                try:
	                    output_file.write(elem.strip())
	                    output_file.write(" ")
	    
	                except IOError:
	                    print("Saving HV Data to file FAILED")
	                    
	            output_file.write("\n")

	    output_file.flush()
	
            global time_read
            time_read = datetime.now()


	    print(".............................")	    
	    print("Read all channels listed in use in the config file - they are....")
            
            for i in range(0,len(HVData)):
                print(str(HVData[i]))

	    print(".............................")

            print("length of HV data is " + str(len(HVData)))
            self.data_downloaded.emit(HVData, HV_ENABLE_val) # data that is sent back. 

            print("Read Loop Complete")
	    #del HVData[:]
	    del serialInput[:]
            
            time.sleep(0.5) #do loop every N sec

class TimeThread(QtCore.QThread): # time thread. so we can costantly update the time
    setTime = QtCore.pyqtSignal(object)
    print("Time Thread Started")
    def __init__(self, url):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            #sets the labels for date and time
            currentTimeOnly = datetime.now()
            self.setTime.emit(currentTimeDate) # data that is sent back. 
            time.sleep(1)
                
# ==== Main UI Window ==== #
class HV_GUI_App(QtGui.QMainWindow, HV_GUI_UI_NoChanges.Ui_MainWindow):
    def __init__(self):                            # allows us to access variables, methods etc in the design.py file
        super(self.__class__, self).__init__()
        self.setupUi(self)                         # This is defined in HV_GUI.py file automatically

        self.threads = [] 
        time = TimeThread("Setting_Time")
        time.setTime.connect(self.time_set)
        self.threads.append(time)
        time.start()

        #displays contents of contents file in GUI
        with open("config.py" , "r") as configfile:
            self.config_file_browser.setText(configfile.read())        

     # It sets up layout and widgets that are defined

        self.setFixedSize(width, height)                # Fixes windows size. Can be resized using def expand below.
        self.setWindowTitle("TRACKER - CAEN SY127 HV System")

        pixmap = QtGui.QPixmap('g-2-tracker-logo-192.ico')
        self.gm2_logo.setPixmap(pixmap)#top right logo
  
        self.exit_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)

        self.connect_button.clicked.connect(self.connect)
        self.disconnect_button.clicked.connect(self.disconnect)
        self.exit_button.clicked.connect(self.exit)
        self.expand_button.clicked.connect(self.expand)

        self.connect_button.click()#click automatically

        self.TextBox_btm.setReadOnly(True)

        print("GUI SET UP")
    
    def time_set(self, datetime):
        global time_read
        
        currentTime = datetime.now()
        
#        print("currentTime " + str(currentTime) )
#        print("time read " + str(time_read) )

        diff = relativedelta(currentTime, time_read) #using the dateutil package

        if (diff.hours == 0) and (diff.minutes == 0):
            self.time_since_update.setText(str(diff.seconds) + "s")
        elif diff.hours == 0:
            self.time_since_update.setText(str(diff.minutes) + "min " + str(diff.seconds) + "s")
        elif diff.days == 0:
            self.time_since_update.setText(str(diff.hours) + "hr " + str(diff.minutes) + "min " + str(diff.seconds) + "s")
        else:
            self.time_since_update.setText(str(diff.days) + "days " + str(diff.hours) + "hrs " + str(diff.minutes) + "mins")

        #above sets the correct date since update in the GUI based on the time in the
        #Current Date - HV data file date. This lets you know how long its been since
        #the HV module spat data out.
                   
        self.date.setText(str(currentTime.date()))
        self.time.setText(str(currentTime.strftime("%H:%M:%S")))

    def connect(self): #starts the connect thread
        #this thread is used to send data back at the same time 
        # as the GUI is open.
        global RUN
        RUN = 1

        try:
            self.TextBox_btm.moveCursor(QtGui.QTextCursor.End)
            self.TextBox_btm.insertPlainText("Retrieving data...\n")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)

            downloader = ConnectThread(" Connecting to SY 127 to read values ")
            downloader.data_downloaded.connect(self.on_data_ready)
            self.threads.append(downloader)
            downloader.start()
        except IOError:
            print("Error in the connect thread !")

    def on_data_ready(self, input_data, HV_ENABLE): # shit that happens when data comes back from connectThread
        #might need to put a check in here to ensure data coming is in the right format. 
        font = QtGui.QFont("Courier") 
        
        print("Got to on_data_ready.... ")
        print("Length of HVData " + str(len(input_data)))

        self.hv_enable.setText(HV_ENABLE)
        if HV_ENABLE == "ON":
            self.hv_enable.setStyleSheet('color: green')
        if HV_ENABLE == "OFF":
            self.hv_enable.setStyleSheet('color: black')

        empty_channel = ["-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1"]
        #fills empty channels with spacers. these -1s are not used in the GUI but stored
        # to keep everything in correct ordering.
        
        while (len(input_data) != totalAmountOfOutputs+1):
            input_data.append(empty_channel)
        
        HV_DATA_tmp = [[] for x in range(0,totalAmountOfOutputs+1)] #make HV_DATA list of list
        HV_DATA_Arranged_list = [[] for x in range(0,totalAmountOfOutputs+1)] #make HV_DATA list of list
        HV_DATA = [[] for x in range(0,totalAmountOfOutputs+1)]
        '''   Vmon IMon
	['CH00 0 0 0 0 1 1 10 20 0 OFF']
	['CH01 0 0 0 0 1 1 10 20 0 OFF']
	['CH02 0 0 0 0 1 1 10 20 0 OFF']
	['CH03 0 0 0 0 1 1 10 20 0 OFF']
        ...
	
	is a list
	
	[['CH00', '0', '0', '0', '0', '1', '1', '10', '20', '0', 'OFF'], ['CH01', '0', '0', '0', '0', '1', '1', '10', '20', '0', 'OFF'], ... ,['CH11', '0', '0', '0', '0', '1', '1', '10', '20', '0', 'OFF']]
	
	is a list of lists = HV_DATA
        '''
        # get input_data from the listener thread
        # split each elelment in each list to make list of lists
        # re-arrange elements based on channel number
        # filling blank channels with -1s

        self.TextBox_btm.setFont(font)
#        global numOfChannels
#        self.TextBox_btm.insertPlainText( "   VMON  IMON   V0     V1     I0    I1    RUP   RDW   T  STATUS | " + input_data[0][0] + "\n")
         
       # input_data.pop(0)#del date

        for i in range (0,numOfChannels):
            for j in range (0, len(input_data[i])):
                self.TextBox_btm.insertPlainText(str(input_data[i][j]))#fill text box with data from file
                self.TextBox_btm.insertPlainText("\n")

        for i in range(0, totalAmountOfOutputs):
            HV_DATA_tmp[i] = [x for y in input_data[i] for x in y.split()]

        for i in range(0,totalAmountOfOutputs):
            if HV_DATA_tmp[i][0] != "-1":
                chNum = HV_DATA_tmp[i][0].strip("CH")
                HV_DATA_Arranged_list[int(chNum)]=HV_DATA_tmp[i]
                
        for i in range(0,totalAmountOfOutputs):
            if (len(HV_DATA_Arranged_list[i]) == 0):
                HV_DATA[i]=empty_channel
            else:
                HV_DATA[i]=HV_DATA_Arranged_list[i]
            
        global glo_input_data
        glo_input_data = HV_DATA

        for i in range(0,totalAmountOfOutputs):
            if "-1" not in HV_DATA[i]:            
                #FILL AND ALIGN VMON 
                fill_VMon_cmd = "self.VMon_"+str(i)+".setText(HV_DATA["+str(i)+"][1])"
                eval(fill_VMon_cmd)
                VMon_Align_cmd = "self.VMon_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(VMon_Align_cmd)
                
                #FILL AND ALIGN IMON
                fill_IMon_cmd = "self.IMon_"+str(i)+".setText(HV_DATA["+str(i)+"][2])"
                eval(fill_IMon_cmd)
                IMon_Align_cmd = "self.IMon_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(IMon_Align_cmd)

                #FILL V0  
                fill_V0 = "self.V0_"+str(i)+".setText(HV_DATA["+str(i)+"][3])"
                eval(fill_V0)
                V0_Align_cmd = "self.V0_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(V0_Align_cmd)
        
                #FILL I0 
                fill_I0 = "self.I0_"+str(i)+".setText(HV_DATA["+str(i)+"][5])"
                eval(fill_I0)
                I0_Align_cmd = "self.I0_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(I0_Align_cmd)
                
                #fill RUP
                fill_RUP = "self.RUP_"+str(i)+".setText(HV_DATA["+str(i)+"][7])"
                eval(fill_RUP)
                RUP_Align_cmd = "self.RUP_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(RUP_Align_cmd)
                
                #fill Ramp Down
                fill_RDN = "self.RDN_"+str(i)+".setText(HV_DATA["+str(i)+"][8])"
                eval(fill_RDN)
                RDN_Align_cmd = "self.RDN_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(RDN_Align_cmd)
                
                #fill trip time
                fill_Trip="self.trip_"+str(i)+".setText(HV_DATA["+str(i)+"][9])"
                eval(fill_Trip)
                Trip_Align_cmd = "self.trip_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(Trip_Align_cmd)
            
                # Fills Status Info
                fill_Status ="self.S_"+str(i)+".setText(HV_DATA["+str(i)+"][10])"
                eval(fill_Status)
                Stat_Align_cmd = "self.S_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                eval(Stat_Align_cmd)


                if HV_DATA[i][10] == "ON": #sets the chceck boxes for power to true
                    power_status = "self.P_"+str(i)+".setChecked(True)"
                    eval(power_status)
                
                elif HV_DATA[i][10] == "OFF": #sets them to false if OFF or TRIP
                    power_status = "self.P_"+str(i)+".setChecked(False)"
                    eval(power_status)

                elif HV_DATA[i][10] == "TRIP":
                    power_status = "self.P_"+str(i)+".setChecked(False)"
                    eval(power_status)
                    
                if len(HV_DATA[i]) == 12:
                    ramp_status = "self.RS_"+str(i)+".setText(HV_DATA["+str(i)+"][11])"
                    eval(ramp_status)
                    ramp_Align_cmd = "self.RS_"+str(i)+".setAlignment(QtCore.Qt.AlignCenter)"
                    eval(ramp_Align_cmd)


                #MODULE 1 STATUS SCREEN
                if (i in module1Chs):
                    Module_Input_Data = [j for j,x in enumerate(module1Chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0] #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON' and HV_ENABLE == "OFF":
                        fill_M1 = "self.M1_"+str(Module_Input_Data)+".setStyleSheet('color: orange')"
                        eval(fill_M1)
                    elif HV_DATA[i][10] == 'ON' and HV_ENABLE == "ON":
                        fill_M1 = "self.M1_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M1)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M1 = "self.M1_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M1)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M1 = "self.M1_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M1)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M1 = "self.M1_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M1)


                        # put in overvoltage OVV and undervoltage UNV. 

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M1 = "self.M1_"+str(Module_Input_Data) +".setStyleSheet('color: yellow')"
                            eval(fill_M1)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M1 = "self.M1_"+str(Module_Input_Data) +".setStyleSheet('color: blue')"
                            eval(fill_M1)


                #MODULE 2 STATUS SCREEN
                if (i in module2Chs):
                    Module_Input_Data = [j for j,x in enumerate(module2Chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0]  #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON':
                        fill_M2 = "self.M2_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M2)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M2 = "self.M2_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M2)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M2 = "self.M2_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M2)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M2 = "self.M2_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M2)

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M2 = "self.M2_"+str(Module_Input_Data)+".setStyleSheet('color: yellow')"
                            eval(fill_M1)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M2 = "self.M2_"+str(Module_Input_Data)+".setStyleSheet('color: blue')"
                            eval(fill_M2)


                #MODULE 3 STATUS SCREEN
                if (i in module3Chs):
                    Module_Input_Data = [j for j,x in enumerate(module3Chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0]  #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON':
                        fill_M3 = "self.M3_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M3)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M3 = "self.M3_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M3)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M3 = "self.M3_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M3)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M3 = "self.M3_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M3)

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M3 = "self.M3_"+str(Module_Input_Data)+".setStyleSheet('color: yellow')"
                            eval(fill_M3)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M3 = "self.M3_"+str(Module_Input_Data)+".setStyleSheet('color: blue')"
                            eval(fill_M3)


                #MODULE 4 STATUS SCREEN
                if (i in module4Chs):
                    Module_Input_Data = [j for j,x in enumerate(module4Chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0]  #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON':
                        fill_M4 = "self.M4_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M4)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M4 = "self.M4_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M4)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M4 = "self.M4_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M4)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M4 = "self.M4_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M4)

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M4 = "self.M4_"+str(Module_Input_Data)+".setStyleSheet('color: yellow')"
                            eval(fill_M4)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M4 = "self.M4_"+str(Module_Input_Data)+".setStyleSheet('color: blue')"
                            eval(fill_M4)


                #MODULE 5 STATUS SCREEN
                if (i in module5Chs):
                    Module_Input_Data = [j for j,x in enumerate(module5Chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0] #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON':
                        fill_M5 = "self.M5_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M5)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M5 = "self.M5_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M5)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M5 = "self.M5_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M5)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M5 = "self.M5_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M5)

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M5 = "self.M5_"+str(Module_Input_Data)+".setStyleSheet('color: yellow')"
                            eval(fill_M5)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M5 = "self.M5_"+str(Module_Input_Data)+".setStyleSheet('color: blue')"
                            eval(fill_M5)


                #MODULE 6 STATUS SCREEN
                if (i in module6Chs):
                    Module_Input_Data = [j for j,x in enumerate(module6Chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0]  #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON':
                        fill_M6 = "self.M6_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M6)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M6 = "self.M6_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M6)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M6 = "self.M6_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M6)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M6 = "self.M6_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M6)

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M6 = "self.M6_"+str(Module_Input_Data)+".setStyleSheet('color: yellow')"
                            eval(fill_M6)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M6 = "self.M6_"+str(Module_Input_Data)+".setStyleSheet('color: blue')"
                            eval(fill_M6)

                #MODULE 7 STATUS SCREEN
                if (i in module7Chs):
                    Module_Input_Data = [j for j,x in enumerate(module7chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0]  #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON':
                        fill_M7 = "self.M7_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M7)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M7 = "self.M7_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M7)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M7 = "self.M7_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M7)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M7 = "self.M7_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M7)

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M7 = "self.M7_"+str(Module_Input_Data)+".setStyleSheet('color: yellow')"
                            eval(fill_M7)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M7 = "self.M7_"+str(Module_Input_Data)+".setStyleSheet('color: blue')"
                            eval(fill_M7)

                #MODULE 8 STATUS SCREEN
                if (i in module8Chs): 
                    Module_Input_Data = [j for j,x in enumerate(module8Chs) if x == i] #finds the input_data number from position of channel number in module input_datas list. 
                    Module_Input_Data = Module_Input_Data[0]  #brings module_input_datas to correct number
                    if HV_DATA[i][10] == 'ON':
                        fill_M8 = "self.M8_"+str(Module_Input_Data)+".setStyleSheet('color: green')"
                        eval(fill_M8)
                    elif HV_DATA[i][10] == 'OFF':
                        fill_M8 = "self.M8_"+str(Module_Input_Data)+".setStyleSheet('color: black')"
                        eval(fill_M8)
                    elif HV_DATA[i][10] == 'TRIP':
                        fill_M8 = "self.M8_"+str(Module_Input_Data)+".setStyleSheet('color: red')"
                        eval(fill_M8)
                    elif  HV_DATA[i][10] == 'OVC':
                        fill_M8 = "self.M8_"+str(Module_Input_Data)+".setStyleSheet('color: pink')"
                        eval(fill_M8)

                    if len(HV_DATA[i]) == 12:
                        if (HV_DATA[i][11] == "UP"):
                            fill_M8 = "self.M8_"+str(Module_Input_Data)+".setStyleSheet('color: yellow')"
                            eval(fill_M8)
                        elif (HV_DATA[i][11] == "DOWN"):
                            fill_M8 = "self.M8_"+str(Module_Input_Data)+".setStyleSheet('color: blue')"
                            eval(fill_M8)
                

#CHECK WHAT OCMES OUT OF THE SUPPLY FOR RAMPING STATUS AND TRIP STATUS MESSAGES 

    def disconnect(self):
        #send signal to the listener to stop listening, so we can send changes. 
        # once changes have been made make sure we change can_read.txt to y 
        global RUN
        RUN = 0
        print("Disconnect Pressed - Run Value changed - Will stop talking to the crate after the current cycle has finished")
        self.disconnect_button.setEnabled(False)
        self.connect_button.setEnabled(True)
            
    def exit(self):
        print("GUI has been terminated")
        self.deleteLater()

    def expand(self):
        global minheight, maxheight, height,  width
        if height == minheight:
            self.setFixedSize(width, maxheight)
            height = maxheight
            print("Window expanded.")
        else:
            self.setFixedSize(width, minheight)
            height = minheight
            print("Window contracted.")
# =============================================================================================

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = HV_GUI_App()
    window.show()
    sys.exit(app.exec_())

#todo - if the supply is restarted or power cycled need to make sure that the group is set to ALL and that under change global absolute the verify is set to NO so kill works.

#TODO- find a way to stop the autofil when a value is changed to be set
# plot the voltages over time (could live stream with plotly

# Cable # in GUI to help debug trips and stuff.

# TODO End plotly stream with  stream.close()
