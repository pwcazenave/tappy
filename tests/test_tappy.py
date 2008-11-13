#!/usr/bin/env python

import sys
import unittest
import glob

import os
import os.path

# directory dance to find tappy.py module in directory above
# test_tappy.py
file_loc = os.path.abspath(__file__)
cur_path = os.path.dirname(file_loc)
tappy_loc = os.path.dirname(cur_path)

sys.path.insert(0, tappy_loc)
import tappy
import difflib

class TappyTest(unittest.TestCase):
    def setUp(self):
        os.chdir(cur_path + os.sep + 'tmp')
        options, args = tappy.process_options('-o --filter transform ../../example/mayport_florida_8720220_data.txt')
        self.con_output = tappy.main(options, args)
        os.chdir(cur_path)

    def test_constituents(self):
        for i in ['M2', 'M8']:
            alines = open(os.sep.join(['output_ts','outts_%s.dat' % i])).readlines()
            blines = open(os.sep.join(['tmp','outts_%s.dat' % i])).readlines()
        d = difflib.Differ()
        a = []
        result = list(d.compare(alines, blines))
        print ''.join(result),
        self.assertEqual(a, [])

    def tearDown(self):
        os.chdir(cur_path + os.sep + 'tmp')
        for file in glob.glob('*.dat'):
            os.remove(file)
        os.chdir(cur_path)

if __name__ == "__main__":
    unittest.main()

