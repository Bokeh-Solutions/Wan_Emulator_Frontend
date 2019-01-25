#!/usr/bin/env bash

# Installation Directory
INSTALL_DIR='/opt/wanem_frontend/'
IP='10.0.2.15'
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

# Getting the Ubuntu Version
VERSION=`lsb_release --release | awk '{print $2}' | awk -F '.' '{print $1}'`

# Updating sources if Version 18
if [ $VERSION = 18 ]
then
    sed -e 's/$/ universe/' -i /etc/apt/sources.list
fi

# Update repositories and upgrade system
apt-get update
apt-get -y dist-upgrade

# Install git and python-pip
if [ $VERSION = 18 ]
then
        apt-get -y install python3-pip python3-virtualenv bridge-utils nginx gunicorn ifupdown
else
        apt-get -y install python-pip python-virtualenv bridge-utils nginx gunicorn
fi

# Creating Bridge Interfaces
echo '***** Creating Bridge Interfaces *****'
for (( i=1; i<=$NUMBER_BRIDGES; i++ ))
    do
        br_name='BR'$i'_NAME'
        br_if_in='BR'$i'_IF_IN'
        br_if_out='BR'$i'_IF_OUT'
        echo "auto ${!br_name}" >> /etc/network/interfaces
        echo "iface ${!br_name} inet manual" >> /etc/network/interfaces
        echo "bridge_ports ${!br_if_in} ${!br_if_out}" >> /etc/network/interfaces
        echo "bridge_stp off" >> /etc/network/interfaces
        echo "address $i.$i.$i.$i" >> /etc/network/interfaces
        echo "netmask 255.255.255.255" >> /etc/network/interfaces
        echo "" >> /etc/network/interfaces
    done
echo '***** Bridge Interfaces Created!!! *****'

# Enable netem Kernel Module
echo '***** Enabling Netem Kernel Module *****'
modprobe sch_netem
echo '***** Netem Kernel Module Enabled *****'

#Create Installation Directory
echo "***** Creating installation directory *****"
mkdir -p $INSTALL_DIR

# Copy content to the installation directory
cp -r . $INSTALL_DIR

# Remove installation file
rm -fr $INSTALL_DIR/install_ubuntu.sh
echo "***** Installation directory Created!!! *****"

# Create virtual environment
echo "***** Installing python dependencies *****"
if [ $VERSION = 18 ]
then
        pip3 install flask Flask-WTF
else
        pip install flask Flask-WTF
fi
echo "***** Python Dependencies Installed!!!! *****"

# Creating User
echo "***** Creating wanem_user *****"
useradd -p wanem -d /home/wanem_user -m -G www-data,sudo -s /bin/bash wanem_user
echo "***** wanem_user Created!!!*****"

# Adding wanem_user to sudoers to allow tc excution
echo "***** Adding wanem_user to sudoers to allow tc excution *****"
echo "wanem_user ALL=(root) NOPASSWD: /sbin/tc" >> /etc/sudoers
echo "***** wanem_user added to sudoers!!!!!*****"

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
User=wanem_user
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/gunicorn --pid /run/gunicorn/pid --bind unix:wanem.sock wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

systemctl start wanem
systemctl enable wanem
echo "***** System service for the application Created!!! *****"

# Configuring NGINX
echo "***** Configuring NGINX *****"
cat > /etc/nginx/sites-available/wanem <<EOF
server {
    listen 80;
    server_name $IP;

    location / {
        include proxy_params;
        proxy_pass http://unix:${INSTALL_DIR}wanem.sock;
    }
}
EOF

rm -fr /etc/nginx/sites-available/default
ln -s /etc/nginx/sites-available/wanem /etc/nginx/sites-enabled
systemctl restart nginx
echo "***** NGINX Configured*****"

# Restart Networking
echo "***** Restart networking *****"
systemctl restart networking
echo "***** Networking restarted!!! *****"