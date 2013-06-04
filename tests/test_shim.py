#!/usr/bin/env python
'''
Test orchestrate.shim
'''

from orchestrate import shim
import os

def get_shim_path():
    'Build canonical, full shim path'
    shim_path = []
    path = os.environ.get('ORCH_SHIM_PATH')
    if path:
        shim_path.append(path)
    shim_path.append(os.path.abspath('./shims/hello'))
    path = shim.orch_share_directory('shims')
    if path:
        shim_path.append(path)
    return ':'.join(shim_path)
    

def test_shim_path():
    sp = get_shim_path()
    assert isinstance(sp, basestring), 'Got weird type for shim path (%s) %s' % (type(sp), sp)

def test_hello():

    hello_version = '2.8'
    hello_pkg_name = 'hello-%s' % hello_version,

    vars = dict(shim_path = get_shim_path(),
                unpacked_dir = '/tmp/test_shim/source/%s'%hello_pkg_name,
                install_dir = '/tmp/test_shim/install',
                build_dir = '/tmp/test_shim/build',
                source_dir = '/tmp/test_shim/source',
                package_name = 'hello',
                package_version = '2.8',
                package_url = 'http://ftp.gnu.org/gnu/hello/%s.tar.gz'%hello_pkg_name,
    )


    s = shim.ShimPackage(**vars)

    for step in s.steps:
        s.run(step)

if '__main__' == __name__:
    test_shim_path()
    test_hello()
