/* Copyright 2000, 2001 William McClain

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
    */

/* Validate Astrolabe routines against examples given in
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

*/

#include "astrolabe.hpp"
#include <cmath>
#include <iomanip>
#include <iostream>

using std::cout;
using std::endl;
using std::setprecision;
using std::string;
using std::vector;
using std::exception;

using astrolabe::calendar::cal_to_day_of_year;
using astrolabe::calendar::cal_to_jd;
using astrolabe::calendar::day_of_year_to_cal;
using astrolabe::calendar::easter;
using astrolabe::calendar::jd_to_cal;
using astrolabe::calendar::jd_to_day_of_week;
using astrolabe::calendar::sidereal_time_greenwich;
using astrolabe::constants::days_per_minute;
using astrolabe::constants::days_per_second;
using astrolabe::constants::km_per_au;
using astrolabe::constants::pi2;
using astrolabe::constants::seconds_per_day;
using astrolabe::dynamical::deltaT_seconds;
using astrolabe::elp2000::ELP2000;
using astrolabe::equinox::equinox_approx;
using astrolabe::equinox::equinox_exact;
using astrolabe::kAutumn;
using astrolabe::kSpring;
using astrolabe::kSummer;
using astrolabe::kWinter;
using astrolabe::nutation::nut_in_lon;
using astrolabe::nutation::nut_in_obl;
using astrolabe::nutation::obliquity;
using astrolabe::nutation::obliquity_hi;
using astrolabe::riseset::rise;
using astrolabe::riseset::set;
using astrolabe::riseset::transit;
using astrolabe::Season;
using astrolabe::sun::aberration_low;
using astrolabe::sun::apparent_longitude_low;
using astrolabe::sun::longitude_radius_low;
using astrolabe::sun::Sun;
using astrolabe::util::dms_to_d;
using astrolabe::util::d_to_dms;
using astrolabe::util::d_to_r;
using astrolabe::util::ecl_to_equ;
using astrolabe::util::equ_to_ecl;
using astrolabe::util::hms_to_fday;
using astrolabe::util::interpolate3;
using astrolabe::util::int_to_string;
using astrolabe::util::load_params;
using astrolabe::util::r_to_d;
using astrolabe::vB;
using astrolabe::vL;
using astrolabe::vR;
using astrolabe::vsop87d::geocentric_planet;
using astrolabe::vsop87d::VSOP87d;
using astrolabe::vsop87d::vsop_to_fk5;
using astrolabe::vVenus;

const string tab = "    ";

void report(const string &label, double computed, double reference, double delta, const string &units) {
    if (fabs(computed - reference) > delta) {
        cout << tab << label << endl;
        cout << tab << tab << "ERROR:" << endl;
        cout << tab << tab << tab << "computed   = " << computed << endl;
        cout << tab << tab << tab << "reference  = " << reference << endl;
        cout << tab << tab << tab << "difference = " << fabs(computed - reference) << " " << units << endl;
        }
    }
        
void report_diff(const string &label, double computed, double reference, const string &units) {
    cout << tab << label << endl;
    cout << tab << tab <<  "Difference: " << setprecision(2) << computed - reference << " " << units << endl;
    }

//
// One of the more unfortunate features of C++ is that template arguments cannot be local types.
// All must be declared at the module level. This is inconvenient when using STL containers.
//
struct Data_8_Easter {
    int yr, mo, day;
    };
    
struct Data_27_Solstice {
    int yr;
    Season season;
    int day;
    double fday;
    };

