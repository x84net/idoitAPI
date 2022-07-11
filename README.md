# idoitAPI

**This project is work in progress, use at your own risk!**  

It's just a python class and i have no intend to create a python package.  

---

## i-doit documentation
Have a look at the i-doit documentation
* [API Methoden](https://kb.i-doit.com/display/de/API+Methoden)
* [Category Fields for Data Arrays](https://kb.i-doit.com/display/en/Category+Fields+for+Data+Arrays)

## JSON-RPC 
If you dont't know JSON-RPC, read this
* [JSON-RPC Specification](https://www.jsonrpc.org/specification)

## Working with i-doit
* Sometimes you'll need to specifiy the object ID as `'id': 12345`, sometimes it's just the ID `12345`. For example not `'manufacturer': {'id': 3}`, just `'manufacturer': 3`.
* Have a look at the categories, you'll need them.
* There are [documented methods](https://kb.i-doit.com/pages/viewpage.action?pageId=7831613#API(JSONRPC)-Methoden) that work but seems to be old. For example `cmdb.location_tree` which is not listed on [API Methoden](https://kb.i-doit.com/display/de/API+Methoden).

https://htmlpreview.github.io/?https://github.com/x84net/idoitAPI/blob/main/doc/html/index.html
