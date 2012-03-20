# tests-client.py

# test the settings manager

import unittest

from client import settingsmanager

class TestSettingsmanager(unittest.TestCase):

   
    def test_LocalDict(self):
        s = settingsmanager.LocalDict(thefile="test-settings.txt")
        s.set("key1", "value1")
        self.assertEqual( s.get("key1"), "value1", "Setting not working" )
        s.save()

    def test_URLDict(self):
    


if __name__=="__main__":
    unittest.main()