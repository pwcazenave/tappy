#!/usr/bin/env python

"""
NAME:
    tappy.py  

SYNOPSIS:
    tappy.py [options] filename

DESCRIPTION:
    Tidal Analysis Program in PYthon.

    Uses least squares fit to estimate tidal amplitude and phase.
    Specific to tides generated on Earth by the Moon and Sun.

OPTIONS:
    -h,--help        this message
    -v,--version     version
    -d,--debug       turn on debug messages
    --bb=xyz         set option bb to xyz

EXAMPLES:
    1. As standalone
        tappy.py -d myfile
    2. As library
        import tappy
        ...

#Copyright (C) 2005  Tim Cera timcera@earthlink.net
#http://tappy.sourceforge.net
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.


"""
#===imports======================
import sys
import os
import os.path
import scipy as N
from scipy.optimize import leastsq
import datetime

import tappy_lib
import sparser
import astrolabe.calendar as cal
import astrolabe.util as uti
import pad.pad as pad

#===globals======================
modname = "tappy"
__version__ = "0.6.0"

#--option args--
debug_p = 0
#opt_b=None  #string arg, default is undefined

#---other---
deg2rad = N.pi/180.0
rad2deg = 180.0/N.pi


#===utilities====================
def msg(txt):
    sys.stdout.write(txt)
    sys.stdout.flush()

def debug(ftn, txt):
    if debug_p:
        sys.stdout.write("%s.%s:%s\n" % (modname, ftn,txt))
        sys.stdout.flush()

def fatal(ftn, txt):
    msg = "%s.%s:FATAL:%s\n" % (modname, ftn,txt)
    raise SystemExit, msg
 
def usage():
    print __doc__

def interpolate(data, start, stop, iavg):
    if start < 1 or stop > len(data) - 1:
        print 'can not interpolate without at least 1 valid point on each side'
    if start < iavg:
        ssl = slice(0, start)
    else:
        ssl = slice(start - iavg, start)

    deltay = N.average(data[stop + 1:stop + iavg]) - N.average(data[ssl])
    numx = stop - start + 2.0
    m = deltay/numx
    b = N.average(data[ssl]) - m*(start - 1)
    for i in range(start, stop + 1):
        data[i] = m*i + b

def zone_calculations(ftn, data, mask):
    start = None
    stop = None
    for index, val in enumerate(mask):
        if val and not start:
            start = index
        if not val and start:
            stop = index - 1
        if start and stop:
            ftn(data, start, stop, 25)
            start = None
            stop = None


