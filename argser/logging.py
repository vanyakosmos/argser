import logging

from termcolor import colored

VERBOSE = 5  # logging level lower than DEBUG
logging.VERBOSE = VERBOSE
logging.addLevelName(VERBOSE, colored('VERBOSE', 'blue'))
