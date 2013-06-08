#!/usr/bin/env python
'''
Test orchestrate.download
'''

import os
import tempfile
import tcommon
from orchestrate import download


tdir = tempfile.mkdtemp()
print 'Using temp directory: %s' % tdir

def test_get_google_index():
    '''
    Get google index.html as test of download.web()
    '''

    download.web('http://www.google.com/',tdir,'google_index.html')

def test_guess_method():
    '''
    Test download.guess_method 
    '''
    fodder = [('git','git@github.com:brettviren/orchestrate.git'),
              ('git','ssh://lycastus/home/bviren/git/orchestrate.git'),
              ('svn','http://cdcvs.fnal.gov/subversion/lbne-software/build'),
              ('svn','svn+http://cdcvs.fnal.gov/subversion/lbne-software/build'),
              ]
    for expect, url in fodder:
        got, newurl = download.guess_method(url)
        assert got.func_name == expect, 'Got wrong method %s != %s for %s' % (got.func_name, expect, url)
        print expect,url,' --> ',got,newurl

def test_get():
    '''
    Get some git/svn anonymous access repos
    '''

    gittag = 'unit_test_get'
    urls = [('bygit','git://github.com/brettviren/orchestrate.git?tag=%s'%gittag),
            ('byhttps','https://github.com/brettviren/orchestrate.git?tag=%s'%gittag),
            ('beanie','http://cdcvs.fnal.gov/subversion/lbne-software/build'),
            ('beanie','svn+http://cdcvs.fnal.gov/subversion/lbne-software/build'),
    ]
    for label, url in urls:
        targetdir = os.path.join(tdir,label)
        retcode = download.get(url, targetdir)
        assert retcode == 0, 'Bad return for %s into %s' % (url, targetdir)
    return


if '__main__' == __name__:
    test_guess_method()
    test_get_google_index()
    test_get()

