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

Usage:

    ./solstice.py start_year [stop_year]
    
Displays the instants of equinoxes and solstices for a range of years.
Times are accurate to one second.

The arguments must be integers.

If one argument is given, the display is for that year.

If two arguments are given, the display is for that range of
years.
    
"""
import sys

from astronomia.constants import days_per_second
from astronomia.calendar import ut_to_lt, lt_to_str
from astronomia.dynamical import dt_to_ut
from astronomia.equinox import equinox_approx, equinox
from astronomia.sun import Sun
from astronomia.util import load_params
import astronomia.globals

tab = 4 * ' '

if len(sys.argv) < 2:
    print __doc__
    sys.exit()
elif len(sys.argv) < 3:
    start = int(sys.argv[1])
    stop = start
elif len(sys.argv) < 4:
    start = int(sys.argv[1])
    stop = int(sys.argv[2])
else:
    print __doc__
    sys.exit()
    
load_params()
#sun = Sun() # load the database here so we don't get a message later

for yr in range(start, stop + 1):
    print yr
    for season in astronomia.globals.season_names:
        approx_jd = equinox_approx(yr, season)
        jd = equinox(approx_jd, season, days_per_second)
        ut = dt_to_ut(jd)
        lt, zone = ut_to_lt(ut)
        print tab, season, lt_to_str(lt, zone)
