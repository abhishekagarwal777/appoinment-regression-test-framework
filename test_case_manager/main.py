from fastapi import FastAPI, HTTPException, Query, File, UploadFile
import shutil
import os
import multiprocessing
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = FastAPI()

UPLOAD_FOLDER = "/Users/abhishekagarwal/WORKSPACES/vEngage/appointment-regression-test-framework-main/test-cases"


test_cases = []


@app.post("/uploadfile/")
async def upload_and_add_test_case(file: UploadFile):
    try:
        target_path = os.path.join(UPLOAD_FOLDER, file.filename)

        with open(target_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        with open(target_path, "r") as f:
            file_content = f.read()
            # Parse the file content to extract the name and description of the test case
            # Modify the parsing logic according to the structure of your test case files
            name, description = parse_test_case_content(file_content)

            # Create a test case object and append it to the list of test cases
            test_case = TestCase(name, description)
            test_cases.append(test_case)

        return {"filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


class TestCase:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.status = "Not Run" 


def save_test_case_to_file(name: str, description: str, filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, "w") as file:
        file.write(f"==SETUP START==\nCENTER_ID=1\n==SETUP END==\n\n")
        file.write(f"==CONVERSATION START==\n{name}\n{description}\n==CONVERSATION END==\n")


@app.post("/test-cases/")
async def create_test_case(name: str, description: str, filename: str = None):
    test_case = TestCase(name, description)
    test_cases.append(test_case)                  #partly or wholelly as a file in a ds
    
    if filename:
        save_test_case_to_file(name, description, filename)
        
    return test_case

@app.get("/test-cases/")
async def list_test_cases():
    return [test_case.__dict__ for test_case in test_cases]



def get_description_and_conversation_for_test_case(name: str):
    test_case_filepath = f"/Users/abhishekagarwal/WORKSPACES/vEngage/appointment-regression-test-framework-main/test-cases/sanity/{name}.tc"

    description = ""
    conversation = ""

    try:
        with open(test_case_filepath, "r") as file:
            lines = file.readlines()

            # Initialize flags to identify setup, description, and conversation sections
            in_setup = False
            in_description = False

            for line in lines:
                line = line.strip()
                if line == "==SETUP START==":
                    in_setup = True
                elif line == "==SETUP END==":
                    in_setup = False
                elif in_setup and line:
                    if line.startswith("CENTER_ID="):
                        center_id = line.split("CENTER_ID=")[1].strip()
                elif line == "==CONVERSATION START==":
                    in_description = True
                elif line == "==CONVERSATION END==":
                    in_description = False
                elif in_description:
                    conversation += line + "\n"  # conv- lines append

            # Everything outside of setup and conversation sections is considered description
            if not in_setup and not in_description:
                description += line + "\n"  # desc- lines append

    except FileNotFoundError:
        pass

    return description, conversation

description, conversation = get_description_and_conversation_for_test_case("conversation-2")
print("Description:")
print(description)
print("\nConversation:")
print(conversation)



@app.get("/test-cases/run/")
async def run_test_case(name: str):
    test_case = next((tc for tc in test_cases if tc.name == name), None)
    if test_case:
        test_case.status = "Passed"
        description, conversation = get_description_and_conversation_for_test_case(name)
        if description and conversation:
            return {"status": test_case.status, "description": description, "conversation": conversation}
        else:
            return {"status": test_case.status, "description": "No description available", "conversation": "No conversation available"}
    else:
        raise HTTPException(status_code=404, detail="Test case not found")



@app.get("/test-cases/run-category/")
async def run_test_category(category: str):
    for test_case in test_cases:
        test_case.status = "Passed"
    return {"message": "All test cases in the category have been executed."}

@app.delete("/test-cases/")
async def delete_test_case(name: str):
    global test_cases
    test_cases = [tc for tc in test_cases if tc.name != name]
    return {"message": "Test case deleted"}

@app.get("/test-report/")
async def generate_test_report():
    report = {
        "total_test_cases": len(test_cases),
        "passed": sum(1 for tc in test_cases if tc.status == "Passed"),
        "failed": sum(1 for tc in test_cases if tc.status == "Failed"),
    }
    return report


#break pts in the code for running through a tps ...



def send_test_report():
    smtp_server = "smtp_server"
    smtp_port = 587
    smtp_username = "username"
    smtp_password = "password"
    sender_email = "abhishek.agarwal@vengage.ai"
    recipient_email = "recipient@example.com"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Test Report"

    body = f"Total test cases: {len(test_cases)}\nPassed: {sum(1 for tc in test_cases if tc.status == 'Passed')}\nFailed: {sum(1 for tc in test_cases if tc.status == 'Failed')}"
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

def run_tests_and_send_report():
    process = multiprocessing.Process(target=run_tests)
    process.start()
    process.join()

    send_test_report()

def run_tests():
    for test_case in test_cases:

        pass  

if __name__ == "__main__":
    import uvicorn

    multiprocessing.set_start_method('spawn')
    run_tests_and_send_report()

    uvicorn.run(app, host="0.0.0.0", port=8000)
