#!/usr/bin/env python3
"""
Example-Script for i-doit API class - group multiple JSON requests in one call
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

    #pyDoit.log_json_request = True

    #group multiple requests in one call
    data = [
        {
            'id': 1,
            'version': '2.0',
            'method': 'idoit.search',
            'params': {
                'q': "10.20.0.4",
                'apikey': pyDoit.apikey,
                'language': pyDoit.language
            },
        },
        {
            'id': 2,
            'version': '2.0',
            'method': 'idoit.search',
            'params': {
                'q': "10.20.0.2",
                'apikey': pyDoit.apikey,
                'language': pyDoit.language
            },
        }
    ]
    res = pyDoit.send_rpc_d(data)
    log.info("group search result:\n{}".format(json.dumps(res, indent=4, sort_keys=True)))
