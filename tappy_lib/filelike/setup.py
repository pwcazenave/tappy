#
#  This is the filelike setuptools script.
#  Originally developed by Ryan Kelly, 2006.
#
#  This script is placed in the public domain.
#

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages, Extension

#  Import to allow pertinent info to be extracted
import filelike

VERSION = filelike.__version__

# Package MetaData
NAME = "filelike"
DESCRIPTION = "Classes for creating and wrapping file-like objects"
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL = ""
# TODO: determine proper license
LICENSE = "LGPL"
KEYWORDS = "file filelike file-like filter"
LONG_DESC = filelike.__doc__

#  Module Lists
PACKAGES = find_packages()
EXT_MODULES = []
PKG_DATA = {}

##
##  Main call to setup() function
##

setup(name=NAME,
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      description=DESCRIPTION,
      long_description=LONG_DESC,
      keywords=KEYWORDS,
      packages=PACKAGES,
      ext_modules=EXT_MODULES,
      package_data=PKG_DATA,
      license=LICENSE,
      test_suite="filelike.testsuite",
     )

