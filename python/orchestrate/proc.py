#!/usr/bin/env python
'''
Run a sub process
'''
import logging

from subprocess import Popen, PIPE, STDOUT, CalledProcessError

def run(cmdstr, env=None, logout=logging.info, logerr=logging.warning):
    '''
    Run the command <cmdstr> and return its error code.

    If a dictionary <env> is given, run using it as the environment.
    Otherwise the callers environment is used.

    The callable objects <logout> or <logerr>, if defined, are passed
    stdout/stderr, respectively, of the command as it runs.
    '''

    stdout, stderr = None, None
    if logout:
        stdout = PIPE
    if logerr:
        stderr = PIPE

    p = Popen(cmdstr.split(), stdout=stdout, stderr=stderr, 
              universal_newlines=True,env=env)

    if not (logout or logerr):  # no need to be fancy
        p.communicate()
        return p.returncode

    # In order to provide async output we have to spin on a poll.
    res = None
    while True:

        if logout:
            out = p.stdout.readline()
        if logerr:
            err = p.stderr.readline()

        res = p.poll()

        if logout and out:
            logout(out)
        if logerr and err:
            logerr(err)

        if res == None:
            continue

        # slurp up any remaining output
        if logout:
            for out in p.stdout.readlines():
                logout(out)
        if logerr:
            for err in p.stderr.readlines():
                logerr(err)

        break
    return res
