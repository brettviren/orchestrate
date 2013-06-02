#!/usr/bin/env python
'''Provide interface to shim processes.

Shim objects encapsulate what is needed to build a package.

'''

import os

class ShimScript(object):
    def __init__(self, script, dep_setup, **vars):
        self.script = script
        self.vars = vars
        self.dep_setup = dep_setup
        return

        

    def __call__(self):
        from subprocess import Popen, PIPE, STDOUT
        print 'Executing %s' % self.script
        proc = Popen(self.script, stdout=PIPE, stderr=STDOUT, 
                     universal_newlines=True, env=self.env)
        out, err = proc.communicate()
        print out
        assert proc.returncode == 0, 'Shim returned err %d (%s)' % (proc.returncode, self.script)
        return

    def __str__(self):
        return '<ShimScript %s>' % self.script


class ShimPackage(object):
    '''
    A shim package.
    '''

    steps = ['version', 'environment', 'dependencies', 'download',
             'unpack', 'prepare', 'build', 'install', 'validate']

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

    def get_runner(self, step):
        '''
        Return the runner script for given step.
        '''
        runner = self.runners.get(step)
        if runner: return runner

        args = []
        if step == 'environment':
            args = [self.generate_runner_filename('env')]
        if step == 'dependency':
            args = [self.generate_runner_filename('dep')]

        for maybe in [self.vars['shim_dir'], self.orch_dir]:
            script = os.path.join(maybe, step)
            if os.path.exists(script):
                runner = self.generate_runner_filename(step)
                self.prepare_runner(runner, script, *args)
                self.runners[step] = runner
                return runner

        raise ValueError, 'No runner found for step "%s" of %s/%s' % \
            (step, self.vars['package_name'], self.vars['package_version'])
        

    def run(self, step):
        runner = self.get_runner(step)
        from subprocess import Popen, PIPE, STDOUT
        print 'Executing %s' % self.script
        proc = Popen(runner, stdout=PIPE, stderr=STDOUT, 
                     universal_newlines=True, env=self.env)
        out, err = proc.communicate()
        print out
        assert proc.returncode == 0, 'Shim returned err %d (%s)' % (proc.returncode, runner)
        return


    def prepare_runner(self, filename, script, *args):
        '''
        Prepare runner script writing into file object.
        '''
        if os.path.exists(filename):
            return
        fp = open(filename,'w')

        funcs = os.path.join(self.orch_dir, 'bash/orchestrate.sh')

        fp.write('#!/bin/bash\n')
        fp.write('source %s\n' % funcs)
        for dep in self.dep_setup:
            fp.write('source %s\n' % dep)
        fp.write('source %s\n' % self.orch_environment_file())
        fp.write('exec %s %s\n' % (script, ' '.join(args)))
        return

    pass
