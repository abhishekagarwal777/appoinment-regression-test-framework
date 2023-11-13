from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

class Conversation(BaseModel):
    setup: str
    conversation: str

def run_test_cases():
    conversation_script = '''
    ==SETUP START==
    CENTER_ID=1
    ==SETUP END==

    ==CONVERSATION START==
    [thanks for calling] are you looking for new appointment >>> yes
    Please read out the [requested scan] as mentioned by your doctor in the referral letter >>> US hand
    You have requested for us hand . [Is that correct?] >>> yes that is correct
    [When would you like to visit us?] >>> today at 1pm
    ==CONVERSATION END==
    '''
    return {"conversation_script": conversation_script}

@app.get("/run_tests/", response_model=Dict[str, str], summary="Run test cases", description="Executes test cases and returns the conversation script.")
def run_tests():
    test_results = run_test_cases()
    return test_results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)




import os
from fastapi import FastAPI, File, UploadFile

app = FastAPI()
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
def run_test_case(category:str, test_case_file_name:str):
    test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
    if not os.path.exists(test_case_file):
        return "Test case file not found"
    
    _script = os.path.join(ROOT_DIR, 'unit-test.py')
    
    subprocess.run(args=[_script, "-tc", test_case_file, "--center-id", "15"], executable="python" )
    return "Ok"