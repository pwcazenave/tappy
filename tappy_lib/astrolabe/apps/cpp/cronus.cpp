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

/* A clock application that displays a variety of celestial events in the
order they occur.

Usage:

    ./cronus start_year [stop_year]
    
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

*/

#include "astrolabe.hpp"
#include <cstdio>
#include <cstdlib>
#include <queue>
#include <iostream>

using std::cout;
using std::endl;
using std::string;
using std::vector;
using std::map;
using std::priority_queue;
using std::exception;

using astrolabe::calendar::cal_to_jd;
using astrolabe::calendar::easter;
using astrolabe::calendar::lt_to_str;
using astrolabe::calendar::ut_to_lt;
using astrolabe::constants::days_per_minute;
using astrolabe::constants::days_per_second;
using astrolabe::constants::standard_rst_altitude;
using astrolabe::constants::sun_rst_altitude;
using astrolabe::dicts::planetToString;
using astrolabe::dynamical::dt_to_ut;
using astrolabe::elp2000::ELP2000;
using astrolabe::equinox::equinox_approx;
using astrolabe::equinox::equinox_exact;
using astrolabe::kSpring;
using astrolabe::kWinter;
using astrolabe::nutation::nut_in_lon;
using astrolabe::nutation::nut_in_obl;
using astrolabe::nutation::obliquity;
using astrolabe::riseset::moon_rst_altitude;
using astrolabe::riseset::rise;
using astrolabe::riseset::set;
using astrolabe::riseset::transit;
using astrolabe::Season;
using astrolabe::sun::aberration_low;
using astrolabe::sun::Sun;
using astrolabe::util::ecl_to_equ;
using astrolabe::util::load_params;
using astrolabe::vEarth;
using astrolabe::vMercury;
using astrolabe::vNeptune;
using astrolabe::vPlanets;
using astrolabe::vsop87d::geocentric_planet;
using astrolabe::vsop87d::vsop_to_fk5;

const double HIGH_PRIORITY = 0.0;

class Task {
    public:
        virtual ~Task() {};
        virtual void Run() = 0;
    };

class Display : public Task {
    public:
        Display(const string &str) : str(str) {};
        void Run();
    private:
        const string str;
    };
    
class Easter : public Task {
    public:
        Easter(int year) : year(year) {};
        void Run();
    private:
        const int year;
    };
    
class Equinox : public Task {
    public:
        Equinox(int year, Season season) : year(year), season(season) {};
        void Run();
    private:
        const int year;
        const Season season;
    };
    
class RiseSetTransitData {
    public:
        RiseSetTransitData() {}; // required by map<>?
        RiseSetTransitData(const string &name, const vector<double> &raList, const vector<double> &decList, const vector<double> &h0List) :
            name(name),
            raList(raList),
            decList(decList),
            h0List(h0List) {};
        
        string name;
        vector<double> raList;
        vector<double> decList;
        vector<double> h0List;
    };

class RiseSetTransit : public Task {
    public:
        RiseSetTransit(double jd_today, Sun &sun, ELP2000 &moon, const map<string, RiseSetTransitData> &rstDict) : 
            jd_today(jd_today), 
            sun(sun),
            moon(moon),
            rstDict(rstDict) {};
        void Run();
    private:
        double jd_today;
        Sun &sun;
        ELP2000 &moon;
        map<string, RiseSetTransitData> rstDict;
    };
    
class Wrapper {
    public:
        Wrapper(double jd, Task *task) : jd(jd), task(task) {};
        bool operator<(const Wrapper &rhs) const {
            return jd >= rhs.jd; // reverse order
            };
        double jd; // should be const
        Task *task; // "        "
    };
    
priority_queue<Wrapper> taskQueue;

void Display::Run() {
    cout << str << endl;
    }
    
void Easter::Run() {
    int month, day;
    easter(year, true, month, day);
    const double jd = cal_to_jd(year, month, day);
    char cstr[200];
    sprintf(cstr, "%-24s %s", lt_to_str(jd, "", "day").c_str(), "Easter");
    taskQueue.push(Wrapper(jd, new Display(cstr)));
    // recalculate on March 1, next year
    taskQueue.push(Wrapper(cal_to_jd(year + 1, 3, 1), new Easter(year + 1)));
    }

void Equinox::Run() {    
    static const string seasons[] = {"Vernal Equinox", "Summer Solstice", "Autumnal Equinox", "Winter Solstice"};
    const double approx_jd = equinox_approx(year, season);
    const double jd = equinox_exact(approx_jd, season, days_per_second);
    const double ut = dt_to_ut(jd);
    double lt;
    string zone;
    ut_to_lt(ut, lt, zone);
    const string str = lt_to_str(lt, zone) + " " + seasons[season];
    taskQueue.push(Wrapper(jd, new Display(str)));
    // recalculate on March 15, next year
    taskQueue.push(Wrapper(cal_to_jd(year + 1, 3, 15), new Equinox(year + 1, season)));
    }
    
