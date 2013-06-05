#!/usr/bin/env python
'''Provide interface to shim processes.

Shim objects encapsulate what is needed to build a package.

'''

import os
import proc

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

def package_shim_directories(package, version, pathlist):
    '''
    Return a list of directories of package shims.
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

        env = dict(os.environ)
        env['ORCH_PACKAGE_VERSION'] = version
        cmdstr = '%s %s' % (shell, vshim)
        rc = proc.run(cmdstr, env)
        if rc != 0:
            raise RuntimeError, 'Command returned non-zero error %d: %s' % (rc, cmdstr)

        ret.append(pdir)
        
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

def package_shim_dependencies(pathlist):
    '''
    Return the contents of the result file from the "dependencies"
    shim script as a list of (package name, optional version
    contraint) tuples
    '''
    dep_shim = package_shim_script('dependencies', pathlist)
    if not dep_shim: return []
        
    cmdstr = '%s %s' % (shell, dep_shim)
    env = dict(os.environ)
    env['ORCH_PACKAGE_VERSION'] = version
    rc = proc.run(cmdstr, env)
    if rc != 0:
        raise RuntimeError, 'Command returned non-zero error %d: %s' % (rc, cmdstr)
    
    return

class ShimScript(object):
    def __init__(self, script = None, **vars):
        self.script = script
        self.vars = vars

class ShimPackage(object):
    '''
    A shim package.
    '''

    steps = ['dependencies', 'environment', 'download',
             'unpack', 'prepare', 'build', 'install', 'validate']

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

        self.vars = vars

        psd = package_shim_directories(vars['package_name'], vars['package_version'], 
                                       vars['shim_path'].split(':'))

        self.shim_scripts = {}
        for step in self.steps:
            self.shim_scripts[step] = package_shim_script(step, psd)
        
        self.dep_setup = []
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

    def write_orch_environment(self, filename):
        '''
        Write ORCH_ environment variable settings to filename
        '''
        if os.path.exists(filename):
            return
        fp = open(filename, 'w')
        for var, val in self.vars.items():
            evar = 'ORCH_' + var.upper()
            fp.write('export %s="%s"\n' % (evar, val))
        fp.close()

    def orch_environment_file(self):
        '''
        Generate and return bash file to source to get this packages ORCH_ environment variables.
        '''
        fn = self.generate_runner_filename('orchenv')
        self.write_orch_environment(fn)
        return fn

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
        if step == 'environment':
            args = [self.generate_runner_filename('env')]
        if step == 'dependencies':
            args = [self.generate_runner_filename('dep')]

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
            fp.write('source %s\n' % dep)
        fp.write('source %s\n' % self.orch_environment_file())
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
