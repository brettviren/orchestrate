#!/usr/bin/env python
'''
Get files from the Internet via a URL.

Each main function takes arguments:

 - url
 - target directory
 - optional final file/directory relative to the target directory


'''

import os
import shutil
from urllib2 import urlopen, urlparse
import util
import proc

def webfile(url, targetdir, final=None):
    '''Download the file at <url> to <targetdir>.  If <final> is
    given download file to <targetdir>/<final> otherwise use the
    file name as determined by the tail of the URL.'''

    if not final:
        final = os.path.basename(url)
    res = urlopen(url)
    util.assuredir(targetdir)
    fullpath = os.path.join(targetdir, final)
    targetfp = open(fullpath, 'w')
    shutil.copyfileobj(res, targetfp)
    targetfp.close()
    return 0

def query2dict(query):
    'Return a dict from a URL query (stuff after the "?")'
    return {a:b for a,b in [kv.split('=') for kv in query.split('&')]}

def gitdir(url, targetdir, final = None):
    '''Make a "clone" of a git repository at <url> in to targetdir.  If
    <final> is not given it will be the last part of the <url>'s path
    (less any ".git" extension and ignoring any URL options).  The URL
    options can be "tag=<tag>" to specify a tag to checkout.  If a
    "branch=<branch>" is also given it will name the branch hold the
    tagged checkout.  If no branch is given it defaults to the tag
    name.

    '''
    
    urlp = urlparse.urlparse(url)
    query = query2dict(urlp.query)
    tag = query.get('tag')
    branch = query.get('branch')

    just_url = urlparse.ParseResult(urlp.scheme, urlp.netloc, urlp.path, '', '', '').geturl()
    if not final:
        final = os.path.splitext(os.path.basename(urlp.path))[0]
    fullpath = os.path.join(targetdir, final)

    util.assuredir(targetdir)
    rc = proc.run("git clone %s %s" % (just_url, fullpath))
    if rc: return rc
    
    if not tag:
        return 0

    if not branch:
        branch = tag

    rc = proc.run('git --work-tree=%s --git-dir=%s/.git checkout -b %s %s' % (fullpath, fullpath, branch, tag))
    return rc
        
