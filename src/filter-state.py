# %%
# STEP 1: Create [STATE] subset of data from the data provided by BOP
    # Find all [STATE] Facilities in the CDFC_FacilityCodes.csv and save as a set
    # Use the set to filter ComplaintFilings.csv so that we are left with only complaints made at [STATE] facilities 
    # Save results to [STATE]_Submissions.csv

import pandas as pd
import os

def filter_submissions(state_code, input_facilities_path, input_submissions_path, output_path):
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Load facilities data, filter for [STATE] facility codes, and save as a variable
    all_facilities = pd.read_csv(input_facilities_path)
    state_facility_codes = set(all_facilities.loc[all_facilities['State'] == state_code, 'Facility_Code'])

    # Load BOP submissions data and filter where CDFCLEVN value (Facility of Occurrence) is in variable
    all_submissions = pd.read_csv(input_submissions_path)
    state_submissions = all_submissions[all_submissions['CDFCLEVN'].isin(state_facility_codes)]

    # Save filtered dataset to a csv file
    filtered_output_file = f"{output_path}/{state_code}_Submissions.csv"
    state_submissions.to_csv(filtered_output_file, index=False)
    print(f"Filtered submissions for state '{state_code}' saved to {filtered_output_file}.")
    return state_submissions

# %%
# STEP 2: Create an enriched dataset with additional columns
  # Add column (subcount) which counts total number of submissions associated with that Case Number (CASENBR)
  # Add column (rejcount) which counts the total number of "Rejected" (rej) submissions associated with that Case Number (CASENBR)
  # Add column (cldclocount) which counts the total number of "Closed Denied" and "Closed Granted" submissions associated with that Case Number (CASENBR)
  # Add column (clgacccount) which counts the total number of "Accepted" and "Closed Granted" submissions associated with that case number (CASENBR)
  # Add column (earliestsitdtrcv) which shows earliest Remedy Case Submission Date Received (sitdtrcv) for that case number (CASENBR)
  # Add column (latestsdtstat) which shows the most recent Date Latest Status Assigned (sdtstat) for that Case Number (CASENBR)
  # Add column (daysbetween) which shows the number of days between earliestsitdtrcv and latestsdtstat. This is the amount of time either between the first complaint and the latest case status.


def enrich_submissions(state_submissions, output_path, state_code):

    # Add a column that counts the total number of submissions associated with that one CASENBR
    subcounts = state_submissions['CASENBR'].value_counts()
    state_submissions['subcount'] = state_submissions['CASENBR'].map(subcounts)
    
    # Add a column to count the total number of "Rejected" submissions for each CASENBR
    rejcounts = state_submissions[state_submissions['CDSTATUS'] == 'REJ'].groupby('CASENBR').size()
    state_submissions['rejcount'] = state_submissions['CASENBR'].map(rejcounts).fillna(0).astype(int)

    # Add a column to count the total number of "Closed Denied" and "Closed Other" submissions for each CASENBR
    cldclocounts = state_submissions[state_submissions['CDSTATUS'].isin(['CLD', 'CLO'])].groupby('CASENBR').size()
    state_submissions['cldclocount'] = state_submissions['CASENBR'].map(cldclocounts).fillna(0).astype(int)

    # Add a column to count the total number of "Closed Granted" and "Accepted" submissions for each CASENBR
    clgacccount = state_submissions[state_submissions['CDSTATUS'].isin(['CLG', 'ACC'])].groupby('CASENBR').size()
    state_submissions['clgacccount'] = state_submissions['CASENBR'].map(clgacccount).fillna(0).astype(int)

    # Make sure 'sitdtrcv' and 'sdtstat' are in datetime format
    state_submissions['sitdtrcv'] = pd.to_datetime(state_submissions['sitdtrcv'])
    state_submissions['sdtstat'] = pd.to_datetime(state_submissions['sdtstat'])

    # Find the earliest sitdtrcv date for each CASENBR
    earliestsitdtrcv = state_submissions.groupby('CASENBR')['sitdtrcv'].min().reset_index()
    earliestsitdtrcv.rename(columns={'sitdtrcv': 'earliest_sitdtrcv'}, inplace=True)

    # Find the latest sdtstat date for each CASENBR
    latestsdtstat = state_submissions.groupby('CASENBR')['sdtstat'].max().reset_index()
    latestsdtstat.rename(columns={'sdtstat': 'latest_sdtstat'}, inplace=True)

    # Merge the earliest submission date and most recent status update date
    merged_dates = pd.merge(earliestsitdtrcv, latestsdtstat, on='CASENBR')

    # Calculate the number of days between the earliest submission date and the most recent status update date
    merged_dates['days_between'] = (merged_dates['latest_sdtstat'] - merged_dates['earliest_sitdtrcv']).dt.days

    # Merge the calculated dates back into the original dataset
    enriched_submissions = pd.merge(state_submissions, merged_dates, on='CASENBR', how='left')

    # save the updated dataset as [STATE]_SubmissionsEnriched.csv
    enriched_output_file = f"{output_path}/{state_code}_SubmissionsEnriched.csv"
    enriched_submissions.to_csv(enriched_output_file, index=False)
    print(f"Enriched submissions for state '{state_code}' saved to {enriched_output_file}.")
    return enriched_submissions


