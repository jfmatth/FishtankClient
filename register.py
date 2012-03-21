# register.py - registration module

import httplib
import urllib
import uuid
import socket
import json

from client.settingsmanager import settings

class RegistrationError(Exception):
    pass

def register():

    # make sure we have the minimum settings we need to register
    if not (settings.get(".managerhost") and settings.get(".registerurl") ):
        raise RegistrationError("missing .managerhost or .registerurl")

    if not settings.get('.registerkey'):
        raise RegistrationError("missing .registerkey")

    try:      
        HTTPConnection = httplib.HTTPConnection(settings.get(".managerhost") )
        URL = settings.get(".registerurl")
    
        macaddr = hex(uuid.getnode())
        sockinfo = socket.gethostbyname_ex(socket.gethostname() )
        ipaddr = sockinfo[2][0]
        hostname = sockinfo[0]
        params = urllib.urlencode( {'verifykey': settings.get('.registerkey'),
                                    'macaddr':macaddr,
                                    'ipaddr':ipaddr,
                                    'hostname':hostname}
                                 )

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        HTTPConnection.request("POST", URL, params, headers)
        response = HTTPConnection.getresponse()

        HTTPresponse = response.read()

        if response.status != 200:
            print "Login failed for id = %s - %s, %s " % (settings.get(".registerkey"), response.status, HTTPresponse)
            return False
    
        else:
            # so we should have gotten something back that was JSON, let's try to decode it.
            jsonresponse = json.loads(HTTPresponse)

            # update our settings file
            settings.set('.guid', jsonresponse['guid'] )
            settings.set('.publickey',jsonresponse['publickey'] )
            settings.set('.privatekey', jsonresponse['privatekey'] )

            return True

    except socket.error:
        return False


def target(*argv):
    main()

def main():
    if register():
        print "Registered"
    
if __name__ == "__main__":
    # grab the userid and password 

    main()