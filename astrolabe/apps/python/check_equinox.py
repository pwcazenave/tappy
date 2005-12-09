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

Check the accuracy of the equinox approximation routines over
4000 years.

Usage:
    
    ./check_equinox.py

Meeus provides formulae for appromimate solstices and equinoxes for
the years -1000 to 3000. How accurate are they over the whole range
of years?

The test below compares the approximate values with the exact
values as determined by the VSOP87d theory.

Result: The maximum differences is 0.0015 days, or about 2.16 minutes. The
maximum occurred for the summer solstice in -408.

"""
import time
from astrolabe.calendar import cal_to_jd
from astrolabe.util import load_params
from astrolabe.equinox import equinox_approx, equinox
from astrolabe.constants import days_per_second
import astrolabe.globals

tab = 4 * ' '
load_params()

months = { \
    "spring" : 3, 
    "summer" : 6, 
    "autumn" : 9, 
    "winter" : 12}

t0 = time.time()
delta = 0.0
for yr in range(-1000, 3000):
    if yr % 100 == 0:
        print yr   # just someting to watch while it runs
    for season in astrolabe.globals.season_names:
        approx_jd = equinox_approx(yr, season)
        #
        # We use the 21st of the month as our guess, just in case the
        # approx_jd is wildly off.
        #
        jd = equinox(cal_to_jd(yr, months[season], 21), season, days_per_second)
        val = abs(approx_jd - jd)
        if val > delta:
            delta = val
            print tab, "new maximum", yr, season, delta
            
print "maximum difference =", delta, "days"
print "run time = %.2f seconds" % (time.time() - t0,)
