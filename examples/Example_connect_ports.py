#!/usr/bin/env python3
"""
Example-Script for i-doit API class - Connecting and / or creating ports
"""

from sys import version_info
MIN_PYTHON = (3, 6)
if version_info < MIN_PYTHON:
    exit("Python %s.%s or later is required.\n" % MIN_PYTHON)


from idoit import IdoitAPI
import idoitSettings_Demo as idoitSettings

import logging
import json
from pprint import pformat                          # nice output for debugging
from requests import HTTPError

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Create port 'Console0'
def create_console0(obj_id):
    d = {
        'title': 'Console0',
        'description': 'Access to serial console',
        'speed': 9600,
        'speed_type': 'C__PORT_SPEED__BIT_S',
        'active': '1',
        'plug_type': 'C__CONNECTION_TYPE__RJ45',
    }
    res = pyDoit.update_object_category(obj_id, 'C__CATG__NETWORK_PORT', d)
    log.info("New port Console0:\n{}\nhttps://demo.i-doit.com/?objID={}&catgID=94".format(
                                                                                json.dumps(res['result'], indent=4, sort_keys=False),
                                                                                obj_id))


# Connect ports of two objects
def connect_ports(obj_id_a, port_title_a, obj_id_b, port_title_b):
    obj_id_title_a = None
    obj_id_title_b = None

    # get connectors from devices - use batch requests
    pyDoit.get_category_from_object(obj_id_a, 'C__CATG__CONNECTOR', batch_request=True)
    pyDoit.get_category_from_object(obj_id_b, 'C__CATG__CONNECTOR', batch_request=True)
    res_d, lst_q, dct_q = pyDoit.send_batch()

    # search for port names in title of first request to get IDs
    for i in res_d[1]['result']:
        if port_title_a == i['title']:
            obj_id_title_a = int(i['id'])
            break

    # search for port names in title of second request to get IDs
    for i in res_d[2]['result']:
        if port_title_b == i['title']:
            obj_id_title_b = int(i['id'])
            break

    # connect ports
    res = pyDoit.update_object_category_entry(obj_id_a, 'C__CATG__CONNECTOR', obj_id_title_a, {'assigned_connector': obj_id_title_b})
    return ((obj_id_a, obj_id_title_a),(obj_id_b, obj_id_title_b))

if __name__ == "__main__":
    # Logging
    logging.basicConfig(level = logging.INFO,
                        format = '%(message)s',
                        #format = '%(funcName)s:%(message)s',
                        #filename = logFileLocation,
                        #filemode = 'a'
    )
    log = logging.getLogger()

    # create API instance and catch all defined exceptions
    try:
        pyDoit = IdoitAPI(**idoitSettings.settings)
    except HTTPError as e_H:
        log.error("HTTP ERR:\n{}\n".format(e_H))
        exit()
    except ValueError as e_V:
        log.error("Value ERR:\n{}\n".format(e_V))
        exit()
    except SystemError as e_S:
        log.error("System ERR: {}\n".format(e_S))
        exit()

    # uncomment to see JSON request that is send to idoit
    #pyDoit.log_json_request = True

    #------------------------------------------------------------------------------------------
    # Connect Switch HQ Infratructure B (id: 3081) Port 02 with HQ Gateway (id: 944) Port eth2 
    #------------------------------------------------------------------------------------------
    sw_id = 3081            # Switch HQ Infratructure B
    sw_port = 'Port 02'
    rt_id = 944             # Router HQ Gateway
    rt_port = 'eth2'
    res = connect_ports(sw_id, sw_port, rt_id, rt_port)
    log.info("IDs of connected objects (Switch to Router):\n{}\n".format(pformat(res)))


    #--------------------------------------------------------------------------------------------------
    # Connect Switch HQ Infratructure B (id: 3081) Port 03 with Panel HQ Intern 01 B (id: 993) Port 02
    #--------------------------------------------------------------------------------------------------
    sw_id = 3081            # Switch HQ Infratructure B
    sw_port = 'Port 03'
    pan_id = 993            # Panel HQ Intern 01 B
    pan_port = 'Port 02'
    res = connect_ports(sw_id, sw_port, pan_id, pan_port)
    log.info("IDs of connected objects (Switch to Patchpanel):\n{}\n".format(pformat(res)))


    #------------------------------------------------------------------------------------------------
    # Create port 'Console0' on switch Switch HQ Infratructure B (id: 3081) or demo router (id: 944) 
    #------------------------------------------------------------------------------------------------
    #devID = '3081'
    devID = '944'
    create_console0(devID)
