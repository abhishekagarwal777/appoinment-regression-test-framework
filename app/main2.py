import os
import multiprocessing
from shutil import copyfile
from fastapi import FastAPI, File, UploadFile
import dotenv
import subprocess
import datetime

app = FastAPI()
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
TEST_CASES_SOURCE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test-cases")
dotenv.load_dotenv(os.path.join(ROOT_DIR, ".env"))

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")

class Job:
    def __init__(self, test_case_file_path: str):
        self.test_case_file_path = test_case_file_path
        self.result = None 
    def run(self, results_dir: str):
        _script = os.path.join(ROOT_DIR, 'unit-test.py')
        subprocess.Popen(["python", _script, "-tc", self.test_case_file_path], stdin=subprocess.DEVNULL, shell=False, start_new_session=True, env=os.environ)

        result_file = f"{os.path.basename(self.test_case_file_path)}.out"
        result_path = os.path.join(results_dir, result_file)

        if os.path.exists(result_path) and "pass" in open(result_path).read():
            self.result = "pass"
        else:
            self.result = "fail"

# class TestFailed(Exception):
#     def __init__(self, *args: object) -> None:
#         super().__init__(*args)
#         print(args)
#         sys.exit(1)

# test_case_file_path = args.test_case

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

        pass_dir = os.path.join(results_dir, "Pass")
        fail_dir = os.path.join(results_dir, "Fail")
        os.makedirs(pass_dir, exist_ok=True)
        os.makedirs(fail_dir, exist_ok=True)

        pass_count = 0
        fail_count = 0

        for job in self.jobs:
            job.run(results_dir)
            if job.result == "pass":
                pass_count += 1
                result_path = os.path.join(pass_dir, f"{os.path.basename(job.test_case_file_path)}.out")
                copyfile(job.test_case_file_path, result_path)
            else:
                fail_count += 1
                result_path = os.path.join(fail_dir, f"{os.path.basename(job.test_case_file_path)}.out")
                copyfile(job.test_case_file_path, result_path)

        summary_report = os.path.join(results_dir, "summary.tc")
        with open(summary_report, "w") as summary_file:
            summary_file.write(f"Passed: {pass_count}\nFailed: {fail_count}")


@app.post("/testcase")
def save_test_case(category: str, test_case_name: str, test_case_file: UploadFile = File(...)):
    destination_path = os.path.join(TEST_CASES_SOURCE_DIR, category)
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
    destination_path = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_name)
    with open(destination_path, "wb") as fd:
        fd.write(test_case_file.file.read())
    return "Ok"

# job_store = JobStore("my_job_store")
# job_store.add_job("/path/to/test_case_1.tc")
# job_store.add_job("/path/to/test_case_2.tc")
# job_store.add_job("/path/to/test_case_3.tc")

# job_store.run()


def run_test_case(category: str, test_case_file_name: str):
    test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
    if not os.path.exists(test_case_file):
        return f"Test case file {test_case_file_name} not found in category {category}"

    _script = os.path.join(ROOT_DIR, 'unit-test.py')
    
    job_store_name = f"{category}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    job_store = JobStore(name=job_store_name)
    job_store.add_job(test_case_file_path=test_case_file)
    job_store.run()
    
    return f"Executed test case {test_case_file_name} in category {category}. Job Store: {job_store_name}"

@app.put("/run/{category}/{test_case_file_name}")
def run_test_case(category: str, test_case_file_name: str):
    test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
    if not os.path.exists(test_case_file):
        return f"Test case file {test_case_file_name} not found in category {category}"

    _script = os.path.join(ROOT_DIR, 'unit-test.py')

    output_file_path = f"{os.path.basename(test_case_file)}.out"

    subprocess.Popen(["python", _script, "-tc", test_case_file], stdin=subprocess.DEVNULL, shell=False, start_new_session=True, env=os.environ)

    return f"Executed test case {test_case_file_name}"


@app.put("/run/{category}")
def run_category(category: str):
    category_path = os.path.join(TEST_CASES_SOURCE_DIR, category)
    if not os.path.exists(category_path):
        return f"Category {category} not found"

    job_store_name = f"{category}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    job_store = JobStore(name=job_store_name)

    for test_case_file_name in os.listdir(category_path):
        if test_case_file_name.endswith(".tc"):
            test_case_file = os.path.join(TEST_CASES_SOURCE_DIR, category, test_case_file_name)
            job_store.add_job(test_case_file_path=test_case_file)

    job_store.run()

    return f"Executed all test cases in category {category}. Job Store: {job_store_name}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)

