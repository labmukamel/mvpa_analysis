__author__ = 'roee'
from nipype.algorithms.modelgen import SpecifyModel
from nipype.interfaces.fsl.model import Level1Design, FEATModel
import nipype.interfaces.fsl as fsl

s = SpecifyModel()
s.inputs.event_files = ['/home/roee/code/mvpa_analysis/evs_test/self1.run001.txt', '/home/roee/code/mvpa_analysis/evs_test/self2.run001.txt']
s.inputs.input_units = 'secs'
s.inputs.functional_runs = ['/media/roee/fMRI/Data/Self-Other/sub001/BOLD/task001_run001/bold_mcf.nii.gz']
s.inputs.time_repetition = 6
s.inputs.high_pass_filter_cutoff = 128.
s.inputs.realignment_parameters = ['/media/roee/fMRI/Data/Self-Other/sub001/BOLD/task001_run001/bold_mcf.nii.gz.par']
#info = [Bunch(conditions=['cond1'], onsets=[[2, 50, 100, 180]],                      durations=[[1]]),                 Bunch(conditions=['cond1'], onsets=[[30, 40, 100, 150]],                       durations=[[1]])]
#s.inputs.subject_info = None

res = s.run()
sessionInfo = res.outputs.session_info

level1design = Level1Design()
level1design.inputs.interscan_interval = 2.5
level1design.inputs.bases = {'dgamma':{'derivs': False}}
level1design.inputs.session_info = sessionInfo
level1design.inputs.model_serial_correlations = False
resLevel = level1design.run()

featModel = FEATModel()
featModel.inputs.fsf_file = resLevel.outputs.fsf_files
featModel.inputs.ev_files = resLevel.outputs.ev_files
resFeat = featModel.run()

glm = fsl.GLM(in_file=s.inputs.functional_runs[0], design=resFeat.outputs.design_file, output_type='NIFTI',mask = '')

resGlm = glm.run()

print "End"