# %%
# STEP 3: Create expanded dataset with tranlations of the codes for easier use

def expand_submissions(enriched_submissions, output_path, state_code, code_files):

    # Import code translation CSVs
    complaintcodes = pd.read_csv(code_files['complaintcodes'])
    facilitycodes = pd.read_csv(code_files['facilitycodes'])
    statuscodes = pd.read_csv(code_files['statuscodes'])
    orglevelcodes = pd.read_csv(code_files['orglevelcodes'])
    statusreasoncodes = pd.read_csv(code_files['statusreasoncodes'])
    columncodes = pd.read_csv(code_files['columncodes'])
    primarysubjectcodes = pd.read_csv(code_files['primarysubjectcodes'])

    # Duplicate dataset to avoid modifying the original
    expanded_submissions = enriched_submissions.copy()

    # Duplicate 'cdsub1cb' column for translation
    expanded_submissions['cdsub1cbTEXT'] = expanded_submissions['cdsub1cb']

    # Replace codes with translations from code files
    expanded_submissions['cdsub1cbTEXT'] = expanded_submissions['cdsub1cbTEXT'].map(complaintcodes.set_index('Code')['Text']).fillna(expanded_submissions['cdsub1cbTEXT'])
    expanded_submissions['CDFCLEVN'] = expanded_submissions['CDFCLEVN'].map(facilitycodes.set_index('Facility_Code')['Facility_Name']).fillna(expanded_submissions['CDFCLEVN'])
    expanded_submissions['CDFCLRCV'] = expanded_submissions['CDFCLRCV'].map(facilitycodes.set_index('Facility_Code')['Facility_Name']).fillna(expanded_submissions['CDFCLRCV'])
    expanded_submissions['CDOFCRCV'] = expanded_submissions['CDOFCRCV'].map(facilitycodes.set_index('Facility_Code')['Facility_Name']).fillna(expanded_submissions['CDOFCRCV'])
    expanded_submissions['ITERLVL'] = expanded_submissions['ITERLVL'].map(orglevelcodes.set_index('Code')['Text']).fillna(expanded_submissions['ITERLVL'])
    expanded_submissions['CDSTATUS'] = expanded_submissions['CDSTATUS'].map(statuscodes.set_index('Code')['Text']).fillna(expanded_submissions['CDSTATUS'])

    # Replace status reason codes
    for col in ['STATRSN1', 'STATRSN2', 'STATRSN3', 'STATRSN4', 'STATRSN5']:
        expanded_submissions[col] = expanded_submissions[col].map(statusreasoncodes.set_index('Reason Code')['Text']).fillna(expanded_submissions[col])

    # Translate primary subject codes
    expanded_submissions['CDSUB1PR'] = expanded_submissions['CDSUB1PR'].map(primarysubjectcodes.set_index('Primary Subject Code')['Primary Subject Code Translation']).fillna(expanded_submissions['CDSUB1PR'])

    # Replace null values in 'sdtdue' for rejected statuses
    expanded_submissions['sdtdue'] = expanded_submissions['sdtdue'].fillna('rejected')

    # Replace binary values with 'yes' and 'no' for clarity
    binary_columns = [
        'accept', 'reject', 'deny', 'grant', 'other', 'submit', 'filed', 'closed',
        'diffreg_filed', 'diffinst', 'timely', 'diffreg_answer', 'overdue',
        'untimely', 'resubmit', 'noinfres', 'attachmt', 'wronglvl', 'otherrej'
    ]
    for col in binary_columns:
        expanded_submissions[col] = expanded_submissions[col].replace({0: 'no', 1: 'yes'})

    # Load column code CSV as a dictionary and rename columns
    columncodes_dict = dict(zip(columncodes['Code'], columncodes['Text']))
    expanded_submissions.rename(columns=columncodes_dict, inplace=True)

    # Save expanded dataset to a CSV file
    expanded_output_file = f"{output_path}/{state_code}_SubmissionsEnrichedExpanded.csv"
    expanded_submissions.to_csv(expanded_output_file, index=False)
    print(f"Expanded submissions for state '{state_code}' saved to {expanded_output_file}.")

    return expanded_submissions


