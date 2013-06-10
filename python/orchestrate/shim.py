#!/usr/bin/env python
'''Provide interface to shim processes.

Shim objects encapsulate what is needed to build a package.

'''

import os
import proc
import tempfile
import logging
from util import version_consistent, orch_share_directory, git_repo, cd
import download, unpack
shell = '/bin/bash'


def package_shim_directories(pathlist, named, env = None):
    '''
    Return a list of directories from the given <pathlist> which
    contain directory in <named> (a string or list of strings).  If a
    "version" shim script is found in a directory, run it in the given
    environment <env> and only keep the directory if a zero error code
    is returned.
    '''
    if isinstance(named, basestring):
        named = [named]

    ret = []
    for name in named:
        for path in pathlist:
            pdir = os.path.join(path, name)
            #logging.debug('Checking shim directory %s' % pdir)
            if not os.path.exists(pdir):
                #logging.debug('Ignoring nonexistent shim directory %s' % pdir)
                continue

            vshim = os.path.join(pdir, 'version')

            # no version shim script, assume applicable
            if not os.path.exists(vshim):
                #logging.debug('Using versionless shim directory %s' % pdir)
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

def package_shim_dependencies(script, env):
    '''
    Return the package dependencies by running the first
    "dependencies" shim script found in <pathlist> in the given <env>
    environment.  Return a list of (<package>, <optional constraint>)
    tuples.
    '''
    
    # for debugging
    pv = '%s/%s' % (env['ORCH_PACKAGE_NAME'], env['ORCH_PACKAGE_VERSION'])

    if not script: 
        logging.debug('no dependencies shim for package %s' % pv)
        return []
        
    fd, fn = tempfile.mkstemp()

    cmdstr = ' '.join([shell, script, fn])
    rc = proc.run(cmdstr, env=env)
    if rc != 0:
        raise RuntimeError, '%s dependencies command returned non-zero error %d: %s' % \
            (pv, rc, cmdstr)
    
    #os.close(fd)
    fd = open(fn)
    ret = []
    for line in fd.readlines():
        line = line.strip()
        #logging.debug('%s dependency line: "%s"' % (pv, line))
        if not line: continue
        line = line.split(' ',1)
        ret.append((line[0], line[1:]))
    os.remove(fn)
    logging.debug('dependencies for package %s: %s from %s' % (pv, str(ret), script))
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

def shims_in(shimlist, name, constraint = None):
    '''
    Return list of all shim objects in <shimlist> with the given name.
    If a constraint is given then a shim must satisfy it to be
    returned.
    '''
    ret = []
    for s in shimlist:
        if name != s.name:
            continue
        if not constraint or version_consistent(s.version, constraint):
            ret.append(s)
            continue
        continue
    return ret

def check_deps(shimlist):
    '''Check that all shims in <shimlist> have dependencies and any
    version constraints satisfied by another shim in <shimlist>.
    Raises ValueError if check fails'''
    for s in shimlist:
        for dname, dconstraint in s.dep_ver:
            dshims = shims_in(shimlist, dname, dconstraint)
            if not dshims:
                msg = 'check dependency failed: no package shim for "%s" needed to satisfy "%s" (constraint="%s") from dependencies file: %s' % (dname, s.name, dconstraint, s.shim_scripts.get('dependencies', '(none)'))
                raise ValueError, msg
            continue
        continue
    return


def order_deps(shimlist):
    '''
    Return a new shimlist which is ordered so that no shim comes before any that it depends on.
    '''
    

