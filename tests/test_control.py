#!/usr/bin/env python
'''
Test the orchestrate.control module
'''

import os
from orchestrate import control

testdir = os.path.dirname(__file__)

def test_list():
    '''
    Test the list command
    '''
    control.main(['-c',os.path.join(testdir,'test.cfg'),'list'])

def test_steps():
    '''
    Install a suite
    '''
    print 'This currently fails as "step" command is not yet implemented:'
    control.main(['-c',os.path.join(testdir,'test.cfg'),'step',])

if '__main__' == __name__:
    test_list()
    test_steps()
