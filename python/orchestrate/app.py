#!/usr/bin/env python
'''
Main application module interface to orchestrate
'''

import os
import suite
import shim
from ConfigParser import NoOptionError

class Orchestrate(object):
    '''
    Interface object to core functionality.
    '''

    def __init__(self, config_files, suitename = None):
        '''
        Create an Orchestrate object with one or more configuration
        files and possibly a suite name.
        '''
        cfg = suite.read_config(config_files)

        # Make a single shim path from environment, configuration file and builtin
        esp = os.environ.get('ORCH_SHIM_PATH')
        csp = None
        try:
            csp = cfg.get('global','shim_path')
        except NoOptionError:
            pass
        osp = shim.orch_share_directory('shims')
        shim_path = ':'.join(filter(None, [esp,csp,osp]))
        if shim_path:
            cfg.set('global','shim_path',shim_path)

        self.vars = suite.resolve(cfg, suitename)
        self.shims = []
        for vars in self.vars:
            s = shim.ShimPackage(**vars)
            self.shims.append(s)
        return
    

