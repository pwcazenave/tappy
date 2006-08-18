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
import getopt
import string
import math
import scipy as N
from scipy.optimize import leastsq
import datetime

import tappy_lib
import sparser

#===globals======================
modname="tappy"
__version__="0.5.1"

#--option args--
debug_p=0
#opt_b=None  #string arg, default is undefined

#---positional args, default is empty---
pargs=[]    

#---other---
deg2rad = N.pi/180.0
rad2deg = 180.0/N.pi


#===utilities====================
def msg(txt):
    sys.stdout.write(txt)
    sys.stdout.flush()

def debug(ftn,txt):
    if debug_p:
        sys.stdout.write("%s.%s:%s\n" % (modname,ftn,txt))
        sys.stdout.flush()

def fatal(ftn,txt):
    msg="%s.%s:FATAL:%s\n" % (modname,ftn,txt)
    raise SystemExit, msg
 
def usage():
    print __doc__


#====================================
class tappy:
    #---class variables---
    #--------------------------
    def __init__(self, filename, def_filename=None):
        ftn="tappy.__init__"
        #---instance variables---
        self.speed_dict = {}

        # Read in data file
        # Data file format is what can be downloaded from COOPS web site.
        fp = sparser.ParseFileLineByLine(filename, def_filename=def_filename, mode='r')
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



    def which_constituents(self):
        # Set data into speed_dict depending on length of time series
        # Required length of time series depends on Raleigh criteria to 
        # differentiate beteen constituents of simmilar speed.
        #  Key is tidal constituent name from Schureman
        #    speed is how fast the constiuent moves in degrees/hour
        #    VAU is V+u taken from Schureman
        #    FF is the node factor from Schureman

        num_hours = (self.jd[-1] - self.jd[0]) * 24
        if num_hours < 13:
            print "Cannot calculate any constituents from this record length"
            sys.exit()
        self.speed_dict["M2"] = {'speed': 28.984104252*deg2rad,
                                 'VAU': 2*(self.T - self.s + self.h + self.zeta - self.mu),
                                 'FF': N.cos(0.5*self.ii)**4 /0.9154  # eq 78
                                 }
        if num_hours >= 24:
            self.speed_dict["K1"] = {'speed': 15.041068632*deg2rad,
                                     'VAU': self.T + self.h + 90 - self.mupp,
                                     'FF': (0.8965*(N.sin(2.*self.ii)**2) + 0.6001*N.sin(2.*self.ii)*N.cos(self.mu*deg2rad) + 0.1006)**0.5  # eq 227
                                     }
        if num_hours >= 25:
            self.speed_dict["M3"] = {'speed': 43.476156360*deg2rad,
                                     'VAU': 3*self.T - 3*self.s + 3*self.h + 3*self.zeta - 3*self.mu,
                                     'FF': N.cos(0.5*self.ii)**6 /0.8758  # eq 149
                                     }
            self.speed_dict["M4"] = {'speed': 57.968208468*deg2rad,
                                     'VAU': 2.*self.speed_dict['M2']['VAU'],
                                     'FF': self.speed_dict['M2']['FF']**2
                                     }
        if num_hours >= 26:
            self.speed_dict["M6"] = {'speed': 86.952312720*deg2rad,
                                     'VAU': 3.*self.speed_dict['M2']['VAU'],
                                     'FF': self.speed_dict['M2']['FF']**2
                                     }
        if num_hours >= 328:
            self.speed_dict["O1"] = {'speed': 13.943035584*deg2rad,
                                     'VAU': self.T - 2*self.s + self.h - 90 + 2*self.zeta - self.mu,
                                     'FF': N.sin(self.ii)*N.cos(0.5*self.ii)**2 /0.3800
                                     }
                                     # thirty_one - thirty
                                     # (sixteen - eight) - (twenty_nine + 90)
                                     # sixteen - eight - twenty_nine - 90
                                     # (three + fifteen) - (mu) - (2*twenty_eight) - 90
                                     # h + T - mu - 2*(one - nine) - 90
                                     # h + T - mu - 2*s + 2*zeta - 90
                                     # T - 2*s + h - 90 + 2*zeta - mu
        if num_hours >= 355:
            self.speed_dict["MSf"] = {'speed': 1.0158957720*deg2rad,
                                      'VAU': 2.0*(self.s - self.h),
                                      'FF': ((2./3.) - N.sin(self.ii)**2)/0.5021
                                      }
            self.speed_dict["S2"] = {'speed': 30.0000000 * deg2rad,
                                     'VAU': 2*self.T,
                                     'FF': N.ones(len(self.T))
                                     }
            self.speed_dict["SK3"] = {'speed': 45.041068656 * deg2rad,
                                      'VAU': 3*self.T + self.h - 90 - self.mupp,
                                      'FF': self.speed_dict['K1']['FF']
                                      }
            self.speed_dict["2SM2"] = {'speed': 31.015884960*deg2rad,
                                      'VAU': 2*self.T + 2*self.s - 2*self.h - 2*self.zeta + 2*self.mu,
                                      'FF': self.speed_dict['M2']['FF']
                                      }
            self.speed_dict["MS4"] = {'speed': 58.984104240*deg2rad,
                                      'VAU': self.speed_dict['M2']['VAU'] + self.speed_dict['S2']['VAU'],
                                      'FF': self.speed_dict['M2']['FF']
                                      }
            self.speed_dict["S4"] = {'speed': 60.0*deg2rad,
                                      'VAU': 4*self.T,
                                      'FF': N.ones(len(self.T))
                                      }
        if num_hours >= 651:
            self.speed_dict["OO1"] = {'speed': 16.139101680*deg2rad,
                                      'VAU': self.T + 2*self.s + self.h - 90 - 2*self.zeta - self.mu,
                                      'FF': (N.sin(self.ii)*N.sin(0.5*self.ii)**2)/0.0164
                                      }
        if num_hours >= 656:
            self.speed_dict["MK3"] = {'speed': 44.025172884*deg2rad,
                                      'VAU': self.speed_dict['M2']['VAU']+self.speed_dict['K1']['VAU'],
                                      'FF': self.speed_dict['M2']['FF']*self.speed_dict['K1']['FF']
                                      }
            # Seems like 2MK3 in Schureman is equivalent to MO3 in Foreman
            self.speed_dict["2MK3"] = {'speed': 42.927139836*deg2rad,
                                      'VAU': 3*self.T - 4*self.s + 3*self.h + 90 + 4*self.zeta - 4*self.mu - 4*self.mupp,
                                      'FF': self.speed_dict['M2']['FF']**2*self.speed_dict['K1']['FF']
                                      }
        if num_hours >= 662:
            self.speed_dict["2Q1"] = {'speed': 12.854286252*deg2rad,
                                      'VAU': self.T - 4*self.s + self.h + 2*self.p + 90 + 2*self.zeta - self.mu,
                                      'FF': self.speed_dict['O1']['FF']
                                      }
            self.speed_dict["Q1"] =  {'speed': 13.3986609*deg2rad,
                                      #'VAU': self.T - 3*self.s + self.h + self.p + 90 + 2*self.zeta - self.mu,
                                      'VAU': self.T - 3*self.s + self.h + self.p - 90 + 2*self.zeta - self.mu,
                       #       h + T - mu - 3*s - 2*self.zeta - 90 + p    ????
                                      # VAU(3) - eighteen
                                      # O1 - (one - two)
                                      # O1 - (s - p)
                                      # O1 - s + p
                                      # T - 2*s + h - 90 + 2*zeta - mu - s + p
                                      # T - 3*s + h - 90 + 2*zeta - mu + p
                                      'FF': self.speed_dict['O1']['FF']
                                      }
            self.speed_dict["J1"] =  {'speed': 15.5854433*deg2rad,
                                      'VAU': self.T + self.s + self.h - self.p - 90 - self.mu,
                                      'FF': N.sin(2.0*self.ii)/0.7214
                                      }
            self.speed_dict["N2"] =  {'speed': 28.439729568*deg2rad,
                                      'VAU': 2*self.T - 3*self.s + 2*self.h + self.p + 2*self.zeta - 2*self.mu,
                                      'FF': self.speed_dict['M2']['FF']
                                      }
            # Seems like KJ2 in Schureman is equivalent to ETA2 in Foreman
            self.speed_dict["KJ2"] = {'speed': 30.626511948*deg2rad,
                                      'VAU': 2*self.T + self.s + 2*self.h - self.p - 2*self.mu,
                                      'FF': N.sin(self.ii)**2/0.1565
                                      }
            # Seems like KQ1 in Schureman is equivalent to UPS1 in Foreman
            self.speed_dict["KQ1"] = {'speed': 16.683476328*deg2rad,
                                      'VAU': self.T + 3*self.s + self.h - self.p - 90 - 2*self.zeta - self.mu,
                                      'FF': N.sin(self.ii)**2/0.1565
                                      }
            # Seems like M1 in Schureman is equivalent to NO1 in Foreman
            self.speed_dict["M1"] =  {'speed': 14.496693984*deg2rad,
                                      'VAU': self.T - self.s + self.h + self.p - 90 - self.mu - self.Q,
                                      'FF': self.speed_dict['O1']['FF'] *(2.31+1.435*N.cos(2.0*self.kap_p))**0.5
                                      }
            self.speed_dict["MN4"] = {'speed': 57.423833820*deg2rad,
                                      'VAU': self.speed_dict['M2']['VAU'] + self.speed_dict['N2']['VAU'],
                                      'FF': self.speed_dict['M2']['FF']**2
                                      }
        if num_hours >= 764:
            self.speed_dict["Mm"] =  {'speed': 0.5443747*deg2rad,
                                      'VAU': self.s - self.p,
                                      'FF': ((2./3.) - N.sin(self.ii)**2)/0.5021
                                      }
            self.speed_dict["L2"] =  {'speed': 29.5284789*deg2rad,
                                      'VAU': 2*self.T - self.s + 2*self.h - self.p + 180 + 2*self.zeta - 2*self.mu - self.R,
                                      'FF': self.speed_dict['M2']['FF'] * (1.0 - 12.0*N.tan(0.5*self.ii)**2 * N.cos(2.0*self.kap_p) + 36.0*N.tan(0.5*self.ii)**4)**0.5
                                      }
            self.speed_dict["MU2"] = {'speed': 27.9682084*deg2rad,
                                      'VAU': 2*self.T - 4*self.s + 4*self.h + 2*self.zeta - 2*self.mu,
                                      'FF': self.speed_dict['M2']['FF']
                                      }
