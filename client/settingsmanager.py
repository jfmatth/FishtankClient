""" settingsmanager.py - a central class for getting / setting all settings in the system.

x = settingsmanager.ftSettings(file="settings.txt")

x[<key>]
x[<key>] = <string value>

print x["mysetting"]

x["mysetting"] = "blah blah blah"

if <key> starts with "." then that value will be written to the local
"settings" file (default is settings.txt)

if <key> starts with #, thats special on the server.
f.
"""

import anydbm
import urllib
import httplib
import ConfigParser
import os

LOCALCHAR = "."

class LocalDict(object):
    # redefine the init call to use a filename instead
    def __init__(self, thefile=None):
        # we only have one section name for the config
        self.section = "settings"
        self.configfile = thefile
        
        # read from our config file, this will raise an exception if the file does not
        # exist.  Good for now.
        self.cp = ConfigParser.SafeConfigParser()
        
            
        if not os.path.isfile(self.configfile):
            self.cp.add_section(self.section)
        else:
            self.cp.readfp( open(self.configfile) )

 #   def __getitem__(self, key):
    def get(self, key):
        try:
            return self.cp.get(self.section, key)
        except ConfigParser.NoOptionError:
            return None

 #   def __setitem__(self, key, value):
    def set(self, key, value):
        self.cp.set(self.section, key, value)

    def save(self):
        self.cp.write(open(self.configfile,"w"))



class URLDict(object):
    
    def __init__(self, host, url, guid):
        self.host = host
        self.url  = url
        self.guid = guid
        
        # define our connection to 
        self.conn = httplib.HTTPConnection(self.host)
           
 #   def __getitem__(self, key):
    def get(self, key):
        ## call the URL to get the value
        self.conn.request("GET", self.url + self.guid + "/" + key + "/")
        response = self.conn.getresponse()

        if response.status != 200:
            return None
        
        return response.read()

 #   def __setitem__(self, key, value):
    def set(self, key, value):
        ## POST our new value.
        params = urllib.urlencode({'value': value})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        self.conn.request("POST", self.url + self.guid + "/" + key + "/", params, headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise Exception("Error setting value for %s, response = %s" % (key, response.read()) )


class Manager(object):
    """  
    Settings docstring 
    """
    LOCALCHAR = "."

    def __init__(self,thefile="settings.txt"):
        # a link to our local settings file, bootstrap.

        if not os.path.exists(thefile):
            raise Exception("%s does not exist in %s" % (thefile, os.getcwd()))

        self.LocalSettings = LocalDict(thefile)
        
        # our DB cache for all our settings from the URL /manager/settings
#        self.DBMSettings = anydbm.open("settings.db", "c")
        
        # URLSettings is none to start in case we don't have enough to bootstrap.
        self.URLSettings = None
#        if self._urlcheck():
#            self._urldict()
#            self._refresh()

    def __del__(self):
        # before we die, save our settings file
        if not self.LocalSettings == None:
            self.LocalSettings.save()

    def _urlcheck(self):
        """
        Checks to make sure we have everything we need to connect to our URL manager
        """
        if (self['.managerhost'] and self['.settingurl'] and self['.guid']):
            return True
        else:
            return False

    def _refresh(self):
        """
        refreshs all keys in the local DBM from the URL manager
        """
        # if we have all the values we need to hookup to the URL
#        for key in self.DBMSettings.keys():
#            if not key.startswith(LOCALCHAR):
#                self.DBMSettings[key] = self._urldict()[key]
        pass

    def _urldict(self):
        """ a semi-factory type method, return the URLSettings pointer if we have one
            otherwise, create it and return it
        """
        if not self.URLSettings == None:
            return self.URLSettings
        else:
            if self._urlcheck():
                # setup URLSettings as a URLDict with the proper settings
                self.URLSettings = URLDict( self['.managerhost'],
                                            self['.settingurl'],
                                            self['.guid'])
                return self.URLSettings
            else:
                raise Exception("Not enough settings for URL connection to manager")

 #   def __getitem__(self,key):
    def get(self,key):
        """ return the value of key, either from the local settings file, the local DB or the URL, 
            and then cache it locally in the DB """
            
        # if it's a 'setting.' then check the DBM, the settings.txt
        if key.startswith(LOCALCHAR):
#            if self.DBMSettings.has_key(key):
#                return self.DBMSettings[key]
#            else:
            # it's a setting, check the local file and then put it in the DBM

            if self.LocalSettings[key]:
#                    self.DBMSettings[key] = self.LocalSettings[key]
#                    return self.DBMSettings[key]
                return self.LocalSettings[key]
            else:
                #if it's not in the local, then we don't have it.
                return None
        else:
            # this is only a manager setting, see if we have it in the DBM otherwise, check the 
            # URL manager
#            if self.DBMSettings.has_key(key):
#                return self.DBMSettings[key]
#            else:
            # need to check the manager via our url    
            value = self._urldict()[key]
#            if value:
#                self.DBMSettings[key] = value
                
            return value

 #   def __setitem__(self,key, value):
    def set(self,key, value):
        """ set the value in the DB or URL or settings file.  if key starts with "setting." then it is
            stored locally only in the settings file
        """
        if key.startswith(LOCALCHAR):
            # if we are putting a local setting, store it in the DB and settings file.
            self.LocalSettings[key] = value
#            self.DBMSettings[key] = value
        else:
            # it's not something local only, so setup the DBM and put it on the URL
#            self.DBMSettings[key] = value
            self._urldict()[key] = value


# define settings here
settings = Manager()