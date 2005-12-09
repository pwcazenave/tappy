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

/*Create a text version of the VSOP87d database.

Usage:
    
    ./create_text_vsop_db > vsop87d.txt   # or whatever path/file.
    
IMPORTANT: A text version of the database is provided with the Astrolabe
package. You need to run this program ONLY if for some reason you want
to recreate that file.

Run the program from a directory containing these files:

    VSOP87D.ear
    VSOP87D.jup
    VSOP87D.mar
    VSOP87D.mer
    VSOP87D.nep
    VSOP87D.sat
    VSOP87D.ura
    VSOP87D.ven

...which have been fetched from the ftp directory referenced at:

    http://cdsweb.u-strasbg.fr/cgi-bin/Cat?VI/81

The program will read each file, select the data required and combine all
of them into a format expected by the Astrolabe vsop87d module. 

Results are written to standard output; redirect them into a file in your
data directory and enter that path/file name into the astrolabe_params.txt
file as the value of "vsop87d_text_path".

*/
/*
#
# Here are file format notes from the original VSOP distribution.
#

#HEADER RECORD
#=============
#Specifications :
#- iv : code of VSOP87 version               integer     i1  col.18
#- bo : name of body                         character   a7  col.23-29
#- ic : index of coordinate                  integer     i1  col.42
#- it : degree alpha of time variable T      integer     i1  col.60
#- in : number of terms of series            integer     i7  col.61-67
#
#The code iv of the version is :
#iv = 4 for the version VSOP87D
#
#The names bo of the bodies are :
#MERCURY, VENUS, EARTH, MARS, JUPITER, SATURN, URANUS, NEPTUNE, SUN,
#and EMB for the Earth-Moon Barycenter.
#
#The index ic of the coordinates are :
#- for the spherical coordinates (versions B,D) :
#  1 : Longitude
#  2 : Latitude
#  3 : Radius
#
#The degree alpha of the time variable is equal to :
#0 for periodic series, 1 to 5 for Poisson series.

#TERM RECORD
#===========
#Specifications :
#iv : code of VSOP87 version                 integer     i1  col.02
#ic : index of coordinate                    integer     i1  col.04
#it : degree alpha of time variable T        integer     i1  col.05
#n  : rank of the term in a serie            integer     i5  col.06-10
#A  : amplitude A                            real dp f18.11  col.80-97
#B  : phase     B                            real dp f14.11  col.98-111
#C  : frequency C                            read dp f20.11  col.112-131
*/

#include "astrolabe.hpp"
#include <cassert>
#include <fstream>
#include <iostream>

using std::string;
using std::vector;
using std::getline;
using std::ifstream;
using std::cout;
using std::endl;
using std::exception;

using astrolabe::util::string_to_int;
using astrolabe::util::strip;
using astrolabe::util::upper;
using astrolabe::util::lower;
using astrolabe::Error;

const string _planets[] = {"Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"};
const VECTOR(planets, string);

const string _coords[] = {"L","B","R"};
const VECTOR(coords, string);

void _main() {
    // each planet file...
    for (std::vector<string>::const_iterator p = planets.begin(); p != planets.end(); p++) {
        const string planet = *p;
        const string fname = "VSOP87D." + lower(planet.substr(0,3));
        ifstream infile(fname.c_str());
        if (!infile)
            throw Error("_main: cannot open file = " + fname);
        string line;
	getline(infile, line);
        // header records...
	while (infile) {
	    assert(line[17] == '4');                                // model "d"
	    assert(strip(line.substr(22 ,7)) == upper(planet));     // planet name
	    const int ic = string_to_int(line.substr(41, 1));       // coord type
            assert(ic >= 0 && ic <= 2);
	    const int it = string_to_int(line.substr(59, 1));       // time degree
	    const int nt = string_to_int(line.substr(60, 7));       // number of terms
	    cout << planet << " " << coords[ic - 1] << " " << it << " " << nt << endl;
            // term records
	    for (int i = 0; i < nt; i++) {
	        getline(infile, line);
		assert(line[1] == '4');                             // model "d"
		const int ict = string_to_int(line.substr(3, 1));   // coord type
		assert(ict == ic);
		const int itt = string_to_int(line.substr(4, 1));   // time degree
		assert(itt == it);
		const string A = strip(line.substr(79, 18));
		const string B = strip(line.substr(97, 14));
		const string C = strip(line.substr(111, 20));
		cout << A << " " << B << " " << C << endl;
                }
	    getline(infile, line);
            }
        infile.close();
        }
    //
    // that's all
    //
    }

int main(int argc, char *argv[]) {
    try {
	_main();
	}
    catch(const exception &e) {
	cout << e.what() << endl;
	}
    return 0;
    }




