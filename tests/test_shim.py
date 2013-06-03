#!/usr/bin/env python
'''
Test orchestrate.shim
'''

from orchestrate import shim
import os
def test_hello():
    vars = dict(shim_dir = os.path.abspath('./shims/hello'),
                unpacked_dir = '/tmp/test_shim/source/hello-2.8',
                install_dir = '/tmp/test_shim/install',
                build_dir = '/tmp/test_shim/build',
                source_dir = '/tmp/test_shim/source',
                package_name = 'hello',
                package_version = '2.8',
                package_url = 'http://ftp.gnu.org/gnu/hello/hello-2.8.tar.gz'
    )

    s = shim.ShimPackage(**vars)

    for step in s.steps:
        s.run(step)

if '__main__' == __name__:
    test_hello()
