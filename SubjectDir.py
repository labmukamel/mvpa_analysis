#!/usr/bin/python

import os
from glob import glob

import pandas as pd

class SubjectDir(object):

	def __init__(self, subject_code, path, raw_path=None, behavioural_path=None, task_order=None, task_mapping=None):
		"""
		Subject Directory Initialization

		Parameters
			path: Output path in openfmri format
			raw_path: Contains the dicom folders
			behavioural_path:
			task_order.txt: List from to task_order.txt.txt
			task_mapping: List from task_mapping.txt
		"""
		self._path 		= path
		self._raw_path 		= raw_path
		self._behavioural_path 	= behavioural_path
		self._task_order 	= task_order
		self._task_mapping	= task_mapping
		self._subject_code	= subject_code

		self._subdirs = {'functional': 	'BOLD', 
				 'anatomical': 	'anatomy',
				 'model':	'model',
				 'masks':	'masks'}

		if(not os.path.isdir(self._path)):
			if raw_path is None:
				raise Exception("Cannot create new subject directory from subcode")
			else:
				# Preparing the subject subdirectories
				self.__create_subject_dirtree__()

		self.__load_dirtree__()

	def __load_dirtree__(self):
		"""
		Creates a dictionary of <task,functional directory of the task>
		Ex: _dir_tree['functional']['task001'][['BOLD/task001_run001'],['BOLD/task001_run002']]
		"""
		self._dir_tree = {'functional': dict(),
                                  'model': dict()}

		# Reads all the sub directories of the functional directory that are in format taskxxx_runxxx
		# Saves to the dictionary where the key is the task and the value is the directory path
		task_pairs =  [(directory.split('/')[-1].split('_')[0], directory)
					   		for directory in glob(os.path.join(self.functional_dir(), 'task[0-9][0-9][0-9]_run[0-9][0-9][0-9]'))]

		for task, run_dir in task_pairs:
			if task in self._dir_tree['functional']:
				self._dir_tree['functional'][task].append(run_dir)
			else:
				self._dir_tree['functional'][task] = [run_dir]

	def dir_tree(self, sub_dir=None):
		"""
		Retrieves the directory from the directory tree
		Sub_dir is of format: functional, anatomical, model, masks
		"""
		if sub_dir:
			return self._dir_tree[sub_dir]
		else:
			return self._dir_tree

	def __repr__(self):
		return "<Subject Dir: sub{:0>3d}>".format(self._subject_code)

	def __create_subject_dirtree__(self):
		"""
		Preparing the subject subdirectories
			- Creating BOLD, anatomy, model, masks folders
			- Creating BOLD/taskxxx_runxxx
			- Creating modelxxx/onsets/taskxxx
			- Mask/anatomytaskxxx_runxxx
		"""
		num_models = 3+1 # we need the +1 because we don't start from index 0

		onset_dirs = ["model{:0>3d}/onsets".format(directory) for directory in range(1, num_models)]

		dir_tree = {
			    self._path: 		self._subdirs.values(), # In the main path we create functional, anatomical, model, masks folders
			    self.functional_dir(): 	self._task_order, # Create the  task order folders inside the functional directory - BOLD/taskxxx_runxxx
			    self.model_dir():		[os.path.join(onset_dir, task) for onset_dir in onset_dirs for task in self._task_order], # Create modelxxx/onsets/taskxxx
			   self.masks_dir():		['anatomy']+self._task_order # Create a different mask directory of each task and run Mask/anatomytaskxxx_runxxx
			   }

		for path, directories in dir_tree.iteritems():
			for directory in directories:
				# If the directory doesn't exist then we create it
				if not os.path.isdir(os.path.join(path, directory)):
					os.makedirs(os.path.join(path, directory))

		self.__dcm_to_nii__()
		#self.__create_evs__(onset_dirs)

