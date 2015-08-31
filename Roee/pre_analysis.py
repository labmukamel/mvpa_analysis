#!/usr/bin/python
import sys
import os
import re
import OpenFMRIAnalyzer
from OpenFMRIData import OpenFMRIData

#subname    	= sys.argv[1]

data_dir   	= os.environ.get('DATA_DIR') or '/media/lior/DAE86CF0E86CCBF7/Data/data'
study_name 	= os.environ.get('STUDY_NAME') or 'EPITest'

raw_dir 	= os.path.join(data_dir,'raw')

op = OpenFMRIData(data_dir, raw_dir,study_name)

#subject_names = ['MoCa'] # Specific subject names
subject_names = op.get_subject_names() # All subjects

for name in subject_names:
    subject_dir = op.create_subject_dir(name)
    # if we want to create new data for analysis
    # subject_dir = op.create_subject_dir(name)
    analyzer = OpenFMRIAnalyzer(op,[subject_dir.subcode()])
    analyzer.extract_brain(subject_dir)

