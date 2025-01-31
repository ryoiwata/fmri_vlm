#!/usr/bin/env python3
"""
This script provides utilities for:

1. Converting fMRI volumes into AAL3-based parcellations and saving time-series data (.dat files).
2. Visualizing the AAL3 atlas.
3. Generating example subsequences from fMRI data for modeling or analysis.

Author: [Your Name]
Date: [Optional: YYYY-MM-DD]

Dependencies:
- numpy
- nibabel
- nilearn
- matplotlib
- ipdb (optional, for debugging)
- pandas
- python >= 3.6
"""

import os
import argparse
import glob
import pickle

import numpy as np
import nibabel as nib
from nilearn import plotting
import matplotlib.pyplot as plt

from ipdb import set_trace


def convert_fMRIvols_to_AAL3(data_path, output_path):
    """
    Convert 4D fMRI volumes into AAL3 parcellations.

    This function:
      1) Scans a given directory (data_path) for .nii.gz files.
      2) For each matching file, it loads an AAL3 atlas (hardcoded path) and the fMRI data.
      3) Reshapes the 4D fMRI volume into [n_voxels, n_timepoints], then extracts
         average time-series data for each AAL3 parcel (1 to 170).
      4) Saves the resulting time-series as a .dat file in 'output_path'.

    Args:
        data_path (str): Directory containing preprocessed fMRI volumes (.nii.gz).
        output_path (str): Directory where the parcellated time-series (.dat) files are saved.

    Notes:
        - The path for the AAL3 atlas is currently hardcoded as:
            '/orange/ruogu.fang/zeyun.zhao/FSL/bb_FSL/data/standard/AAL/AAL3.nii.gz'
        - The function is set to skip files unless they match a specific substring
          ("1000023_20227_2_0_fMRI_in_MNI_space.nii.gz") in this example code; adapt as needed.
        - Each .dat file is named after the original fMRI filename with '.nii.gz' removed.

    Returns:
        None
    """
    paths = os.listdir(data_path)
    print("fMRI data path specified:", data_path)
    print("Number of fMRI files found:", len(paths))

    # Hardcoded AAL3 atlas path
    aal_path = '/orange/ruogu.fang/zeyun.zhao/FSL/bb_FSL/data/standard/AAL/AAL3.nii.gz'
    print("Atlas file:", aal_path)

    # Load the atlas
    try:
        label_img = nib.load(aal_path)
        label_data = label_img.get_fdata()
        label_data = label_data.flatten()  # Flatten into 1D
        print("Atlas successfully loaded.")
    except Exception as e:
        print(f'Error loading AAL3 atlas at {aal_path}: {str(e)}')
        return

    # Loop over all files in the directory
    for f in paths:
        file_path = os.path.join(data_path, f)

        # Example filter: proceed only if filename contains a specific substring
        if "1000023_20227_2_0_fMRI_in_MNI_space.nii.gz" not in f:
            continue

        # Process only .nii.gz files
        if ".nii.gz" in f:
            print(f'Loading 4D image from {file_path}')
            try:
                dts_img = nib.load(file_path)
                dts_data = dts_img.get_fdata()
                print("Loaded fMRI data.")
            except Exception as e:
                print(f'Error loading 4D fMRI file "{f}": {str(e)}')
                continue

            try:
                print(f"Extracting AAL3 parcels for {f}...")
                # Reshape from (X, Y, Z, T) to (T, X*Y*Z)
                flattened = dts_data.reshape((-1, dts_data.shape[-1])).T
                n_timepoints = flattened.shape[0]

                # AAL3 has 170 parcels (labeled 1 through 170)
                n_parcels = 170
                pmTS = np.zeros((n_timepoints, n_parcels))

                # Compute mean signal for each parcel i
                # The label_data is also flattened (same shape in spatial dims).
                for i in range(1, n_parcels + 1):
                    parcel_mask = (label_data == i)
                    y = flattened[:, parcel_mask]
                    pmTS[:, i - 1] = np.nanmean(y, axis=1)

                # Replace NaNs with 0
                pmTS[np.isnan(pmTS)] = 0

                # Save time series as .dat
                save_name = f.split('.nii.gz')[0]
                out_file = os.path.join(output_path, f'{save_name}.dat')
                print(f"Saving {out_file} with shape {pmTS.shape} (timepoints x parcels).")
                np.savetxt(out_file, pmTS, delimiter='\t')

                set_trace()  # Debug if needed
            except Exception as e:
                print(f"Error extracting or saving parcels for {f}: {str(e)}")
        else:
            print(f"Skipping non-NIfTI file: {f}")


