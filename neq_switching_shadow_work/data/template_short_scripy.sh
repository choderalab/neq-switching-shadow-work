#!/bin/bash
##This is a template for running short (less than 6 hour) jobs on lilac
#BSUB -J {calculation_name}
#BSUB -n 1
#BSUB -R rusage[mem={memory}]
#BSUB -R span[hosts=1]
#BSUB -q gpuqueue
#BSUB -gpu num=1:j_exclusive=yes:mode=shared
#BSUB -W  {wallclock_time}
#BSUB -We {estimated_time}
#BSUB -m "ls-gpu lt-gpu lp-gpu lg-gpu"
#BSUB -o %J.stdout
#BSUB -eo %J.stderr
#BSUB -L /bin/bash

# quit on first error
set -e

# copy input files to scratch for working
#cp -r $LS_SUBCWD/* .

cd $LS_SUBCWD

# Launch my program.
module load cuda/9.0
python {path_to_setup_script} {yaml_filename}