#====================================
class tappy:
    #---class variables---
    #--------------------------
    def __init__(self, filename, def_filename = None):
        ftn = "tappy.__init__"
        #---instance variables---
        self.speed_dict = {}

        # Read in data file
        # Data file format is what can be downloaded from COOPS web site.
        fp = sparser.ParseFileLineByLine(filename, 
                                         def_filename = def_filename, 
                                         mode='r')
        self.elevation = []
        self.dates = []
        for line in fp:
            if not isinstance(line, dict):
                continue
            self.elevation.append(line['water_level'])
            self.dates.append(datetime.datetime(line['year'],
                                                line['month'],
                                                line['day'],
                                                line['hour'],
                                                line['minute']))
        self.elevation = N.array(self.elevation)
        self.dates = N.array(self.dates)


    def which_constituents(self, length, package, rayleigh_comp = 1.0):
        (zeta, nu, nupp, two_nupp, kap_p, ii, R, Q, T, jd, s, h, Nv, p, p1) = package
        speed_dict = {}

        # Set data into speed_dict depending on length of time series
        # Required length of time series depends on Raleigh criteria to 
        # differentiate beteen constituents of simmilar speed.
        #  Key is tidal constituent name from Schureman
        #    speed is how fast the constiuent moves in radians/hour
        #    VAU is V+u taken from Schureman
        #    FF is the node factor from Schureman

        # TASK has the following constituents
        #  MSN6       87.4238337

        self.tidal_dict = {}

        self.tidal_dict["M2"] = {'speed': 28.984104252*deg2rad,
                                 'VAU': 2*(T - s + h + zeta - nu),
                                 'FF': N.cos(0.5*ii)**4 /0.9154  # eq 78
                                 }
        self.tidal_dict["K1"] = {'speed': 15.041068632*deg2rad,
                                 'VAU': T + h - 90 - nupp,
                                 'FF': (0.8965*(N.sin(2.*ii)**2) + 0.6001*N.sin(2.*ii)*N.cos(nu*deg2rad) + 0.1006)**0.5  # eq 227
                                 }
        self.tidal_dict["M3"] = {'speed': 43.476156360*deg2rad,
                                 'VAU': 3*(T - s + h + zeta - nu),
                                 'FF': N.cos(0.5*ii)**6 /0.8758  # eq 149
                                 }
        self.tidal_dict["M4"] = {'speed': 57.968208468*deg2rad,
                                 'VAU': 2.*self.tidal_dict['M2']['VAU'],
                                 'FF': self.tidal_dict['M2']['FF']**2
                                 }
        self.tidal_dict["M6"] = {'speed': 86.952312720*deg2rad,
                                 'VAU': 3.*self.tidal_dict['M2']['VAU'],
                                 'FF': self.tidal_dict['M2']['FF']**2
                                 }
        self.tidal_dict["M8"] = {'speed': 115.936416972*deg2rad,
                                 'VAU': 4.*self.tidal_dict['M2']['VAU'],
                                 'FF': self.tidal_dict['M2']['FF']**4
                                 }
        self.tidal_dict["S6"] = {'speed': 90.0*deg2rad,
                                 'VAU': 6*T,
                                 'FF': N.ones(length)
                                 }
        self.tidal_dict["O1"] = {'speed': 13.943035584*deg2rad,
                                 'VAU': T - 2*s + h + 90 + 2*zeta - nu,
                                 'FF': N.sin(ii)*N.cos(0.5*ii)**2 /0.3800
                                 }
        self.tidal_dict["S2"] = {'speed': 30.0000000 * deg2rad,
                                 'VAU': 2*T,
                                 'FF': N.ones(length)
                                 }
        self.tidal_dict["2MS6"] = {'speed': 87.968208492*deg2rad, #?
                                  'VAU': 2.0*self.tidal_dict['M2']['VAU'] + self.tidal_dict['S2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']**2
                                  }
        self.tidal_dict["2SM6"] = {'speed': 88.984104228*deg2rad, #?
                                  'VAU': 2.0*self.tidal_dict['S2']['VAU'] + self.tidal_dict['M2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']
                                  }
        self.tidal_dict["MSf"] = {'speed': 1.0158957720*deg2rad,
                                  'VAU': 2.0*(s - h),
                                  'FF': ((2./3.) - N.sin(ii)**2)/0.5021
                                  }
        self.tidal_dict["SK3"] = {'speed': 45.041068656 * deg2rad,
                                  'VAU': self.tidal_dict['S2']['VAU'] + self.tidal_dict['K1']['VAU'],
                                  'FF': self.tidal_dict['K1']['FF']
                                  }
        # Might need to move this to another time span - couldn't find this
        # in Foreman for Rayleigh comparison pair.
        self.tidal_dict["2SM2"] = {
                              'speed': 31.01589576*deg2rad,   
                                  'VAU': 2.0*self.tidal_dict['S2']['VAU'] - self.tidal_dict['M2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']
                                  }
        self.tidal_dict["MS4"] = {'speed': 58.984104240*deg2rad,
                                  'VAU': self.tidal_dict['M2']['VAU'] + self.tidal_dict['S2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']
                                  }
        self.tidal_dict["S4"] = {'speed': 60.0*deg2rad,
                                  'VAU': 4*T,
                                  'FF': N.ones(length)
                                  }
        self.tidal_dict["OO1"] = {'speed': 16.139101680*deg2rad,
                                  'VAU': T + 2*s + h - 90 - 2*zeta - nu,
                                  'FF': (N.sin(ii)*N.sin(0.5*ii)**2)/0.0164
                                  }
        self.tidal_dict["MK3"] = {'speed': 44.025172884*deg2rad,
                                  'VAU': self.tidal_dict['M2']['VAU'] + self.tidal_dict['K1']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']*self.tidal_dict['K1']['FF']
                                  }
        # Seems like 2MK3 in Schureman is equivalent to MO3 in Foreman
        self.tidal_dict["MO3"] = {'speed': 42.927139836*deg2rad,
                                  'VAU': 2*self.tidal_dict['M2']['VAU'] - self.tidal_dict['K1']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']**2*self.tidal_dict['K1']['FF']
                                  }
        self.tidal_dict["N2"] =  {'speed': 28.439729568*deg2rad,
                                  'VAU': 2*T - 3*s + 2*h + p + 2*zeta - 2*nu,
                                  'FF': self.tidal_dict['M2']['FF']
                                  }
        self.tidal_dict["2MN6"] = {'speed': 86.407938036*deg2rad,
                                  'VAU': 2*self.tidal_dict['M2']['VAU'] + self.tidal_dict['N2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']**2
                                  }
        self.tidal_dict["2Q1"] = {'speed': 12.854286252*deg2rad,
                                  'VAU': T - 4*s + h + 2*p + 90 + 2*zeta - nu,
                                  'FF': self.tidal_dict['O1']['FF']
                                  }
        self.tidal_dict["Q1"] =  {'speed': 13.3986609*deg2rad,
                                  'VAU': T - 3*s + h + p + 90 + 2*zeta - nu,
                                  'FF': self.tidal_dict['O1']['FF']
                                  }
        self.tidal_dict["J1"] =  {'speed': 15.5854433*deg2rad,
                                  'VAU': T + s + h - p - 90 - nu,
                                  'FF': N.sin(2.0*ii)/0.7214
                                  }
        # Seems like KJ2 in Schureman is equivalent to ETA2 in Foreman
        self.tidal_dict["ETA2"] = {'speed': 30.626511948*deg2rad,
                                  'VAU': 2*T + s + 2*h - p - 2*nu,
                                  'FF': N.sin(ii)**2/0.1565
                                  }
        # Seems like KQ1 in Schureman is equivalent to UPS1 in Foreman
        self.tidal_dict["UPS1"] = {'speed': 16.683476328*deg2rad,
                                  'VAU': T + 3*s + h - p - 90 - 2*zeta - nu,
                                  'FF': N.sin(ii)**2/0.1565
                                  }
        #
        #        Foreman         Schureman           TASK
        #        =======         =========           ====
        # NO1   14.496693984        NA            UNKNOWN
        # M1        NA           14.4966939      14.4920521
        # (M1)      NA           14.4920521         NA
        # 
        # Foreman mentions that M1 is a satellite of NO1 but does not have a
        # speed for M1.

        # By comparing the speeds from the different sources, I now think that
        # the component of M1 in Schureman is actually NO1 (speed=14.496693984)
        # and M1 in TASK is equal to (M1) in Schureman.

        # Flater writes:

            # In summary, M1 is a minor constituent that doesn't deserve to be
            # such an inconvenience.  Until someone complains, I am just going
            # to use the NOS M1 for all data containing a constituent named M1
            # and hope for the best.  Future producers of harmonic constants
            # are advised to abolish M1 and just use NO1.

        # If M1 is 1/2 the speed of M2 that would mean TASK's M1 speed is
        # correct.  How do I get V, u, and f?

        # TAPPY
        # Constituent     Speed        V, u, and f
        # M1            14.492052126  From Schureman A71
        # NO1           14.496693984  From Schureman M1

        self.tidal_dict["M1"] =  {'speed': 14.4920521*deg2rad,
                                  'VAU': T - s + h + zeta + nu, # term A71 in Schureman
                                  'FF': (1.0 - 10.0*N.sin(0.5*ii)**2 + 15.0*N.sin(0.5*ii)**4)*N.cos(0.5*ii)**2/0.5873
                                  }
        self.tidal_dict["NO1"] = {'speed': 14.496693984*deg2rad,
                                  'VAU': T - s + h - 90 + zeta - nu + Q,
                                  # 2.307**0.5 factor was missed in Darwin's analysis
                                  'FF': 2.307**0.5*self.tidal_dict['O1']['FF']*(2.31+1.435*N.cos(2.0*kap_p))**0.5
                                  }
        self.tidal_dict["MN4"] = {'speed': 57.423833820*deg2rad,   # From TASK
                                  'VAU': self.tidal_dict['M2']['VAU'] + self.tidal_dict['N2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF']**2
                                  }
        self.tidal_dict["Mm"] =  {'speed': 0.5443747*deg2rad,
                                  'VAU': s - p,
                                  'FF': ((2./3.) - N.sin(ii)**2)/0.5021
                                  }
        self.tidal_dict["L2"] =  {'speed': 29.5284789*deg2rad,
                                  'VAU': 2*T - s + 2*h - p + 180 + 2*zeta - 2*nu - R,
                                  'FF': self.tidal_dict['M2']['FF'] * (1.0 - 12.0*N.tan(0.5*ii)**2 * N.cos(2.0*kap_p) + 36.0*N.tan(0.5*ii)**4)**0.5
                                  }
        self.tidal_dict["MU2"] = {'speed': 27.9682084*deg2rad,
                                  'VAU': 2*T - 4*s + 4*h + 2*zeta - 2*nu,
                                  'FF': self.tidal_dict['M2']['FF']
                                  }
