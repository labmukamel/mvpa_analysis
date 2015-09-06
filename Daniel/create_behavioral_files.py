import scipy.io
import glob

def create_behavioral_files(subjectsFolder,subjectName):
    restDur = 8
    trialDur = 6
    files = glob.glob("{}{}{}*".format(subjectsFolder, subjectName, 'run'))
    for file in sorted(files):
        mat = scipy.io.loadmat(file)['data1sub'][1:, 0:3]  # load only the trial number,modality and active/passive
        trial = []
        condition = []
        run = file[-5]
        behavPath = glob.glob("{}{}*{}".format(targetFolder, 'task001_', run + '/'))[0]
        behavFile = open("{}{}".format(behavPath, 'behavdata.txt'), "w")
        behavFile.write("{}\t{}\t{}\n".format('Onset', 'StimVar', 'Condition'))
        for row in range(mat.shape[0]):
            trial.append(mat[row, 0].item())
            behavFile.write("{}\t".format(str(4 + (row + 1) * restDur + ((row + 1) - 1) * trialDur)))
            if mat[row, 1].item() == 0 and str(mat[row, 2].item()) == 'active':
                condition.append('auditory active')
                behavFile.write("{}\t{}\n".format('1', condition[row]))
            elif mat[row, 1].item() == 0 and str(mat[row, 2].item()) == 'passive':
                condition.append('auditory passive')
                behavFile.write("{}\t{}\n".format('2', condition[row]))
            elif mat[row, 1].item() == 1 and str(mat[row, 2].item()) == 'active':
                condition.append('visual active')
                behavFile.write("{}\t{}\n".format('3', condition[row]))
            elif mat[row, 1].item() == 1 and str(mat[row, 2].item()) == 'passive':
                condition.append('visual passive')
                behavFile.write("{}\t{}\n".format('4', condition[row]))
            else:
                condition.append('oddball')
                behavFile.write("{}\t{}\n".format('5', condition[row]))
        behavFile.close()


create_behavioral_files()

def test():
    subjectName    = 'Karin'
    subjectsFolder = '/home/daniel/fsl-analysis/behavioral/'
    targetFolder = '/home/daniel/fsl-analysis/data/behavioral/'

if __name__ == "__main__":
    test()













