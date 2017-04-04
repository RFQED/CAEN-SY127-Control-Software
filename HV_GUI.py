import sys
from PyQt4 import QtCore, QtGui
import time
import HV_GUI_UI_NoChanges , error_GUI
import serial # so we can talk over serial
from config import *
from datetime import datetime, timedelta
from itertools import islice
import os, signal #signal needed for killing PID for Listener

from dateutil.relativedelta import relativedelta
#https://pypi.python.org/pypi/python-dateutil/2.5.3

global Elements,  minheight, maxheight, height,  width, errorsignal, config, old_date, PID
minheight = 750 #hardcoded, change UI before changing these values 
maxheight = 900
height = minheight #starts with debug box hidden
width = 1000 
errorsignal = 0 #errorsignal is used to pass a signal back to MainWindow from ErrorWindow to detect which button has been pressed 
old_date = 0

ser = serial.Serial(serial_addr, baud_rate, timeout=3)
ser.setDTR(False)  #toggle Data Terminal Ready - makes sure all serial data is passed back

try:
    with open(Listener_PID_File, 'r', os.O_NONBLOCK) as f:
        PID = f.readline() #write PID to file
        print("Read PID file") #this is used when using the KILL function in GUI
except IOError:
    print("PID file open failed")



class ConnectThread(QtCore.QThread): # connect thread. so we can constantly read data
    data_downloaded = QtCore.pyqtSignal(object , object , object) #passing back three objects 
                                                                  #HV_Data, time diff and HV_ENABLE status
    def __init__(self, url):
        QtCore.QThread.__init__(self)
        self.url = url
        print(url) 

    def run(self):
        global RUN, old_date 
        HV_DATA = []
        while (RUN == 1): # loop forever
            try:
                with open(HV_DATA_FILE_NAME) as HV_DATA_FILE:#read the last X lines from the HV_Data_file
                    tail = list(islice(reversed(list(HV_DATA_FILE)), numOfChannels+1) )   #where X is the amount of channels in the config (+1 for the time)
            
                for i in range(len(tail)-1,-1,-1): #puts list ordering back in correct order
                    HV_DATA.append(tail[i].strip().split("\n"))

                if old_date != HV_DATA[0]: #'checks to see if the last date entry is new. if it is send data
                    old_date = str(HV_DATA[0])
                    old_date = old_date.strip('[]').strip('\'')
                
                    stamp, utc_time, curr_time, date, HV_ENABLE = old_date.split()
                    #splits the top line of the data into the time, date and the HV enable string
                    #then joins the time and date back again for the difference calc. 
                
                    old_date = str(curr_time) + " " + str(date) 
                    old_date = datetime.strptime(old_date, '%H:%M:%S %d/%m/%Y')
                    current_time = datetime.now()
                    diff = relativedelta(current_time, old_date) #using the dateutil package
                    #difference between old date - new date. 

                    self.data_downloaded.emit(HV_DATA, diff, HV_ENABLE) # data that is sent back. 
            
            except IOError:
                print("Can not open HV Data file - No data sent to GUI")

            time.sleep(5) #do loop every 5sec
            del HV_DATA[:]  

class TimeThread(QtCore.QThread): # time thread. so we can constantly update the time
    setTime = QtCore.pyqtSignal(object)
    print("Time Thread Started")
    def __init__(self, url):
        QtCore.QThread.__init__(self)

    def run(self):
        while True:
            #sets the labels for date and time
            currentTimeOnly = time.strftime("%H:%M:%S")
            currentDateOnly = time.strftime("%d/%m/%Y")
            datetime = currentTimeOnly + "|" + currentDateOnly
            self.setTime.emit(datetime) # data that is sent back. 
            time.sleep(1)
                
# ==== ERROR WINDOW ==== #
class Error_Message(QtGui.QDialog, error_GUI.Ui_Dialog):
    def __init__(self, windowtitle, header, message):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.setWindowTitle(windowtitle)
        self.Error_Title.setText(header)
        self.Error_Message.setText(message)
        self.Error_Buttons.accepted.connect(self.ok) #how to comminicate with the 'Ok' button
        self.Error_Buttons.rejected.connect(self.cancel) #how to comminicate with the 'Cancel' button

    def ok(self):
        global errorsignal
        errorsignal = 1

    def cancel(self):
        global errorsignal
        errorsignal = 0 #probably a better way of doing this
            
