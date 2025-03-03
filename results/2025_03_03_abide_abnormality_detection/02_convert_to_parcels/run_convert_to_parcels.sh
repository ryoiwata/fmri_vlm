#!/bin/bash
#SBATCH --job-name=register_MNI_array   # SLURM job name
#SBATCH --output=register_MNI_%A_%a.out # Log file per array job
#SBATCH --time=0:10:00                  # Time limit per task
#SBATCH --cpus-per-task=1
#SBATCH --mem=8gb
#SBATCH --array=0-1036                  # Job array size
#SBATCH --error=register_MNI_%A_%a.err  # Error log

# -----------------------------------------------------------------------------
# This script:
#  1) Reads a line from "file_list.txt", each line is an fMRI file.
#  2) Registers that fMRI to MNI with FLIRT, producing _MNI_2mm.nii.gz
#  3) Calls the "segment_single_fMRI.py" to do atlas-based parcellation
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Each array task processes a different file in parallel.
#
# 1. Create a file list before submitting:
#    find /blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_MNI_2mm/ -name "*.nii.gz" > file_list.txt
# 2. Submit the job with sbatch:
#    sbatch --array=0-$(($(wc -l < file_list.txt) - 1))%10 register_to_MNI_array.slurm
# -----------------------------------------------------------------------------


module load conda  # or your own conda environment with nibabel, etc.

conda activate /blue/ruogu.fang/ryoi360/projects/fmri_vlm/bin/conda/nibabel_env

set -e  # stop on error

# Input text file with list of .nii.gz paths
IN_LIST="file_list.txt"

# Atlas info for the python script
ATLAS_PATH="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/AAL3.nii.gz"
N_PARCELS="166"

# Directory for final .dat outputs after segmentation
PARCEL_OUT_DIR="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_parcelled"

# Get the input file from file_list
in_file=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${IN_LIST}")
if [[ ! -f "$in_file" ]]; then
    echo "No valid file for SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"
    exit 1
fi

echo "-------------------------------------------------"
echo "SLURM task ID  = ${SLURM_ARRAY_TASK_ID}"
echo "Input file     = ${in_file}"

# (2) Now run the python script on this newly created file
# passing e.g. --fmri_file and --atlas_path, etc.

python segment_single_fMRI.py \
    --fmri_file "${in_file}" \
    --atlas_path "${ATLAS_PATH}" \
    --n_parcels "${N_PARCELS}" \
    --out_dir "${PARCEL_OUT_DIR}"

echo "Parcellation done. Output is in: ${PARCEL_OUT_DIR}"
echo "-------------------------------------------------"
