#!/usr/bin/env python
'''
Test orchestration.unpack
'''

import os
import shutil
import zipfile
import tarfile
import tempfile
from orchestrate import unpack, util

def zipdir(path, zfile):
    for root, dirs, files in os.walk(path):
        for fn in files:
            zfile.write(os.path.join(root, fn))

def test_unzip():
    '''
    Test orchestrate.unpack.unzip
    '''
    dst = tempfile.mktemp()
    src = dst + '.zip'
    zf = zipfile.ZipFile(src, mode='w')
    zipdir('tests', zf)
    zf.close()

    unpack.unzip(src, dst, 'tests')
    print 'unpacked %s to %s, now removing' % (src,dst)
    os.remove(src)
    shutil.rmtree(dst)

def test_untar():
    '''
    Test orchestrate.unpack.untar
    '''
    dst = tempfile.mktemp()
    for ext, mode in [('tar.gz','w:gz'),
                      ('tar','w'),
                      ('tgz','w:gz'),
                      ('tar.bz2','w:bz2')]:

        src = '.'.join([dst,ext])
        tf = tarfile.open(src, mode)
        tf.add('tests')
        tf.close()
        unpack.untar(src, dst, 'tests')
        print 'unpacked %s to %s, now removing' % (src,dst)
        os.remove(src)
        shutil.rmtree(dst)

def test_ungit():
    '''
    Test orchestrate.unpack.ungit
    '''
    dst = tempfile.mkdtemp()
    src = util.git_repo(os.path.realpath('.'))
    unpack.ungit(src, dst, 'orchtest')
    print dst


if '__main__' == __name__:
    test_unzip()
    test_untar()
    test_ungit()
