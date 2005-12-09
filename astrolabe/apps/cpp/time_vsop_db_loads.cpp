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

/* Compare the loading time of text and binary VSOp87d databases.

Usage:

    ./time_vsop_db_loads
    
Result: the binary version is only slightly faster than the text
version.

NOTE: No binary database for C++ yet.
        
*/

#include "astrolabe.hpp"
#include <iostream>
#include <ctime>

using std::cout;
using std::endl;
using std::exception;

using astrolabe::util::load_params;
using astrolabe::vsop87d::load_vsop87d_text_db;

void _main() {
    load_params();
    cout << "reading text database..." << endl;
    const time_t t0 = time(NULL);
    const clock_t c0 = clock();
    load_vsop87d_text_db();
    const clock_t c1 = clock();
    cout << difftime(time(NULL), t0) << " seconds" << endl;
    cout << ((float)(c1 - c0)) / CLOCKS_PER_SEC << " cpu seconds" << endl;

    /*
    print "reading binary database..."
    t0 = time.time()
    load_vsop87d_binary_db()
    print time.time() - t0, "seconds"
    */    
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
