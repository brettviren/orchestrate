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
    
def hello_vars():
    hello_version = '2.8'
    hello_pkg_name = 'hello-%s' % hello_version,
    return dict(shim_path = get_shim_path(),
                unpacked_dir = '/tmp/test_shim/source/%s'%hello_pkg_name,
                install_dir = '/tmp/test_shim/install',
                build_dir = '/tmp/test_shim/build',
                source_dir = '/tmp/test_shim/source',
                download_dir = '/tmp/test_shim/downloads',
                package_name = 'hello',
                package_version = '2.8',
                package_url = 'http://ftp.gnu.org/gnu/hello/%s.tar.gz'%hello_pkg_name,
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

def test_builtin():
    vars = hello_vars()
    s = shim.ShimPackage(**vars)
    print 'Running run("bogus")'
    s.run('bogus')
    print 'Running run_bogus()'
    s.run_bogus()

def test_hello():

    vars = hello_vars()
    s = shim.ShimPackage(**vars)

    print 'orch env file:', s.orch_env_file
    print 'pkg env file:', s.pkg_env_file
    print 'deps:', s.dep_ver

    for step in s.steps:
        print 'Running shim step: %s' % step
        s.run(step)

if '__main__' == __name__:
    test_shim_path()
    test_psd()
    test_builtin()
    test_hello()
