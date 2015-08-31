#!/usr/bin/python

import os
import nibabel
import shutil
import subprocess
import signal
import pre_proc_fromexample as pp
from SubjectDir import SubjectDir
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
                if(type(subject) is str):
                    self._subjects_list.append(self._fmri_data.load_subject_dir(subcode=subject))
                elif(type(subject) is SubjectDir):
                    self._subjects_list.append(subject)
                else:
                    raise BaseException("Invalid file type for {}".format(subject))
        else:
            pass # load all subjects

    def add_subject(self, subject_dir):
        self._subjects_list.append(subject_dir)

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
                anat_reg_dir = os.path.join(subject.anatomical_dir(),'reg')
                highres2mni_mat = os.path.join(anat_reg_dir,'highres2standard.mat')
                highres2standard_warp = os.path.join(anat_reg_dir,'highres2standard_warp.nii.gz')
                example_func2highres_mat = os.path.join(reg_dir,'example_func2highres.mat')
                example_func2standard_warp = os.path.join(reg_dir,'example_func2standard_warp.nii.gz')

                standard_image = fsl.Info.standard_image('MNI152_T1_2mm_brain.nii.gz')
                convert_warp = fsl.utils.ConvertWarp(reference = standard_image,
                                   premat   = example_func2highres_mat,
                                   warp1     = highres2standard_warp,
                                   out_file  = example_func2standard_warp)
                convert_warp.run()
                apply_warp = fsl.preprocess.ApplyWarp(ref_file   = standard_image,
                                      in_file    = mid_file,
                                      field_file = example_func2standard_warp,
                                      out_file   = os.path.join(reg_dir,'example_func2standard.nii.gz' ))
                apply_warp.run()


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

        anatomical_head = os.path.join(subject.anatomical_dir(),'highres001.nii.gz')
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


    def estimate_bias_field(self, subject, overwrite = False):
        """
            Bias field estimation
             - Before running FAST an image of a head should first be brain-extracted, using BET. The resulting brain-only image can then be fed into FAST.

            Parameters
                subject = Subject Dir object
                overwrite = False

            Returns:
                Path to 'highres001.nii.gz' file
        """

        print(">>> Bias field estimation")

        anat_filename = os.path.join(subject.anatomical_dir(), 'highres001_brain.nii.gz')
        #anat_filename = os.path.join(subject.anatomical_dir(), 'highres001.nii.gz')
        restore_file = os.path.join(subject.anatomical_dir(), 'highres001_restore.nii.gz')

        if not overwrite and os.path.isfile(restore_file):
            print(">>>> Skipped")
            return anat_filename

        try:
            fast = fsl.FAST(in_files=anat_filename,
                    out_basename=os.path.join(subject.anatomical_dir(), 'highres001'),
                    bias_lowpass=10, # bias field smoothing extent (FWHM) in mm
                    output_biascorrected=True, # output restored image (bias-corrected image)
                    output_biasfield=True, # output estimated bias field
                    img_type=1, #T1
                    bias_iters=5, # number of main-loop iterations during bias-field removal
                    no_pve=True, # turn off PVE (partial volume estimation)
                    iters_afterbias=1) # number of main-loop iterations after bias-field removal

            fast = fast.run()

            # TODO need to remove temporary files created by this process

            os.rename(anat_filename,anat_filename.replace('.nii.gz','_pre_restore.nii.gz'))
            shutil.copy(fast.outputs.image_restored,anat_filename)
            return anat_filename
        except Exception as ex:
            print ex
            os.rename(anat_filename,anat_filename.replace('.nii.gz','_pre_restore.nii.gz'))
            shutil.copy(restore_file, anat_filename)
            return anat_filename

    def extract_brain(self, subject, overwrite = False, f=0.5, g=-0.1):
        """
            Brain Extraction
                - Creates 'mask/anatomy/brain.nii.gz'
                - Creates 'anatomy/highres001_bias.nii.gz', 'highres001_brain.nii.gz'

            Parameters
                subject = Subject Dir object
                overwrite = States whether or not to overwrite the image
                f = fractional intensity threshold
                g = vertical gradient in fractional intensity threshold (-1, 1)
        """
        print ">>> Brain Extraction"

        #Check whether brain has already been extracted
        brain_image = os.path.join(subject.anatomical_dir(), 'highres001_brain.nii.gz')

        if not overwrite and os.path.isfile(brain_image):
            print(">>>> Skipped")
            return

        input_image = os.path.join(subject.anatomical_dir(), 'highres001.nii.gz')

        # Estimate bias field
        #input_image = self.estimate_bias_field(subject) # TODO - in http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST it says that The resulting brain-only image(from bet) can then be fed into FAST.

        bet = fsl.BET(in_file=input_image,
                  out_file=brain_image,
                  mask=True, # create binary mask image
                  robust=True, # robust brain centre estimation (iterates BET several times)
                  frac=f, # fractional intensity threshold
                  vertical_gradient=g) # vertical gradient in fractional intensity threshold (-1, 1)

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

        # Saves the anatomical brain after mask to the mask directory
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
            cmd = "eog {}".format(os.path.join(directory,'preproc','realign','mapflow','_realign0','bold_dtype_mcf.nii.gz_rot.png'))
            subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
            cmd = "eog {}".format(os.path.join(directory,'preproc','realign','mapflow','_realign0','bold_dtype_mcf.nii.gz_trans.png'))
            subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)

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
                intnorm_files = [os.path.join(directory, 'bold_mcf_intnorm.nii.gz') for directory in directories]
                if all(map(lambda x: os.path.isfile(x), mcf_files)):
                    print ">>> Motion Correction has already been performed"
                    continue

                merge_dir = os.path.join(subject.functional_dir(), 'temp_{}_merged'.format(task))
                merge_file = os.path.join (merge_dir, 'bold.nii.gz'.format(task))
                mcf_merge_file = merge_file.replace('.nii.gz','_mcf.nii.gz')
                intnorm_merge_file = mcf_merge_file.replace('.nii.gz','_intnorm.nii.gz')
                if not os.path.isdir(merge_dir):

                    os.mkdir(merge_dir)


                if not os.path.isfile(merge_file):
                    merger = fsl.Merge()

                    merger.inputs.in_files = bold_files
                    merger.inputs.dimension = 't'
                    merger.inputs.output_type = 'NIFTI_GZ'
                    merger.inputs.merged_file = merge_file

                    merger.run()
                    self.__motion_correct_file__(merge_file, mcf_merge_file,subject,merge_dir)

                func_lengths = [nibabel.load(x).shape[3] for x in bold_files]
                for output_merge_file,output_files in zip([mcf_merge_file,intnorm_merge_file],[mcf_files,intnorm_files]):
                    split_dir = os.path.join(subject.functional_dir(), 'temp_split') + '/'
                    if(not os.path.isfile(split_dir)):
                        os.mkdir(split_dir)
                        splitter = fsl.Split(in_file       = output_merge_file,
                                     out_base_name = split_dir,
                                                                     dimension     = 't')
                        result = splitter.run()

                        split_dcms = sorted(result.outputs.out_files)
                        idx = 0

                        for out_file, run_length in zip(output_files, func_lengths):
                            input_files = split_dcms[idx:idx+run_length]
                            merge = fsl.Merge(in_files = input_files,
                                      dimension='t',
                                      output_type = 'NIFTI_GZ',
                                      merged_file = out_file)
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