import subprocess
import sys

def run_analysis():
    # Ask user to enter the state code/all
    state_code = input("Enter the state code (e.g., 'NY', 'CA', 'DC', or 'ALL'): ").strip().upper()
    
    # Define the paths for the python script and R script
    main_python_script = "FilterStateData.py"
    r_script = "StateAnalysis.R"

    # Run the main Python script with the chosen state_code
    try:
        print(f"Running the Python script for: {state_code}")
        subprocess.run(
            [sys.executable, main_python_script, state_code],
            check=True  # Raises an error if the script fails
        )
        print(f"Python script executed successfully for: {state_code}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the Python script: {e}")
        return

    # Step 2: Run the R script with the chosen state_code
    try:
        print(f"Running the R script for: {state_code}")
        subprocess.run(
            ["Rscript", r_script, state_code],
            check=True  # Raises an error if the script fails
        )
        print(f"R script executed successfully for state: {state_code}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running the R script: {e}")

# Entry point
if __name__ == "__main__":
    run_analysis()
