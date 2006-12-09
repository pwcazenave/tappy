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
import astrolabe.calendar as cal
import astrolabe.util as uti

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
    for index,val in enumerate(mask):
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


    def which_constituents(self, length, package):
        (zeta, mu, mupp, two_mupp, kap_p, ii, R, Q, T, jd, s, h, Nv, p, p1) = package
        speed_dict = {}

        # Set data into speed_dict depending on length of time series
        # Required length of time series depends on Raleigh criteria to 
        # differentiate beteen constituents of simmilar speed.
        #  Key is tidal constituent name from Schureman
        #    speed is how fast the constiuent moves in radians/hour
        #    VAU is V+u taken from Schureman
        #    FF is the node factor from Schureman

        num_hours = (jd[-1] - jd[0]) * 24
        if num_hours < 13:
            print "Cannot calculate any constituents from this record length"
            sys.exit()
        speed_dict["M2"] = {'speed': 28.984104252*deg2rad,
                                 'VAU': 2*(T - s + h + zeta - mu),
                                 'FF': N.cos(0.5*ii)**4 /0.9154  # eq 78
                                 }
        if num_hours >= 24:
            speed_dict["K1"] = {'speed': 15.041068632*deg2rad,
                                     'VAU': T + h + 90 - mupp,
                                     'FF': (0.8965*(N.sin(2.*ii)**2) + 0.6001*N.sin(2.*ii)*N.cos(mu*deg2rad) + 0.1006)**0.5  # eq 227
                                     }
        if num_hours >= 25:
            speed_dict["M3"] = {'speed': 43.476156360*deg2rad,
                                     'VAU': 3*T - 3*s + 3*h + 3*zeta - 3*mu,
                                     'FF': N.cos(0.5*ii)**6 /0.8758  # eq 149
                                     }
            speed_dict["M4"] = {'speed': 57.968208468*deg2rad,
                                     'VAU': 2.*speed_dict['M2']['VAU'],
                                     'FF': speed_dict['M2']['FF']**2
                                     }
        if num_hours >= 26:
            speed_dict["M6"] = {'speed': 86.952312720*deg2rad,
                                     'VAU': 3.*speed_dict['M2']['VAU'],
                                     'FF': speed_dict['M2']['FF']**2
                                     }
        if num_hours >= 328:
            speed_dict["O1"] = {'speed': 13.943035584*deg2rad,
                                     'VAU': T - 2*s + h - 90 + 2*zeta - mu,
                                     'FF': N.sin(ii)*N.cos(0.5*ii)**2 /0.3800
                                     }
                                     # thirty_one - thirty
                                     # (sixteen - eight) - (twenty_nine + 90)
                                     # sixteen - eight - twenty_nine - 90
                                     # (three + fifteen) - (mu) - (2*twenty_eight) - 90
                                     # h + T - mu - 2*(one - nine) - 90
                                     # h + T - mu - 2*s + 2*zeta - 90
                                     # T - 2*s + h - 90 + 2*zeta - mu
        if num_hours >= 355:
            speed_dict["MSf"] = {'speed': 1.0158957720*deg2rad,
                                      'VAU': 2.0*(s - h),
                                      'FF': ((2./3.) - N.sin(ii)**2)/0.5021
                                      }
            speed_dict["S2"] = {'speed': 30.0000000 * deg2rad,
                                     'VAU': 2*T,
                                     'FF': N.ones(length)
                                     }
            speed_dict["SK3"] = {'speed': 45.041068656 * deg2rad,
                                      'VAU': 3*T + h - 90 - mupp,
                                      'FF': speed_dict['K1']['FF']
                                      }
            speed_dict["2SM2"] = {'speed': 31.015884960*deg2rad,
                                      'VAU': 2*T + 2*s - 2*h - 2*zeta + 2*mu,
                                      'FF': speed_dict['M2']['FF']
                                      }
            speed_dict["MS4"] = {'speed': 58.984104240*deg2rad,
                                      'VAU': speed_dict['M2']['VAU'] + speed_dict['S2']['VAU'],
                                      'FF': speed_dict['M2']['FF']
                                      }
            speed_dict["S4"] = {'speed': 60.0*deg2rad,
                                      'VAU': 4*T,
                                      'FF': N.ones(length)
                                      }
        if num_hours >= 651:
            speed_dict["OO1"] = {'speed': 16.139101680*deg2rad,
                                      'VAU': T + 2*s + h - 90 - 2*zeta - mu,
                                      'FF': (N.sin(ii)*N.sin(0.5*ii)**2)/0.0164
                                      }
        if num_hours >= 656:
            speed_dict["MK3"] = {'speed': 44.025172884*deg2rad,
                                      'VAU': speed_dict['M2']['VAU']+speed_dict['K1']['VAU'],
                                      'FF': speed_dict['M2']['FF']*speed_dict['K1']['FF']
                                      }
            # Seems like 2MK3 in Schureman is equivalent to MO3 in Foreman
            speed_dict["2MK3"] = {'speed': 42.927139836*deg2rad,
                                      'VAU': 3*T - 4*s + 3*h + 90 + 4*zeta - 4*mu - 4*mupp,
                                      'FF': speed_dict['M2']['FF']**2*speed_dict['K1']['FF']
                                      }
        if num_hours >= 662:
            speed_dict["2Q1"] = {'speed': 12.854286252*deg2rad,
                                      'VAU': T - 4*s + h + 2*p + 90 + 2*zeta - mu,
                                      'FF': speed_dict['O1']['FF']
                                      }
            speed_dict["Q1"] =  {'speed': 13.3986609*deg2rad,
                                      #'VAU': T - 3*s + h + p + 90 + 2*zeta - mu,
                                      'VAU': T - 3*s + h + p - 90 + 2*zeta - mu,
                       #       h + T - mu - 3*s - 2*zeta - 90 + p    ????
                                      # VAU(3) - eighteen
                                      # O1 - (one - two)
                                      # O1 - (s - p)
                                      # O1 - s + p
                                      # T - 2*s + h - 90 + 2*zeta - mu - s + p
                                      # T - 3*s + h - 90 + 2*zeta - mu + p
                                      'FF': speed_dict['O1']['FF']
                                      }
            speed_dict["J1"] =  {'speed': 15.5854433*deg2rad,
                                      'VAU': T + s + h - p - 90 - mu,
                                      'FF': N.sin(2.0*ii)/0.7214
                                      }
            speed_dict["N2"] =  {'speed': 28.439729568*deg2rad,
                                      'VAU': 2*T - 3*s + 2*h + p + 2*zeta - 2*mu,
                                      'FF': speed_dict['M2']['FF']
                                      }
            # Seems like KJ2 in Schureman is equivalent to ETA2 in Foreman
            speed_dict["KJ2"] = {'speed': 30.626511948*deg2rad,
                                      'VAU': 2*T + s + 2*h - p - 2*mu,
                                      'FF': N.sin(ii)**2/0.1565
                                      }
            # Seems like KQ1 in Schureman is equivalent to UPS1 in Foreman
            speed_dict["KQ1"] = {'speed': 16.683476328*deg2rad,
                                      'VAU': T + 3*s + h - p - 90 - 2*zeta - mu,
                                      'FF': N.sin(ii)**2/0.1565
                                      }
            # Seems like M1 in Schureman is equivalent to NO1 in Foreman
            speed_dict["M1"] =  {'speed': 14.496693984*deg2rad,
                                      'VAU': T - s + h + p - 90 - mu - Q,
                                      'FF': speed_dict['O1']['FF'] *(2.31+1.435*N.cos(2.0*kap_p))**0.5
                                      }
            speed_dict["MN4"] = {'speed': 57.423833820*deg2rad,
                                      'VAU': speed_dict['M2']['VAU'] + speed_dict['N2']['VAU'],
                                      'FF': speed_dict['M2']['FF']**2
                                      }
        if num_hours >= 764:
            speed_dict["Mm"] =  {'speed': 0.5443747*deg2rad,
                                      'VAU': s - p,
                                      'FF': ((2./3.) - N.sin(ii)**2)/0.5021
                                      }
            speed_dict["L2"] =  {'speed': 29.5284789*deg2rad,
                                      'VAU': 2*T - s + 2*h - p + 180 + 2*zeta - 2*mu - R,
                                      'FF': speed_dict['M2']['FF'] * (1.0 - 12.0*N.tan(0.5*ii)**2 * N.cos(2.0*kap_p) + 36.0*N.tan(0.5*ii)**4)**0.5
                                      }
            speed_dict["MU2"] = {'speed': 27.9682084*deg2rad,
                                      'VAU': 2*T - 4*s + 4*h + 2*zeta - 2*mu,
                                      'FF': speed_dict['M2']['FF']
                                      }