class ShimPackage(object):
    '''
    A shim package.
    '''

    # ordered steps
    steps = ['download', 'unpack', 'prepare', 'build', 'install', 'postinst', 'validate']

    # map a step to where it runs from by default
    rundirs = {
        'unpack':        'source_dir',
        'prepare':       'build_dir',
        'build':         'build_dir',
        'install':       'build_dir',
        'postinst':      'install_dir',
        'validate':      'install_dir',
    }

    # required variables
    required = ['package_name', 'package_version', 'source_url', 'download_dir',
                'source_dir', 'unpacked_dir', 'build_dir', 'install_dir',
                'shim_path']

    def __init__(self, steps = None, **vars):

        if steps:
            self.steps = steps

        missing = set(self.required).difference(vars.keys())
        if missing:
            raise ValueError, 'Shim missing variables: %s' % (', '.join(missing),)

        pname = vars['package_name']

        # find packages - calls the "version" shim scripts
        self.vars = vars
        env = {'ORCH_%s'%k.upper():v for k,v in vars.items()}

        shim_names = []
        for varname in ['shim_name','package_name','shim_fallback']:
            n = vars.get(varname)
            if not n: continue
            for maybe in [x.strip() for x in n.split(',')]:
                if maybe not in shim_names:
                    shim_names.append(maybe)

        shim_path = vars['shim_path']
        psd = package_shim_directories(shim_path.split(':'), 
                                       shim_names, env)
        logging.debug('Using shim directories for %s: %s' % (pname, ':'.join(psd)))

        # Determine the dependencies, if any, for this package
        dep_shim = package_shim_script('dependencies', psd)
        self.dep_ver = package_shim_dependencies(dep_shim, env)
        self.dep_setup = []

        # resolve shim script locations 
        self.shim_scripts = {}
        self.shim_scripts['dependencies'] = dep_shim
        for step in self.steps:
            self.shim_scripts[step] = package_shim_script(step, psd)

        # Write this package's orchestrate variables to environment setup script
        self.orch_env_file = self.generate_runner_filename('orchenv')
        self.orch_unenv_file = self.generate_runner_filename('orchunenv')
        fp = open(self.orch_env_file, 'w')
        unfp = open(self.orch_unenv_file, 'w')
        for kv in env.items():
            fp.write('export %s="%s"\n' % kv)
            unfp.write('unset %s\n' % kv[0])
        fp.close()
        unfp.close()

        # Write this package's own environment via the shim script
        self.pkg_env_file = self.generate_runner_filename('{package_name}env'.format(**vars))
        fp = open(self.pkg_env_file,'w')
        fp.write('source %s\n' % os.path.join(orch_share_directory('bash'), 'orchestrate.sh'))
        fp.write('source %s\n' % self.orch_env_file)
        fp.close()
        package_shim_environment(self.pkg_env_file, psd, env)
        fp = open(self.pkg_env_file,'a')
        fp.write('source %s\n' % self.orch_unenv_file)
        fp.close()

        #self.runners = {s:r for s,r in zip(self.steps,map(self.make_runner, self.steps))}
        self._runners_cache = {}
        return


    @property
    def name(self):
        'Get the name of the package this shims'
        return self.vars['package_name']
    @property
    def version(self):
        'Get the version string of the package this shims'
        return self.vars['package_version']
    @property
    def depends(self):
        'Return list of names of shims on which this one depends'
        return map(lambda x: x[0], self.dep_ver)

    def generate_runner_filename(self, step):
        '''
        Generate a runner file name for given step.  Runners go in build_dir/orch/.
        '''
        odir = os.path.join(self.vars['build_dir'],'orch')
        if not os.path.exists(odir):
            os.makedirs(odir)
        return os.path.join(odir, step)

    def get_rundir(self, step):
        '''
        Return the directory from which to run the shim
        '''
        rundir = self.rundirs.get(step, 'build_dir')
        return self.vars[rundir]

    def run(self, step):
        runner = self._runners_cache.get(step)
        if runner:
            return runner()
        runner = self.make_runner(step)
        if not runner:
            return
        self._runners_cache[step] = runner
        return runner()


    def run_bogus(self):
        '''
        A bogus built in
        '''
        msg = 'bogus runner called on {package_name}/{package_version}'.format(**self.vars)
        logging.warning(msg)
        return

    def run_download(self):
        '''
        Download the <source_url> to the <download_dir>.
        '''
        with cd(self.get_rundir('download')):
            rc = download.get(self.vars['source_url'],self.vars['download_dir'], 
                              self.vars.get('download_final'))
        return rc
        
    def run_unpack(self):
        '''Unpack source into <source_dir>.  Source is taken from
        <source_package> which may be a zip or tar file (with various
        compression methods supported) or a git directory.  If it is a
        git directory the <source_tag> is used to determine what is
        checked out into <source_dir>.  If <unpacked_dir> or
        <unpacked_reldir> (relative to <source_dir>) are defined they
        will be used as indication that the unpacking has already been
        done.
        '''
        dldir = self.vars.get('download_dir')
        src = self.vars.get('source_package')
        if not src.startswith('/'):
            src = os.path.join(dldir, src)
        dst = self.vars.get('source_dir')
        if not (src and dst):
            raise ValueError, 'Need both a source_package (got: "%s") and a source_dir (got: "%s" for unpacking' % (src,dst)

        creates = self.vars.get('unpacked_dir')
        if not creates:
            creates = self.vars.get('unpacked_reldir')
            if creates:
                creates = os.path.join(dst, creates)
        dst,creates = os.path.split(creates)

        logging.debug('builtin unpack: src:%s dst:%s creates:%s' % (src,dst,creates))

        isgit = git_repo(src)
        if isgit:
            tag = self.vars.get('source_tag','HEAD')
            return unpack.ungit(isgit, dst, creates, tag)
        if src.endswith('.zip'):
            return unpack.unzip(src, dst, creates)
        return unpack.untar(src, dst, creates)

    def make_runner(self, step):
        '''
        Make a runner for given step.
        '''
        script = self.shim_scripts.get(step)
        if not script:          # maybe a builtin?
            meth = self.__class__.__dict__.get('run_' + step)
            if not meth:
                return
            def meth_curry():
                return meth(self)
            return meth_curry

        args = []
        runner = self.generate_runner_filename(step)
        rundir = self.get_rundir(step)
        self.prepare_runner(runner, script, rundir, *args)
        def runner_curry():
            cmdstr = '%s %s' % (shell, runner)
            logging.info('Executing shim script %s' % cmdstr)

            rc = proc.run(cmdstr)
            if rc != 0:
                msg = 'Failed to run %s of %s/%s' % \
                      (runner, self.vars['package_name'], self.vars['package_version'])
                raise RuntimeError, msg
        return runner_curry

    def prepare_runner(self, filename, script, rundir, *args):
        '''
        Prepare runner script writing into file object.
        '''
        # fixme: make this optional dependent on a "force" value
        #if os.path.exists(filename):
        #    return
        fp = open(filename,'w')

        funcs = os.path.join(orch_share_directory('bash'),  'orchestrate.sh')

        fp.write('#!/bin/bash\n')
        #fp.write('set -x\n')
        fp.write('source %s\n' % funcs)
        for dep in self.dep_setup:
            fp.write('source %s\n' % dep[0])
        fp.write('source %s\n' % self.orch_env_file)
        if rundir:
            fp.write('assuredir %s\n' % rundir)
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
