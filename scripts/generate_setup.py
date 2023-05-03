#!/usr/bin/env python3

import os, requests, re, sys
from string import Template

SETUP_SRC_URL_IAR = os.environ.get('SETUP_SRC_URL_IAR')
SETUP_SRC_URL_IAR_TAG = os.environ.get('SETUP_SRC_URL_IAR_TAG')
SETUP_SRC_URL_IRR = os.environ.get('SETUP_SRC_URL_IRR')

# try to fetch from version-branch URL with fallback to master-branch URL:
requests.packages.urllib3.util.connection.HAS_IPV6 = False
if SETUP_SRC_URL_IAR == None: raise Exception('SETUP_SRC_URL_IAR undefined')
rq = requests.get(SETUP_SRC_URL_IAR)
if rq.status_code == 404:
    print(f"SETUP_SRC_URL_IAR not found ({rq.status_code} on {SETUP_SRC_URL_IAR}) => using fallback ({SETUP_SRC_URL_IAR_TAG})", file=sys.stderr)
    rq = requests.get(SETUP_SRC_URL_IAR_TAG)
    rq.raise_for_status()
data = rq.text

if SETUP_SRC_URL_IRR == None: raise Exception('SETUP_SRC_URL_IRR undefined')
rq2 = requests.get(SETUP_SRC_URL_IRR)
rq2.raise_for_status()
data += rq2.text

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
    return resarr

def process_extras_requires(data):
    resdict = {}
    exname = None
    sp = "    "
    for line in data:
        rr = re.match("^([a-zA-Z][a-zA-Z0-9]*) =", line)
        if rr:
            exname = rr.group(1)
            resdict[exname] = []
        else:
            rr = re.match("^([ 	]+)([a-zA-Z0-9].*)$", line)
            if rr:
                sp = rr.group(1)
                exval = f"{sp*2}'{rr.group(2)}',".lower()
                if exval not in resdict[exname]:
                    resdict[exname].append(exval)
            else:
                raise Exception(f"Uncognized line \"{line}\"")
    return resdict

state = STATE_NONE
buff = []
resdict = {'install_requires': [], 'extras_require': {}}
for line in data.split('\n'):
    if state == STATE_NONE:
        if line == "install_requires =":
            state = STATE_INSTALL_REQUIRES
            buff = []
        elif line == "[options.extras_require]":
            state = STATE_EXTRAS_REQUIRES
            buff = []
    elif state == STATE_INSTALL_REQUIRES:
        if line != "":
            buff.append(line)
        else:
            state = STATE_NONE
            resdict['install_requires'] += process_install_requires(buff)
    elif state == STATE_EXTRAS_REQUIRES:
        if line != "":
            buff.append(line)
        else:
            state = STATE_NONE
            for exname,exval in process_extras_requires(buff).items():
                exname = exname.lower()
                if exname in resdict['extras_require']:
                    resdict['extras_require'][exname] += exval
                else:
                    resdict['extras_require'][exname] = exval

resdict['install_requires']='\n'.join(resdict['install_requires'])
sp = "    "
resarr = []
for exname, exval in resdict['extras_require'].items():
    # omit repeated exvals:
    exval = list(set(exval))
    exval.append(f"{sp*2}'flask>=2.2.5',")
    resarr.append(f"{sp}'{exname}': [\n"+'\n'.join(exval)+f"\n{sp}],")
resdict['extras_require'] = resarr
resdict['extras_require'] = '\n'.join(resdict['extras_require'])

with open('./setup.py.template') as f:
    template_str = f.read()
template = Template(template_str)
result = template.substitute(resdict)

print(result, end='')
