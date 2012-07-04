import logging
import os
from client.settingsmanager import settings
from client import utility

log = logging.getLogger(__name__)
loglevel = settings["log_level"] or 50 
log.setLevel(int(loglevel))

fm = logging.Formatter('%(asctime)s - %(levelname)s:%(filename)s.%(funcName)s(%(lineno)d) - %(message)s')

file_location = os.path.normpath(settings['.installdir'] +settings["log_path"] ) or "./"
utility.check_dir(file_location) 
fl=logging.FileHandler("%s/client.log" % file_location, mode="a")
fl.setFormatter(fm)
log.addHandler(fl)

if settings['log_stream']:
    ch = logging.StreamHandler()
    ch.setFormatter(fm)
    log.addHandler(ch)

log.info("Logging Started")