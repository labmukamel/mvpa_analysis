#!/usr/bin/python
import sys
import os

from OpenFMRIAnalyzer import OpenFMRIAnalyzer
from OpenFMRIData import OpenFMRIData

#subname    	= sys.argv[1]

data_dir   	= os.environ.get('DATA_DIR') or '/media/lior/DAE86CF0E86CCBF7/Data/data'
study_name 	= os.environ.get('STUDY_NAME') or 'EPITest'

raw_dir 	= os.path.join(data_dir,'raw')
behavioural_dir = os.path.join(data_dir,'behavioural')

#Specific for Roni
def create_evs(subjectdir, onset_dirs,behavioural_path):
    import os
    from glob import glob
    import pandas as pd


    for file_regex, task_sequence in subjectdir._task_mapping.iteritems():

        run_files = sorted(glob(os.path.join(behavioural_path, '{}*.csv'.format(file_regex))))
        ### From here on out this function is specific to my experiment. parsing logs from psychopy
        print "{}->{}".format(file_regex, run_files)
        for run_number,run_file in enumerate(run_files):
            df = pd.read_csv(run_file)
            conds = {}

            if 'keyPressed' in df.columns:
                conds['catch'] = df[df.keyPressed.notnull()]
                df = df[-(df.stim1.str.contains('atch') | df.stim2.str.contains('atch') | df.stim3.str.contains('atch')| df.stim4.str.contains('atch')) & df.keyPressed.isnull()]

            df['cond'] = df.stim1.str.split('\\').str[1]
            conds.update(dict((cond,df[df.cond.eq(cond)]) for cond in df.cond.unique()))
            for condition_number, key in enumerate(sorted(conds.keys())):
                value = conds[key]
                col_idx = df.columns.get_loc("start stim")
                value = value.ix[:,col_idx:col_idx+1]
                value['onset'] = value['start stim'].astype(int)
                if 'MVPA' in run_file:
                    value['duration'] = 4
                    # TODO: Replace this shit!
                else:
                    value['duration'] = 12
                    # TODO: Replace this shit!

                value['weight'] = 1
                conds[key] = value

                #run_name = "{}_run{:0>3d}".format(task_sequence, run_number+1)
                condition_name = "cond{:0>3d}.txt".format(condition_number+1)
                print ">>> condition mapping: {}->{}".format(key,condition_number)
                for onset_dir in onset_dirs:
                    value.to_csv(os.path.join(subjectdir.model_dir(), onset_dir, task_sequence, condition_name), sep='\t',index=False,header=False)

op = OpenFMRIData(data_dir, raw_dir,study_name)

#subject_names = ['MoCa'] # Specific subject names
subject_names = op.get_subject_names() # All subjects

for name in subject_names:
    subject_dir = op.load_subject_dir(subname=name,create_behav_dict = {'func': create_evs, 'behav': os.path.join(behavioural_dir,study_name,name)})
    # if we want to create new data for analysis
    # subject_dir = op.create_subject_dir(name)
    analyzer = OpenFMRIAnalyzer(op,[subject_dir])
    analyzer.analyze(mc_merge=True)

