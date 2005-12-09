#!/usr/bin/env python
"""
NAME:
    all_tests.py  

SYNOPSIS:
    all_tests.py

DESCRIPTION:
    Run all unit tests

OPTIONS:
    -h,--help        this message
    -v,--version     version


EXAMPLES:
    1. As standalone
         all_tests.py

#Copyright (C) 2005  Tim Cera timcera@earthlink.net
#http://tappy.sourceforge.net
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


"""
#===imports======================
import sys,os,getopt,time,string
import unittest
sys.path.insert(0,"..")

#===globals======================
modname="all_tests"
__version__="0.1"

#--option args--
debug_p=1  #hardcoded to bypass unittest

#---positional args, default is empty---
pargs=[]    


#===utilities====================
def msg(txt):
    sys.stdout.write(txt)
    sys.stdout.flush()

def debug(ftn,txt):
    if debug_p:
        sys.stdout.write("%s.%s:%s\n" % (modname,ftn,txt))
        sys.stdout.flush()

def fatal(ftn,txt):
    msg="%s.%s:FATAL:%s\n" % (modname,ftn,txt)
    raise SystemExit, msg
 
def usage():
    print __doc__
#====================================
def suite():
    modules_to_test=('basic_tests',)
    alltests=unittest.TestSuite()
    for module in map(__import__, modules_to_test):
        alltests.addTest(module.suite())
    return alltests

#=============================
def main():
    unittest.main(defaultTest='suite')

#-------------------------
if __name__ == '__main__':
    ftn = "main"
    opts,pargs=getopt.getopt(sys.argv[1:],'hv',
                 ['help','version'])
    for opt in opts:
        if opt[0]=='-h' or opt[0]=='--help':
            print modname+": version="+__version__
            usage()
            sys.exit(0)
        elif opt[0]=='-v' or opt[0]=='--version':
            print modname+": version="+__version__
            sys.exit(0)

    #---make the object and run it---
    main()
