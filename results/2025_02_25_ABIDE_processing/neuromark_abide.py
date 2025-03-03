#!/usr/bin/env python3
"""
Example Python script illustrating the multi-step ICA pipeline described in your excerpt.

Required libraries:
    numpy, scipy, scikit-learn, nibabel (for loading NIfTI, if needed), etc.
    
DISCLAIMER:
    - This is a simplified illustration only. Adjust as needed for your environment.
    - Actual Infomax ICA and true ICASSO procedures may differ in details from FastICA.
"""

import os
import numpy as np
import nibabel as nib
from sklearn.decomposition import PCA, FastICA
from scipy.stats import skew

# ---------------------------------------------------------------------------
# Step 1: Load and prepare data
# ---------------------------------------------------------------------------
def load_fmri_data(list_of_nifti_paths):
    """
    Example loader that:
      - Reads each preprocessed 4D fMRI file (time x x_dim x y_dim x z_dim).
      - Reshapes to a 2D array: (time, n_voxels).
      - Returns a list of subject data arrays.
    """
    subject_data = []
    for fpath in list_of_nifti_paths:
        img = nib.load(fpath)
        data_4d = img.get_fdata()  # shape: (x_dim, y_dim, z_dim, time)
        # Move time to axis=0 and flatten the spatial dims:
        data_2d = np.reshape(np.moveaxis(data_4d, -1, 0),
                             (data_4d.shape[-1], -1))
        subject_data.append(data_2d)
    return subject_data


def individual_subject_pca(subject_data, n_components=110):
    """
    Perform PCA on each subject’s data (time x voxel) to reduce to `n_components`.
    Return a list of reduced 2D arrays: (time, n_components).
    """
    subject_pcs = []
    for data_2d in subject_data:
        pca = PCA(n_components=n_components)
        reduced = pca.fit_transform(data_2d)  # shape: (time_points, n_components)
        subject_pcs.append(reduced)
    return subject_pcs


# ---------------------------------------------------------------------------
# Step 2 & 3: Concatenate individual PCs and run group-level PCA, then ICA
# ---------------------------------------------------------------------------
def run_group_pca_then_ica(subject_pcs, n_group_components=100,
                           n_ica_runs=100, random_state=0):
    """
    - Concatenate each subject's PCA results along the row dimension (time),
      forming a large group matrix: (sum_of_times, 110).
    - Run a second PCA to reduce to `n_group_components` (default=100).
    - Then run multiple ICA (FastICA) attempts for ICASSO-like approach.
    - Pick best run based on similarity to a "consensus" or by max neg-entropy, etc.
    - Return the best-run's IC mixing matrix and the final group-level ICs.
    """
    # 1) Concatenate:
    # subject_pcs is a list of arrays shape (time, 110)
    group_data = np.concatenate(subject_pcs, axis=0)  # (sum_of_times, 110)
    
    # 2) PCA to reduce to 100 group-level PCs
    group_pca = PCA(n_components=n_group_components, random_state=random_state)
    group_pcs_data = group_pca.fit_transform(group_data)  # shape: (sum_of_times, 100)
    
    # For an "ICASSO-like" approach, run multiple ICA with different random seeds:
    ica_components_list = []
    
    # Typically, you might store all unmixing matrices & then do a clustering step.
    # Here we do a simplified approach, then pick the "best" by average kurtosis, e.g.
    for run_idx in range(n_ica_runs):
        rng = np.random.RandomState(run_idx)  # or vary seeds
        ica_model = FastICA(n_components=n_group_components,
                            random_state=rng,
                            max_iter=1000,
                            whiten=True)
        S_ = ica_model.fit_transform(group_pcs_data)  # shape: (time_points, 100)
        # The columns of `S_` are the estimated IC time-courses (component signals).
        # The mixing matrix W^-1 is ica_model.mixing_. 
        # The actual spatial maps can be derived from S_ or from the pseudo-inverse as needed.
        # We'll store the "spatial" IC patterns as S_.T or do a pinv if you prefer that orientation.
        ica_components_list.append(S_.T)
    
    # Decide which run is "best" – e.g., pick run with highest average neg-entropy or kurtosis:
    # (Below is a crude example using the sum of absolute kurtosis across all components.)
    best_run_idx = None
    best_run_metric = -np.inf
    for i, comps_2d in enumerate(ica_components_list):
        # `comps_2d` shape: (n_components, time_points)
        # we could use kurtosis, or negentropy approximation, etc.
        # for simplicity, we do:
        kurt_vals = np.array([skew(c, bias=False) for c in comps_2d])
        # sum of absolute skew:
        metric = np.sum(np.abs(kurt_vals))
        if metric > best_run_metric:
            best_run_metric = metric
            best_run_idx = i
    
    best_ica_maps = ica_components_list[best_run_idx]  # shape: (100, time_points)
    
    # Reshape or invert to get group-level "spatial" components. 
    # For Infomax-like ICA on PCA outputs, we typically interpret components 
    # by (pseudo-inverse of mixing) or the dot product with group PCA loadings.
    # This example just returns best_ica_maps as "group-level ICs" to be refined if needed.
    return best_ica_maps  # shape: (n_components, time_points)


