#!/bin/bash
#SBATCH --job-name=register_to_MNI    # (Optional) SLURM job name
#SBATCH --output=register_to_MNI_%j.log  # (Optional) SLURM log file name
#SBATCH --time=02:00:00              # (Optional) time limit hh:mm:ss
#SBATCH --cpus-per-task=1            # (Optional) number of CPU cores
#SBATCH --mem=4gb                    # (Optional) memory per CPU core
#SBATCH --mail-type=ALL              # (Optional) email events (BEGIN, END, FAIL)
#SBATCH --mail-user=your_email@ufl.edu # (Optional) email address

# -----------------------------------------------------------------------------
# This script searches for files ending in "*filtered_func_data_clean.nii.gz"
# under a given directory structure and registers them to an MNI template
# using FSL's flirt command.
#
# Each output is saved in the SAME folder as the input file. That is, if the
# input file is located in /path/to/subjectX/fMRI/rfMRI.ica/filtered_func_data_clean.nii.gz,
# the output (filtered_func_data_clean_MNI.nii.gz) will also appear in that rfMRI.ica folder.
#
# Make sure you have loaded an appropriate FSL module on Hipergator before running:
#   module load fsl
# or load it within the script if needed.
# -----------------------------------------------------------------------------

# Exit immediately if a command exits with a non-zero status
set -e

# Path to directory containing the subfolders with *filtered_func_data_clean.nii.gz files
IN_DIR="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/UKB/brain"

# Reference MNI template (2 mm) from FSL or your custom path
REF_PATH="/orange/ruogu.fang/zeyun.zhao/FSL/bb_FSL/data/standard/tpl-MNI152NLin6Asym_res-02_T1w.nii.gz"

# Desired isotropic voxel size in mm as a string (e.g., "2")
APPLY_ISO_XFM="2"

# Optionally load FSL module (if needed):
# module load fsl

echo "Starting registration for all matching files under: ${IN_DIR}"
echo "Using reference: ${REF_PATH}"
echo "Applying iso xfm: ${APPLY_ISO_XFM}"
echo

# Loop through each file matching the wildcard pattern
for in_file in "${IN_DIR}"/*/*/*unzip/*/fMRI/rfMRI.ica/filtered_func_data_clean.nii.gz; do
    
    # If the glob doesn't match any files, skip
    if [[ ! -e "$in_file" ]]; then
        echo "No matching files found in ${IN_DIR}."
        break
    fi

    # Extract the directory in which this file resides
    in_dir=$(dirname "${in_file}")

    # Define output file in the same folder
    out_file="${in_dir}/filtered_func_data_clean_MNI.nii.gz"

    echo "-------------------------------------------------"
    echo "Registering: ${in_file}"
    echo "Output will be: ${out_file}"
    
    # Run the flirt registration
    flirt -in "${in_file}" \
          -ref "${REF_PATH}" \
          -out "${out_file}" \
          -applyisoxfm "${APPLY_ISO_XFM}"
    
    echo "Finished registering ${in_file}"
done

echo "All registrations completed (if any files were found)."