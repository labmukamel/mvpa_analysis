#!/usr/bin/python

import os
import nibabel
import shutil
import subprocess
import signal
import pre_proc_fromexample as pp
from OpenFMRIData import OpenFMRIData

from nipype.interfaces import fsl


class OpenFMRIAnalyzer(object):
	def __init__(self, fmri_data, subjects):
		self._fmri_data 	= fmri_data
		self._subjects_list 	= []

		self.__load_subjects__(subjects)

	def __load_subjects__(self, subjects):
		if len(subjects) > 0:
			for subject in subjects:
				self._subjects_list.append(self._fmri_data.subject_dir(subcode=subject))
		else:
			pass # load all subjects

	def analyze(self, **kwargs):
		for subject in self._subjects_list:
			print "Started:{}".format(subject)
			self.extract_brain(subject)
		for subject in self._subjects_list:

			if 'mc_merge' in kwargs:
				self.motion_correction(subject, kwargs['mc_merge'])
			else:
				self.motion_correction(subject)

		for subject in self._subjects_list:
			self.anatomical_registration(subject)
		for subject in self._subjects_list:
			self.functional_registration(subject)
		for subject in self._subjects_list:
			if 'func_seg' in kwargs:
				self.functional_segmentation(subject)
			else:
				self.segmentation(subject)
				self.generate_functional_gm_masks(subject)

	def generate_functional_gm_masks(self, subject):
		print ">>> Creating functional gray matter masks"
		mask_name = 'grey.nii.gz'
        	gm_mask = os.path.join(subject.masks_dir(),'anatomy',mask_name)
		for task, directories in subject.dir_tree('functional').iteritems():
			for directory in directories:
				run_name = directory.split('/')[-1]
				reg_dir = os.path.join(directory,'reg')
			
				gm2func_mask = fsl.preprocess.ApplyXfm()
				gm2func_mask.inputs.in_matrix_file = os.path.join(reg_dir, 'highres2example_func.mat')
				gm2func_mask.inputs.reference = os.path.join(reg_dir,'example_func.nii.gz')
				gm2func_mask.inputs.in_file = gm_mask
				gm2func_mask.inputs.out_file = os.path.join(subject.masks_dir(),run_name,mask_name)
				gm2func_mask.run()


	def functional_registration(self, subject):
		print ">>> Functional Registration"
		brain_image = subject.anatomical_brain_nii()
		for task, directories in subject.dir_tree('functional').iteritems():
			for directory in directories:
				bold_file = os.path.join(directory,'bold_mcf.nii.gz')
				bold_length = nibabel.load(bold_file).shape[3]
				reg_dir = os.path.join(directory,'reg')
				if os.path.isfile(os.path.join(reg_dir, 'highres2example_func.mat')):
					print "registration for {} already performed".format(directory)
					continue
				print "working on {}".format(directory)
				if not os.path.isdir(reg_dir):
					os.mkdir(reg_dir)
				else:
					shutil.rmtree(reg_dir)
				log_file = os.path.join(directory,'log_reg')
				mid_file =  os.path.join(directory,'mid_func.nii.gz')
				extract_mid = fsl.ExtractROI(in_file	= bold_file, 
							     roi_file	= mid_file,
							     t_min	= bold_length/2,
							     t_size	= 1)
				result = extract_mid.run()