#            speed_dict["ALP1"] = 
            # Seems like MNS2 in Schureman is equivalent to EPS2 in Foreman
            speed_dict["MNS2"] = {'speed': 27.423833796*deg2rad,
                                      'VAU': 2*T - 5*s + 4*h + p + 4*zeta - 4*mu,
                                      'FF': speed_dict['M2']['FF']**2
                                      }
        if num_hours >= 4383:
            speed_dict["Ssa"] = {'speed': 0.0821373*deg2rad,
                                      'VAU': 2.0*h,
                                      'FF': N.ones(length)
                                      }
            speed_dict["Mf"] =  {'speed': 1.0980331*deg2rad,
                                      'VAU': 2.0*(s - zeta),
                                      'FF': N.sin(ii)**2 /0.1578
                                      }
            speed_dict["P1"] = {'speed': 14.9589314*deg2rad,
                                     'VAU': T - h + 90,
                                     'FF': N.ones(length)
                                     }
            speed_dict["K2"] = {'speed': 30.0821373*deg2rad,
                                     'VAU': 2*(T + h - two_mupp),
                                     'FF': (19.0444*(N.sin(ii)**4) + 2.7702*(N.sin(ii)**2) * N.cos(2.*mu*deg2rad) + 0.0981)**0.5
                                     }
            speed_dict["SO3"] = {'speed': 43.9430356*deg2rad,
                                      'VAU': 3*T - 2*s + h + 90 + 2*zeta - mu,
                                      'FF': speed_dict["O1"]["FF"]
                                      }
            speed_dict["PHI1"] = {'speed': 15.1232059*deg2rad,
                                       'VAU': T + 3*h - 90,
                                       'FF': N.ones(length)
                                       }
            speed_dict["SO1"] = {'speed': 16.0569644*deg2rad,
                                      'VAU': T + 2*s - h - 90 - mu,
                                      'FF': speed_dict['J1']['FF']
                                      }
            # Seems like A54 in Schureman is equivalent to MKS2 in Foreman
            speed_dict["A54"] = {'speed': 29.066241528*deg2rad,
                                      'VAU': 2*T - 2*s + 4*h - 2*mu,
                                      'FF': speed_dict['KJ2']['FF']
                                      }
            # Seems like MP1 in Schureman is equivalent to TAU1 in Foreman
            speed_dict["MP1"] = {'speed': 14.025172896*deg2rad,
                                      'VAU': T - 2*s + 3*h - 90 - mu,
                                      'FF': speed_dict['J1']['FF']
                                      }
            # Seems like A19 in Schureman is equivalent to BET1 in Foreman
            speed_dict["A19"] = {'speed': 14.414556708*deg2rad,
                                      'VAU': T - s - h + p - 90 - 2*zeta - mu,
                                      'FF': speed_dict['O1']['FF']
                                      }
            speed_dict["MK4"] = {'speed': 59.066241516*deg2rad,
                                      'VAU': speed_dict['M2']['VAU'] + speed_dict['K2']['VAU'],
                                      'FF': speed_dict['M2']['FF'] * speed_dict['K2']['FF']
                                      }
            # Mentioned, but no speed available...
            # speed_dict["MSN2"] =
        if num_hours >= 4942:
            speed_dict["2N2"] = {'speed': 27.8953548*deg2rad,
                                      'VAU': 2*(T - 2*s + h + p + zeta - mu),
                                      'FF': speed_dict['M2']['FF']
                                      }
            speed_dict["NU2"] = {'speed': 28.5125831*deg2rad,
                                      'VAU': 2*T - 3*s + 4*h - p + 2*zeta - 2*mu,
                                      'FF': speed_dict['M2']['FF']
                                      }
            # Seems like A4 in Schureman is equivalent to MSM in Foreman
            speed_dict["A4"] = {'speed': 0.4715210880*deg2rad,
                                     'VAU': s - 2*h + p,
                                     'FF': speed_dict['Mm']['FF']
                                     }
            speed_dict["SIGMA1"] = {'speed': 12.9271398*deg2rad,
                                         'VAU': T - 4*s + 3*h + 90 + 2*zeta - mu,
                                         'FF': speed_dict['O1']['FF']
                                         }
            speed_dict["RHO1"] = {'speed': 13.4715145*deg2rad,
                                       'VAU': T - 3*s + 3*h - p + 90 + 2*zeta - mu,
                                       'FF': speed_dict['O1']['FF']
                                       }
            speed_dict["CHI1"] = {'speed': 14.5695476*deg2rad,
                                       'VAU': T - s + 3*h - p - 90 - mu,
                                       'FF': speed_dict['J1']['FF']
                                       }
            speed_dict["THETA1"] = {'speed': 15.5125897*deg2rad,
                                         'VAU': T + s - h + p - 90 - mu,
                                         'FF': speed_dict['J1']['FF']
                                         }
