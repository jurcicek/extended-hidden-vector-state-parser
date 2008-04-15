# Note: this setup script expects the GNU toolchain.  It is unlikely that the
# Class Library for Numbers will build on any other compiler so there is no
# attempt at portability for the clnum package.

from distutils.core import setup
from distutils.extension import Extension

setup(
name='clnum',
version='1.4',
description='Class Library for Numbers interface',
author='Ray Buvel',
author_email='rlbuvel@gmail.com',
url='http://calcrpnpy.sourceforge.net/clnum.html',
packages=['clnum'],
ext_modules=[ 
    Extension('clnum.clnum', ['clnum/src/clnum.cpp', ],
        libraries=['cln', 'gmp'],
        # Remove symbols.
        extra_link_args=['-s'],
    ),
],
)

