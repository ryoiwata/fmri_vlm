#!/usr/bin/env python3

"""
A modular Python script for segmenting a single 4D fMRI volume
into parcel-based time series using a specified atlas.

Usage (example):
  python segment_single_fMRI.py \
    --fmri_file /path/to/some_fMRI.nii.gz \
    --atlas_path /path/to/AAL3.nii.gz \
    --n_parcels 170 \
    --out_dir /path/to/output_folder

Steps:
  1) Load the NIfTI atlas, flatten into label_data.
  2) Load the single 4D fMRI file.
  3) For each of the n_parcels, compute the mean time series over that region.
  4) Write the resulting time series array to a .dat file in the chosen output directory
     (default: same folder as the fMRI file).
"""

import os
import sys
import argparse
import numpy as np
import nibabel as nib


def load_atlas(atlas_path: str) -> np.ndarray:
    """
    Load a NIfTI atlas from `atlas_path` and return it as a flattened NumPy array.
    """
    try:
        atlas_img = nib.load(atlas_path)
        atlas_data = atlas_img.get_fdata()
        return atlas_data.flatten()
    except Exception as e:
        raise IOError(f"Failed to load atlas at {atlas_path}: {str(e)}")


def extract_parcel_timeseries(
    fmri_path: str,
    label_data: np.ndarray,
    n_parcels: int
) -> np.ndarray:
    """
    Load a 4D fMRI volume from `fmri_path`, reshape it to (timepoints, voxels),
    and compute mean time series for each of the `n_parcels` in `label_data`.
    Assumes labels 1..n_parcels. Returns a 2D array of shape (timepoints, parcels).
    """
    fmri_img = nib.load(fmri_path)
    fmri_data = fmri_img.get_fdata()
    
    # Flatten spatial dims, transpose => shape: (timepoints, voxels)
    flattened = fmri_data.reshape((-1, fmri_data.shape[-1])).T
    n_timepoints = flattened.shape[0]

    pmTS = np.zeros((n_timepoints, n_parcels))

    for i in range(1, n_parcels + 1):
        parcel_mask = (label_data == i)
        num_voxels  = np.sum(parcel_mask)

        if num_voxels == 0:
            # If no voxels in this parcel, fill with 0.0
            pmTS[:, i - 1] = 0.0
        else:
            y = flattened[:, parcel_mask]  # shape: (timepoints, #voxels_in_parcel)
            pmTS[:, i - 1] = np.nanmean(y, axis=1)

    # Replace any remaining NaNs with 0
    pmTS[np.isnan(pmTS)] = 0
    return pmTS


def save_timeseries(pmTS: np.ndarray, out_file: str):
    """
    Save time series (2D NumPy array) to a .dat file using tab delimiters.
    """
    np.savetxt(out_file, pmTS, delimiter='\t')


def main():
    parser = argparse.ArgumentParser(
        description="Segment a single 4D fMRI volume into parcel-based time series."
    )
    parser.add_argument(
        "--fmri_file", required=True,
        help="Path to the single 4D fMRI .nii.gz file."
    )
    parser.add_argument(
        "--atlas_path", required=True,
        help="Path to the NIfTI atlas file, e.g. AAL3.nii.gz"
    )
    parser.add_argument(
        "--n_parcels", type=int, default=170,
        help="Number of parcels expected in the atlas. (default=170)"
    )
    parser.add_argument(
        "--out_dir", default=None,
        help="Optional output directory (default: same folder as --fmri_file)."
    )

    args = parser.parse_args()

    # 1) Load the atlas
    label_data = load_atlas(args.atlas_path)

    # 2) Extract time series from the single fMRI file
    pmTS = extract_parcel_timeseries(
        fmri_path=args.fmri_file,
        label_data=label_data,
        n_parcels=args.n_parcels
    )

    # Decide output directory
    if args.out_dir is not None:
        out_dir = args.out_dir
        # Create the out_dir if needed
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
    else:
        # Default: same folder as fmri_file
        out_dir = os.path.dirname(args.fmri_file)

    # Build output file name
    fmri_file = os.path.basename(args.fmri_file)
    base_name = fmri_file.replace(".nii.gz", "")
    out_file = os.path.join(out_dir, f"{base_name}.dat")

    # 3) Save the parcellated time series
    save_timeseries(pmTS, out_file)
    print(f"Parcel-based time series saved to: {out_file}")


if __name__ == "__main__":
    main()