#            speed_dict["OQ2"] =
            speed_dict["LAMBDA2"] = {'speed': 29.4556253*deg2rad,
                                          'VAU': 2*T - s + p + 180,
                                          'FF': speed_dict['M2']['FF']
                                          }
        if num_hours >= 8766:
            speed_dict["Sa"] = {'speed': 0.0410686*deg2rad,
                                     'VAU': h,
                                     'FF': N.ones(length)
                                     }
        if num_hours >= 8767:
            speed_dict["S1"] = {'speed': 15.0000000*deg2rad,
                                     'VAU': T,
                                     'FF': N.ones(length)
                                     }
            speed_dict["T2"] = {'speed': 29.9589333*deg2rad,
                                     'VAU': 2*T - h + p1,
                                     'FF': N.ones(length)
                                     }
            speed_dict["R2"] = {'speed': 30.0410667*deg2rad,
                                     'VAU': 2*T + h - p1 + 180,
                                     'FF': N.ones(length)
                                     }
            speed_dict["PI1"] = {'speed': 14.9178647*deg2rad,
                                      'VAU': T - 2*h + p1 + 90,
                                      'FF': N.ones(length)
                                      }
            speed_dict["PSI1"] = {'speed': 15.0821352*deg2rad,
                                       'VAU': T + 2*h - p1 - 90,
                                       'FF': N.ones(length)
                                       }
