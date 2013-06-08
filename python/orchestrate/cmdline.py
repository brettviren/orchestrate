#!/usr/bin/env python
'''
Functions following a command line interface to some internal utilities.

They all takes string args, may print directly and return integer error codes.
'''

import get

def cmdline_download(*args):
    '''
    download <url> <targetdir> [<result>]
    '''
    get(*args)
    return 0
