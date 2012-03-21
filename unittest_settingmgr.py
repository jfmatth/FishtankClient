# tests-client.py

# test the settings manager

import unittest

from client import settingsmanager

MH = '.managerhost'
SU = '.settingurl'
GU = '.guid'
TR = 'tracker_ip'

class TestSettingsmanager(unittest.TestCase):
   
    def setUP(self):
        pass
    
    def tearDown(self):
        import os
        
        if os.path.exists('test-settings.txt'):
            os.remove('test-settings.txt')
   
    def test_1_LocalDict(self):
        s = settingsmanager.LocalDict(thefile="test-settings.txt")
        s.set("key1", "value1")
        self.assertEqual( s.get("key1"), "value1", "LocalDict get/set not working" )
        s.save()

    def test_2_URLDict(self):

        s = settingsmanager.LocalDict(thefile="settings.txt")

        self.assertNotEqual(s.get(MH), None, 'No %s specified' % MH) 
        self.assertNotEqual(s.get(SU), None, 'No %s specified' % SU) 
        self.assertNotEqual(s.get(GU), None, 'No %s specified' % GU)
        
        u = settingsmanager.URLDict(s.get(MH),
                                    s.get(SU),
                                    s.get(GU)
                                    )
        self.assertNotEqual(u.get('tracker_ip'), None, 'No Tracker IP')
        
    def test_3_Manager(self):
        # this makes sure the manager, which uses both of the above tests, works too.
        #
        #self.assertRaises(Exception, settingsmanager.Manager(thefile="none.txt"), Exception, "Fail")
        
        m = settingsmanager.Manager()

        # make sure the local settings work first
        self.assertNotEqual(m.get(MH), None, "%s is None" % MH)
        m.set('.test', "testvalue")
        self.assertNotEqual(m.get('.test'), None)
        
        # does going to the server work?
        self.assertNotEqual(m.get(TR), None, 'No %s ' % TR)
        
if __name__=="__main__":
    unittest.main()