#            self.speed_dict["ALP1"] = 
            # Seems like MNS2 in Schureman is equivalent to EPS2 in Foreman
            self.speed_dict["MNS2"] = {'speed': 27.423833796*deg2rad,
                                      'VAU': 2*self.T - 5*self.s + 4*self.h + self.p + 4*self.zeta - 4*self.mu,
                                      'FF': self.speed_dict['M2']['FF']**2
                                      }
        if num_hours >= 4383:
            self.speed_dict["Ssa"] = {'speed': 0.0821373*deg2rad,
                                      'VAU': 2.0*self.h,
                                      'FF': N.ones(len(self.T))
                                      }
            self.speed_dict["Mf"] =  {'speed': 1.0980331*deg2rad,
                                      'VAU': 2.0*(self.s - self.zeta),
                                      'FF': N.sin(self.ii)**2 /0.1578
                                      }
            self.speed_dict["P1"] = {'speed': 14.9589314*deg2rad,
                                     'VAU': self.T - self.h + 90,
                                     'FF': N.ones(len(self.T))
                                     }
            self.speed_dict["K2"] = {'speed': 30.0821373*deg2rad,
                                     'VAU': 2*(self.T + self.h - self.two_mupp),
                                     'FF': (19.0444*(N.sin(self.ii)**4) + 2.7702*(N.sin(self.ii)**2) * N.cos(2.*self.mu*deg2rad) + 0.0981)**0.5
                                     }
            self.speed_dict["SO3"] = {'speed': 43.9430356*deg2rad,
                                      'VAU': 3*self.T - 2*self.s + self.h + 90 + 2*self.zeta - self.mu,
                                      'FF': self.speed_dict["O1"]["FF"]
                                      }
            self.speed_dict["PHI1"] = {'speed': 15.1232059*deg2rad,
                                       'VAU': self.T + 3*self.h - 90,
                                       'FF': N.ones(len(self.T))
                                       }
            self.speed_dict["SO1"] = {'speed': 16.0569644*deg2rad,
                                      'VAU': self.T + 2*self.s - self.h - 90 - self.mu,
                                      'FF': self.speed_dict['J1']['FF']
                                      }
            # Seems like A54 in Schureman is equivalent to MKS2 in Foreman
            self.speed_dict["A54"] = {'speed': 29.066241528*deg2rad,
                                      'VAU': 2*self.T - 2*self.s + 4*self.h - 2*self.mu,
                                      'FF': self.speed_dict['KJ2']['FF']
                                      }
            # Seems like MP1 in Schureman is equivalent to TAU1 in Foreman
            self.speed_dict["MP1"] = {'speed': 14.025172896*deg2rad,
                                      'VAU': self.T - 2*self.s + 3*self.h - 90 - self.mu,
                                      'FF': self.speed_dict['J1']['FF']
                                      }
            # Seems like A19 in Schureman is equivalent to BET1 in Foreman
            self.speed_dict["A19"] = {'speed': 14.414556708*deg2rad,
                                      'VAU': self.T - self.s - self.h + self.p - 90 - 2*self.zeta - self.mu,
                                      'FF': self.speed_dict['O1']['FF']
                                      }
            self.speed_dict["MK4"] = {'speed': 59.066241516*deg2rad,
                                      'VAU': self.speed_dict['M2']['VAU'] + self.speed_dict['K2']['VAU'],
                                      'FF': self.speed_dict['M2']['FF'] * self.speed_dict['K2']['FF']
                                      }
