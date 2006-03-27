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
from distutils.core import setup,Extension

#===globals======
modname='setup'
debug_p=0

#===configuration======
pkgname='tappy'
version=string.strip(open("VERSION").readline())
exec_prefix=sys.exec_prefix
description = "Tidal Analysis Program in PYthon"
author = "Tim Cera"
author_email = "timcera@earthlink.net"
url="http://tappy.sourceforge.net"
license = "GPL"

scripts=['tappy.py']
py_modules=['tappy_lib/pyparsing/pyparsing']
packages=['tappy_lib', 'tappy_lib/astrolabe/lib/python/astrolabe']

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
    setup (#---meta-data---
           name = pkgname,
           version = version,
           description = description,
           author = author,
           author_email = author_email,
           url=url,
           license = license,

           #---scripts,modules and packages---
           scripts=scripts,
           py_modules = py_modules,
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
            print modname+": version="+version
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
