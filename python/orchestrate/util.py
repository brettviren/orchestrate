#!/usr/bin/env python

import os

from subprocess import check_output, CalledProcessError

def orch_share_directory(subdir = '.'):
    'Find <subdir> in installed app area'
    venvdir = os.environ.get('VIRTUAL_ENV')
    if venvdir:                 # installed in virtual env
        maybe = os.path.realpath(os.path.join(venvdir, 'share/orchestrate', subdir))
        if os.path.exists(maybe):
            return maybe

    # in-source
    maybe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),subdir)
    maybe = os.path.realpath(maybe)
    if os.path.exists(maybe):
        return maybe

    return None

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
        ret[k] = v
    platform = '{kernelname}-{machine}'.format(**ret)
    ret['platform'] = platform
    
    try:
        flavor = check_output(['ups','flavor'])
    except OSError:
        flavor = ups_flavor()
    ret['ups_flavor'] = flavor

    ret['orch_dir'] = orch_share_directory()
    return ret


def interpolate_dict(d):
    '''Take a dict of string values and call .format() on each value
    using the dict itself until all "{...}" variables are
    interpolated.
    '''
    depth = 10
    last_d = dict(d)
    #print last_d

    def dump_last():
        p = last_d.get('package_name','(unknown package)')
        v = last_d.get('package_version','(unknown version)')
        return '%s/%s' % (p,v)
    while depth:
        depth -= 1
        new_d = {}
        for k,v in last_d.items():
            try:
                new_v = v.format(**last_d)
            except ValueError, err:
                print 'Attempted interpolation on: %s = "%s" in %s' % (k,v, dump_last())
                raise
            except KeyError, err:
                print 'Attempted interpolation on: %s = "%s" in %s' % (k,v, dump_last())
                raise
            new_d[k] = new_v
        if new_d == last_d:         # converged
            return new_d
        last_d = new_d
    raise ValueError, 'Exceeded maximum interpolation recursion'

def wash_env(d):
    '''
    Return a new dictionary based on input which has all values run
    through os.path.expandvars() and os.path.expanduser()
    '''
    ret = {}
    for k,v in d.items():
        ret[k] = os.path.expanduser(os.path.expandvars(v))
    return ret

def list_split(lst, delim = ','):
    '''
    Split individual strings in a list of strings by the delimiter
    <delim> to produce a single flat list.
    '''
    if not lst:
        return lst
    ret = []
    for x in lst:
        ret += x.split(delim)
    return ret


def order_depends(lst):
    '''
    Return a new version of the given list <lst> such that no element
    comes before any no which it depends.  Each element should have a
    .name property giving its name an a .depends property giving a
    list of names of other elements on which it depends, if any
    '''
    n2e = {e.name:e for e in lst}
    ordered = []
    def satisfied(ele):
        deps = element.depends
        if not deps: return True
        for dep in deps:
            if not dep in ordered:
                return False
        return True
    while lst:
        left = []
        for element in lst:
            if satisfied(element):
                ordered.append(element.name)
                #print ordered, [x.name for x in left]
                continue
            left.append(element)
        lst = left
    return [n2e[x] for x in ordered]

def assuredir(directory):
    '''
    Assure that the directory exists.  Return False if already exists, True o.w.
    '''
    if os.path.exists(directory):
        return False
    os.makedirs(directory)
    return True

