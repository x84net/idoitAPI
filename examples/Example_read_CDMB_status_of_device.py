#!/usr/bin/env python3
"""
Example-Script for i-doit API class - Query CMDB status of a device
"""
from sys import version_info, exit
MIN_PYTHON = (3, 6)
if version_info < MIN_PYTHON:
    exit("Python %s.%s or later is required.\n" % MIN_PYTHON)

from idoit import IdoitAPI
import idoitSettings_Demo as idoitSettings

import logging
from pprint import pformat                          # nice output for debugging
from requests import HTTPError

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import json

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

    # Object ID to query
    obj_ID = 3077       # ID of Switch HQ Infratructure A

    res = pyDoit.get_category_from_object(obj_ID, 'C__CATG__GLOBAL')
    if res['result']:
        log.info("{}\nStatus of C__CATG__GLOBAL:\n{}".format(res['result'][0]['title'],
                                                            json.dumps(res['result'][0]['cmdb_status'], indent=4, sort_keys=True)))
    else:
        log.info("Object ID '{}' not found".format(obj_ID))
