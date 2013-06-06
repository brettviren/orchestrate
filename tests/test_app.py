#!/usr/bin/env python
'''
Test the orchestrate.app module.
'''

import os
from orchestrate import app

testdir = os.path.dirname(__file__)

def test_simple():
    orch = app.Orchestrate(os.path.join(testdir,'test.cfg'))
    assert orch, 'Failed to make Orchestrate app'
    return

def test_should_fail():
    '''
    Test that the Orchestrate detects bad dependencies
    '''
    try:
        app.Orchestrate(os.path.join(testdir,'test-baddep.cfg'))
    except ValueError, msg:
        print 'Got expected ValueError: %s' % msg
        pass

def test_shim_path():
    good_shims = os.path.join(testdir, 'shims')
    bad_shims = '/path/does/not/exist'
    extra_shims = ':'.join([good_shims, bad_shims])
    orch = app.Orchestrate(os.path.join(testdir,'test.cfg'),shim_path=extra_shims)
    print 'Above warning about /path/does/not/exist is expected'

    sp = orch.cfg.get('global','shim_path')
    assert good_shims in sp, 'No %s in %s' % (good_shims,sp)
    assert bad_shims not in sp, 'Bad shim %s in %s' % (bad_shims,sp)

def test_bad_shim():
    sp = os.path.join(testdir, 'shims-bad')
    try:
        app.Orchestrate(os.path.join(testdir,'test.cfg'),shim_path=sp)
    except ValueError, msg:
        assert 'no package "emacs"' in str(msg), 'Got unexpected ValueError message: %s' % msg
        print 'Got expected ValueError, should be about needing emacs: %s' % msg 
    

if '__main__' == __name__:
    test_shim_path()
    test_simple()
    test_should_fail()
    test_bad_shim()