# %%
# STEP 4: Create subset of [STATE] submissions data with unique complaints only. The one record/row with the most recent status update from each Case Number will be present in this dataset.

def create_unique_submissions(enriched_submissions, output_path, state_code):
    
    # Sort "sitdtrcv" (submission date) in descending order 
    unique_submissions = enriched_submissions.sort_values(by='sitdtrcv', ascending=False)

    # Drop duplicate CASENBRs, keeping the most recent (highest sitdtrcv)
    unique_submissions = unique_submissions.drop_duplicates(subset='CASENBR', keep='first')

    # Save Unique NY Submissions to a CSV
    unique_output_file = f"{output_path}/{state_code}_UniqueComplaintsEnriched.csv"
    unique_submissions.to_csv(unique_output_file, index=False)
    print(f"Unique submissions for state '{state_code}' saved to {unique_output_file}.")
    return unique_submissions


# %%
# STEP 5: Create expanded dataset of NYSubmissionsEnriched.csv with codes translated for easier use 

def expand_unique_submissions(unique_submissions, output_path, state_code, code_files):
    """
    Expands the unique submissions dataset by translating codes into human-readable formats.

    Parameters:
        unique_submissions (pd.DataFrame): The unique submissions dataset.
        output_path (str): Path to save the expanded dataset.
        state_code (str): The state code (e.g., 'NY').
        code_files (dict): Dictionary containing paths to code translation CSV files.

    Returns:
        pd.DataFrame: The expanded unique dataset.
    """
    # Import code translation CSVs
    complaintcodes = pd.read_csv(code_files['complaintcodes'])
    facilitycodes = pd.read_csv(code_files['facilitycodes'])
    statuscodes = pd.read_csv(code_files['statuscodes'])
    orglevelcodes = pd.read_csv(code_files['orglevelcodes'])
    statusreasoncodes = pd.read_csv(code_files['statusreasoncodes'])
    columncodes = pd.read_csv(code_files['columncodes'])
    primarysubjectcodes = pd.read_csv(code_files['primarysubjectcodes'])

    # Duplicate dataset to avoid modifying the original
    unique_expanded_submissions = unique_submissions.copy()

    # Duplicate 'cdsub1cb' column for translation
    unique_expanded_submissions['cdsub1cbTEXT'] = unique_expanded_submissions['cdsub1cb']

    # Replace codes with translations from code files
    unique_expanded_submissions['cdsub1cbTEXT'] = unique_expanded_submissions['cdsub1cbTEXT'].map(complaintcodes.set_index('Code')['Text']).fillna(unique_expanded_submissions['cdsub1cb'])
    unique_expanded_submissions['CDFCLEVN'] = unique_expanded_submissions['CDFCLEVN'].map(facilitycodes.set_index('Facility_Code')['Facility_Name']).fillna(unique_expanded_submissions['CDFCLEVN'])
    unique_expanded_submissions['CDFCLRCV'] = unique_expanded_submissions['CDFCLRCV'].map(facilitycodes.set_index('Facility_Code')['Facility_Name']).fillna(unique_expanded_submissions['CDFCLRCV'])
    unique_expanded_submissions['CDOFCRCV'] = unique_expanded_submissions['CDOFCRCV'].map(facilitycodes.set_index('Facility_Code')['Facility_Name']).fillna(unique_expanded_submissions['CDOFCRCV'])
    unique_expanded_submissions['ITERLVL'] = unique_expanded_submissions['ITERLVL'].map(orglevelcodes.set_index('Code')['Text']).fillna(unique_expanded_submissions['ITERLVL'])
    unique_expanded_submissions['CDSTATUS'] = unique_expanded_submissions['CDSTATUS'].map(statuscodes.set_index('Code')['Text']).fillna(unique_expanded_submissions['CDSTATUS'])

    # Replace status reason codes
    for col in ['STATRSN1', 'STATRSN2', 'STATRSN3', 'STATRSN4', 'STATRSN5']:
        unique_expanded_submissions[col] = unique_expanded_submissions[col].map(
            statusreasoncodes.set_index('Reason Code')['Text']).fillna(unique_expanded_submissions[col])

    # Translate primary subject codes
    unique_expanded_submissions['CDSUB1PR'] = unique_expanded_submissions['CDSUB1PR'].map(primarysubjectcodes.set_index('Primary Subject Code')['Primary Subject Code Translation']).fillna(unique_expanded_submissions['CDSUB1PR'])

    # Replace null values in 'sdtdue' for rejected statuses
    unique_expanded_submissions['sdtdue'] = unique_expanded_submissions['sdtdue'].fillna('rejected')

    # Replace binary values with 'yes' and 'no' for clarity
    binary_columns = [
        'accept', 'reject', 'deny', 'grant', 'other', 'submit', 'filed', 'closed',
        'diffreg_filed', 'diffinst', 'timely', 'diffreg_answer', 'overdue',
        'untimely', 'resubmit', 'noinfres', 'attachmt', 'wronglvl', 'otherrej'
    ]
    for col in binary_columns:
        unique_expanded_submissions[col] = unique_expanded_submissions[col].replace({0: 'no', 1: 'yes'})

    # Load column code CSV as a dictionary and rename columns
    columncodes_dict = dict(zip(columncodes['Code'], columncodes['Text']))
    unique_expanded_submissions.rename(columns=columncodes_dict, inplace=True)

    # Save expanded unique dataset to a CSV file
    unique_expanded_output_file = f"{output_path}/{state_code}_UniqueComplaintsEnrichedExpanded.csv"
    unique_expanded_submissions.to_csv(unique_expanded_output_file, index=False)
    print(f"Unique expanded submissions for state '{state_code}' saved to {unique_expanded_output_file}.")

    return unique_expanded_submissions


