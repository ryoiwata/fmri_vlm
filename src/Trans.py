#!/usr/bin/env python3
"""
Refactor Example: Convert a set of subject data folders into a minimal BIDS structure.

This script iterates over folders in 'input_dir'. For each subject:
  1) Determines the subject ID from the folder name.
  2) Creates BIDS-like directories (anat, func) under 'output_dir/<subject_id>'.
  3) Copies the subject's T1-weighted image and resting-state fMRI data into the correct BIDS paths.
  4) Copies a corresponding JSON sidecar (if present).

Author: [Your Name]
Date: [Optional: YYYY-MM-DD]
"""

import os
import shutil
import json
from ipdb import set_trace

# Input: Directory with subject subfolders (each containing <subject_id>_T1w.nii.gz, etc.)
INPUT_DIR = "/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/my_dataset"
# Output: Base directory where BIDS structure will be created
OUTPUT_DIR = "/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/bids_try"


def create_bids_structure(subject_id):
    """
    Create minimal BIDS-like directories for a single subject.

    This function ensures 'anat' and 'func' subdirectories exist for the subject.

    Args:
        subject_id (str): The subject identifier (e.g., '01').
    """
    anat_dir = os.path.join(OUTPUT_DIR, f"{subject_id}", "anat")
    func_dir = os.path.join(OUTPUT_DIR, f"{subject_id}", "func")

    os.makedirs(anat_dir, exist_ok=True)
    os.makedirs(func_dir, exist_ok=True)


def convert_to_bids(subject_dir, subject_id):
    """
    Convert a single subject's data into a BIDS-like structure.

    Copies T1-weighted and resting BOLD data (plus optional JSON metadata) from the subject directory
    to the newly created BIDS directories under OUTPUT_DIR.

    Args:
        subject_dir (str): Path to the subject's original data folder.
        subject_id (str): Unique subject identifier (e.g., '01') derived from the folder name.
    """
    # Create BIDS directories (anat, func)
    create_bids_structure(subject_id)

    # Debug if needed
    # set_trace()

    # Copy T1-weighted data
    t1_src = os.path.join(subject_dir, f"{subject_id}_T1w.nii.gz")
    t1_dest = os.path.join(OUTPUT_DIR, subject_id, "anat", f"{subject_id}_T1w.nii.gz")
    shutil.copy(t1_src, t1_dest)

    # Copy resting BOLD data
    bold_src = os.path.join(subject_dir, f"{subject_id}_rest_bold.nii.gz")
    bold_dest = os.path.join(OUTPUT_DIR, subject_id, "func", f"{subject_id}_rest_bold.nii.gz")
    shutil.copy(bold_src, bold_dest)

    # Copy JSON sidecar if it exists
    info_file = os.path.join(subject_dir, f"{subject_id}_rest_bold.json")
    if os.path.exists(info_file):
        with open(info_file, "r") as f:
            info = json.load(f)

        json_output_path = os.path.join(OUTPUT_DIR, subject_id, "func", f"{subject_id}_rest_bold.json")
        with open(json_output_path, "w") as f:
            json.dump(info, f, indent=4)


def main():
    """
    Main loop: traverse 'INPUT_DIR', identify subject folders, and convert each to BIDS format.

    The subject ID is extracted from the folder name by splitting on underscores
    and taking the last element. For example, a directory named 'sub_01'
    yields a subject_id of '01'.
    """
    for subject in os.listdir(INPUT_DIR):
        subject_dir = os.path.join(INPUT_DIR, subject)
        if os.path.isdir(subject_dir):
            # Example extraction of subject ID from folder name
            subject_id = subject.split("_")[-1]
            convert_to_bids(subject_dir, subject_id)


if __name__ == "__main__":
    main()
