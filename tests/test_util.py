#!/usr/bin/env python

import os
        
def test_version_consistent():
    '''
    Test orchestrate.util.version_consistent()
    '''
    from orchestrate.util import version_consistent
    vc_to_check = [
        ('1.0', 'version < 1.0', False),
        ('1.0', 'version == 1.0', True),
        ('1.0', 'version >= 1.0', True),
        ('2.0', 'version != 1.0', True),
        ]
    for version, constraint, tf in vc_to_check:
        result = version_consistent(version, constraint)
        if tf != result:
            raise ValueError, 'Fail with: "%s" "%s" %s != %s' % \
                (version, constraint, tf, result)
        #print 'Success with: "%s" "%s" %s == %s' % \
        #        (version, constraint, tf, result)


def test_host_description():
    '''
    Test orchestrate.util.host_description()
    '''
    from orchestrate.util import host_description
    hd = host_description()
    # lame test:
    assert hd and len(hd)>3, 'Failed to get a host description'
    print 'Host description:\n\t%s' % '\n\t'.join(['%s = %s' % kv for kv in hd.items()])

def test_share_directory():
    '''
    Test orchestrate.util.orch_share_directory
    '''
    from orchestrate.util import orch_share_directory
    osd = orch_share_directory("tests")
    mydir = os.path.dirname(os.path.realpath(__file__))
    assert osd == mydir, 'Can not find self %s != %s' % (osd, mydir)

if __name__ == '__main__':
    test_version_consistent()
    test_host_description()
    test_share_directory()

