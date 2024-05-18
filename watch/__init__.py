import logging

__version__ = "0.2.0"

logging.getLogger("urllib3").propagate = False

format = logging.Formatter(fmt="%(levelname)-8s %(message)s")

handler = logging.StreamHandler()
handler.setFormatter(format)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
