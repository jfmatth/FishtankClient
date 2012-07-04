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

import urllib
import httplib
import ConfigParser
import os
import sys
import servicemanager

from client import utility

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

    def __getitem__(self, key):
        try:
            return self.cp.get(self.section, key)
        except ConfigParser.NoOptionError:
            return None

    def __setitem__(self, key, value):
        self.cp.set(self.section, key, value)
        
    def __delitem__(self,key):
        self.cp.remove_option(self.section, key)

    def save(self):
        self.cp.write(open(self.configfile,"w"))



class URLDict(object):
    def __init__(self, host, url, guid):
        self.host = host
        self.url  = url
        self.guid = guid

        # if the tracker is offline, then set this for now, and never check back in.
        self.offline = False
                           
    def __getitem__(self, key):
        if self.offline:
            raise
        else:
            try:
                conn = httplib.HTTPConnection(self.host)
        
                ## call the URL to get the value
                conn.request("GET", self.url + self.guid + "/" + key + "/")
                response = conn.getresponse()

                if response.status != 200:
                    return None
                
                return response.read()
            except:
                self.offline = True
# raise an exception, so that the calling manager knows that it should pull from cache.                
                raise


    def __setitem__(self, key, value):
        conn = httplib.HTTPConnection(self.host)
        
        ## POST our new value.
        params = urllib.urlencode({'value': value})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        conn.request("POST", self.url + self.guid + "/" + key + "/", params, headers)
        response = conn.getresponse()
        if response.status != 200:
            raise Exception("Error setting value for %s, response = %s" % (key, response.read()) )


class Manager(object):
    """  
    Settings docstring 
    """
    LOCALCHAR = "."

    # these are the minimum values we need in our settings file.
    RequiredSettings = ['.managerhost',
                        '.settingurl',
                        '.registerurl'
                        ]

    settings_filename = None    # holder for the filename of the settings.txt file

    def __init__(self,thefile="settings.txt"):
        # a link to our local settings file, bootstrap.

        self.settings_filename = thefile
        
        if not os.path.exists(self.settings_filename):
            raise Exception("%s does not exist in %s" % (self.settings_filename, os.path.dirname(self.settings_filename) ) )

        self.LocalSettings = LocalDict(self.settings_filename)
        self.LocalCache = LocalDict(self.settings_filename + ".cache")
        
        # URLSettings is none to start in case we don't have enough to bootstrap.
        self.URLSettings = None

    def __del__(self):
        # before we die, save our settings file
        if not self.LocalSettings == None:
            self.LocalSettings.save()
            self.LocalCache.save()

    def reset(self):
        """
        Reset the settings environment
        
        Removes all but the RequiredSettings values
        
        typically only called from the register.py module.
        """
        
        hold = {}
        
        # Save our current settings.
        for x in self.RequiredSettings:
            hold[x] = self.LocalSettings[x]
            
        # reset everything.
        self.LocalSettings.save()
        self.LocalSettings = None
        
        self.LocalCache.save()
        self.LocalCache = None
        
        os.remove(self.settings_filename)
        os.remove(self.settings_filename + '.cache')
        self.LocalSettings = LocalDict(self.settings_filename)
        self.LocalCache = LocalDict(self.settings_filename + ".cache")

        # re-populate.
        for x in hold:
            self.LocalSettings[x] = hold[x]


    def validate(self):
        """
        validates that we have all the necessary values
        """
        utility.validate_settings(self)

    def _urlcheck(self):
        """
        Checks to make sure we have everything we need to connect to our URL manager
        """
        if (self['.managerhost'] and self['.settingurl'] and self['.guid']):
            return True
        else:
            return False

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

    def __getitem__(self,key):
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
            try:    
                value = self._urldict()[key]
                if value:
                    self.LocalCache[key] = value
                    return value
                else:
                    if self.LocalCache[key]:
                        del self.LocalCache[key]
            except:
                # if an exception is raised, then we are offline.
                return self.LocalCache[key]

    def __setitem__(self,key, value):
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

# do some checking for our new environment
if servicemanager.RunningAsService():
    if "python.exe" in sys.executable.lower():
        sfile = os.path.join( os.path.dirname(sys.argv[0]),"settings.txt" )
    else:
        sfile = os.path.join( os.path.dirname(sys.executable), "settings.txt" )
else:    sfile = os.path.join(os.path.curdir, "settings.txt")

# define settings here
settings = Manager(thefile=sfile)

#utility.validate_settings(settings)