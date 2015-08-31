#!/usr/bin/python

import os
from glob import glob

import pandas as pd


class SubjectDir(object):
    def __init__(self, subject_code, path, raw_path=None, task_order=None, task_mapping=None, createbehavdict=None):
        """
		Subject Directory Initialization

		Parameters
			path: Output path in openfmri format
			raw_path: Contains the dicom folders
			task_order.txt: List from to task_order.txt
			task_mapping: List from task_mapping.txt
			createbehavdict: dictionary[2] {'func': function that creates the conditions of the models, 'behav': behavioural path}
		"""

        print("Subject {}".format(subject_code))

        self._path = path
        self._raw_path = raw_path
        self._task_order = task_order
        self._task_mapping = task_mapping
        self._subject_code = subject_code
        self._create_behav_dict = createbehavdict

        self._subdirs = {'functional': 'BOLD',
                         'anatomical': 'anatomy',
                         'model': 'model',
                         'masks': 'masks',
                         'behav': 'behav'}

        isValid = self.__isValid__(self._path)

        if (not os.path.isdir(self._path) or not isValid):

            if os.path.isdir(self._path) and not isValid:
                print("Openfmri directory exists but is not valid")

            if raw_path is None:
                raise Exception("Cannot create new subject directory from subcode")
            else:
                # Preparing the subject subdirectories
                print("Preparing the subject subdirectories")
                self.__create_subject_dirtree__()

        self.__load_dirtree__()

    def __isValid__(self, path):

        # Must have all the relevant folders(BOLD,anatomy,model,masks,behav)
        if os.listdir(path).sort() != self._subdirs.values().sort():
            print("Openfmri directory doesn't have all its subdirectories")
            return False

        # Has the anatomical file
        if not os.path.exists(self.anatomical_brain_nii()):
            print("Openfmri directory doesn't have the anatomical nii")
            return False

        # Checks that there exists a bold file in each task directory in each functional directory
        if not all(os.path.exists(os.path.join(bold,'bold.nii.gz')) for bold in [os.path.join(self.functional_dir(), taskrun) for taskrun in self._task_order]):
            print("Openfmri directory doesn't have all the bold nii files")
            return False

        return True

    def __load_dirtree__(self):
        """
		Creates a dictionary of <task,functional directory of the task>
		Ex: _dir_tree['functional']['task001'][['BOLD/task001_run001'],['BOLD/task001_run002']]
		"""
        print("Loading openfmri directory structure")
        self._dir_tree = {'functional': dict(),
                          'model': dict()}

        # Reads all the sub directories of the functional directory that are in format taskxxx_runxxx
        # Saves to the dictionary where the key is the task and the value is the directory path

        task_pairs = [(directory.split('/')[-1].split('_')[0], directory)
                      for directory in
                      glob(os.path.join(self.functional_dir(), 'task[0-9][0-9][0-9]_run[0-9][0-9][0-9]'))]

        for task, run_dir in task_pairs:
            if task in self._dir_tree['functional']:
                self._dir_tree['functional'][task].append(run_dir)
            else:
                self._dir_tree['functional'][task] = [run_dir]

    def dir_tree(self, sub_dir=None):
        """
		Retrieves the directory from the directory tree
		Sub_dir is of format: functional, anatomical, model, masks, behav
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
			- behav/taskxxx_runxxx
		"""
        num_models = 3 + 1  # we need the +1 because we don't start from index 0

        onset_dirs = ["model{:0>3d}/onsets".format(directory) for directory in range(1, num_models)]

        dir_tree = {
        # In the main path we create functional, anatomical, model, masks folders
            self._path: self._subdirs.values(),

        # Create the task order folders inside the functional directory - BOLD/taskxxx_runxxx
            self.functional_dir(): self._task_order,

        # Create modelxxx/onsets/taskxxx
            self.model_dir(): [os.path.join(onset_dir, task) for onset_dir in onset_dirs for task in self._task_order],

        # Create a different mask directory of each task and run Mask/anatomytaskxxx_runxxx
            self.masks_dir(): ['anatomy'] + self._task_order,

        # Create the task order folders inside the behavioural directory - behav/taskxxx_runxxx
            self.behavioural_dir(): self._task_order,

        }

        for path, directories in dir_tree.iteritems():
            for directory in directories:
                # If the directory doesn't exist then we create it
                if not os.path.isdir(os.path.join(path, directory)):
                    os.makedirs(os.path.join(path, directory))

        self.__dcm_to_nii__()

        if(self._create_behav_dict != None and hasattr(self._create_behav_dict['func'], '__call__')):
            func = self._create_behav_dict['func']
            behav = self._create_behav_dict['behav']
            func(self,onset_dirs,behav)


    def __dcm_convert__(self, source_directory, target_directory, target_filename, rename_prefix, erase=False):
        cmd = "dcm2nii -o {} {} > /dev/null".format(target_directory, source_directory)
        os.system(cmd)

        nii_files = glob("{}/{}*".format(target_directory, rename_prefix))
        if (len(nii_files) == 0):
            print("Error: Check that your dicom files are ok, dcm2nii doesn't convert well")
        os.rename(nii_files[0], os.path.join(target_directory, '{}.nii.gz'.format(target_filename)))

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
        raw_anatomical = glob("{}/*MPRAGE_iso*".format(self._raw_path))[
            0]  # The anatomical directory in the raw data contains MPRAGE
        raw_functional_dirs = sorted(
            glob("{}/*ep2*".format(self._raw_path)))  # The functional directories in the raw data contains ep2

        print("Converting DCM to NII")

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
        print("Finished Converting DCM to NII")

    def path(self):
        return self._path

    def raw_path(self):
        return self._raw_path

    def masks_dir(self):
        return os.path.join(self._path, self._subdirs['masks'])

    def anatomical_dir(self):
        return os.path.join(self._path, self._subdirs['anatomical'])

    def anatomical_brain_nii(self):
        return os.path.join(self.anatomical_dir(), 'highres001_brain.nii.gz')

    def model_dir(self):
        return os.path.join(self._path, self._subdirs['model'])

    def behavioural_dir(self):
        return os.path.join(self._path, self._subdirs['behav'])

    def functional_dir(self):
        return os.path.join(self._path, self._subdirs['functional'])

    def subcode(self):
        return self._subject_code


def test():
    task_order = []
    task_mapping = []

    with open("task_order.txt", 'r') as fh:
        task_order = fh.read().splitlines()

    # with open('task_mapping.txt', 'r') as fh:
    #		task_mapping = fh.read().splitlines()

    # Will read from raw_data folder and create all the folders under openfmri/
    s = SubjectDir('001', 'openfmri', 'raw_data', task_order)


if __name__ == "__main__":
    test()
