#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField
from wtforms.validators import InputRequired
import subprocess as sub
import re

app = Flask(__name__)


class Bridge_Config_Form(FlaskForm):
    InputMeanDelay = IntegerField('Mean Delay (ms)', validators=[InputRequired()])
    InputStdDev = IntegerField('Standard Deviation (ms)', validators=[InputRequired()])
    InputDelayCorrelation = IntegerField('Delay Correlation (%)', validators=[InputRequired()])
    InputPktLoss = DecimalField('Packet Loss (%)', validators=[InputRequired()])
    InputPktLossCorrelation = IntegerField('Packet Loss Correlation (%)', validators=[InputRequired()])


def get_tc_status():
    """
    Fucntion to return the TC status
    :return: List with all the lines of the output of the command
    """
    output = sub.check_output(['tc', 'qdisc']).split('\n')
    return output


def get_bridges():
    """
    Function to return the bridges and associations
    :return: Dictionary with the following format: {'<#>':{'name':<br_name>, 'interface_in':<if_in>, 'interface_out':<if_out>}, ...}
    """
    br_list={}
    i = 0
    # Grab the output from the command "brctl show", and split it in lines
    output = sub.check_output(['brctl', 'show']).split('\n')
    for c in range(0,len(output)):
        regex1 = re.search('(br[0-9]+).*(en.+)', output[c])
        if regex1:
            br_list[i] = {'name':regex1.group(1), 'interface_in':regex1.group(2)}
            regex2 = re.search('.+(en.+)', output[c+1])
            if regex2:
                br_list[i]['interface_out'] = regex2.group(1)
            i +=1
    return br_list


def get_interfaces():
    """
    Function to process the interfaces available on the system
    :return: if_list: Dictionary with the following format: {'<if_number>':{'name':<if_name>, 'status':<if_status>, 'ip_addr':<if_ip_address>}, ...}
    """
    # Initialize the interface list dictionary
    if_list = {}
    if_group = {}
    i = 0
    # Grab the output from the command "ip address", and split it in lines
    output = sub.check_output(['ip', 'address']).split('\n')
    # Process each line to find the number, name and status, create also a dictionary with the rest of the info to extract ip address
    for line in output:
        regex = re.search('([0-9]*):\s*(.*):\s*<.*>\s*mtu.*state\s*([A-Za-z]+)\s*group', line)
        if regex:
            i += 1
            # Add data to the if_list dictionary
            if_list[int(regex.group(1))]={'name':regex.group(2).lower(), 'status':regex.group(3).lower()}
            if_group[i]=[line]
        else:
            if_group[i].append(line)

    # Process other dictionary to grab ip address from interface
    for key in if_group:
        for value in if_group[key]:
            regex = re.search('.*inet +([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\/[0-9]+) +', value)
            if regex:
                if_list[key]['ip_addr'] = regex.group(1)

    # Return the dictionary
    return if_list


@app.route('/config_br/<br>', methods=['GET', 'POST'])
def config_br(br):
    form = Bridge_Config_Form(request.form)
    if request.method == 'POST':
        print form.errors
        InputMeanDelay = request.form['InputMeanDelay']
        InputStdDev = request.form['InputStdDev']
        InputDelayCorrelation = request.form['InputDelayCorrelation']
        InputPktLoss = request.form['InputPktLoss']
        InputPktLossCorrelation = request.form['InputPktLossCorrelation']
        print InputMeanDelay
        print InputStdDev
        print InputDelayCorrelation
        print InputPktLoss
        print InputPktLossCorrelation
        if form.validate_on_submit():
            sub.call('sudo tc qdisc del dev ' + br + ' root', shell=True)
            if InputMeanDelay <> 0 and InputPktLoss <> 0:
                sub.call('sudo tc qdisc add dev ' + br + ' root netem loss ' + InputPktLoss + '% ' + InputPktLossCorrelation +
                     '% delay ' + InputMeanDelay + 'ms ' + InputStdDev + 'ms ' + InputDelayCorrelation + '%',
                     shell=True)
            elif InputMeanDelay == 0 and InputPktLoss <> 0:
                sub.call('sudo tc qdisc add dev ' + br + ' root netem loss ' + InputPktLoss + '% ' + InputPktLossCorrelation +
                    '%',shell=True)
            elif InputMeanDelay <> 0 and InputPktLoss == 0:
                sub.call('sudo tc qdisc add dev ' + br + ' root netem delay ' + InputMeanDelay + 'ms ' + InputStdDev +
                         'ms ' + InputDelayCorrelation + '%',shell=True)
            return redirect('/config')

    active = {"status": "", "config": "bg-success", "title": "Config " + br}
    return render_template('config_bridge.html', active=active, bridge=br, form=form)


@app.route('/config')
def config():
    bridges = get_bridges()
    active = {"status": "", "config": "bg-success", "title":"Config"}
    return render_template('config.html', active=active, bridges=bridges)


@app.route('/')
def status():
    interfaces = get_interfaces()
    bridges = get_bridges()
    tc_status = get_tc_status()
    active = {"status": "bg-success", "config": "", "title":"Status"}
    return render_template('status.html', active=active, interfaces=interfaces, bridges=bridges, tc_status=tc_status)


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'development'
    app.run(host='0.0.0.0')