#            self.speed_dict["MSN2"] =
        if num_hours >= 4942:
            self.speed_dict["2N2"] = {'speed': 27.8953548*deg2rad,
                                      'VAU': 2*(self.T - 2*self.s + self.h + self.p + self.zeta - self.mu),
                                      'FF': self.speed_dict['M2']['FF']
                                      }
            self.speed_dict["NU2"] = {'speed': 28.5125831*deg2rad,
                                      'VAU': 2*self.T - 3*self.s + 4*self.h - self.p + 2*self.zeta - 2*self.mu,
                                      'FF': self.speed_dict['M2']['FF']
                                      }
            # Seems like A4 in Schureman is equivalent to MSM in Foreman
            self.speed_dict["A4"] = {'speed': 0.4715210880*deg2rad,
                                     'VAU': self.s - 2*self.h + self.p,
                                     'FF': self.speed_dict['Mm']['FF']
                                     }
            self.speed_dict["SIGMA1"] = {'speed': 12.9271398*deg2rad,
                                         'VAU': self.T - 4*self.s + 3*self.h + 90 + 2*self.zeta - self.mu,
                                         'FF': self.speed_dict['O1']['FF']
                                         }
            self.speed_dict["RHO1"] = {'speed': 13.4715145*deg2rad,
                                       'VAU': self.T - 3*self.s + 3*self.h - self.p + 90 + 2*self.zeta - self.mu,
                                       'FF': self.speed_dict['O1']['FF']
                                       }
            self.speed_dict["CHI1"] = {'speed': 14.5695476*deg2rad,
                                       'VAU': self.T - self.s + 3*self.h - self.p - 90 - self.mu,
                                       'FF': self.speed_dict['J1']['FF']
                                       }
            self.speed_dict["THETA1"] = {'speed': 15.5125897*deg2rad,
                                         'VAU': self.T + self.s - self.h + self.p - 90 - self.mu,
                                         'FF': self.speed_dict['J1']['FF']
                                         }
