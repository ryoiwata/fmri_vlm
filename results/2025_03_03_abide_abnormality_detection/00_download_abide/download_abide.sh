#!/bin/bash
#SBATCH --job-name=abide_download    # Job name
#SBATCH --output=abide_download_%j.log  # Log file name
#SBATCH --time=8:00:00               # Time limit hh:mm:ss
#SBATCH --cpus-per-task=1            # Number of CPU cores
#SBATCH --mem=4gb                   # Memory allocation
#SBATCH --output=abide_download.out  
#SBATCH --error=abide_download.err  

# Load Python module (ensure the correct version is used)
module load conda  # Adjust as needed

# Activate virtual environment if required
conda activate /blue/ruogu.fang/ryoi360/projects/fmri_vlm/bin/conda/nibabel_env

# Run the Python script
python abide_download.py
