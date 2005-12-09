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

/* Usage:

    ./solstice start_year [stop_year]
    
Displays the instants of equinoxes and solstices for a range of years.
Times are accurate to one second.

The arguments must be integers.

If one argument is given, the display is for that year.

If two arguments are given, the display is for that range of
years.
    
*/

#include "astrolabe.hpp"
#include <cstdlib>
#include <iostream>

using std::string;
using std::cout;
using std::endl;
using std::exception;

using astrolabe::calendar::lt_to_str;
using astrolabe::calendar::ut_to_lt;
using astrolabe::constants::days_per_second;
using astrolabe::dicts::seasonToString;
using astrolabe::dynamical::dt_to_ut;
using astrolabe::equinox::equinox_approx;
using astrolabe::equinox::equinox_exact;
using astrolabe::kSpring;
using astrolabe::kWinter;
using astrolabe::Season;
using astrolabe::util::load_params;

const string tab = "    ";

void usage() {
    cout << "Usage:" << endl;
    cout << endl;
    cout << "    ./solstice start_year [stop_year]" << endl;
    cout << endl;
    cout << "Displays the instants of equinoxes and solstices for a range of years." << endl;
    cout << "Times are accurate to one second." << endl;
    cout << endl;
    cout << "The arguments must be integers." << endl;
    cout << endl;
    cout << "If one argument is given, the display is for that year." << endl;
    cout << endl;
    cout << "If two arguments are given, the display is for that range of" << endl;
    cout << "years." << endl;
    }

void _main(int argc, char *argv[]) {
    int start, stop;
    if (argc < 2) {
        usage();
        exit(EXIT_FAILURE);
        }
    else if (argc < 3) {
        start = atoi(argv[1]);
        stop = start;
        }
    else if (argc < 4) {
        start = atoi(argv[1]);
        stop = atoi(argv[2]);
        }
    else {
        usage();
        exit(EXIT_FAILURE);
        }

    load_params();
    for (int yr = start; yr <= stop; yr++) {
        cout << yr << endl;
        for (int season = kSpring; season <= kWinter; season++) {
            const double approx_jd = equinox_approx(yr, static_cast<Season>(season));
            const double jd = equinox_exact(approx_jd, static_cast<Season>(season), days_per_second);
            const double ut = dt_to_ut(jd);
            double lt;
            string zone;
            ut_to_lt(ut, lt, zone);
            cout << tab << seasonToString[static_cast<Season>(season)] << " " << lt_to_str(lt, zone) << endl;
            }
        }
    }

int main(int argc, char *argv[]) {
    try {
        _main(argc, argv);
        }
    catch(const exception &e) {
        cout << e.what() << endl;
        }
    return 0;
    }
