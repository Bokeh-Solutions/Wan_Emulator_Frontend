# WAN Emulator Frontend

This script is a frontend to monitor and config a WAN Emulator made with the LINUX TC and netem to emulate conditions like Bandwidth, delay, packet loss in a link.

The Frontend was developed in python using Flask and the subprocess library, the web application is presented with Gunicorn and NGINX

The virtual machine where this should be installed should have 1 management interface and a minimum of 2 and a maximum of 10 interfaces that will create 1 to 5 bridge interfaces.

This Front End was tested only on Ubuntu 16.04 LTS Server.

Follow this steps to install it:

+ Connect to the ubuntu virtual machine via SSH or through console
+ Clone the github project with:
  ```
  cd
  sudo git clone http://github.com/mercolino/wan_emulator_frontend
  cd wan_emulator_frontend
  ```
+ Allow the installation script to execute
  ```
  sudo chmod +x install_ubuntu.sh
  ```
+ Check the name of the interfaces present on the system
  ```
  sudo ip addr show
  ```
+ Modify the installation script
  ```
  sudo vim install_ubuntu.sh
  ```

+ You can specify the installation directory, the number of bridge interfaces and the physical interfaces assigned to each bridge by modifying the variables at the beggining of the script
  + **INSTALL_DIR**: Is the installation directory that you want to use
  + **IP**: It is the management IP address, you will have to use this ip address to connect to the gui
  + **NUMBER_BRIDGES**: This is the number of bridges that you want to configure with the script, a bridge is a pair of interfaces bridging the interfaces in Layer2, meaning that every fram that goes through one interface of the bridge is going to be bridged to the second interface, that is why you need between
  + **BR#_NAME**: Name of the bridge interface
  + **BR#_IF_IN**: Is the IN interface for the Bridge interface number
  + **BR#_IF_OUT**: Is the OUT interface for the bridge interface number

+ Run the script
  ```
  sudo ./install_ubuntu.sh
  ```
+ The Frontend application should be installed by default on `/opt/wan_frontend` unless the script was changed

**_Note:_**: This script is provided as_is, no support comes with it and you are responsible to run it on your systems, if something breaks youa re the only one to blame...

