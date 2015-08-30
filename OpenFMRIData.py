#!/usr/bin/python

import os
import json
import re

from glob import glob
from SubjectDir import SubjectDir


class OpenFMRIData(object):

	def __init__(self, data_dir, raw_data_dir, behavioural_dir, study_name):
		"""
			Loads subject mapping, task order, task mapping files

			Parameters
				data_dir: Target openfmri directory
				raw_data_dir: Root raw directory (Only the path to the raw directory (in raw/study_name/subxxx))
				behavioural_dir:
				study_name: The name of the study folder containing relevant subjects
		"""
		self._data_dir                = data_dir
		self._raw_data_dir            = os.path.join(raw_data_dir, study_name)
		self._behavioural_dir	      = os.path.join(behavioural_dir, study_name)

		self._study_name              = study_name
		self._study_dir               = os.path.join(self._data_dir, self._study_name)

		self._subject_mapping_file    = os.path.join(self._study_dir, 'mapping_subject.json')

		self.load_subject_mapping()
		self.load_task_order()
		self.load_task_mapping()

	def load_subject_mapping(self):
		if os.path.isfile(self._subject_mapping_file):
			mapping_file = open(self._subject_mapping_file, 'r')

			self._subject_mapping = json.load(mapping_file)
			mapping_file.close()
		else:
			self._subject_mapping = dict()
			self.__write_subject_mapping__()

	def load_task_order(self):
		with open(os.path.join(self._study_dir, 'task_order.txt'), 'r') as fh:
			self._task_order = fh.read().splitlines()

	def load_task_mapping(self):
		with open(os.path.join(self._study_dir, 'task_mapping.txt'), 'r') as fh:
			task_data = fh.read().splitlines()

		self._task_mapping = dict()

		task_pairs = [(task.split('\t')[0], task.split('\t')[1]) for task in task_data]
		for task_name, task_sequence in task_pairs:
			self._task_mapping[task_name] = task_sequence


	def get_subject_names(self):
		'''
		Extracting the subject names from the dicom raw data directories. In our lab the format is like: "RM_lab_.*_(.*)_[0-9]{8}_[0-9]{4}"
		Example: RM_lab_Roee_KrNo_20150618_1320
		:return:Array of subject names based on the directory of the raw data
		'''
		rgx = re.compile("RM_lab_.*_(.*)_[0-9]{8}_[0-9]{4}")
		return [rgx.search(dirname).group(1) for dirname in os.listdir(self._raw_data_dir)]

	def mapping_json(self):
		return self._subject_mapping

	def data_dir(self):
		return self._data_dir
	
	def study_dir(self):
		return self._study_dir

	def behavioural_dir(self):
		return self._behavioural_dir

	def raw_study_dir(self):
		return self._raw_data_dir

	def __get_latest_subject_directory__(self):
		directory_prefix = "sub"

		study_dirlist = glob("{}/{}*".format(self._study_dir, directory_prefix))

		# Takes the subject codes from the subjects in study directory
		subject_codes =[]
		for x in study_dirlist:
			# Replace the directory name to get only the subject code
			subject_codes.append(int(x.replace("{}/{}".format(self._study_dir, directory_prefix), "")))
		# Getting the largest number
		latest_dir_sequence = max(subject_codes + [0]) + 1

		#latest_dir_sequence = (max([int(x.replace("{}/{}".format(self._study_dir, directory_prefix), "")) for x in study_dirlist] + [0])+1)

		return latest_dir_sequence

	def __write_subject_mapping__(self):
		mapping_file = open(self._subject_mapping_file, 'w+')
		json.dump(self._subject_mapping, mapping_file)
		mapping_file.close()

	def __subcode_to_dir_format__(self, code):
		return os.path.join(self.study_dir(), "sub{:0>3d}".format(int(code)))

	def create_subject_dir(self, subject_name):
		"""
			Creates the openfmri structure by creating SubjectDir

			Parameters
				subname = (string)
			Returns:
				SubjectDir Object
		"""
		behavioural_dir = None

		# Gets the largest/latest subject code + 1 (from the study directory)
		subject_code = self.__get_latest_subject_directory__()

		# Adds the the new subject name to the subject_mapping dictionary
		self._subject_mapping[subject_name] = subject_code

		# Check whether subject raw directory exists before adding the mapping
		raw_dirs = glob('{}/*{}*'.format(self.raw_study_dir(), subject_name))

		if len(raw_dirs) == 0:
			raise BaseException("No subject by the name of {}".format(subject_name))

		raw_dir = raw_dirs[0]

		# behavioural_dirs = glob('{}/*{}*'.format(self.behavioural_dir(), subject_name))
		#
		# if len(behavioural_dirs) == 0:
		# 	raise BaseException("No behavioural data for subject {}".format(subject_name))
		# behavioural_dir = behavioural_dirs[0]

		# Saves the subject mapping to a file
		self.__write_subject_mapping__()

		return SubjectDir(subject_code, self.__subcode_to_dir_format__(subject_code), raw_dir, behavioural_dir, self._task_order, self._task_mapping)

	def load_subject_dir(self, **kwargs):
		"""
			Creates or uses the openfmri structure by creating SubjectDir
				- Creates the new directories only when given subname!
				- Uses current structure when given subcode/subname and the subject_mapping file exists in the study dir

			Parameters
				subcode = (number) or subname = (string)
				- Ex: subject_dir(subcode = 1) or subject_dir(subname = 'AzOr')
			Returns:
				SubjectDir Object
		"""

		subject_code 	= None
		raw_dir      	= None
		behavioural_dir = None

		if 'subcode' in kwargs:
			subject_code = kwargs['subcode']
		elif 'subname' in kwargs:
			# load mapping from pickle, if subject name does not exist, create and populate pickle
			subject_name = kwargs['subname']

			if subject_name in self._subject_mapping:
				subject_code = self._subject_mapping[subject_name]
			else:
				# If the subject doesn't exist in the subject mapping then we create the structure
				return self.create_subject_dir(subject_name)

		# Params-
		#	1) subject_code, 2) data_dir/study_name/sub[subject_code], 3) data_dir/raw, 4) data_dir/behavioural,
		# 	5) array of task_order.txt, 6) array of task_mapping.txt
		# Returns- subjectdir object that contains the openfmri structure
		return SubjectDir(subject_code, self.__subcode_to_dir_format__(subject_code), raw_dir, behavioural_dir, self._task_order, self._task_mapping)

