#!/usr/bin/env python
'''
Run a sub process
'''
import os
import logging

from subprocess import Popen, PIPE, STDOUT

def logout(text):
    'Default standard output logger'
    logging.info(text.strip())

def run(cmdstr, env=None, logger=logout, shell=True):
    '''
    Run the command <cmdstr> and return its error code.

    If a dictionary <env> is given, run using it as the environment.
    Otherwise the callers environment is used.

    The callable objects <logout> or <logerr>, if defined, are passed
    stdout/stderr, respectively, of the command as it runs.  Log lines
    are passed unfiltered.  In particular any trailing newlines are
    left intact.
    '''

    stdout, stderr = None, None
    if logout:
        stdout = PIPE
        stderr = STDOUT

    if not shell:
        cmdstr = cmdstr.split()

    logging.debug('proc running: "%s"' % cmdstr)
    p = Popen(cmdstr, stdin=open(os.devnull), stdout=stdout, stderr=stderr, 
              universal_newlines=True, env=env, shell=shell)

    if not logger:  # no need to be fancy
        p.communicate()
        return p.returncode

    # In order to provide async output we have to spin on a poll.
    res = None
    while True:

        out = p.stdout.readline()
        res = p.poll()

        if out:
            logger(out)

        if res == None:
            continue

        # slurp up any remaining output
        for out in p.stdout.readlines():
            logger(out)

        break
    return res
