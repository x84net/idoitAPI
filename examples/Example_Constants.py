#!/usr/bin/env python3
"""
Example-Script for i-doit API class - Display all available constants from idoit (Method cmdb.constants) 

- show structure of one of the global categories (Method cmdb.category_info)
- show structure of one of the specific categories (Method cmdb.category_info)
- show structure of one of the custom categories (Method cmdb.category_info)
"""

from sys import version_info, exit
MIN_PYTHON = (3, 6)
if version_info < MIN_PYTHON:
    exit("Python %s.%s or later is required.\n" % MIN_PYTHON)


from idoit import IdoitAPI
import idoitSettings_Demo as idoitSettings

import logging
import json
from requests import HTTPError

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


if __name__ == "__main__":
    # Logging
    logging.basicConfig( level = logging.INFO,
                         format = '%(message)s',
                         #format = '%(funcName)s:%(message)s',
                         #filename = logFileLocation,
                         #filemode = 'a'
                        )
    log = logging.getLogger()


    # create API instance and catch all defined exceptions
    try:
        pyDoit = IdoitAPI(**idoitSettings.settings)
    except HTTPError as e:
        log.error("HTTP ERR:\n{}\n".format(e))
        exit()
    except ValueError as e:
        log.error("Value ERR:\n{}\n".format(e))
        exit()
    except SystemError as e:
        log.error("System ERR: {}\n".format(e))
        exit()

    res = pyDoit.get_constants()
    log.info("constants:\n{}".format(json.dumps(res, indent=4, sort_keys=True)))

    res = pyDoit.get_global_category_info('C__CATG__IP')
    log.info("global category 'C__CATG__IP':\n{}".format(json.dumps(res, indent=4, sort_keys=True)))

    res = pyDoit.get_specific_category_info('C__CATS__ACCESS_POINT')
    log.info("specific category 'C__CATS__ACCESS_POINT':\n{}".format(json.dumps(res, indent=4, sort_keys=True)))

    res = pyDoit.get_custom_category_info('C__CATG__CUSTOM_FIELDS_BGV_A3_PRFUNG_PROTOKOLL')
    log.info("custom category 'C__CATG__CUSTOM_FIELDS_BGV_A3_PRFUNG_PROTOKOLL':\n{}".format(json.dumps(res, indent=4, sort_keys=True)))

