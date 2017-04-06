# KILL BUTTON

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
            
            ser.write("1")  #top menu
            time.sleep(shortDelay)
            
            ser.write("b")  #modify setting
            time.sleep(shortDelay)
            
            ser.write("e") #change of global absolute
            time.sleep(shortDelay)

            ser.write("n")  #change of status
            time.sleep(shortDelay)
            
            ser.write("n") #type N
            time.sleep(shortDelay)
            
            ser.write("o")  #type O
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)
            time.sleep(shortDelay)


            ser.write("\r\n".encode('ascii'))# press return
            time.sleep(shortDelay)
            
            ser.write("1")  #top menu
            print("KILLED - connect to GTKTerm to quickly check this.")

            self.dialog = Error_Message("Warning Message", "GUI will now close", "HV Listener and HV GUI Need to be RESTARTED" )
            self.dialog.exec_()
            self.deleteLater()

        elif errorsignal == 0:
            print("Cancel - Not Killed")

        errorsignal = 0






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
            ser.write("1")  #top menu# TODO - add to documentation that when you first turn on (or power cycle ) the supply you will need to
# change the group to ALL and set the verify of changing a global absolute to NO.
            time.sleep(shortDelay)
           
            ser.write("b")  #modify setting
            time.sleep(shortDelay)
          
            ser.write("e") #change of global absolute 
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
            ser.write("1")  #top menu

        else:
            print("No changes made on globals screen")

        self.V0_glo.setText("")
        self.I0_glo.setText("")
        self.RUP_glo.setText("")
        self.RDN_glo.setText("")
        self.trip_glo.setText("")
        self.connect_button.click()










############ SEND BUTTON


    def send(self): 
        print("in send func got changes " + str(final_changes))
        #in send fucntion get access to final_changes
        #these are checked values and are only changes
        for ch, chan in enumerate(final_changes):
            if ch in cr2Chs:
                print("changing to crate 2")
                #change to other crate. have to think about different ch numbers on other crate. 


            time.sleep(shortDelay)

            ser.write("1")  
            time.sleep(shortDelay)

            ser.write("1".encode('utf-8'))  
            time.sleep(shortDelay)

            ser.write("b")            
            time.sleep(longDelay)

            ser.write("a")            
            time.sleep(longDelay)

            print("Chaning Values of CH " + str("%02d" % final_changes[ch][0]))
            ser.write("a")            
            time.sleep(longDelay)

#            command = "CH" + "%02d" % final_changes[ch][0]
            cmd = list("CH" + "%02d" % final_changes[ch][0])

            for char in cmd:
                ser.write(str(char))
                time.sleep(shortDelay)

            ser.write("\r\n".encode('ascii'))
            time.sleep(longDelay)

            print("Changing CH to " + str("%02d" % final_changes[ch][0]))

            if final_changes[ch][1] != -1: #voltage
                print("change voltage to " + str(final_changes[ch][1]))
                ser.write("c") #change to voltage menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][1]))
                for char in cmd:
                    ser.write(str(char))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][2] != -1: #current
                print("change current to " + str(final_changes[ch][2]))
                ser.write("f") #change to current menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][2]))
                for char in cmd:
                    ser.write(str(char))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][3] != -1: #ramp up
                print("change RUP to " + str(final_changes[ch][3]))
                ser.write("i") #change to RUP menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][3]))
                for char in cmd:
                    ser.write(str(char))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][4] != -1: #ramp down
                print("change RDN to " + str(final_changes[ch][4]))
                ser.write("j") #change to RUP menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][4]))
                for char in cmd:
                    ser.write(str(char))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)
                    

            if final_changes[ch][5] != -1:
                print("change trip_time to " + str(final_changes[ch][5]))
                ser.write("l") #change to Trip Time menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][5]))
                for char in cmd:
                    ser.write(str(char))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


            if final_changes[ch][6] != -1:
                print("change power to " + str(final_changes[ch][6]))
                ser.write("n") #change to Trip Time menu
                time.sleep(longDelay)
                cmd = list(str(final_changes[ch][6]))
                for char in cmd:
                    ser.write(str(char))
                    time.sleep(shortDelay)
                ser.write("\r\n".encode('ascii'))
                time.sleep(shortDelay)


        ser.write("1")  
        time.sleep(longDelay)
        self.connect_button.click()#click automatically

        # start the listener thread again
        # make check button disalbed 
        # make send button disabled. 