# ===/ERROR WINDOW==== #

# ==== Main UI Window ==== #
class HV_GUI_App(QtGui.QMainWindow, HV_GUI_UI.Ui_MainWindow):
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
  
        self.set_button.setEnabled(False)
        self.send_button.setEnabled(False)
        self.kill_button.setEnabled(True)
        self.exit_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)

        self.connect_button.clicked.connect(self.connect)
        self.disconnect_button.clicked.connect(self.disconnect)
        self.set_button.clicked.connect(self.set)
        self.send_button.clicked.connect(self.send)
        self.kill_button.clicked.connect(self.kill)
        self.exit_button.clicked.connect(self.exit)
        self.expand_button.clicked.connect(self.expand)

        self.connect_button.click()#click automatically

        self.change_global_btn.clicked.connect(self.change_globals)
        self.change_global_btn.setEnabled(False)

        self.TextBox_btm.setReadOnly(True)

        print("GUI SET UP")
    
    def time_set(self, datetime):
        currentTime, currentDate = datetime.split('|')
        self.time.setText(currentTime)
        self.date.setText(currentDate)
        

    def connect(self): #starts the connect thread
        #this thread is used to send data back at the same time 
        # as the GUI is open.
        global RUN
        RUN = 1

        try:
            with open(can_Read_File, 'w', os.O_NONBLOCK) as f: #allow listener thread to start listening again
                f.write("y")
                f.flush()
            print("Reading HV_DATA_FILE")
        
            self.TextBox_btm.moveCursor(QtGui.QTextCursor.End)
            self.TextBox_btm.insertPlainText("Retrieving data...\n")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.set_button.setEnabled(False) 
            self.send_button.setEnabled(False)
            self.change_global_btn.setEnabled(False)

            downloader = ConnectThread("Passing to Connect ")
            downloader.data_downloaded.connect(self.on_data_ready)
            self.threads.append(downloader)
            downloader.start()


        except IOError:
            print("Can not change can_read status in file. HV_Listner may not be running!")

    def on_data_ready(self, input_data, diff, HV_ENABLE): # shit that happens when data comes back from connectThread

        #might need to put a check in here to ensure data coming is in the right format. 
        currentTime = time.strftime("%H:%M:%S %d/%m/%Y")

        font = QtGui.QFont("Courier") 

        self.hv_enable.setText(HV_ENABLE)
        if HV_ENABLE == "ON":
            self.hv_enable.setStyleSheet('color: green')
        if HV_ENABLE == "OFF":
            self.hv_enable.setStyleSheet('color: black')


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
            
        empty_channel = ["-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1"]
        #fills empty channels with spacers. these -1s are not used in the GUI but stored
        # to keep everything in correct ordering.
        
        while (len(input_data) != totalAmountOfOutputs+1):
            input_data.append(empty_channel)
        
        HV_DATA_tmp = [[] for x in range(0,79)] #make HV_DATA list of list
        HV_DATA_Arranged_list = [[] for x in range(0,79)] #make HV_DATA list of list
        HV_DATA = [[] for x in range(0,79)]
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
        # get input_data from file
        # split each elelment in each list to make list of lists
        # re-arrange elements based on channel number
        # filling blank channels with -1s

        self.TextBox_btm.setFont(font)
        global numOfChannels
        self.TextBox_btm.insertPlainText( "   VMON  IMON   V0     V1     I0    I1    RUP   RDW   T  STATUS | " + input_data[0][0] + "\n")
         
        input_data.pop(0)#del date

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
        time.sleep(5)
        try:
            with open(can_Read_File, 'w', os.O_NONBLOCK) as f:
                f.write("n")
                f.flush()
                confirmPaused = "n"
                while confirmPaused == "n":
                    with open(can_Read_File, 'r', os.O_NONBLOCK) as f:
                        line = f.readline()
                        confirmPaused = line.rstrip('\n') #logic for blocking reading while GUI is sending changes 
                    #this waits for Listener to change can_read to p to show its paused and ready for us to send changes
                    print("Waiting for Paused to be confirmed")
                    time.sleep(2)
            
            print("paused confirmed  | confirmPaused = " + str(confirmPaused))
            print("Disconnect Pressed")
            can_Read = False
            self.disconnect_button.setEnabled(False)
            self.connect_button.setEnabled(True)
            self.change_global_btn.setEnabled(True)
            self.set_button.setEnabled(True)
            self.send_button.setEnabled(False)
        except IOError:
            print("Error in disconnect. can not save can_read file")
            
    def set(self):