#        self.tidal_dict["ALPHA1"] = 
        self.tidal_dict["EPS2"] = {'speed': 27.423833796*deg2rad,
                                  'VAU': 2*T - 5*s + 4*h + p + 4*zeta - 4*nu, # verify
                                  'FF': self.tidal_dict['M2']['FF']**2
                                  }
        self.tidal_dict["SN4"] = {'speed': 58.4397295560*deg2rad,
                                  'VAU': 2*T - 5*s + 4*h + p + 4*zeta - 4*nu,
                                  'FF': self.tidal_dict['M2']['FF']**2
                                  }
        self.tidal_dict["Ssa"] = {'speed': 0.0821373*deg2rad,
                                  'VAU': 2.0*h,
                                  'FF': N.ones(length)
                                  }
        self.tidal_dict["Mf"] =  {'speed': 1.0980331*deg2rad,
                                  'VAU': 2.0*(s - zeta),
                                  'FF': N.sin(ii)**2 /0.1578
                                  }
        self.tidal_dict["P1"] = {'speed': 14.9589314*deg2rad,
                                 'VAU': T - h + 90,
                                 'FF': N.ones(length)
                                 }
        self.tidal_dict["K2"] = {'speed': 30.0821373*deg2rad,
                                 'VAU': 2*(T + h - two_nupp),
                                 'FF': (19.0444*(N.sin(ii)**4) + 2.7702*(N.sin(ii)**2) * N.cos(2.*nu*deg2rad) + 0.0981)**0.5
                                 }
        self.tidal_dict["SO3"] = {'speed': 43.9430356*deg2rad,
                                  'VAU': 3*T - 2*s + h + 90 + 2*zeta - nu,
                                  'FF': self.tidal_dict["O1"]["FF"]
                                  }
        self.tidal_dict["PHI1"] = {'speed': 15.1232059*deg2rad,
                                   'VAU': T + 3*h - 90,
                                   'FF': N.ones(length)
                                   }
        self.tidal_dict["SO1"] = {'speed': 16.0569644*deg2rad,
                                  'VAU': T + 2*s - h - 90 - nu,
                                  'FF': self.tidal_dict['J1']['FF']
                                  }
        # Seems like A54 in Schureman is equivalent to MKS2 in Foreman
        self.tidal_dict["MKS2"] = {'speed': 29.066241528*deg2rad,
                                  'VAU': 2*T - 2*s + 4*h - 2*nu,
                                  'FF': self.tidal_dict['ETA2']['FF']
                                  }
        # Seems like MP1 in Schureman is equivalent to TAU1 in Foreman
        self.tidal_dict["TAU1"] = {'speed': 14.025172896*deg2rad,
                                  'VAU': T - 2*s + 3*h - 90 - nu,
                                  'FF': self.tidal_dict['J1']['FF']
                                  }
        # Seems like A19 in Schureman is equivalent to BET1 in Foreman
        self.tidal_dict["BETA1"] = {'speed': 14.414556708*deg2rad,
                                  'VAU': T - s - h + p - 90 - 2*zeta - nu,
                                  'FF': self.tidal_dict['O1']['FF']
                                  }
        self.tidal_dict["MK4"] = {'speed': 59.066241516*deg2rad,
                                  'VAU': self.tidal_dict['M2']['VAU'] + self.tidal_dict['K2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF'] * self.tidal_dict['K2']['FF']
                                  }
        self.tidal_dict["MSN2"] = {'speed': 59.066241516*deg2rad,
                                  'VAU': self.tidal_dict['M2']['VAU'] + self.tidal_dict['K2']['VAU'],
                                  'FF': self.tidal_dict['M2']['FF'] * self.tidal_dict['K2']['FF']
                                  }
        self.tidal_dict["2N2"] = {'speed': 27.8953548*deg2rad,
                                  'VAU': 2*(T - 2*s + h + p + zeta - nu),
                                  'FF': self.tidal_dict['M2']['FF']
                                  }
        self.tidal_dict["NU2"] = {'speed': 28.5125831*deg2rad,
                                  'VAU': 2*T - 3*s + 4*h - p + 2*zeta - 2*nu,
                                  'FF': self.tidal_dict['M2']['FF']
                                  }
        # Seems like A4 in Schureman is equivalent to MSM in Foreman
        self.tidal_dict["A4"] = {'speed': 0.4715210880*deg2rad,
                                 'VAU': s - 2*h + p,
                                 'FF': self.tidal_dict['Mm']['FF']
                                 }
        self.tidal_dict["SIGMA1"] = {'speed': 12.9271398*deg2rad,
                                     'VAU': T - 4*s + 3*h + 90 + 2*zeta - nu,
                                     'FF': self.tidal_dict['O1']['FF']
                                     }
        self.tidal_dict["RHO1"] = {'speed': 13.4715145*deg2rad,
                                   'VAU': T - 3*s + 3*h - p + 90 + 2*zeta - nu,
                                   'FF': self.tidal_dict['O1']['FF']
                                   }
        self.tidal_dict["CHI1"] = {'speed': 14.5695476*deg2rad,
                                   'VAU': T - s + 3*h - p - 90 - nu,
                                   'FF': self.tidal_dict['J1']['FF']
                                   }
        self.tidal_dict["THETA1"] = {'speed': 15.5125897*deg2rad,
                                     'VAU': T + s - h + p - 90 - nu,
                                     'FF': self.tidal_dict['J1']['FF']
                                     }
