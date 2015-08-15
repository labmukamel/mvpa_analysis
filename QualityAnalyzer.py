#!/usr/bin/python

from OpenFMRIData import OpenFMRIData
import nibabel as nib
from statsmodels.tsa.tsatools import detrend
import os
import numpy as np
class QualityAnalyzer(object):
	def __init__(self, fmri_dataset):
		self._fmri_dataset = fmri_dataset
		self.__load_taskname_mapping__()
	
	def __load_taskname_mapping__(self):
		with open(os.path.join(self._fmri_dataset.study_dir(), 'task_key.txt'), 'r') as fh:
                        task_data = fh.read().splitlines()

                self._taskname_mapping = dict([(task.split('\t')[0], task.split('\t')[1]) for task in task_data])

	
	def analyze_runs(self, subcode):
		print ">>> Analyzing sub{:0>3d}".format(subcode)
		subject = self._fmri_dataset.subject_dir(subcode=subcode)
		
		for task , directories in subject.dir_tree('functional').iteritems():
			for directory in directories:
                                run_name = directory.split('/')[-1]
				maskfile = os.path.join(subject.masks_dir(),run_name,'gray.nii.gz')
				nonbrain_mask = os.path.join(subject.masks_dir(),run_name,'non_brain.nii.gz')

				img = nib.load(os.path.join(directory,'bold_mcf.nii.gz'))
				imgdata = img.get_data()
				maskimg=nib.load(maskfile)
				maskdata=maskimg.get_data()
				nonbrain_maskdata = nib.load(nonbrain_mask).get_data()
				voxmean=np.mean(imgdata,3)
				voxstd=np.std(imgdata,3)
				maskvox=np.where(maskdata>0)
				nonmaskvox=np.where(nonbrain_maskdata>0)
				voxsfnr=voxmean/voxstd
				meansfnr=np.mean(voxsfnr[maskvox])
				imgsnr=np.zeros(imgdata.shape[3])

				for t in range(imgdata.shape[3]):
					tmp=imgdata[:,:,:,t]
					tmp_brain=tmp[maskvox]
					tmp_nonbrain=tmp[nonmaskvox]
					maskmean=np.mean(tmp_brain)
					imgsnr[t]=maskmean/np.std(tmp_nonbrain)
				
				task_name, run_number = run_name.split('_')
				print '{} \n {}\nsfnr => {:>40f} \nsnr => {:>40f}'.format(self._taskname_mapping[task_name],run_number,meansfnr,np.mean(imgsnr))
				
				continue	
				detrended_zscore=np.zeros(imgdata.shape)
				detrended_data=np.zeros(imgdata.shape)
				print imgdata.shape
				for i in range(len(maskvox[0])):
					tmp=imgdata[maskvox[0][i],maskvox[1][i],maskvox[2][i],:]
					tmp_detrended=detrend(tmp)
					detrended_data[maskvox[0][i],maskvox[1][i],maskvox[2][i],:]=tmp_detrended
					detrended_zscore[maskvox[0][i],maskvox[1][i],maskvox[2][i],:]=(tmp_detrended - np.mean(tmp_detrended))/np.std(tmp_detrended)
				voxmean_detrended=np.mean(detrended_data,3)
				voxstd_detrended=np.std(detrended_data,3)


			

def test():
	fmri_data = OpenFMRIData('/home/user/data', '/home/user/data/raw', '/home/user/data/behavioural', 'EPITest')
	qa = QualityAnalyzer(fmri_data)
	qa.analyze_runs(1)
	pass

if __name__ == "__main__":
	test()
