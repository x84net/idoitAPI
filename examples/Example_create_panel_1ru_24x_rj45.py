#!/usr/bin/env python3
"""
Example-Script for i-doit API class - Create 19' Patchpanel with height 1RU and 24x RJ45 Ports
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
except HTTPError as e_H:
    log.error("HTTP ERR:\n{}\n".format(e_H))
    exit()
except ValueError as e_V:
    log.error("Value ERR:\n{}\n".format(e_V))
    exit()
except SystemError as e_S:
    log.error("System ERR: {}\n".format(e_S))
    exit()

#pyDoit.log_json_request = True


def create_panel_1ru_24x_rj45_new(pan_title, prefix_in, in_start_nr, prefix_out, out_start_nr):
    """Create 19' Patchpanel with height 1RU and 24x RJ45 Ports

            Args:
                pan_title: ``str``: Name of patchpanel
                prefix_in: ``str``: Prefix of input port
                in_start_nr:``int``: Number of first input port
                prefix_out:``str``: Prefix of output port
                out_start_nr:``int``: Number of first output port
            Returns:
                Object ID of new panel.
    """
    # query if panel already exists
    log.info("Checking if Panel with name '{}' already exists...\n".format(pan_title))
    resExists = pyDoit.get_objects_by_type('C__OBJTYPE__PATCH_PANEL', title=pan_title)
    if resExists['result']:
        log.error("ERR: Panel already exists!\n{}".format(json.dumps(resExists['result'], indent=4, sort_keys=False)))
        return resExists['result'][0]['id']
    else:
        log.info("Panel with name '{}' does not exists, creating new one.\n".format(pan_title))

    # build list of ports that should be created - IN port: <P>xx, OUT port: <P>xx
    catg_lst = []
    for i in range(24):
        catg_lst.append({'connection_type': {'const': 'C__CONNECTION_TYPE__RJ45'},
                        'title': "{}{:02d}".format(prefix_in, i+in_start_nr),
                        'type': 1})
        catg_lst.append({'connection_type': {'const': 'C__CONNECTION_TYPE__RJ45'},
                        'title': "{}{:02d}".format(prefix_out, i+out_start_nr),
                        'type': 2})

    # create new panel with ports, set height and form factor - first API call
    resPan = pyDoit.create_object_by_type('C__OBJTYPE__PATCH_PANEL',
                                            title=pan_title,
                                            status=6,
                                            categories = {
                                                'C__CATG__CONNECTOR': catg_lst,
                                                'C__CATG__FORMFACTOR':[
                                                    {
                                                        'formfactor': 'C__FORMFACTOR_TYPE__19INCH',
                                                        'rackunits': 1
                                                    }
                                                ]
                                            })['result']
    log.info("Panel created:\n{}\n".format(json.dumps(resPan, indent=4, sort_keys=True)))

    # build list of port siblings
    pyDoit.return_query_do_not_send = True
    for i in range(0, 47, 2):
        inObj = pyDoit.update_object_category_entry(resPan['id'],
                                                'C__CATG__CONNECTOR',
                                                resPan['categories']['C__CATG__CONNECTOR'][i],
                                                {'connector_sibling': resPan['categories']['C__CATG__CONNECTOR'][i+1]})

        pyDoit.build_batch(inObj)
        outObj = pyDoit.update_object_category_entry(resPan['id'],
                                                'C__CATG__CONNECTOR',
                                                resPan['categories']['C__CATG__CONNECTOR'][i+1],
                                                {'connector_sibling': resPan['categories']['C__CATG__CONNECTOR'][i]})
        pyDoit.build_batch(outObj)
    pyDoit.return_query_do_not_send = False

    # send list of siblings to idoit - second API call
    resCon,lst = pyDoit.send_batch()

    log.info("IN/OUT Ports connected to each other:\n{}".format(json.dumps(resCon, indent=4, sort_keys=True)))
    return resPan['id']


# Generate some uniq panel name
pan_name = "Panel_{}".format(datetime.now().strftime("%H%M%S"))

# Create new Panel with uniq name
res = create_panel_1ru_24x_rj45_new(pan_name, "P", 1, "Pout ", 1)
log.info("ObjID of new Panel is: {}".format(json.dumps(res, indent=4, sort_keys=False)))

## Show data of all in-/output ports
#resC = pyDoit.get_category_from_object(res, 'C__CATG__CONNECTOR')['result']
#for i in resC:
#    log.info("res:\n{}".format(json.dumps(i, indent=4, sort_keys=False)))