#        self.tidal_dict["OQ2"] =
        self.tidal_dict["LAMBDA2"] = {'speed': 29.4556253*deg2rad,
                                      'VAU': 2*T - s + p + 180,
                                      'FF': self.tidal_dict['M2']['FF']
                                      }
        self.tidal_dict["Sa"] = {'speed': 0.0410686*deg2rad,
                                 'VAU': h,
                                 'FF': N.ones(length)
                                 }
        self.tidal_dict["S1"] = {'speed': 15.0000000*deg2rad,
                                 'VAU': T,
                                 'FF': N.ones(length)
                                 }
        self.tidal_dict["T2"] = {'speed': 29.9589333*deg2rad,
                                 'VAU': 2*T - h + p1,
                                 'FF': N.ones(length)
                                 }
        self.tidal_dict["R2"] = {'speed': 30.0410667*deg2rad,
                                 'VAU': 2*T + h - p1 + 180,
                                 'FF': N.ones(length)
                                 }
        self.tidal_dict["PI1"] = {'speed': 14.9178647*deg2rad,
                                  'VAU': T - 2*h + p1 + 90,
                                  'FF': N.ones(length)
                                  }
        self.tidal_dict["PSI1"] = {'speed': 15.0821352*deg2rad,
                                   'VAU': T + 2*h - p1 - 90,
                                   'FF': N.ones(length)
                                   }

        num_hours = (jd[-1] - jd[0]) * 24
        if num_hours < 13:
            print "Cannot calculate any constituents from this record length"
            sys.exit()
        speed_dict["M2"] = self.tidal_dict["M2"]
        if num_hours >= (24 * rayleigh_comp):
            speed_dict["K1"] = self.tidal_dict["K1"]
        if num_hours >= 25 * rayleigh_comp:
            speed_dict["M3"] = self.tidal_dict["M3"]
            speed_dict["M4"] = self.tidal_dict["M4"]
        if num_hours >= 26 * rayleigh_comp:
            speed_dict["M6"] = self.tidal_dict["M6"]
            speed_dict["M8"] = self.tidal_dict["M8"]
        if num_hours >= 235 * rayleigh_comp:
            # Slower than diurnal: S6
            # Diurnal: 
            # Semidiurnal: 
            # Shallow water:
            # Need: 
            speed_dict["S6"] = self.tidal_dict["S6"]
        if num_hours >= 328 * rayleigh_comp:
            # Slower than diurnal: 
            # Diurnal: O1 
            # Semidiurnal: 
            # Shallow water: 
            # Need: 
            speed_dict["O1"] = self.tidal_dict["O1"]
        if num_hours >= 355 * rayleigh_comp:
            # Slower than diurnal: MSf
            # Diurnal: 
            # Semidiurnal: S2
            # Shallow water: SK3, MS4, S4, 2MS6, 2SM6
            # Need: 
            speed_dict["S2"] = self.tidal_dict["S2"]
            speed_dict["2MS6"] = self.tidal_dict["2MS6"]
            speed_dict["2SM6"] = self.tidal_dict["2SM6"]
            speed_dict["MSf"] = self.tidal_dict["MSf"]
            speed_dict["SK3"] = self.tidal_dict["SK3"]
            # Might need to move this to another time span - couldn't find this
            # in Foreman for Rayleigh comparison pair.
            speed_dict["2SM2"] = self.tidal_dict["2SM2"]
            speed_dict["MS4"] = self.tidal_dict["MS4"]
            speed_dict["S4"] = self.tidal_dict["S4"]
        if num_hours >= 651 * rayleigh_comp:
            # Slower than diurnal: 
            # Diurnal: OO1
            # Semidiurnal: 
            # Shallow water: 
            # Need: 
            speed_dict["OO1"] = self.tidal_dict["OO1"]
        if num_hours >= 656 * rayleigh_comp:
            # Slower than diurnal: 
            # Diurnal: 
            # Semidiurnal: 
            # Shallow water: MK3, MO3
            # Need: 
            speed_dict["MK3"] = self.tidal_dict["MK3"]
            # Seems like 2MK3 in Schureman is equivalent to MO3 in Foreman
            speed_dict["MO3"] = self.tidal_dict["MO3"]
        if num_hours >= 662 * rayleigh_comp:
            # Slower than diurnal: 
            # Diurnal: 2Q1, Q1, NO1, J1, UPS1
            # Semidiurnal: N2, ETA2
            # Shallow water: MN4, 2MN6
            # Need: 
            speed_dict["N2"] =  self.tidal_dict["N2"]
            speed_dict["2MN6"] = self.tidal_dict["2MN6"]
            speed_dict["2Q1"] = self.tidal_dict["2Q1"]
            speed_dict["Q1"] =  self.tidal_dict["Q1"]
            speed_dict["J1"] =  self.tidal_dict["J1"]
            # Seems like KJ2 in Schureman is equivalent to ETA2 in Foreman
            speed_dict["ETA2"] = self.tidal_dict["ETA2"]
            # Seems like KQ1 in Schureman is equivalent to UPS1 in Foreman
            speed_dict["UPS1"] = self.tidal_dict["UPS1"]
            speed_dict["NO1"] =  self.tidal_dict["NO1"]
            speed_dict["MN4"] = self.tidal_dict["MN4"]
        if num_hours >= 764 * rayleigh_comp:
            # Slower than diurnal: Mm
            # Diurnal: ALPHA1
            # Semidiurnal: EPS2, MU2, L2
            # Shallow water: SN4
            # Need: ALPHA1
            speed_dict["Mm"] =  self.tidal_dict["Mm"]
            speed_dict["L2"] =  self.tidal_dict["L2"]
            speed_dict["MU2"] = self.tidal_dict["MU2"]
#            speed_dict["ALPHA1"] = self.tidal_dict["ALPHA1"]
            speed_dict["EPS2"] = self.tidal_dict["EPS2"]
            speed_dict["SN4"] = self.tidal_dict["SN4"]
        if num_hours >= 4383 * rayleigh_comp:
            # Slower than diurnal: Ssa, Mf
            # Diurnal: PHI1, P1, BETA1, TAU1
            # Semidiurnal: K2, MSN2
            # Shallow water: SO1, MKS2, MSN3, SO3, MK4, SK4, 2MK6, MSK6
            # Need MSN3, SK4, 2MK6, MSK6
            speed_dict["Ssa"] = self.tidal_dict["Ssa"]
            speed_dict["Mf"] =  self.tidal_dict["Mf"]
            speed_dict["P1"] = self.tidal_dict["P1"]
            speed_dict["K2"] = self.tidal_dict["K2"]
            speed_dict["SO3"] = self.tidal_dict["SO3"]
            speed_dict["PHI1"] = self.tidal_dict["PHI1"]
            speed_dict["SO1"] = self.tidal_dict["SO1"]
            # Seems like A54 in Schureman is equivalent to MKS2 in Foreman
            speed_dict["MKS2"] = self.tidal_dict["MKS2"]
            # Seems like MP1 in Schureman is equivalent to TAU1 in Foreman
            speed_dict["TAU1"] = self.tidal_dict["TAU1"]
            # Seems like A19 in Schureman is equivalent to BET1 in Foreman
            speed_dict["BETA1"] = self.tidal_dict["BETA1"]
            speed_dict["MK4"] = self.tidal_dict["MK4"]
            speed_dict["MSN2"] = self.tidal_dict["MSN2"]
        if num_hours >= 4942 * rayleigh_comp:
            speed_dict["2N2"] = self.tidal_dict["2N2"]
            speed_dict["NU2"] = self.tidal_dict["NU2"]
            # Seems like A4 in Schureman is equivalent to MSM in Foreman
            speed_dict["A4"] = self.tidal_dict["A4"]
            speed_dict["SIGMA1"] = self.tidal_dict["SIGMA1"]
            speed_dict["RHO1"] = self.tidal_dict["RHO1"]
            speed_dict["CHI1"] = self.tidal_dict["CHI1"]
            speed_dict["THETA1"] = self.tidal_dict["THETA1"]
#            speed_dict["OQ2"] =self.tidal_dict["OQ2"]
            speed_dict["LAMBDA2"] = self.tidal_dict["LAMBDA2"]
        if num_hours >= 8766 * rayleigh_comp:
            speed_dict["Sa"] = self.tidal_dict["Sa"]
        if num_hours >= 8767 * rayleigh_comp:
            speed_dict["S1"] = self.tidal_dict["S1"]
            speed_dict["T2"] = self.tidal_dict["T2"]
            speed_dict["R2"] = self.tidal_dict["R2"]
            speed_dict["PI1"] = self.tidal_dict["PI1"]
            speed_dict["PSI1"] = self.tidal_dict["PSI1"]
