#!/usr/bin/env python
'''
Procedures and objects for an orchestration suite.
'''

import os
import re

from ConfigParser import SafeConfigParser # , NoOptionError

from util import version_consistent, host_description

def read_config(fname):
    cfg = SafeConfigParser()
    cfg.read(fname)
    return cfg


def package_sections(sections, package):
    '''Return a sub-list of sections from the given list of <sections>
    that match a given <package>
    '''
    pat = r'package %s\b' % package
    ret = []
    for sec in sections:
        if re.match(pat,sec):
            #print 'Checking %s' % (sec,)
            ret.append(sec)
    return ret

def section_constraint(section, type='package'):
    '''Return a constraint from a section title or None.
    Section title is of form: "<type> <name> [<the constraint>]"'''
    if not section.startswith('%s ' % type):
        raise ValueError, 'Section not of type %s: %s' % (type, section)
    parts = section.split(' ',2)
    if len(parts) == 2:         # no constraint
        return
    return parts[2]

def get_package_section(cfg, package, version):
    '''Return a dictionary of the first package section of <cfg> with
    given <package> name and a version consistent with <version>.
    '''
    for section in package_sections(cfg.sections(), package):
        constraint = section_constraint(section)
        if constraint and not version_consistent(version, constraint):
            continue
        return dict(cfg.items(section))
    raise ValueError, 'No consistent package section for %s/%s found' % \
        (package, version)

def interpolate_dict(d):
    '''Take a dict of string values and call .format() on each value
    using the dict itself until all "{...}" variables are
    interpolated.
    '''
    depth = 10
    last_d = dict(d)
    #print last_d
    while depth:
        depth -= 1
        new_d = {}
        for k,v in last_d.items():
            try:
                new_v = v.format(**last_d)
            except ValueError:
                print 'Attempted interpolation on: "%s"' % v
                raise
            new_d[k] = new_v
        if new_d == last_d:         # converged
            return new_d
        last_d = new_d
    raise ValueError, 'Exceeded maximum interpolation recursion'


def resolve(cfg, suitename = None):
    '''Return information about a suite from the given suite configuration file.

    If no <suitename> is provided the [global] section is checked for
    a <suite> entry.  Otherwise ValueError is raised.

    Results are of the form of a list of dictionaries, one for each
    package, with all values fully interpolated.
    '''

    globals = dict(cfg.items('global'))

    if not suitename:
        suitename = globals['suite']
    if not suitename:
        raise ValueError, 'no suite name given'

    suite_section = 'suite %s' % suitename
    tags = cfg.get(suite_section, 'tags')
    packagelist = cfg.get(suite_section, 'packages')
    defaults_name = cfg.get(suite_section, 'defaults')

    # load up defaults for all packages
    defaults = host_description()
    defaults.update(dict(cfg.items('defaults %s' % defaults_name)))
    defaults.setdefault('tags', tags)
    tags = map (lambda x: x.strip(), defaults.get('tags').split(','))
    defaults.setdefault('tagsdashed', '-'.join(tags))
    defaults.setdefault('tagscolon', ':'.join(tags))
    defaults.setdefault('suite', suitename)
    

    pkgobjs = []
    for pkgname, pkgver in cfg.items('packagelist %s' % packagelist):
        #print pkgname, pkgver
        pkg_sec = get_package_section(cfg, pkgname, pkgver)
        d = dict(globals)
        d.update(defaults)
        d.setdefault('package_name', pkgname)
        d.setdefault('package_version', pkgver)
        d.setdefault('package', pkgname)
        d.setdefault('version', pkgver)
        d.update(pkg_sec)
        pkgobjs.append(d)

    return map(interpolate_dict, pkgobjs)