#            self.speed_dict["OQ2"] =
            self.speed_dict["LAMBDA2"] = {'speed': 29.4556253*deg2rad,
                                          'VAU': 2*self.T - self.s + self.p + 180,
                                          'FF': self.speed_dict['M2']['FF']
                                          }
        if num_hours >= 8766:
            self.speed_dict["Sa"] = {'speed': 0.0410686*deg2rad,
                                     'VAU': self.h,
                                     'FF': N.ones(len(self.T))
                                     }
        if num_hours >= 8767:
            self.speed_dict["S1"] = {'speed': 15.0000000*deg2rad,
                                     'VAU': self.T,
                                     'FF': N.ones(len(self.T))
                                     }
            self.speed_dict["T2"] = {'speed': 29.9589333*deg2rad,
                                     'VAU': 2*self.T - self.h + self.p1,
                                     'FF': N.ones(len(self.T))
                                     }
            self.speed_dict["R2"] = {'speed': 30.0410667*deg2rad,
                                     'VAU': 2*self.T + self.h - self.p1 + 180,
                                     'FF': N.ones(len(self.T))
                                     }
            self.speed_dict["PI1"] = {'speed': 14.9178647*deg2rad,
                                      'VAU': self.T - 2*self.h + self.p1 + 90,
                                      'FF': N.ones(len(self.T))
                                      }
            self.speed_dict["PSI1"] = {'speed': 15.0821352*deg2rad,
                                       'VAU': self.T + 2*self.h - self.p1 - 90,
                                       'FF': N.ones(len(self.T))
                                       }
