#!/usr/bin/env python
'''
Test the suite configuration file
'''

import os
from orchestrate import suite

testdir = os.path.dirname(__file__)
testcfg = suite.read_config(os.path.join(testdir, 'test.cfg'))

def test_package_sections():
    '''
    Test that we get expected package sections from the test.cfg.
    '''
    packages = ['hello', 'bc', 'vi']
    no_sec = ['vi']
    for pkg in packages:
        ret = suite.package_sections(testcfg.sections(), pkg)
        if pkg in no_sec:
            assert not ret, 'Got unexpected section for package "%s"' % pkg
        else:
            assert ret, 'No sections for package "%s"' % pkg
        continue

def test_section_constraint():
    constraints = ['version < 1.0', '', ' ', 'version', '1.0']
    for constraint in constraints:
        got = suite.section_constraint('package foo %s'%constraint,
                                       type='package')
        assert got == constraint, 'Failed "%s" != "%s"' % (got, constraint)
        #print 'Success "%s" == "%s"' % (got, constraint)

def test_get_package_section():
    for package, version in [('hello','2.8'), ('bc', '1.06')]:
        got = suite.get_package_section(testcfg, package, version)
        #print got
        assert got, 'Failed to get package section "%s" / "%s"' % \
            (package, version)


def test_resolve():
    cfg = suite.resolve(testcfg)
    for o in cfg:
        assert 'shim_dir' in o.keys()
        print '\n'.join(['%s: %s' %(k,v) for k,v in o.items()])
        print 

if '__main__' == __name__:
    test_package_sections()
    test_version_consistent()
    test_section_constraint()
    test_get_package_section()
    test_resolve()
