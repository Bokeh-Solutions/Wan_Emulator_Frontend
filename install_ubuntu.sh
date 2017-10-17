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
apt-get -y install python-pip bridge-utils gunicorn nginx

# Install pip
pip install Flask

# Creating Bridge Interfaces
for (( i=1; i<=$NUMBER_BRIDGES; i++ ))
do
    br_name='BR'$i'_NAME'
    br_if_in='BR'$i'_IF_IN'
    br_if_out='BR'$i'_IF_OUT'
    brctl addbr ${!br_name}
    brctl addif ${!br_name} ${!br_if_in}
    brctl addif ${!br_name} ${!br_if_out}
done

#Create Installation Directory
mkdir -p $INSTALL_DIR

# Copy content to the installation directory
cp -r . $INSTALL_DIR

