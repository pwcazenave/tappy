#!/usr/bin/env python

import sys
import unittest
import glob
import subprocess
import difflib
import os
import os.path

# directory dance to find tappy.py module in directory above
# test_tappy.py
file_loc = os.path.abspath(__file__)
cur_path = os.path.dirname(file_loc)
tappy_loc = os.path.dirname(cur_path)

sys.path.insert(0, tappy_loc)

class TappyTest(unittest.TestCase):
    def setUp(self):
        os.chdir(os.path.join(cur_path, 'tmp'))
        for files in ['*.dat', '*.xml']:
            for f in glob.glob(files):
                os.remove(f)
        self.con_output1 = subprocess.Popen([
                os.path.join(os.path.pardir,os.path.pardir,'tappy.py'),
                'analysis',
                os.path.join(os.path.pardir,os.path.pardir,'example','mayport_florida_8720220_data.txt'), 
                os.path.join(os.path.pardir,os.path.pardir,'example','mayport_florida_8720220_data_def.txt'), 
        #        '--zero_ts="transform"',
                '--outputts=True', 
                '--outputxml="testout.xml"', 
        #        '--filter="transform"',
                '--include_inferred=False'
                ],
                stdout = subprocess.PIPE)
        sts = os.waitpid(self.con_output1.pid, 0)[1]

    def test_constituents(self):
        for i in ['M2', 'M8']:
            alines = open(os.path.join(os.path.pardir,'output_ts','outts_%s.dat' % i)).readlines()
            blines = open(os.path.join('outts_%s.dat' % i)).readlines()
            d = difflib.Differ()
            result = list(d.compare(alines, blines))
            result = [i for i in result if i[0] in ['+', '-', '?']]
            print ''.join(result),
            self.assertEqual(result, [])

    def test_closure(self):
        self.con_output2 = subprocess.call([
                os.path.join(os.path.pardir,os.path.pardir,'tappy.py'),
                'prediction',
                'testout.xml', 
                '2000-01-01T00:00:00', 
                '2000-02-01T00:00:00', 
                '60', 
                '--fname="predict.out"'
                ])
        self.con_output3 = subprocess.Popen([
                os.path.join(os.path.pardir,os.path.pardir,'tappy.py'),
                'analysis',
                'predict.out', 
                os.path.join(os.path.pardir,'predict_def.out'), 
        #        '--zero_ts="transform"',
                '--outputxml="testoutclosure.xml"', 
        #        '--filter="transform"',
                '--include_inferred=False'
                ],
                stdout = subprocess.PIPE)
        sts = os.waitpid(self.con_output3.pid, 0)[1]
        alines = open(os.path.join('testout.xml')).readlines()
        blines = open(os.path.join('testoutclosure.xml')).readlines()
        d = difflib.Differ()
        result = list(d.compare(alines, blines))
        result = [i for i in result if i[0] in ['+', '-', '?']]
        print ''.join(result),
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()

