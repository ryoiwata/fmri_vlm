#!/bin/bash
#SBATCH --job-name=smooth_MNI_array  # SLURM job name
#SBATCH --output=smooth_MNI_%A_%a.out  # Log file per array job
#SBATCH --time=0:10:00                 # Time limit per task
#SBATCH --cpus-per-task=1              # CPU cores per task
#SBATCH --mem=8gb                      # Memory per task
#SBATCH --array=0-1036                 # Job array: Adjust range as needed
#SBATCH --error=smooth_MNI_%A_%a.err  # Log file per array job

# -----------------------------------------------------------------------------
# This script applies Gaussian smoothing (FWHM = 6mm) to fMRI images in MNI space
# using SLURM job arrays. Each array task processes a different file in parallel.
#
# 1. Create a file list before submitting:
#    find /blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_MNI -name "*MNI.nii.gz" > file_list.txt
# 2. Submit the job with sbatch:
#    sbatch --array=0-$(($(wc -l < file_list.txt) - 1))%10 smooth_MNI_array.slurm
# -----------------------------------------------------------------------------

module load fsl  # Load FSL on HiPerGator

# Exit immediately if a command exits with a non-zero status
set -e

# Paths
IN_LIST="file_list.txt"  # Text file containing input file paths
OUT_DIR="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_MNI_SMOOTH"

# Ensure output directory exists
mkdir -p "${OUT_DIR}"

# Read the file corresponding to this SLURM_ARRAY_TASK_ID (adjust indexing)
in_file=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${IN_LIST}")

# Check if file exists
if [[ ! -f "$in_file" ]]; then
    echo "No valid file at index ${SLURM_ARRAY_TASK_ID}: ${in_file}"
    exit 1
fi

# Extract filename (removing "_MNI.nii.gz")
file_base_name=$(basename "${in_file}" "_MNI.nii.gz")

# Define smoothed output file path
smoothed_out_file="${OUT_DIR}/${file_base_name}_MNI_smoothed.nii.gz"

echo "-------------------------------------------------"
echo "Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Smoothing: ${in_file}"
echo "Smoothed output will be: ${smoothed_out_file}"

# Apply Gaussian smoothing (FWHM = 6mm)
fslmaths "${in_file}" -s 2.55 "${smoothed_out_file}"

echo "Finished smoothing ${in_file}"