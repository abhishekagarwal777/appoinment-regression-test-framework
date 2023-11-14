import os
import multiprocessing
from shutil import copyfile
from fastapi import FastAPI, File, UploadFile
import dotenv
import subprocess

command = ['python', 'script.py']
subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


app = FastAPI()
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
TEST_CASES_SOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),"test-cases")
dotenv.load_dotenv(os.path.join(ROOT_DIR, ".env"))

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")

class Job:
    def __init__(self, test_case_file_path: str):
        self.test_case_file_path = test_case_file_path


     def run(self, results_dir: str):
        _script = os.path.join(ROOT_DIR, 'unit-test.py')
        subprocess.Popen(["python", _script, "-tc", self.test_case_file_path], stdin=subprocess.DEVNULL, shell=False, start_new_session=True, env=os.environ)

        result = "pass" 

        result_dir = os.path.join(results_dir, result)
        os.makedirs(result_dir, exist_ok=True)
        copyfile(self.test_case_file_path, os.path.join(result_dir, os.path.basename(self.test_case_file_path)))



class JobStore:
    def __init__(self, name: str):
        self.name = name
        self.jobs = []

    def add_job(self, test_case_file_path: str):
        job = Job(test_case_file_path)
        self.jobs.append(job)

    def run(self):
        results_dir = os.path.join(RESULTS_DIR, self.name)
        os.makedirs(results_dir, exist_ok=True)

        with multiprocessing.Pool() as pool:
            pool.starmap(Job.run, [(job, results_dir) for job in self.jobs])


        
def run_test_case(category: str, test_case_file_name: str):
    test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
    if not os.path.exists(test_case_file):
        return f"Test case file {test_case_file_name} not found in category {category}"

    _script = os.path.join(ROOT_DIR, 'unit-test.py')
    
    output_file_path = f"{os.path.basename(test_case_file)}.out"
    
    subprocess.Popen(["python", _script, "-tc", test_case_file], stdin=subprocess.DEVNULL, shell=False, start_new_session=True, env=os.environ)
    
    return f"Executed test case {test_case_file_name}"



@app.post("/testcase")
def save_test_case(category: str, test_case_name: str, test_case_file: UploadFile = File(...)):
    destination_path = os.path.join(TEST_CASES_SOURCE_DIR, category)
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
    destination_path = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_name)
    with open(destination_path, "wb") as fd:
        fd.write(test_case_file.file.read())
    return "Ok"

@app.put("/run/{category}")
def run_category(category: str):
    category_path = os.path.join(TEST_CASES_SOURCE_DIR, category)
    if not os.path.exists(category_path):
        return f"Category {category} not found"

    for test_case_file_name in os.listdir(category_path):
        if test_case_file_name.endswith(".tc"):
            run_test_case(category, test_case_file_name)

    return f"Executed all test cases in category {category}"


@app.put("/run/{category}/{test_case_file_name}")
def run_test_case(category: str, test_case_file_name: str):
    test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
    if not os.path.exists(test_case_file):
        return "Test case file not found"

    _script = os.path.join(ROOT_DIR, 'unit-test.py')
    
    output_file_path = f"{os.path.basename(test_case_file)}.out"
    
    # with open(output_file_path, "w") as fd:
    subprocess.Popen(["python", _script, "-tc", test_case_file], stdin=subprocess.DEVNULL, shell=False, start_new_session=True, env=os.environ)
    
    return "Ok"



if __name__ == "__main__":
    job_store = JobStore(name="2023-11-01_12-59-45")
    job_store.add_job(test_case_file_path="/results/<JobStore/test_case_1.tc")
    job_store.add_job(test_case_file_path="/results/<JobStore/test_case_2.tc")
    
    job_store.run()
    