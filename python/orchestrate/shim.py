#!/usr/bin/env python
'''Provide interface to shim processes.

Shim objects encapsulate what is needed to build a package.

'''

import os
import proc
import tempfile
import logging
from util import version_consistent, orch_share_directory, git_repo, cd, is_bash
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
    ret = []
    fullenv = dict(os.environ)
    if env:
        fullenv.update(env)
    for name in named:
        name = name.strip()     # be nice
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
            print 'cmdstr="%s", env=:' % cmdstr
            for k,v in fullenv.iteritems():
                #print '(%s)%s = (%s)%s' % (type(k),k, type(v), v)
                assert isinstance(k,basestring)
                assert isinstance(v,basestring)
            rc = proc.run(cmdstr, env=fullenv)
            if rc == 0:
                ret.append(pdir)

            continue
        
    return ret
    
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
        ret.append((line[0], line[1:] or ''))
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


    
def emit_source(funcfile, args = ""):
    return '''if [ -f {funcfile} ] ; then
    source {funcfile} {args}
else
    fail "No such file: {funcfile}"
    exit 1
fi
'''.format(**locals())


class ShimPackage(object):
    '''
    Encapsulate a packages shims.  Stepping through them installs the package.
    '''

    # ordered steps
    steps = ['version', 'dependencies', 
             'environment', 'download', 'unpack', 'prepare',
             'build', 'install', 'postinst', 'validate']

    # map a step to where it runs from by default
    rundirs = {
        'unpack':        'source_dir',
        'prepare':       'build_dir',
        'build':         'build_dir',
        'install':       'build_dir',
        'postinst':      'install_dir',
        'validate':      'install_dir',
    }

    # required keyword variables
    required = ['package_name', 'package_version', 'source_url', 'download_dir',
                'source_package', 'source_dir', 'unpacked_dir', 'build_dir', 'install_dir',
                'shim_path',    # colon-separated list of directories holding package shims
                'shim_names',   # comma-separated list of package shim names
                ]

    generated_filetypes = ['orch_setenv', 'orch_unsetenv', 'package_setenv']


    def __init__(self, steps = None, **myvars):
        '''
        Create a ShimPackage.  This will then know the steps it is
        configured to run, the directories in which to find shim
        scripts and the name/version pairs of all dependencies.  

        Construction should be followed up with a call to .setup()
        once all ShimPackage objects in the suite are created.
        '''

        missing = set(self.required).difference(myvars.keys())
        if missing:
            raise ValueError, 'Shim missing variables: %s' % (', '.join(missing),)

        self.force = True
        if steps:               # allow limiting which steps to do
            self.steps = steps
        self.vars = myvars
        self.orch_env = {'ORCH_%s'%k.upper():v for k,v in self.vars.items()}

        # Maybe calls the "version" script(s) in the orch_env.  This
        # is done special as we use it to determine which directories
        # hold shim scripts which can be applied to the requested version.
        self.psd = package_shim_directories(myvars['shim_path'].split(':'),
                                            myvars['shim_names'].split(','),
                                            self.orch_env)
        logging.debug('Using shim directories for %s: %s' % (self.name, ':'.join(self.psd)))

        # Determine the dependencies, if any, for this package in the
        # form of package name and version.  This is also done in
        # special, in a limited environment as we do not yet know the
        # dependencies needed to make the full environment
        dep_shim = self.package_shim_script('dependencies')
        self.dep_pkgcon = package_shim_dependencies(dep_shim, self.orch_env)

        self.step_runners = {}
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
        return map(lambda x: x[0], self.dep_pkgcon)


    def setup(self, shim_list):
        '''
        Setup wrapper scripts for running shim scripts.  The list of
        shims in <shim_list> should contain at least those shims for
        packages that this one depends on.
        '''
        if len(shim_list) < len(self.depends):
            raise ValueError, 'setup of "%s" shim package not get enough shims to cover dependencies' % self.name

        def get_shim(name, constraint):
            for s in shim_list:
                if s.name != name:
                    continue
                if not constraint:
                    return s
                if version_consistent(s.version, constraint):
                    return s
                else:
                    log.warning('Package "%s/%s" inconsistent with constraint "%s"' % \
                                    (s.name, s.version, constraint))
                continue
            raise ValueError, 'No shim satisfying "%s/%s" in setup' % \
                (name, constraint or "(any)")

        self.dep_shims = {n:get_shim(n,c) for n,c in self.dep_pkgcon}

        # produce sequence of callable objects that run one step
        self.step_runners = {step:self.make_runner(step) for step in self.steps}
        self._ran = []
        return


    def run_noop(self):
        return

    def make_runner(self, step):
        '''
        Make a callable object that will run the given step.
        '''
        script = self.package_shim_script(step)

        if not script:          # no script, maybe we have a builtin?
            meth = self.__class__.__dict__.get('run_' + step)
            if not meth:
                return self.run_noop
            def meth_curry():   # curry self
                return meth(self)
            return meth_curry

        wrapped = self.make_wrapper(step, script)

        def runner_curry():
            cmdstr = '%s %s' % (shell, wrapped)
            logging.info('Executing shim script via wrapper: %s' % cmdstr)
            rc = proc.run(cmdstr)
            if rc != 0:
                msg = 'Failed to run %s of %s/%s' % (wrapped, self.name, self.version)
                raise RuntimeError, msg
        return runner_curry

    def make_wrapper(self, step, script):
        '''
        Wrap the given <script> for the <step> in order to set up
        calling environment.  Return the full path to the wrapper
        script.
        '''
        # fixme, should not specify this here, use generated_args(step) or something
        script_args = ''
        if step == 'environment':
            script_args = self.generated_filename('package_setenv')
        
        wrapper = self.generated_filename(step)
        fp = open(wrapper,'w')
        fp.write('#!/bin/bash\n')
        #fp.write('set -x\n')

        funcfile = os.path.join(orch_share_directory('bash'), 'orchestrate.sh')
        fp.write(emit_source(funcfile))

        for dep_name in self.depends:
            dep_shim = self.dep_shims[dep_name]
            fp.write(emit_source(dep_shim.generated_filename('package_setenv')))

        orchenv = self.generated_filename('orch_setenv')
        fp.write(emit_source(orchenv))
        
        rundir = self.get_rundir(step)
        fp.write('assuredir %s\n' % rundir)
        fp.write('goto %s\n' % rundir)

        fp.write(emit_source(self.orch_setenv_file()))

        script_run = 'exec'
        if is_bash(script):
            script_run = 'source'
        fp.write('%s %s %s\n' % (script_run, script, script_args))
        
        fp.write('goback\n')
        return wrapper


    def package_shim_script(self, step):
        '''
        Return the first instance of a shim script of given <step>
        '''
        for pdir in self.psd:
            # fixme: here would be where to allow shim scripts with file extensions
            maybe = os.path.join(pdir, step) 
            if os.path.exists(maybe):
                return maybe
        return None



    def generated_filename(self, filetype):
        '''
        Return the full path to file of the given <filetype> type.
        '''
        allowed_types = self.generated_filetypes + self.steps
        if not filetype in allowed_types:
            raise ValueError, 'Unknown filetype: %s' % filetype
        odir = os.path.join(self.vars['build_dir'],'orch')
        if not os.path.exists(odir):
            os.makedirs(odir)
        return os.path.join(odir, filetype)

    def _orch_xxxsetenv_file(self, which):
        '''
        Return and maybe generate the file that sets/unsets ORCH_* variables
        '''
        ftype = 'orch_' + which
        filename = self.generated_filename(ftype)
        if os.path.exists(filename) and not self.force:
            return filename
        fp = open(filename,'w')
        for kv in self.orch_env.items():
            if which == 'setenv':
                fp.write('export %s="%s"\n' % kv)
            if which == 'unsetenv':
                fp.write('unset %s\n' % kv[0])
        fp.close()
        return filename
        
    def orch_setenv_file(self):
        return self._orch_xxxsetenv_file('setenv')
    def orch_unsetenv_file(self):
        return self._orch_xxxsetenv_file('unsetenv')

    def get_rundir(self, step):
        '''
        Return the directory from which to run the shim
        '''
        rundir = self.rundirs.get(step, 'build_dir')
        return self.vars[rundir]

    def run(self, step):
        '''
        Run a step once.
        '''
        if not self.step_runners:
            raise RuntimeError, 'ShimPackage for "%s" has not been setup' % self.name

        if step in self._ran:
            raise ValueError, 'Already ran step "%s"' % step
        
        runner = self.step_runners[step]
        rc = runner()
        self._ran.append(step)
        return rc

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

    pass