void RiseSetTransit::Run() {
    std::map<string, RiseSetTransitData>::iterator p;
    //
    // Find and queue rise-set-transit times for all objects
    //
    double jd = jd_today;
    for (p = rstDict.begin(); p != rstDict.end(); p++) {
        double td = rise(jd, p->second.raList, p->second.decList, p->second.h0List[1], days_per_minute);
        if (td >= 0.0) {
            const double ut = dt_to_ut(td);
            double lt;
            string zone;
            ut_to_lt(ut, lt, zone);
            char cstr[200];
            sprintf(cstr, "%-20s %s %s rises", lt_to_str(lt, "", "minute").c_str(), zone.c_str(), p->second.name.c_str());
            taskQueue.push(Wrapper(td, new Display(cstr)));
            }
        else
            cout << "****** RiseSetTransit failure: " << p->second.name << " rise" << endl;
            
        td = set(jd, p->second.raList, p->second.decList, p->second.h0List[1], days_per_minute);
        if (td >= 0.0) {
            const double ut = dt_to_ut(td);
            double lt;
            string zone;
            ut_to_lt(ut, lt, zone);
            char cstr[200];
            sprintf(cstr, "%-20s %s %s sets", lt_to_str(lt, "", "minute").c_str(), zone.c_str(), p->second.name.c_str());
            taskQueue.push(Wrapper(td, new Display(cstr)));
            }
        else
            cout << "****** RiseSetTransit failure: " << p->second.name << " set" << endl;

        td = transit(jd, p->second.raList, days_per_second);
        if (td >= 0.0) {
            const double ut = dt_to_ut(td);
            double lt;
            string zone;
            ut_to_lt(ut, lt, zone);
            char cstr[200];
            sprintf(cstr, "%-24s %s transits", lt_to_str(lt, zone).c_str(), p->second.name.c_str());
            taskQueue.push(Wrapper(td, new Display(cstr)));
            }
        else
            cout << "****** RiseSetTransit failure: " << p->second.name << " transit" << endl;
        }
    //
    // setup the day after tomorrow
    //
    jd += 2;
    
    // nutation in longitude
    const double deltaPsi = nut_in_lon(jd);
    
    // apparent obliquity
    const double eps = obliquity(jd) + nut_in_obl(jd);
    
    //
    // Planets
    //
    for (int planet = vMercury; planet <= vNeptune; planet++) {
        if (planet == vEarth)
            continue;
        double ra, dec;
        geocentric_planet(jd, static_cast<vPlanets>(planet), deltaPsi, eps, days_per_second, ra, dec);
        p = rstDict.find(planetToString[static_cast<vPlanets>(planet)]);
        p->second.raList.erase(p->second.raList.begin());
        p->second.decList.erase(p->second.decList.begin());
        p->second.h0List.erase(p->second.h0List.begin());
        p->second.raList.push_back(ra);
        p->second.decList.push_back(dec);
        p->second.h0List.push_back(standard_rst_altitude);
        }
    //
    // Moon
    //
    double l, b, r;
    moon.dimension3(jd, l, b, r);
    
    // nutation in longitude
    l += deltaPsi;

    // equatorial coordinates
    double ra, dec;
    ecl_to_equ(l, b, eps, ra, dec);

    p = rstDict.find("Moon");
    p->second.raList.erase(p->second.raList.begin());
    p->second.decList.erase(p->second.decList.begin());
    p->second.h0List.erase(p->second.h0List.begin());
    p->second.raList.push_back(ra);
    p->second.decList.push_back(dec);
    p->second.h0List.push_back(moon_rst_altitude(r));
    //
    // Sun
    //
    sun.dimension3(jd, l, b, r);

    // correct vsop coordinates    
    vsop_to_fk5(jd, l, b);

    // nutation in longitude
    l += deltaPsi;
    
    // aberration
    l += aberration_low(r);

    // equatorial coordinates
    ecl_to_equ(l, b, eps, ra, dec);
    
    p = rstDict.find("Sun");
    p->second.raList.erase(p->second.raList.begin());
    p->second.decList.erase(p->second.decList.begin());
    p->second.h0List.erase(p->second.h0List.begin());
    p->second.raList.push_back(ra);
    p->second.decList.push_back(dec);
    p->second.h0List.push_back(sun_rst_altitude);
    
    // all Rise-Set-Transit events
    taskQueue.push(Wrapper(jd_today + 1, new RiseSetTransit(jd_today + 1, sun, moon, rstDict)));
    }
    
void usage() {
    cout << "A clock application that displays a variety of celestial events in the" << endl;
    cout << "order they occur." << endl;
    cout << endl;
    cout << "Usage:" << endl;
    cout << endl;
    cout << "    ./cronus start_year [stop_year]" << endl;
    }

