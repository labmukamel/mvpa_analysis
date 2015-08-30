#!/usr/bin/python
import sys
import os
import re

from OpenFMRIData import OpenFMRIData

#subname    	= sys.argv[1]

data_dir   	= os.environ.get('DATA_DIR') or '/home/daniel/mvpa_analysis/data/'
study_name 	= os.environ.get('STUDY_NAME') or 'AV'

raw_dir 	= os.path.join(data_dir,'raw')
behavioural_dir = os.path.join(data_dir,'behavioural')

op = OpenFMRIData(data_dir, raw_dir, '' ,study_name)

#subject_names = ['MoCa'] # Specific subject names
subject_names = op.get_subject_names(raw_dir) # All subjects

for name in subject_names:
    subject_dir = op.load_subject_dir(subname=name)
    # if we want to create new data for analysis
    # subject_dir = op.create_subject_dir(name)
    #analyzer = OpenFMRIAnalyzer(op,[subject_dir.subcode()])
    #analyzer.analyze(mc_merge=True)

