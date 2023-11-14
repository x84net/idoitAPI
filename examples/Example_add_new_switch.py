#!/usr/bin/env python3
"""
Example-Script for i-doit API class - add a new switch to idoit / create new switch object
"""

from sys import version_info
MIN_PYTHON = (3, 6)
if version_info < MIN_PYTHON:
    exit("Python %s.%s or later is required.\n" % MIN_PYTHON)


from idoit import IdoitAPI
import idoitSettings_Demo as idoitSettings

import logging
import json
from datetime import datetime
from requests import HTTPError

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_new_switch():
    # Generate some uniq hostname / serialnumber
    sw_name = "Switch_{}".format(datetime.now().strftime("%H%M%S"))
    sw_sn = "c0ffee{}".format(datetime.now().strftime("%H%M%S"))

    # Create new switch
    resSW = pyDoit.create_object_by_type('C__OBJTYPE__SWITCH',
                                            title = sw_name,
                                            status = 6,
                                            description = "The Switch to be",
                                            categories = {
                                                'C__CATG__IP': [{
                                                        "net_type": 1,
                                                        "ipv4_assignment": 1,
                                                        "ipv4_address": "192.168.1.13",
                                                        "primary_hostaddress": "192.168.1.13"
                                                }],
                                                'C__CATG__MODEL': [{
                                                        'manufacturer': 3,          # HP
                                                        'title': 12,                # 2530-48G-PoE+-2SFP+
                                                        'serial': sw_sn,
                                                }],
                                                'C__CATG__FORMFACTOR': [{
                                                        'formfactor': "C__FORMFACTOR_TYPE__19INCH",
                                                        'rackunits': 1
                                                }],
                                                'C__CATG__LOCATION': [{
                                                        'parent': 57,               # ObjID from Rack Colo A002
                                                        'option': 3,                # 3=horizontal
                                                        'insertion': 1,             # 0=back, 1=front, 2=both
                                                        #'pos': {                   # doesn't work, pos is always top fo the rack
                                                        #    'visually_from': 32,
                                                        #    'visually_to': 33
                                                        #}
                                                }]
                                            }
                                        )['result']
    return resSW

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

    """
    # Example: Switch Switch HQ Infratructure A ID: 3077
    res = pyDoit.get_category_from_object(3077, 'C__CATG__MODEL')
    log.info("'C__CATG__MODEL':\n{}".format(json.dumps(res, indent=4)))

    res = pyDoit.get_category_from_object(3077, 'C__CATG__FORMFACTOR')
    log.info("'C__CATG__FORMFACTOR':\n{}".format(json.dumps(res, indent=4,)))

    res = pyDoit.get_category_from_object(3077,  'C__CATG__LOCATION')
    log.info(" 'C__CATG__LOCATION':\n{}".format(json.dumps(res, indent=4)))
    """

    res = create_new_switch()
    log.info("Switch: \n{}\nhttps://demo.i-doit.com/?objID={}".format(json.dumps(res, indent=4), res['id']))
