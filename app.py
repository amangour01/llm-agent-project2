import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API key
api_key = os.getenv('AIPROXY_TOKEN')

def create_llm_response(question):
    # System prompt that instructs the model how to respond
    system_prompt = """
   
    """
    
def create_llm_response(question):
    # System prompt that instructs the model how to respond
    system_prompt = """
    - You are an LLM agent solving assignment questions for IIT Madras’ Online Degree course in Data Science, specifically in the "Tools in Data Science" course.
    - Your task is to accurately answer questions from the graded assignments.
    - You will be provided with a question and with required file if needed.
    
    How to approach problem -
    1. Focus on accuracy and precision.
    2. If the question involves calculations, code or anything else just execute it and provide the final answer.
    3. Befor finalizing the answer deeply think about question, take your time, then iteratively execute your solution and check for answer then at last provide final answer.
    4. Solve every problem by writing python code.

    Output format -
    1. Your response must be **strictly structured** as a JSON object with a **single key: "answer"**.
    2. Return only the final answer inside the "answer" key. Do not include explanations or formatting.
    3. Your response **must follow this JSON format**:
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
                "tools": [function_schema],  # Corrected placement of function schema
                "tool_choice": {"type": "function", "function": {"name": "get_answer"}}  # Ensure function calling
            },
            verify=False,  # Disable SSL verification (optional: for avoiding warning)
        )

        response.raise_for_status()  # Raise an exception for HTTP errors

        # Extract the response
        response_data = response.json()
        print(json.dumps(response_data, indent=4))  # Debugging output

        # Extract answer from tool call response
        if 'choices' in response_data and response_data['choices']:
            tool_call = response_data['choices'][0].get("message", {}).get("tool_calls", [{}])[0]
            function_args = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            return json.dumps(function_args)  # Ensure valid JSON output
        else:
            return json.dumps({"answer": "Error: Invalid response format."})

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return json.dumps({"answer": "Error: Unable to process the request."})
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON response.")
        return json.dumps({"answer": "Error: Invalid JSON response."})

# Example usage
def main():
    question = "IRunning uv run --with httpie -- https [URL] installs the Python package httpie and sends a HTTPS request to the URL.\
            Send a HTTPS request to https://httpbin.org/get with the URL encoded parameter email set to aman.gour@gramener.com \
            What is the JSON output of the command? (Paste only the JSON body, not the headers)"'
    
    A1_question_4= """Let's make sure you can write formulas in Google Sheets. Type this formula into Google Sheets. (It won't work in Excel)\
        =SUM(ARRAY_CONSTRAIN(SEQUENCE(100, 100, 2, 10), 1, 10))\
        What is the result?\
        instructions - Before finalizing the answer deeply think about question, take your time, then iteratively execute your solution and check for answer then at last provide final answer.
    """
    A1_question_5 = """Let's make sure you can write formulas in Excel. Type this formula into Excel.
        Note: This will ONLY work in Office 365.
        =SUM(TAKE(SORTBY({0,7,2,5,7,12,10,5,7,14,8,9,4,11,3,10}, {10,9,13,2,11,8,16,14,7,15,5,4,6,1,3,12}), 1, 6))
        What is the result?
        instructions - Before finalizing the answer deeply think about question, take your time, then iteratively execute your solution and check for answer then at last provide final answer.
    """
    
    A1_question_7 = """
        How many Wednesdays are there in the date range 1988-11-25 to 2015-09-19?
        The dates are in the year-month-day format. Include both the start and end date in your count. You can do this using any tool (e.g. Excel, Python, JavaScript, manually).
        instructions - Before finalizing the answer deeply think about question, take your time, then iteratively execute your solution and check for answer then at last provide final answer.
    """
    answer = create_llm_response(A1_question_7)
    print("\nResponse:")
    print(answer)

main()