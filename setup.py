"""
NAME:
    setup.py
  
SYNOPSIS:
    python setup.py [options] [command]
    
DESCRIPTION:
    Using distutils "setup", build, install, or make tarball of the package.
    
OPTIONS:
    See Distutils documentation for details on options and commands.
    Common commands:
    build               build the package, in preparation for install
    install             install module(s)/package(s) [runs build if needed]
    install_data        install datafiles (e.g., in a share dir)   
    install_scripts     install executable scripts (e.g., in a bin dir)   
    sdist               make a source distribution
    bdist               make a binary distribution
    clean               remove build temporaries

EXAMPLES:
    cd mydir
    (cp myfile-0.1.tar.gz here)
    gzip -cd myfile-0.1.tar.gz | tar xvf -
    cd myfile-0.1
    python setup.py build
    python setup.py install
    python setup.py sdist
"""

#===imports=============
import os,sys,re,string,getopt,shutil,commands
# Let's see if ez_setup is installed
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

#===globals======
modname='setup'
debug_p=0

#===configuration======
pkgname='tappy'
version_text=string.strip(open("VERSION").readline())
exec_prefix=sys.exec_prefix
description = "Tidal Analysis Program in PYthon"
long_description = "TAPPY is a tidal analysis package. It breaks down an hourly record of water levels into the component sine waves. It is written in Python and uses the least squares optimization and other functions in SciPy?. The focus is to make the most accurate analysis possible. TAPPY only determines the constituents that are calculatable according to the length of the time series."
download_url = "http://prdownloads.sourceforge.net/tappy/tappy-0.7.4.tar.gz?download"
author = "Tim Cera"
author_email = "timcera@earthlink.net"
url="http://tappy.sourceforge.net"
license = "GPL-2"

scripts=['tappy.py']
packages=[
    'tappy_lib', 
    'tappy_lib/astrolabe/lib/python/astrolabe', 
    'tappy_lib/filelike/filelike', 
    'tappy_lib/pyparsing',
    'tappy_lib/pad',
    ]

#===utilities==========================
def debug(ftn,txt):
    if debug_p:
        sys.stdout.write("%s.%s:%s\n" % (modname,ftn,txt))
        sys.stdout.flush()

def fatal(ftn,txt):
    msg="%s.%s:FATAL:%s\n" % (modname,ftn,txt)
    raise SystemExit, msg
    
def usage():
    print __doc__

#=============================
def main():
    # patch distutils if it can't cope with the "classifiers" or
    # "download_url" keywords
    from sys import version
    if version < '2.2.3':
            from distutils.dist import DistributionMetadata
            DistributionMetadata.classifiers = None
            DistributionMetadata.download_url = None
    setup (#---meta-data---
           name = pkgname,
           version = version_text,
           description = description,
           long_description = long_description,
           download_url = download_url,
           author = author,
           author_email = author_email,
           url=url,
           license = license,

           #---scripts,modules and packages---
           scripts=scripts,
           packages = packages,
	   package_data = {'tappy_lib' : ['astrolabe/data/vsop87d.txt']},
           )
#==============================
if __name__ == '__main__':
    opts,pargs=getopt.getopt(sys.argv[1:],'hv',
                 ['help','version','exec-prefix'])
    for opt in opts:
        if opt[0]=='-h' or opt[0]=='--help':
            usage()
            sys.exit(0)
        elif opt[0]=='-v' or opt[0]=='--version':
            print modname+": version="+version_text
        elif opt[0]=='--exec-prefix':
            exec_prefix=opt[1]

    for arg in pargs:
        if arg=='test':
            do_test()
            sys.exit(0)
        elif arg=='doc':
            do_doc()
            sys.exit(0)
        else:
            pass

    main()
