# app.py
from fastapi import FastAPI, HTTPException, Request
import os
import json
from typing import Dict

app = FastAPI()

# Logs directory and file setup
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "inference_logs.txt")

@app.get("/", summary="Root endpoint")
def read_root():
    return {"Hello": "World"}

@app.post("/inference/", summary="Save JSON data to text file")
async def inference(request: Request):
    try:
        # Get JSON data from request body
        json_data = await request.json()
        # Write JSON data to a text file
        with open(log_file, "a") as f:
            f.write(json.dumps(json_data) + "\n")
        return {"message": log_file}
    except Exception as e:
        print(f"Error writing to log file: {e}")
        raise HTTPException(status_code=500, detail="Could not write to log file")

    return {"message": "Inference data saved successfully"}

@app.get("/inference/", summary="Retrieve all inference data")
def get_all_inference_data():
    try:
        # Read all lines from the text file
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            return [json.loads(line.strip()) for line in all_lines]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Inference log file not found")
    except Exception as e:
        print(f"Error reading log file: {e}")
        raise HTTPException(status_code=500, detail="Error reading inference log file")
