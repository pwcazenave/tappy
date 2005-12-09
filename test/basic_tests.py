#!/usr/bin/env python
"""
NAME:
    basic_tests.py  

SYNOPSIS:
    basic_tests.py

DESCRIPTION:
    Run basic tests

OPTIONS:
    -h,--help        this message
    -v,--version     version

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
import sys,os,getopt,time,string,filecmp
from cStringIO import StringIO
import unittest
import tappy.tappy as model

#===globals======================
modname="basic_tests"
__version__="0.1"

#--option args--
debug_p=1  #hardcoded to bypass unittest

#---positional args, default is empty---
#---other----------------

#===utilities====================
def debug(ftn,txt):
    sys.stdout.write("%s.%s:%s\n" % (modname,ftn,txt))
    sys.stdout.flush()

def fatal(ftn,txt):
    msg="%s.%s:FATAL:%s\n" % (modname,ftn,txt)
    raise SystemExit, msg
 
def usage():
    print __doc__

#====================================
class BasicTestCase(unittest.TestCase):
    #------------------------
    def setUp(self):
        self.olddir=os.getcwd()
        self.obj=model.Tappy()
    #------------------------
    def tearDown(self):
        os.chdir(self.olddir)
        del self.obj
    #------------------------
    def mkfile(self,ftn,model):
        testname=  os.path.join('testdata','test_'  +ftn+'.txt')
        f=open(testname,'w')
        model.run(f)
        f.close()
        
    #------------------------
    def check(self,ftn):
        oraclename=os.path.join('testdata','oracle_'+ftn+'.txt')
        testname=  os.path.join('testdata','test_'  +ftn+'.txt')

        result=filecmp.cmp(oraclename,testname)
        self.assert_(result==1)
    #------------------------
    # Cases
    #------------------------
    def testHello(self):
        ftn='Hello'
        m=self.obj
        self.mkfile(ftn,m)

        self.check(ftn)
        


#=====================================
def suite():
    suite1 = unittest.TestSuite()
    cases=['Hello'
           ]
    
    for c in cases:
        suite1.addTest(BasicTestCase("test%s" % c))
    return suite1

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
