""" A ``dict`` which should be named **settings** as configuration file for 
    the **official i-doit demo system**.
    Pass it as **parameter when creating a new object from this class.

    Attributes:
        username ``str``: your Username
        password ``str``: your Password
        apikey ``str``: API Key for this i-doit instance
        base_url ``str``: Domain Name
        verify ``bool``: Verify SSL Connection?
        language ``str``: The Language your are using e.g. en or de
"""
settings = {
    'username': 'admin',
    'password': 'admin',
    'apikey': 'c1ia5q',
    'base_url': 'demo.i-doit.com',
    'verify': False,
    'language': 'en'
}