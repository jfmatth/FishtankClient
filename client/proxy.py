# proxy class


import httplib, urllib

class Proxy(object):
    
    """ runs like a dictionary, but we override the get/set item methods to do our own thang
    
    """
           
    def __getitem__(self, key):
        pass
    
    def __setitem__(self, key, value):
        pass

# LocalProxy
class LocalProxy(Proxy):
    # redefine the init call to use a filename instead
    def __init__(self, thefile=None, create=False):
        # we only have one section name for the config
        self.section = "settings"
        self.configfile = thefile
        
        # read from our config file, this will raise an exception if the file does not
        # exist.  Good for now.
        self.cp = ConfigParser.SafeConfigParser()
        if create:
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

    def save(self):
        self.cp.write(open(self.configfile,"w"))
    
# URLProxy, is the main interface to our tracker / manager for all settings for this client.
# it will need to know how to get our secretkey and use it when querying or posting new values.
class URLProxy(Proxy):
    
    def __init__(self):
        # open a link to the tracker (using a localproxy) and read in all our
        # settings for this client.
        self.localsettings = "settings.txt"
        self.config = LocalProxy(self.localsettings)

        # make sure we have the settings we need 
        if not self.config["managerhost"]:
            raise Exception('No "managerhost" setting found')
        if not self.config["settingurl"]:
            raise Exception('No "settingurl" setting found')
        if not self.config["guid"]:
            raise Exception('no "guid" value found in settings file')

        # define our connection to 
        self.conn = httplib.HTTPConnection(self.config["managerhost"])
        
    def __getitem__(self, key):
        ## call the URL to get the value
        self.conn.request("GET", self.config["settingurl"] + self.config["guid"] + "/" + key + "/")
        response = self.conn.getresponse()

        if response.status != 200:
            return None
        
        return response.read()

    def __setitem__(self, key, value):
        ## POST our new value.
        params = urllib.urlencode({'value': value})
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
        self.conn.request("POST", self.config["settingurl"] + self.config["guid"] + "/" + key + "/", params, headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise Exception("Error setting value for %s, response = %s" % (key, response.read()) )
        