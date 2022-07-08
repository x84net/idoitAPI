__version__ = "0.5.1"
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
        - cmdb.category.create - ``Implemented but fiXXXme``
        - cmdb.category.read - ``Implemented``
        - cmdb.category.update - ``Not implemented``
        - cmdb.category.delete - ``Not implemented``
        - cmdb.category.quickpurge - ``Implemented - UNTESTED FIXXXME``
        - cmdb.category.purge - ``Implemented - UNTESTED FIXXXME``
        - cmdb.category.recycle - ``Not implemented``
        - cmdb.category.archive - ``Not implemented``
        - cmdb.dialog.read - ``Implemented``
        - cmdb.dialog.create - ``Not implemented``
        - cmdb.dialog.update - ``Not implemented``
        - cmdb.dialog.delete - ``Not implemented``
        - cmdb.reports.read - ``Not implemented``

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
        return_query_do_not_send: ``bool``: Guard to get JSON query from method instead of sending it. 
                Can be used to get `obj_dict` for build_batch().
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

        self.log_json_request = False
        self.return_query_do_not_send = False

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

        if self.return_query_do_not_send:
            return data
        
        response = requests.post(self.url, json=data, headers=self.session_header, verify=self.verify)
        self.log.debug("response:\n{}".format(pformat(response.json())))

        if response.status_code == 200:
            if 'error' not in response.json():
                if not batch:
                    return response.json()
                else: 
                    r_d = {}
                    for i in response.json():
                        x = i.pop('id')
                        r_d[x] = i
                    return r_d

            # tested with wrong user, pass, apikey
            e = response.json()['error']
            self.log.error("\nError Code: {}\nError Message: {}\nError Data: {}\n".format(e['code'], e['message'], e['data']))
            raise ValueError(e['message'])

        return response.raise_for_status()

    def send_rpc(self, method, params_dict, header=None):
        """Generic method to send json-rpc call to server.
            Only set method and method specific params. Parameters like **apikey** and **language** etc will be added.

            Args:
                method: ``dict``: JSON-RPC method to use
                params_dict: ``dict``: Method specific parameters.
                header: ``dict``: Header if other than default needs to be used.

            Returns:
                JSON object of response or raise exception.
        """
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

        if self.return_query_do_not_send:
            return data

        if self.log_json_request:
            self.log.info("send_rpc:\n{}".format(json.dumps(data, indent=4, sort_keys=False)))

        response = requests.post(self.url, json=data, headers=headers, verify=self.verify)
        self.log.debug("response:\n{}".format(pformat(response.json())))

        if response.status_code == 200:
            if 'error' not in response.json():
                return response.json()

            # tested with wrong user, pass, apikey
            e = response.json()['error']
            self.log.error("\nError Code: {}\nError Message: {}\nError Data: {}\n".format(e['code'], e['message'], e['data']))
            raise ValueError(e['message'])

        return response.raise_for_status()

    def search_text(self, text):
        """Simple search - like in i-doit top right\n
            - Uses: ``idoit.search``

            Args:
                text: ``str``: Text to search for.
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('idoit.search', {'q': text})

    def get_constants(self):
        """Fetch defined constants from i-doit\n
            - Uses: ``idoit.constants``
        
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('idoit.constants', {})

    def get_idoit_version(self):
        """Fetch information about i-doit and the current user\n
            - Uses: ``idoit.version``
        
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('idoit.version', {})

    def get_category_hostaddress(self):
        """get structure of category host address

            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'catgID': 47})

    def get_global_category_info(self, cat_g_id):
        """get structure of a certain global category

            Args:
                cat_g_id: ``str``: Global category constant
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'catgID': cat_g_id})

    def get_specific_category_info(self, cat_s_id):
        """get structure of a certain specific category

            Args:
                cat_s_id: ``str``: Specific category constant
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'catsID': cat_s_id})

    def get_custom_category_info(self, cat_c_id):
        """get structure of a certain custom category

            Args:
                cat_c_id: ``str``: Custom category constant
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.category_info', {'customID': cat_c_id})

    def get_object_type_categories_by_obj_type(self, obj_type):
        """Fetch all categories that belong to a certain object

            Args:
                obj_type: ``str``: Object type constant to fetch
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.object_type_categories.read', {'type': obj_type})

    def get_object(self, obj_id):
        """Read general informations of an object specified by it's ID\n
            - Uses: ``cmdb.object.read``

            Args:
                obj_id: ``str``: Object ID of i-doit object
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.object.read', {'id': obj_id})

    def get_objects_by_type(self, obj_type, status=2, title=None, limit=None):
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
        return self.send_rpc('cmdb.objects.read', f)

    def get_category_from_object(self, obj_id, category):      # better name?
    #def get_category_by_obj_id(self, obj_id, category):         # old name 
        """Read a certain category of an object\n
            - Uses: ``cmdb.category.read``

            Args:
                obj_id: ``str``: Object ID of i-doit object.
                category: ``str``: **Category constant**.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
                'category': category,
                'objID': obj_id
            }
        return self.send_rpc('cmdb.category.read', p)

    def get_filtered_objects(self, filter_dict, categories=None):
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
        
        return self.send_rpc('cmdb.objects.read', p)

    def get_dropdown_values(self, category, property_name):
        """get values from drop down menus like manufacturer, model, CPU type etc.
            Use get_global_category_info(<category>) to find the property_name
        """
        p = {
                'category': category,
                'property': property_name,
            }
        return self.send_rpc('cmdb.dialog.read', p)

    def create_object_by_type(self, obj_type, title="Default Title - CHANGEME", status=1,
                                category=None, description=None, purpose=None, categories=None):
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

                CMDB status IDs
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
                    - 11: ``int``: stored
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
        return self.send_rpc('cmdb.object.create', p)

    def create_category(self, new_obj_id, category, data_dict):
        """**Experimental**\n
            - Uses: ``cmdb.category.create``
            - **how to create unique obj_id?**

            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'objID': new_obj_id,
            'category': category,
            'data': data_dict
        }
        return self.send_rpc('cmdb.category.create', p)

    def update_object_category(self, obj_id, category, data_dict):
        """Update some entries of an object in a certain category.\n
            - Uses: ``cmdb.category.save``

            Args:
                obj_id: ``str``: Object ID of i-doit object.
                category: ``str``: **Category constant**.
                data_dict: ``dict``: Dict with entries to update.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'object': obj_id,
            'category': category,
            'data': data_dict
        }
        return self.send_rpc('cmdb.category.save', p)

    def update_object_category_entry(self, obj_id, category, entry_id, data_dict):
        """Update an entry in a category of an object.\n
            - Uses: ``cmdb.category.save``
        
            Args:
                obj_id: ``str``: Object ID of i-doit object.
                category: ``str``: **Category constant**.
                entry_id: ``str``: ID of entry to be updated.
                data_dict: ``dict``: Dict with entries to update.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'object': obj_id,
            'category': category,
            'entry': entry_id,
            'data': data_dict,
        }
        return self.send_rpc('cmdb.category.save', p)

    def update_cmdb_status(self, obj_id, status_id):
        """Update CMDB Status of an Object
            - status IDs are listed in ``create_object_by_type()``

            Args:
                obj_id: ``str``: Object ID of i-doit object.
                status_id: ``int``: CMDB status ID (planned, inoperative, etc.).
            Returns:
                JSON object of response or raise exception.
        """
        c = 'C__CATG__GLOBAL'
        d = {'cmdb_status': status_id}
        return self.update_object_category(obj_id, c, d)

    def update_object_title(self, obj_id, title):
        """Update the title of a certain object\n
            - Uses: ``cmdb.object.update``

            Args:
                obj_id: ``str``: Object ID of i-doit object.
                title: ``str``: Descriptive title of object.
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'id': obj_id,
            'title': title
        }
        return self.send_rpc('cmdb.object.update', p)

    def recycle_object(self, obj_id):
        """Move object from archived or deleted back to normal\n
            - Uses: ``cmdb.object.recycle``

            Args:
                obj_id: ``str``: Object ID of i-doit object
            Returns:
                JSON object of response or raise exception.
        """
        return self.send_rpc('cmdb.object.recycle', {'object': obj_id})

    def delete_object(self, obj_id, move_to='C__RECORD_STATUS__ARCHIVED'):
        """**Delete** an object from CMDB, per default delete = archived\n
            - Uses: ``cmdb.object.delete``

            Args:
                obj_id: ``str``: Object ID of i-doit object
                move_to: ``str``: **Status constant** to move to
            Returns:
                JSON object of response or raise exception.
            
            Attributes:
                Status constants:
                    - "C__RECORD_STATUS__ARCHIVED": ``str``: Archived object
                    - "C__RECORD_STATUS__DELETED": ``str``: Mark object as deleted
        """
        p = {
            'id': obj_id,
            'status': move_to
        }
        return self.send_rpc('cmdb.object.delete', p)

    def purge_object(self, obj_id, category, entry):
        """UNTESTED FIXXXME - Purge category entry of an object from CMDB\n
            - Uses: ``cmdb.category.purge``

            Args:
                obj_id: ``int``: Object ID of i-doit object
                category: ``str``: Category constant
                entry: ``int``: Entry identificator
            Returns:
                JSON object of response or raise exception.
        """
        p = {
            'object': obj_id,
            'category': category,
            'entry': entry
        }
        return self.send_rpc('cmdb.category.purge', p)

    def quickpurge_object(self, obj_id, category, cat_e_id):
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
            'objID': obj_id,
            'category': category,
            'cateID': cat_e_id
        }
        return self.send_rpc('cmdb.category.quickpurge', p)


    def get_ipv4_address(self, obj_id, primary=True, fqdn=False):
        """Fetch IPv4 Address from object. Per default the 'primary_hostaddress'
            will be returned.

            Args:
                obj_id: ``str``: Object ID of i-doit object
                primary: ``bool``: When primery=False first match for 'hostaddress' will be returned.
                fqdn: ``str``: If fqdn is true a tupple (ip,fqdn) will be returned. **fqdn might be 'None'!**
            Returns:
                JSON object of response or raise exception.
        """
        for i in self.get_category_by_obj_id(obj_id, 'C__CATG__IP')['result']:
            if i.get('primary_hostaddress'):
                pAddr = {'ip': i.get('primary_hostaddress')['ref_title']}
                if fqdn:
                    if i.get('primary_fqdn'):
                        pAddr.update({'name': i.get('primary_fqdn')['ref_title']})
                    else:
                        pAddr.update({'name': None})
                    return (pAddr['ip'], pAddr['name'])
                return pAddr['ip']
            if i.get('hostaddress') and not primary:
                addr = {'ip': i.get('hostaddress')['ref_title']}
                if fqdn:
                    if i.get('primary_fqdn'):               # fqdn seems to be always 'primary_fqdn'
                        addr.update({'name': i.get('primary_fqdn')['ref_title']})
                    else:
                        addr.update({'name': None})
                    return (addr['ip'], addr['name'])
                return addr['ip']
        return None

    def get_all_os(self):
        """Get a list of all available operating systems

            - filter type 35 = OS
            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type(35, 2)

    def get_all_servers(self):
        """Get a list of all devices in category Hardware->Servers
    
            - filter type 5 = Server - constant 'C__OBJTYPE__SERVER'
            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type(5, 2)

    def get_all_switches(self):
        """Get a list of all devices in category Hardware->Switches

            - filter type 6 = Switches
            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type(6, 2)

    def get_all_routers(self):
        """Get a list of all devices in category Hardware->Routers

            - filter type 7 = Router
            - filter status 2 = Normal (not archived or deleted)

            Returns:
                JSON object of response or raise exception.
        """
        return self.get_objects_by_type(7, 2)

    def build_batch(self, obj_dict):
        """Attach object to a list to be submited as batch request within a single call.
            Dataset ID equals to length of list, beginning with 1 as first ID
            as of JSON-RPC 2.0 IDs should not be null.\n
            obj_dict can be created by calling the appropriate method with return_query_do_not_send
            guard set.

            Args:
                grp_list: ``list``: List of JSON objects
                obj_dict: ``dict``: JSON query / object
            Returns:
                List of JSON-RPC objects
        """
        obj_dict['id'] = len(self.batch_list)+1
        self.batch_list.append(obj_dict)

    def send_batch(self):
        """ Submit the currently queued requests and clear the list of queued requests.

            Returns:
                Tuple with result of batch request and batch list that has been send.
        """
        res = self.send_rpc_d(self.batch_list, True)
        lst = self.batch_list
        self.batch_list = []
        return (res,lst)

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
        self.return_query_do_not_send = True
        if host:
            self.build_batch(self.search_text(host))
        if ip_addr:
            self.build_batch(self.search_text(ip_addr))
        if serial:
            self.build_batch(self.search_text(serial))
        self.return_query_do_not_send = False

        res,lst = self.send_batch()
        self.log.debug("query:\n{}\nresponse:\n{}".format(pformat(lst), pformat(res)))

        d = {}
        for i in res:
            pos = i['id'] - 1                                   # JSON-RPC 2.0 IDs should not be null
            l_id = lst[pos]['params']['q']
            if len(i['result']) == 1:
                d.update({l_id: i['result'][0]['documentId']})
            else:
                for x in i['result']:
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

