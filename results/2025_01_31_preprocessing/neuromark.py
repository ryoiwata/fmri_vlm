import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.linalg import svd
from scipy.stats import skew
from sklearn.utils.extmath import randomized_svd
from sklearn.decomposition import FastICA
from icasso import Icasso

# Step 1: Load fMRI Data
# Assuming `fmri_data` is a 4D numpy array of shape (subjects, voxels, timepoints)
# Replace with actual loading code (e.g., using nibabel for NIfTI data)
def load_fmri_data(file_path):
    return np.load(file_path)  # Example placeholder

# Example: Simulated fMRI data
n_subjects_GSP = 1005
n_subjects_HCP = 823
n_voxels = 5000  # Example number of brain voxels
n_timepoints = 300  # Example number of timepoints

fmri_data_GSP = np.random.randn(n_subjects_GSP, n_voxels, n_timepoints)
fmri_data_HCP = np.random.randn(n_subjects_HCP, n_voxels, n_timepoints)

# Step 2: Apply PCA to Each Subject to Reduce to 110 PCs
def apply_subject_pca(fmri_data, n_components=110):
    pca = PCA(n_components=n_components)
    subject_pcs = np.array([pca.fit_transform(fmri_data[i].T) for i in range(fmri_data.shape[0])])
    return subject_pcs

subject_pcs_GSP = apply_subject_pca(fmri_data_GSP, n_components=110)
subject_pcs_HCP = apply_subject_pca(fmri_data_HCP, n_components=110)

# Step 3: Concatenate Subject-Level PCs Across Subjects and Apply Group-Level PCA (100 PCs)
def apply_group_pca(subject_pcs, n_components=100):
    reshaped_pcs = subject_pcs.reshape(subject_pcs.shape[0], -1)  # Flatten across subjects
    scaler = StandardScaler()
    reshaped_pcs = scaler.fit_transform(reshaped_pcs)
    pca = PCA(n_components=n_components)
    group_pcs = pca.fit_transform(reshaped_pcs)
    return group_pcs

group_pcs_GSP = apply_group_pca(subject_pcs_GSP, n_components=100)
group_pcs_HCP = apply_group_pca(subject_pcs_HCP, n_components=100)

# Step 4: Perform ICA Decomposition Using Infomax Algorithm
def apply_ica(group_pcs, n_components=100):
    ica = FastICA(n_components=n_components, whiten=True, max_iter=1000, algorithm="parallel")
    independent_components = ica.fit_transform(group_pcs)
    return independent_components

ica_components_GSP = apply_ica(group_pcs_GSP, n_components=100)
ica_components_HCP = apply_ica(group_pcs_HCP, n_components=100)

# Step 5: Apply ICASSO for ICA Stability (Run ICA 100 times and select best solution)
def icasso_ica(group_pcs, n_components=100, n_runs=100):
    icasso = Icasso(FastICA(n_components=n_components, whiten=True, max_iter=1000, algorithm="parallel"),
                    repetitions=n_runs)
    icasso.fit(group_pcs)
    stable_ic = icasso.get_stable_components()
    return stable_ic

stable_ica_GSP = icasso_ica(group_pcs_GSP, n_components=100, n_runs=100)
stable_ica_HCP = icasso_ica(group_pcs_HCP, n_components=100, n_runs=100)

# Step 6: Compute Skewness and Flip Components If Necessary
def adjust_skewness(ica_components):
    for i in range(ica_components.shape[1]):
        if skew(ica_components[:, i]) < 0:
            ica_components[:, i] *= -1
    return ica_components

adjusted_ica_GSP = adjust_skewness(stable_ica_GSP)
adjusted_ica_HCP = adjust_skewness(stable_ica_HCP)

# Step 7: Save Processed ICA Components
np.save("processed_ica_GSP.npy", adjusted_ica_GSP)
np.save("processed_ica_HCP.npy", adjusted_ica_HCP)

print("ICA processing completed and components saved successfully.")