#0    1  2   3   4   5   6    7   8    9 10
#CH35 0  0   0   0   1   1   10   20   0 ON
        
        #for i in allChs:
        #    print("CH" + str(i) + str(glo_input_data[i]))
        
        global final_changes #this holds the changes AFTER they have been checked for limits 
        final_changes = []
        
        curr_Voltage = []
        old_Voltage = []

        curr_current = []
        old_current = []

        curr_RUP = []
        old_RUP = []

        curr_RDN = []
        old_RDN = []

        curr_trip_time = []
        old_trip_time = []

        curr_power = []
        old_power = []

        for i in range (0,79):
            voltages_string = "self.V0_" + str(i) + ".text()"
            GUI_voltage = eval(voltages_string)
            curr_Voltage.append(GUI_voltage)
            old_Voltage.append(glo_input_data[i][3])

            current_string = "self.I0_" + str(i) + ".text()"
            GUI_current = eval(current_string)
            curr_current.append(GUI_current)
            old_current.append(glo_input_data[i][5])

            RUP_string = "self.RUP_" + str(i) + ".text()"
            GUI_RUP = eval(RUP_string)
            curr_RUP.append(GUI_RUP)
            old_RUP.append(glo_input_data[i][7])

            RDN_string = "self.RDN_" + str(i) + ".text()"
            GUI_RDN = eval(RDN_string)
            curr_RDN.append(GUI_RDN)
            old_RDN.append(glo_input_data[i][8])

            trip_time_string = "self.trip_" + str(i) + ".text()"
            GUI_trip_time = eval(trip_time_string)
            curr_trip_time.append(GUI_trip_time)
            old_trip_time.append(glo_input_data[i][9])

            power_string = "self.P_" + str(i) + ".checkState()"
            GUI_power = eval(power_string)
            curr_power.append(GUI_power)
            if glo_input_data[i][10] == "ON":
                old_power.append(2)
            else:
                old_power.append(0)

        print("****************")
        print("GUI Voltages")
        print(curr_Voltage)
        print("file_voltages")
        print(old_Voltage)
        print("****************")
        print("GUI currents")
        print(curr_current)
        print("file_currents")
        print(old_current)
        print("****************")
        print("GUI ramp up")
        print(curr_RUP)
        print("file ramp up")
        print(old_RUP)
        print("****************")
        print("GUI ramp dn")
        print(curr_RDN)
        print("file ramp DN")
        print(old_RDN)
        print("****************")
        print("GUI trip time")
        print(curr_trip_time)
        print("file trip")
        print(old_trip_time)
        print("****************")
        print("GUI POWER")
        print(curr_power)
        print("old power")
        print(old_power)
        print("****************")
        
        changes = [[-1 for x in range(0,7)] for y in range(0,79)] 
        check_changes = [[-1 for x in range(0,7)] for y in range(0,79)] 

        #compares GUI values with file values, saves each channel out, filled with -1's for no changes. 
        #need to include power functionality 
        # for power, can have 0 = changed to off     1 = changed to on    -1 = no change. 
        for i in allChs:
            changes[i][0] = i

            if curr_Voltage[i] != old_Voltage[i]:
                changes[i][1] = int(curr_Voltage[i])

            if curr_current[i] != old_current[i]:
                changes[i][2] = int(curr_current[i])

            if curr_RUP[i] != old_RUP[i]:
                changes[i][3] = int(curr_RUP[i])

            if curr_RDN[i] != old_RDN[i]:
                changes[i][4] = int(curr_RDN[i])

            if curr_trip_time[i] != old_trip_time[i]:
                changes[i][5] = int(curr_trip_time[i])

            if curr_power[i] != old_power[i]:
                changes[i][6] = int(curr_power[i])
            #print("CH" + str(i) + " is " + str(changes[i]))
           # print("Done")
          
        
        #looks in each channels changes - if contains -1's then dont send to HV changes module 
        # if it contains changes send changes to HV control code.
        print("-------------------------------")       
        for ch in allChs:
            for value in range(0,7):
                if (sum(changes[ch])-int(changes[ch][0])) != -6:
                    if changes[ch][value] != -1:
                        #print("Change in CH" + str(ch))
                        if int(changes[ch][value]) > limits[value]:#Error message will pop up
                            self.dialog = Error_Message("Warning Message", "Value Error" ,"" + str(change_titles[value]) + 
                                                        " limit is " + str(limits[value]) + str(units[value]) + " you entered "
                                                        + str(changes[ch][value]) + str(units[value]) + ". Limits can be changed in config.py") 
                        
                            self.dialog.exec_()
                            print("Change can not be made to " + str(change_titles[value]) + " as " + str(changes[ch][value])  +
                                  " is greater than the limit set of " + str(limits[value]) + str(units[value]) + " changing value to -1" )
                        
                            changes[ch][value] = -1

                        else:
                            print("Make changes to " + change_titles[value] + " to " + str(changes[ch][value]) )
                            check_changes[ch][value] = int(changes[ch][value])

                            #make the send button active if no errors. 
                            self.send_button.setEnabled(True)
                    else:
                        print("No changes needed for " + change_titles[value])
            print("-------------------------------")
            if (sum(changes[ch])-int(changes[ch][0])) == -6:
                print("No change needed for CH"+str(ch))

            if (sum(changes[ch])-int(changes[ch][0])) != -6:
                final_changes.append(check_changes[ch])

                #make sure the error window dosent pop up 1000's of times 
                #final_changes is the array/list holding the approved changes. which is global and will be used in send. 
            

        #print("Final changes are -")
        #print(final_changes)
