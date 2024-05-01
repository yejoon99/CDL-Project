import os
import pandas as pd
import pickle
import time
import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")


# Function to load the pickled model
def load_model(filename):
    with open(filename, 'rb') as file:
        model = pickle.load(file)
    return model

# Function to continuously process data row by row, excluding the target column
def process_data_row_by_row(model, directory):
    # List all CSV files that start with "data_"
    data_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.startswith('data_') and file.endswith('.csv')]
    while True:
        for data_filename in data_files:
            # Ensure the file exists before attempting to open it
            if os.path.exists(data_filename):
                # Read the entire CSV file
                data = pd.read_csv(data_filename)
                # Drop the 'target' column if it exists
                if 'target' in data.columns:
                    data.drop(columns=['target'], inplace=True)
                # Iterate through each row
                for index, row in data.iterrows():
                    # Process each row with the model
                    prediction = model.predict([row])
                    # Print or handle the prediction
                    print(f"Prediction for {data_filename}:", prediction)
                    # Sleep for 3 seconds before processing the next row
                    time.sleep(0.5)
                print(f"Reached the end of the file {data_filename}, moving to the next file...")
            else:
                print(f"File {data_filename} does not exist.")
        print("Completed all files, starting over...")
        # Refresh the file list in case new files are added
        data_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.startswith('data_') and file.endswith('.csv')]

# Main execution flow
if __name__ == "__main__":
    model = load_model('final_nn_model.pkl')
    directory = os.getcwd()  # Set the directory to the current working directory
    process_data_row_by_row(model, directory)
