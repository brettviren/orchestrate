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

def test_suite():
    '''
    Install a suite
    '''
    control.main(['-c',os.path.join(testdir,'test.cfg'),'step',])

if '__main__' == __name__:
    test_list()