#_____________________________________________________________________
# change_titles = CH |   V0  |  I0  |   RUP   | RDN  |   TRIP | POWER | 
# units         =  0 |   V   |  uA  |   V/s   |  V/s |   ms   |  NA   |
# limits        =  0 |  1500 |  1   |   10    |  20  |   0    |  0    |
# value_changes = CH |   V0  |  I0  |   RUP   | RDN  |   TRIP | POWER | 
#---------------------------------------------------------------------
#changes to CH1, to 1500V, no change in i, change to 10V/s RUP and no other changes 
#changes = (CH1,1500,-1,10,-1,-1)


    
    def send(self): 
        print("in send func got changes " + str(final_changes))
        #in send fucntion get access to final_changes
        #these are checked values and are only changes
        for ch, chan in enumerate(final_changes):
            if ch in cr2Chs:
                print("changing to crate 2")
                #change to other crate. have to think about different ch numbers on other crate. 


            time.sleep(shortDelay)

            ser.write("1".encode('utf-8'))  
            time.sleep(shortDelay)

            ser.write("1".encode('utf-8'))  
            time.sleep(shortDelay)

            ser.write("b".encode('utf-8'))            
            time.sleep(longDelay)

            ser.write("a".encode('utf-8'))            
            time.sleep(longDelay)

            print("Chaning Values of CH " + str("%02d" % final_changes[ch][0]))
            ser.write("a".encode('utf-8'))            
            time.sleep(longDelay)