#            speed_dict["H1"] =self.tidal_dict["H1"]
#            speed_dict["H2"] =self.tidal_dict["H2"]
        if num_hours >= 11326 * rayleigh_comp:
            # GAM2 from Foreman should go here, but couldn't find comparable
            # constituent information from Schureman
            pass
        # This is what is required to separate NO1 and M1
        if num_hours >= 77554 * rayleigh_comp:
            speed_dict["M1"] = self.tidal_dict["M1"]

        key_list = speed_dict.keys()
        key_list.sort()

        # Fix VAU to be between 0 and 360
        for key in key_list:
            speed_dict[key]['VAU'] = N.mod(speed_dict[key]['VAU'], 360)
            try:
                speed_dict[key]['VAU'] = speed_dict[key]['VAU'][0]
            except TypeError:
                pass
        return (speed_dict, key_list)


    def dates2jd(self, dates):
        jd = N.zeros(len(dates), "d")
        if isinstance(dates[0], datetime.datetime):
            for index, dt in enumerate(dates):
                # The -0.5 is needed because astronomers measure their zero from GMT noon,
                # whereas oceanographers measure the tide from zero at midnight.
                jd[index] = (cal.cal_to_jd(dt.year, dt.month, dt.day) + uti.hms_to_fday(dt.hour, dt.minute, dt.second))# + 0.5
        else:
            jd = dates
        return jd


    def astronomic(self, dates):
        # Work from astrolabe and Jean Meeuss
        import astrolabe.elp2000 as elp
        import astrolabe.sun as sun

        lunar_eph = elp.ELP2000()
        solar_eph = sun.Sun()

        Nv = N.zeros(len(dates), "d")
        p1 = N.zeros(len(dates), "d")
        jd = self.dates2jd(dates)
        for index, dt in enumerate(dates):
            jdc = cal.jd_to_jcent(jd[index])
            Nv[index] = N.mod(125.0445479 - 1934.1362891*jdc + 0.0020754*jdc**2
                       + (jdc**3)/467441.0 - (jdc**4)/60616000.0, 360)
            p1[index] = N.mod((1012395.0 + 6189.03*(jdc + 1) + 1.63*(jdc + 1)**2 + 0.012*(jdc + 1)**3)/3600.0, 360)
        jdc = cal.jd_to_jcent(jd[0])
        p = N.mod(83.3532465 + 4069.0137287*jdc - 0.0103200*jdc**2
                   - (jdc**3)/80053.0 + (jdc**4)/18999000.0, 360)

        s = lunar_eph.dimension(jd[0] - 0.5, 'L') * rad2deg
        h = solar_eph.dimension(jd[0] - 0.5, 'L') * rad2deg

        Nrad = Nv * deg2rad
        # Calculate constants for V+u
        # I, inclination of Moon's orbit, pg 156, Schureman
        i = N.arccos(0.9136949 - 0.0356926 * N.cos(Nrad))

        # pg 156
        const_1 = 1.01883*N.tan(0.5*Nrad)
        const_2 = 0.64412*N.tan(0.5*Nrad)
        const_3 = 2.*N.arctan(const_1)-Nrad
        const_4 = 2.*N.arctan(const_2)-Nrad
        zeta = -0.5*(const_3+const_4)
        nu = 0.5*(const_3-const_4)

        const_1 = N.sin(2.0*i)*N.sin(nu)
        const_2 = N.sin(2.0*i)*N.cos(nu)+0.3347
        nupp = N.arctan(const_1/const_2)  # eq 224

        const_1 = N.sin(i)**2 * N.sin(2.0*nu)
        const_2 = N.sin(i)**2 * N.cos(2.0*nu)+0.0727
        two_nupp = N.arctan(const_1/const_2) # eq 232

        i = i*rad2deg
        zeta = zeta*rad2deg
        nu = nu*rad2deg
        nupp = nupp*rad2deg
        two_nupp = two_nupp*rad2deg
        #hour = jd - jd.astype('i') 
        hour = jd[0] - int(jd[0])

        kap_p = (p-zeta)*deg2rad
        ii = i*deg2rad
        # pg 44, Schureman
        term1 = N.sin(2.*kap_p)
        term2 = (1./6.)*(1./N.tan(ii*0.5))**2
        term3 = N.cos(2.*kap_p)
        R = N.arctan(term1/(term2-term3))*rad2deg

        # pg 42
        Q = N.arctan(0.483*N.tan(kap_p))*rad2deg

        T = 360.*hour

        # This should be stream lined... needed to support 
        # the larger sized vector when filling missing values.
        return (zeta, nu, nupp, two_nupp, kap_p, ii, R, Q, T, jd, s, h, Nv, p, p1)


    def usgs_filter(self, dates, elev):
        """ Filters out periods of 25 hours and less from self.elevation.

        """

        kern = [  
              -0.00027,-0.00114,-0.00211,-0.00317,-0.00427,
              -0.00537,-0.00641,-0.00735,-0.00811,-0.00864,
              -0.00887,-0.00872,-0.00816,-0.00714,-0.00560,
              -0.00355,-0.00097, 0.00213, 0.00574, 0.00980,
               0.01425, 0.01902, 0.02400, 0.02911, 0.03423,
               0.03923, 0.04399, 0.04842, 0.05237, 0.05576,
               0.05850, 0.06051, 0.06174, 0.06215, ]

        kern = N.concatenate((kern[:-1], kern[::-1]))

        usgs_filtered = N.convolve(elev, kern, mode = 1)

        return usgs_filtered


    def missing(self, task, dates, elev):
        """ What to do with the missing values """

        if task not in ['fail', 'ignore', 'fill']:
            print "missing-data must be one of 'fail' (the default), 'ignore', or 'fill'"
            sys.exit()

        if task == 'ignore':
            return (dates, elev)

        interval = dates[1:] - dates[:-1]

        if N.any(interval > datetime.timedelta(seconds = 3600)):
            if task == 'fail':
                print "There is a difference of greater than one hour between values"
                sys.exit()

        if task == 'fill':
            # Create real dates
            start = dates[0]
            # Dominant interval
            interval.sort()
            interval = interval[len(interval)/2]
    
            dt = dates[0]
            dates_filled = []
            while dt <= dates[-1]:
                dates_filled.append(dt)
                dt = dt + interval
    
            dates_filled = N.array(dates_filled)
    
            where_good = N.zeros(len(dates_filled), dtype='bool') 
    
            for dt in dates:
                where_good[dates_filled == dt] = True

            if N.all(where_good):
                return (dates, elev)

            # Had to make this 'f8' in order to match 'total' and 'self.elevation'
            # Don't know why this was different.
            residuals = N.ones(len(dates_filled), dtype='f8') * -99999.0
    
            package = self.astronomic(dates_filled)
            (speed_dict, key_list) = self.which_constituents(len(dates_filled), package)
            (zeta, nu, nupp, two_nupp, kap_p, ii, R, Q, T, jd_filled, s, h, Nv, p, p1) = package

            # This means that we might do this twice...
            try:
                a = self.r
            except AttributeError:
                self.constituents()
    
            ntimes_filled = (jd_filled - jd_filled[0])*24
            total = self.sum_signals(self.key_list, ntimes_filled, speed_dict)
    
    
            residuals[where_good] = elev - total[where_good]
    
            # Might be able to use N.piecewise, but have to rethink
            # N.piecewise gives the piece of the array to the function
            #  but I want to use the border values of the array zone
            zone_calculations(interpolate, residuals, residuals == -99999)
   
            return (dates_filled, residuals + total)


    def remove_extreme_values(self):
        avg = N.average(self.elevation)
        std = N.std(self.elevation)

        good = self.elevation < (avg + 2.0*std)
        self.elevation = N.compress(good, self.elevation)
        self.dates = N.compress(good, self.dates)

        good = self.elevation > (avg - 2.0*std)
        self.elevation = N.compress(good, self.elevation)
        self.dates = N.compress(good, self.dates)


    def residuals(self, p, ht, t, key_list):
        """ Used for least squares fit.
    
        """
        H = {}
        phase = {}
        slope = {}
        for index, key in enumerate(key_list):
            H[key] = p[index]
            phase[key] = p[index + len(key_list)]

        if len(self.speed_dict[key_list[0]]['FF']) == len(t):
            ff = self.tidal_dict
        else:
            # This is for the short term harmonic analysis.
            ff = {}
            for key in key_list:
                ff[key] = {'FF': N.ones(len(t))}

        self.inferred_key_list = []
        self.inferred_r = {}
        self.inferred_phase = {}
        if 'O1' in key_list and 'K1' in key_list:
            if 'J1' not in key_list:
                self.inferred_key_list.append('J1')
                self.inferred_r['J1'] = H['J1'] = 0.079 * H['O1']
                self.inferred_phase['J1'] = phase['J1'] = phase['K1'] + 0.496*(phase['K1'] - phase['O1']) 
            # How should I handle this?  Shureman seems to confuse M1 and NO1
            #if 'M1' not in key_list:
            #    self.inferred_key_list.append('M1')
            #    self.inferred_r['M1'] = H['M1'] = 0.071 * H['O1']
            #    self.inferred_phase['M1'] = phase['M1'] = phase['K1'] - 0.5*(phase['K1'] - phase['O1']) 
            if 'OO1' not in key_list:
                self.inferred_key_list.append('OO1')
                self.inferred_r['OO1'] = H['OO1'] = 0.043 * H['O1']
                self.inferred_phase['OO1'] = phase['OO1'] = phase['K1'] + 1.0*(phase['K1'] - phase['O1']) 
            if 'P1' not in key_list:
                self.inferred_key_list.append('P1')
                self.inferred_r['P1'] = H['P1'] = 0.331 * H['K1']
                self.inferred_phase['P1'] = phase['P1'] = phase['K1'] - 0.075*(phase['K1'] - phase['O1']) 
            if 'Q1' not in key_list:
                self.inferred_key_list.append('Q1')
                self.inferred_r['Q1'] = H['Q1'] = 0.194 * H['O1']
                self.inferred_phase['Q1'] = phase['Q1'] = phase['K1'] - 1.496*(phase['K1'] - phase['O1']) 
            if '2Q1' not in key_list:
                self.inferred_key_list.append('2Q1')
                self.inferred_r['2Q1'] = H['2Q1'] = 0.026 * H['O1']
                self.inferred_phase['2Q1'] = phase['2Q1'] = phase['K1'] - 1.992*(phase['K1'] - phase['O1']) 
            if 'RHO1' not in key_list:
                self.inferred_key_list.append('RHO1')
                self.inferred_r['RHO1'] = H['RHO1'] = 0.038 * H['O1']
                self.inferred_phase['RHO1'] = phase['RHO1'] = phase['K1'] - 1.429*(phase['K1'] - phase['O1']) 
        if 'S2' in key_list and 'M2' in key_list:
            if 'K2' not in key_list:
                self.inferred_key_list.append('K2')
                self.inferred_r['K2'] = H['K2'] = 0.272 * H['S2']
                self.inferred_phase['K2'] = phase['K2'] = phase['S2'] + 0.081*(phase['S2'] - phase['M2']) 
            if 'L2' not in key_list:
                self.inferred_key_list.append('L2')
                self.inferred_r['L2'] = H['L2'] = 0.028 * H['M2']
                self.inferred_phase['L2'] = phase['L2'] = phase['S2'] - 0.464*(phase['S2'] - phase['M2']) 
            if 'N2' not in key_list:
                self.inferred_key_list.append('N2')
                self.inferred_r['N2'] = H['N2'] = 0.194 * H['M2']
                self.inferred_phase['N2'] = phase['N2'] = phase['S2'] - 1.536*(phase['S2'] - phase['M2']) 
            if '2N2' not in key_list:
                self.inferred_key_list.append('2N2')
                self.inferred_r['2N2'] = H['2N2'] = 0.026 * H['M2']
                self.inferred_phase['2N2'] = phase['2N2'] = phase['S2'] - 2.072*(phase['S2'] - phase['M2']) 
            if 'R2' not in key_list:
                self.inferred_key_list.append('R2')
                self.inferred_r['R2'] = H['R2'] = 0.008 * H['S2']
                self.inferred_phase['R2'] = phase['R2'] = phase['S2'] + 0.040*(phase['S2'] - phase['M2']) 
            if 'T2' not in key_list:
                self.inferred_key_list.append('T2')
                self.inferred_r['T2'] = H['T2'] = 0.059 * H['S2']
                self.inferred_phase['T2'] = phase['T2'] = phase['S2'] - 0.040*(phase['S2'] - phase['M2']) 
            if 'LAMBDA2' not in key_list:
                self.inferred_key_list.append('LAMBDA2')
                self.inferred_r['LAMBDA2'] = H['LAMBDA2'] = 0.007 * H['M2']
                self.inferred_phase['LAMBDA2'] = phase['LAMBDA2'] = phase['S2'] - 0.536*(phase['S2'] - phase['M2']) 
            if 'MU2' not in key_list:
                self.inferred_key_list.append('MU2')
                self.inferred_r['MU2'] = H['MU2'] = 0.024 * H['M2']
                self.inferred_phase['MU2'] = phase['MU2'] = phase['S2'] - 2.0*(phase['S2'] - phase['M2']) 
            if 'NU2' not in key_list:
                self.inferred_key_list.append('NU2')
                self.inferred_r['NU2'] = H['NU2'] = 0.038 * H['M2']
                self.inferred_phase['NU2'] = phase['NU2'] = phase['S2'] - 1.464*(phase['S2'] - phase['M2']) 
        for key in self.inferred_key_list:
            if self.inferred_r[key] < 0:
                self.inferred_r[key] = abs(self.inferred_r[key])
                self.inferred_phase[key] = self.inferred_phase[key] + 180.0
            try:
                self.inferred_phase[key] = N.mod(self.inferred_phase[key] + self.tidal_dict[key]['VAU'][0], 360)
            except TypeError:
                self.inferred_phase[key] = N.mod(self.inferred_phase[key] + self.tidal_dict[key]['VAU'], 360)



        sumterm = N.zeros((len(t)))
        for i in key_list + self.inferred_key_list:
            sumterm = sumterm + H[i]*ff[i]['FF']*N.cos(self.tidal_dict[i]['speed']*t - phase[i])

        if self.options.linear_trend:
            self.err = ht - (p[-2]*t + p[-1] + sumterm)
        else:    
            self.err = ht - (p[-1] + sumterm)

