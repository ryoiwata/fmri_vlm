import pandas as pd
import os
import requests

# Load the summary spreadsheet
spreadsheet_url = "https://s3.amazonaws.com/fcp-indi/data/Projects/ABIDE_Initiative/Phenotypic_V1_0b.csv"
df = pd.read_csv(spreadsheet_url)

# Select subject IDs
subject_ids = df["FILE_ID"].dropna().astype(str).tolist()

# Define parameters
pipeline = "cpac"
strategy = "filt_noglobal"
derivative = "func_preproc"
output_dir = "/blue/ruogu.fang/ryoi360/projects/fmri_vlm/data/ABIDE_preprocessed"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Download fMRI files
for index, subject_id in enumerate(subject_ids):  # Modify this number for more subjects
    print("Progress: {}/{}".format(index, len(subject_ids)))
    file_url = f"https://s3.amazonaws.com/fcp-indi/data/Projects/ABIDE_Initiative/Outputs/{pipeline}/{strategy}/{derivative}/{subject_id}_{derivative}.nii.gz"
    file_path = os.path.join(output_dir, f"{subject_id}_{derivative}.nii.gz")

    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {file_path}")
    else:
        print(f"Failed to download: {file_url}")
