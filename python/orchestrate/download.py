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
import logging

# this is wonky
# import urllib2
# urllib2.install_opener(
#     urllib2.build_opener(
#         urllib2.ProxyHandler({'http': '127.0.0.1'})
#     )
# )

from urllib2 import urlopen, urlparse
import util
import proc


# fixme: probably need to add an "pull/update" to git/svn methods if the target already exists

def svn(url, targetdir, final=None):
    '''
    Do an svn checkout of <url> to <targetdir>.
    '''
    print 'in svn: %s' % str(url)
    urlp = urlparse.urlparse(url)
    util.assuredir(targetdir)
    if not final:
        final = os.path.splitext(os.path.basename(urlp.path))[0]
    fullpath = os.path.join(targetdir, final)
    if os.path.exists(fullpath):
        return 0
    rc = proc.run('svn checkout %s %s' % (url, fullpath))
    return rc

def web(url, targetdir, final=None):
    '''Download the file at <url> to <targetdir>.  If <final> is
    given download file to <targetdir>/<final> otherwise use the
    file name as determined by the tail of the URL.'''

    if not final:
        final = os.path.basename(url)
    fullpath = os.path.join(targetdir, final)
    if os.path.exists(fullpath):
        return 0

    util.assuredir(targetdir)
    res = urlopen(url)
    targetfp = open(fullpath, 'w')
    shutil.copyfileobj(res, targetfp)
    targetfp.close()
    return 0


def query2dict(query):
    'Return a dict from a URL query (stuff after the "?")'
    if not query: return dict()
    chunks = query.split('&')
    if not chunks: return dict()
    return {a:b for a,b in [kv.split('=') for kv in chunks]}


def git(url, targetdir, final = None):
    '''Make a "clone" of a git repository at <url> in to targetdir.  If
    <final> is not given it will be the last part of the <url>'s path.
    if <final> ends in '.git' it a bare clone will be made.  The URL
    options can be "tag=<tag>" to specify a tag to checkout.  If a
    "branch=<branch>" is also given it will name the branch hold the
    tagged checkout.  If no branch is given it defaults to the tag
    name.

    '''
    
    urlp = urlparse.urlparse(url)
    query = query2dict(urlp.query)
    tag = query.get('tag')
    branch = query.get('branch')

    url_no_query = urlparse.ParseResult(urlp.scheme, urlp.netloc, urlp.path, '', '', '').geturl()
    if not final:
        final = os.path.basename(urlp.path)
    bare = ""
    if final.endswith('.git'):
        bare = '--bare'
    fullpath = os.path.join(targetdir, final)
    if os.path.exists(fullpath):
        return 0

    util.assuredir(targetdir)
    rc = proc.run("git clone %s %s %s" % (bare, url_no_query, fullpath))
    if rc: return rc
    
    if not tag:
        return 0

    if not branch:
        branch = tag

    rc = proc.run('git --work-tree=%s --git-dir=%s/.git checkout -b %s %s' % (fullpath, fullpath, branch, tag))
    return rc
        

def guess_method(url):
    '''Guess the function to use to download a given URL.  Return a tuple
    containing the function (one of "web", "git" or "svn")
    and the URL modified to be what is expected by that method
    '''

    urlp = urlparse.urlparse(url)
    scheme = urlp.scheme.split('+')

    # we could instead do this with an eval()
    s2f = {'git':git, 'svn':svn, 'web':web}

    # caller follows the rules and provides <method>+<actual_scheme>
    if len(scheme) == 2:
        if scheme == ('svn', 'ssh'): # svn directly accepts svn+ssh:// 
            return (svn, url)      # but not others like svn+http://
        simple_url = url.split('+',1)[1]
        return (s2f[scheme[0]], simple_url)

    # scheme is explicitly dedicated to one method.
    if scheme in ['git','svn']:
        return (s2f[scheme], url)

    # Not guaranteed, but a good guess
    if urlp.path.endswith('.git'):
        return (git, url)

    # give these to git.
    if scheme in ['ssh','rsync']:
        return (git, url)

    # if there is a non-".git" file extension, probably just a file
    if os.path.splitext(urlp.path)[1]:
        return (web, url)

    # what is left might be svn or plain web.  Let's check
    url_no_query = urlparse.ParseResult(urlp.scheme, urlp.netloc, urlp.path, '', '', '').geturl()
    def noop(stuff): pass       # keep proc quiet
    rc = proc.run('svn info %s' % url_no_query, logger=noop)
    if rc == 0:
        return (svn, url)

    return (web, url)
        


def get(url, targetdir, final = None):
    '''Switch yard for choosing a download method.  It accepts URLs with
    an extended scheme formed by a method name + a native scheme.  If
    recognized, the method (and the "+") is stripped off and used to
    select a function to perform the download.

    <method>+<scheme>://<domain>/<path>/[?query]

    '''
    method, newurl = guess_method(url)
    logging.info('downloading by %s: "%s"' % (method.func_name, newurl))
    return method(newurl, targetdir, final)
