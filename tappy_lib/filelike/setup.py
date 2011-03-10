
import sys
import distribute_setup
distribute_setup.use_setuptools()
from setuptools import setup, find_packages


setup_kwds = {}
setup_kwds["test_suite"] = "filelike.tests.build_test_suite"
if sys.version_info > (3,):
    setup_kwds["use_2to3"] = True


info = {}
try:
    next = next
except NameError:
    def next(i):
        return i.next()
src = open("filelike/__init__.py")
lines = []
ln = next(src)
while "__version__" not in ln:
    lines.append(ln)
    ln = next(src)
while "__version__" in ln:
    lines.append(ln)
    ln = next(src)
exec("".join(lines),info)


NAME = "filelike"
VERSION = info["__version__"]
DESCRIPTION = "Classes for creating and wrapping file-like objects"
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL = "http://www.rfk.id.au/software/filelike/"
LICENSE = "LGPL"
KEYWORDS = "file filelike file-like filter crypt compress"
LONG_DESC = info["__doc__"]


PACKAGES = find_packages()
EXT_MODULES = []
PKG_DATA = {}


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
      **setup_kwds
     )

