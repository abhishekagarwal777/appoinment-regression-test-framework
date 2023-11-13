from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from typing import List
import os
import requests
from uuid import uuid4
import multiprocessing
from functools import partial

app = FastAPI()

SMTP_SERVER = "smtp_server"
SMTP_PORT = 587
SMTP_USERNAME = "username"
SMTP_PASSWORD = "password"
SENDER_EMAIL = "abhishek.agarwal@vengage.ai"

class TestCategory(BaseModel):
    setup: str
    category: str

class TestReport(BaseModel):
    email: str

categories = {}

def send_test_report(email, passed, failed):
    msg = MIMEMultipart()
    msg['From'] = 'abhishek.gupta@vengage.ai'
    msg['To'] = email
    msg['Subject'] = "Test Report"

    body = f"{passed} test cases passed, {failed} test cases failed."
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())

@app.post("/categories/{category}", response_model=TestCategory)
def create_category(category: str, item: TestCategory):
    if category not in categories:
        categories[category] = []
    categories[category].append(item)
    return item

@app.get("/categories/{category}", response_model=List[TestCategory])
def get_category(category: str):
    if category in categories:
        return categories[category]
    raise HTTPException(status_code=404, detail="Category not found")

@app.put("/categories/{category}/{index}", response_model=TestCategory)
def update_category(category: str, index: int, item: TestCategory):
    if category in categories and 0 <= index < len(categories[category]):
        categories[category][index] = item
        return item
    raise HTTPException(status_code=404, detail="Category not found")

@app.delete("/categories/{category}/{index}", response_model=TestCategory)
def delete_category(category: str, index: int):
    if category in categories and 0 <= index < len(categories[category]):
        deleted_category = categories[category].pop(index)
        return deleted_category
    raise HTTPException(status_code=404, detail="Category not found")

def run_tests(email, category, report_queue):
    # Replace this with your test execution logic
    # Your existing test execution logic should go here
    # Run the test cases, collect results, and send the results to the queue
    try:
        # Your existing test execution code here
        # ...
        # Test results
        passed = 5
        failed = 2

        report_queue.put((email, passed, failed))
    except Exception as e:
        report_queue.put((email, 0, 1))  # Mark test as failed

@app.post("/trigger_tests/{category}", response_model=dict)
def trigger_tests_and_send_report(category: str, report: TestReport):

    if category not in categories:
        raise HTTPException(status_code=404, detail="Category not found")

    report_queue = multiprocessing.Queue()

    processes = []

    for item in categories[category]:
        email = report.email
        p = multiprocessing.Process(target=run_tests, args=(email, category, report_queue))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # Collect results from the queue
    total_passed = 0
    total_failed = 0
    while not report_queue.empty():
        email, passed, failed = report_queue.get()
        total_passed += passed
        total_failed += failed

    send_test_report(report.email, total_passed, total_failed)

    return {"message": "Tests triggered and report sent successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)































# from fastapi import FastAPI, HTTPException, Query
# from pydantic import BaseModel
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# import smtplib
# import os
# import re
# import datetime
# import requests
# import threading
# import websocket
# from uuid import uuid4

# app = FastAPI()

# # Data Models
# class TestCase(BaseModel):
#     name: str
#     category: str
#     status: str

# param_patterns = {
#     "CENTER_ID": r"CENTER_ID=(\d+)",
#     "BLOCK-TIME-RANGE": r"BLOCK-TIME-RANGE",
#     "MODALITY": r"MODALITY=([\w\s]+)",
#     "SDATE": r"SDATE=([\w\d\+\-]+)",
#     "STIME": r"STIME=([\d:]+)",
#     "ETIME": r"ETIME=([\d:]+)",
# }

# # Email configuration
# SMTP_SERVER = "your_smtp_server"
# SMTP_PORT = 587
# SMTP_USERNAME = "your_username"
# SMTP_PASSWORD = "your_password"
# SENDER_EMAIL = "your_email"

# def send_test_report(email, passed, failed):
#     msg = MIMEMultipart()
#     msg['From'] = SENDER_EMAIL
#     msg['To'] = email
#     msg['Subject'] = "Test Report"

#     body = f"{passed} test cases passed, {failed} test cases failed."
#     msg.attach(MIMEText(body, 'plain'))

#     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
#         server.starttls()
#         server.login(SMTP_USERNAME, SMTP_PASSWORD)
#         server.sendmail(SENDER_EMAIL, email, msg.as_string())

# # Simulated test data and database
# test_cases_db = []

# class TestFailed(Exception):
#     pass

# def calculate_date_for_asked_iso_weekday_from_ref_date(ref_date: datetime.datetime, iso_weekday: int):
#     # Add your date calculation logic here
#     pass

# # Your functions for executing test cases
# def execute_setup_instruction(instruction: str):
#     # Add your setup instruction execution logic here
#     pass

# # FastAPI route to trigger tests and send a report
# @app.post("/trigger_tests/")
# def trigger_tests_and_send_report(email: str):
#     # Simulated test data (replace with actual test data)
#     test_cases = [
#         TestCase(name="Test Case 1", category="sanity", status="passed"),
#         TestCase(name="Test Case 2", category="sanity", status="failed"),
#         TestCase(name="Test Case 3", category="service request", status="passed"),
#     ]

#     # Simulate test execution and calculate the number of passed and failed test cases
#     passed = sum(1 for tc in test_cases if tc.status == "passed")
#     failed = sum(1 for tc in test_cases if tc.status == "failed")

#     # Send the test report via email
#     send_test_report(email, passed, failed)

#     return {"message": "Tests triggered and report sent successfully"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)





