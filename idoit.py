__version__ = "1.0"
from pprint import pformat
import os
import logging
import json
import requests

"""Sphinx uses Google Style Python Docstrings"""

class IdoitAPI():
    """Python3 class to access i-doit JSON-RPC API

    API methods - Namespace idoit:
        **Methods currently available in the i-doit JSON-RPC API**

        - idoit.search - ``Implemented``
        - idoit.version - ``Implemented``
        - idoit.constants - ``Implemented``
        - idoit.login - ``Implemented``
        - idoit.logout - ``Implemented``

    API methods - Namespace cmdb:
        **Methods currently available in the i-doit JSON-RPC API**

        - cmdb.object.create - ``Implemented``
        - cmdb.object.read - ``Implemented``
        - cmdb.object.update - ``Implemented``
        - cmdb.object.delete - ``Implemented``
        - cmdb.object.recycle - ``Implemented``
        - cmdb.object.archive - ``Not implemented``
        - cmdb.object.purge - ``Not implemented``
        - cmdb.object.markAsTemplate - ``Not implemented``
        - cmdb.object.markAsMassChangeTemplate - ``Not implemented``
        - cmdb.objects.read - ``Implemented``
        - cmdb.category.save - ``Implemented``
        - cmdb.category.create - ``Not Implemented``
        - cmdb.category.read - ``Implemented``
        - cmdb.category.update - ``Not implemented``
        - cmdb.category.delete - ``Not implemented``
        - cmdb.category.quickpurge - ``Implemented - UNTESTED FIXXXME``
        - cmdb.category.purge - ``Implemented``
        - cmdb.category.recycle - ``Not implemented``
        - cmdb.category.archive - ``Not implemented``
        - cmdb.dialog.read - ``Implemented``
        - cmdb.dialog.create - ``Not implemented``
        - cmdb.dialog.update - ``Not implemented``
        - cmdb.dialog.delete - ``Not implemented``
        - cmdb.reports.read - ``Implemented``

    Args:
        base_url: ``str``: Domain Name
        verify: ``bool``: Verify SSL Connection?
        language: ``str``: The Language your are using e.g. en or de
        username: ``str``: your Username - can be left empty and set by environment variable IDOIT_USERNAME
        password: ``str``: your Password - can be left empty and set by environment variable IDOIT_PASSWORD
        apikey: ``str``: API Key for this i-doit instance - can be left empty and set by environment variable IDOIT_APIKEY

    Raise:
        requests.HTTPError: Raised by requests lib.
        ValueError: Raised when JSON-RPC PORT request returns not HTTP 200 statuscode.
        SystemError: Raised when credentials are missing (username, password or apikey).

    Attributes:
        log_json_request: ``bool``: Set to `True` to log JSON requests send to i-doit.
    """

    def __init__(self, base_url, verify, language, username=None, password=None, apikey=None):
        self.log = logging.getLogger(__name__)

        if username is None:
            self.username = os.environ.get('IDOIT_USERNAME', None)
        else:
            self.username = username

        if password is None:
            self.password = os.environ.get('IDOIT_PASSWORD', None)
        else:
            self.password = password

        if apikey is None:
            self.apikey = os.environ.get('IDOIT_APIKEY', None)
        else:
            self.apikey = apikey
        
        if None in [self.username, self.password, self.apikey]:
            raise SystemError("Missing username, password or apikey.")

        self.base_url = base_url
        self.verify = verify
        self.language = language

        # ID/Cookie of active session
        self.sessionid = ""
        self.url = 'https://{}/src/jsonrpc.php'.format(self.base_url)

        self.batch_list = []
        self.batch_dict = {}        # like batch list, key == json rpc request id

        self.log_json_request = False

        self._api_login()
        # Default JSON-RPC HTTP header for all calls except login()
        self.session_header = {
            'Content-Type': 'application/json',
            'X-RPC-Auth-Session': self.sessionid
        }

    def get_version(self):
        """Get version of this class"""
        return __version__

    def _api_login(self):
        """Login into i-doit and set session ID for later use\n
            - Uses: ``idoit.login``"""
        headers = {
            'Content-Type': 'application/json',
            'X-RPC-Auth-Username': self.username,
            'X-RPC-Auth-Password': self.password
        }
        res = self.send_rpc('idoit.login', {}, headers)
        self.sessionid = res['result']['session-id']        

    def api_logout(self):
        """Terminate active session to i-doit \n
            - Uses: ``idoit.logout``"""
        self.send_rpc('idoit.logout', {})

    def send_rpc_d(self, data, batch=False):
        """Generic method to send json-rpc call to server

            Args:
                data: ``dict``: supply your own data dictionary
                batch: ``bool``: RPC call is batch request.
            Returns:
                JSON object of response or raise exception or when batch is True
                dictionary with object IDs as keys.
        """
        if self.log_json_request:
            self.log.info("send_rpc_d:\n{}".format(json.dumps(data, indent=4, sort_keys=False)))

        response = requests.post(self.url, json=data, headers=self.session_header, verify=self.verify)
        self.log.debug("response:\n{}".format(pformat(response.json())))

        if response.status_code == 200:
            if 'error' not in response.json():
                if not batch:
                    return response.json()
                else: 
                    res_dict = {}
                    for i in response.json():
                        x = i.pop('id')
                        res_dict[x] = i
                    return res_dict

            # tested with wrong user, pass, apikey
            e = response.json()['error']
            self.log.error("\nError Code: {}\nError Message: {}\nError Data: {}\n".format(e['code'], e['message'], e['data']))
            raise ValueError(e['message'])

        return response.raise_for_status()

    def send_rpc(self, method, params_dict, header=None, batch_request=False):
        """Generic method to send json-rpc call to server.
            Only set method and method specific params. Parameters like **apikey** and **language** etc will be added.

            Args:
                method: ``dict``: JSON-RPC method to use
                params_dict: ``dict``: Method specific parameters.
                header: ``dict``: Header if other than default needs to be used.

            Returns:
                JSON object of response or raise exception.
        """
        #self.log.warning("send_rpc() - method={} - batch_request={}".format(method, batch_request))           #DEBUG
        if header:
            headers = header
        else:
            headers = self.session_header

        data = {
            'id': 1,
            'version': '2.0',
            'method': method,
            'params': {
                'apikey': self.apikey,
                'language': self.language
            },
        }
        data['params'].update(params_dict)      # add custom params
        self.log.debug(pformat(data))

        # update batch list/dict myself instead of build_batch()
        if batch_request:
            #self.log.warning("send_rpc() - batch_request")                  #DEBUG
            self.batch_dict.update({len(self.batch_list)+1: data})      # dict with direct access to RPC ID
            data['id'] = len(self.batch_list)+1
            self.batch_list.append(data)
            return data

        if self.log_json_request:
            self.log.info("send_rpc:\n{}".format(pformat(data)))

        response = requests.post(self.url, json=data, headers=headers, verify=self.verify)
        self.log.debug("response code: {}".format(pformat(response.status_code)))
        if response.status_code != 204:
            self.log.debug("response:\n{}".format(pformat(response.json())))

        if response.status_code == 200:
            if 'error' not in response.json():
                return response.json()

            # tested with wrong user, pass, apikey
            e = response.json()['error']
            self.log.error("\nError Code: {}\nError Message: {}\nError Data: {}\n".format(e['code'], e['message'], e['data']))
            raise ValueError(e['message'])

        return response.raise_for_status()

    def send_batch(self):
        """ Submit the currently queued requests and clear the list of queued requests.

            Returns:
                Tuple with result of batch request, batch list that has been send and 
                dictionary with keys = JSON-RPC request ID.
        """
        res = self.send_rpc_d(self.batch_list, True)
        lst = self.batch_list
        dct = self.batch_dict
        self.batch_list = []
        self.batch_dict = {}
        return (res,lst,dct)

    #######################
    ## Low Level Methods ##
    #######################

    def search_text(self, text, batch_request=False):
        """Simple search - like in i-doit top right\n
            - Uses: ``idoit.search``

            Args:
                text: ``str``: Text to search for.
            Returns:
                JSON object of response or raise exception.
        """
        #self.log.warning("search_text() - text={} - batch_request={}".format(text, batch_request))        #DEBUG
        return self.send_rpc('idoit.search', {'q': text}, batch_request=batch_request)

    def get_constants(self, batch_request=False):
        """Fetch defined constants from i-doit\n
            - Uses: ``idoit.constants``
        
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('idoit.constants', {}, batch_request=batch_request)

    def get_idoit_version(self, batch_request=False):
        """Fetch information about i-doit and the current user\n
            - Uses: ``idoit.version``
        
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('idoit.version', {}, batch_request=batch_request)

    def get_category_hostaddress(self, batch_request=False):
        """get structure of category host address

            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'catgID': 47}, batch_request=batch_request)

    def get_global_category_info(self, cat_g_id, batch_request=False):
        """get structure of a certain global category

            Args:
                cat_g_id: ``str``: Global category constant
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'catgID': cat_g_id}, batch_request=batch_request)

    def get_specific_category_info(self, cat_s_id, batch_request=False):
        """get structure of a certain specific category

            Args:
                cat_s_id: ``str``: Specific category constant
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'catsID': cat_s_id}, batch_request=batch_request)

    def get_custom_category_info(self, cat_c_id, batch_request=False):
        """get structure of a certain custom category

            Args:
                cat_c_id: ``str``: Custom category constant
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'customID': cat_c_id}, batch_request=batch_request)

    def get_object_type_categories_by_obj_type(self, obj_type, batch_request=False):
        """Fetch all categories that belong to a certain object

            Args:
                obj_type: ``str``: Object type constant to fetch
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.object_type_categories.read', {'type': obj_type}, batch_request=batch_request)

    def get_object(self, obj_id, batch_request=False):
        """Read general informations of an object specified by it's ID\n
            - Uses: ``cmdb.object.read``

            Args:
                obj_id: ``int``: Object ID of i-doit object
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.object.read', {'id': int(obj_id)}, batch_request=batch_request)

    def get_objects_by_type(self, obj_type, status=2, title=None, limit=None, batch_request=False):
        """Fetch a list of objects filtered by obj_type, title, limit\n
            - Uses: ``cmdb.objects.read``

            Args:
                obj_type: ``int / str``: Number or constant of object type
                status: ``int`` default 2 = Normal (not archived or deleted)
                title: ``str``: Title of object
                limit: ``int / str``: default no limit, can be fixed or with offset
            **limit**:
                - 1000: ``int``: get 1000 objects
                - '1000, 1000': ``str``: with offset, here *get the next thousand object*

            Returns:
                JSON object of response or raise exception.
        """
        f = {'filter': {
                'type': obj_type,
                'status': status
            },
        }
        if limit:
            f['filter'].update({'limit': limit})
        if title:
            f['filter'].update({'title': title})
        return self.send_rpc('cmdb.objects.read', f, batch_request=batch_request)

    def get_category_from_object(self, obj_id, category, batch_request=False):      # better name?
    #def get_category_by_obj_id(self, obj_id, category):         # old name 
        """Read a certain category of an object\n
            - Uses: ``cmdb.category.read``

            Args:
                obj_id: ``int``: Object ID of i-doit object.
                category: ``str``: **Category constant**.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
                'category': category,
                'objID': int(obj_id)
            }
        return self.send_rpc('cmdb.category.read', p, batch_request=batch_request)

    def get_filtered_objects(self, filter_dict, categories=None, batch_request=False):
        """Fetch a list of objects filtered by values in filter_dict and/or categories list\n
            - Uses: ``cmdb.objects.read``

            Args:
                filter_dict: ``dict``: Dictionary with keys to filter request
                categories: ``str``: List of **Category constant(s)**.
            Returns:
                JSON object of response or raise exception."""
        p = {'filter': filter_dict}
        if categories:
            if isinstance(categories, list):
                p.update({'categories': categories})
            else:
                p.update({'categories': [categories]})
        
        return self.send_rpc('cmdb.objects.read', p, batch_request=batch_request)

    def get_dropdown_values(self, category, property_name, batch_request=False):
        """get values from drop down menus like manufacturer, model, CPU type etc.
            Use get_global_category_info(<category>) to find the property_name
        """
        p = {
                'category': category,
                'property': property_name,
            }
        return self.send_rpc('cmdb.dialog.read', p, batch_request=batch_request)

    def create_object_by_type(self, obj_type, title="Default Title - CHANGEME", status=1,
                                category=None, description=None, purpose=None, categories=None, 
                                batch_request=False):
        """Create a new Object of a certain type\n
            - Uses: ``cmdb.object.create``

            Args:
                obj_type: ``str``: Object type constant to fetch.
                title: ``str``: Descriptive title of object.
                status_id: ``int``: CMDB status ID (planned, inoperative, etc.).
                category: ``str``: **Category constant**.
                description: ``str``: Description of object.
                purpose: ``str``: Purpose (constant?) of object (production, test, dev, etc.).
                categories: ``dict``: Categories to populate.

            Attributes:
                Some Object Types:
                    - ??: ``int``: 'C__OBJTYPE__PATCH_PANEL'
                    - 35: ``int``: 'C__OBJTYPE__OPERATING_SYSTEM'
                    -  7: ``int``: 'C__OBJTYPE__ROUTER'
                    -  6: ``int``: 'C__OBJTYPE__SWITCH'
                    -  5: ``int``: 'C__OBJTYPE__SERVER'

                CMDB status IDs:
                    -  1: ``int``: planned
                    -  2: ``int``: ordered
                    -  3: ``int``: delivered
                    -  4: ``int``: assembled
                    -  5: ``int``: tested
                    -  6: ``int``: in operation - constant 'C__CMDB_STATUS__IN_OPERATION'
                    -  7: ``int``: defect
                    -  8: ``int``: under repair
                    -  9: ``int``: delivered from repair
                    - 10: ``int``: inoperative
                    - 11: ``int``: stored - constant 'C__CMDB_STATUS__STORED'
                    - 12: ``int``: scrapped
                    - 15: ``int``: swapped
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'type': obj_type,
            'title': title,
            'cmdb_status': status
        }
        if category:
            p.update({'category': category})
        if description:
            p.update({'description': description})
        if purpose:
            p.update({'purpose': purpose})
        if categories:
            p.update({'categories': categories})
        return self.send_rpc('cmdb.object.create', p, batch_request=batch_request)

    def update_object_category(self, obj_id, category, data_dict, batch_request=False):
        """Update some entries of an object in a certain category.\n
            - Uses: ``cmdb.category.save``

            Args:
                obj_id: ``int``: Object ID of i-doit object.
                category: ``str``: **Category constant**.
                data_dict: ``dict``: Dict with entries to update.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'object': int(obj_id),
            'category': category,
            'data': data_dict
        }
        return self.send_rpc('cmdb.category.save', p, batch_request=batch_request)

    def update_object_category_entry(self, obj_id, category, entry_id, data_dict, batch_request=False):
        """Update an entry in a category of an object.\n
            - Uses: ``cmdb.category.save``
        
            Args:
                obj_id: ``int``: Object ID of i-doit object.
                category: ``str``: **Category constant**.
                entry_id: ``int``: ID of entry to be updated.
                data_dict: ``dict``: Dict with entries to update.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'object': int(obj_id),
            'category': category,
            'entry': int(entry_id),
            'data': data_dict,
        }
        return self.send_rpc('cmdb.category.save', p, batch_request=batch_request)

    def update_cmdb_status(self, obj_id, status_id, batch_request=False):
        """Update CMDB Status of an Object
            - status IDs are listed in ``create_object_by_type()``

            Args:
                obj_id: ``int``: Object ID of i-doit object.
                status_id: ``int``: CMDB status ID (planned, inoperative, etc.).
            Returns:
                JSON object of response or raise exception.
        """
        c = 'C__CATG__GLOBAL'
        d = {'cmdb_status': status_id}
        return self.update_object_category(obj_id, c, d, batch_request=batch_request)

    def update_object_title(self, obj_id, title, batch_request=False):
        """Update the title of a certain object\n
            - Uses: ``cmdb.object.update``

            Args:
                obj_id: ``int``: Object ID of i-doit object.
                title: ``str``: Descriptive title of object.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'id': int(obj_id),
            'title': title
        }
        return self.send_rpc('cmdb.object.update', p, batch_request=batch_request)

    def recycle_object(self, obj_id, batch_request=False):
        """Move object from archived or deleted back to normal\n
            - Uses: ``cmdb.object.recycle``

            Args:
                obj_id: ``int``: Object ID of i-doit object
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.object.recycle', {'object': int(obj_id)}, batch_request=batch_request)

    def delete_object(self, obj_id, move_to='C__RECORD_STATUS__ARCHIVED', batch_request=False):
        """**Delete** an object from CMDB, per default delete = archived\n
            - Uses: ``cmdb.object.delete``

            Args:
                obj_id: ``int``: Object ID of i-doit object
                move_to: ``str``: **Status constant** to move to
            Returns:
                JSON object of response or raise exception.
            
            Attributes:
                Status constants:
                    - "C__RECORD_STATUS__ARCHIVED": ``str``: Archived object
                    - "C__RECORD_STATUS__DELETED": ``str``: Mark object as deleted
        """
        p = {
            'id': int(obj_id),
            'status': move_to
        }
        return self.send_rpc('cmdb.object.delete', p, batch_request=batch_request)

    def purge_object(self, obj_id, category, entry, batch_request=False):
        """Purge category entry of an object from CMDB, for example ip entries from category host address \n
            - Uses: ``cmdb.category.purge``

            Args:
                obj_id: ``int``: Object ID of i-doit object
                category: ``str``: Category constant
                entry: ``int``: Entry identificator
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'object': int(obj_id),
            'category': category,
            'entry': int(entry)
        }
        return self.send_rpc('cmdb.category.purge', p, batch_request=batch_request)

    def quickpurge_object(self, obj_id, category, cat_e_id, batch_request=False):
        """UNTESTED FIXXXME - Purge category entry of an object from CMDB - if quickpurge is active\n
            - Uses: ``cmdb.category.quickpurge``

            Args:
                obj_id: ``int``: Object ID of i-doit object
                category: ``str``: Category constant
                cat_e_id: ``int``: Entry identificator
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'objID': int(obj_id),
            'category': category,
            'cateID': int(cat_e_id)
        }
        return self.send_rpc('cmdb.category.quickpurge', p, batch_request=batch_request)

    def get_report(self, rep_id):
        """Get the results of a predefined report

            Args:
                rep_id: ``int``: ID of the predefined report
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.reports.read', {'id': int(rep_id)}, batch_request=False)

    ########################
    ## High Level Methods ##
    ########################

    def get_ipv4_address(self, obj_id, primary=True, fqdn=False):
        """Fetch IPv4 Address from object. Per default the 'primary_hostaddress' will be returned.

            Args:
                obj_id: ``int``: Object ID of i-doit object
                primary: ``bool``: When primery=False first match for 'hostaddress' will be returned.
                fqdn: ``str``: If fqdn is true a tupple (ip,fqdn) will be returned. **fqdn might be 'None'!**
            Returns:
                Dictionary with keys: 'ip' and maybe 'hostname'
        """
        for i in self.get_category_from_object(obj_id, 'C__CATG__IP')['result']:            
            self.log.info("get_ipv4_address - type(i):\n{}\ni:\n{}".format(type(i), pformat(i)))
            if 'primary_hostaddress' in i and i['primary_hostaddress'] != None:
                pAddr = {'ip': i['primary_hostaddress']['ref_title']}
                if fqdn:
                    if i.get('primary_fqdn'):
                        pAddr.update({'name': i['primary_fqdn'][0]['title']})
                    else:
                        pAddr.update({'name': None})
                    return {'ip': pAddr['ip'], 'hostname': pAddr['name']}
                return {'ip': pAddr['ip']}
            if 'hostaddress' in i and not primary:
                addr = {'ip': i['hostaddress']['ref_title']}
                if fqdn:
                    if 'primary_fqdn' in i:               # fqdn seems to be always 'primary_fqdn'
                        addr.update({'name': i['primary_fqdn']['title']})
                    else:
                        addr.update({'name': None})
                    return {'ip': pAddr['ip'], 'hostname': pAddr['name']}
                return {'ip': pAddr['ip']}
        return None

    def set_ipv4_address(self, obj_id, dev_ip, is_primary=False, hostname=None, fqdn=None, batch_request=False):
        """ Set IPv4 addess and / or hostname, fqdn

            Args:
                obj_id: ``int``: Object ID of i-doit object to get contacts from
                dev_ip: ``str``: IP address to set
                is_primary: ``bool``: set to True if this is the primary address / hostname
                hostname: ``str``: hostname to set
                fqdn: ``str``: fqdn to set
            Returns:
                json rpc response
        """
        values = {'ipv4_address': dev_ip}
        if is_primary:
            values.update({'primary': 1})       # add entry as primary address        
        if hostname:
            values.update({'hostname': hostname})        
        if fqdn:
            values.update({'domain': fqdn})        
        res = self.update_object_category(obj_id, 'C__CATG__IP', values, batch_request=batch_request)        
        return res

    def remove_all_ip_addresses(self, obj_id): 
        """remove all ip entrys from object
            Args:
                obj_id: ``int``: Object ID of i-doit object to remove IPs from
            Returns:
                List of dicts with keys: 'entry_id', 'ip', 'hostname', 'domain', 'is_primary'
        """
        res = self.get_category_from_object(obj_id, 'C__CATG__IP')              # DEBUG
        self.log.info("Switch ip: \n{}".format(pformat(res)))                   # DEBUG
        ip_entrys = []
        for i in res['result']:
            self.log.info("entry id: {}".format(i['id']))
            ip_entrys.append({
                'entry_id': i['id'],
                'ip': i['hostaddress']['ref_title'],
                'hostname': i['hostname'],
                'domain': i['domain'],
                'is_primary': i['primary']['value']
            })

        for ie in ip_entrys:
            self.log.info("purge_object ie: {}".format(pformat(ie['entry_id'])))         # DEBUG
            res = self.purge_object(obj_id, 'C__CATG__IP', ie['entry_id'])
            self.log.info("purge_object res: \n{}\n".format(pformat(res)))

        res = self.get_category_from_object(obj_id, 'C__CATG__IP')              # DEBUG
        self.log.info("Switch ip: \n{}".format(pformat(res)))                   # DEBUG
        return ip_entrys

    def remove_ip_entry(self, obj_id, ip_address): 
        """remove given ip entry from object
            Args:
                obj_id: ``int``: Object ID of i-doit object to remove IPs from
                ip_address: ``str``: IP to remove
            Returns:
                json rpc response                
        """
        res = self.get_category_from_object(obj_id, 'C__CATG__IP')              # DEBUG
        self.log.info("Switch ip: \n{}".format(pformat(res)))                   # DEBUG
        for i in res['result']:
            if ip_address == i['hostaddress']['ref_title']:
                self.log.info("purge_object i: {}".format(pformat(i)))         # DEBUG
                res = self.purge_object(obj_id, 'C__CATG__IP', i)
                self.log.info("purge_object res: \n{}\n".format(pformat(res)))
                break

        stat = self.get_category_from_object(obj_id, 'C__CATG__IP')              # DEBUG
        self.log.info("Switch ip: \n{}".format(pformat(stat)))                   # DEBUG
        return res
            
        # WORKS - reset ipv4 ip in hostadress to empty string
        """
        res = pyDoit.get_category_from_object(obj_id, 'C__CATG__IP')
        log.info("Switch ip: \n{}".format(pformat(res)))
        ip_entrys = []
        for i in res['result']:
            log.info("entry id: \n{}".format(i['id']))
            ip_entrys.append(i['id'])

        for ie in ip_entrys:
            res = pyDoit.update_object_category_entry(obj_id, 'C__CATG__IP', ie, {'ipv4_address':''})
            log.info("Update res: \n{}\n".format(pformat(res)))

        res = pyDoit.get_category_from_object(obj_id, 'C__CATG__IP')
        log.info("Switch ip: \n{}".format(pformat(res)))
        """

    def get_contact(self, obj_id):
        """Get category contact
            Args:
                obj_id: ``int``: Object ID of i-doit object to get contacts from
            Returns:
                json rpc response
        """
        res = self.get_category_from_object(obj_id, 'C__CATG__CONTACT')
        return res

    def get_general(self, obj_id, batch_request=False):
        """Get title, category, cmdb_status, description, purpose, tags from general
            Args:
                obj_id: ``int``: Object ID of i-doit object to get genreal information from
            Returns:
                dict 
        """
        g_obj = self.get_category_from_object(obj_id,'C__CATG__GLOBAL', batch_request=batch_request)
        if batch_request:
            return g_obj
        return self.extract_general(g_obj) 

    def extract_general(self, jsonrpc_response):
        """Extract title, id, category, cmdb_status, description, purpose, tags from response of json-rpc call to 'C__CATG__GLOBAL'
            => to be used with get_general()
            Args:
                obj_id: ``str``: json-rpc response object
            Returns:
                Dict with keys: 'title', 'id', 'category', 'cmdb_status', 'description', 'purpose', 'tag'
        """
        if not len(jsonrpc_response['result']):
            return None
        ret = {}
        ret.update({'title': jsonrpc_response['result'][0]['title']})
        ret.update({'id': int(jsonrpc_response['result'][0]['id'])})
        ret.update({'cmdb_status': jsonrpc_response['result'][0]['cmdb_status']['id']})
        ret.update({'description': jsonrpc_response['result'][0].get('description', None)})
        
        if jsonrpc_response['result'][0]['purpose']:
            ret.update({'purpose': jsonrpc_response['result'][0]['purpose']['id']})

        if jsonrpc_response['result'][0]['category']:
            ret.update({'category': jsonrpc_response['result'][0]['category']['id']})
        
        # tags list
        if jsonrpc_response['result'][0]['tag']:
            tags = []
            for t in jsonrpc_response['result'][0]['tag']:
                tags.append(t['id'])
            ret.update({'tag': tags})

        return ret

    def set_general(self, obj_id, g_dict, batch_request=False):
        """Set 'title', 'category', 'cmdb_status', 'description', 'purpose', 'tags' from dict in general
        
            Args:
                obj_id: ``int``: Object ID of i-doit object to get contacts from
                g_dict: ``dict``: Dictionary with vales to set, purpose and tags might be empty
                                    'category', 'purpose' and 'tags' are not set if None
                
            Attributes:
                Purpose IDs:
                    - '1': ``int``: Produktion
                    - '2': ``int``: Integration
                CMDB status IDs:
                    -  1: ``int``: planned
                    -  6: ``int``: in operation
                    - 10: ``int``: inoperative
                    - 11: ``int``: stored
                    
            Returns:
                json rpc response
        """
        if not batch_request:
            g_obj = self.get_category_from_object(obj_id,'C__CATG__GLOBAL')
            self.log.warning("Changing category General on Object '{}'\n=> from:\n{}\n=> to:\n{}".format(
                                obj_id, pformat(g_obj['result']), pformat(g_dict)))
        values = {
            'title': g_dict['title'],
            'cmdb_status': int(g_dict['cmdb_status']),
        }
        if g_dict.get('description') and g_dict['description'] != 'null':
            values.update({'description': g_dict['description']})
            
        if g_dict.get('category') and g_dict['category'] != 'null':
            values.update({'category': int(g_dict['category'])})
            
        if g_dict.get('purpose') and g_dict['purpose'] != 'null':
            values.update({'purpose': int(g_dict['purpose'])})
            
        if g_dict.get('tag') and g_dict['tag'] != 'null':
            values.update({'tag': g_dict['tag']})

        ret = self.update_object_category(obj_id, 'C__CATG__GLOBAL', values, batch_request=batch_request)
        return ret 

    def get_location(self, obj_id, batch_request=False):
        """Get title, location ID and path of location from an object

            Args:
                obj_id: ``int``: Object ID of i-doit object
            Returns:
                Dict with keys title, id, location_path or raise exception
        """
        res = self.get_category_from_object(obj_id, 'C__CATG__LOCATION', batch_request=batch_request)
        if batch_request:
            return res
        return self.extract_location(res)

    def extract_location(self, jsonrpc_response):
        """Extract title, location ID and path of location from response of json-rpc call to 'C__CATG__LOCATION'
            => to be used with get_location()

            Args:
                jsonrpc_response: ``str``: json-rpc response object
            Returns:
                Dict with keys: 'title', 'id', 'location_path' or raise exception
        """
        if not len(jsonrpc_response['result']):
            return None
        loc = jsonrpc_response['result'][0]['parent']
        return {'title': loc['title'], 'id': loc['id'], 'location_path': loc['location_path']}

    def set_location(self, obj_id, location_id, batch_request=False):
        """Set location path of an object

            Args:
                obj_id: ``int``: Object ID of i-doit object
                location_id: ``int``: Location ID from extract_location()[1]
            Returns:
                json rpc response
        """
        res = self.update_object_category(obj_id,
                                            'C__CATG__LOCATION', 
                                            {'parent': location_id},
                                            batch_request=batch_request)
        return res

    def copy_location(self, from_obj_id, to_obj_id):
        """Copy location from one object to another

            Args:
                from_obj_id: ``int``: Object ID of i-doit object to copy from
                to_obj_id: ``int``: Object ID of i-doit object to copy to
            Returns:
                Dict with keys 'title', 'id', 'location_path' or raise exception as returned by get_location()
        """
        loc = self.get_location(from_obj_id)
        res = self.set_location(to_obj_id, loc[1])
        return loc

    def get_contract_assignment(self, obj_id, batch_request=False):
        """Get contract assignment from an object

            Args:
                obj_id: ``int``: Object ID of i-doit object
            Returns:
                Dict with contract 'title' and 'id' if not batch_request
        """
        res = self.get_category_from_object(obj_id, 'C__CATG__CONTRACT_ASSIGNMENT', batch_request=batch_request)
        if batch_request:
            return res
        return self.extract_contract_assignment(res)

    def extract_contract_assignment(self, jsonrpc_response):
        """Extract contract assignment from response of json-rpc call to 'C__CATG__CONTRACT_ASSIGNMENT'
            Args:
                jsonrpc_response: ``str``: json-rpc response object
            Return:
                Dict with contract 'title' and 'id' if contract is set, else None
        """
        if not len(jsonrpc_response['result']):
            return None
        con = jsonrpc_response['result'][0]['connected_contract']
        return {'title': con['title'], 'id': con['id']}

    def set_contract_assignment(self, obj_id, contract_id, batch_request=False):
        """Set contract assignment from an object

            Args:
                obj_id: ``int``: Object ID of i-doit object
                contract_id: ``int``: Contract ID of contract to assign
            Returns:
                Dict with contract 'title' and 'id' if not batch_request
        """
        res = self.update_object_category(obj_id, 
                                            'C__CATG__CONTRACT_ASSIGNMENT', 
                                            {'connected_contract': contract_id},
                                            batch_request=batch_request)
        return res

    def get_service_assignment(self, obj_id, batch_request=False):
        """Get service assignment from an object

            Args:
                obj_id: ``int``: Object ID of i-doit object
            Returns:
                Dict with contract 'title' and 'id' if not batch_request
        """
        res = self.get_category_from_object(obj_id, 'C__CATG__IT_SERVICE', batch_request=batch_request)
        if batch_request:
            return res
        return self.extract_service_assignment(res)

    def extract_service_assignment(self, jsonrpc_response):
        """Extract service assignment from response of json-rpc call to 'C__CATG__IT_SERVICE'
            Args:
                jsonrpc_response: ``str``: json-rpc response object
            Return:
                Dict with contract 'title' and 'id' if service is set, else None
        """
        if not len(jsonrpc_response['result']):
            return None
        ser = jsonrpc_response['result'][0]['connected_object']
        return {'title': ser['title'], 'id': ser['id']}

    def set_service_assignment(self, obj_id, service_id, batch_request=False):
        """Set service assignment from an object

            Args:
                obj_id: ``int``: Object ID of i-doit object
                service_id: ``int``: Service ID of service to assign
            Returns:
                json rpc response
        """
        res = self.update_object_category(obj_id,
                                            'C__CATG__IT_SERVICE',
                                            {'connected_object': service_id},
                                            batch_request=batch_request)
        return res

    def get_all_os(self):
        """Get a list of all available operating systems

            - filter type 35 = OS
            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type('C__OBJTYPE__OPERATING_SYSTEM', 2)

    def get_all_servers(self):
        """Get a list of all devices in category Hardware->Servers
    
            - filter type 5 = Server - constant 'C__OBJTYPE__SERVER'
            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type('C__OBJTYPE__SERVER', 2)

    def get_all_switches(self):
        """Get a list of all devices in category Hardware->Switches

            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type('C__OBJTYPE__SWITCH', 2)

    def get_all_routers(self):
        """Get a list of all devices in category Hardware->Routers

            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type('C__OBJTYPE__ROUTER', 2)

    def get_all_firewalls(self):
        """Get a list of all devices in category Hardware->Firewall

            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type('C__OBJTYPE__SD_FIREWALL', 2)

    def get_all_loadbalancers(self):
        """Get a list of all devices in category Hardware->Loadbalancer

            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type('C__OBJTYPE__SD_LOADBALANCER', 2)

    def find_host_ip_serial(self, host=None, ip_addr=None, serial=None):
        """Query i-doit for a set of hostname, IP address and serial number in a single call.

            Args:
                host: ``str``: hostname to look for, might be empty
                ip: ``str``: ip address to look for, might be empty
                serial: ``str``: serial number to look for, might be empty
            Returns:
                Dictionary with given host, IP, serial as keys and a list of object IDs
                with matching results as value. Only keys with search results will be present.
        """
        #self.log.warning("=> find_host_ip_serial()")              #DEBUG
        if host:
            #self.log.warning("find_host_ip_serial() host={}".format(host))              #DEBUG
            self.search_text(host, batch_request=True)
        if ip_addr:
            #self.log.warning("find_host_ip_serial() ip_addr={}".format(ip_addr))        #DEBUG
            self.search_text(ip_addr, batch_request=True)
        if serial:
            #self.log.warning("find_host_ip_serial() serial={}".format(serial))          #DEBUG
            self.search_text(serial, batch_request=True)
        
        res,lst,dct = self.send_batch()
        #self.log.debug("query list:\n{}\nquery dict:\n{}\nresponse:\n{}".format(pformat(lst), pformat(dct), pformat(res)))
        #self.log.info("query list:\n{}\nquery dict:\n{}\nresponse:\n{}".format(pformat(lst), pformat(dct), pformat(res)))
        self.log.info("query dict:\n{}\n\nresponse:\n{}".format(pformat(dct), pformat(res)))

        d = {}
        #for i in res:
        for k,v in res.items():
            pos = k - 1                                   # JSON-RPC 2.0 IDs should not be null
            l_id = lst[pos]['params']['q']
            if len(v['result']) == 1:
                d.update({l_id: v['result'][0]['documentId']})
            else:
                for x in v['result']:
                    if not d.get(l_id, None):                   # don't add key if present
                        d.update({l_id: [x['documentId']]})
                    else:
                        if x['documentId'] not in d[l_id]:      # don't add value if present
                            d[l_id].append(x['documentId'])

        return d

    def find_rack(self, r_title):
        """Query i-doit for an object type 'enclosure' with a given title
            Args:
                r_title: ``str``: Enclosure title
            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type('C__OBJTYPE__ENCLOSURE', title=r_title)
