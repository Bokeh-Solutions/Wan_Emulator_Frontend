#!/usr/bin/env bash

# Installation Directory
INSTALL_DIR='/opt/wanem_frontend/'

# Update repositories and upgrade system
apt-get update
apt-get -y dist-upgrade

# Install git and python-pip
apt-get -y git python-pip

# Install pip
pip install Flask

mkdir $INSTALL_DIR

