#!/bin/bash
##Useful template for running long jobs on lilac
#BSUB -J {calculation_name}
#BSUB -n 1
#BSUB -R rusage[mem={memory}]
#BSUB -R span[hosts=1]
#BSUB -q gpuqueue
#BSUB -gpu num=1:j_exclusive=yes:mode=shared
#BSUB -W  {wallclock_time}
#BSUB -We {estimated_time}
#BSUB -o %J.stdout
#BSUB -eo %J.stderr
#BSUB -L /bin/bash

# quit on first error
set -e

# Change to working directory used for job submission
cd $LS_SUBCWD

# Launch my program.
module load cuda/9.0
python {path_to_setup_script} {yaml_filename}