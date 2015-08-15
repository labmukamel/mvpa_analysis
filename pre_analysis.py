import sys
import os

from OpenFMRIData import OpenFMRIData
from OpenFMRIAnalyzer import OpenFMRIAnalyzer

subname    	= sys.argv[1]
data_dir   	= os.environ.get('DATA_DIR') or '/home/user/data'
study_name 	= os.environ.get('STUDY_NAME') or 'LP'

raw_dir 	= os.path.join(data_dir,'raw')
behavioural_dir = os.path.join(data_dir,'behavioural')

op = OpenFMRIData(data_dir, raw_dir, behavioural_dir,study_name)
subject_dir = op.subject_dir(subname=subname)
analyzer = OpenFMRIAnalyzer(op,[subject_dir.subcode()])
analyzer.analyze(mc_merge=True)

