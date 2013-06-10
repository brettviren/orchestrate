#!/usr/bin/env python
'''
Test orchestrate.shim
'''

from orchestrate import shim
import os

import logging
logging.basicConfig(filename='/dev/stdout', level=logging.DEBUG)

def get_shim_path():
    'Build canonical, full shim path'
    shim_path = []
    path = os.environ.get('ORCH_SHIM_PATH')
    if path:
        shim_path.append(path)
    shim_path.append(os.path.abspath('./tests/shims'))
    path = shim.orch_share_directory('shims')
    if path:
        shim_path.append(path)
    return ':'.join(shim_path)
    
def make_vars(pkg, ver):
    namever = '%s-%s' % (pkg,ver)
    tarball = '%s.tar.gz'%namever
    return dict(shim_path = get_shim_path(),
                unpacked_dir = '/tmp/test_shim/source/%s'%namever,
                install_dir = '/tmp/test_shim/install/',
                build_dir = '/tmp/test_shim/build/%s'%namever,
                source_dir = '/tmp/test_shim/source',
                download_dir = '/tmp/test_shim/downloads',
                package_name = pkg,
                package_version = ver,
                source_package = tarball,
                source_url = 'http://ftp.gnu.org/gnu/%s/%s'%(pkg,tarball),
                shim_names = '%s,autoconf'%pkg,
            )

def test_shim_path():
    sp = get_shim_path()
    assert isinstance(sp, basestring), 'Got weird type for shim path (%s) %s' % (type(sp), sp)

def test_psd():
    '''
    Test shim.package_shim_directories
    '''
    pathlist = get_shim_path().split(':')
    psd = shim.package_shim_directories(pathlist, ['bc','autoconf','default'])
    assert psd, 'Got no psd for bc from %s' % pathlist
    print 'psd=%s' % ', '.join(psd)

def test_steps():
    bvars = make_vars('bc','1.06')
    hvars = make_vars('hello','2.8')
    bs = shim.ShimPackage(**bvars)
    hs = shim.ShimPackage(**hvars)
    shim_list = [bs,hs]
    for s in shim_list:
        s.setup(shim_list)
    for s in shim_list:
        print 'Running %s.run("bogus")' % s.name
        try:
            s.run('bogus')
        except KeyError:
            print 'Caught expected run of bogus step'

        print 'Running %s.run_bogus()' % s.name
        s.run_bogus()

    for step in s.steps:
        print 'Running shim step: %s' % step
        bs.run(step)
        hs.run(step)

def test_hello_names():

    vars = make_vars('hello','2.8')
    s = shim.ShimPackage(**vars)

    for gt in s.generated_filetypes:
        print '%s: %s' % (gt, s.generated_filename(gt))
    print 'deps:', s.dep_pkgcon


if '__main__' == __name__:
    # test_shim_path()
    # test_psd()
    # test_hello_names()
    test_steps()