#            self.speed_dict["H1"] =
#            self.speed_dict["H2"] =
        if num_hours >= 11326:
            # GAM2 from Foreman should go here, but couldn't find comparable
            # constituent from Schureman
            pass

        self.key_list = self.speed_dict.keys()
        self.key_list.sort()

        # Fix VAU to be between 0 and 360
        for key in self.key_list:
            self.speed_dict[key]['VAU'] = N.mod(self.speed_dict[key]['VAU'], 360)


    def astronomic(self):
        # Work from astrolabe and Jean Meeuss
        import astrolabe.calendar as cal
        import astrolabe.util as uti
        import astrolabe.elp2000 as elp
        import astrolabe.sun as sun

        lunar_eph = elp.ELP2000()
        solar_eph = sun.Sun()

        self.jd = N.zeros(len(self.dates), "d")
        self.s  = N.zeros(len(self.dates), "d")
        self.h  = N.zeros(len(self.dates), "d")
        self.N  = N.zeros(len(self.dates), "d")
        self.p  = N.zeros(len(self.dates), "d")
        self.p1 = N.zeros(len(self.dates), "d")
        for index,dt in enumerate(self.dates):
            # The -0.5 is needed because astronomers measure their zero from GMT noon,
            # whereas oceanographers measure the tide from zero at midnight.
            jd = (cal.cal_to_jd(dt.year, dt.month, dt.day) + uti.hms_to_fday(dt.hour, dt.minute, dt.second)) - 0.5
            self.jd[index] = jd
            self.s[index] = lunar_eph.dimension(jd, 'L') * rad2deg
            self.h[index] = solar_eph.dimension(jd, 'L') * rad2deg
            jdc = cal.jd_to_jcent(jd)
            self.p[index] = N.mod(83.3532465 + 4069.0137287*jdc - 0.0103200*jdc**2
                       - (jdc**3)/80053 + (jdc**4)/18999000, 360)
            self.N[index] = N.mod(125.0445479 - 1934.1362891*jdc + 0.0020754*jdc**2
                       + (jdc**3)/467441 - (jdc**4)/60616000, 360)
            self.p1[index] = N.mod((1012395 + 6189.03*(jdc + 1) + 1.63*(jdc + 1)**2 + 0.012*(jdc + 1)**3)/3600, 360)

        Nrad = self.N * deg2rad
        # Calculate constants for V+u
        # I, inclination of Moon's orbit, pg 156, Schureman
        i = N.arccos(0.9136949 - 0.0356926 * N.cos(Nrad))
        const_1=1.01883*N.tan(0.5*Nrad)
        const_2=0.64412*N.tan(0.5*Nrad)
        const_3=2.*N.arctan(const_1)-Nrad
        const_4=2.*N.arctan(const_2)-Nrad
        self.zeta=-0.5*(const_3+const_4)
        self.mu=0.5*(const_3-const_4)

        const_1=N.sin(2.0*i)*N.sin(self.mu)
        const_2=N.sin(2.0*i)*N.cos(self.mu)+0.3347
        self.mupp=N.arctan(const_1/const_2)
        const_1=N.sin(i)**2 * N.sin(2.0*self.mu)
        const_2=N.sin(i)**2 * N.cos(2.0*self.mu)+0.0727
        self.two_mupp=N.arctan(const_1/const_2)

        i=i*rad2deg
        self.zeta=self.zeta*rad2deg
        self.mu=self.mu*rad2deg
        self.mupp=self.mupp*rad2deg
        self.two_mupp=self.two_mupp*rad2deg
        hour=self.jd - self.jd.astype('i') 

        self.kap_p=(self.p-self.zeta)*deg2rad
        self.ii=i*deg2rad
        # pg 44, Schureman
        term1=N.sin(2.*self.kap_p)
        term2=(1./6.)*(1./N.tan(self.ii*0.5))**2
        term3=N.cos(2.*self.kap_p)
        self.R=N.arctan(term1/(term2-term3))*rad2deg
        self.Q=N.arctan(0.483*N.tan(self.kap_p))*rad2deg
        self.T=360.*hour


    def filter(self):
        """ Filters out periods of 25 hours and less from self.elevation and centers
        series at zero.

        """
        difference = self.dates[1:] - self.dates[:-1]
        if N.any(difference == datetime.timedelta(seconds=3600)):
            print "To use the --filter option you must use hourly values."
            sys.exit()
        kern = N.ones(25) * (1./25.)
        self.elevation = self.elevation - N.convolve(self.elevation, kern, mode=1)


    def missing(self, task):
        """ Fills missing values with the mean of the values. """

        if task not in ['fail', 'ignore', 'fill']:
            print "missing-data must be one of 'fail' (the default), 'ignore', or 'fill'"
            sys.exit()

        if task == 'ignore':
            return 1

        difference = self.dates[1:] - self.dates[:-1]

        if N.any(difference > datetime.timedelta(seconds=3600)):
            if task == 'fail':
                print "There is a difference of greater than one hour between values"
                sys.exit()
            if task == 'fill':
                # Very difficult - I hate place-holders, but here is one
                print "The 'missing-data=fill' function is not available yet."
                sys.exit()


    def remove_extreme_values(self):
        avg = N.average(self.elevation)
        std = N.std(self.elevation)

        good = self.elevation < (avg + 2.0*std)
        self.elevation = N.compress(good, self.elevation)
        self.dates = N.compress(good, self.dates)

        good = self.elevation > (avg - 2.0*std)
        self.elevation = N.compress(good, self.elevation)
        self.dates = N.compress(good, self.dates)


    def residuals(self, p, ht, t):
        """ Used for least squares fit.
    
        """
        H = {}
        phase = {}
        for index,key in enumerate(self.key_list):
            H[key] = p[index]
            phase[key] = p[index + len(self.key_list)]

        sumterm = N.zeros((len(t)))
        for i in self.key_list:
            sumterm = sumterm + H[i]*self.speed_dict[i]['FF']*N.cos(self.speed_dict[i]['speed']*t - phase[i])

        err = ht - (p[-1] + sumterm)
        return err

    #--------------------------

                                                
    def constituents(self):
        difference = self.dates[1:] - self.dates[:-1]
        if N.any(difference < datetime.timedelta(seconds=0)):
            print "Let's do the time warp again!"
            print "The date values reverse - they must be constantly increasing."
            sys.exit()

        p0 = [1.0]*(len(self.speed_dict)*2 + 1)
        ntimes = (self.jd - self.jd[0]) * 24 

        lsfit = leastsq(self.residuals, p0, args=(self.elevation, ntimes))

        a = {}
        b = {}
        for index,key in enumerate(self.key_list):
            a[key] = lsfit[0][index]
            b[key] = lsfit[0][index + len(self.key_list)]

        self.r = {}
        self.phase = {}
        for i in self.key_list:

            self.r[i] = a[i]
            self.phase[i] = b[i]*rad2deg
            if self.r[i] < 0:
                self.r[i] = abs(self.r[i])
                self.phase[i] = self.phase[i] - 180
            self.phase[i] = N.mod(self.phase[i] + self.speed_dict[i]['VAU'][0], 360)


    def write_components(self):
        total = N.zeros(len(self.dates))
        for i in self.key_list:
            fpo = open("outts_%s.dat" % (i, ), "w")
            for index,d in enumerate(self.dates):
                component = self.r[i] * math.cos(index*self.speed_dict[i]['speed'] - self.phase[i]*deg2rad)
                total[index] = total[index] + component
                fpo.write("%s %f\n" % (d.isoformat(), component))
            fpo.close()
        fpo = open("outts_total.dat", "w")
        for d,v in zip(self.dates, total):
            fpo.write("%s %f\n" % (d.isoformat(), v))

    def print_con(self):
        for i in self.key_list:
            print i, self.r[i], self.phase[i]

    def print_ephemeris_table(self):
        for index,d in enumerate(self.dates):
            print d.isoformat(), self.s[index], self.p[index], self.h[index], self.p1[index], self.N[index]

    def print_v_u_table(self):
        pass

    def print_node_factor_table(self):
        pass

