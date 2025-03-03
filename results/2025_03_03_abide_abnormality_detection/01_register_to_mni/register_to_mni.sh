#!/bin/bash
#SBATCH --job-name=register_MNI_array  # SLURM job name
#SBATCH --output=register_MNI_%A_%a.out  # Log file per array job
#SBATCH --time=0:10:00                 # Time limit per task
#SBATCH --cpus-per-task=1              # CPU cores per task
#SBATCH --mem=8gb                     # Memory per task
#SBATCH --array=0-1036                # Job array: 100 jobs (modify as needed)
#SBATCH --error=register_MNI_%A_%a.err  # Log file per array job

# -----------------------------------------------------------------------------
# This script registers fMRI images to MNI space using SLURM job arrays.
# Each array task processes a different file in parallel.
#
# 1. Create a file list before submitting:
#    find /blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_preprocessed -name "*func_preproc.nii.gz" > file_list.txt
# 2. Submit the job with sbatch:
#    sbatch --array=0-$(($(wc -l < file_list.txt) - 1))%10 register_to_MNI_array.slurm
# -----------------------------------------------------------------------------

module load fsl  # Load FSL on HiPerGator

# Exit immediately if a command exits with a non-zero status
set -e

# Paths
IN_LIST="file_list.txt"  # Text file containing input file paths
OUT_DIR="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_MNI_2mm"
REF_PATH="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/tpl-MNI152NLin6Asym_res-02_T1w.nii.gz"
APPLY_ISO_XFM="2"

# Read the file corresponding to this SLURM_ARRAY_TASK_ID
in_file=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${IN_LIST}")

# Check if file exists
if [[ ! -f "$in_file" ]]; then
    echo "No valid file at index ${SLURM_ARRAY_TASK_ID}."
    exit 1
fi

# Extract filename (removing "_func_preproc.nii.gz")
file_base_name=$(basename "${in_file}" "_func_preproc.nii.gz")

# Define output file path
out_file="${OUT_DIR}/${file_base_name}_MNI_2mm.nii.gz"

echo "-------------------------------------------------"
echo "Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Registering: ${in_file}"
echo "Output will be: ${out_file}"

# Run FLIRT registration
flirt -in "${in_file}" \
      -ref "${REF_PATH}" \
      -out "${out_file}" \
      -applyisoxfm "${APPLY_ISO_XFM}"

echo "Finished registering ${in_file}"

