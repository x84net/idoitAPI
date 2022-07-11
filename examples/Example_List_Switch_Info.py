#!/usr/bin/env python3
"""
Example-Script for i-doit API class - Demo usage of method get_all_switches()

- get all switches which are in operation ('cmdb_status_title': 'In Betrieb', 'cmdb_status': 6)
- list: Title, ObjID, Hostname, Domain and IP (address informations from category C__CATG__IP)
"""

from sys import version_info, exit
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

    res = pyDoit.get_all_switches()

    if res['result']:
        log.info("get_all_switches - got {}\n{}\n".format(len(res['result']), json.dumps(res, indent=4, sort_keys=True)))
    else:
        log.info("No switches found")
        exit(1)

    for h in res['result']:
        # print only switches that are "in operation"
        if h['cmdb_status'] != 6:
            continue

        log.info("Title: {}\nObjID: {}".format(h['title'], h['id']))

        addr = pyDoit.get_category_from_object(h['id'],'C__CATG__IP')
        log.debug("addr:\n{}\n".format(pformat(addr['result'])))

        for x in addr['result']:
            log.info("Hostname: {}\nDomain: {}\nIP: {}\n".format(x['hostname'], x['domain'], x['hostaddress']['ref_title']))
