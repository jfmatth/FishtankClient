# register.py - registration module

import httplib
import urllib
import uuid
import socket
import json
import sys
import os

from client.settingsmanager import settings

class RegistrationError(Exception):
    pass

def register(key=None):

    # make sure we have the minimum settings we need to register
    if not (settings[".managerhost"] and settings[".registerurl"]):
        raise RegistrationError("missing .managerhost or .registerurl")

    #if not settings['.registerkey']:
    #    raise RegistrationError("missing .registerkey")
    # use a parameter now for the register key
    if key == None:
        raise RegistrationError("missing registration key")

    try:      
        HTTPConnection = httplib.HTTPConnection(settings[".managerhost"])
        URL = settings[".registerurl"]
    
        macaddr = hex(uuid.getnode())
        sockinfo = socket.gethostbyname_ex(socket.gethostname() )
        ipaddr = sockinfo[2][0]
        hostname = sockinfo[0]

        params = urllib.urlencode( {'verifykey': key,
                                    'macaddr':macaddr,
                                    'ipaddr':ipaddr,
                                    'hostname':hostname}
                                 )

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        HTTPConnection.request("POST", URL, params, headers)
        response = HTTPConnection.getresponse()

        HTTPresponse = response.read()

        if response.status != 200:
            print "Login failed for id = %s - %s, %s " % (key, response.status, HTTPresponse)
    
        else:
            # so we should have gotten something back that was JSON, let's try to decode it.
            jsonresponse = json.loads(HTTPresponse)

            # update our settings file
            settings['.guid'] = jsonresponse['guid']
            settings['.publickey'] = jsonresponse['publickey']
            settings['.privatekey'] = jsonresponse['privatekey']
            
            # update install directory
            settings['.installdir'] = os.getcwd()
    
    except socket.error:
        print "Error connecting to backup manager, is it running?"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        register(sys.argv[1])
    else:
        print "No registration key given, aborting"
    