# ---------------------------------------------------------------------------
# Step 4: Flip IC if its skewness is negative
# ---------------------------------------------------------------------------
def flip_negative_skew(ics_2d):
    """
    Given 2D array of shape (n_components, n_timepoints/voxels),
    compute skewness for each row, flip if negative.
    Returns the array with flips applied.
    """
    flipped_ics = ics_2d.copy()
    n_comp = flipped_ics.shape[0]
    for i in range(n_comp):
        # compute skewness for the ith row
        val = skew(flipped_ics[i, :], bias=False)
        if val < 0:
            flipped_ics[i, :] *= -1
    return flipped_ics


# ---------------------------------------------------------------------------
# Step 5: Greedy matching of two sets of IC maps
# ---------------------------------------------------------------------------
def greedy_spatial_match(ics_a, ics_b, corr_threshold=0.4):
    """
    ics_a, ics_b: each shape = (n_components, n_voxels) or (n_components, n_timepoints)
                  but typically you'd have them in "spatial map" form (component x voxel).
    
    1. Compute an abs-correlation matrix between the two sets of ics, shape= (Na, Nb).
    2. Repeatedly pick the max correlation pair, sign-flip if original correlation is negative.
    3. Zero out that row and column to exclude them from further pairing.
    4. Return the matched pairs that exceed the threshold, plus their sign-flipped versions.
    """
    nA, nV = ics_a.shape
    nB, _ = ics_b.shape
    # correlation matrix (absolute value)
    # We'll keep track of the sign as well. 
    corr_mat = np.zeros((nA, nB))
    sign_mat = np.zeros((nA, nB))
    
    for i in range(nA):
        for j in range(nB):
            corr_ij = np.corrcoef(ics_a[i,:], ics_b[j,:])[0,1]
            corr_mat[i,j] = abs(corr_ij)
            sign_mat[i,j] = np.sign(corr_ij)  # +1 or -1 or 0
    
    # Now do the iterative "greedy" selection:
    matched_pairs = []  # will store tuples like (idxA, idxB, correlation, sign_of_correlation)
    
    # Make a copy of corr_mat to zero out as we pick pairs
    tmp_corr = corr_mat.copy()
    
    for _ in range(nA):  # up to min(nA,nB) matches
        # find max in tmp_corr
        i_max, j_max = np.unravel_index(np.argmax(tmp_corr), tmp_corr.shape)
        max_val = tmp_corr[i_max, j_max]
        if max_val < corr_threshold:
            # no more pairs exceed threshold
            break
        
        matched_pairs.append((i_max, j_max, max_val, sign_mat[i_max,j_max]))
        
        # zero out that row and column
        tmp_corr[i_max, :] = 0.0
        tmp_corr[:, j_max] = 0.0
    
    # If correlation sign was negative, we sign-flip ICS_B’s component 
    # or ICS_A’s, but typically flip ICS_B for convenience. 
    # (In actual pipeline, you might want to store a separate copy for the flips.)
    # We'll do it in-place here for demonstration.
    for (ia, ib, val, sgn) in matched_pairs:
        if sgn < 0:
            ics_b[ib,:] *= -1
    
    # Return the subset of matched pairs that exceed threshold 
    # plus the possibly sign-flipped ics_b:
    final_pairs = [p for p in matched_pairs if p[2] >= corr_threshold]
    return final_pairs, ics_a, ics_b