# Specific for Roni
# 	def __create_evs__(self, onset_dirs, dummy=False):
# 		for file_regex, task_sequence in self._task_mapping.iteritems():
# 			run_files = sorted(glob(os.path.join(self.behavioural_path(), '{}*.csv'.format(file_regex)))
# )
# 			### From here on out this function is specific to my experiment. parsing logs from psychopy
# 			print "{}->{}".format(file_regex, run_files)
# 			for run_number,run_file in enumerate(run_files):
# 				df = pd.read_csv(run_file)
# 				conds = {}
#
# 				if 'keyPressed' in df.columns:
# 					conds['catch'] = df[df.keyPressed.notnull()]
# 					df = df[-(df.stim1.str.contains('atch') | df.stim2.str.contains('atch') | df.stim3.str.contains('atch')| df.stim4.str.contains('atch')) & df.keyPressed.isnull()]
#
# 				df['cond'] = df.stim1.str.split('\\').str[1]
# 				conds.update(dict((cond,df[df.cond.eq(cond)]) for cond in df.cond.unique()))
# 				for condition_number, key in enumerate(sorted(conds.keys())):
# 					value = conds[key]
# 					col_idx = df.columns.get_loc("start stim")
# 					value = value.ix[:,col_idx:col_idx+1]
# 					value['start stim'] = value['start stim'].astype(int)
# 					if 'MVPA' in run_file:
# 						value['length'] = 4
# 						# TODO: Replace this shit!
# 					else:
# 						value['length'] = 12
# 						# TODO: Replace this shit!
#
# 					value['value'] = 1
# 					conds[key] = value
#
# 					#run_name = "{}_run{:0>3d}".format(task_sequence, run_number+1)
# 					condition_name = "cond{:0>3d}.txt".format(condition_number+1)
# 					print ">>> condition mapping: {}->{}".format(key,condition_number)
# 					for onset_dir in onset_dirs:
# 						value.to_csv(os.path.join(self.model_dir(), onset_dir, task_sequence, condition_name), sep='\t',index=False,header=False)
#



	def __dcm_convert__(self, source_directory, target_directory, target_filename, rename_prefix, erase=False):
		cmd = "dcm2nii -o {} {} > /dev/null".format(target_directory, source_directory)
                os.system(cmd)

                nii_file = glob("{}/{}*".format(target_directory, rename_prefix))[0]
                os.rename(nii_file, os.path.join(target_directory, '{}.nii.gz'.format(target_filename)))

		if erase:
			for file_name in glob("{}/*".format(target_directory)):
				if target_filename not in file_name:
					os.remove(file_name)

	def __dcm_to_nii__(self, dummy=False):
		"""
		Converts the dicom files:
		 	- MPRAGE directory ->  NIFTY in anatomical folder(anatomy/highres001.nii.gz)
			- ep2 directories ->  NIFTY in functional folder(bold/taskxxx_runxxx/bold.nii.gz)
		"""
		raw_anatomical = glob("{}/*MPRAGE*".format(self._raw_path))[0] # The anatomical directory in the raw data contains MPRAGE
		raw_functional_dirs = sorted(glob("{}/*ep2*".format(self._raw_path))) # The functional directories in the raw data contains ep2

		print "Converting DCM to NII"

		if dummy:
			print "self.__dcm_convert__(raw_anatomical, self.anatomical_dir(), 'highres001', 'co', True)"
		else:
			self.__dcm_convert__(raw_anatomical, self.anatomical_dir(), 'highres001', 'co', True)

		if dummy:
			print "creating functional niis"
		else:
			# Matching the tasks(from task_order.txt.txt) to the functional directories of the raw data(ep2) and converting the dicom files to nifty
			for raw_functional_directory, run_name in zip(raw_functional_dirs, self._task_order):
				self.__dcm_convert__(raw_functional_directory, 
						     os.path.join(self.functional_dir(), run_name),
						     'bold',
						     '',
						     False)

	def path(self):
		return self._path

	def raw_path(self):
		return self._raw_path
	
	def behavioural_path(self):
		return self._behavioural_path
	
	def masks_dir(self):
		return os.path.join(self._path,self._subdirs['masks'])
	
	def anatomical_dir(self):
		return os.path.join(self._path,self._subdirs['anatomical'])
	
	def anatomical_brain_nii(self):
		return os.path.join(self.anatomical_dir(),'highres001_brain.nii.gz')
			
	def model_dir(self):
		return os.path.join(self._path,self._subdirs['model'])	
	
	def functional_dir(self):
		return os.path.join(self._path,self._subdirs['functional'])	

	def subcode(self):
		return self._subject_code
def test():
	task_order = [];
	task_mapping = [];
	with open("/home/lior/PycharmProjects/mvpa_analysis/task_order.txt", 'r') as fh:
			task_order = fh.read().splitlines()

	#with open('task_mapping.txt', 'r') as fh:
	#		task_mapping = fh.read().splitlines()

	s = SubjectDir('001','openfmri','/media/lior/DAE86CF0E86CCBF7/Data/RM_lab_Roee_BaOf_20150618_1100','',task_order)

if __name__ == "__main__":
	test()
