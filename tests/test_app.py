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


if '__main__' == __name__:
    test_simple()

