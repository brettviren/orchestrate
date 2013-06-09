#!/usr/bin/env python
'''Implement builtin unpack step.

Each main function takes

 - The source (archive, VCS dir) to unpack

 - The target directory to unpack in

 - An optional file or directory that will be created on an successful
   unpacking.  If this file exists the unpacking will not be done.  If
   it is a relative path it is taken w.r.t. the target directory.

'''

import os
import logging
import zipfile
import tarfile

import proc
import util

def prepare(src, dst, creates):
    '''If <creates> exists, do nothing.  Otherwise make sure directory
    <dst> exists.  Return true if actual unpacking should continue.
    '''
    if not os.path.exists(src):
        raise ValueError, 'No such source to unpack: %s' % src

    if creates:
        if not creates.startswith('/'):
            creates = os.path.join(dst,creates)
        if os.path.exists(creates):
            logging.debug('idem: unzip result already exists: %s' % creates)
            return False
    util.assuredir(dst)
    return True

def unzip(src, dst, creates=None):
    '''
    Unzip <src> file into <dst> directory unless <creates> already exists.
    '''

    if not prepare(src, dst, creates):
        return

    # http://stackoverflow.com/questions/7806563/how-to-unzip-a-file-with-python-2-4
    zfile = zipfile.ZipFile(src)
    for name in zfile.namelist():
        (reldir, filename) = os.path.split(name)
        dirname = os.path.join(dst, reldir)
        if not os.path.exists(dirname):
            util.assuredir(dirname)
        fullpath = os.path.join(dst,name)
        fd = open(fullpath, 'w')
        fd.write(zfile.read(name))
        fd.close()
    zfile.close()
    return 0

def untar(src, dst, creates=None):
    '''
    Untar <src> file into <dst> directory unless <creates> already exists
    '''

    if not prepare(src, dst, creates):
        return
    
    tf = tarfile.open(src)
    for member in tf.getmembers():
        tf.extract(member, dst)
    tf.close()
    return 0

def ungit(src, dst, creates, treeish='HEAD'):
    '''Produce an archive from a local git repository <src> and unpack it to <dst>.

    Unlike the other un*() functions in this module the <creates>
    argument must be given and it is interpreted as the sub-directory
    under <dst> that should be created.  It will usually be chosen be
    the <package_name> or <package_name>-<package_version>.  An
    optional git "treeish" can be specified, else HEAD is used.
    '''

    if not prepare(src, dst, creates):
        return

    cmd = 'git --git-dir={src} archive --format=tar --prefix={creates}/ {treeish} | tar -xf- -C {dst}'.format(**locals())
    print cmd
    return proc.run(cmd)
    