# What was this from?
#        self.err[N.absolute(self.err) > (N.average(self.err) + 3.0*N.std(self.err))] = 0.0

        return self.err


    #--------------------------

                                                
    def constituents(self):
        difference = self.dates[1:] - self.dates[:-1]
        if N.any(difference < datetime.timedelta(seconds = 0)):
            print "Let's do the time warp again!"
            print "The date values reverse - they must be constantly increasing."
            sys.exit()

        p0 = [1.0]*(len(self.speed_dict)*2 + 2)
        p0[-2] = 0.0
        p0[-1] = N.average(self.elevation)
        self.ntimes = (self.jd - self.jd[0]) * 24 

        lsfit = leastsq(self.residuals, p0, args=(self.elevation, self.ntimes, self.key_list))

        self.r = {}
        self.phase = {}
        for index, key in enumerate(self.key_list):
            self.r[key] = lsfit[0][index]
            self.phase[key] = lsfit[0][index + len(self.key_list)]*rad2deg

            if self.r[key] < 0:
                self.r[key] = abs(self.r[key])
                self.phase[key] = self.phase[key] + 180
            self.phase[key] = N.mod(self.phase[key] + self.speed_dict[key]['VAU'], 360)
        self.fitted_average = p0[-1]
        self.slope = p0[-2]


    def sum_signals(self, skey_list, hours, speed_dict, amp = None, phase = None):
        total = N.zeros(len(hours), dtype='f')
        if isinstance(hours[0], datetime.datetime):
            hours = self.dates2jd(hours)
            hours = (hours - hours[0]) * 24
        for i in skey_list:
            if amp != None:
                R = (amp - N.average(amp)) + self.r[i]
            else:
                R = self.r[i]
            if phase != None:
                p = (phase - N.average(phase)) + self.phase[i]
            else:
                p = self.phase[i]
            component = R*speed_dict[i]['FF']*N.cos(speed_dict[i]['speed']*hours - (p - speed_dict[i]['VAU'])*deg2rad)
            total = total + component
        return total


    def filters(self, nstype, dates, elevation, pad_type=None):

        # For the time being the filters can only work on hourly data.  If the
        # data is less than hourly, I filter each data point separately.  For
        # example: if the data is every 15 minutes I run the filter 4 times -
        # on the hour, quarter past, half past, quarter till.

        interval = dates[1:] - dates[:-1]
        interval.sort()
        interval = interval[len(interval)/2]

        rep_dict = {
                    60: 1,
                    6 : 10,
                    10: 6,
                    12: 5,
                    15: 4,
                    20: 3,
                    30: 2,
                   }

        tot_rep = rep_dict[interval.seconds/60]

        dates, elevation = self.missing('fill', 
                                        dates, 
                                        elevation)

        relevation = N.empty_like(elevation)

        for rep in range(tot_rep):
            ndates = dates[rep::tot_rep]
            nelevation = elevation[rep::tot_rep]

            if nstype == 'doodson':
                # Doodson filter

                # The Doodson X0 filter is a simple filter designed to damp out
                # the main tidal frequencies. It takes hourly values, 19 values
                # either side of the central one. A weighted average is taken
                # with the following weights

                #(1010010110201102112 0 2112011020110100101)/30.
                kern = [1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 2, 0, 1, 1, 0, 2, 1, 1, 2,
                        0,
                        2, 1, 1, 2, 0, 1, 1, 0, 2, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1]

                kern = [i/30.0 for i in kern]
                relevation[rep::tot_rep] = N.convolve(nelevation, kern, mode = 1)

            if nstype == 'usgs':
                relevation[rep::tot_rep] = self.usgs_filter(ndates, nelevation)

            if nstype == 'boxcar':
                kern = N.ones(25) * (1./25.)
                relevation[rep::tot_rep] = N.convolve(nelevation, kern, mode = 1)

            if nstype == 'mstha':
                blen = 12
                s_list = ['M2', 'K1', 'M3', 'M4']

                p0 = [1.0]*(len(s_list)*2 + 2)
                p0[-2] = 0.0
                new_dates = N.concatenate(([ndates[0] - datetime.timedelta(hours = blen)],
                                        ndates,
                                        [ndates[-1] + datetime.timedelta(hours = blen)]))
                new_elevation = N.concatenate(([nelevation[0]],
                                            nelevation,
                                            [nelevation[-1]]))
                (new_dates, new_elev) = self.missing('fill', new_dates, new_elevation)
                slope = []
                new_dates = self.dates2jd(new_dates)
                ntimes = N.arange(2*blen + 1)
                for d in range(len(new_dates))[blen:-blen]:
              #      ntimes = (new_dates[d-12:d+12] - new_dates[d]) * 24 
                    nelev = new_elev[d-blen:d+blen+1]
                    lsfit = leastsq(self.residuals, p0, args=(nelev, ntimes, s_list))
                    slope.append(lsfit[0][-2])

                relevation[rep::tot_rep] = slope

            if nstype == 'wavelet':
                import pywt
                import pylab
    
                for wl in pywt.wavelist():
    
                    w = pywt.Wavelet(wl)
    
                    max_level = pywt.dwt_max_level(len(elevation), w.dec_len)
                    a = pywt.wavedec(elevation, w, level = max_level, mode='sym')
    
                    for i in range(len(a))[1:]:
                        avg = N.average(a[i][:])
                        std = 2.0*N.std(a[i][:])
                        a[i][(a[i][:] < (avg + std)) & (a[i][:] > (avg - std))] = 0.0
        
                    for index, items in enumerate(a):
                        self.write_file("outts_wavelet_%s_%i.dat" % (wl, index), dates, items)
        
                    y = pywt.waverec(a, w, mode='sym')
                    self.write_file("%s.dat" % wl, dates, y)
        
                relevation[rep::tot_rep] = y
    
            if nstype == 'cd':
                print "Complex demodulation filter doesn't work right yet - still testing."
        
                (new_dates, new_elev) = self.missing('fill', ndates, nelevation)
                package = self.astronomic(new_dates)
                (zeta, nu, nupp, two_nupp, kap_p, ii, R, Q, T, jd_filled, s, h, Nv, p, p1) = package
                (speed_dict, key_list) = self.which_constituents(len(new_dates), package)
                kern = N.ones(25) * (1./25.)
    
                ns_amplitude = {}
                ns_phase = {}
                constituent_residual = {}
                tot_amplitude = N.zeros(len(jd_filled))
                for key in key_list:
                    # Since speed that I have been using is radians/hour
                    # you have to divide by 2*N.pi so I just removed 2*N.pi
                    # from the multiplication.
                    ntimes_filled = (jd_filled - jd_filled[0])*24
                    yt = new_elev*N.exp(-1j*speed_dict[key]['speed']*ntimes_filled)
    
                    ns_amplitude[key] = N.absolute(yt)
                    ns_amplitude[key] = yt.real
                    ns_amplitude[key] = N.convolve(ns_amplitude[key], 
                                                   kern, 
                                                   mode = 1)
    
                    ns_phase[key] = N.arctan2(yt.imag, yt.real) * rad2deg
                    ns_phase[key] = N.convolve(ns_phase[key], kern, mode = 1)
    
                    new_list = [i for i in self.key_list if i != key]
                    everything_but = self.sum_signals(new_list, 
                                                      ntimes_filled, 
                                                      speed_dict)
                    constituent_residual[key] = new_elev - everything_but
                relevation[rep::tot_rep] = everything_but
        return relevation


    def write_file(self, fname, x, y):
        if isinstance(y, dict):
            print y.keys()
            for key in y.keys():
                nfname = "%s_%s.dat" % (os.path.splitext(fname)[-2], key)
                self.write_file(nfname, x, y[key])
        else:
            fpo = open(fname, "w")
            for d, v in zip(x, y):
                fpo.write("%s %f\n" % (d.isoformat(), v))


    def sortbyvalue(self, dict):
        """ Return a list of (key, value) pairs, sorted by value. """
        _swap2 = lambda (x, y): (y, x)
        mdict = map(_swap2, dict.items())
        mdict.sort()
        mdict = map(_swap2, mdict)
        return mdict


    def print_con(self):
        ndict = {}
        for k in self.key_list:
            ndict[k] = self.speed_dict[k]['speed']

        print "\n%12s %12s %12s %12s" % ("NAME", "SPEED", "H", "PHASE")
        print   "%12s %12s %12s %12s" % ("====", "=====", "=", "=====")
        klist = [i[0] for i in self.sortbyvalue(ndict)]
        for i in klist:
            print "%12s %12.8f %12.4f %12.4f" % (i, 
                                                self.speed_dict[i]['speed']*rad2deg, 
                                                self.r[i], 
                                                self.phase[i])
        print "\nINFERRED CONSTITUENTS"
        ndict = {}
        for k in self.inferred_key_list:
            ndict[k] = self.tidal_dict[k]['speed']
        print "%12s %12s %12s %12s" % ("NAME", "SPEED", "H", "PHASE")
        print "%12s %12s %12s %12s" % ("====", "=====", "=", "=====")
        klist = [i[0] for i in self.sortbyvalue(ndict)]
        for i in klist:
            print "%12s %12.8f %12.4f %12.4f" % (i, 
                                                self.tidal_dict[i]['speed']*rad2deg, 
                                                self.inferred_r[i], 
                                                self.inferred_phase[i])

        print "\nAVERAGE (Z0) = ", self.fitted_average
        if self.options.linear_trend:
            print "SLOPE OF REMOVED LINEAR TREND = ", self.slope


    def print_ephemeris_table(self):
        for d in range(1600, 2001, 100):
            dates = [datetime.datetime(d, 1, 1, 12, 0), 
                     datetime.datetime(d, 1, 2, 12, 0)]
            package = self.astronomic(dates)
            (zeta, nu, nupp, two_nupp, kap_p, ii, R, Q, T, jd_filled, s, h, Nv, p, p1) = package
            print dates[0].isoformat(), h, p1[0], s, p, Nv[0]


    def print_v_u_table(self):
        dates = []
        for d in range(1850, 2001):
            dates.append(datetime.datetime(d, 1, 1, 0, 0))
        dates = N.array(dates)

        package = self.astronomic(dates)
        (zeta, nu, nupp, two_nupp, kap_p, ii, R, Q, T, jd_filled, s, h, Nv, p, p1) = package
        (speed_dict, key_list) = self.which_constituents(len(dates), package)

        key_list.sort()
        for key in key_list:
            print key, speed_dict[key]['VAU']


    def print_node_factor_table(self):
        pass

