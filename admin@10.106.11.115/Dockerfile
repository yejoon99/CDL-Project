# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt ./
COPY data_1.csv ./
COPY final_nn_model.pkl ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's source code from your host to your image filesystem.
COPY . .

# Command to run your Python script when the container launches
CMD ["python", "./script.py"]
