# This script connects to the HV supply using the settings in the config file
# and saves the data from each channel to a text file. Refreshes supply values 
# and loops over all channels/crates available (writen in config). 

import os
import sys
import time
import serial # so we can talk over serial
from config import *

ser = serial.Serial(serial_addr, baud_rate, timeout=3)
ser.setDTR(False) #needed to keep data coming over serial without timeout     
pPressed = 0 #this stores the amount of times p has been pressed on one supply. 
    # each display Params window can hold 10CH values. each crate can hold 40CH's
    # so once pPressed = 4 (MAX) and if there are still channels not read from, need to change
    # crate to #2. CRATE#1 may not be full, more realistically, if CRATE#1 has 24CHs, the config 
    # will have this written down 

numChsTotal = len(allChs)
numCr1Chs = len(cr1Chs)
numCr2Chs = len(cr2Chs)

#####Checking CH Nums in Config######

if len(cr1Chs) == 0:
    print("No channels present for Crate#1 in config.py")
elif (len(cr1Chs) < cr1Chs[-1]+1):
    print("Length of channel list in Crate#1 is shorter than the last channel number present, you have a channel missing from the config.")
if len(cr2Chs) == 0:
    print("No channels present for Crate#2 in config.py")
elif (len(cr2Chs) < cr2Chs[-1]+1):
    print("Length of channel list in Crate#2 is shorter than the last channel number present, you have a channel missing from the config.")

print("Total Num of CHs in config " + str(numChsTotal) + " with " + str(numCr1Chs) + " in Crate#1 and " + str(numCr2Chs) + " in Crate#2")
######################################


