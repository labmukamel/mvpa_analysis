import sys
import os
import re

from OpenFMRIAnalyzer import OpenFMRIAnalyzer
from OpenFMRIData import OpenFMRIData

# subname    	= sys.argv[1]

data_dir   	= os.environ.get('DATA_DIR') or '/home/daniel/fsl-analysis/data'
study_name 	= os.environ.get('STUDY_NAME') or 'AV'

raw_dir 	= os.path.join(data_dir, 'raw')

op = OpenFMRIData(data_dir, raw_dir, study_name)

# subject_names = ['HiAn'] # Specific subject names
subject_names = op.get_subject_names()  # All subjects

for name in subject_names:
    subject_dir = op.create_subject_dir(name, overwrite=True)
    #  if we want to create new data for analysis
    # subject_dir = op.create_subject_dir(name)
    #  if we want to load new data for analysis
    # subject_dir = op.load_subject_dir(subname=name)
    analyzer = OpenFMRIAnalyzer(op,[subject_dir])
    brain_image = analyzer.extract_brain(subject_dir)
    analyzer.estimate_bias_field(subject_dir, brain_image, overwrite=True)
    analyzer.motion_correction(subject_dir)
    analyzer.anatomical_registration(subject_dir)
    analyzer.functional_registration(subject_dir)
    analyzer.highpassfilter(subject_dir,highpass_freq=2,)