#=============================
def main(options, args):

    if len(args) == 1:
        def_filename = None
    elif len(args) == 2:
        def_filename = args[1]
    else:
        fatal('main', 'Need to pass input file name and optional definition file name')

    x = tappy(args[0], def_filename = def_filename)

    x.options = options

    if x.options.ephemeris:
        x.print_ephemeris_table()

    if x.options.print_vau_table:
        x.print_v_u_table()

    if x.options.missing_data == 'fail':
        x.dates_filled, x.elevation_filled = x.missing(x.options.missing_data, 
                                                       x.dates, 
                                                       x.elevation)

    if x.options.remove_extreme:
        x.remove_extreme_values()

    package = x.astronomic(x.dates)
    (x.zeta, x.nu, x.nupp, x.two_nupp, x.kap_p, x.ii, x.R, x.Q, x.T, x.jd, x.s, x.h, x.N, x.p, x.p1) = package

    if options.rayleigh:
        ray = float(options.rayleigh)
    else:
        ray = 1.0
    (x.speed_dict, x.key_list) = x.which_constituents(len(x.dates), 
                                                      package, 
                                                      rayleigh_comp = ray)

    if x.options.zero_ts:
        x.elevation = x.elevation - x.filters(options.zero_ts, 
                                              x.dates, 
                                              x.elevation)

    x.constituents()

    if x.options.missing_data == 'fill':
        x.dates_filled, x.elevation_filled = x.missing(x.options.missing_data, x.dates, x.elevation)
        x.write_file('outts_filled.dat', x.dates_filled, x.elevation_filled)

    if x.options.filter:
        for item in x.options.filter.split(','):
            if item in ['mstha', 'wavelet', 'cd', 'boxcar', 'usgs']:# 'lecolazet', 'godin', 'sfa']:
                result = x.filters(item, x.dates_filled, x.elevation_filled)
                x.write_file('outts_filtered_%s.dat' % (item,), x.dates_filled, result)

    if not x.options.quiet:
        x.print_con()

    if x.options.output:
        for key in x.key_list:
            x.write_file("outts_%s.dat" % (key,), 
                         x.dates, 
                         x.sum_signals([key], x.dates, x.speed_dict))
        x.write_file("outts_total_prediction.dat", 
                     x.dates, 
                     x.sum_signals(x.key_list, x.dates, x.speed_dict))
        x.write_file("outts_original.dat", x.dates, x.elevation)

