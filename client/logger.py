import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

fm = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')

fl=logging.FileHandler("z.log", mode="w")
fl.setFormatter(fm)
fl.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(fm)

log.addHandler(fl)
log.addHandler(ch)
log.info("Logging Started")