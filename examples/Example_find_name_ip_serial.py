#!/usr/bin/env python3
"""
Example-Script for i-doit API class - Demo usage of method find_host_ip_serial()
"""

from sys import version_info
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

res1 = pyDoit.find_host_ip_serial('swinfrab', '10.20.0.4','asdasdasd1234')
res2 = pyDoit.find_host_ip_serial('gateway', '10.20.0.1')
res3 = pyDoit.find_host_ip_serial('swin','10.20.0.4')
res4 = pyDoit.find_host_ip_serial(serial='asdasda1234')
res5 = pyDoit.find_host_ip_serial('swinfrab')


log.info("Result 1:\n{}".format(json.dumps(res1, indent=4, sort_keys=True)))
log.info("Result 2:\n{}".format(json.dumps(res2, indent=4, sort_keys=True)))
log.info("Result 3:\n{}".format(json.dumps(res3, indent=4, sort_keys=True)))
log.info("Result 4:\n{}".format(json.dumps(res4, indent=4, sort_keys=True)))
log.info("Result 5:\n{}".format(json.dumps(res5, indent=4, sort_keys=True)))
