#!/usr/bin/env bash
# TEMPLATE: manager must fill account/partition/paths and obtain exact policy review.
#SBATCH --job-name=wagers-myotally-control
#SBATCH --account=REQUIRED_ACCOUNT
#SBATCH --partition=REQUIRED_PARTITION
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:20:00
# No GPUs. Submit from an approved persistent evidence directory for Slurm logs.
set -euo pipefail
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
module load python
bash REQUIRED_ABSOLUTE_ONBOARDING_DIR/scripts/bootstrap.sh REQUIRED_ABSOLUTE_DEPLOY_CONFIG
module use REQUIRED_ABSOLUTE_MODULE_ROOT
module load wagers-myotally/1.0.2-env001
wagers-myotally doctor
wagers-myotally validate-one --evidence-dir REQUIRED_NEW_ABSOLUTE_EVIDENCE_DIR
