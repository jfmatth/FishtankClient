import unittest

from client.settingsmanager import settings
from register import register, RegistrationError

class testSettings(unittest.TestCase):
    
    def testLocal(self):
        self.assertFalse(settings[".registerurl"] == None,".registerurl missing")
        self.assertFalse(settings[".managerhost"] == None, ".managerhost missting")
        self.assertFalse(settings[".settingurl"] == None, ".settingurl missing")
    
    def testRequiredSettings(self):
        self.assertFalse(settings["block_sz"] == None,"setting block_sz missing")
        self.assertFalse(settings["filespec"] == None, "setting filespec missing")
        self.assertFalse(settings["temppath"] == None, "setting temppath missing")
        self.assertFalse(settings["dbpath"] == None, "setting dbpath missing")
        self.assertFalse(settings[".publickey"] == None, "setting .publickey missing")
        self.assertFalse(settings["cloud_files"] == None, "setting cloud_files missing")
        self.assertFalse(settings["cloud_meta"] == None, "setting cloud_meta missing")
        self.assertFalse(settings["tracker_ip"] == None, "setting tracker_ip missing")
        self.assertFalse(settings["max_free_perc"] == None, "max_free_perc missing")
        self.assertFalse(settings["min_free_gb"] == None, "min_free_gb missing")
    
    def testPutandGet(self):
        pass    
    
#class testRegister(unittest.TestCase):
#    def testParameters(self):
#        self.failUnlessRaises(RegistrationError, register())

    
if __name__ == "__main__":
    unittest.main()
    