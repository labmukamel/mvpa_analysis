import scipy.io
import glob

targetFolder = ''
run = ''
behavPath = glob.glob("{}{}*{}".format(targetFolder, 'task001_', run + '/'))[0]
behavFile = open("{}{}".format(behavPath, 'behavdata.txt'), "w")
behavFile.read("{}\t{}\t{}\n".format('Onset', 'StimVar', 'Condition'))