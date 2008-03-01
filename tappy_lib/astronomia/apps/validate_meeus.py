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

Validate Astrolabe routines against examples given in
_Astronomical Algorithms_ by Jean Meeus, second edition 1998,
Willmann-Bell Inc.

Where testing shows no differences between Meeus and the Astrolabe
results (to the precision printed in Meeus), I have used the report()
routine to verify the results.

In some cases I do show small differences and display these with the
report_diff() routine. The differences do not seem to be of any consequential
sizes, but are inexplicable. I speculate they may be caused by:

    1. Errors in Astrolabe code
    2. Misprints in the book
    3. Differences in math libraries (which seems unlikely, in
        that I get the same values on different platforms)
        
Attached to the bottom of this script is the output I get.
    
Note that Meeus presents a truncated version of VSOP87d and some differences
are to be expected when comparing results with the complete version that
Astrolabe uses. He sometimes prints values are derived from the complete
theory, and we use those where possible.

"""
from astronomia.constants import pi2, seconds_per_day, km_per_au, days_per_second, days_per_minute
from astronomia.calendar import cal_to_jd, jd_to_cal, jd_to_day_of_week, cal_to_day_of_year, day_of_year_to_cal, easter, sidereal_time_greenwich
from astronomia.dynamical import deltaT_seconds
from astronomia.elp2000 import ELP2000
from astronomia.equinox import equinox_approx, equinox
from astronomia.nutation import nut_in_lon, nut_in_obl, obliquity, obliquity_hi
from astronomia.riseset import transit, rise, set
from astronomia.sun import longitude_radius_low, apparent_longitude_low, aberration_low, Sun
from astronomia.util import load_params, hms_to_fday, equ_to_ecl, r_to_d, d_to_r, d_to_dms, dms_to_d, ecl_to_equ, interpolate3
from astronomia.vsop87d import vsop_to_fk5, VSOP87d, geocentric_planet

import astronomia.globals

tab = 4 * ' '

def report(label, computed, reference, delta, units):
    if abs(computed - reference) > delta:
        print tab, label
        print 2 * tab, "ERROR:"
        print 3 * tab, "computed   =", computed
        print 3 * tab, "reference  =", reference
        print 3 * tab, "difference =", abs(computed - reference), units
    
def report_diff(label, computed, reference, units):
    print tab, label
    print 2 * tab, "Difference: %.2f %s" % ((computed) - reference, units)
    
load_params()
sun = Sun()
vsop = VSOP87d()

print "3.1 Interpolate3"
y = interpolate3(0.18125, (0.884226, 0.877366, 0.870531))
report("au", y, 0.876125, 1e-6, "au")
        
print "7.a Convert Gregorian date to Julian day number"
jd = cal_to_jd(1957, 10, 4.81)
report("julian day", jd, 2436116.31, 0.01, "days")

print "7.b Convert Julian date to Julian day number"
jd = cal_to_jd(333, 1, 27.5, False)
report("julian day", jd, 1842713.0, 0.01, "days")

print "7.c Convert Julian day number to Gregorian date"
yr, mo, day = jd_to_cal(2436116.31)
report("year", yr, 1957, 0, "years")
report("month", mo, 10, 0, "months")
report("day", day, 4.81, 0.01, "days")

print "7.c(1) Convert Julian day number to Julian date"
yr, mo, day = jd_to_cal(1842713.0, False)
report("year", yr, 333, 0, "years")
report("month", mo, 1, 0, "months")
report("day", day, 27.5, 0.01, "days")

print "7.c(2) Convert Julian day number to Julian date"
yr, mo, day = jd_to_cal(1507900.13, False)
report("year", yr, -584, 0, "years")
report("month", mo, 5, 0, "months")
report("day", day, 28.63, 0.01, "days")

print "7.d Time interval in days"
jd0 = cal_to_jd(1910, 4, 20.0)
jd1 = cal_to_jd(1986, 2, 9.0)
report("interval", jd1 - jd0, 27689, 0, "days")

print "7.d(1) Time interval in days"
jd = cal_to_jd(1991, 7, 11)
jd = jd + 10000
yr, mo, day = jd_to_cal(jd)
report("year", yr, 2018, 0, "years")
report("month", mo, 11, 0, "months")
report("day", day, 26, 0, "days")

print "7.e Day of the week"
jd = cal_to_jd(1954, 6, 30.0)
report("julian day", jd, 2434923.5, 0, "days")
dow = jd_to_day_of_week(jd)
report("day of week", dow, 3, 0, "days")

print "7.f Day of the year"
N = cal_to_day_of_year(1978, 11, 14)
report("day of the year", N, 318, 0, "days")

print "7.g Day of the year"
N = cal_to_day_of_year(1988, 4, 22)
report("day of the year", N, 113, 0, "days")

print "7(pg 66-1) Day of the year to calendar"
mo, day = day_of_year_to_cal(1978, 318)
report("month", mo, 11, 0, "months")
report("days", day, 14, 0, "days")

print "7(pg 66-2) Day of the year to calendar"
mo, day = day_of_year_to_cal(1988, 113)
report("month", mo, 4, 0, "months")
report("day", day, 22, 0, "days")

tbl = ( \
    (1991, 3, 31),
    (1992, 4, 19),
    (1993, 4, 11),
    (1954, 4, 18),
    (2000, 4, 23),
    (1818, 3, 22))
    
print "8(pg 68) Gregorian Easter (6 times)"
for yr, mo, day in tbl:
    xmo, xday = easter(yr)
    report("month", xmo, mo, 0, "months")
    report("day", xday, day, 0, "days")

print "8(pg 69) Julian Easter (3 times)"
for yr in [179, 711, 1243]:
    mo, day = easter(yr, False)
    report("month", mo, 4, 0, "months")
    report("day", day, 12, 0, "days")

print "10.a DeltaT 1990 (pg 78)"
jd = cal_to_jd(1990, 1, 27)
secs = deltaT_seconds(jd)
report("seconds", secs, 57, 1, "seconds")

print "10.a DeltaT 1977"
jd = cal_to_jd(1977, 2, 18)
secs = deltaT_seconds(jd)
report("seconds", secs, 48, 1, "seconds")

print "10.b DeltaT 333"
jd = cal_to_jd(333, 2, 6)
secs = deltaT_seconds(jd)
report("seconds", secs, 6146, 1, "seconds")

print "12.a Sidereal time (mean)"
theta0 = sidereal_time_greenwich(2446895.5)
fday = hms_to_fday(13, 10, 46.3668)
report("sidereal time", theta0 / pi2, fday, 1.0 / (seconds_per_day * 1000), "days")

print "12.b Sidereal time (mean)"
theta0 = sidereal_time_greenwich(2446896.30625)
report("sidereal time", theta0 / pi2, 128.7378734 / 360, 1e-7, "days")

print "13.a Equitorial to ecliptical coordinates"
L, B = equ_to_ecl(d_to_r(116.328942), d_to_r(28.026183), d_to_r(23.4392911))
report("longitude", r_to_d(L), 113.215630, 1e-6, "degrees")
report("latitude", r_to_d(B), 6.684170, 1e-6, "degrees")

print "13.a Ecliptical to equitorial coordinates"
ra, dec = ecl_to_equ(d_to_r(113.215630), d_to_r(6.684170), d_to_r(23.4392911))
report("right accension", r_to_d(ra), 116.328942, 1e-6, "degrees")
report("declination", r_to_d(dec), 28.026183, 1e-6, "degrees")

print "15.a Rise, Set, Transit"
save_Long = astronomia.globals.longitude
save_Lat = astronomia.globals.latitude
astronomia.globals.longitude = d_to_r(71.0833)
astronomia.globals.latitude = d_to_r(42.3333)

ut = cal_to_jd(1988, 3, 20)
raList = (d_to_r(40.68021), d_to_r(41.73129), d_to_r(42.78204))
decList = (d_to_r(18.04761), d_to_r(18.44092), d_to_r(18.82742))

jd = rise(ut, raList, decList, d_to_r(-0.5667), days_per_minute)
report("rise, julian days", jd - ut, 0.51766, 1e-5, "days")

jd = set(ut, raList, decList, d_to_r(-0.5667), days_per_minute)
report("set, julian days", jd - ut, 0.12130, 1e-5, "days")

jd = transit(ut, raList, 1.0 / (60 * 24))
report("transit, julian days", jd - ut, 0.81980, 1e-5, "days")

astronomia.globals.longitude = save_Long
astronomia.globals.latitude = save_Lat

print "22.a Nutation (delta psi)"
deltaPsi = nut_in_lon(2446895.5)
d, m, s = d_to_dms(r_to_d(deltaPsi))
report("degrees", d, 0, 0, "degrees")
report("minutes", m, 0, 0, "minutes")
report("seconds", s, -3.788, 0.001, "seconds")

print "22.a Nutation (delta epsilon)"
deltaEps = nut_in_obl(2446895.5)
d, m, s = d_to_dms(r_to_d(deltaEps))
report("degrees", d, 0, 0, "degrees")
report("minutes", m, 0, 0, "minutes")
report("seconds", s, 9.443, 0.001, "seconds")

print "22.a Nutation (epsilon)"
eps = obliquity(2446895.5)
d, m, s = d_to_dms(r_to_d(eps))
report("degrees", d, 23, 0, "degrees")
report("minutes", m, 26, 0, "minutes")
report("seconds", s, 27.407, 0.001, "seconds")

print "22.a Nutation (epsilon - high precision)"
eps = obliquity_hi(2446895.5)
d, m, s = d_to_dms(r_to_d(eps))
report("degrees", d, 23, 0, "degrees")
report("minutes", m, 26, 0, "minutes")
report("seconds", s, 27.407, 0.001, "seconds")

print "25.a Sun position, low precision"
L, R = longitude_radius_low(2448908.5)
report("longitude", r_to_d(L), 199.90988, 1e-5, "degrees")
report("radius", R, 0.99766, 1e-5, "au")
L = apparent_longitude_low(2448908.5, L)
report("longitude", r_to_d(L), 199.90895, 1e-5, "degrees")

print "25.b Sun position, high precision"
L, B, R = sun.dimension3(2448908.5)
report_diff("longitude", r_to_d(L) * 3600, 199.907372 * 3600, "arc-seconds")
report_diff("latitude", r_to_d(B) * 3600, 0.644, "arc-seconds")
report_diff("radius", R * km_per_au, 0.99760775 * km_per_au, "km")
L, B = vsop_to_fk5(2448908.5, L, B)
report_diff("corrected longitude", r_to_d(L) * 3600, 199.907347 * 3600, "arc-seconds")
report_diff("corrected latitude", r_to_d(B) * 3600, 0.62, "arc-seconds")
aberration = aberration_low(R)
report("aberration", r_to_d(aberration) * 3600, -20.539, 0.001, "arc-seconds")

print "25.b Sun position, high precision (complete theory pg 165)"
report("longitude", r_to_d(L) * 3600 * 100, dms_to_d(199, 54, 26.18) * 3600 * 100, 1, "arc-seconds/100")
report("latitude", r_to_d(B) * 3600 * 100, 0.72 * 100, 1, "arc-seconds/100")
report("radius", R, 0.99760853, 1e-8, "au")

print "27.a Approximate solstice"
jd = equinox_approx(1962, "summer")
report("julian day", jd, 2437837.39245, 1e-5, "days")

print "27.a Exact solstice"
jd = equinox(2437837.38589, "summer", days_per_second)
report("julian day", jd, cal_to_jd(1962, 6, 21) + hms_to_fday(21, 24, 42), 1e-5, "days")

tbl = [ \
    (1996, 
        (("spring", 20, hms_to_fday( 8,  4,  7)),
        ("summer",  21, hms_to_fday( 2, 24, 46)),
        ("autumn",  22, hms_to_fday(18,  1,  8)),
        ("winter",  21, hms_to_fday(14,  6, 56)))),
    (1997,
        (("spring", 20, hms_to_fday(13, 55, 42)),
        ("summer",  21, hms_to_fday( 8, 20, 59)),
        ("autumn",  22, hms_to_fday(23, 56, 49)),
        ("winter",  21, hms_to_fday(20,  8,  5)))),
    (1998,
        (("spring", 20, hms_to_fday(19, 55, 35)),
        ("summer",  21, hms_to_fday(14,  3, 38)),
        ("autumn",  23, hms_to_fday( 5, 38, 15)),
        ("winter",  22, hms_to_fday( 1, 57, 31)))),
    (1999,
        (("spring", 21, hms_to_fday( 1, 46, 53)),
        ("summer",  21, hms_to_fday(19, 50, 11)),
        ("autumn",  23, hms_to_fday(11, 32, 34)),
        ("winter",  22, hms_to_fday( 7, 44, 52)))),
    (2000,
        (("spring", 20, hms_to_fday( 7, 36, 19)),
        ("summer",  21, hms_to_fday( 1, 48, 46)),
        ("autumn",  22, hms_to_fday(17, 28, 40)),
        ("winter",  21, hms_to_fday(13, 38, 30)))),
    (2001,
        (("spring", 20, hms_to_fday(13, 31, 47)),
        ("summer",  21, hms_to_fday( 7, 38, 48)),
        ("autumn",  22, hms_to_fday(23,  5, 32)),
        ("winter",  21, hms_to_fday(19, 22, 34)))),
    (2002,
        (("spring", 20, hms_to_fday(19, 17, 13)),
        ("summer",  21, hms_to_fday(13, 25, 29)),
        ("autumn",  23, hms_to_fday( 4, 56, 28)),
        ("winter",  22, hms_to_fday( 1, 15, 26)))),
    (2003,
        (("spring", 21, hms_to_fday( 1,  0, 50)),
        ("summer",  21, hms_to_fday(19, 11, 32)),
        ("autumn",  23, hms_to_fday(10, 47, 53)),
        ("winter",  22, hms_to_fday( 7,  4, 53)))),
    (2004,
        (("spring", 20, hms_to_fday( 6, 49, 42)),
        ("summer",  21, hms_to_fday( 0, 57, 57)),
        ("autumn",  22, hms_to_fday(16, 30, 54)),
        ("winter",  21, hms_to_fday(12, 42, 40)))),
    (2005,
        (("spring", 20, hms_to_fday(12, 34, 29)),
        ("summer",  21, hms_to_fday( 6, 47, 12)),
        ("autumn",  22, hms_to_fday(22, 24, 14)),
        ("winter",  21, hms_to_fday(18, 36, 01))))]

months = {"spring" : 3,  "summer" : 6, "autumn" : 9, "winter" : 12}
       
print "27(pg 182) Exact solstice (40 times)"
for yr, terms in tbl:
    for season, day, fday in terms:
        approx = equinox_approx(yr, season)
        jd = equinox(approx, season, days_per_second)
        report("julian day %d %s" % (yr, season), jd, cal_to_jd(yr, months[season], day + fday), days_per_second, "days")
    
print "32.a Planet position"
L, B, R = vsop.dimension3(2448976.5, "Venus")
report_diff("longitude", r_to_d(L) * 3600, 26.11428 * 3600, "arc-seconds")
report_diff("latitude", r_to_d(B) * 3600, -2.62070 * 3600, "arc-seconds")
report_diff("radius", R * km_per_au, 0.724603 * km_per_au, "km")

print "33.a Apparent position"
ra, dec = geocentric_planet(2448976.5, "Venus", d_to_r(dms_to_d(0, 0, 16.749)), d_to_r(23.439669), days_per_second)
report("ra", r_to_d(ra), r_to_d(hms_to_fday(21, 4, 41.454) * pi2), 1e-5, "degrees")
report("dec", r_to_d(dec), dms_to_d(-18, 53, 16.84), 1e-5, "degrees")

elp2000 = ELP2000()
print "47.a Moon position"
L, B, R = elp2000.dimension3(2448724.5)
report_diff("longitude", r_to_d(L) * 3600 * 1000, 133.162655 * 3600 * 1000, "arc-seconds/1000")
report("latitude", r_to_d(B), -3.229126, 1e-6, "degrees")
report("radius", R, 368409.7, 0.1, "km")

L = elp2000.dimension(2448724.5, "L")
report_diff("longitude(1)", r_to_d(L) * 3600 * 1000, 133.162655 * 3600 * 1000, "arc-seconds/1000")

B = elp2000.dimension(2448724.5, "B")
report("latitude(1)", r_to_d(B), -3.229126, 1e-6, "degrees")

R = elp2000.dimension(2448724.5, "R")
report("radius(1)", R, 368409.7, 0.1, "km")


"""
Here are my results:

loading binary db...
3.1 Interpolate3
7.a Convert Gregorian date to Julian day number
7.b Convert Julian date to Julian day number
7.c Convert Julian day number to Gregorian date
7.c(1) Convert Julian day number to Julian date
7.c(2) Convert Julian day number to Julian date
7.d Time interval in days
7.d(1) Time interval in days
7.e Day of the week
7.f Day of the year
7.g Day of the year
7(pg 66-1) Day of the year to calendar
7(pg 66-2) Day of the year to calendar
8(pg 68) Gregorian Easter (6 times)
8(pg 69) Julian Easter (3 times)
10.a DeltaT 1990 (pg 78)
10.a DeltaT 1977
10.b DeltaT 333
12.a Sidereal time (mean)
12.b Sidereal time (mean)
13.a Equitorial to ecliptical coordinates
13.a Ecliptical to equitorial coordinates
15.a Rise, Set, Transit
22.a Nutation (delta psi)
22.a Nutation (delta epsilon)
22.a Nutation (epsilon)
22.a Nutation (epsilon - high precision)
25.a Sun position, low precision
25.b Sun position, high precision
     longitude
         Difference: -0.27 arc-seconds
     latitude
         Difference: 0.10 arc-seconds
     radius
         Difference: 115.23 km
     corrected longitude
         Difference: -0.27 arc-seconds
     corrected latitude
         Difference: 0.10 arc-seconds
25.b Sun position, high precision (complete theory pg 165)
     longitude
         Difference: 0.09 arc-seconds
     latitude
         Difference: 0.02 arc-seconds
     radius
         Difference: -1.46 km
27.a Approximate solstice
27.a Exact solstice
27(pg 182) Exact solstice (40 times)
32.a Planet position
     longitude
         Difference: -0.58 arc-seconds
     latitude
         Difference: 0.35 arc-seconds
     radius
         Difference: -198.07 km
33.a Apparent position
47.a Moon position
     longitude
         Difference: -4.05 arc-seconds/1000
     longitude(1)
         Difference: -4.05 arc-seconds/1000
"""