#            speed_dict["H1"] =
#            speed_dict["H2"] =
        if num_hours >= 11326:
            # GAM2 from Foreman should go here, but couldn't find comparable
            # constituent information from Schureman
            pass

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
            for index,dt in enumerate(dates):
                # The -0.5 is needed because astronomers measure their zero from GMT noon,
                # whereas oceanographers measure the tide from zero at midnight.
                jd[index] = (cal.cal_to_jd(dt.year, dt.month, dt.day) + uti.hms_to_fday(dt.hour, dt.minute, dt.second)) - 0.5
        else:
            jd = dates
        return jd


    def astronomic(self, dates):
        # Work from astrolabe and Jean Meeuss
        import astrolabe.elp2000 as elp
        import astrolabe.sun as sun

        lunar_eph = elp.ELP2000()
        solar_eph = sun.Sun()

        s  = N.zeros(len(dates), "d")
        h  = N.zeros(len(dates), "d")
        Nv = N.zeros(len(dates), "d")
        p  = N.zeros(len(dates), "d")
        p1 = N.zeros(len(dates), "d")
        jd = self.dates2jd(dates)
        for index,dt in enumerate(dates):
            jdc = cal.jd_to_jcent(jd[index])
            Nv[index] = N.mod(125.0445479 - 1934.1362891*jdc + 0.0020754*jdc**2
                       + (jdc**3)/467441 - (jdc**4)/60616000, 360)
            p1[index] = N.mod((1012395 + 6189.03*(jdc + 1) + 1.63*(jdc + 1)**2 + 0.012*(jdc + 1)**3)/3600, 360)
        jdc = cal.jd_to_jcent(jd[0])
        p = N.mod(83.3532465 + 4069.0137287*jdc - 0.0103200*jdc**2
                   - (jdc**3)/80053 + (jdc**4)/18999000, 360)

        s = lunar_eph.dimension(jd[0], 'L') * rad2deg
        h = solar_eph.dimension(jd[0], 'L') * rad2deg

        Nrad = Nv * deg2rad
        # Calculate constants for V+u
        # I, inclination of Moon's orbit, pg 156, Schureman
        i = N.arccos(0.9136949 - 0.0356926 * N.cos(Nrad))
        const_1=1.01883*N.tan(0.5*Nrad)
        const_2=0.64412*N.tan(0.5*Nrad)
        const_3=2.*N.arctan(const_1)-Nrad
        const_4=2.*N.arctan(const_2)-Nrad
        zeta=-0.5*(const_3+const_4)
        mu=0.5*(const_3-const_4)

        const_1=N.sin(2.0*i)*N.sin(mu)
        const_2=N.sin(2.0*i)*N.cos(mu)+0.3347
        mupp=N.arctan(const_1/const_2)
        const_1=N.sin(i)**2 * N.sin(2.0*mu)
        const_2=N.sin(i)**2 * N.cos(2.0*mu)+0.0727
        two_mupp=N.arctan(const_1/const_2)

        i=i*rad2deg
        zeta=zeta*rad2deg
        mu=mu*rad2deg
        mupp=mupp*rad2deg
        two_mupp=two_mupp*rad2deg
        #hour=jd - jd.astype('i') 
        hour=jd[0] - int(jd[0])

        kap_p=(p-zeta)*deg2rad
        ii=i*deg2rad
        # pg 44, Schureman
        term1=N.sin(2.*kap_p)
        term2=(1./6.)*(1./N.tan(ii*0.5))**2
        term3=N.cos(2.*kap_p)
        R=N.arctan(term1/(term2-term3))*rad2deg
        Q=N.arctan(0.483*N.tan(kap_p))*rad2deg
        T=360.*hour

        # This should be stream lined... needed to support 
        # the larger sized vector when filling missing values.
        return (zeta, mu, mupp, two_mupp, kap_p, ii, R, Q, T, jd, s, h, Nv, p, p1)


    def usgs_filter(self, dates, elev):
        """ Filters out periods of 25 hours and less from self.elevation.

        """

        (dates,elev) = self.missing('fill', dates, elev)

        kern = [  
              -0.00027,-0.00114,-0.00211,-0.00317,-0.00427,
              -0.00537,-0.00641,-0.00735,-0.00811,-0.00864,
              -0.00887,-0.00872,-0.00816,-0.00714,-0.00560,
              -0.00355,-0.00097, 0.00213, 0.00574, 0.00980,
               0.01425, 0.01902, 0.02400, 0.02911, 0.03423,
               0.03923, 0.04399, 0.04842, 0.05237, 0.05576,
               0.05850, 0.06051, 0.06174, 0.06215, ]

        kern = N.concatenate((kern[:-1],kern[::-1]))

        usgs_filtered = N.convolve(elev, kern, mode=1)

        return usgs_filtered


    def missing(self, task, dates, elev):
        """ What to do with the missing values """

        if task not in ['fail', 'ignore', 'fill']:
            print "missing-data must be one of 'fail' (the default), 'ignore', or 'fill'"
            sys.exit()

        if task == 'ignore':
            return (dates, elev)

        interval = dates[1:] - dates[:-1]

        if N.any(interval > datetime.timedelta(seconds=3600)):
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
    
            # Had to make this 'f8' in order to match 'total' and 'self.elevation'
            # Don't know why this was different.
            residuals = N.ones(len(dates_filled), dtype='f8') * -99999.0
    
            package = self.astronomic(dates_filled)
            (speed_dict, key_list) = self.which_constituents(len(dates_filled), package)
            (zeta, mu, mupp, two_mupp, kap_p, ii, R, Q, T, jd_filled, s, h, Nv, p, p1) = package
    
            ntimes_filled = (jd_filled - jd_filled[0])*24
            total = self.sum_signals(self.key_list, ntimes_filled, speed_dict)
    
            for dt in dates:
                where_good[dates_filled == dt] = True
    
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
        for index,key in enumerate(key_list):
            H[key] = p[index]
            phase[key] = p[index + len(key_list)]

        if len(self.speed_dict[key_list[0]]['FF']) == len(t):
            ff = self.speed_dict
        else:
            ff = {}
            for key in key_list:
                ff[key] = {'FF': N.ones(len(t))}

        sumterm = N.zeros((len(t)))
        for i in key_list:
            sumterm = sumterm + H[i]*ff[i]['FF']*N.cos(self.speed_dict[i]['speed']*t - phase[i])

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
        if N.any(difference < datetime.timedelta(seconds=0)):
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
        for index,key in enumerate(self.key_list):
            self.r[key] = lsfit[0][index]
            self.phase[key] = lsfit[0][index + len(self.key_list)]*rad2deg

            if self.r[key] < 0:
                self.r[key] = abs(self.r[key])
                self.phase[key] = self.phase[key] - 180
            self.phase[key] = N.mod(self.phase[key] + self.speed_dict[key]['VAU'], 360)
        self.fitted_average = p0[-1]
        self.slope = p0[-2]


    def sum_signals(self, skey_list, hours, speed_dict, amp=None, phase=None):
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


    def filters(self, nstype, dates, elevation):

        if nstype == 'usgs':
            return self.usgs_filter(dates, elevation)

        if nstype == 'boxcar':
            kern = N.ones(25) * (1./25.)
            return N.convolve(elevation, kern, mode=1)

        if nstype == 'mstha':
            blen = 24
            blen = 12
            s_list = ['M2','K1','M3','M4']

            p0 = [1.0]*(len(s_list)*2 + 2)
            p0[-2] = 0.0
            ndates = N.concatenate(([dates[0] - datetime.timedelta(hours=blen/2)],
                                    dates,
                                    [dates[-1] + datetime.timedelta(hours=blen/2)]))
            nelevation = N.concatenate(([elevation[0]],
                                        elevation,
                                        [elevation[-1]]))
            (new_dates, new_elev) = self.missing('fill', ndates, nelevation)
            slope = []
            new_dates = self.dates2jd(new_dates)
            ntimes = N.arange(2*blen + 1)
            for d in range(len(new_dates))[blen:-blen]:
          #      ntimes = (new_dates[d-12:d+12] - new_dates[d]) * 24 
                nelev = new_elev[d-blen:d+blen+1]
                lsfit = leastsq(self.residuals, p0, args=(nelev, ntimes, s_list))
                slope.append(lsfit[0][-2])
    
            return slope

        if nstype == 'wavelet':
            import pywt
            import pylab

            for wl in pywt.wavelist():

                w = pywt.Wavelet(wl)

                max_level = pywt.dwt_max_level(len(elevation), w.dec_len)
                print elevation
                print w
                print max_level
                a = pywt.wavedec(elevation, w, level=max_level, mode='sym')

                for i in range(len(a))[1:]:
                    avg = N.average(a[i][:])
                    std = 2.0*N.std(a[i][:])
                    a[i][(a[i][:] < (avg + std)) & (a[i][:] > (avg - std))] = 0.0
    
                for index,items in enumerate(a):
                    self.write_file("outts_wavelet_%s_%i.dat" % (wl, index), dates, items)
    
                y = pywt.waverec(a, w, mode='sym')
                self.write_file("%s.dat" % wl, dates, y)
    
            return y

        if nstype == 'cd':
    
            (new_dates, new_elev) = self.missing('fill', dates, elevation)
            package = self.astronomic(new_dates)
            (zeta, mu, mupp, two_mupp, kap_p, ii, R, Q, T, jd_filled, s, h, Nv, p, p1) = package
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
                ns_amplitude[key] = N.convolve(ns_amplitude[key], kern, mode=1)

                ns_phase[key] = N.arctan2(yt.imag, yt.real) * rad2deg
                ns_phase[key] = N.convolve(ns_phase[key], kern, mode=1)

                new_list = [i for i in self.key_list if i != key]
                everything_but = self.sum_signals(new_list, ntimes_filled, speed_dict)
                constituent_residual[key] = new_elev - everything_but
            return ns_amplitude


    def write_file(self, fname, x, y):
        if isinstance(y, dict):
            print y.keys()
            for key in y.keys():
                nfname = "%s_%s.dat" % (os.path.splitext(fname)[-2], key)
                self.write_file(nfname, x, y[key])
        else:
            fpo = open(fname, "w")
            for d,v in zip(x, y):
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
def main(options, args):

    if len(args) == 1:
        def_filename = None
    elif len(args) == 2:
        def_filename = args[1]
    else:
        fatal('main', 'Need to pass input file name and optional definition file name')

    x=tappy(args[0], def_filename=def_filename)

    x.options = options

    if x.options.ephemeris:
        x.print_ephemeris_table()

    if x.options.zero_ts:
        x.elevation = x.elevation - x.filters(item, x.dates, x.elevation)

    if x.options.missing_data == 'fail':
        x.dates_filled,x.elevation_filled = x.missing(x.options.missing_data, x.dates, x.elevation)

    if x.options.remove_extreme:
        x.remove_extreme_values()

    package = x.astronomic(x.dates)
    (x.zeta, x.mu, x.mupp, x.two_mupp, x.kap_p, x.ii, x.R, x.Q, x.T, x.jd, x.s, x.h, x.N, x.p, x.p1) = package

    (x.speed_dict, x.key_list) = x.which_constituents(len(x.dates), package)

    x.constituents()

    if x.options.missing_data == 'fill':
        x.dates_filled,x.elevation_filled = x.missing(x.options.missing_data, x.dates, x.elevation)
        x.write_file('outts_filled.dat', x.dates_filled, x.elevation_filled)

    if x.options.filter:
        if x.options.missing_data != 'fill':
            x.dates_filled,x.elevation_filled = x.missing(x.options.missing_data, x.dates, x.elevation)
        for item in x.options.filter.split(','):
            if item in ['mstha', 'wavelet', 'cd', 'boxcar', 'usgs',]:# 'lecolazet', 'godin', 'sfa']:
                result = x.filters(item, x.dates_filled, x.elevation_filled)
                x.write_file('outts_filtered_%s.dat' % (item,), x.dates_filled, result)

    if not x.options.quiet:
        x.print_con()

    if x.options.output:
        for key in x.key_list:
            x.write_file("outts_%s.dat" % (key,), x.dates, x.sum_signals([key], x.dates, x.speed_dict))
        x.write_file("outts_total_prediction.dat", x.dates, x.sum_signals(x.key_list, x.dates, x.speed_dict))
        x.write_file("outts_original.dat", x.dates, x.elevation)

