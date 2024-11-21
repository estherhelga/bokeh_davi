# League of Legends OTP Dashboard

This dashboard visualizes League of Legends One-Trick Pony (OTP) statistics using Bokeh.  It allows users to select a champion and view interactive plots of their performance metrics.

## Installation

1. **Conda Environment:** If you don't have conda installed, download and install Anaconda or Miniconda.
2. **Create Environment:** Create a conda environment with Python 3.9 (or the version you used). For example, run this from the Anaconda Prompt/Powershell:
   ```bash
   conda create -n lol-otp-dashboard python=3.9

1. **Activate Environment:** Activate the environment by running the following in your terminal: 'conda activate lol-otp-dashboard'
2. **Install Requirements:** Install the required packages from the requirements.txt file by running the following in your terminal: 'pip install -r requirements.txt'

## Running the Dashboard

**Activate Environment:** Make sure the lol-otp-dashboard environment is activated.

**Navigate to Project Directory:** Open a terminal or Anaconda Prompt and navigate to the directory containing dashboard.py.

**Run Bokeh Server:** Start the Bokeh server by running the following in your terminal: 'bokeh serve --show dashboard.py'

**Deactivate Bokeh Server:** Stop the Bokeh server by pressing ctrl + c

## File Overview 

The original data file optained from Anders after the API data collection was roughly cleaned, and produced the combined_matches.csv. This file was then used for further cleaning/wrangling. 

1. cleaned_data.csv -> This CVS file containes cleaned data from the combined_matches.csv
    - All matches < 900 (15 minutes) seconda have been filtered out 
    - All matches where 'team_position' != "TOP" were filtered out

2. filtered_patch_data.cvs -> This CSV file containes ONLY info on patches 14.x Includes the columns:
    - champion
    - game_version
    - lane_opponent
    - losses
    - wins
The losses and wins are counts per patch against a specific opponent. For example "Aatrox,14.01,Akshan,1,0" means Aatrox has 1 loss and 0 wins against Akshan in patch 14.01

3. scatterplot_filtered_data.csv -> 
    - Count the occurrences of each opponent in 'lane_opponent' 
    - Filter the dataset to keep only rows where 'lane_opponent' appears 20 or more times