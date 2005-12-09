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

/* Test the VSOP87d calculations against the check document.

Usage:

    ./check_vsop87d vsop87.chk
    
where "vsop87.chk" has been fetched from the ftp directory referenced
at:

    http://cdsweb.u-strasbg.fr/cgi-bin/Cat?VI/81

The program scans through the file and selects those 80 tests which
apply to VSOP87d. We calculate results for each test and compare
with the given value.

Result: all calculations match within 1e-10 radians or au.

*/

#include "astrolabe.hpp"
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <list>

using std::string;
using std::vector;
using std::ifstream;
using std::list;
using std::cout;
using std::endl;
using std::getline;
using std::exception;

using astrolabe::vPlanets;
using astrolabe::util::load_params;
using astrolabe::vsop87d::VSOP87d;
using astrolabe::Error;
using astrolabe::util::split;
using astrolabe::util::lower;
using astrolabe::util::string_to_double;
using astrolabe::dicts::stringToPlanet;

void report(double computed, double reference, double delta) {
    if (fabs(computed - reference) > delta) {
        cout << "\tERROR:" << endl;
        cout << "\t\tcomputed   = " << computed << endl;
        cout << "\t\treference  = " << reference << endl;
        cout << "\t\tdifference = " << fabs(computed - reference) << endl;
        }
    }        

class Refs {
    public:
        Refs(const string &name, vPlanets planet, double jd, double l, double b, double r) :
            name(name),
            planet(planet),
            jd(jd),
            l(l),
            b(b),
            r(r) {};

        const string name;
        const vPlanets planet;
        const double jd;
        const double l;
        const double b;
        const double r;
    };

void usage() {
    cout << "Test the VSOP87d calculations against the check document." << endl;
    cout << endl;
    cout << "Usage:" << endl;
    cout << endl;
    cout << "    ./check_vsop87d vsop87.chk" << endl;
    cout << endl;
    cout << "where 'vsop87.chk' has been fetched from the ftp directory referenced" << endl;
    cout << "at:" << endl;
    cout << endl;
    cout << "    http://cdsweb.u-strasbg.fr/cgi-bin/Cat?VI/81" << endl;
    };
        
void _main(int argc, char *argv[]) {
    if (argc != 2) {
        usage();
        exit(EXIT_FAILURE);
        }
    //
    // a list of tuples of the form (planet_name, julian_day, longitude, latitude, radius)
    // 
    list<Refs> refs;
    
    load_params();
    
    ifstream infile(argv[1]);
    if (!infile)
        throw Error("_main: unable to open input file = " + string(argv[1]));

    string line;
    getline(infile, line);
    while (infile) {
        vector<string> fields = split(line);
        if (!fields.empty())
            if (fields[0] == "VSOP87D") {
                string planet = fields[1];
                planet = planet[0] + lower(planet.substr(1));
                string jdstr = fields[2];
                jdstr = jdstr.substr(2);
                const double jd = string_to_double(jdstr);
                getline(infile, line);
                fields = split(line);
                const double l = string_to_double(fields[1]);
                const double b = string_to_double(fields[4]);
                const double r = string_to_double(fields[7]);
                refs.push_back(Refs(planet, stringToPlanet[planet], jd, l, b, r));
                }
        getline(infile, line);
        }
    infile.close();

    cout << refs.size() << " tests" << endl;

    VSOP87d vsop;

    for (std::list<Refs>::const_iterator p = refs.begin(); p != refs.end(); p++) {
        double L, B, R;
        vsop.dimension3(p->jd, p->planet, L, B, R);
        cout << p->name << " " << (long)p->jd << " L" << endl;
        report(L, p->l, 1e-10);
        cout << p->name << " " << (long)p->jd << " B" << endl;
        report(B, p->b, 1e-10);
        cout << p->name << " " << (long)p->jd << " R" << endl;
        report(R, p->r, 1e-10);
        cout << endl;
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