#            command = "CH" + "%02d" % final_changes[ch][0]
            cmd = list("CH" + "%02d" % final_changes[ch][0])

            for char in cmd:
                ser.write(str(char).encode('utf-8'))
                time.sleep(shortDelay)

            ser.write("\r\n".encode('ascii'))
            time.sleep(longDelay)

            print("Changing CH to " + str("%02d" % final_changes[ch][0]))

            if final_changes[ch][1] != -1: #voltage
                print("change voltage to " + str(final_changes[ch][1]))
                ser.write("c".encode('utf-8')) #change to voltage menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][1]))
                for char in cmd:
                    ser.write(str(char).encode('utf-8'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][2] != -1: #current
                print("change current to " + str(final_changes[ch][2]))
                ser.write("f".encode('utf-8')) #change to current menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][2]))
                for char in cmd:
                    ser.write(str(char).encode('utf-8'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][3] != -1: #ramp up
                print("change RUP to " + str(final_changes[ch][3]))
                ser.write("i".encode('utf-8')) #change to RUP menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][3]))
                for char in cmd:
                    ser.write(str(char).encode('utf-8'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][4] != -1: #ramp down
                print("change RDN to " + str(final_changes[ch][4]))
                ser.write("j".encode('utf-8')) #change to RUP menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][4]))
                for char in cmd:
                    ser.write(str(char).encode('utf-8'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)
                    

            if final_changes[ch][5] != -1:
                print("change trip_time to " + str(final_changes[ch][5]))
                ser.write("l".encode('utf-8')) #change to Trip Time menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][5]))
                for char in cmd:
                    ser.write(str(char).encode('utf-8'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][6] != -1:
                print("change power to " + str(final_changes[ch][6]))
                ser.write("n".encode('utf-8')) #change to Trip Time menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][6]))
                for char in cmd:
                    ser.write(str(char).encode('utf-8'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


        ser.write("1".encode('utf-8'))  
        time.sleep(longDelay)
        self.connect_button.click()#click automatically

        # start the listener thread again
        # make check button disalbed 
        # make send button disabled. 

    def kill(self):
        #put in warning message

        self.dialog = Error_Message("Warning Message", "Kill All Channels?", "Confirm you wish to turn every channel OFF and kill Listener" )
        self.dialog.exec_()

        global errorsignal
        if errorsignal == 1:
            print("OK - Kill button pressed")
            try:
                print("LAST PROCESS ID OF LISTENER ID =  " + PID)
                os.kill(int(PID), signal.SIGKILL)
                print("PROCESS ID OF LISTENER KILLED ")
            
            except ProcessLookupError:
                print("Process "  + PID + " not running ")
            
            ser.write("\x03".encode('ASCII'))  #send ctrl-c
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            
            ser.write("1".encode('utf-8'))  #top menu
            time.sleep(shortDelay)
            
            ser.write("b".encode('utf-8'))  #modify setting
            time.sleep(shortDelay)
            
            ser.write("e".encode('utf-8')) #change of global absolute
            time.sleep(shortDelay)

            ser.write("n".encode('utf-8'))  #change of status
            time.sleep(shortDelay)
            
            ser.write("n".encode('utf-8')) #type N
            time.sleep(shortDelay)
            
            ser.write("o".encode('utf-8'))  #type O
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)


            ser.write("\r\n".encode('ascii'))# press return
            time.sleep(shortDelay)
            
            ser.write("1".encode('utf-8'))  #top menu
            print("KILLED - connect to GTKTerm to quickly check this.")

            self.dialog = Error_Message("Warning Message", "GUI will now close", "HV Listener and HV GUI Need to be RESTARTED" )
            self.dialog.exec_()
            self.deleteLater()

        elif errorsignal == 0:
            print("Cancel - Not Killed")

        errorsignal = 0

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

    def change_globals(self):
        print("in change globals")
        print("updated!!!")
        V0_glo = self.V0_glo.text()
        I0_glo = self.I0_glo.text()
        RUP_glo = self.RUP_glo.text()
        RDN_glo = self.RDN_glo.text()
        trip_glo = self.trip_glo.text()

        
        if V0_glo or I0_glo or RUP_glo or RDN_glo or trip_glo != "" :
            print("A change has been made")

            #STOP LISTENER THREAD
            #change has been made go to global abs menu 
            ser.write("1".encode('utf-8'))  #top menu# TODO - add to documentation that when you first turn on (or power cycle ) the supply you will need to
# change the group to ALL and set the verify of changing a global absolute to NO.
            time.sleep(shortDelay)
           
            ser.write("b".encode('utf-8'))  #modify setting
            time.sleep(shortDelay)
          
            ser.write("e".encode('utf-8')) #change of global absolute 
            time.sleep(shortDelay)
            time.sleep(shortDelay)

            # SET ALL VOLTAGES
            if V0_glo != "" and int(V0_glo) < limits[1]:
                print("change made to voltage. New voltage is " + V0_glo)
                #send changes
                time.sleep(shortDelay)
                ser.write("c".encode('ascii')) #change of global absolute 
                time.sleep(shortDelay)
                for i in range(0,len(V0_glo)):
                    ser.write(V0_glo[i].encode('ascii'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)

            elif V0_glo != "" and int(V0_glo) > limits[1]:
                print("WARNING MESSAGE - V0 global is above V limit")
        
            #   SET ALL CURRENTS 
            if I0_glo != "" and int(I0_glo) < limits[2]:
                print("change made to Current. New current is " + I0_glo)
                time.sleep(shortDelay)
                ser.write("F".encode('ascii')) #change of global absolute 
                time.sleep(shortDelay)
                for i in range(0,len(I0_glo)):
                    ser.write(I0_glo[i].encode('ascii'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)

            elif I0_glo != "" and  int(I0_glo) > limits[2]:
                print("WARNING MESSAGE - I0 global is above I limit")


            # SET ALL RAMP UP 
            if RUP_glo != "" and int(RUP_glo) <= limits[3] and int(RUP_glo) >= 1:
                print("change made to RUP. New Ramp Up speed is " + RUP_glo)
                time.sleep(shortDelay)
                ser.write("I".encode('ascii')) #change of global absolute 
                time.sleep(shortDelay)
                for i in range(0,len(RUP_glo)):
                    ser.write(RUP_glo[i].encode('ascii'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)
                #send changes
            elif RUP_glo != "" and int(RUP_glo) > limits[3]:
                print("WARNING MESSAGE - RUP global is above RUP limit")
            elif RUP_glo != "" and int(RUP_glo) < 1:
                print("RAMP UP SPEED HAS TO BE GREATER THAN 1V/s")

            # SET ALL RAMP DOWN
            if RDN_glo != "" and int(RDN_glo) <= limits[4] and int(RDN_glo) >= 1:
                print("change made to RDN. New ramp down speed is " + RDN_glo)
                time.sleep(shortDelay)
                #send changes
                ser.write("J".encode('ascii')) #change of global absolute 
                time.sleep(shortDelay)
                for i in range(0,len(RDN_glo)):
                    ser.write(RDN_glo[i].encode('ascii'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)

            elif RDN_glo != "" and int(RDN_glo) > limits[4]:
                print("WARNING MESSAGE - RDN global is above RDN limit")
            elif RDN_glo != "" and int(RDN_glo) < 1:
                print("RAMP DOWN SPEED HAS TO BE GREATER THAN 1V/s")


            # SET ALL TRIP TIMES 
            if trip_glo != "" and int(trip_glo) <= limits[5]:
                print("change made to voltage. New trip time is " + trip_glo)
                time.sleep(shortDelay)
                ser.write("L".encode('ascii')) #change of global absolute 
                time.sleep(shortDelay)
                for i in range(0,len(trip_glo)):
                    ser.write(trip_glo[i].encode('ascii'))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)

                #send changes
            elif trip_glo != "" and int(trip_glo) > limits[5]:
                print("WARNING MESSAGE - TRIP global is above Trip Time limit")

            #end by going back to main menu
            time.sleep(shortDelay)
            ser.write("1".encode('utf-8'))  #top menu

        else:
            print("No changes made on globals screen")

        self.V0_glo.setText("")
        self.I0_glo.setText("")
        self.RUP_glo.setText("")
        self.RDN_glo.setText("")
        self.trip_glo.setText("")
        self.connect_button.click()

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
