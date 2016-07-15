import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

classifiers = """\
Development Status :: stable
Environment :: Console
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: GPL
Operating System :: OS Independent
Programming Language :: Python
Topic :: Scientific/Engineering
Topic :: Software Development :: Libraries :: Python Modules
"""

setup(
    name = "TAPPY",
    version = "0.10.2",
    author = "Tim Cera, Pierre Cazenave",
    author_email = "tim@cerazone.net, pica@pml.ac.uk",
    description = ("TAPPY is a tidal analysis package. It breaks down an hourly record of water levels into the component sine waves."),
    license = "GPLv2",
    keywords = "harmonic analysis, tides, ellipses, consituents",
    platforms = "any",
    url = "http://sourceforge.net/projects/tappy, http://gitlab.em.pml.ac.uk/pica/PyFVCOM, https://github.com/pwcazenave/tappy",
    packages=['tappy', 'tappy.tappy_lib'],
    long_description=read('README.md'),
    classifiers=classifiers
)
