#!/usr/bin/env python
'''
Test get
'''

import os
import tempfile
from orchestrate import get


def test_get_google_index():
    '''
    Get google index.html as test of get.webfile()
    '''

    get.webfile('http://www.google.com/','/tmp','google_index.html')

def test_get_git_orch():
    '''
    Get orch git repo as test of get.gitdir()
    '''

    tdir = tempfile.mkdtemp()
    print 'Using temp directory: %s' % tdir

    tag = 'unit_test_get'
    urls = [('bygit','git://github.com/brettviren/orchestrate.git?tag=%s'%tag),
            ('byhttps','https://github.com/brettviren/orchestrate.git?tag=%s'%tag)]
    for label, url in urls:
        targetdir = os.path.join(tdir,label)
        retcode = get.gitdir(url, targetdir)
        assert retcode == 0, 'Bad return for %s into %s' % (url, targetdir)
    return

if '__main__' == __name__:
    #test_get_google_index()
    test_get_git_orch()