#-------------------------
if __name__ == '__main__':
    ftn = "main"

    from optparse import OptionParser

    parser = OptionParser(usage='%prog [options] input_file [optional_definition_file]', version=__version__)
    parser.add_option(
                   '-q', 
                   '--quiet', 
                   help='Print nothing to the screen.', 
                   action='store_true',
                   default=False,
                     )
    parser.add_option(
                   '-d',
                   '--debug',
                   help='Print debug messages.',
                   action='store_true',
                   default=False,
                     )
    parser.add_option(
                   '-o',
                   '--output',
                   help='Write output time-series.',
                   action='store_true',
                   default=False,
                     )
    parser.add_option(
                   '-e',
                   '--ephemeris',
                   help='Print out ephemeris tables.',
                   action='store_true',
                   default=False,
                     )
    parser.add_option(
                   '-m',
                   '--missing-data',
                   help='What should be done if there is missing data.  One of: fail, ignore, or fill. [default: %default]',
                   default='ignore',
                     )
    parser.add_option(
                   '-l',
                   '--linear-trend',
                   help='Include a linear trend in the least squares fit.',
                   action='store_true',
                     )
    parser.add_option(
                   '-r',
                   '--remove-extreme',
                   help='Remove values outside of 2 standard deviations before analysis.',
                   action='store_true',
                     )
    parser.add_option(
                   '-z',
                   '--zero-ts',
                   help='Zero the input time series before constituent analysis by subtracting filtered data. One of: boxcar,usgs,mstha,cd.',#lecolazet,godin,sfa
                   metavar='FILTER',
                     )
    parser.add_option(
                   '-f',
                   '--filter',
                   help='Filter input data set with tide elimination filters. The -o output option is implied. Any mix separated by commas and no spaces: boxcar,usgs,mstha,wavelet,cd.',#,lecolazet,godin,sfa
                   metavar='FILTER',
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