while True:
    with open(can_Read_File, 'r', os.O_NONBLOCK) as f:
        line = f.readline()
        line = line.rstrip('\n') #logic for blocking reading while GUI is sending changes 

        if line == "y": #can read
            can_Read = True 
        if line == "n": #cant read and paused not acknowledged
            can_Read = False
            confirmPaused = False
        if line == "p":#cant read and paused acknowledged
            can_Read = False
            confirmPaused = True
    
    if can_Read == False and confirmPaused == False:
        try:
            with open(can_Read_File, 'w', os.O_NONBLOCK) as f:
                f.write("p")
        except IOError:
            print("Can not write to can_read_file")
        
    if can_Read == True:
        try:
            output_file = open(output_file_name, 'a', os.O_NONBLOCK) #none blocking so can write in one file and read from another
        except IOError:
            print("Can not open HV Data file to save to")
   	
        ser.write("1".encode('ASCII')) #make sure supply is on top menu
        ser.read(9000).decode() #if you dont do something with the serial data waiting on the line it will stay there

        time.sleep(shortDelay)

        ser.write("1".encode('ASCII')) #make sure supply is on top menu
        ser.read(9000).decode() #if you dont do something with the serial data waiting on the line it will stay there

        time.sleep(shortDelay)
   	
        ser.write("A".encode('ASCII')) #change to the display params window
        ser.read(9192).decode() #if you dont do something with the serial data waiting on the line it will stay there
   	 #time.sleep(shortDelay)
        ser.write("o".encode('utf-8')) #refresh params       
   	 #put try catch around this
        serialInput = ser.read(8192).decode().strip().split('\n') # read 8192 bytes or until timeout (set to 3)
   	
        HV_ENABLE = serialInput[22].split(" ")
        try:
            HV_ENABLE_val = HV_ENABLE[26].strip('\r')
        except IndexError:
            print("Can't find HV_ENABLE in data coming back")

        if HV_ENABLE_val not in ["ON","OFF"]:
            print("HV ENABLE STRING NOT FOUND")
         
        for i in range(0,26):
            serialInput.pop(0) #kills the formatting lines
             
        serialInput.pop()#kills the escape sequence chars (not checked this after changing pop(10) to pop() which gets last entry. 
   	
        print("HV ENABLE IS " + str(HV_ENABLE_val))

        serialDataTemp=[]
        serialDataTmp=[]
        HVData=[]
   	 
        for i in range(0,10):
            serialDataTemp.append(serialInput[i].split(' '))
            serialDataTmp.append([j for j in serialDataTemp[i] if j != ''])#strips empty ,'', from channel vars
            HVData.append([j for j in serialDataTmp[i] if j != '\r'])#strips ,'\r', from channel vars list
   	     
        for i in range(0,len(HVData)):
            print("CH" + str(i) + " is  -  " +  str(HVData[i]))
   	         
   	     #now here we see if the number of elements (channels) in HVData is = number of channels present.
   	     #if not we press 'p' to go to the next page then there should be number of chans - 9 on this page. 
   	         
        print("Number of channels is " + str(numChsTotal) + ". and Lenght of HVData " + str(len(HVData)))
   	
        while numCr1Chs > len(HVData): #if number of channels in config is > num of channels read, press p to go to next page of channels
            print("in while numCr1Chs > HVDATA -- Number of channels is " + str(numCr1Chs) + ". and Lenght of HVData " + str(len(HVData)))
   	
   	     #and get the data from these ones too, save these to end of the HVData list. 
            print("Num of channels is greater than the amount in Serial Data. Pressing P")
            ser.write("p".encode('utf-8')) #go to next page of channels  
            serialInput_P = ser.read(8192).decode().strip().split('\n') # read 8192 bytes or until timeout (set to 3)
   	     
            for i in range(0,26):
                serialInput_P.pop(0) #kills the formatting lines
   	
            serialInput_P.pop()#kills the escape sequence chars (not checked this after changing pop(10) to pop() which gets last entry. 
   	
            serialDataTemp_P=[]
            serialDataTmp_P=[]
   	     
            for i in range(0,len(serialInput_P)):
                serialDataTemp_P.append(serialInput_P[i].split(' '))
                serialDataTmp_P.append([j for j in serialDataTemp_P[i] if j != ''])#strips empty ,'', from channel vars
                HVData.append([j for j in serialDataTmp_P[i] if j != '\r'])#strips ,'\r', from channel vars list
   	     
            for i in range(0,len(HVData)):
                print(str(HVData[i]))
            print("end of loop")
   	                    
            #done with extra channels pressing p (should have check to see if got all channels yet)
   	     
        print("number of channels is " + str(numChsTotal) + " and number of channels we have read is " + str(len(HVData)))    
   	
        del serialDataTemp[:]
        del serialDataTmp[:]
   	
        if (len(cr2Chs) != 0):
            while numChsTotal >=  len(HVData): #if we have missing cards this may become a problem
                                                # or if we have cards present but not used and future cards in place that are used.
                print("There are some channels in create #2 also")
                ser.write("1".encode('utf-8')) #go to the main menu
                print(ser.read(9000).decode()) #if you dont do something with the serial data waiting on the line it will stay there
   	
                ser.write("i".encode('utf-8')) #go to crate number menu
                ser.read(9000).decode() #if you dont do something with the serial data waiting on the line it will stay there
   	
                ser.write("1".encode('utf-8')) #go to crate number 2   #CHANGE THIS TO TWO WHEN WE HAVE ANOTHER CRATE CONNECTED
                ser.read(9000).decode() #if you dont do something with the serial data waiting on the line it will stay there
                
                ser.write("A".encode('utf-8')) #display params
                ser.read(9000).decode() #if you dont do something with the serial data waiting on the line it will stay there
   	
                serialInput = ser.read(8192).decode().strip().split('\n') # read 8192 bytes or until timeout (set to 3)
   	    
                for i in range(0,26):
                    serialInput.pop(0) #kills the formatting lines
   	             
                    serialInput.pop()#kills the escape sequence chars (not checked this after changing pop(10) to pop() which gets last entry. 
   	
                    serialDataTemp=[]
                    serialDataTmp=[]
                    HVData=[]
   	         
                for i in range(0,10):
                    serialDataTemp.append(serialInput[i].split(' '))
                    serialDataTmp.append([j for j in serialDataTemp[i] if j != ''])#strips empty ,'', from channel vars
                    HVData.append([j for j in serialDataTmp[i] if j != '\r'])#strips ,'\r', from channel vars list
   	
   	
        if numChsTotal <= len(HVData):
            print("got all the channels data")
            currentTimeOnly = time.strftime("%H:%M:%S")
            currentDateOnly = time.strftime("%d/%m/%Y")

            currentUTC      = int(time.time())
            datetime = currentTimeOnly + " " + currentDateOnly
            opStr = "TIME %d %s %s" % (currentUTC,datetime,str(HV_ENABLE_val))  
            output_file.write(opStr+ "\n")
   	     
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
   	
        del serialDataTemp[:]
        del serialDataTmp[:]
        del HVData[:]
        del serialInput[:]
   	 
   	
        print("done reading")
        output_file.flush()

    if can_Read == False:
        print("Cant read right now")
        time.sleep(5)

'''
        ['CH00', '0', '0', '0', '0', '1', '1', '10', '20', '0', 'OFF'] Ramp Status (optional)
HVData    [0]  , [1], [2], [3], [4], [5], [6],  [7],  [8], [9],  [10], [11]
'''