#=============================
def main(option_dict):
    if len(sys.argv) == 2:
        def_filename = None
    elif len(sys.argv) == 3:
        def_filename = sys.argv[2]
    else:
        fatal('main', 'Need to pass input file name and optional defition file name')

    x=tappy(sys.argv[1], def_filename=def_filename)

    if option_dict['ephemeris_table']:
        x.print_ephemeris_table()
        sys.exit()

    if option_dict['filter_p']:
        x.filter()

    if option_dict['remove_extreme']:
        x.remove_extreme_values()

    if option_dict['missing_data']:
        x.missing(option_dict['missing_data'])

    x.astronomic()

    x.which_constituents()

    x.constituents()

    if not option_dict['quiet']:
        x.print_con()

    if option_dict['output_p']:
        x.write_components()
    
#-------------------------
if __name__ == '__main__':
    ftn = "main"
    option_dict = {
                   'debug_p':0,
                   'filter_p':0,
                   'output_p':0,
                   'quiet':0,
                   'ephemeris_table':0,
                   'missing_data':'fail',
                   'remove_extreme':0,
                   }
    opts,pargs=getopt.getopt(sys.argv[1:],'hvdfoqem=r',
                 [
                 'help',
                 'version',
                 'debug',
                 'filter',
                 'output',
                 'quiet',
                 'ephemeris',
                 'missing-data=',
                 'remove-extreme',
                 ])
    for opt in opts:
        if opt[0]=='-h' or opt[0]=='--help':
            print modname+": version="+__version__
            usage()
            sys.exit(0)
        elif opt[0]=='-v' or opt[0]=='--version':
            print modname+": version="+__version__
            sys.exit(0)
        elif opt[0]=='-d' or opt[0]=='--debug':
            option_dict['debug_p'] = 1
            sys.argv.remove(opt[0])
        elif opt[0]=='-f' or opt[0]=='--filter':
            option_dict['filter_p'] = 1
            sys.argv.remove(opt[0])
        elif opt[0]=='-o' or opt[0]=='--output':
            option_dict['output_p'] = 1
            sys.argv.remove(opt[0])
        elif opt[0]=='-q' or opt[0]=='--quiet':
            option_dict['quiet_p'] = 1
            sys.argv.remove(opt[0])
        elif opt[0]=='-e' or opt[0]=='--ephemeris':
            option_dict['ephemeris_table'] = 1
            sys.argv.remove(opt[0])
        elif opt[0]=='-m' or opt[0]=='--missing-data':
            option_dict['missing_data'] = opt[1]
            sys.argv.remove(opt[0])
            sys.argv.remove(opt[1])
        elif opt[0]=='-r' or opt[0]=='--remove-extreme':
            option_dict['remove_extreme'] = 1
            sys.argv.remove(opt[0])

    #---make the object and run it---
    main(option_dict)

#===Revision Log===
#Created by mkpythonproj:
#2005-06-13  Tim Cera  
#
