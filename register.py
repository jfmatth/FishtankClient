# register.py - registration module

import httplib
import urllib
import uuid
import socket
import json
from client.settingsmanager import settings

def getlogininfo():
    # YES - Hardcoded for now :)
    return ("2", "password")

def main():
    # uses settings.txt for now as settings for this module.

    # settings is defined from settingsmanager
    
#    settings = settingsmanager.Settings()
    
    # check that all the neccessary things are there
    user, password = getlogininfo()

    # check if settings already has a GUID
    if not (settings[".guid"] == None or settings[".publickey"] == None):
        print "We are already registered"
        return
    
    # make sure we have the minimum settings we need to register
    if not (settings[".managerhost"] and settings[".registerurl"]):
        raise Exception("missing .managerhost or .registerurl")
        
    # no GUID, then send info to tracker and
    print "managerhost = %s" % settings[".managerhost"]
    print "registerurl = %s" % settings[".registerurl"]
    
    try:      
        HTTPConnection = httplib.HTTPConnection(settings[".managerhost"])
        URL = settings[".registerurl"]
    
        # build the info we need for requesting a registration:
        #  user, password
        #  mac and hostname
    
        macaddr = hex(uuid.getnode())
        sockinfo = socket.gethostbyname_ex(socket.gethostname() )
        ipaddr = sockinfo[2][0]
        hostname = sockinfo[0]
        params = urllib.urlencode( {'user': user,'password':password, 'macaddr':macaddr, 'ipaddr':ipaddr, 'hostname':hostname} )
        
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        HTTPConnection.request("POST", URL, params, headers)
        response = HTTPConnection.getresponse()
    
        HTTPresponse = response.read()
    
        if response.status != 200:
            print HTTPresponse
            raise Exception("non 200 error on POST %s " % response.status)
    
        # so we should have gotten something back that was JSON, let's try to decode it.
        jsonresponse = json.loads(HTTPresponse)
    
        # if we get this far w/o and exception, it must be ok?
        print "public key is %s " % (jsonresponse['publickey'])
        print "guid is %s" % (jsonresponse['guid'])
        
        # update our settings file
        settings['.guid'] = jsonresponse['guid']
        settings['.publickey'] = jsonresponse['publickey']
    except socket.error:
        print "Error connecting to backup manager, is it running?"

if __name__ == "__main__":
    main()
    