import logging

from argser.utils import _yellow

VERBOSE = 5  # logging level lower than DEBUG
logging.VERBOSE = VERBOSE
logging.addLevelName(VERBOSE, _yellow('VERBOSE'))
