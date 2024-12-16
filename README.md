# Instructions for Getting Started

Be sure to read the wiki page to learn more about the project and the expected outputs. https://github.com/emilyalcu/BOP-inmate-complaints/wiki

## Step 1: Download this repository 
- Click the green "Code" button on the github repo page
- Click "Download ZIP"
- Make sure to unzip the file

## Step 2: Download the BOP dataset from the Data Liberation Project
- Download the CSV dataset from https://drive.google.com/file/d/1LzJ4smDkviTAVVErFCuYYdhhM4VD2CYJ/view?usp=sharing
- The CSV file should already be named "complaint-filings.cvs". If not, rename it.
- Move the file into the "data" subfolder of the "BOP-inmate-complaints" folder

## Step 3: Download and Install Visual Studio Code 
- https://code.visualstudio.com/ 

## Step 4: Download and Install Python 3.13.1
- https://www.python.org/downloads/

## Step 5: Download and Install R 4.4.2
- https://cran.r-project.org/mirrors.html
- Select a CRAN (Comprehensive R Archive Network) mirror
- Select the proper download link for your system

## Step 6: Install Libraries in R
- Open the R application
- Select a CRAN mirror 
- Run all six of the following:
    - install.packages("languageserver")
    - install.packages("ggplot2")
    - install.packages("tibble")
    - install.packages("dplyr")
    - install.packages("tidyr")
    - install.packages("readr")

## Step 7: Install extensions in Visual Studio Code
- Open Visual Studio Code applicaiton
- Go to the "Extensions" tab on the right or press Shift+Command+X
- Download the following extensions:
    - Python https://marketplace.visualstudio.com/items?itemName=ms-python.python
    - Jupyter https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter
    - R https://marketplace.visualstudio.com/items?itemName=REditorSupport.r

## Step 8: Install pandas in Visual Studio Code
- While in the Studio Code application open a new Jupyter Notebook with the 3.12.1 kernel
- Open the terminal within the application (terminal>new terminal)
- Run "pip3 install pandas"

## Step 9: Run the first script - (01_RunScriptsWithStateCode.py)
- Open the terminal
- Change directories to the src subfolder
    - cd ...
- Run "python3 01_RunScriptsWithStateCode.py"
- You will be prompted to enter a two letter state code. You can also enter "DC" for Washington DC or "ALL" to create datasets, reports, and visualizations for the entire dataset.
- The dataset outputs from the Python script can be found in results>data
- The report and visualization outputs from the R script can be found in results>analysis
- You can rerun this script to get the same outputs for other states.

## Step 10: Run the second script - (02_NationalAnalysis.r)
- You MUST complete the previous step with "ALL" to create the dataset that will be used in this step
- Open the terminal 
- Change directories to the src subfolder if not done already 
- Run "Rscript 02_NationalAnalysis.r"
- The visualization outputs from this step will be found in results>analysis
