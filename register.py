# register.py - registration module

import httplib
import urllib
import uuid
import socket
import json
from optparse import OptionParser

from client.settingsmanager import settings

class RegistrationError(Exception):
    pass

def register():

#    if (userid == None or password == None):
#        raise RegistrationError("You must supply a id and password")
    # make sure we have the minimum settings we need to register
    if not (settings[".managerhost"] and settings[".registerurl"]):
        raise RegistrationError("missing .managerhost or .registerurl")

    if not settings['.registerkey']:
        raise RegistrationError("missing .registerkey")

    try:      
        HTTPConnection = httplib.HTTPConnection(settings[".managerhost"])
        URL = settings[".registerurl"]
    
        macaddr = hex(uuid.getnode())
        sockinfo = socket.gethostbyname_ex(socket.gethostname() )
        ipaddr = sockinfo[2][0]
        hostname = sockinfo[0]
#        params = urllib.urlencode( {'userid': userid,
#                                    'password':password,
#                                    'macaddr':macaddr,
#                                    'ipaddr':ipaddr,
#                                    'hostname':hostname}
#                                 )
        params = urllib.urlencode( {'verifykey': settings['.registerkey'],
                                    'macaddr':macaddr,
                                    'ipaddr':ipaddr,
                                    'hostname':hostname}
                                 )

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        HTTPConnection.request("POST", URL, params, headers)
        response = HTTPConnection.getresponse()

        HTTPresponse = response.read()

        if response.status != 200:
            print "Login failed for id = %s - %s, %s " % (settings[".registerkey"], response.status, HTTPresponse)
    
        else:
            # so we should have gotten something back that was JSON, let's try to decode it.
            jsonresponse = json.loads(HTTPresponse)

            # update our settings file
            settings['.guid'] = jsonresponse['guid']
            settings['.publickey'] = jsonresponse['publickey']
            settings['.privatekey'] = jsonresponse['privatekey']

    except socket.error:
        print "Error connecting to backup manager, is it running?"

if __name__ == "__main__":
    # grab the userid and password 
    parser = OptionParser()
#    parser.add_option("-u", "--user",
#                      action="store",
#                      type="string",
#                      dest="userid",
#                      help="specify the userid"
#                      )
#    parser.add_option("-p", "--password",
#                      dest="password",
#                      action="store",
#                      type="string",
#                      help="specify the users password")
    register()
    