// C++: must be at outer level
class RSTValue {
    public:
        RSTValue() {}; // required by map<>?
        RSTValue(double delta_psi, double epsilon) : delta_psi(delta_psi), epsilon(epsilon) {};

        double delta_psi;
        double epsilon;
    };
        
void initRST(int start_year, Sun &sun, ELP2000 &moon) {    
    const double start_jd = cal_to_jd(start_year);

    int day;
    //
    // We need nutation values for each of three days
    // 
    map<int, RSTValue> nutation;
    for (day = -1; day <= 1; day++) {
        const double jd = start_jd + day;
        // nutation in longitude
        const double delta_psi = nut_in_lon(jd);
        // apparent obliquity
        double epsilon = obliquity(jd) + nut_in_obl(jd);
        nutation[day] = RSTValue(delta_psi, epsilon);
        }

    map<string, RiseSetTransitData> rstDict;

    //
    // Planets
    //
    for (int planet = vMercury; planet <= vNeptune; planet++) {
        if (planet == vEarth)
            continue;
        vector<double> raList;
        vector<double> decList;
        vector<double> h0List;
        for (int day = -1; day <= 1; day++) {
            const double jd = start_jd + day;
            RSTValue &nut = nutation[day];
            double ra, dec;
            geocentric_planet(jd, static_cast<vPlanets>(planet), nut.delta_psi, nut.epsilon, days_per_second, ra, dec);
            raList.push_back(ra);
            decList.push_back(dec);
            h0List.push_back(standard_rst_altitude);
            }
        rstDict[planetToString[static_cast<vPlanets>(planet)]] = RiseSetTransitData(planetToString[static_cast<vPlanets>(planet)], raList, decList, h0List);
        }

    //
    // Moon
    //
    vector<double> raList;
    vector<double> decList;
    vector<double> h0List;
    for (day = -1; day <= 1; day++) {
        const double jd = start_jd + day;
        RSTValue &nut = nutation[day];
        double l, b, r;
        moon.dimension3(jd, l, b, r);
        // nutation in longitude
        l += nut.delta_psi;
        // equatorial coordinates
        double ra, dec;
        ecl_to_equ(l, b, nut.epsilon, ra, dec);
        raList.push_back(ra);
        decList.push_back(dec);
        h0List.push_back(moon_rst_altitude(r));
        }
    rstDict["Moon"] = RiseSetTransitData("Moon", raList, decList, h0List);

    //
    // Sun
    //
    raList.erase(raList.begin(), raList.end());
    decList.erase(decList.begin(), decList.end());
    h0List.erase(h0List.begin(), h0List.end());
    for (day = -1; day <= 1; day++) {
        const double jd = start_jd + day;
        double l, b, r;
        sun.dimension3(jd, l, b, r);
        // correct vsop coordinates    
        vsop_to_fk5(jd, l, b);
        RSTValue &nut = nutation[day];
        // nutation in longitude
        l += nut.delta_psi;
        // aberration
        l += aberration_low(r);
        // equatorial coordinates
        double ra, dec;
        ecl_to_equ(l, b, nut.epsilon, ra, dec);
        raList.push_back(ra);
        decList.push_back(dec);
        h0List.push_back(sun_rst_altitude);
        }
    rstDict["Sun"] = RiseSetTransitData("Sun", raList, decList, h0List);
    
    // all Rise-Set-Transit events
    taskQueue.push(Wrapper(start_jd, new RiseSetTransit(start_jd, sun, moon, rstDict)));
    }
    
void _main(int argc, char *argv[]) {
    int start_year;
    double stop_jd;
    if (argc < 2) {
        usage();
        exit(EXIT_FAILURE);
        }
    if (argc < 3) {
        start_year = atoi(argv[1]);
        stop_jd = cal_to_jd(10000); // default stopping date: 10,000AD
        }
    else if (argc < 4) {
        start_year = atoi(argv[1]);
        stop_jd = cal_to_jd(atoi(argv[2]));
        }
    else {
        usage();
        exit(EXIT_FAILURE);
        }

    load_params();
//    VSOP87d vsop;
    Sun sun;
    ELP2000 moon;

    // Easter
    taskQueue.push(Wrapper(HIGH_PRIORITY, new Easter(start_year)));

    // four equinox/solstice events
    for (int season = kSpring; season <= kWinter; season++)
        taskQueue.push(Wrapper(HIGH_PRIORITY, new Equinox(start_year, static_cast<Season>(season))));

    // initialize rise-set-transit objects  
    initRST(start_year, sun, moon);

    // start the task loop
    Wrapper w = taskQueue.top();
    taskQueue.pop();
    while (w.jd < stop_jd) {
        w.task->Run();
        delete w.task; //should be auto_ptr
        w = taskQueue.top();
        taskQueue.pop();
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
