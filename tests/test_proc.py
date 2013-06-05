#!/usr/bin/env python
'''
Test the orchestrate.proc module
'''

from orchestrate import proc

class Printer(object):
    def __init__(self, command):
        print 'Running: "%s"' % command
        self.prefix = command.split()[0]


    def out(self, stuff):
        print '[%s] out: "%s"' % (self.prefix, stuff.strip())

    def err(self, stuff):
        print '[%s] err: "%s"' % (self.prefix, stuff.strip())
    

def do_run(cmd, code = 0):
    p = Printer(cmd)
    rc = proc.run(cmd, logout=p.out, logerr=p.err)
    assert rc == code, 'got unexpected code %d != %d' % (rc, code)


def test_simple():
    cmds = [("/bin/echo Hello World", 0),
            ("/bin/false", 1),
            ("/bin/true", 0),
            ("/bin/ls", 0),
            ]
    for cmd, code in cmds:
        do_run(cmd, code)

if '__main__' == __name__:
    test_simple()
