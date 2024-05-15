import os
import pandas as pd
import pickle
import time
import warnings
import json
import requests

# Ignore all warnings
warnings.filterwarnings("ignore")

# Function to load the pickled model
def load_model(filename):
    with open(filename, 'rb') as file:
        model = pickle.load(file)
    return model

# Function to post JSON data to FastAPI
def post_to_fastapi(json_data, url):
    response = requests.post(url, json=json_data)
    return response

# Function to continuously process data row by row, excluding the target column
def process_data_row_by_row(model, directory, fastapi_url):
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
                    
                    # Create a JSON object for the prediction
                    result = {
                        "key": prediction.tolist()  # Assuming the endpoint expects the key 'key'
                    }
                    
                    # Post to FastAPI
                    response = post_to_fastapi(result, fastapi_url + "/inference/")
                    
                    # Print response from the FastAPI server
                    print(f"Prediction for {data_filename} at row {index}:", prediction)
                    print("Response from FastAPI:", response.status_code, response.text)
                    
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
    fastapi_url = 'http://localhost:8000'  # Base URL of your FastAPI endpoint
    process_data_row_by_row(model, directory, fastapi_url)
