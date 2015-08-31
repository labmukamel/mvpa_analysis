#!/usr/bin/python

import sys
from os.path import join as _opj
import os
from mvpa2.datasets.sources.openfmri import OpenFMRIDataset
from mvpa2.datasets.eventrelated import fit_event_hrf_model
from mvpa2.base.hdf5 import h5save
from mvpa2.mappers.detrend import poly_detrend
from mvpa2.mappers.zscore import zscore
#from nilearn.image import smooth_img
import nibabel as nb
import numpy as np



"""
def smooth(img):
    # we need to preserve the original header because the smoothing function
    # fucks the TR up
    nimg = smooth_img(img, fwhm=2.0)
    return nb.Nifti1Image(nimg.get_data(),
                          img.get_affine(),
                          header=img.get_header())
"""
def detrend(ds):
	poly_detrend(ds, polyord=1, chunks_attr='chunks')
	zscore(ds, chunks_attr='chunks', dtype='float32')
	return ds
def make_ds(sub, datapath, flavor):
	of = OpenFMRIDataset(datapath)
	ds = of.get_model_bold_dataset(
	    model_id=1, subj_id=sub,
	    flavor=flavor,
	    mask=_opj(
		datapath, 'sub%.3i' % sub, 'masks', 'task001_run001',
		'grey.nii.gz'),
	    #preproc_img=smooth,
	    preproc_ds = detrend, 
	    modelfx=fit_event_hrf_model,
	    time_attr='time_coords',
	    condition_attr='condition')
	ds14 = ds[np.array([c in ['G1','G4']for c in ds.sa['condition']])]
	ds23 = ds[np.array([c in ['G2','G3']for c in ds.sa['condition']])]
	
	result_dir = _opj(datapath,'mvpa','ds',flavor)
	if not os.path.isdir(result_dir):
		os.makedirs(result_dir)	
	print "{:0>3d}-ds14 {},{}".format(sub,ds14.shape,ds14.sa.condition)
	print "{:0>3d}-ds23 {},{}".format(sub,ds23.shape,ds23.sa.condition)
	h5save(_opj(result_dir, 'sub%.3i_14_hrf.hdf5' % sub), ds14)
	h5save(_opj(result_dir, 'sub%.3i_23_hrf.hdf5' % sub), ds23)

def main():
	sub = int(sys.argv[1]) 
	data_dir   	= os.environ.get('DATA_DIR') or '/home/user/data'
	study_name 	= os.environ.get('STUDY_NAME') or 'LP'
	flavor		= 'mcf'
	make_ds(sub, _opj(data_dir,study_name),flavor)


if __name__ == '__main__':
	main()
