#!/usr/bin/env python
'''
Main application module interface to orchestrate
'''

import os
import suite
import shim
import logging
from ConfigParser import NoOptionError

def build_shim_path(cfg, extra=None):
    '''
    Build and single shim path from environment, configuration file
    and builtin, set it into the "global" section of the config
    object.
    '''
    esp = os.environ.get('ORCH_SHIM_PATH')
    csp = None
    try:
        csp = cfg.get('global','shim_path')
    except NoOptionError:
        pass
    osp = shim.orch_share_directory('shims')
    shim_path = ':'.join(filter(None, [extra, esp,csp,osp]))
    if not shim_path:
        raise ValueError, 'no shim path could be built'

    final = []
    for part in shim_path.split(':'):
        part = os.path.realpath(part)
        if not os.path.exists(part):
            logging.warning('ignoring nonexistent shim directory: %s' % part)
            continue
        final.append(part)
    shim_path = ':'.join(final)
    
    if not shim_path:
        raise ValueError, 'no shim path remains'

    cfg.set('global','shim_path',shim_path)
    return shim_path

def resolve_suite(cfg, suitename):
    'Return the list of shim objects for the given configuration and suite name'
    varlist = suite.resolve(cfg, suitename)
    shims = []
    for vars in varlist:
        s = shim.ShimPackage(**vars)
        shims.append(s)
    return shims

class Orchestrate(object):
    '''
    Interface object to core functionality.
    '''

    def __init__(self, config_files, suitename = None, shim_path = None):
        '''
        Create an Orchestrate object with one or more configuration
        files and possibly a suite name.
        '''
        self.cfg = suite.read_config(config_files)
        shim_path = build_shim_path(self.cfg, shim_path)
        logging.info('Using shim path: %s' % shim_path)
        self.shims = resolve_suite(self.cfg, suitename)
        shim.check_deps(self.shims)
        return
    

