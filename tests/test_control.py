#!/usr/bin/env python
'''
Test the orchestrate.control module
'''

import os
from orchestrate import control, shim

testdir = os.path.dirname(__file__)
testcfgfile = os.path.join(testdir,'test.cfg')

cmdstr = '-c %s -s ./tests/shims' % testcfgfile

def test_list():
    '''
    Test the list command
    '''
    cmd = cmdstr + ' list'
    print 'testing with command: %s' % cmd
    control.app_main(cmd.split())

def test_steps():
    '''
    Install a suite
    '''
    cmd = cmdstr + ' step'
    print 'testing with command: %s' % cmd
    control.app_main(cmd.split())

def test_bc():
    '''
    Install one package from a suite, one step at a time.
    '''
    for step in shim.ShimPackage.steps:
        cmd = cmdstr + ' --last-step %s --packages bc step' % step
        print 'Test limit with "%s"' % cmd
        control.app_main(cmd.split())


if '__main__' == __name__:
    test_list()
    test_steps()
    test_bc()
