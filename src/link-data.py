import os
import glob
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create symlinks to all fastq\'s in a sequencing directory. Just specify where the sequencing run is located relative to the current directory and we\'ll handle the rest!')
    parser.add_argument('in_dir',
                        type=str,
                        help='path to sequencing run (or stdin if none)')
    args = parser.parse_args()

    # dump links in to a fold with the run id
    in_dir = args.in_dir.rstrip('/')
    out_dir = './' + in_dir.split('/')[-1]
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    # prepend extra '../' to relative paths
    fastqs = glob.iglob(in_dir + '/Data/Intensities/BaseCalls/*.fastq*')
    if in_dir[:2] == '..':
        sample_sheet = '../' + in_dir + '/SampleSheet.csv'
        if os.path.exists(sample_sheet):
            os.symlink(sample_sheet, out_dir + '/SampleSheet.csv')
        for file in fastqs:
            fastq_name = file.split('/')[-1]
            os.symlink('../' + file, out_dir + '/' + fastq_name)
    else:
        sample_sheet = in_dir + '/SampleSheet.csv'
        if os.path.exists(sample_sheet):
            os.symlink(sample_sheet, out_dir + '/SampleSheet.csv')
        for file in fastqs:
            fastq_name = file.split('/')[-1]
            os.symlink(file, out_dir + '/' + fastq_name)
