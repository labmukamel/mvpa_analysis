__author__ = 'roee'
from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces.fsl.model import Level1Design, FEATModel
import nipype.interfaces.fsl as fsl
import os
from glob import glob

class createFirstLevel:

    def runglmperun(self, subject, trtimeinsec):
        s = SpecifyModel()
        # loop on all runs and models within each run
        modelfiles = subject._modelfiles

        for model in modelfiles:
            s.inputs.event_files = model[2]
            s.inputs.input_units = 'secs'
            s.inputs.functional_runs = os.path.join(subject._path,'BOLD',model[1], 'bold_mcf.nii.gz')
            # use nibable to get the tr of from the .nii file
            s.inputs.time_repetition = trtimeinsec
            s.inputs.high_pass_filter_cutoff = 128.
            # find par file that has motion
            motionfiles = glob(os.path.join(subject._path, 'BOLD', model[1], "*.par"))
            s.inputs.realignment_parameters = motionfiles
            #info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]],                      durations=[[1]]),                 Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]],                       durations=[[1]])]
            #s.inputs.subject_info = None

            res = s.run()
            print ">>>> preparing evs for model " + model[1] + "and run " + model[0]
            sessionInfo = res.outputs.session_info

            level1design = Level1Design()
            level1design.inputs.interscan_interval = trtimeinsec
            level1design.inputs.bases = {'dgamma':{'derivs': False}}
            level1design.inputs.session_info = sessionInfo
            level1design.inputs.model_serial_correlations = True
            resLevel = level1design.run()

            featModel = FEATModel()
            featModel.inputs.fsf_file = resLevel.outputs.fsf_files
            featModel.inputs.ev_files = resLevel.outputs.ev_files
            resFeat = featModel.run()

            print ">>>> creating fsf design files for  " + model[1] + "and run " + model[0]
            # TODO: give mask here
            glm = fsl.GLM(in_file=s.inputs.functional_runs[0], design=resFeat.outputs.design_file, output_type='NIFTI')

            print ">>>> running glm for  " + model[1] + "and run " + model[0]
            resGlm = glm.run()

            print ">>>> finished running  glm for  " + model[1] + "and run " + model[0]