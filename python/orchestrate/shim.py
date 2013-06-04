#!/usr/bin/env python
'''Provide interface to shim processes.

Shim objects encapsulate what is needed to build a package.

'''

import os

    

def locate_path(subpath, pathlist):
    '''
    Return first occurrence of a file named <subpath> found in an
    element of the directory list <pathlist>.  A match is returned as
    a full path or None.
    '''
    for p in pathlist:
        maybe = os.path.join(p, subpath)
        if os.path.exists(maybe):
            return maybe
    return None

class ShimPackage(object):
    '''
    A shim package.
    '''

    shell = '/bin/bash'
    steps = ['version', 'environment', 'dependencies', 'download',
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
                'shim_dir']

    def __init__(self, **vars):

        missing = set(self.required).difference(vars.keys())
        if missing:
            raise ValueError, 'Shim missing variables: %s' % (', '.join(missing),)
        self.orch_dir = vars.get('orch_dir', 
                                 os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.vars = vars

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

        args = []
        if step == 'environment':
            args = [self.generate_runner_filename('env')]
        if step == 'dependencies':
            args = [self.generate_runner_filename('dep')]

        for maybe in [self.vars['shim_dir'], self.orch_dir]:
            script = os.path.join(maybe, step)
            if os.path.exists(script):
                runner = self.generate_runner_filename(step)
                rundir = self.get_rundir(step)
                self.prepare_runner(runner, script, rundir, *args)
                self.runners[step] = runner
                return runner

        raise ValueError, 'No runner found for step "%s" of %s/%s' % \
            (step, self.vars['package_name'], self.vars['package_version'])
        

    def run(self, step):
        runner = self.get_runner(step)
        from subprocess import Popen, PIPE, STDOUT
        cmdline = [self.shell, runner]
        print 'Executing %s' % ' '.join(cmdline)
        try:
            proc = Popen(cmdline, stdout=PIPE, stderr=STDOUT, 
                         universal_newlines=True)
        except OSError:
            print 'Failed to run %s of %s/%s' % \
                (runner, self.vars['package_name'], self.vars['package_version'])
            raise
        out, err = proc.communicate()
        print out
        assert proc.returncode == 0, 'Shim returned err %d (%s)' % (proc.returncode, runner)
        return


    def prepare_runner(self, filename, script, rundir, *args):
        '''
        Prepare runner script writing into file object.
        '''
        if os.path.exists(filename):
            return
        fp = open(filename,'w')

        funcs = os.path.join(self.orch_dir, 'bash/orchestrate.sh')

        fp.write('#!/bin/bash\n')
        #fp.write('set -x\n')
        fp.write('source %s\n' % funcs)
        for dep in self.dep_setup:
            fp.write('source %s\n' % dep)
        fp.write('source %s\n' % self.orch_environment_file())
        if rundir:
            fp.write('runcmd pushd %s >/dev/null 2>&1\n' % rundir)
        fp.write('''if head -1 {script} | grep -q /bin/bash ; then 
    source {script} {argstr}
else 
    exec %s %s
fi
'''.format(script=script, argstr = ' '.join(args)))
        if rundir:
            fp.write('runcmd popd > /dev/null 2>&1\n')
        return

    pass
