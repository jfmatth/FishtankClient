from client.settingsmanager import settings

import sys

def main(path=None):
    # build a settings.txt file to output directory
    if path == None:
        return 10

    f = open(path + "settings.txt", "w")
    f.write("[settings]" + "\n")
    f.write(".registerurl=" + settings[".registerurl"] + "\n") 
    f.write(".managerhost=" + settings[".managerhost"] + "\n")
    f.write(".settingurl=" + settings[".settingurl"] + "\n")
    f.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "No destination folder given."
        sys.exit(10)
    
    main(sys.argv[1])
    
    