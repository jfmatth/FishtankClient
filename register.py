# register.py - registration module

#import httplib
#import urllib
#import json

import requests

import uuid
import socket
import sys
import os

from client.settingsmanager import settings

class RegistrationError(Exception):
    pass

def register(key=None):

    # make sure we have the minimum settings we need to register
    if not (settings[".managerhost"] and settings[".registerurl"]):
        raise RegistrationError("missing .managerhost or .registerurl")

    if key == None:
        raise RegistrationError("missing registration key")

    # reset the settings environment before we register
    settings.reset()

    try:      
#        HTTPConnection = httplib.HTTPConnection(settings[".managerhost"])
#        URL = settings[".registerurl"]
#        macaddr = hex(uuid.getnode())
#        sockinfo = socket.gethostbyname_ex(socket.gethostname() )
#        ipaddr = sockinfo[2][0]
#        hostname = sockinfo[0]
#        params = urllib.urlencode( {'verifykey': key,
#                                    'macaddr':macaddr,
#                                    'ipaddr':ipaddr,
#                                    'hostname':hostname}
#                                 )

        # support Requests now.
        sockinfo = socket.gethostbyname_ex(socket.gethostname() )

        regparams = {'verifykey': key,
                     'macaddr':hex(uuid.getnode()),
                     'ipaddr': sockinfo[2][0] ,
                     'hostname':sockinfo[0]
                    }

        connection = settings[".managerhost"] + settings[".registerurl"]
        RequestConn = requests.post(connection,data=regparams)

#        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
#        HTTPConnection.request("POST", URL, params, headers)
#        response = HTTPConnection.getresponse()
#        HTTPresponse = response.read()

#        if response.status != 200:
        if RequestConn.status_code != 200:
#            print "Login failed for id = %s - %s, %s " % (key, response.status, HTTPresponse)
            print "Login failed for id = %s - %s " % (key, RequestConn.status_code) 
        else:
            # so we should have gotten something back that was JSON, let's try to decode it.
#            jsonresponse = json.loads(HTTPresponse)

            if RequestConn.json:
                # update our settings file
                settings['.guid'] = RequestConn.json['guid']
                settings['.publickey'] = RequestConn.json['publickey']
                settings['.privatekey'] = RequestConn.json['privatekey']

                # update install directory
                settings['.installdir'] = os.getcwd()
            else:
                print "Error in the JSON"

    except socket.error:
        print "Error connecting to backup manager, is it running?"

if __name__ == "__main__":
    if len(sys.argv) == 2:
        register(sys.argv[1])
    else:
        print "No registration key given, aborting"