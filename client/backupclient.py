# our first attempt at a backup client.

import backup
import proxy
import torrent

def main():

    settings = proxy.URLProxy()

    if settings['clouddir'] == None:
        raise Exception("clouddir not defined")

    if settings['datadir'] == None:
        raise Exception("missing datadir")
    
    if settings['tracker'] == None:
        raise Exception("missing tracker")
    
    # start up a cloud?
    cloud = torrent.Cloud(torr_dir=settings["clouddir"],
                          data_dir=settings["datadir"],
                          tracker_ip=settings['tracker'])
    

    # backup our files.
    b = backup.encryptedBackup(settings)

    print "Backing up..."

    b.go()

    print "Sending to torrent"

if __name__ == "__main__":
    main()
    
