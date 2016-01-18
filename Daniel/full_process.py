#!/usr/bin/python
import os
from OpenFMRIData import OpenFMRIData
from OpenFMRIAnalyzer import OpenFMRIAnalyzer
from subject_searchlight import run_searchlight

from make_ds import make_ds
from glob2 import glob
from os.path import join as _opj
from single_subject_sl import do_searchlight
from mvpa2.cmdline.helpers import arg2ds
from group_level_map import generate_group_level_map
from mvpa2.generators.permutation import AttributePermutator
from analysis_configuration import AnalysisConfiguration

def main():
	conf = AnalysisConfiguration()

	data_dir = os.environ.get('DATA_DIR') or '/home/daniel/fsl-analysis/data'

	op = OpenFMRIData(data_dir, conf.study_name)
	analyzer = OpenFMRIAnalyzer(op, conf)
	all_subject_dirs = op.all_subjects_dirs_with_raw()

	for subject in all_subject_dirs:
		analyzer.extract_brain(subject)

	for subject in all_subject_dirs:
		analyzer.anatomical_registration(subject)

	for subject in all_subject_dirs:
		#for task in conf.mvpa_tasks:
			#subject.remove_volumes_from_model(1, "", task, conf.num_of_volumes_to_delete)

		analyzer.motion_correction(subject)
		analyzer.functional_registration(subject)

		if conf.func_seg:
			analyzer.functional_segmentation(subject)
		else:
			analyzer.segmentation(subject)
			analyzer.generate_functional_gm_masks(subject)
		#analyzer.warp_standard_mask(subject)


	for subject in all_subject_dirs:
		# DO SL
		out_dir = _opj(subject.path(),'results',conf.dir_name())
		if not os.path.exists(out_dir):
			os.makedirs(out_dir)
		run_searchlight(op, subject, conf, out_dir)
#		run_searchlight(op.study_dir(), subject.subcode(), mask_name, k, [['G1','G4']], out_dir,flavor)


	#Group Level
#	output_dir = _opj(op.study_dir(), 'results', "{}".format(conf.dir_name()))

#	if not os.path.exists(output_dir):
#		os.makedirs(output_dir)

#	files = glob(_opj(op.study_dir(), "**", 'results', conf.dir_name(), '*acc_mni.nii.gz'))
#	print files
#	generate_group_level_map( files, output_dir)


if __name__ == '__main__':
	main()