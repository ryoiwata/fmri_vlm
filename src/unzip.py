import os
import zipfile
import shutil
import subprocess


def extract_filtered_func_data(zip_file_path, file_to_extract, output_path):
    """
    Extract a specific file from a ZIP archive, rename it, and remove the intermediate folder.

    This function opens the ZIP file at 'zip_file_path' and checks if 'file_to_extract' exists within it.
    If found, it extracts the file into 'output_path'. Afterwards, it renames the extracted file
    to a new location (based on the output folder name) and removes the temporary extraction folder.

    Note:
        - The function assumes a particular file structure:
              fMRI/rfMRI.ica/filtered_func_data_clean.nii.gz
        - Once extracted, the file is moved to:
              /orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/rsfMRI_processed_nii/filtered_func_data_clean/
          plus a suffix of the subject ID extracted from 'output_path'.
        - Then 'output_path' (the temporary folder) is deleted.

    Args:
        zip_file_path (str): The file path to the ZIP archive.
        file_to_extract (str): The path (inside the ZIP) to the file to be extracted.
        output_path (str): The directory path where the file will initially be extracted.

    Returns:
        int: Always returns 0 upon completion.
    """
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Check if the specified file exists within the ZIP
        if file_to_extract in zip_ref.namelist():
            zip_ref.extract(file_to_extract, output_path)
            print(f"Extracted '{file_to_extract}' into: {output_path}")

            # Construct source and target file paths
            source_file_path = os.path.join(output_path, "fMRI", "rfMRI.ica", "filtered_func_data_clean.nii.gz")
            subject_id = os.path.basename(output_path)  # e.g., "1000023_20227_2_0"
            target_file_path = (
                "/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/"
                "rsfMRI_processed_nii/filtered_func_data_clean/"
                f"{subject_id}_filtered_func_data_clean.nii.gz"
            )

            # Rename/move the extracted file to the target file path
            os.rename(source_file_path, target_file_path)

            # Remove the intermediate extraction folder
            shutil.rmtree(output_path)
        else:
            print(f"File '{file_to_extract}' not found in '{zip_file_path}'. Skipping.")

    return 0


def register_to_mni_space(in_path, out_path, 
                          ref_path="/orange/ruogu.fang/zeyun.zhao/FSL/bb_FSL/data/standard/tpl-MNI152NLin6Asym_res-02_T1w.nii.gz", 
                          applyisoxfm="2"):
    """
    Register a 3D or 4D NIfTI file to MNI standard space using FSL's flirt.

    This function applies an isotropic transformation (default 2mm) from the input file
    to a given reference template (commonly the MNI152 T1-weighted template). It leverages
    the 'flirt' command-line tool to do so.

    Args:
        in_path (str): Path to the input NIfTI file to be registered.
        out_path (str): Path where the registered output NIfTI file will be saved.
        ref_path (str, optional): Path to the reference MNI template. Defaults to a 2mm MNI template.
        applyisoxfm (str, optional): Desired isotropic voxel size in mm (as a string). Defaults to "2".

    Raises:
        subprocess.CalledProcessError: If the 'flirt' command fails.
    """
    flirt_command = [
        "flirt",
        "-in", in_path,
        "-ref", ref_path,
        "-out", out_path,
        "-applyisoxfm", applyisoxfm
    ]

    try:
        subprocess.run(flirt_command, check=True)
        print(f"FLIRT command executed successfully. Output saved to: {out_path}")
    except subprocess.CalledProcessError as exc:
        print(f"FLIRT command failed: {exc}")


def main():
    """
    Example main function to demonstrate iterating through a folder
    and extracting a specified file from ZIP archives.

    It looks for ZIP files in '/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/rsfMRI_processed_nii',
    extracts a particular file ('fMRI/rfMRI.ica/filtered_func_data_clean.nii.gz'),
    and places the extracted file in a dedicated directory for further processing.
    """
    folder_path = "/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/rsfMRI_processed_nii"
    file_to_extract = "fMRI/rfMRI.ica/filtered_func_data_clean.nii.gz"

    # Loop through all items in the specified folder
    for root in os.listdir(folder_path):
        # Only process if the item is a ZIP file
        if not root.endswith(".zip"):
            continue

        zip_file_path = os.path.join(folder_path, root)
        # Output path is a subdirectory named after the ZIP file (minus '.zip')
        output_path = os.path.join(
            folder_path,
            "filtered_func_data_clean",
            root[:-4]
        )

        extract_filtered_func_data(zip_file_path, file_to_extract, output_path)


if __name__ == "__main__":
    # Example usage of the registration function (hardcoded paths)
    input_file = "/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/rsfMRI_processed_nii/filtered_func_data_clean/1000023_20227_2_0_filtered_func_data_clean.nii.gz"
    output_file = "/orange/ruogu.fang/zeyun.zhao/DATA/UKB_sub/rsfMRI_processed_nii/Affined/000.nii.gz"

    # Uncomment to run the main extraction process
    # main()

    # Perform registration of the extracted file to MNI space
    register_to_mni_space(in_path=input_file, out_path=output_file)