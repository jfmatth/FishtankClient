import unittest

from client.settingsmanager import settings

class testSettings(unittest.TestCase):
    
    def testLocal(self):
        self.assertFalse(settings[".registerurl"] == None,".registerurl missing")
        self.assertFalse(settings[".managerhost"] == None, ".managerhost missting")
        self.assertFalse(settings[".settingurl"] == None, ".settingurl missing")
    
    def testRequiredSettings(self):
        self.assertFalse(settings["filespec"] == None, "setting filespec missing")
        self.assertFalse(settings["dirspec"] == None, "setting dirspec missing")
        self.assertFalse(settings["temppath"] == None, "setting temppath missing")
        self.assertFalse(settings["dbpath"] == None, "setting dbpath missing")
        self.assertFalse(settings["cloud_files"] == None, "setting cloud_files missing")
        self.assertFalse(settings["cloud_meta"] == None, "setting cloud_meta missing")
        self.assertFalse(settings["tracker_ip"] == None, "setting tracker_ip missing")
#        self.assertFalse(settings["max_free_perc"] == None, "max_free_perc missing")
#        self.assertFalse(settings["min_free_gb"] == None, "min_free_gb missing")
#        self.assertFalse(settings["backupsize"] == None, "backupsize missing")
        self.assertFalse(settings["btctime"] == None, "btctime missing")
        self.assertFalse(settings["bfctime"] == None, "bfctime missing")
        self.assertFalse(settings["backupdrives"] == None, "backupdrives missing")
        self.assertFalse(settings["log_path"] == None, "log_path missing")
        self.assertFalse(settings["log_level"] == None, "log_level missing")
            
    def testPutandGet(self):
        pass    
    
#class testRegister(unittest.TestCase):
#    def testParameters(self):
#        self.failUnlessRaises(RegistrationError, register())

    
if __name__ == "__main__":
    unittest.main()
    