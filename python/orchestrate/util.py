#!/usr/bin/env python

import os

from subprocess import check_output, CalledProcessError

def version_consistent(version, constraint):
    '''
    Return true if the constraint string is consistent with the version string.
    '''
    from pkg_resources import parse_version
    cleaned = []
    for token in [x.strip() for x in constraint.split()]:
        if token in ['version','and','or','==','!=','<','>','<=','>=']:
            cleaned.append(token)
            continue
        cleaned.append('pv("%s")' % token)
    code = ' '.join(cleaned)
    return eval(code, {'version':parse_version(version), 'pv':parse_version})


def ups_flavor():
    '''
    Ow, my balls.
    '''
    kern, host, rel, vend, mach = os.uname()
    if mach in ['x86_64','sun','ppc64']:
        mach = '64bit'
    else:
        mach = ''
    rel = '.'.join(rel.split('.')[:2])
    libc = check_output(['ldd','--version']).split('\n')[0].split()[-1]
    return '%s%s+%s-%s' % (kern, mach, rel, libc)

def host_description():
    '''
    Return a dictionary of host description variables.
    '''
    ret = {}

    uname_fields = ['kernelname', 'hostname', 
                    'kernelversion', 'vendorstring', 'machine']
    uname = os.uname()
    for k,v in zip(uname_fields, uname):
        ret.setdefault(k,v)
    platform = '{kernelname}-{machine}'.format(**ret)
    ret.setdefault('platform',platform)
    
    try:
        upsflavor = check_output(['ups','flavor'])
    except OSError:
        upsflavor = ups_flavor()

    ret.setdefault('upsflavor',upsflavor)
    return ret
