#!/usr/bin/env bash

# Installation Directory
INSTALL_DIR='/opt/wanem_frontend/'
MGMT_IF='enp0s3'
NUMBER_BRIDGES=5
# Bridge 1
BR1_NAME='br0'
BR1_IF_IN='enp0s8'
BR1_IF_OUT='enp0s9'
# Bridge 2
BR2_NAME='br1'
BR2_IF_IN='enp0s8'
BR2_IF_OUT='enp0s9'
# Bridge 3
BR3_NAME='br2'
BR3_IF_IN='enp0s8'
BR3_IF_OUT='enp0s9'
# Bridge 4
BR4_NAME='br3'
BR4_IF_IN='enp0s8'
BR4_IF_OUT='enp0s9'
# Bridge 5
BR5_NAME='br4'
BR5_IF_IN='enp0s8'
BR5_IF_OUT='enp0s9'

# Update repositories and upgrade system
apt-get update
apt-get -y dist-upgrade

# Install git and python-pip
apt-get -y install python-pip python-virtualenv bridge-utils nginx

# Creating Bridge Interfaces
echo '***** Creating Bridge Interfaces *****'
for (( i=1; i<=$NUMBER_BRIDGES; i++ ))
do
    br_name='BR'$i'_NAME'
    br_if_in='BR'$i'_IF_IN'
    br_if_out='BR'$i'_IF_OUT'
    brctl addbr ${!br_name}
    brctl addif ${!br_name} ${!br_if_in}
    brctl addif ${!br_name} ${!br_if_out}
done
echo '***** Bridge Interfaces Created!!! *****'

#Create Installation Directory
echo "***** Creating installation directory *****"
mkdir -p $INSTALL_DIR

# Copy content to the installation directory
cp -r . $INSTALL_DIR

# Remove installation file
rm -fr $INSTALL_DIR/install_ubuntu.sh
echo "***** Installation directory Created!!! *****"

#Create virtual environment
echo "***** Installing gunicorn and flask *****"
pip install flask gunicorn
echo "***** Gunicorn and Flask Installed!!!! *****"

#Creating User
echo "***** Creating wanem_user *****"
useradd -p wanem -d /home/wanem_user -m -G www-data,sudo -s /bin/bash wan_user
echo "***** wanem_user Created!!!*****"

#Changing perimssions to the directory
echo "***** Changing Permissions to the Installation directory *****"
chown -R wanem_user:www-data $INSTALL_DIR
echo "***** Permissions to the Installation directory changed !!!*****"

#Create service for automatic bootup
echo "***** Creating system service for the application *****"
cat > /etc/systemd/system/wanem.service << EOF
[Unit]
Description=Gunicorn instance to serve the Wan Emulator FrontEnd
After=network.target

[Service]
PIDFile=/run/gunicorn/pid
User=mercolino
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/gunicorn --pid /run/gunicorn/pid   \
          --bind unix:test.sock wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
echo "***** System service for the application Created!!! *****"
