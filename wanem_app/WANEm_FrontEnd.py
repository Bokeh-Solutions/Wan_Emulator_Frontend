#!/usr/bin/env python

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField, SelectField
from wtforms.validators import InputRequired, Optional, ValidationError
import subprocess as sub
import re
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


class Bridge_Config_Form(FlaskForm):
    InputBwLimit = IntegerField('Bandwidth Rate (kbps)', validators=[Optional()])
    InputBwBurst = IntegerField('Bandwidth Burst (bytes)', validators=[Optional()])
    InputMeanDelay = IntegerField('Mean Delay (ms)', validators=[Optional()])
    InputStdDev = IntegerField('Standard Deviation (ms)', validators=[Optional()])
    InputDelayCorrelation = IntegerField('Delay Correlation (%)', validators=[Optional()])
    InputDelayDistribution = SelectField('Delay Distribution', choices=[('normal', 'Normal'),('pareto', 'Pareto'),('paretonormal', 'Pareto Normal')],
                                         default='Normal')
    InputPktLoss = DecimalField('Packet Loss (%)', validators=[Optional()])
    InputPktLossCorrelation = IntegerField('Packet Loss Correlation (%)', validators=[Optional()])

    def validate(self):
        if not super(Bridge_Config_Form, self).validate():
            return False

        if self.InputBwLimit.data is not None:
            if not self.InputBwLimit.data > 0:
                self.InputBwLimit.errors.append('Rate limit should be greater than 0 kbps')
                return False
        if self.InputBwLimit.data is not None and self.InputBwBurst.data is None:
            self.InputBwBurst.errors.append('Burst Should be specified')
            return False
        if self.InputMeanDelay.data is not None:
            if not self.InputMeanDelay.data > 0:
                self.InputMeanDelay.errors.append('Delay should be greater than 0 ms')
                return False
        if self.InputMeanDelay.data is not None and not self.InputStdDev.data >= 1:
            self.InputStdDev.errors.append('Standard Deviation should be at least 1ms')
            return False
        if self.InputStdDev.data > self.InputMeanDelay.data:
            self.InputStdDev.errors.append('Standard Deviation should be less than the delay')
            return False
        if self.InputDelayCorrelation.data is not None:
            if not self.InputDelayCorrelation.data > 0:
                self.InputDelayCorrelation.errors.append('Delay Correlation should be greater than 0%')
                return False
        if self.InputPktLossCorrelation.data is not None:
            if not self.InputPktLossCorrelation.data > 0:
                self.InputPktLossCorrelation.errors.append('Loss Correlation should be greater than 0%')
                return False
        if self.InputBwLimit.data is None and self.InputBwBurst.data is not None:
            self.InputBwBurst.errors.append("Can't specify burst without limit")
            return False
        if self.InputMeanDelay.data is None and self.InputStdDev.data is not None:
            self.InputStdDev.errors.append("Can't specify std deviation without delay")
            return False
        if self.InputPktLoss.data is None and self.InputPktLossCorrelation.data is not None:
            self.InputStdDev.errors.append("Can't specify loss correlation without packet loss")
            return False
        return True


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
    # Grab the output from the command "ip address", and split it in lines
    output = sub.check_output(['ip', 'address']).split('\n')
    # Process each line to find the number, name and status, create also a dictionary with the rest of the info to extract ip address
    for line in output:
        regex = re.search('([0-9]*):\s*(.*):\s*<.*>\s*mtu.*state\s*([A-Za-z]+)\s*group', line)
        if regex:
            i = int(regex.group(1))
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
    bridges = get_bridges()
    iface_in = bridges[int(br[-1])]['interface_in']
    iface_out = bridges[int(br[-1])]['interface_out']
    form = Bridge_Config_Form(request.form)
    if request.method == 'POST':
        InputBwLimit = request.form['InputBwLimit']
        InputBwBurst = request.form['InputBwBurst']
        InputMeanDelay = request.form['InputMeanDelay']
        InputStdDev = request.form['InputStdDev']
        InputDelayCorrelation = request.form['InputDelayCorrelation']
        InputDelayDistribution = request.form['InputDelayDistribution']
        InputPktLoss = request.form['InputPktLoss']
        InputPktLossCorrelation = request.form['InputPktLossCorrelation']
        if form.validate_on_submit():
            sub.call('sudo tc qdisc del dev ' + iface_in + ' root', shell=True)
            sub.call('sudo tc qdisc del dev ' + iface_out + ' root', shell=True)
            if InputBwLimit:
                sub.call(
                    'sudo tc qdisc add dev ' + iface_in + ' root handle 1:0 tbf rate ' + InputBwLimit + 'kbit buffer ' +
                    InputBwBurst + ' latency 2000',shell=True)
                sub.call(
                    'sudo tc qdisc add dev ' + iface_out + ' root handle 1:0 tbf rate ' + InputBwLimit + 'kbit buffer ' +
                    InputBwBurst + ' latency 2000', shell=True)
                if InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation <> '' and InputPktLossCorrelation <> '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                         '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation <> '' and InputPktLossCorrelation == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation == '' and InputPktLossCorrelation <> '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                         '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation == '' and InputPktLossCorrelation == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay == '' and InputPktLoss <> '' and InputPktLossCorrelation <> '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '%',shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '%', shell=True)
                elif InputMeanDelay == '' and InputPktLoss <> '' and InputPktLossCorrelation == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ',shell=True)
                    sub.call('sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem loss ' + str(int(InputPktLoss)/2) + '% ',
                             shell=True)
                elif InputMeanDelay <> '' and InputDelayCorrelation <> '' and InputPktLoss == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                             'ms ' + InputDelayCorrelation  + '% ' + 'distribution ' + InputDelayDistribution, shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                        'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution, shell=True)
                elif InputMeanDelay <> '' and InputDelayCorrelation == '' and InputPktLoss == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' parent 1:0 netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                             'ms ' + 'distribution ' + InputDelayDistribution, shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' parent 1:0 netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                        'ms ' + 'distribution ' + InputDelayDistribution, shell=True)
                return redirect('/config')
            else:
                if InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation <> '' and InputPktLossCorrelation <> '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                         '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation <> '' and InputPktLossCorrelation == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' root netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation == '' and InputPktLossCorrelation <> '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                         '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) + 'ms ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay <> '' and InputPktLoss <> '' and InputDelayCorrelation == '' and InputPktLossCorrelation == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + InputStdDev + 'ms ' + 'distribution ' + InputDelayDistribution,
                         shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' root netem loss ' + str(int(InputPktLoss)/2) + '% delay ' + str(int(InputMeanDelay)/2) + 'ms ' + InputStdDev + 'ms ' + 'distribution ' + InputDelayDistribution,
                        shell=True)
                elif InputMeanDelay == '' and InputPktLoss <> '' and InputPktLossCorrelation <> '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '%',shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ' + InputPktLossCorrelation +
                        '%', shell=True)
                elif InputMeanDelay == '' and InputPktLoss <> '' and InputPktLossCorrelation == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ',shell=True)
                    sub.call('sudo tc qdisc add dev ' + iface_out + ' root netem loss ' + str(int(InputPktLoss)/2) + '% ',
                             shell=True)
                elif InputMeanDelay <> '' and InputDelayCorrelation <> '' and InputPktLoss == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                             'ms ' + InputDelayCorrelation  + '% ' + 'distribution ' + InputDelayDistribution, shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_in + ' root netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                        'ms ' + InputDelayCorrelation + '% ' + 'distribution ' + InputDelayDistribution, shell=True)
                elif InputMeanDelay <> '' and InputDelayCorrelation == '' and InputPktLoss == '':
                    sub.call('sudo tc qdisc add dev ' + iface_in + ' root netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                             'ms ' + 'distribution ' + InputDelayDistribution, shell=True)
                    sub.call(
                        'sudo tc qdisc add dev ' + iface_out + ' root netem delay ' + str(int(InputMeanDelay)/2) + 'ms ' + str(int(InputStdDev)/2) +
                        'ms ' + 'distribution ' + InputDelayDistribution, shell=True)
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
    app.run(host='0.0.0.0')
