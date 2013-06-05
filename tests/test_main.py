#!/usr/bin/env python

import os
from orchestrate import main

testdir = os.path.dirname(__file__)

def test_create_main():
    'Create a main orchestrate object.'
    o = main.Orchestrate(os.path.join(testdir,'test.cfg'))
    for n,v in o.package_list():
        print n,v

if '__main__' == __name__:
    test_create_main()
