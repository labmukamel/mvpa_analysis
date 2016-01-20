import sys
import os
import re
from PreProcessing import PreProcessing
from OpenFMRIData import OpenFMRIData
from createFirstLevel import createFirstLevel
#subname    	= sys.argv[1]

# data_dir   	= os.environ.get('DATA_DIR') or '/home/rack-hezi-03/home/roigilro/fMRI/Data/'
# data_dir   	= os.environ.get('DATA_DIR') or '/media/roee/fMRI/Data/'
data_dir   	=  '/media/roee/fMRI/Data/'

# study_name 	= os.environ.get('STUDY_NAME') or 'Self-Other'
study_name 	= 'Self-Other'

raw_dir 	= os.path.join(data_dir,'raw')

op = OpenFMRIData(data_dir, raw_dir,study_name)

#subject_names = ['MoCa'] # Specific subject names
subject_names = op.get_subject_names() # All subjects

for name in subject_names:
    # if we want to create new data for analysis - test
    # subject_dir = op.create_subject_dir(name)
    # create new data (convert dicom to nii etc.creat
    subject = op.load_subject_dir(subname=name)
    subject_dir_name = subject._path
    op.create_subject_evs(subject_dir_name= subject_dir_name , mode = 'basic')
    # - Creates the new directories only when given subname!
    # jsonmaping = op.mapping_json()
    # subject_code = jsonmaping[name]
    # just load existing data structure
    # subject = op.load_subject_dir(subname= name, subcode= subject_code)
    # preprocess = PreProcessing(op,[subject])

    ### CREATE FIRST LEVEL
    # first_level = createFirstLevel()
    # set the tr
    # trtimeinsec = 2.5
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
