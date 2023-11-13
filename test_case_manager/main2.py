import os
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException    

from conversation_executor import ConversationExecutor


app = FastAPI()

TEST_CASES_SOURCE_DIR = "/Users/abhishekagarwal/WORKSPACES/vEngage/appointment-regression-test-framework-main/test-cases" 

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
TEST_CASES_SOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),"test-cases")

@app.post("/testcase")
def save_test_case(category:str, test_case_name:str, test_case_file:UploadFile=File(...)):
    destination_path = os.path.join(TEST_CASES_SOURCE_DIR, category)
    print(destination_path)
    if os.path.exists(destination_path) == False:
        os.makedirs(destination_path)
    destination_path = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_name)
    with open(destination_path, "wb") as fd:
        fd.write(test_case_file.file.read())
    return "Ok"

@app.put("/run/{category}")
def run_category():
    return "Ok"



import subprocess

@app.put("/run/{category}/{test_case_file_name}")
def run_test_case(category: str, test_case_file_name: str):
    test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
    if not os.path.exists(test_case_file):
        return "Test case file not found"

    _script = os.path.join(ROOT_DIR, 'unit-test.py')

    try:
        result = subprocess.run(['python', _script, "-tc", test_case_file, "--center-id", "15"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            output = result.stdout  
        else:
            output = f"Test case execution failed: {result.stderr}"
    except Exception as e:
        output = f"Test case execution failed: {str(e)}"

    return output



# def run_test_case(category: str, test_case_file_name: str):
#     test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
    
#     if not os.path.exists(test_case_file):
#         raise HTTPException(status_code=404, detail="Test case file not found")

#     try:
#         result = subprocess.run(['python', test_case_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#         if result.returncode == 0:
#             output = result.stdout
#         else:
#             output = f"Test case execution failed: {result.stderr}"
#     except Exception as e:
#         output = f"Test case execution failed: {str(e)}"

#     return output














# @app.put("/run/{category}/{test_case_file_name}")

# def run_test_case(category: str, test_case_file_name: str):
#     test_case_file_path = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)

#     if not os.path.exists(test_case_file_path):
#         raise HTTPException(status_code=404, detail="Test case file not found")

#     try:
#         with open(test_case_file_path, 'r') as file:
#             conversation = file.read()

#         output = simulate_conversation(conversation)

#     except Exception as e:
#         output = f"Test case execution failed: {str(e)}"

#     return output

# def simulate_conversation(conversation_text):
#     conversation_lines = conversation_text.splitlines()
#     output_lines = []

#     for line in conversation_lines:
#         if line.startswith("[User]"):
#             user_input = line[len("[User]"):].strip()
#             response = simulate_user_input(user_input)
#             output_lines.append(f"[Bot] {response}")
#         elif line.startswith("[Bot]"):
#             output_lines.append(line)

#     return "\n".join(output_lines)

# def simulate_user_input(user_input):
#     return user_input











# def create_conversation_executor():
#     return ConversationExecutor()

# conversation_executor = ConversationExecutor()

# @app.put("/run/{category}/{test_case_file_name}")
# def run_test_case(category: str, test_case_file_name: str):
#     test_case_file_path = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)

#     if not os.path.exists(test_case_file_path):
#         raise HTTPException(status_code=404, detail="Test case file not found")

#     try:
#         conversation_executor = create_conversation_executor()

#         with open(test_case_file_path, 'r') as file:
#             conversation = file.read()

#         print("Received conversation:")
#         print(conversation) 

#         # Simulate the conversation using the conversation_executor
#         output = conversation_executor.simulate_conversation(conversation)

#         print("Test case execution output:")
#         print(output) 

#         if output is None:
#             raise HTTPException(status_code=500, detail="Test case execution returned an empty result")

#     except Exception as e:
#         output = f"Test case execution failed: {str(e)}"

#     return output








# @app.put("/run/{category}/{test_case_file_name}")
# def run_test_case(category:str, test_case_file_name:str):
#     test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
#     if not os.path.exists(test_case_file):
#         return "Test case file not found"
    
#     _script = os.path.join(ROOT_DIR, 'pseudocode.py')
    
#     subprocess.run(args=[_script, "-tc", test_case_file, "--center-id", "15"], executable="python" )
#     return "Ok"