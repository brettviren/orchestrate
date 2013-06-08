#!/usr/bin/env python
'''
Some thing common to a few tests
'''

import logging

logging.basicConfig(filename='/dev/stdout',
                    level=logging.DEBUG,
                    format='%(levelname)-7s %(message)s (%(filename)s:%(lineno)d)')
