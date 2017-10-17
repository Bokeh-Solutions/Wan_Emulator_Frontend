# WAN Emulator Frontend

This script is a frontend to monitor and config a WAN Emulator made with the LINUX TC and netem to emulate conditions like Bandwidth, delay, packet loss in a link.

The Frontend was developed in python using Flask and the subprocess library, the web application is presented with Gunicorn and NGINX

The virtual machine where this should be installed should have 1 management interface and a minimum of 2 and a maximum of 10 interfaces that will create 1 to 5 bridge interfaces.

This Front End was tested only on Ubuntu 16.04 LTS.

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
  + Modify the installation script
  ```
  sudo vim install_ubuntu.sh
  ```
  + You can specify the installation directory, the number of bridge interfaces and the physical interfaces assigned to each bridge
  + Run the script
  ```
  sudo ./install_ubuntu.sh
  ```
  + The Frontend application should be installed by default on `/opt/wan_frontend` unless the script was changed

**_Note:_**: This script is provided as_is, no support comes with it and you are responsible to run it on your systems, if something breaks youa re the only one to blame...

