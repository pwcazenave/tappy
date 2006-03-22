import sys
import os

ced = os.path.abspath(os.sep.join(__path__))
sys.path.insert(0, ced)

ced = os.path.abspath(os.sep.join(__path__ + ['filelike']))
sys.path.insert(0, ced)

ced = os.path.abspath(os.sep.join(__path__ + ['astrolabe', 'lib', 'python']))
sys.path.insert(0, ced)

os.environ['TAPPY_LIB'] = os.sep.join(__path__)