def test():
	o = OpenFMRIData('/home/user/data', '/home/user/data/raw', '/home/user/data/behavioural', 'LP')

	print "{:<40s}{}".format("data_dir", o.data_dir())
	print "{:<40s}{}".format("study_dir", o.study_dir())
	print "{:<40s}{}".format("raw_study_dir", o.raw_study_dir())
	print "{:<40s}{}".format("behavioural_dir", o.behavioural_dir())

	subject_dir_by_name = o.subject_dir(subname='KeEl')
	print "{:<40s}{}".format("subject(subname='KeEl').path()", subject_dir_by_name.path())
	print "{:<40s}{}".format("subject(subname='KeEl').raw_path()", subject_dir_by_name.raw_path())
	print "{:<40s}{}".format("subject(subname='KeEl').behavioural_path()", subject_dir_by_name.behavioural_path())

	subject_dir = o.subject_dir(subcode=1)
	print "{:<40s}{}".format("subject(subcode=1).path()", subject_dir.path())
	print "{:<40s}{}".format("subject(subcode=1).anatomical_dir()", subject_dir.anatomical_dir())

	print "{:<40s}{}".format("mapping_json", o.mapping_json())
	print "{:<40s}{}".format("__get_latest_subject_directory__", o.__get_latest_subject_directory__())

	print "{:<40s}{}".format("task_order.txt", o._task_order)

if __name__ == "__main__":
	test()
