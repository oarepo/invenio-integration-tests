#!/usr/bin/env python3

import os, requests, re
from string import Template

SETUP_SRC_URL = os.environ.get('SETUP_SRC_URL')

if SETUP_SRC_URL == None: raise Exception('SETUP_SRC_URL undefined')
requests.packages.urllib3.util.connection.HAS_IPV6 = False
rq = requests.get(SETUP_SRC_URL)
data = rq.text

STATE_NONE = 0
STATE_INSTALL_REQUIRES = 1
STATE_EXTRAS_REQUIRES = 2
STATE_REMOVE = 3
STATE_EXTRAS_GROUP = 4

def process_install_requires(data):
    state = STATE_NONE
    resarr = []
    for line in data:
        if state == STATE_NONE:
            if re.match("^[ 	]+# Invenio-App-RDM$", line):
                state = STATE_REMOVE
                continue
            rr = re.match("^([ 	]+)([^# 	].+)$", line)
            if rr:
                resarr.append(rr.group(1)+"'"+rr.group(2)+"',")
            elif line != "": resarr.append(line)
        elif state == STATE_REMOVE:
            if re.match("^[ 	]+invenio-rdm-records[<>=!]", line):
                state = STATE_NONE
        else: raise Exception(f"Wrong state \"{state}\"")
    result = '\n'.join(resarr)
    return result

def process_extras_requires(data):
    resdict = {}
    ename = None
    sp = "    "
    for line in data:
        rr = re.match("^([a-zA-Z][a-zA-Z0-9]*) =", line)
        if rr:
            ename = rr.group(1)
            resdict[ename] = []
        else:
            rr = re.match("^([ 	]+)([a-zA-Z0-9].*)$", line)
            if rr:
                sp = rr.group(1)
                resdict[ename].append(f"{sp*2}'{rr.group(2)}',")
            else:
                raise Exception(f"Uncognized line \"{line}\"")
    resarr = []
    for ename in resdict.keys():
        resdict[ename].append(f"{sp*2}'jsonref<1.0.0',")
        resarr.append(f"{sp}'{ename}': [\n"+'\n'.join(resdict[ename])+f"\n{sp}],")
    result = '\n'.join(resarr)
    return result

state = STATE_NONE
buff = []
resdict = {}
for line in data.split('\n'):
    if state == STATE_NONE:
        if line == "install_requires =":
            state = STATE_INSTALL_REQUIRES
            
        elif line == "[options.extras_require]":
            state = STATE_EXTRAS_REQUIRES
            buff = []
    elif state == STATE_INSTALL_REQUIRES:
        if line != "":
            buff.append(line)
        else:
            state = STATE_NONE
            resdict['install_requires'] = process_install_requires(buff)
    elif state == STATE_EXTRAS_REQUIRES:
        if line != "":
            buff.append(line)
        else:
            state = STATE_NONE
            resdict['extras_require'] = process_extras_requires(buff)

with open('./setup.py.template') as f:
    template_str = f.read()

template = Template(template_str)
result = template.substitute(resdict)

print(result, end='')
