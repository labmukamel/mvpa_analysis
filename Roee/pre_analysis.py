#!/usr/bin/python
import sys
import os
import re
from OpenFMRIAnalyzer import OpenFMRIAnalyzer
from OpenFMRIData import OpenFMRIData

#subname    	= sys.argv[1]

data_dir   	= os.environ.get('DATA_DIR') or '/media/roee/fMRI/Data/'
study_name 	= os.environ.get('STUDY_NAME') or 'Self-Other'

raw_dir 	= os.path.join(data_dir,'raw')

op = OpenFMRIData(data_dir, raw_dir,study_name)

#subject_names = ['MoCa'] # Specific subject names
subject_names = op.get_subject_names() # All subjects

for name in subject_names:
    subject = op.load_subject_dir(subname=name)
    # if we want to create new data for analysis
    # subject_dir = op.create_subject_dir(name)
    analyzer = OpenFMRIAnalyzer(op,[subject])

    # Brain Extraction and bias field estimation
    print "Started Analysis:{}".format(subject)
    brain_image = analyzer.extract_brain(subject,automatic_approval=True)
    anat_image = analyzer.estimate_bias_field(subject, brain_image)

    # Motion Correction
    analyzer.motion_correction(subject)

    # Slice‐time correction
    # analyzer.slice_time_correction(subject)

    # Spatial  filtering  ( Smoothing)
    analyzer.anatomical_smoothing(subject,8.0,2000.0)
    # analyzer.functional_smoothing(subject,kwargs['fwhm'],kwargs['brightness_threshold'])

    # Temporal  filtering (High Pass)

    # Anatomical Registration
    analyzer.anatomical_registration(subject)

    # Functional Registration
    analyzer.functional_registration(subject)

    # Segmentation
    # if 'func_seg' in kwargs:
    #     analyzer.functional_segmentation(subject)
    # else:
    #     analyzer.segmentation(subject)
    #     analyzer.generate_functional_gm_masks(subject)
