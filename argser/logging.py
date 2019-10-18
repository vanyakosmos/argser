import logging

from argser.utils import colors

VERBOSE = 5  # logging level lower than DEBUG
logging.VERBOSE = VERBOSE
logging.addLevelName(VERBOSE, colors.yellow('VERBOSE'))
