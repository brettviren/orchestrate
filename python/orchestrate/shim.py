#!/usr/bin/env python
'''Provide interface to shim processes.

Shim objects encapsulate what is needed to build a package.

'''

import os
import proc
import tempfile
import logging

shell = '/bin/bash'


def orch_share_directory(subdir):
    'Find <subdir> in installed app area'
    venvdir = os.environ.get('VIRTUAL_ENV')
    if venvdir:                 # installed in virtual env
        maybe = os.path.join(venvdir, 'share/orchestrate', subdir)
        if os.path.exists(maybe):
            return maybe

    # in-source
    maybe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),subdir)
    if os.path.exists(maybe):
        return maybe

    return None

def package_shim_directories(pathlist, package, env = None):
    '''
    Return a list of directories from the given <pathlist> which
    contain a <package> shim script.  If a "version" shim script is
    found, run it in the given environment <env> and only keep that
    package shim if the "version" shim script returns 0 error code.
    '''
    ret = []
    for path in pathlist:
        pdir = os.path.join(path,package)
        if not os.path.exists(pdir):
            continue

        vshim = os.path.join(pdir, 'version')

        # no version shim script, assume applicable
        if not os.path.exists(vshim):
            ret.append(pdir)
            continue

        cmdstr = '%s %s' % (shell, vshim)
        rc = proc.run(cmdstr, env=env)
        if rc == 0:
            ret.append(pdir)

        continue
        
    return ret
    
def package_shim_script(name, pathlist):
    '''
    Return the first instance of a shim script of given <name> in <pathlist>
    '''
    for pdir in pathlist:
        maybe = os.path.join(pdir, name)
        if os.path.exists(maybe):
            return maybe
    return None

def package_shim_dependencies(pathlist, env):
    '''
    Return the package dependencies by running the first
    "dependencies" shim script found in <pathlist> in the given <env>
    environment.  Return a list of (<package>, <optional constraint>)
    tuples.
    '''
    dep_shim = package_shim_script('dependencies', pathlist)
    if not dep_shim: 
        return []
        
    fd, fn = tempfile.mkstemp()

    cmdstr = ' '.join([shell, dep_shim, fn])
    rc = proc.run(cmdstr, env=env)
    if rc != 0:
        raise RuntimeError, 'Command returned non-zero error %d: %s' % (rc, cmdstr)
    
    os.close(fd)
    fd = open(fn)
    ret = []
    for line in fd.readlines():
        line = line.strip()
        if not line: continue
        line = line.split(' ',1)
        ret.append((line[0], line[1:]))
    os.remove(fn)
    return ret

def package_shim_environment(filename, pathlist, env):
    '''
    Produce the package environment set up in the given <filename> by
    calling the "environment" shim script.
    '''
    logging.debug('generating env file %s' % filename)
    env_shim = package_shim_script('environment', pathlist)
    if not env_shim: 
        logging.debug('No environment shim script for %s' % env['ORCH_PACKAGE_NAME'])
        return 
        
    if not os.path.exists(env_shim):
        logging.debug('Environment shim script does not exist: %s' % env_shim)
        return

    cmdstr = ' '.join([shell, env_shim, filename])
    rc = proc.run(cmdstr, env=env)
    if rc != 0:
        raise RuntimeError, 'Command returned non-zero error %d: %s' % (rc, cmdstr)

    return


class ShimPackage(object):
    '''
    A shim package.
    '''

    steps = ['download', 'unpack', 'prepare', 'build', 'install', 'validate']

    rundirs = {
        'unpack':        'source_dir',
        'prepare':       'build_dir',
        'build':         'build_dir',
        'install':       'build_dir',
        'validate':      'install_dir',
    }

    required = ['package_name', 'package_version', 'package_url',
                'source_dir', 'unpacked_dir', 'build_dir', 'install_dir',
                'shim_path']

    def __init__(self, **vars):

        missing = set(self.required).difference(vars.keys())
        if missing:
            raise ValueError, 'Shim missing variables: %s' % (', '.join(missing),)

        # find packages - calls the "version" shim scripts
        self.vars = vars
        env = {'ORCH_%s'%k.upper():v for k,v in vars.items()}
        psd = package_shim_directories(vars['shim_path'].split(':'), 
                                       vars['package_name'], env)

        # Determine the dependencies, if any, for this package
        self.dep_ver = package_shim_dependencies(psd, env)
        self.dep_setup = []

        # resolve shim script locations 
        self.shim_scripts = {}
        for step in self.steps:
            self.shim_scripts[step] = package_shim_script(step, psd)

        # Write this package's orchestrate variables to environment setup script
        self.orch_env_file = self.generate_runner_filename('orchenv')
        fp = open(self.orch_env_file, 'w')
        for kv in env.items():
            fp.write('export %s="%s"\n' % kv)
        fp.close()

        # Write this package's own environment via the shim script
        self.pkg_env_file = self.generate_runner_filename('{package_name}env'.format(**vars))
        package_shim_environment(self.pkg_env_file, psd, env)

        self.runners = {}       # step->script to run
        return

    def get_gen_dir(self):
        odir = os.path.join(self.vars['build_dir'],'orch')
        if not os.path.exists(odir):
            os.makedirs(odir)
        return odir

    def generate_runner_filename(self, step):
        '''
        Generate a runner file name for given step.  Runners go in build_dir/orch/.
        '''
        return os.path.join(self.get_gen_dir(), step)

    def get_rundir(self, step):
        '''
        Return the directory from which to run the shim
        '''
        rundir = self.rundirs.get(step, 'build_dir')
        return self.vars[rundir]

    def get_runner(self, step):
        '''
        Return the runner script for given step.
        '''
        runner = self.runners.get(step)
        if runner: return runner

        script = self.shim_scripts[step]
        if not script:
            return None

        args = []

        runner = self.generate_runner_filename(step)
        rundir = self.get_rundir(step)
        self.prepare_runner(runner, script, rundir, *args)
        self.runners[step] = runner
        return runner

    def run(self, step):
        runner = self.get_runner(step)
        cmdstr = '%s %s' % (shell, runner)
        print 'Executing %s' % cmdstr

        rc = proc.run(cmdstr)
        if rc != 0:
            msg = 'Failed to run %s of %s/%s' % \
                (runner, self.vars['package_name'], self.vars['package_version'])
            raise RuntimeError, msg
        return


    def prepare_runner(self, filename, script, rundir, *args):
        '''
        Prepare runner script writing into file object.
        '''
        if os.path.exists(filename):
            return
        fp = open(filename,'w')

        funcs = os.path.join(orch_share_directory('bash'),  'orchestrate.sh')

        fp.write('#!/bin/bash\n')
        #fp.write('set -x\n')
        fp.write('source %s\n' % funcs)
        for dep in self.dep_setup:
            fp.write('source %s\n' % dep[0])
        fp.write('source %s\n' % self.orch_env_file)
        if rundir:
            fp.write('goto %s\n' % rundir)
        fp.write('''if head -1 {script} | grep -q /bin/bash ; then 
    source {script} {argstr}
else 
    exec %s %s
fi
'''.format(script=script, argstr = ' '.join(args)))
        if rundir:
            fp.write('goback\n')
        return

    pass