#				cmd = 'mainfeatreg -F 6.00 -d {} -l {} -i {} -h {} -w BBR -x 90 > /dev/null'.format(directory,log_file,mid_file, brain_image)
				cmd = 'mainfeatreg -F 6.00 -d {} -l {} -i {} -h {} -w 6 -x 90  > /dev/null'.format(directory,log_file,mid_file, brain_image)
				subprocess.call(cmd,shell=True)


	def anatomical_registration(self, subject):
		print ">>> Anatomical registration"
		brain_image = subject.anatomical_brain_nii()
		reg_dir = os.path.join(subject.anatomical_dir(), 'reg')
		out_file = os.path.join(reg_dir, 'highres2standard.nii.gz')  
		out_mat_file = os.path.join(reg_dir, 'highres2standard.mat')  
		standard_image = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz') 
		
		if not os.path.isfile(out_mat_file):	
			print ">>> FLIRT"
			os.mkdir(reg_dir)
			flirt = fsl.FLIRT(in_file	 = brain_image, 
					  reference	 = standard_image, 
					  out_file 	 = out_file, 
					  out_matrix_file= out_mat_file, 
					  cost		 = 'corratio', 
					  dof		 = 12, 
					  searchr_x	 = [-90, 90], 
					  searchr_y	 = [-90, 90], 
					  searchr_z	 = [-90, 90], 
					  interp	 ='trilinear')
			flirt.run()
	
		#TODO: do this better: don't use restore hard-coded
		anatomical_head = os.path.join(subject.anatomical_dir(),'highres001_restore.nii.gz')
		output_fielf_coeff = os.path.join(reg_dir, 'highres2standard_warp.nii.gz')
		output_jacobian = os.path.join(reg_dir, 'highres2highres_jac')
		standard_head = fsl.Info.standard_image('MNI152_T1_2mm.nii.gz')
		standard_mask = fsl.Info.standard_image('MNI152_T1_2mm_brain_mask_dil.nii.gz')
		if not os.path.isfile(output_fielf_coeff):
			print ">>> FNIRT"
			fnirt = fsl.FNIRT(warped_file	 = out_file, 
					  in_file	 = anatomical_head, 
					  affine_file	 = out_mat_file, 
					  fieldcoeff_file= output_fielf_coeff, 
					  jacobian_file	 = output_jacobian, 
					  config_file	 = 'T1_2_MNI152_2mm', 
					  ref_file	 = standard_head, 
					  refmask_file	 = standard_mask)
			fnirt.run()
			cmd = 'fslview {} {} -t 0.5 '.format(standard_image,out_file)
			pro = subprocess.Popen(cmd, stdout=subprocess.PIPE,
			       shell=True, preexec_fn=os.setsid)

	def functional_segmentation(self,subject):
		print ">>> Functional Segmentation"
		for task, directories in subject.dir_tree('functional').iteritems():
			for directory in directories:
				run_name = directory.split('/')[-1]
				gm_mask_name = os.path.join(subject.masks_dir(),run_name,'grey.nii.gz')
				if os.path.isfile(gm_mask_name):
					continue
				bold_file = os.path.join(directory,'mid_func.nii.gz')
				out_basename = os.path.join(subject.masks_dir(),run_name,'seg')
				fast = fsl.FAST(in_files=bold_file, 
						out_basename=out_basename, 
						img_type=2, 
						number_classes=3, 
						hyper=0.1,
						output_biascorrected=True, 
						output_biasfield=True,
						bias_iters=5, 
						iters_afterbias=2,
						segments=True)
				try:
					result = fast.run()
					gm_pve_file = result.outputs.partial_volume_files[0]
				except:
					gm_pve_file = '{}_pve_0.nii.gz'.format(out_basename)
				try:
					os.rename(gm_pve_file,gm_mask_name)
				except:
					pass

	def segmentation(self, subject):
		print ">>> Segmentation"
        	gm_mask_name = os.path.join(subject.masks_dir(),'anatomy','grey.nii.gz')
        	if os.path.isfile(gm_mask_name):
			return
        	
		brain_image = os.path.join(subject.anatomical_dir(),"highres001_brain.nii.gz")
        	fast = fsl.FAST(in_files=brain_image, out_basename=os.path.join(subject.masks_dir(),'anatomy','seg'), img_type=1, number_classes=3, hyper=0.4,segments=True)

		try:
			result = fast.run()
			gm_pve_file = result.outputs.partial_volume_files[1]
		except:
			gm_pve_file = os.path.join(subject.masks_dir(),'anatomy','seg_pve_1.nii.gz')
			gm_seg_file = os.path.join(subject.masks_dir(),'anatomy','seg_seg_1.nii.gz')

			# TODO: bug in fast result output parsing!!!
		if False:
			cmd = 'fslview {} {} -l Red -t 0.1 -b 0,0.1'.format(brain_image,gm_pve_file)
			pro = subprocess.Popen(cmd, stdout=subprocess.PIPE,
				       shell=True, preexec_fn=os.setsid)
			thr = float(raw_input("Insert a GM thershold for the mask: default is 0\n")) or 0.0
			os.killpg(pro.pid,signal.SIGTERM)
			gen_mask = fsl.utils.ImageMaths(in_file=gm_pve_file,op_string = '-thr {} -bin'.format(thr), out_file=gm_mask_name)
			gen_mask.run()
		else:
			os.rename(gm_seg_file,gm_mask_name)


	def estimate_bias_field(self, subject):
		print ">>> Bias field estimation"

		anat_filename = os.path.join(subject.anatomical_dir(), 'highres001.nii.gz')
		restore_file = os.path.join(subject.anatomical_dir(), 'highres001_restore.nii.gz')

		if os.path.isfile(restore_file):
			return anat_filename

		try:
			fast = fsl.FAST(in_files=anat_filename, 
					out_basename=os.path.join(subject.anatomical_dir(), 'highres001'),
					bias_lowpass=10,
					output_biascorrected=True, 
					output_biasfield=True,
					img_type=1, 
					bias_iters=5, 
					no_pve=True, 
					iters_afterbias=1)

			fast = fast.run()

			# TODO need to remove temporary files created by this process	
			
			os.raname(anat_filename,anatfilename.replace('.nii.gz','_pre_restore.nii.gz'))
			shutil.copy(fast.outputs.image_restored,anat_filename)
			return anat_filename
		except:
			return restore_file

	def extract_brain(self, subject):
		# Check whether brain has already been extracted
		brain_image = os.path.join(subject.anatomical_dir(), 'highres001_brain.nii.gz')

		if os.path.isfile(brain_image):
			return

		# Estimate bias field
		input_image = self.estimate_bias_field(subject)

		print ">>> Brain Extraction"

		f = 0.5
		g = 0.1

		bet = fsl.BET(in_file=input_image, 
			      out_file=brain_image,
			      mask=True, 
			      robust=True, 
			      frac=f, 
			      vertical_gradient=g)

		result = bet.run()

		is_ok = 'n'
		while 'n' in is_ok:
			cmd = 'fslview {} {} -l Green'.format(input_image, result.outputs.out_file)
			pro = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

			is_ok = raw_input("Is this ok? [y]/n\n") or 'y'
			if 'n' in is_ok:
				bet.inputs.frac = float(raw_input("Set fraction: default is previous ({})\n".format(bet.inputs.frac)) or bet.inputs.frac)
				bet.inputs.vertical_gradient = float(raw_input("Set gradient: default is previous ({})\n".format(bet.inputs.vertical_gradient)) or bet.inputs.vertical_gradient)
				result = bet.run()
			os.killpg(pro.pid,signal.SIGTERM)
		os.rename(os.path.join(subject.anatomical_dir(),'highres001_brain_mask.nii.gz'),os.path.join(subject.masks_dir(),'anatomy','brain.nii.gz'))


	def __motion_correct_file__(self, input_file, output_file,subject,directory,use_example_pp=True):
		# Check whether motion correction has already been completed
		if os.path.isfile(output_file):
			return

		print "{}".format(input_file)
		
		if use_example_pp:
			pp.preproc.inputs.inputspec.func = input_file
			pp.preproc.inputs.inputspec.struct = os.path.join(subject.anatomical_dir(),'highres001.nii.gz')
			pp.preproc.base_dir = directory
			
			pp.preproc.run()
			# TODO: copy motion correction photos as well	
			intnorm_file = output_file.replace('.nii.gz','_intnorm.nii.gz')
			shutil.copy(os.path.join(directory,'preproc','intnorm','mapflow','_intnorm0','bold_dtype_mcf_mask_intnorm.nii.gz'),intnorm_file)
			shutil.copy(os.path.join(directory,'preproc','maskfunc2','mapflow','_maskfunc20','bold_dtype_mcf_mask.nii.gz'),output_file)
		else:
			mcflt = fsl.MCFLIRT(in_file=input_file, out_file=output_file, save_plots=True)
			result = mcflt.run()

			pmp = fsl.PlotMotionParams(in_file = result.outputs.par_file,in_source='fsl')

			pmp.inputs.plot_type = 'rotations'
			pmp.run()
			pmp.inputs.plot_type = 'translations'
			pmp.run()

	def motion_correction(self, subject, merge_task_runs=False):
		print ">>> Motion correction"

		# TODO: Make sure we skip this step if motion is already corrected (when merge is true)

		for task, directories in subject.dir_tree('functional').iteritems():
			if merge_task_runs and len(directories) > 1:
				# Merge the files before motion correction and then split back to single files.

				bold_files = [os.path.join(directory, 'bold.nii.gz') for directory in directories]
				mcf_files = [os.path.join(directory, 'bold_mcf.nii.gz') for directory in directories]
				if all(map(lambda x: os.path.isfile(x), mcf_files)):
					print ">>> Motion Correction has already been performed"
					continue

				merge_dir = os.path.join(subject.functional_dir(), 'temp_{}_merged'.format(task))
				if not os.path.isfile(merge_dir):
					
					os.mkdir(merge_dir)
					merge_file = os.path.join (merge_dir, 'bold.nii.gz'.format(task))
					mcf_merge_file = merge_file.replace('.nii.gz','_mcf.nii.gz')


				if not os.path.isfile(merge_file):
					merger = fsl.Merge()

					merger.inputs.in_files = bold_files
					merger.inputs.dimension = 't'
					merger.inputs.output_type = 'NIFTI_GZ'
					merger.inputs.merged_file = merge_file

					merger.run()

					self.__motion_correct_file__(merge_file, mcf_merge_file,subject,merge_dir)

				func_lengths = [nibabel.load(x).shape[3] for x in bold_files]
				split_dir = os.path.join(subject.functional_dir(), 'temp_split') + '/'

				if(not os.path.isfile(split_dir)):
					os.mkdir(split_dir)
					splitter = fsl.Split(in_file=mcf_merge_file,out_base_name=split_dir,dimension='t')
					result = splitter.run()
				
					split_dcms = sorted(result.outputs.out_files)
					idx = 0

					for mcf_file, run_length in zip(mcf_files, func_lengths):
						input_files = split_dcms[idx:idx+run_length]
						merge = fsl.Merge(in_files = input_files,
							  dimension='t',
							  output_type = 'NIFTI_GZ',
							  merged_file = mcf_file
							)
						merge.run()
						idx += run_length

				shutil.rmtree(split_dir)
			else:	
				# No need to merge the files..
				for directory in sorted(directories):
					input_file = os.path.join(directory, 'bold.nii.gz')
					output_file = input_file.replace('.nii.gz', '_mcf.nii.gz')

					self.__motion_correct_file__(input_file, output_file, subject,directory)


		
def test():
	fmri_data = OpenFMRIData('/home/user/data', '/home/user/data/raw', '/home/user/data/behavioural', 'LP')
	analyzer  = OpenFMRIAnalyzer(fmri_data, [1])

	print "{:<40s}{}".format("subjects_list", analyzer._subjects_list)

	analyzer.analyze(mc_merge=True)

if __name__ == "__main__":
	test()
		

