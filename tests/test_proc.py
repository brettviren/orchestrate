#!/usr/bin/env python
'''
Test the orchestrate.proc module
'''

import os
from orchestrate import proc

import tempfile
testdir = os.path.dirname(__file__)

class Printer(object):
    def __init__(self, command):
        print 'Running: "%s"' % command
        self.prefix = command.split()[0]
    def __call__(self, stuff):
        print '[%s] out: "%s"' % (self.prefix, stuff.strip())
    

def do_run(cmd, code = 0):
    p = Printer(cmd)
    fullenv = dict(os.environ)
    rc = proc.run(cmd, env=fullenv, logger=p)
    assert rc == code, 'got unexpected code %d != %d' % (rc, code)


def test_simple():
    cmds = [("/bin/echo Hello World", 0),
            ("/bin/false", 1),
            ("/bin/true", 0),
            ("/bin/ls", 0),
            ("/bin/bash %s" % os.path.join(testdir, 'testscript.sh'), 0),
            ]
    for cmd, code in cmds:
        do_run(cmd, code)

def test_pipe():
    do_run('ls /tmp | sort -n')

def test_git_pipe():
    dst = tempfile.mkdtemp()
    cmd='git --git-dir=.git archive --format=tar --prefix=orchtest/ HEAD | tar -xvf- -C %s'%dst
    do_run(cmd)

if '__main__' == __name__:
    test_simple()
    test_pipe()
    test_git_pipe()