#-------------------------
if __name__ == '__main__':
    ftn = "main"

    from optparse import OptionParser

    parser = OptionParser(usage = '%prog [options] input_file [optional_definition_file]', version = __version__)
    parser.add_option(
                   '-q', 
                   '--quiet', 
                   help='Print nothing to the screen.', 
                   action='store_true',
                   default = False,
                     )
    parser.add_option(
                   '-d',
                   '--debug',
                   help='Print debug messages.',
                   action='store_true',
                   default = False,
                     )
    parser.add_option(
                   '-o',
                   '--output',
                   help='Write output time-series.',
                   action='store_true',
                   default = False,
                     )
    parser.add_option(
                   '-e',
                   '--ephemeris',
                   help='Print out ephemeris tables.',
                   action='store_true',
                   default = False,
                     )
    parser.add_option(
                   '-y',
                   '--rayleigh',
                   help='Print out ephemeris tables.',
                   metavar = 'FACTOR'
                     )
    parser.add_option(
                   '-u',
                   '--print-vau_table',
                   help='Print out VAU table.',
                   action='store_true',
                   default = False,
                     )
    parser.add_option(
                   '-m',
                   '--missing-data',
                   help='What should be done if there is missing data.  One of: fail, ignore, or fill. [default: %default]',
                   default = 'ignore',
                     )
    parser.add_option(
                   '-l',
                   '--linear-trend',
                   help='Include a linear trend in the least squares fit.',
                   action = 'store_true',
                     )
    parser.add_option(
                   '-r',
                   '--remove-extreme',
                   help='Remove values outside of 2 standard deviations before analysis.',
                   action = 'store_true',
                     )
    parser.add_option(
                   '-z',
                   '--zero-ts',
                   help='Zero the input time series before constituent analysis by subtracting filtered data. One of: boxcar,usgs,mstha,cd.',#lecolazet,godin,sfa
                   metavar = 'FILTER',
                     )
    parser.add_option(
                   '-f',
                   '--filter',
                   help='Filter input data set with tide elimination filters. The -o output option is implied. Any mix separated by commas and no spaces: boxcar,usgs,mstha,wavelet,cd.',#,lecolazet,godin,sfa
                   metavar = 'FILTER',
                     )
#    parser.add_option(
#                   '-p',
#                   '--pad-filters',
#                   help='Pad input data set with values to return same size after filtering.  Realize edge effects are unavoidable.  One of [reflect, mean, median]',
#                   action='store_true',
#                     )
    
    (options, args) = parser.parse_args()


    #---make the object and run it---
    main(options, args)

#===Revision Log===
#Created by mkpythonproj:
#2005-06-13  Tim Cera  
#
