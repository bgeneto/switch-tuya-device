#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ping-watchdog.py
#
# Purpose: reboot the machine if pinging host failed
#
# Copyright (c) 2021 by bgeneto <b g e n e t o at g m a i l  dot c o m>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "bgeneto"
__maintainer__ = "bgeneto"
__contact__ = "b g e n e t o  at g m a i l"
__copyright__ = "Copyright 2021, bgeneto"
__license__ = "GPLv3"
__status__ = "Development"
__date__ = "2022/04/04"
__version__ = "1.0.2"

import argparse
import json
import os
from posixpath import expanduser
import sys
import time
import tinytuya
from datetime import datetime

errors = {
    "dev_not_found": 1,
    "cmd_unknown": 2,
    "cmd_error": 3,
    "file_not_found": 4,
    "json_parse_error": 5
}


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def script_full_path():
    '''
    Return the full path of this script
    '''
    script_dir = os.path.dirname(sys.argv[0])
    if script_dir == '':
        script_dir = '.'
    script_path = os.path.abspath(script_dir)
    return script_path


def set_cmd_args():
    # command line args setup
    parser = argparse.ArgumentParser(
        description="Turn on/off tuya power plug devices")

    # define args
    #parser.add_argument('-d', '--dev', help='device name, id, ip or mac', required=True)
    parser.add_argument(
        'dev', help='device name, id, ip or mac')
    parser.add_argument(
        'cmd', help='command to issue (on or off)')
    parser.add_argument(
        '-f', '--file', default='tuya-devices.json', help='input json file containing devices list')
    parser.add_argument(
        '-d', '--delay', default=0, help='delay (in seconds) before sending the command')
    args = parser.parse_args()

    return args


def get_device(devices, val):
    for dev in devices:
        for key in dev:
            if dev[key].lower() == val.lower():
                return dev

    eprint("device not found")
    sys.exit(errors["dev_not_found"])


def read_devices(fn):
    obj = None
    if not fn:
        fn = "tuya-devices.json"
    if os.path.isfile(fn):
        try:
            with open(fn) as file:
                obj = json.load(file)
        except:
            eprint("error parsing json file (%s)" % fn)
            sys.exit(errors["json_parse_error"])
    else:
        eprint("devices json file (%s) not found" % fn)
        sys.exit(errors["file_not_found"])

    return obj


def main():
    # setup command line arguments
    args = set_cmd_args()

    # read tuya devices from json file
    input_file = os.path.join(script_full_path(), args.file)
    devices = read_devices(input_file)

    # set command delay
    cd = 0
    if args.delay:
        cd = int(args.delay)

    # get/select device from command line arg
    dev = get_device(devices, args.dev)

    # first we get switch status
    if dev["type"] == "outlet":
        d = tinytuya.OutletDevice(dev["id"], dev["ip"], dev["key"])
    elif dev["type"] == "bulb":
        d = tinytuya.BulbDevice(dev["id"], dev["ip"], dev["key"])
    d.set_version(float(dev["ver"]))
    data = d.status()

    # then we check for comunication errors
    if "dps" not in data:
        if "Error" in data:
            eprint(data["Error"])
            return int(data["Err"])

    try:
        switch_state = data['dps']['1']
    except:
        switch_state = data['dps']['20']
    
    #print("switch_state=",switch_state)
    switch_cmd = args.cmd.strip().lower()
    now = str(datetime.utcnow())
    msg = now + "|turning %s device id %s"

    try:
        if switch_cmd == 'on':
            print(msg % ("on", dev["id"]))
            time.sleep(cd)
            d.turn_on()
        elif switch_cmd == 'off':
            print(msg % ("off", dev["id"]))
            time.sleep(cd)
            d.turn_off()
        elif switch_cmd == 'toggle':
            if switch_state:
                print(msg % ("off", dev["id"]))
            else:
                print(msg % ("on", dev["id"]))
            time.sleep(cd)
            d.set_status(not switch_state)
        else:
            eprint('unknown command')
            return errors["cmd_unknown"]
    except:
        eprint("command failed")
        return errors["cmd_error"]


if __name__ == "__main__":
    ret = main()
    sys.exit(ret)