void _main() {    
    load_params();
    Sun sun;
    VSOP87d vsop;
    ELP2000 elp2000;

    cout << "3.1 Interpolate3" << endl; {
        const double _tbl[] = {0.884226, 0.877366, 0.870531};
        const VECTOR(tbl, double);
        const double y = interpolate3(0.18125, tbl);
        report("au", y, 0.876125, 1e-6, "au");
        }

    cout << "7.a Convert Gregorian date to Julian day number" << endl; {
        const double jd = cal_to_jd(1957, 10, 4.81);
        report("julian day", jd, 2436116.31, 0.01, "days");
        }

    cout << "7.b Convert Julian date to Julian day number" << endl; {
        const double jd = cal_to_jd(333, 1, 27.5, false);
        report("julian day", jd, 1842713.0, 0.01, "days");
        }

    cout << "7.c Convert Julian day number to Gregorian date" << endl; {
        int yr, mo;
        double day;
        jd_to_cal(2436116.31, true, yr, mo, day);
        report("year", yr, 1957, 0, "years");
        report("month", mo, 10, 0, "months");
        report("day", day, 4.81, 0.01, "days");
        }
        
    cout << "7.c(1) Convert Julian day number to Julian date" << endl; {
        int yr, mo;
        double day;
        jd_to_cal(1842713.0, false, yr, mo, day);
        report("year", yr, 333, 0, "years");
        report("month", mo, 1, 0, "months");
        report("day", day, 27.5, 0.01, "days");
        }

    cout << "7.c(2) Convert Julian day number to Julian date" << endl; {
        int yr, mo;
        double day;
        jd_to_cal(1507900.13, false, yr, mo, day);
        report("year", yr, -584, 0, "years");
        report("month", mo, 5, 0, "months");
        report("day", day, 28.63, 0.01, "days");
        }

    cout << "7.d Time interval in days" << endl; {
        const double jd0 = cal_to_jd(1910, 4, 20.0);
        const double jd1 = cal_to_jd(1986, 2, 9.0);
        report("interval", jd1 - jd0, 27689, 0, "days");
        }

    cout << "7.d(1) Time interval in days" << endl; {
        double jd = cal_to_jd(1991, 7, 11);
        jd += 10000;
        int yr, mo;
        double day;
        jd_to_cal(jd, true, yr, mo, day);
        report("year", yr, 2018, 0, "years");
        report("month", mo, 11, 0, "months");
        report("day", day, 26, 0, "days");
        }

    cout << "7.e Day of the week" << endl; {
        const double jd = cal_to_jd(1954, 6, 30.0);
        report("julian day", jd, 2434923.5, 0, "days");
        const int dow = jd_to_day_of_week(jd);
        report("day of week", dow, 3, 0, "days");
        }

    cout << "7.f Day of the year" << endl; {
        const int N = cal_to_day_of_year(1978, 11, 14);
        report("day of the year", N, 318, 0, "days");
        }

    cout << "7.g Day of the year" << endl; {
        const int N = cal_to_day_of_year(1988, 4, 22);
        report("day of the year", N, 113, 0, "days");
        }

    cout << "7(pg 66-1) Day of the year to calendar" << endl; {
        int mo, day;
        day_of_year_to_cal(1978, 318, true, mo, day);
        report("month", mo, 11, 0, "months");
        report("days", day, 14, 0, "days");
        }

    cout << "7(pg 66-2) Day of the year to calendar" << endl; {
        int mo, day;
        day_of_year_to_cal(1988, 113, true, mo, day);
        report("month", mo, 4, 0, "months");
        report("day", day, 22, 0, "days");
        }
        
    cout << "8(pg 68) Gregorian Easter (6 times)" << endl; {
        const Data_8_Easter _tbl[] = { 
            {1991, 3, 31},
            {1992, 4, 19},
            {1993, 4, 11},
            {1954, 4, 18},
            {2000, 4, 23},
            {1818, 3, 22}
            };
        const VECTOR(tbl, Data_8_Easter);
        for (std::vector<Data_8_Easter>::const_iterator p = tbl.begin(); p != tbl.end(); p++) {
            int mo, day;
            easter(p->yr, true, mo, day);
            report("month", mo, p->mo, 0, "months");
            report("day", day, p->day, 0, "days");
            }
        }
        
    cout << "8(pg 69) Julian Easter (3 times)" << endl; {
        const int _tbl[] = {179, 711, 1243};
        const VECTOR(tbl, int);
        for (std::vector<int>::const_iterator p = tbl.begin(); p != tbl.end(); p++) {
            int mo, day;
            easter(*p, false, mo, day);
            report("month", mo, 4, 0, "months");
            report("day", day, 12, 0, "days");
            }
        }

    cout << "10.a DeltaT 1990 (pg 78)" << endl; {
        const double jd = cal_to_jd(1990, 1, 27);
        const double secs = deltaT_seconds(jd);
        report("seconds", secs, 57, 1, "seconds");
        }

    cout << "10.a DeltaT 1977" << endl; {
        const double jd = cal_to_jd(1977, 2, 18);
        const double secs = deltaT_seconds(jd);
        report("seconds", secs, 48, 1, "seconds");
        }
        
    cout << "10.b DeltaT 333" << endl; {
        const double jd = cal_to_jd(333, 2, 6);
        const double secs = deltaT_seconds(jd);
        report("seconds", secs, 6146, 1, "seconds");
        }

    cout << "12.a Sidereal time (mean)" << endl; {
        const double theta0 = sidereal_time_greenwich(2446895.5);
        const double fday = hms_to_fday(13, 10, 46.3668);
        report("sidereal time", theta0 / pi2, fday, 1.0 / (seconds_per_day * 1000), "days");
        }
        
    cout << "12.b Sidereal time (mean)" << endl; {
        const double theta0 = sidereal_time_greenwich(2446896.30625);
        report("sidereal time", theta0 / pi2, 128.7378734 / 360, 1e-7, "days");
        }

    cout << "13.a Equitorial to ecliptical coordinates" << endl; {
        double L, B;
        equ_to_ecl(d_to_r(116.328942), d_to_r(28.026183), d_to_r(23.4392911), L, B);
        report("longitude", r_to_d(L), 113.215630, 1e-6, "degrees");
        report("latitude", r_to_d(B), 6.684170, 1e-6, "degrees");
        }

    cout << "13.a Ecliptical to equitorial coordinates" << endl; {
        double ra, dec;
        ecl_to_equ(d_to_r(113.215630), d_to_r(6.684170), d_to_r(23.4392911), ra, dec);
        report("right accension", r_to_d(ra), 116.328942, 1e-6, "degrees");
        report("declination", r_to_d(dec), 28.026183, 1e-6, "degrees");
        }

    cout << "15.a Rise, Set, Transit" << endl; {
        const double save_Long = astrolabe::globals::longitude;
        const double save_Lat = astrolabe::globals::latitude;
        astrolabe::globals::longitude = d_to_r(71.0833);
        astrolabe::globals::latitude = d_to_r(42.3333);

        const double ut = cal_to_jd(1988, 3, 20);
        const double _raList[] = {d_to_r(40.68021), d_to_r(41.73129), d_to_r(42.78204)};
        const VECTOR(raList, double);
        const double _decList[] = {d_to_r(18.04761), d_to_r(18.44092), d_to_r(18.82742)};
        const VECTOR(decList, double);

        double jd = rise(ut, raList, decList, d_to_r(-0.5667), days_per_minute);
        report("rise, julian days", jd - ut, 0.51766, 1e-5, "days");

        jd = set(ut, raList, decList, d_to_r(-0.5667), days_per_minute);
        report("set, julian days", jd - ut, 0.12130, 1e-5, "days");

        jd = transit(ut, raList, 1.0 / (60 * 24));
        report("transit, julian days", jd - ut, 0.81980, 1e-5, "days");

        astrolabe::globals::longitude = save_Long;
        astrolabe::globals::latitude = save_Lat;
        }

    cout << "22.a Nutation (delta psi)" << endl; {
        const double deltaPsi = nut_in_lon(2446895.5);
        int d, m;
        double s;
        d_to_dms(r_to_d(deltaPsi), d, m, s);
        report("degrees", d, 0, 0, "degrees");
        report("minutes", m, 0, 0, "minutes");
        report("seconds", s, -3.788, 0.001, "seconds");
        }
        
    cout << "22.a Nutation (delta epsilon)" << endl; {
        const double deltaEps = nut_in_obl(2446895.5);
        int d, m;
        double s;
        d_to_dms(r_to_d(deltaEps), d, m, s);
        report("degrees", d, 0, 0, "degrees");
        report("minutes", m, 0, 0, "minutes");
        report("seconds", s, 9.443, 0.001, "seconds");
        }
        
    cout << "22.a Nutation (epsilon)" << endl; {
        const double eps = obliquity(2446895.5);
        int d, m;
        double s;
        d_to_dms(r_to_d(eps), d, m, s);
        report("degrees", d, 23, 0, "degrees");
        report("minutes", m, 26, 0, "minutes");
        report("seconds", s, 27.407, 0.001, "seconds");
        }
        
    cout << "22.a Nutation (epsilon - high precision)" << endl; {
        const double eps = obliquity_hi(2446895.5);
        int d, m;
        double s;
        d_to_dms(r_to_d(eps), d, m, s);
        report("degrees", d, 23, 0, "degrees");
        report("minutes", m, 26, 0, "minutes");
        report("seconds", s, 27.407, 0.001, "seconds");
        }

    cout << "25.a Sun position, low precision" << endl; {
        double L, R;
        longitude_radius_low(2448908.5, L, R);
        report("longitude", r_to_d(L), 199.90988, 1e-5, "degrees");
        report("radius", R, 0.99766, 1e-5, "au");
        L = apparent_longitude_low(2448908.5, L);
        report("longitude", r_to_d(L), 199.90895, 1e-5, "degrees");
        }

    cout << "25.b Sun position, high precision" << endl; {
        double L, B, R;
        sun.dimension3(2448908.5, L, B, R);
        report_diff("longitude", r_to_d(L) * 3600, 199.907372 * 3600, "arc-seconds");
        report_diff("latitude", r_to_d(B) * 3600, 0.644, "arc-seconds");
        report_diff("radius", R * km_per_au, 0.99760775 * km_per_au, "km");
        vsop_to_fk5(2448908.5, L, B);
        report_diff("corrected longitude", r_to_d(L) * 3600, 199.907347 * 3600, "arc-seconds");
        report_diff("corrected latitude", r_to_d(B) * 3600, 0.62, "arc-seconds");
        const double aberration = aberration_low(R);
        report("aberration", r_to_d(aberration) * 3600, -20.539, 0.001, "arc-seconds");

        cout << "25.b Sun position, high precision (complete theory pg 165)" << endl; 
        report("longitude", r_to_d(L) * 3600 * 100, dms_to_d(199, 54, 26.18) * 3600 * 100, 1, "arc-seconds/100");
        report("latitude", r_to_d(B) * 3600 * 100, 0.72 * 100, 1, "arc-seconds/100");
        report("radius", R, 0.99760853, 1e-8, "au");
        }

    cout << "27.a Approximate solstice" << endl; {
        const double jd = equinox_approx(1962, kSummer);
        report("julian day", jd, 2437837.39245, 1e-5, "days");
        }

    cout << "27.a Exact solstice" << endl; {
        const double jd = equinox_exact(2437837.38589, kSummer, days_per_second);
        report("julian day", jd, cal_to_jd(1962, 6, 21) + hms_to_fday(21, 24, 42), 1e-5, "days");
        }

    cout << "27(pg 182) Exact solstice (40 times)" << endl; {
        const Data_27_Solstice _tbl[] = {
            {1996, kSpring, 20, hms_to_fday( 8,  4,  7)},
            {1996, kSummer, 21, hms_to_fday( 2, 24, 46)},
            {1996, kAutumn, 22, hms_to_fday(18,  1,  8)},
            {1996, kWinter, 21, hms_to_fday(14,  6, 56)},
            {1997, kSpring, 20, hms_to_fday(13, 55, 42)},
            {1997, kSummer, 21, hms_to_fday( 8, 20, 59)},
            {1997, kAutumn, 22, hms_to_fday(23, 56, 49)},
            {1997, kWinter, 21, hms_to_fday(20,  8,  5)},
            {1998, kSpring, 20, hms_to_fday(19, 55, 35)},
            {1998, kSummer, 21, hms_to_fday(14,  3, 38)},
            {1998, kAutumn, 23, hms_to_fday( 5, 38, 15)},
            {1998, kWinter, 22, hms_to_fday( 1, 57, 31)},
            {1999, kSpring, 21, hms_to_fday( 1, 46, 53)},
            {1999, kSummer, 21, hms_to_fday(19, 50, 11)},
            {1999, kAutumn, 23, hms_to_fday(11, 32, 34)},
            {1999, kWinter, 22, hms_to_fday( 7, 44, 52)},
            {2000, kSpring, 20, hms_to_fday( 7, 36, 19)},
            {2000, kSummer, 21, hms_to_fday( 1, 48, 46)},
            {2000, kAutumn, 22, hms_to_fday(17, 28, 40)},
            {2000, kWinter, 21, hms_to_fday(13, 38, 30)},
            {2001, kSpring, 20, hms_to_fday(13, 31, 47)},
            {2001, kSummer, 21, hms_to_fday( 7, 38, 48)},
            {2001, kAutumn, 22, hms_to_fday(23,  5, 32)},
            {2001, kWinter, 21, hms_to_fday(19, 22, 34)},
            {2002, kSpring, 20, hms_to_fday(19, 17, 13)},
            {2002, kSummer, 21, hms_to_fday(13, 25, 29)},
            {2002, kAutumn, 23, hms_to_fday( 4, 56, 28)},
            {2002, kWinter, 22, hms_to_fday( 1, 15, 26)},
            {2003, kSpring, 21, hms_to_fday( 1,  0, 50)},
            {2003, kSummer, 21, hms_to_fday(19, 11, 32)},
            {2003, kAutumn, 23, hms_to_fday(10, 47, 53)},
            {2003, kWinter, 22, hms_to_fday( 7,  4, 53)},
            {2004, kSpring, 20, hms_to_fday( 6, 49, 42)},
            {2004, kSummer, 21, hms_to_fday( 0, 57, 57)},
            {2004, kAutumn, 22, hms_to_fday(16, 30, 54)},
            {2004, kWinter, 21, hms_to_fday(12, 42, 40)},
            {2005, kSpring, 20, hms_to_fday(12, 34, 29)},
            {2005, kSummer, 21, hms_to_fday( 6, 47, 12)},
            {2005, kAutumn, 22, hms_to_fday(22, 24, 14)},
            {2005, kWinter, 21, hms_to_fday(18, 36, 01)}
            };
        const VECTOR(tbl, Data_27_Solstice);

        const string season_names[] = {"spring", "summer", "autumn", "winter"};
        const int season_months[] = {3, 6, 9, 12};

        for (std::vector<Data_27_Solstice>::const_iterator p = tbl.begin(); p != tbl.end(); p++) {
            const double approx = equinox_approx(p->yr, p->season);
            const double jd = equinox_exact(approx, p->season, days_per_second);
            report("julian day " + int_to_string(p->yr) + " " + season_names[p->season], jd, 
                cal_to_jd(p->yr, season_months[p->season], p->day + p->fday), days_per_second, "days");
            }
        }

    cout << "32.a Planet position" << endl; {
        double L, B, R;
        vsop.dimension3(2448976.5, vVenus, L, B, R);
        report_diff("longitude", r_to_d(L) * 3600, 26.11428 * 3600, "arc-seconds");
        report_diff("latitude", r_to_d(B) * 3600, -2.62070 * 3600, "arc-seconds");
        report_diff("radius", R * km_per_au, 0.724603 * km_per_au, "km");
        }

    cout << "33.a Apparent position" << endl; {
        double ra, dec;
        geocentric_planet(2448976.5, vVenus, d_to_r(dms_to_d(0, 0, 16.749)), d_to_r(23.439669), days_per_second, ra, dec);
        report("ra", r_to_d(ra), r_to_d(hms_to_fday(21, 4, 41.454) * pi2), 1e-5, "degrees");
        report("dec", r_to_d(dec), dms_to_d(-18, 53, 16.84), 1e-5, "degrees");
        }

    cout << "47.a Moon position" << endl; {
        double L, B, R;
        elp2000.dimension3(2448724.5, L, B, R);
        report_diff("longitude", r_to_d(L) * 3600 * 1000, 133.162655 * 3600 * 1000, "arc-seconds/1000");
        report("latitude", r_to_d(B), -3.229126, 1e-6, "degrees");
        report("radius", R, 368409.7, 0.1, "km");

        L = elp2000.dimension(2448724.5, vL);
        report_diff("longitude(1)", r_to_d(L) * 3600 * 1000, 133.162655 * 3600 * 1000, "arc-seconds/1000");

        B = elp2000.dimension(2448724.5, vB);
        report("latitude(1)", r_to_d(B), -3.229126, 1e-6, "degrees");

        R = elp2000.dimension(2448724.5, vR);
        report("radius(1)", R, 368409.7, 0.1, "km");
        }
    }

int main() {
    try {
        _main();
        }
    catch(const exception &e) {
        cout << e.what() << endl;
        }
    return 0;
    }
