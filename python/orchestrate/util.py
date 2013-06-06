#!/usr/bin/env python


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
