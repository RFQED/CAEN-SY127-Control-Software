Monitoring and Control Software for CAEN SY127 High Voltage Supply
===================
 

*A program with a graphical user interface (GUI) has been developed to monitor and control a CAEN SY127 High Voltage Supply, which is responsible for powering the Straw Tracker Modules for the Fermilab E989 $g-2$ Experiment. The GUI carries out the tasks of setting and reading all the channel settings by communicating to the high voltage supply over a serial connection. This program could provide real time plotting, trip detection and slack notifications, which enables safe, long term running.*
*The features and the setup of the GUI are discussed in details. Moreover, a simple operating manual is included.*

--- 
Will Turner, Talal Albahri and Matt Franks 

Department of Physics, University of Liverpool

----------

Introduction
------------
The CAEN SY127 High Voltage Supply - [Technical Information Manual](http://www.tunl.duke.edu/documents/public/electronics/CAEN/caen_sy127.pdf) - was designed to supply power to a variety of detectors used in High Energy Physics Experiments. The supply is composed of several separate modules: Main Controller, Communication Controller and High Voltage Channels.  There are two standard methods of changing settings on the CAEN HV supply. The first is to operate the supply manually using a numeric keypad and a 16 character LED display located on the front panel of the supply. All the relevant parameters of each channel may be displayed and modified by calling the appropriate "functions". The second method is using a built-in communication controller which provides the system with an RS232C port and a high speed serial line interface (CAENET). This in turn can be exploited by using a terminal emulator such as GTKTerm or Minicom. However, due to the limitations and time consumption of these two methods, a monitoring and control software was designed in order to allow a more sophisticated way to operate the CAEN HV supply. 

 Feature | Value
-------- | ---
HV Module| A333P/N
Voltage Full Scale | +/- 3/4kV
Current Full Scale | 2/3mA
Voltage Resolution | 1V
Current Resolution | 1 $\mu$A
OVV, UNV, Alarm | 50V
Vmax Test Point Full Scale | 2V / 1kV
Ptotal Max per board | 32W
RUP, RDWN Full Scale | 500V/sec
Ripple Max peak-peak Full Load | <80mV


The GUI is built and designed using QT Designer. This in turn can be converted to a Python source using PyQt. A main python script then utilizes the UI and PyQt source files and any necessary additional libraries to act as the main GUI program. 

----------


Features
-------------
This program was written to enable quick and easy control and monitoring of the CAEN SY127 HV Supply.  It currently allows you to - 

- View the status of all of the HV outputs on one overview screen (see picture X )
- See a full break down, module by module of all of the outputs and their corresponding settings
- Change any one of the channels settings from the GUI

Many features can be included to improve the functionality of the program such as real time plotting, trip detection and slack notifications. 

 - Real Time Plotting: The voltages for each channel can be streamed in real time to the web service **Plotly** using the python API. This allows remote monitoring as well as easy local monitoring with an interactive live updating graph.
 - Trip Detection and Slack Notifications: The data coming back over serial from the HV supply is monitored for the STATUS variable to change to TRIP. If this happens an automatic message is sent over **Slack** to a dedicated channel for straw module testing, this can be changed in the future to any channel wanting to be notified. 

----------
Setup
-----------------------

the CAEN SY127 HV supply contains a A128HS communication controller which is connected to a local machine using an RS232C serial cable. The controller also contains a permanent  memory (EEPROM) which holds the current values of the parameters of all the channels in the crate. The communication settings can be set using dip switches located on the controller which allows selecting the RS232 configuration. The settings used are: Baud Rate = 4800, Number of Bits = 8, Number of Stop bits = 1 and disabled parity. The crate number is also set via these dip switches, with the crate we are controlling via serial being crate #1 and the second supply connected via a lemo cable being crate #2. Then the local machine requires the following python packages: PyQt4, serial and for the extra features  SLACKER (Slack API), Plotly API.

The monitoring and control software is composed of three main parts; the **HV Listener**, **HV GUI** and the **config file**. 

#### HV Listener
The HV Listener controls the HV supply to retrieve all of the data from the channels listed in the **config file**.  This is then saved to a text file in the format 

```
TIME (Time in UTC) (Time Regular) (Date Regular) (HV_ENABLE Status)
(CH #) (VMon) (IMon) (V0) (V1) (I0) (I1) (RUP) (RDN) (TRIP_TIME) (STATUS)
```
for example,
```
 TIME 1473754761 09:19:21 13/09/2016 OFF
 CH00 0 0 1500 0 1 10 20 0 OFF
 CH01 0 0 1500 0 1 10 20 0 OFF
 CH02 0 0 1500 0 1 10 20 0 OFF
 CH03 0 0 1500 0 1 10 20 0 OFF
 CH04 0 0 1500 0 1 10 20 0 OFF
 CH05 0 0 1500 0 1 10 20 0 OFF
 CH06 0 0 1500 0 1 10 20 0 OFF
 CH07 0 0 1500 0 1 10 20 0 OFF
 CH08 0 0 1500 0 1 10 20 0 OFF
 CH09 0 0 1500 0 1 10 20 0 OFF
 CH10 0 0 1500 0 1 10 20 0 OFF
 CH11 0 0 1500 0 1 10 20 0 OFF
```
#### HV GUI
This is the part of the program the user will interface with, the HV GUI imports data from the HV Data File and displays it on the GUI. The GUI also allows users to change any channels setting on the HV supply, this is explained in more details later. To be able to send changes the HV GUI is required to communicate with the HV Listener to pause the listener from sending commands to the HV supply while the GUI sends changes. This is achieved by both files writing and reading to a file called canRead.txt. When the HV Listener is allowed to continue to read from the supply this file just contains 'y', when the HV Listner is required to stop talking to the supply the file contains 'n' and the HV Listener confirms that it recieved the pause command by writing 'p' to this canRead.txt file.  


#### Config.py

This Config file is a python script which is loaded into both the HV Listener and the HV GUI and contains variables specific to the users set up. For example it contains the lists the channels from each CAEN HV supply along with the channels to each tracker module. It also displays the necessary serial information for commnuication with the HV module. Another important feature in the config file are the limits set for each of the channel settings. For our use the default limits are

Setting | Limit
--------|----
Max Voltage | 1500V
Max Current | 10uA
Ramp Up | 10V/s
Ramp Down | 20V/s 
Trip Time | 0s

 This allows the user the modify the program and use the GUI according to their own setup.

------------
##How to Use
The user should first start the HV Listener either from MIDAS or running the Python script **HVListener.py** and the HV GUI **HVGUI.py**
Upon running the HV GUI Python script, the user will be presented with the following GUI window.

**PICTURE HERE ** 

The main screen of the GUI shows the status of the channels of all 8 modules in a single tracker station. All the channels and setting are viewable over multiple tabs.

The associated parameters shown for each channel on the GUI are:

  -  **VMon**: The current voltage value read by the controller, expressed in V.
  -  **IMon**: The current current value read by the controller, expressed in $\mu A$.
  -  **V0**: The voltage programmed value to ramp up to, expressed in V. The maximum limit is set to 1500V for our usage.
  -  **I0**: The current limit programmed value, expressed in $\mu A$. The maximum limit is 10$\mu A$ for our usage.
  -  **RUP**: The voltage ramp up speed, expressed in V/s.
  -  **RDW**: The voltage ramp down speed, expressed in V/s.
  -  **Trip**: The length of the trip time, which is the maximum time an "overcurrent" is allowed to last. If an overcurrent lasts more than the programmed value, from 1 to 9998 it will cause the channel to trip. The output voltage will drop to zero at the programmed ramp down rate and the channel will be put on the OFF state. If this parameter is set to 9999, the overcurrent may last indefinitely. If it is set to 0, the channel will be switched off as soon as an overcurrent is detected. The trip time is expressed in ms. This value is set to 0 for our usage. 
  -  **Status**: The status, which can be ON, OFF, TRIP, OVC, OVV, UNV.
       -  **ON**: The channel is ON.
       -  **OFF**: The channel is OFF.
       -  **TRIP**: The channel has "tripped".
       -  **OVC**: "Overcurrent", the current limit has been reached and the channel is now behaving like a constant current source.
       -  **OVV**: "Overvoltage", the actual value of the high voltage output is higher than the programmed value.
       -  **UNV**: "Undervoltage", the actual value of the high voltage is lower than the programmed value.
  - **Ramp**: The ramp status, which can be RUP or RDW (or blank).


####To modify the parameters for each channel
As mentioned above the GUI allows for fast, easy and most importantly safe updating of channel settings on the HV module. To change a setting -

   -  Select the tab of interest.
   -  Press the **Stop Listener** button to disable the monitoring.
   -  Turn On/Off the power of the wanted channel(s) using the tick boxes down the left hand side and change setting by using the text boxes below each setting.
   -  Confirm the changes by pressing the **Check Changes** button, which checks the values entered are below the allowable limit. If they are, then the settings will be sent to **Send Changes**. If the values are outside of the allowable range then a warning pop-up window will be displayed and these changes will **NOT** be sent to the send changes function. This prevents the user from entering in an incorrect value by error. *IF the user did want to change a setting beyond the limits set then they would need to edit the config file manually and restart the GUI. *
 
** picture of pop up window **
    
  -  Press **Send Changes** to forward the confirmed changes to the HV supply over the serial connection.
  -  Once all the changes have been made, the Listener program will resume automatically and after a few seconds the changes made should load into the GUI. The is also confirmed by the **Time Since Last Update** label.

Moreover, there is a debug output window which can be viewed by pressing the expansion button - see figure 3. This will expand the GUI window and display the debug window with an updated readings of the monitored parameters.

####Safety Features
As mentioned previously, the program checks the values of the changed settings are within the allowable range before confirming the changes. If the values are outside the allowable range then a warning pop-up window is displayed and these values will not be allowed to be sent to the supply. Moreover a **KILL** button *will be * implemented to allow automatic disabling the HV in case of any safety issues.

The user should also keep in mind the following safety and operating suggestions:

  - Observe that the air flow within the HV supply is sufficient to prevent overheating and fires.
  -  Be aware that if the "Time since update" field on the GUI displays a time larger than ~2mins then the HV Listner script may have closed unexpectedly and the values you are seeing displayed will not update.
  -  Never connect any channel to any output while the HV is enabled.
  -  Be sure that the RS232 serial cable is properly connected to the crate.
  -  Never insert or remove any HV modules while HV ENABLE is ON.
  -  Always make sure that the HV modules are fixed to their crates using screws.



####Future
 The HV Listener can be also be started from **MIDAS** and notifies MIDAS of any errors or tripping. 

####TODO
Include a way to auto rectify a trip 
