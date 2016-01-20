import sys
import os
import re
from PreProcessing import PreProcessing
from OpenFMRIData import OpenFMRIData
from createFirstLevel import createFirstLevel

# data_dir   	= os.environ.get('DATA_DIR') or '/home/rack-hezi-03/home/roigilro/fMRI/Data/'
data_dir   	=  '/media/roee/fMRI/Data/'

# study_name 	= os.environ.get('STUDY_NAME') or 'Self-Other'
study_name 	= 'Self-Other'

raw_dir 	= os.path.join(data_dir,'raw')

op = OpenFMRIData(data_dir, raw_dir,study_name)

subject_names = op.get_subject_names() # All subjects

# create open fMRI data structure and conver .dcms to .nii
for name in subject_names:
    x=2
    # subject_dir = op.create_subject_dir(name, overwrite=True)

#TODO: agree on a standard to include open behvadata.txt files in raw directory structure
# copy over the behavdata.txt files to correct place in open-fmri data struc created above:
# ~/sub001/behav/tak00X_run00X/behavdata.txt

for name in subject_names:
    subject = op.load_subject_dir(subname=name)
    subject_dir_name = subject._path
    op.create_subject_evs(subject_dir_name= subject_dir_name , mode = 'basic')
    op.create_subject_evs(subject_dir_name= subject_dir_name , mode = 'trial_base')


# run preprocessing and first levle naalysis
for name in subject_names:
    subject = op.load_subject_dir(subname=name)
    #  if we want to create new data for analysis
    # subject_dir = op.create_subject_dir(name)
    #  if we want to load new data for analysis
    # structural:
    subject_dir = subject._path
    preproc = PreProcessing(op,[subject])
    brain_image = preproc.extract_brain(subject,automatic_approval = True)
    preproc.estimate_bias_field(subject, brain_image, overwrite=True)

    #functional
    # preproc.motion_correction(subject)
    # preproc.anatomical_registration(subject)
    # preproc.functional_registration(subject)
    # preproc.highpassfilter(subject,highpass_freq=2,)
    #
    #
    # ### CREATE FIRST LEVEL
    # first_level = createFirstLevel()
    # trtimeinsec = 2.5 # set the tr
    # first_level.runglmperun(subject,trtimeinsec)
    #### END CREATE FIRST LEVEL GLM PER SUB

    # Brain Extraction and bias field estimation
    # print "Started Analysis:{}".format(subject)
    # brain_image = preprocess.extract_brain(subject,automatic_approval=True)
    # anat_image = preprocess.estimate_bias_field(subject, brain_image)
    # Motion
    # preprocess.motion_correction(subject)

    # Slice‐time correction - test 2
    # preprocess.slice_time_correction(subject)

    # Spatial  filtering  ( Smoothing)
    # preprocess.anatomical_smoothing(subject,8.0,2000.0)
    # preprocess.functional_smoothing(subject,kwargs['fwhm'],kwargs['brightness_threshold'])

    # Temporal  filtering (High Pass)

    # Anatomical Registration
    # preprocess.anatomical_registration(subject)

    # Functional Registration
    # preprocess.functional_registration(subject)

    # Segmentation
    # if 'func_seg' in kwargs:
    #     preprocess.functional_segmentation(subject)
    # else:
    #     preprocess.segmentation(subject)
    #     preprocess.generate_functional_gm_masks(subject)
