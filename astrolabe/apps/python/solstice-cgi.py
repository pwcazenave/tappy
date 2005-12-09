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

CGI interface to the Equinox/Solstice routines.

Will display a table of times of equinoxes and solstices for a
range of years.

One application handles both the input form and the displayed
results.

"""

import cgi
import sys
import time

#
# Rather than setup PYTHONPATH in a shell script, we add it
# through sys. That way we need only one file for the application.
#
#
# This path is specific to SourceForge.
#
sys.path.append('/home/groups/a/as/astrolabe/lib/python')

from astrolabe.constants import days_per_second
from astrolabe.calendar import ut_to_lt, lt_to_str
from astrolabe.dynamical import dt_to_ut
from astrolabe.equinox import equinox_approx, equinox
from astrolabe.sun import Sun
from astrolabe.util import load_params
import astrolabe.globals

standard_zones = (
    'GMT-12',
    'GMT-11',
    'GMT-10',
    'GMT-9',
    'PST',
    'MST',
    'CST',
    'EST',
    'GMT-4',
    'GMT-3',
    'GMT-2',
    'GMT-1',
    'GMT',
    'GMT+1',
    'GMT+2',
    'GMT+3',
    'GMT+4',
    'GMT+5',
    'GMT+6',
    'GMT+7',
    'GMT+8',
    'GMT+9',
    'GMT+10',
    'GMT+11',
    'GMT+12')

standard_zone_hours = {
    'GMT-12': -12,
    'GMT-11': -11,
    'GMT-10': -10,
    'GMT-9': -9,
    'PST': -8,
    'MST': -7,
    'CST': -6,
    'EST': -5,
    'GMT-4': -4,
    'GMT-3': -3,
    'GMT-2': -2,
    'GMT-1': -1,
    'GMT': 0,
    'GMT+1': 1,
    'GMT+2': 2,
    'GMT+3': 3,
    'GMT+4': 4,
    'GMT+5': 5,
    'GMT+6': 6,
    'GMT+7': 7,
    'GMT+8': 8,
    'GMT+9': 9,
    'GMT+10': 10,
    'GMT+11': 11,
    'GMT+12': 12}

daylight_zones = (
    'GMT-12',
    'GMT-11',
    'GMT-10',
    'GMT-9',
    'GMT-8',
    'PDT',
    'MDT',
    'CDT',
    'EDT',
    'GMT-3',
    'GMT-2',
    'GMT-1',
    'GMT',
    'GMT+1',
    'GMT+2',
    'GMT+3',
    'GMT+4',
    'GMT+5',
    'GMT+6',
    'GMT+7',
    'GMT+8',
    'GMT+9',
    'GMT+10',
    'GMT+11',
    'GMT+12')

daylight_zone_hours = {
    'GMT-12': -12,
    'GMT-11': -11,
    'GMT-10': -10,
    'GMT-9': -9,
    'GMT-8': -8,
    'PDT': -7,
    'MDT': -6,
    'CDT': -5,
    'EDT': -4,
    'GMT-3': -3,
    'GMT-2': -2,
    'GMT-1': -1,
    'GMT': 0,
    'GMT+1': 1,
    'GMT+2': 2,
    'GMT+3': 3,
    'GMT+4': 4,
    'GMT+5': 5,
    'GMT+6': 6,
    'GMT+7': 7,
    'GMT+8': 8,
    'GMT+9': 9,
    'GMT+10': 10,
    'GMT+11': 11,
    'GMT+12': 12}

default_standard_zone = 'CST'
default_daylight_zone = 'CDT'

form = cgi.FieldStorage()

#
# Collect the input parameters
#
def display_form():
    fields = time.localtime(time.time())
    year = fields[0]
    
    print 'Content-type: text/html' 
    print                               
    print '<HEAD>'
    print '<TITLE>Astrolabe Solstice Parameters</TITLE>'
    print '</HEAD>'
    
    print '<BODY>'
    print '<H1>Astrolabe Solstice Parameters</H1>'
    
    print '<FORM action="http://astrolabe.sourceforge.net/cgi-bin/solstice-cgi.py" method="post">'
    
    print '<TABLE>'
    print '<TR>'
    print '<TD><LABEL for="starting_year">Starting year</LABEL></TD>'
    print '<TD><INPUT type="text" size=4 name="starting_year" id="starting_year" value="%d"></TD>' % (year - 5)
    print '</TR>'
    print '<TR>'
    print '<TD><LABEL for="ending_year">Ending year</LABEL></TD>'
    print '<TD><INPUT type="text" size=4 name="ending_year" id="ending_year" value="%d"></TD>' % (year + 5)
    print '</TR>'
    print '<TR>'
    print '<TD><LABEL for="standard_zone">Standard Time Zone</LABEL></TD>'
    print '<TD><SELECT name = "standard_zone">'
    for zone in standard_zones:
        if zone == default_standard_zone:
            print '<OPTION SELECTED>' + zone + '</OPTION>'
        else:
            print '<OPTION>' + zone + '</OPTION>'
    print '</SELECT></TD>'
    print '</TR>'
    print '<TR>'
    print '<TD><LABEL for="daylight_zone">Daylight Time Zone</LABEL></TD>'
    print '<TD><SELECT name = "daylight_zone">'
    for zone in daylight_zones:
        if zone == default_daylight_zone:
            print '<OPTION SELECTED>' + zone + '</OPTION>'
        else:
            print '<OPTION>' + zone + '</OPTION>'
    print '</SELECT></TD>'
    print '</TR>'
    print '</TABLE>'

    print '<INPUT type="submit" value="Run"> <INPUT type="reset">'
 
    print '<INPUT type="hidden" name="results" value="1">'
 
    print '</FORM>'
    print '</BODY>'

#
# Display an error message
#
def display_error(msg):
    print '<HEAD>'
    print '<TITLE>Astrolabe Solstice Error</TITLE>'
    print '</HEAD>'
    print '<BODY>'
    print '<H1>', msg, '</H1>'
    print '</BODY>'

#
# Display the results
#
def display_results():
    #
    # Assign the global parameters directly so we don't have to read a param file.
    #
    astrolabe.globals.standard_timezone_name = form['standard_zone'].value
    astrolabe.globals.standard_timezone_offset = -standard_zone_hours[astrolabe.globals.standard_timezone_name] / 24.0
    astrolabe.globals.daylight_timezone_name = form['daylight_zone'].value
    astrolabe.globals.daylight_timezone_offset = -daylight_zone_hours[astrolabe.globals.daylight_timezone_name] / 24.0
    astrolabe.globals.vsop87d_text_path = '/home/groups/a/as/astrolabe/data/vsop87d.txt'
    astrolabe.globals.vsop87d_binary_path = '/home/groups/a/as/astrolabe/data/vsop87d.dat'

    print 'Content-type: text/html' 
    print                               
    print '<HEAD>'
    print '<TITLE>Astrolabe Solstice Results</TITLE>'
    print '</HEAD>'

    #
    # To do: We should validate the integer values
    #
    # If no starting_year, start with 5 years ago.
    #
    if form.has_key('starting_year'):
        starting_year = int(form['starting_year'].value)
    else:
        fields = time.localtime(time.time())
        year = fields[0]
        starting_year = year - 5

    #
    # If no ending_year, end 10 years after the starting_year.
    #
    if form.has_key('ending_year'):
        ending_year = int(form['ending_year'].value)
    else:
        ending_year = starting_year + 10

    #
    # Make sure end_year >= starting_year.
    #
    if (ending_year < starting_year):
        display_error('Ending year %d is earlier than starting year %d' % (ending_year, starting_year))
        return

    #
    # We can't go farther back than the first Julian Day number.
    #
    if (starting_year < -4712):
        display_error('Starting year %d is earlier than 4713BC' % starting_year)
        return

    #
    # Finally, we display the results.
    #
    print '<BODY>'
    print '<H1>Astrolabe Solstice Results</H1>'

    print '<TABLE BORDER>'

    print '<TR>'
    print '<TH>Vernal Equinox</TH>'
    print '<TH>Summer Solstice</TH>'
    print '<TH>Autumnal Equinox</TH>'
    print '<TH>Winter Solstice</TH>'
    print '</TR>'

    for year in range(starting_year, ending_year + 1):
        print '<TR>'
        for season in astrolabe.globals.season_names:
            approx_jd = equinox_approx(year, season)
            jd = equinox(approx_jd, season, days_per_second)
            ut = dt_to_ut(jd)
            lt, zone = ut_to_lt(ut)
            print '<TD>' + lt_to_str(lt, zone) + '</TD>'
        print '</TR>'
    print '</TABLE>'

    # handy diagnostic routines
    """
    print "<H1>print_environ</H1>"
    cgi.print_environ() 
    print "<H1>print_directory</H1>"
    cgi.print_directory() 
    print "<H1>print_environ_usage</H1>"
    cgi.print_environ_usage()
    print "<H1>FieldStorage</H1>"
    #form = cgi.FieldStorage()
    cgi.print_form(form)
    """
    
    print '</BODY>'

#
# Main routine. There is a hidden field "results" on the parameter form. If it
# is not present, we display the form. If it is, we display the results.
#
if form.has_key('results'):
    display_results()
else:
    display_form()



