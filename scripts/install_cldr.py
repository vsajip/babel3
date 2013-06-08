#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Vinay Sajip
# All rights reserved.
#
# Distribution license: as for Babel
#
from io import BytesIO
import os
import shutil
import sys
import tempfile
import zipfile
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

URL = 'http://unicode.org/Public/cldr/1.7.2/core.zip'

def main():
    td = tempfile.mkdtemp()
    rc = 0
    try:
        os.system('python setup.py egg_info')
        print('Downloading CLDR from %s' % URL)
        data = urlopen(URL).read()
        zf = zipfile.ZipFile(BytesIO(data))
        try:
            zf.extractall(td)
            print('Extracted %d files to %s' % (len(zf.infolist()), td))
        finally:
            zf.close()
        workdir = os.path.join(td, 'common')
        ldpath = os.path.join('babel', 'localedata')
        if not os.path.exists(ldpath):
            print('Creating %s' % ldpath)
            os.makedirs(ldpath)
        cmd = 'python scripts/import_cldr.py %s' % workdir
        print('Running %r' % cmd)
        rc = os.system(cmd)
        if rc:
            print('import_cldr failed with error code %d' % rc)
            rc = 1
    finally:
        shutil.rmtree(td)
    return rc

if __name__ == '__main__':
    try:
        rc = main()
    except Exception as e:
        print(e)
        rc = 1
    sys.exit(rc)
