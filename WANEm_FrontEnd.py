#!/usr/bin/env python

from flask import Flask
from flask import render_template
import subprocess as sub
import re

app = Flask(__name__)


def get_interfaces():
    """
    Function to process the interfaces available on the system
    :return: if_list: Dictionary with the following format: {<if_number>:{'name':<if_name>, 'status':<if_status>}, ...}
    """
    # Initialize the interface list dictionary
    if_list = {}
    # Grab the output from the command "ip address", and split it in lines
    output = sub.check_output(['ip', 'address']).split('\n')
    # Process each linet to find the number, name and status
    for line in output:
        regex = re.search('([0-9]*):\s*(.*):\s*<.*>\s*mtu.*state\s*([A-Za-z]+)\s*group', line)
        if regex:
            # Add data to the if_list dictionary
            if_list[regex.group(1)]={'name':regex.group(2).lower(), 'status':regex.group(3).lower()}
    # Return the dictionary
    return if_list


@app.route('/config')
def config():
    active = {"status": "", "config": "bg-success"}
    return render_template('config.html', active=active)


@app.route('/')
def status():
    interfaces = get_interfaces()
    active = {"status": "bg-success", "config": ""}
    return render_template('status.html', active=active, interfaces=interfaces)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