# %%
# Define paths
state_code = input("Enter the state code (e.g., 'NY', 'CA'): ").strip().upper()
input_facilities_path = '../data/CDFC_FacilityCodes.csv'
input_submissions_path = '../data/ComplaintFilings.csv'
output_path = '../results/data'
code_files = {
    'complaintcodes': '../data/cdsub1cb_ConcatSubjectCodes.csv',
    'facilitycodes': '../data/CDFC_FacilityCodes.csv',
    'statuscodes': '../data/CDSTATUS_CaseStatusCodes.csv',
    'orglevelcodes': '../data/ITERLVL_OrgLevelCodes.csv',
    'statusreasoncodes': '../data/STATRSN_StatusReasonCodes.csv',
    'columncodes': '../data/ColumnCodes.csv',
    'primarysubjectcodes': '../data/CDSUB1PR _PrimarySubjectCodes.csv'
}

# Execute steps
filtered_data = filter_submissions(state_code, input_facilities_path, input_submissions_path, output_path)
enriched_data = enrich_submissions(filtered_data, output_path, state_code)
expanded_data = expand_submissions(enriched_data, output_path, state_code, code_files)
unique_data = create_unique_submissions(enriched_data, output_path, state_code)
expand_unique_submissions(unique_data, output_path, state_code, code_files)
# %%
import subprocess

# Define the path to your R script
r_script_path = "analysis.R"

# Run the R script and pass the state_code as an argument
try:
    subprocess.run(
        ["Rscript", r_script_path, state_code],
        check=True  # Raises an error if the R script fails
    )
    print(f"R script executed successfully for state: {state_code}")
except subprocess.CalledProcessError as e:
    print(f"Error occurred while running the R script: {e}")





