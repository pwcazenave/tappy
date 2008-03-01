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

A clock application that displays a variety of celestial events in the
order they occur.

Usage:

    ./cronus.py start_year [stop_year]
    
To do:
    -- Add many more events
    -- Support both real-time and "fast" modes
    -- Allow finer start and stop times
    
Currently the program always runs in "fast" mode, queueing and
displaying events in the future as fast as possible. Eventually
I would like to have enough events covered so that the display 
runs continuously even in real-time. Since the next event of
a given type needs to be calculated only when the previous one
has been delivered, this is not as computationally intense as it
sounds.

"""
import sys
from heapq import heappush, heappop
from math import *

from astronomia.calendar import easter, cal_to_jd, ut_to_lt, lt_to_str
from astronomia.constants import days_per_second, days_per_minute, standard_rst_altitude, sun_rst_altitude
from astronomia.dynamical import dt_to_ut
from astronomia.elp2000 import ELP2000
from astronomia.equinox import equinox_approx, equinox
from astronomia.nutation import nut_in_lon, nut_in_obl, obliquity
from astronomia.riseset import rise, set, transit, moon_rst_altitude
from astronomia.sun import Sun, aberration_low
from astronomia.util import ecl_to_equ, d_to_r
from astronomia.vsop87d import VSOP87d, geocentric_planet, vsop_to_fk5, planet_names
from astronomia.util import load_params
import astronomia.globals

vsop = None # delay loading this until we are sure the script can run
sun = None  #  "                  "
moon = ELP2000()

HIGH_PRIORITY = 0.0

rstDict = {}

class Task:
    def __init__(self, jd, func, args):
        self.jd = jd
        self.func = func
        self.args = args
        
    def __cmp__(self, other):
        return cmp(self.jd, other.jd)

taskQueue = []

class RiseSetTransit:
    def __init__(self, name, raList, decList, h0List):
        self.name = name
        self.raList = raList
        self.decList = decList
        self.h0List = h0List

def display(str):
    print str

def doEaster(year):
    month, day = easter(year)
    jd = cal_to_jd(year, month, day)
    str = "%-24s %s" % (lt_to_str(jd, None, "day"), "Easter")
    heappush(taskQueue, Task(jd, display, (str,)))
    # recalculate on March 1, next year
    heappush(taskQueue, Task(cal_to_jd(year + 1, 3, 1), doEaster, (year + 1,)))
    
_seasons = {"spring": "Vernal Equinox", "summer": "Summer Solstice",
            "autumn": "Autumnal Equinox", "winter": "Winter Solstice"}
            
def doEquinox(year, season):
    approx_jd = equinox_approx(year, season)
    jd = equinox(approx_jd, season, days_per_second)
    ut = dt_to_ut(jd)
    lt, zone = ut_to_lt(ut)
    str = lt_to_str(lt, zone) + " " + _seasons[season]
    heappush(taskQueue, Task(jd, display, (str,)))
    heappush(taskQueue, Task(jd, doEquinox, (year + 1, season)))

def doRiseSetTransit(jd_today):
    #
    # Find and queue rise-set-transit times for all objects
    #
    jd = jd_today
    for obj in rstDict.values():
        td = rise(jd, obj.raList, obj.decList, obj.h0List[1], days_per_minute)
        if td:
            ut = dt_to_ut(td)
            lt, zone = ut_to_lt(ut)
            str = "%-20s %s %s rises" % (lt_to_str(lt, "", "minute"), zone, obj.name)
            heappush(taskQueue, Task(td, display, (str,)))
        else:
            print "****** RiseSetTransit failure:", obj.name, "rise"
            
        td = set(jd, obj.raList, obj.decList, obj.h0List[1], days_per_minute)
        if td:
            ut = dt_to_ut(td)
            lt, zone = ut_to_lt(ut)
            str = "%-20s %s %s sets" % (lt_to_str(lt, "", "minute"), zone, obj.name)
            heappush(taskQueue, Task(td, display, (str,)))
        else:
            print "****** RiseSetTransit failure:", obj.name, "set"

        td = transit(jd, obj.raList, days_per_second)
        if td:
            ut = dt_to_ut(td)
            lt, zone = ut_to_lt(ut)
            str = "%-24s %s transits" % (lt_to_str(lt, zone), obj.name)
            heappush(taskQueue, Task(td, display, (str,)))
        else:
            print "****** RiseSetTransit failure:", obj.name, "transit"

    #
    # setup the day after tomorrow
    #
    jd += 2
    
    # nutation in longitude
    deltaPsi = nut_in_lon(jd)
    
    # apparent obliquity
    eps = obliquity(jd) + nut_in_obl(jd)
    
    #
    # Planets
    #
    for planet in planet_names:
        if planet == "Earth":
            continue
        ra, dec = geocentric_planet(jd, planet, deltaPsi, eps, days_per_second)
        obj = rstDict[planet]
        del obj.raList[0]
        del obj.decList[0]
        del obj.h0List[0]
        obj.raList.append(ra)
        obj.decList.append(dec)
        obj.h0List.append(standard_rst_altitude)
    #
    # Moon
    #
    l, b, r = moon.dimension3(jd)
    
    # nutation in longitude
    l += deltaPsi

    # equatorial coordinates
    ra, dec = ecl_to_equ(l, b, eps)
    
    obj = rstDict["Moon"]
    del obj.raList[0]
    del obj.decList[0]
    del obj.h0List[0]
    obj.raList.append(ra)
    obj.decList.append(dec)
    obj.h0List.append(moon_rst_altitude(r))
    
    #
    # Sun
    #
    l, b, r = sun.dimension3(jd)

    # correct vsop coordinates    
    l, b = vsop_to_fk5(jd, l, b)

    # nutation in longitude
    l += deltaPsi
    
    # aberration
    l += aberration_low(r)

    # equatorial coordinates
    ra, dec = ecl_to_equ(l, b, eps)
    
    obj = rstDict["Sun"]
    del obj.raList[0]
    del obj.decList[0]
    del obj.h0List[0]
    obj.raList.append(ra)
    obj.decList.append(dec)
    obj.h0List.append(sun_rst_altitude)
    
    heappush(taskQueue, Task(jd, doRiseSetTransit, (jd_today + 1,)))

def initRST(start_year):    
    start_jd = cal_to_jd(start_year)
    
    #
    # We need nutation values for each of three days
    # 
    nutation = {}
    for day in (-1, 0, 1):
        jd = start_jd + day
        # nutation in longitude
        deltaPsi = nut_in_lon(jd)
        # apparent obliquity
        eps = obliquity(jd) + nut_in_obl(jd)
        nutation[day] = deltaPsi, eps
        
    #
    # Planets
    #
    for planet in planet_names:
        if planet == "Earth":
            continue
        raList = []
        decList = []
        h0List = []
        for day in (-1, 0, 1):
            jd = start_jd + day
            deltaPsi, eps = nutation[day]
            ra, dec = geocentric_planet(jd, planet, deltaPsi, eps, days_per_second)
            raList.append(ra)
            decList.append(dec)
            h0List.append(standard_rst_altitude)
        rstDict[planet] = RiseSetTransit(planet, raList, decList, h0List)

    #
    # Moon
    #
    raList = []
    decList = []
    h0List = []
    for day in (-1, 0, 1):
        jd = start_jd + day
        deltaPsi, eps = nutation[day]
        l, b, r = moon.dimension3(jd)
        # nutation in longitude
        l += deltaPsi
        # equatorial coordinates
        ra, dec = ecl_to_equ(l, b, eps)
        raList.append(ra)
        decList.append(dec)
        h0List.append(moon_rst_altitude(r))
    rstDict["Moon"] = RiseSetTransit("Moon", raList, decList, h0List)

    #
    # Sun
    #
    raList = []
    decList = []
    h0List = []
    for day in (-1, 0, 1):
        jd = start_jd + day
        deltaPsi, eps = nutation[day]
        l, b, r = sun.dimension3(jd)
        # correct vsop coordinates    
        l, b = vsop_to_fk5(jd, l, b)
        # nutation in longitude
        l += deltaPsi
        # aberration
        l += aberration_low(r)
        # equatorial coordinates
        ra, dec = ecl_to_equ(l, b, eps)
        raList.append(ra)
        decList.append(dec)
        h0List.append(sun_rst_altitude)
    rstDict["Sun"] = RiseSetTransit("Sun", raList, decList, h0List)
    
    # all Rise-Set-Transit events
    heappush(taskQueue, Task(HIGH_PRIORITY, doRiseSetTransit, (start_jd,)))
    
def run():
    global vsop
    global sun
    if len(sys.argv) < 2:
        print __doc__
        sys.exit()
    if len(sys.argv) < 3:
        start_year = int(sys.argv[1])
        stop_jd = cal_to_jd(10000) # default stopping date: 10,000AD
    elif len(sys.argv) < 4:
        start_year = int(sys.argv[1])
        stop_jd = cal_to_jd(int(sys.argv[2]))
    else:
        print __doc__
        sys.exit()

    load_params()
    vsop = VSOP87d()
    sun = Sun()

    # Easter
    heappush(taskQueue, Task(HIGH_PRIORITY, doEaster, (start_year,)))
    
    # four equinox/solstice events
    for season in astronomia.globals.season_names:
        heappush(taskQueue, Task(HIGH_PRIORITY, doEquinox, (start_year, season)))

    # initialize rise-set-transit objects  
    initRST(start_year);
        
    # start the task loop        
    t = heappop(taskQueue)
    while t.jd < stop_jd:
        #apply(t.func, t.args)   
        t.func(*t.args)   
        t = heappop(taskQueue)

run()
