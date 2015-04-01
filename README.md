TAPPY
-----

TAPPY is a tidal analysis package. It breaks down an hourly record of water
levels into the component sine waves. It is written in Python and uses the
least squares optimization and other functions in SciPy. The focus is to make
the most accurate analysis possible. TAPPY only determines the constituents
that are calculatable according to the length of the time series.

Authors
-------

* Tim Cera (tim at cerazone.net)
* Pierre Cazenave (Plymouth Marine Laboratory)

Source
------

This repository is an import of the CVS repository found on the official site:

https://sourceforge.net/p/tappy/wiki/Main_Page

http://sourceforge.net/projects/tappy

I (Pierre Cazenave) have made minor changes to the code to allow TAPPY to be used as a module in scripts.

Examples
--------

The official SourceForge site contains an extensive wiki which covers the usage of TAPPY. Given the change I made to allow the code to be imported as a module, an example of its use in that manner is useful.

```python

import tappy

if __name__ == '__main__':

    # Load a time series to analyse
    dates = ... # a datetime.datetime list of dates
    elevation = ... # a list of surface elevation values

    # Set up the bits needed for TAPPY. This is mostly lifted from
    # tappy.py in the baker function "analysis" (around line 1721).
    quiet = True
    debug = False
    outputts = False
    outputxml = False
    ephemeris = False
    rayleigh = 1.0
    print_vau_table = False
    missing_data = 'ignore'
    linear_trend = False
    remove_extreme = False
    zero_ts = None
    filter = None
    pad_filters = None
    include_inferred = True

    if rayleigh:
        ray = float(rayleigh)

    x = tappy.tappy(
        outputts = outputts,
        outputxml = outputxml,
        quiet=quiet,
        debug=debug,
        ephemeris=ephemeris,
        rayleigh=rayleigh,
        print_vau_table=print_vau_table,
        missing_data=missing_data,
        linear_trend=linear_trend,
        remove_extreme=remove_extreme,
        zero_ts=zero_ts,
        filter=filter,
        pad_filters=pad_filters,
        include_inferred=include_inferred,
        )

    x.dates = dates
    x.elevation = elevation[:, p].tolist()
    package = x.astronomic(x.dates)
    (x.zeta, x.nu, x.nup, x.nupp, x.kap_p, x.ii, x.R, x.Q, x.T, x.jd, x.s, x.h, x.N, x.p, x.p1) = package
    (x.speed_dict, x.key_list) = x.which_constituents(len(x.dates),
            package, rayleigh_comp=ray)

    x.constituents() # the analysis

    # Print the M2 amplitude and phase.
    print('M2 amplitude: {}'.format(x.phase[x.key_list.index('M2')]))
    print('M2 phase:     {}'.format(x.r[x.key_list.index('M2')]))

```
