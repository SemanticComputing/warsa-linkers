from arpa_linker.link_helper import process_stage
import logging
import sys

logger = logging.getLogger('arpa_linker.arpa')

if __name__ == '__main__':

    process_stage(sys.argv, log_level='INFO')