# ---------------------------------------------------------------------------
# Main demonstration function
# ---------------------------------------------------------------------------
def main_example():
    """
    Demonstrate the pipeline, step by step, using hypothetical file lists
    for two cohorts: controls and disease.
    """
    # Hypothetical example: lists of NIfTI paths
    #  - Replace with your actual preprocessed fMRI NIfTI files
    control_paths = ["/path/to/control_subject_01_preproc.nii.gz",
                     "/path/to/control_subject_02_preproc.nii.gz",
                     # ...
                    ]
    disease_paths = ["/path/to/disease_subject_01_preproc.nii.gz",
                     "/path/to/disease_subject_02_preproc.nii.gz",
                     # ...
                    ]
    
    # 1) Load data & do subject-level PCA
    control_data = load_fmri_data(control_paths)   # list of arrays (time x voxel)
    disease_data = load_fmri_data(disease_paths)   # list of arrays (time x voxel)
    
    control_pcs = individual_subject_pca(control_data, n_components=110)
    disease_pcs = individual_subject_pca(disease_data, n_components=110)
    
    # 2 & 3) Group-level PCA then ICA with repeated runs (ICASSO style)
    ctrl_group_ics = run_group_pca_then_ica(control_pcs,
                                            n_group_components=100,
                                            n_ica_runs=100,
                                            random_state=0)
    dis_group_ics  = run_group_pca_then_ica(disease_pcs,
                                            n_group_components=100,
                                            n_ica_runs=100,
                                            random_state=0)
    # ctrl_group_ics, dis_group_ics each shape: (100, group_time_points)
    # but for matching we usually want them as (100, voxel), i.e. "spatial maps."
    # If your group-time dimension is not the same as voxel dimension, you'd 
    # typically invert the mixing or do post-processing to obtain spatial maps.
    # We'll pretend these are already "spatial" for the sake of demonstration.
    
    # 4) Flip negative skewness
    ctrl_group_ics = flip_negative_skew(ctrl_group_ics)
    dis_group_ics  = flip_negative_skew(dis_group_ics)
    
    # 5) Greedy matching between the two sets
    matched_pairs, ctrl_flipped, dis_flipped = greedy_spatial_match(
        ctrl_group_ics,
        dis_group_ics,
        corr_threshold=0.4
    )
    
    print(f"Number of matched IC pairs (corr>0.4): {len(matched_pairs)}")
    for pair in matched_pairs:
        iA, iB, corr_val, sign_ = pair
        print(f"  Pair: IC_ctrl={iA}, IC_dis={iB}, corr={corr_val:.3f}, sign={sign_}")
    
    # The matched_pairs with correlation > 0.4 are considered reproducible ICs. 
    # Next steps might include:
    #   - Inspect each matched IC pair’s spatial pattern.
    #   - Exclude artifactual components using heuristics (peak in gray matter, etc.).
    #   - Compare final sets of reproducible ICNs across cohorts.
    #   - Downstream connectivity/functional analyses.

    print("Done. This demonstration performed the group-ICA-like pipeline.")

if __name__ == "__main__":
    main_example()
