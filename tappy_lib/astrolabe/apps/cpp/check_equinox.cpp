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

/* Check the accuracy of the equinox approximation routines over
4000 years.

Usage:
    
    ./check_equinox

Meeus provides formulae for appromimate solstices and equinoxes for
the years -1000 to 3000. How accurate are they over the whole range
of years?

The test below compares the approximate values with the exact
values as determined by the VSOP87d theory.

Result: The maximum differences is 0.0015 days, or about 2.16 minutes. The
maximum occurred for the summer solstice in -408.

*/

#include <cmath>
#include <ctime>
#include <iostream>
#include "astrolabe.hpp"

using std::string;
using std::cout;
using std::endl;
using std::map;
using std::exception;

using astrolabe::calendar::cal_to_jd;
using astrolabe::constants::days_per_second;
using astrolabe::dicts::seasonToString;
using astrolabe::equinox::equinox_approx;
using astrolabe::equinox::equinox_exact;
using astrolabe::Error;
using astrolabe::kAutumn;
using astrolabe::kSpring;
using astrolabe::kSummer;
using astrolabe::kWinter;
using astrolabe::Season;
using astrolabe::util::int_to_string;
using astrolabe::util::load_params;

class SeasonToMonth {
    public:
        SeasonToMonth() {
            class Data {
                public:
                    Data(Season season, int month) : season(season), month(month) {};

                    Season season;
                    int month;
                };

            const Data tbl[] = {            
                Data(kSpring, 3),
                Data(kSummer, 6),
                Data(kAutumn, 9),
                Data(kWinter, 12)
                };
            for (const Data *p = tbl; p != tbl + ARRAY_SIZE(tbl); p++)
                pmap[p->season] = p->month;
            };
            
        const int &operator[](Season season) const {
            std::map<Season, int>::const_iterator p = pmap.find(season);
            if (p == pmap.end())
                throw Error("SeasonToMonth::const int &operator[]: season out of range = " + int_to_string(season));
            return p->second;
            };

    private:
        map<Season, int> pmap;
    };

const SeasonToMonth seasonToMonth;

void _main() {
    const string tab = "    ";
    load_params();
    const time_t t0 = time(NULL);
    double delta = 0.0;
    for (int yr = -1000; yr < 3000; yr++) {
        if (yr % 100 == 0)
            cout << yr << endl;  // just someting to watch while it runs
        for (int season = kSpring; season <= kWinter; season++) {
            const double approx_jd = equinox_approx(yr, static_cast<Season>(season));
            //
            // We use the 21st of the month as our guess, just in case the
            // approx_jd is wildly off.
            //
            const double jd = equinox_exact(cal_to_jd(yr, seasonToMonth[static_cast<Season>(season)], 21), static_cast<Season>(season), days_per_second);
            const double val = fabs(approx_jd - jd);
            if (val > delta) {
                delta = val;
                cout << tab << "new maximum " << yr << " " << seasonToString[static_cast<Season>(season)] << " " << delta << endl;
                }
            }
        }
    cout << "maximum difference = " << delta << " days" << endl;
    cout << "run time = " << difftime(time(NULL), t0) << " seconds" << endl;
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