def show_AAL3(aal_template_path, save_dir):
    """
    Visualize each region in the AAL3 atlas by generating separate PNGs.

    This function:
      - Loads the AAL3 template.
      - Iterates over all possible region indices (0 to 169 in this script).
      - For each region, creates a binary mask image, then uses nilearn.plotting.plot_roi
        to produce an orthographic display, saved as a PNG.

    Args:
        aal_template_path (str): Path to the AAL3 atlas NIfTI file (e.g., AAL3.nii.gz).
        save_dir (str): Directory where the visualization PNG files are saved.

    Returns:
        None
    """
    output_image_path = os.path.join(save_dir, "AAL.jpg")

    try:
        label_img = nib.load(aal_template_path)
        label_data = label_img.get_fdata().reshape(91, 109, 91, 1)
    except Exception as e:
        print(f"Error loading AAL3 atlas at {aal_template_path}: {str(e)}")
        return

    set_trace()  # Debug if needed

    # AAL3 has 170 regions by default; adjust if needed
    for roi_index in range(170):
        # Create a binary mask for the current ROI
        roi_mask_data = (label_data == roi_index).astype(np.int16)
        roi_mask_img = nib.Nifti1Image(roi_mask_data, affine=label_img.affine)

        # Show ROI in an orthographic view
        display = plotting.plot_roi(
            roi_mask_img,
            title=f"ROI Index {roi_index}",
            display_mode='ortho',
            colorbar=True
        )
        # Save figure
        output_path = os.path.join(save_dir, f"{roi_index}.png")
        display.savefig(output_path)
        display.close()


def generate_subsequences(fmri_data, subsequence_length=200, segment_length=20, num_segments=10):
    """
    Sample random subsequences and segment them for each region of the fMRI data.

    Given an fMRI dataset shaped (timepoints, regions):
      1) Randomly sample a subsequence of length = subsequence_length (default 200) from the time dimension.
      2) Split that subsequence into multiple (num_segments) segments, each of length segment_length.

    Args:
        fmri_data (np.ndarray): fMRI data shaped (T, R), where T=number of timepoints, R=number of regions.
        subsequence_length (int): Length of the randomly sampled subsequence (default=200).
        segment_length (int): Size of each segment (default=20).
        num_segments (int): Number of segments per subsequence (default=10).

    Returns:
        list of np.ndarray:
            A list containing one set of segments for each region. Each set is
            a list of `num_segments` arrays, each of shape (segment_length,).

    Raises:
        AssertionError: If the split does not produce the expected number of segments.
    """
    num_timesteps, num_regions = fmri_data.shape
    subsequences = []

    set_trace()  # Debug if needed

    for i in range(num_regions):
        # Random start index for the subsequence
        start_idx = np.random.randint(0, num_timesteps - subsequence_length)
        # Extract the subsequence for region i
        subsequence = fmri_data[start_idx:start_idx + subsequence_length, i]
        # Split the subsequence into smaller segments
        segments = [subsequence[j:j + segment_length] for j in range(0, subsequence_length, segment_length)]
        # Check we have exactly num_segments segments
        assert len(segments) == num_segments, f"Expected {num_segments} segments, got {len(segments)}"
        subsequences.append(segments)

    return subsequences


def main():
    """
    Main execution flow for testing and demonstration.

    1) Defines paths for the AAL3 template, an fMRI data directory, and an output directory.
    2) Optionally calls the show_AAL3() function to visualize the AAL3 atlas.
    3) Optionally calls the convert_fMRIvols_to_AAL3() function to parcellate .nii.gz data into .dat files.
    4) Demonstrates how to generate random subsequences from artificially-created fMRI data (490 timepoints, 90 regions).
    """
    aal_template_path = '/orange/ruogu.fang/zeyun.zhao/FSL/bb_FSL/data/standard/AAL/AAL3.nii.gz'  
    output_path = "/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/rsfMRI_processed_nii/imgs"
    fmri_data_path = '/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/rsfMRI_processed_nii/Affined'

    # Uncomment if you want to visualize AAL3 regions
    # show_AAL3(aal_template_path, output_path)

    # Uncomment if you want to convert volumes in fmri_data_path
    # convert_fMRIvols_to_AAL3(fmri_data_path, output_path)

    # Example usage of generate_subsequences:
    print("Generating random example subsequences from mock data...")
    fmri_data = np.random.rand(490, 90)  # (timepoints=490, regions=90)
    subsequences = generate_subsequences(fmri_data)
    set_trace()


if __name__ == "__main__":
    main()
