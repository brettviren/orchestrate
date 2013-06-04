#!/usr/bin/env python
from glob import glob
from distutils.core import setup

shims = glob('shims/*/*')
print shims

setup(name = 'orchestrate',
      version = '0.0',
      url = 'https://github.com/brettviren/orchestrate',
      author = 'Brett Viren',
      author_email = 'bv@bnl.gov',
      packages = ['orchestrate'],
      package_dir = {'': 'python'},
      data_files = [('share/orchestrate/shims', shims),
                    ('share/orchestrate/bash', ['bash/orchestrate.sh']),
                    ],
      )
