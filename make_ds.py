#!/usr/bin/python

import sys
from os.path import join as _opj

from mvpa2.datasets.sources.openfmri import OpenFMRIDataset
from mvpa2.datasets.eventrelated import fit_event_hrf_model
from mvpa2.base.hdf5 import h5save
from mvpa2.mappers.detrend import poly_detrend
from nilearn.image import smooth_img
import nibabel as nb
import numpy as np
datapath = '/home/user/data/LP'
of = OpenFMRIDataset(datapath)

sub = int(sys.argv[1]) + 1


def smooth(img):
    # we need to preserve the original header because the smoothing function
    # fucks the TR up
    nimg = smooth_img(img, fwhm=2.0)
    return nb.Nifti1Image(nimg.get_data(),
                          img.get_affine(),
                          header=img.get_header())
def detrend(ds):
	poly_detrend(ds, polyord=1, chunks_attr='chunks')
	print ds
#	ds.sa['split_conditions'] = ["{}_{}".format(c,i)  for i,c in enumerate(ds.sa['conditions'])]
	return ds

ds = of.get_model_bold_dataset(
    model_id=1, subj_id=sub,
    flavor='mcf',
    # full brain
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
print "ds14 {},{}".format(ds14.shape,ds14.sa['condition'])
print "ds23 {},{}".format(ds23.shape,ds23.sa['condition'])
h5save(_opj('data', 'sub%.3i_14_hrf.hdf5' % sub), ds14)
h5save(_opj('data', 'sub%.3i_23_hrf.hdf5' % sub), ds23)
