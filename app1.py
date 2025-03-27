import os
import json
import shutil
import requests
import zipfile
import pandas as pd
from fastapi import FastAPI, File, UploadFile, Form
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API key
api_key = os.getenv("AIPROXY_TOKEN")

# Initialize FastAPI
app = FastAPI()

# OpenAI System Prompt
system_prompt = """
- You are an LLM agent solving assignment questions for IIT Madras’ Online Degree course in Data Science, specifically in the "Tools in Data Science" course.
- Your task is to accurately answer questions from the graded assignments.
- You will be provided with a question and an optional file if needed.
- **Your response must be structured as JSON with a single key: "answer"**.

Output format:
{
  "answer": "Your final answer here"
}
"""

# Define function schema to enforce JSON output
function_schema = {
    "type": "function",
    "function": {
        "name": "get_answer",
        "description": "Returns a JSON object containing only the final answer",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The final answer to the question"
                }
            },
            "required": ["answer"]
        }
    }
}


# OpenAI API request function
def query_openai(question):
    try:
        response = requests.post(
            "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0,
                "tools": [function_schema],  # Enforcing JSON format
                "tool_choice": {"type": "function", "function": {"name": "get_answer"}}
            },
            verify=False,
        )

        response.raise_for_status()
        response_data = response.json()

        # Extract answer from tool call response
        if 'choices' in response_data and response_data['choices']:
            tool_call = response_data['choices'][0].get("message", {}).get("tool_calls", [{}])[0]
            function_args = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            return function_args  # Ensure valid JSON output
        else:
            return {"answer": "Error: Invalid response format."}

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return {"answer": "Error: Unable to process the request."}
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON response.")
        return {"answer": "Error: Invalid JSON response."}


# API Endpoint
@app.post("/api/")
async def process_question(question: str = Form(...), file: UploadFile = File(None)):
    """
    API Endpoint to accept a question and an optional file, process it, and return the answer.
    """

    # If a file is uploaded, save and process it
    if file:
        file_location = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)

        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Handle ZIP file extraction
        if file.filename.endswith(".zip"):
            extract_folder = "temp/extracted"
            os.makedirs(extract_folder, exist_ok=True)

            with zipfile.ZipFile(file_location, "r") as zip_ref:
                zip_ref.extractall(extract_folder)

            # Find the extracted CSV file
            extracted_files = os.listdir(extract_folder)
            csv_file = next((f for f in extracted_files if f.endswith(".csv")), None)

            if csv_file:
                csv_path = os.path.join(extract_folder, csv_file)
                df = pd.read_csv(csv_path)

                # Extract the "answer" column if present
                if "answer" in df.columns:
                    answer_value = str(df["answer"].iloc[0])
                    return {"answer": answer_value}

    # If no file or answer extracted, query OpenAI
    return query_openai(question)
