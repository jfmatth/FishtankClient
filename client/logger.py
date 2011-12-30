import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
fm = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
fl = logging.FileHandler("z.log", mode="w")
fl.setFormatter(fm)
log.addHandler(fl)
log.info("Logging Started")