#! /usr/bin/env python

"""Copyright 2000, 2001 William McClain

    This file is part of Astrolabe.

    Astrolabe is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Astrolabe is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Astrolabe; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Test the VSOP87d calculations against the check document.

Usage:

    ./check_vsop87d.py vsop87.chk
    
where "vsop87.chk" has been fetched from the ftp directory referenced
at:

    http://cdsweb.u-strasbg.fr/cgi-bin/Cat?VI/81

The program scans through the file and selects those 80 tests which
apply to VSOP87d. We calculate results for each test and compare
with the given value.

Result: all calculations match within 1e-10 radians or au.

"""
import sys
import string

from astrolabe.util import load_params
from astrolabe.vsop87d import VSOP87d

def report(computed, reference, delta):
    if abs(computed - reference) > delta:
        print "\tERROR:"
        print "\t\tcomputed   =", computed
        print "\t\treference  =", reference
        print "\t\tdifference =", abs(computed - reference)
        

if len(sys.argv) != 2:
    print __doc__
    sys.exit()
    
#
# a list of tuples of the form (planet_name, julian_day, longitude, latitude, radius)
# 
refs = []

load_params()

f = file(sys.argv[1])
line = f.readline()
while line:
    fields = line.split()
    if fields:
        if fields[0] == "VSOP87D":
            planet = fields[1]
            planet = planet[0] + planet[1:].lower()
            jd = fields[2]
            jd = float(jd[2:])
            line = f.readline()
            fields = line.split()
            l = float(fields[1])
            b = float(fields[4])
            r = float(fields[7])
            refs.append((planet, jd, l, b, r))
    line = f.readline()
f.close()

print len(refs), "tests"

vsop = VSOP87d()

for planet, jd, l, b, r in refs:
    L, B, R = vsop.dimension3(jd, planet)
    print planet, jd, "L"
    report(L, l, 1e-10)
    print planet, jd, "B"
    report(B, b, 1e-10)
    print planet, jd, "R"
    report(R, r, 1e-10)
    print
    
