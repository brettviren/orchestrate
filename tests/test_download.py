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

def test_query2dict():
    d = download.query2dict('')
    assert len(d) == 0

    d = download.query2dict('foo=bar&baz=quax')
    assert d['foo'] == 'bar'
    assert d['baz'] == 'quax'
    print d

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
    urls = [
        #('bygit','git://github.com/brettviren/orchestrate.git?tag=%s'%gittag),
        #('byhttps','https://github.com/brettviren/orchestrate.git?tag=%s'%gittag),
        #('beanie','http://cdcvs.fnal.gov/subversion/lbne-software/build'),
        #('beanie','svn+http://cdcvs.fnal.gov/subversion/lbne-software/build'),
        #('ftptest','ftp://root.cern.ch/root/pythia6.tar.gz'),
        ('pythontest','http://www.python.org/ftp/python/2.7.3/Python-2.7.3.tgz'),
    ]
    for label, url in urls:
        targetdir = os.path.join(tdir,label)
        retcode = download.get(url, targetdir)
        assert retcode == 0, 'Bad return for %s into %s' % (url, targetdir)
    return



if '__main__' == __name__:
    #test_query2dict()
    #test_guess_method()
    #test_get_google_index()
    test_get()

