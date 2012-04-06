import logging
import os
from client.settingsmanager import settings

log = logging.getLogger(__name__)
loglevel = settings["log_level"] or 50 
log.setLevel(int(loglevel))

fm = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')

file_location = os.path.normpath(settings['.installdir'] +settings["log_path"] ) or "./" 
fl=logging.FileHandler("%s/client.log" % file_location, mode="w")
fl.setFormatter(fm)
log.addHandler(fl)

if settings['log_stream']:
    ch = logging.StreamHandler()
    ch.setFormatter(fm)
    log.addHandler(ch)

log.info("Logging Started")