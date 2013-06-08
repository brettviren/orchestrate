#!/usr/bin/env python
'''
Main application module interface to orchestrate
'''

import os
import itertools
import logging

import suite
import shim
from util import order_depends
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
    shim_path = ':'.join(filter(None, [extra, esp, csp, osp]))
    if not shim_path:
        raise ValueError, 'no shim path could be built'

    final = []
    for part in shim_path.split(':'):
        part = os.path.realpath(part)
        if part in final:
            continue
        if not os.path.exists(part):
            logging.warning('ignoring nonexistent shim directory: %s' % part)
            continue
        final.append(part)

    
    shim_path = ':'.join(final)
    
    if not shim_path:
        raise ValueError, 'no shim path remains'

    cfg.set('global','shim_path',shim_path)
    return shim_path


class Orchestrate(object):
    '''
    Interface object to core functionality.
    '''

    def __init__(self, config_files, suitename = None, shim_path = None, 
                 packages=None, steps=None):
        '''
        Create an Orchestrate object with one or more configuration
        files and possibly a suite name.
        
        Additional shim path segment can be set with <shim_path>.

        The list of packages and/or shims can be specified.  If None
        they will be set to the application defaults.
        '''

        self.cfg = suite.read_config(config_files)
        self.shim_path = build_shim_path(self.cfg, shim_path)
        self.varlist = suite.resolve(self.cfg, suitename)

        logging.info('Using shim path: %s' % (self.shim_path,))

        self.packages = packages or filter(None, [x.get('package_name') for x in self.varlist])
        self.steps = steps or shim.ShimPackage.steps
        self.shims = []
        self.package_shim = {}
        return

    def shim(self, package):
        '''
        Return shim object for <package>.
        '''
        return self.package_shim[package]

    def set_shims(self, packages = None, steps = None):
        '''
        Set the shims for the given packages/steps.  If left
        unspecified, the ones determined at construction time will be
        used.
        '''
        if packages:
            self.packages = packages
        if steps:
            self.steps = steps
            
        self.shims = []
        self.package_shim = {}
        for vars in self.varlist:
            pname = vars.get('package_name')
            if not pname in self.packages:
                continue
            #print '\n'.join(['%s:%s'%kv for kv in vars.items()])
            s = shim.ShimPackage(steps=self.steps, **vars)
            self.shims.append(s)
            self.package_shim[pname] = s

        logging.debug('Initial set of shims: %s' % ', '.join([x.name for x in self.shims]))
        shim.check_deps(self.shims)
        self.shims = order_depends(self.shims)
        logging.info('steps: %s' % ', '.join(self.steps))
        logging.info('packages: %s' % ', '.join(self.packages))
        return


    def step_package_items(self):
        '''Return sequence of (package, step) which first iterate over all
        packages for a given step.'''
        return map(lambda x: (x[1],x[0]), itertools.product(self.steps, self.packages))

    def package_step_items(self):
        '''Return sequence of (package, step) which first iterate over all
        steps for a given package.'''
        return itertools.product(self.packages, self.steps)

    items = package_step_items
    def set_iter_dominance(self, which):
        if which.startswith('step'):
            self.items = self.step_package_items
        if which.startswith('package'):
            self.items = self.package_step_items
        

    def __call__(self, package, step):
        '''
        Run the <step> for the <package>.
        '''
        shim = self.package_shim[package]
        shim.run(step)
