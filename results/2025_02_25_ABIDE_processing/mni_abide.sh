#!/bin/bash
#SBATCH --job-name=register_to_MNI    # (Optional) SLURM job name
#SBATCH --output=register_to_MNI_%j.log  # (Optional) SLURM log file name
#SBATCH --time=6:00:00              # (Optional) time limit hh:mm:ss
#SBATCH --cpus-per-task=2            # (Optional) number of CPU cores
#SBATCH --mem=64gb                    # (Optional) memory per CPU core
#SBATCH --mail-type=ALL              # (Optional) email events (BEGIN, END, FAIL)
#SBATCH --output=mni_abide.out 
#SBATCH --error=mni_abide.err

# -----------------------------------------------------------------------------
# This script searches for files ending in "*func_preproc.nii.gz"
# under a given directory structure and registers them to an MNI template
# using FSL's flirt command.
#
# Each output is saved in the specified OUT_DIR with a cleaned-up filename.
#
# Make sure you have loaded an appropriate FSL module on Hipergator before running:
#   module load fsl
# -----------------------------------------------------------------------------

module load fsl

# Exit immediately if a command exits with a non-zero status
set -e

# Path to directory containing input *func_preproc.nii.gz files
IN_DIR="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_preprocessed"

# Output directory
OUT_DIR="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_MNI"

# Reference MNI template (2 mm) from FSL or your custom path
REF_PATH="/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/tpl-MNI152NLin6Asym_res-02_T1w.nii.gz"

# Desired isotropic voxel size in mm as a string (e.g., "2")
APPLY_ISO_XFM="3"

echo "Starting registration for all matching files under: ${IN_DIR}"
echo "Using reference: ${REF_PATH}"
echo "Applying iso xfm: ${APPLY_ISO_XFM}"
echo

# Loop through each file matching the wildcard pattern
for in_file in "${IN_DIR}"/*func_preproc.nii.gz; do
    
    # If no matching files exist, skip
    if [[ ! -e "$in_file" ]]; then
        echo "No matching files found in ${IN_DIR}."
        break
    fi

    # Extract the base filename (Remove "_func_preproc.nii.gz")
    file_base_name=$(basename "${in_file}" "_func_preproc.nii.gz")

    # Define output file in the specified OUT_DIR
    out_file="${OUT_DIR}/${file_base_name}_MNI.nii.gz"

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