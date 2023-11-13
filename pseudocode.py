import re
import os    
import sys
import argparse
import json
import threading
import requests
import datetime
import websocket
from uuid import uuid4
import time
from fastapi import FastAPI, HTTPException
from typing import Dict


# app = FastAPI()

# @app.get("/run_tests/", response_model=Dict[str, str], summary="Run test cases", description="Execute test cases and return results.")
# def run_tests():

#     try:
#         # Your existing test execution code here
#         # ...
#         # Test results
#         passed = 5
#         failed = 2

#         return {"passed": passed, "failed": failed}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

# @app.post("/run_single_test_case/", response_model=Dict[str, str], summary="Run a single test case", description="Execute a single test case and return results.")
# def run_single_test_case(test_case: str):
#     # Add your code to execute a single test case here
#     try:
#         # Your code to execute a single test case
#         # ...
#         # Test results
#         passed = 1
#         failed = 0

#         return {"passed": passed, "failed": failed}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Test execution failed: {str(e)}")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

param_patterns = {
    "CENTER_ID": r"CENTER_ID=(\d+)",
    "BLOCK-TIME-RANGE": r"BLOCK-TIME-RANGE",
    "MODALITY": r"MODALITY=([\w\s]+)",
    "SDATE": r"SDATE=([\w\d\+\-]+)",
    "STIME": r"STIME=([\d:]+)",
    "ETIME": r"ETIME=([\d:]+)",
}
variables = {
    "CENTER_ID": None,
    "BLOCK-TIME-RANGE": False,
    "MODALITY": None,
    "SDATE": None,
    "STIME": None,
    "ETIME": None,
}

config_file_path = "/Users/abhishekagarwal/WORKSPACES/vEngage/appointment-regression-test-framework-main/test-cases/sanity/conversation-2.tc"

with open(config_file_path, "r") as config_file:
    config_lines = config_file.readlines()

for line in config_lines:
    for param, pattern in param_patterns.items():
        match = re.search(pattern, line)
        if match:
            if param == "CENTER_ID":
                variables[param] = int(match.group(1))
            elif param == "BLOCK-TIME-RANGE":
                variables[param] = True
            else:
                variables[param] = match.group(1)


center_id = variables['CENTER_ID']

print(f"Using center_id: {center_id}")
print(f"Block Time Range: {variables['BLOCK-TIME-RANGE']}")
print(f"Modality: {variables['MODALITY']}")
print(f"Start Date: {variables['SDATE']}")
print(f"Start Time: {variables['STIME']}")
print(f"End Time: {variables['ETIME']}")
# center_id = 1
response_mode = "PUSH"

# class TestFailed(Exception):
#     def __init__(self, *args: object) -> None:
#         super().__init__(*args)
#         print(args)
#         sys.exit(0)
        

class TestFailed(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print(args)
        sys.exit(1)

def striphtml(data):
    p = re.compile(r'<.*?>')
    return " ".join(p.sub('', data).split())

def calculate_date_for_asked_iso_weekday_from_ref_date(ref_date: datetime.datetime, iso_weekday: int):
    days_ahead = iso_weekday - ref_date.isoweekday()
    if days_ahead <= 0:
        days_ahead += 7
    return ref_date + datetime.timedelta(days_ahead)

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def prRed(skk): 
    print("\033[91m{}\033[00m" .format(skk))

def prGreen(skk): 
    print("\033[92m{}\033[00m" .format(skk))

def prYellow(skk): 
    print("\033[93m{}\033[00m" .format(skk))

def prLightPurple(skk): 
    print("\033[94m {}\033[00m" .format(skk))

def prPurple(skk): 
    print("\033[95m{}\033[00m" .format(skk))

def prCyan(skk): 
    print("\033[96m{}\033[00m" .format(skk))

def prLightGray(skk): 
    print("\033[97m{}\033[00m" .format(skk))

def prBlack(skk): 
    print("\033[98m{}\033[00m" .format(skk))

parser = argparse.ArgumentParser()
parser.add_argument("-H", "--hostname", dest="hostname", default="https://chat-staging.vengage.ai", help="Server name")
parser.add_argument("-p", "--port", dest="port", default="443", help="Server port")
# parser.add_argument("-cid", "--center-id", dest="center_id", default="1", help="Center ID")
# parser.add_argument("-rm", "--response-mode", dest="response_mode", default="PUSH", help="Response mode: PUSH/POLL")
parser.add_argument("-tc", "--test-case", dest="test_case", default=None, help="Test case file path")


args = parser.parse_args()

conversation_id = str(uuid4())

# Initialize center_id using the command line argument
# center_id = int(args.center_id)
caller_id = "load-" + conversation_id[-12:]
test_case_file_path = args.test_case


test_script = """
==SETUP START==
center_id=15
==SETUP END==

==CONVERSATION START==
[thanks for calling] are you looking for a new appointment >>> yes
Please read out the [requested scan] as mentioned by your doctor in the referral letter >>> US hand
You have requested for US hand . [Is that correct?] >>> yes that is correct
[When would you like to visit us?] >>> saturday at 1pm
==CONVERSATION END==
"""

center_id_match = re.search(r"==SETUP START==\s*\nCENTER_ID=(\d+)", test_script)

if center_id_match:
    center_id = int(center_id_match.group(1))

print(f"Using center_id: {center_id}")

# args = parser.parse_args()

# conversation_id = str(uuid4())

# center_id = int(args.center_id)
# caller_id = "load-" + conversation_id[-12:]
# response_mode = args.response_mode
# test_case_file_path = args.test_case

ws_url = f"{args.hostname.replace('http','ws')}:{args.port}/api/chatter"
response_url = f"{args.hostname}:{args.port}/response/{conversation_id}"

# if test_case_file_path is None:
#     prRed("Missing argument: -tc/--test-case (Please provide the test case file that you wish to execute!)")
#     sys.exit(1)

RIS_SIMULATOR_ENDPOINT = os.getenv("RIS_SIMULATOR_ENDPOINT")

MACROS = {}
for i in range(30):
    MACROS[f"TODAY+{i}"] = (datetime.datetime.now() + datetime.timedelta(days=i)).date().strftime("%Y-%m-%d")

def execute_setup_instruction(instruction: str):
    global center_id

    instruction_list = list(map(lambda x: x.strip().lower(), instruction.split(",")))

    command = instruction_list[0]
    args = instruction_list[1:]

    keywords = {"modality": None, "sdate": None, "edate": None, "stime": None, "etime": None}
    for each in args:
        _args = each.split("=")
        keywords[_args[0]] = _args[1]

    if command == "center_id":
        center_id = int(keywords.get("value", center_id))
        print(f"Switched center_id to {center_id}")

    if command in ["block-all", "unblock-all"]:
        if keywords["sdate"] == None:
            prRed("Start date cannot be: None")
            sys.exit(1)
        if keywords["modality"] == None:
            prRed("Modality cannot be: None")
            sys.exit(1)
        start_date = datetime.datetime.strptime(keywords['sdate'], '%Y-%m-%d')
        date_range = [start_date]

        if keywords["edate"] is not None:
            end_date = datetime.datetime.strptime(keywords['edate'], '%Y-%m-%d')
            number_of_days = (end_date - start_date).days
            for i in range(number_of_days):
                _date = start_date + datetime.timedelta(days=i)
                if _date not in date_range:
                    date_range.append(_date)

        for each in date_range:
            url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
            requests.get(url=url)

    if command in ["block-current-week", "unblock-current-week"]:
        _command = "block-all" if command == 'block-current-week' else 'unblock-all'
        if keywords["modality"] == None:
            prRed("Modality cannot be: None")
            sys.exit(1)
        start_date = datetime.datetime.now()
        end_date = calculate_date_for_asked_iso_weekday_from_ref_date(start_date, iso_weekday=7)
        date_range = []
        number_of_days = (end_date - start_date).days
        for i in range(number_of_days):
            _date = start_date + datetime.timedelta(days=i)
            date_range.append(_date)
        for each in date_range:
            url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{_command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
            requests.get(url=url)

    if command in ["block-time-range", "unblock-time-range"]:
        _command = "block-slot-range" if command == 'block-time-range' else 'unblock-slot-range'
        if keywords["modality"] == None:
            prRed("Modality cannot be: None")
            sys.exit(1)

        if keywords["sdate"] == None:
            prRed("Start date cannot be: None")
            sys.exit(1)

        if keywords["stime"] == None:
            prRed("Start time cannot be: None")
            sys.exit(1)

        if keywords["etime"] == None:
            prRed("End time cannot be: None")
            sys.exit(1)

        url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{_command}?modality={keywords['modality'].upper()}&slot_date={keywords['sdate']}&start_time={keywords['stime']}&end_time={keywords['etime']}"
        print(url)
        response = requests.put(url=url)
        print(response.text)


with open(test_case_file_path, "r") as fd:
    test_script = fd.read()

    regex = r"==SETUP START==[A-Za-z\-\+0-9=\s,:\n]*==SETUP END=="
    matches = re.finditer(regex, test_script, re.MULTILINE)
    setup_section = None
    for matchNum, match in enumerate(matches, start=1):
        setup_section = match.group()

    prGreen("Setup:\n===============")

    if setup_section is not None:
        for macro, value in MACROS.items():
            setup_section = setup_section.replace(macro, value)

        setup_section = setup_section.strip()
        setup_section = setup_section.splitlines()
        for each in setup_section:
            if each in ["==SETUP START==", "==SETUP END=="]:
                continue
            execute_setup_instruction(each)
    else:
        print("Setup section not found in the input file.")

print("-" * 30)
print("-" * 30)
regex = r"==CONVERSATION START==[\[\]A-Za-z\-\+0-9=\s,:\n>.?]*==CONVERSATION END=="
matches = re.finditer(regex, test_script, re.MULTILINE | re.IGNORECASE)
conversation_section = None
for matchNum, match in enumerate(matches, start=1):
    conversation_section = match.group()
conversation = conversation_section.splitlines()[1:-1]
print(conversation)


is_running = True
current_step = 0

def fetch_response(ws):
    while is_running:
        req = requests.get(url=response_url, timeout=15)
        if req.text == "null":
            time.sleep(1)
            continue
        msg = req.text.replace('"', '')
        on_message(ws=ws, message=msg)

def send_request(ws, text: str):
    msg = json.dumps({
        "event": "DATA",
        "conversation_id": conversation_id,
        "data": text,
        "center_id": center_id,
    })
    prGreen(f"CLI:{text}")
    ws.send(msg)

current_step = 0

def on_message(ws, message):
    global is_running
    global current_step
    message = striphtml(message)
    prYellow(f"BOT:{message}")
    time.sleep(1)

    if current_step < len(conversation):
        conversation_step = conversation[current_step].split(">>>")
        current_step += 1

        bot_utterance = conversation_step[0]

        if current_step < len(conversation):
            user_response = conversation_step[1]

            regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
            matches = re.finditer(regex, bot_utterance, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
            for matchNum, match in enumerate(matches, start=1):
                _match = match.group().replace("[", "")
                _match = _match.replace("]", "")
                if _match.lower() in message.lower():
                    send_request(ws, text=user_response)
                    break
        else:
            is_running = False
            ws.close()
            sys.exit(0)

    else:
        user_response = "US hand"  
        send_request(ws, text=user_response)

    conversation_step = conversation[current_step].split(">>>")
    current_step = current_step + 1
    bot_utterance = conversation_step[0]
    user_response = conversation_step[1]
    regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
    matches = re.finditer(regex, bot_utterance, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
    for matchNum, match in enumerate(matches, start=1):
        _match = match.group().replace("[","")
        _match = _match.replace("]","")
        if _match.lower() in message.lower():
            send_request(ws, text=user_response)
            break

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws: websocket):
    msg = json.dumps({
        "event": "CONNECTED",
        "conversation_id": conversation_id,
        "type": "MOBILE",
        "contact": caller_id,
        "center_id": center_id,
        "response_mode": response_mode
    })
    
    ws.send(msg)
    msg = json.dumps({ "event": "NEW-CONVERSATION", "center_id": center_id, "conversation_id": conversation_id, "contact": caller_id })
    ws.send(msg)
    if response_mode == "POLL":
        x = threading.Thread(target=fetch_response, args=(ws,), daemon=True)
        x.start()
    
ws = websocket.WebSocketApp(ws_url,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
ws.run_forever() 
is_running = False




































# import re
# import os
# import sys
# import argparse
# import json
# import threading
# import requests
# import datetime
# import websocket
# from uuid import uuid4
# import time

# CENTER_ID = None

# class TestFailed(Exception):
#     def __init__(self, *args: object) -> None:
#         super().__init__(*args)
#         print(args)
#         sys.exit(1)

# def striphtml(data):
#     p = re.compile(r'<.*?>')
#     return " ".join(p.sub('', data).split())

# def calculate_date_for_asked_iso_weekday_from_ref_date(ref_date: datetime.datetime, iso_weekday: int):
#     days_ahead = iso_weekday - ref_date.isoweekday()
#     if days_ahead <= 0:
#         days_ahead += 7
#     return ref_date + datetime.timedelta(days_ahead)

# def cls():
#     os.system('cls' if os.name == 'nt' else 'clear')

# def prRed(skk):
#     print("\033[91m{}\033[00m" .format(skk))

# def prGreen(skk):
#     print("\033[92m{}\033[00m" .format(skk))

# def prYellow(skk):
#     print("\033[93m{}\033[00m" .format(skk))

# def prLightPurple(skk):
#     print("\033[94m {}\033[00m" .format(skk))

# def prPurple(skk):
#     print("\033[95m{}\033[00m" .format(skk))

# def prCyan(skk):
#     print("\033[96m{}\033[00m" .format(skk))

# def prLightGray(skk):
#     print("\033[97m{}\033[00m" .format(skk))

# def prBlack(skk):
#     print("\033[98m{}\033[00m" .format(skk))

# parser = argparse.ArgumentParser()
# parser.add_argument("-H", "--hostname", dest="hostname", default="https://chat-staging.vengage.ai", help="Server name")
# parser.add_argument("-p", "--port", dest="port", default="443", help="Server port")
# parser.add_argument("-rm", "--response-mode", dest="response_mode", default="PUSH", help="Response mode: PUSH/POLL")
# parser.add_argument("-tc", "--test-case", dest="test_case", default=None, help="Test case file path")
# args = parser.parse_args()

# conversation_id = str(uuid4())
# caller_id = "load-" + conversation_id[-12:]
# response_mode = args.response_mode
# test_case_file_path = args.test_case

# ws_url = f"{args.hostname.replace('http','ws')}:{args.port}/api/chatter"
# response_url = f"{args.hostname}:{args.port}/response/{conversation_id}"

# if test_case_file_path is None:
#     prRed("Missing argument: -tc/--test-case (Please provide the test case file that you wish to execute!)")
#     sys.exit(1)

# RIS_SIMULATOR_ENDPOINT = os.getenv("RIS_SIMULATOR_ENDPOINT")
# MACROS = {}
# for i in range(30):
#     MACROS[f"TODAY+{i}"] = (datetime.datetime.now() + datetime.timedelta(days=i)).date().strftime("%Y-%m-%d")

# def execute_setup_instruction(instruction: str):
#     global CENTER_ID
#     instruction_list = list(map(lambda x: x.strip().lower(), instruction.split(",")))
#     command = instruction_list[0]
#     args = instruction_list[1:]
#     keywords = {"modality": None, "sdate": None, "edate": None, "stime": None, "etime": None}
#     for each in args:
#         _args = each.split("=")
#         keywords[_args[0]] = _args[1]
#     if command == "center_id":
#         CENTER_ID = int(keywords.get("value", CENTER_ID))
#         print(f"Switched CENTER_ID to {CENTER_ID}")
#     elif command in ["block-all", "unblock-all"]:
#         if keywords["sdate"] == None:
#             prRed("Start date cannot be: None")
#             sys.exit(1)
#         if keywords["modality"] == None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)
#         start_date = datetime.datetime.strptime(keywords['sdate'], '%Y-%m-%d')
#         date_range = [start_date]
#         if keywords["edate"] is not None:
#             end_date = datetime.datetime.strptime(keywords['edate'], '%Y-%m-%d')
#             number_of_days = (end_date - start_date).days
#             for i in range(number_of_days):
#                 _date = start_date + datetime.timedelta(days=i)
#                 if _date not in date_range:
#                     date_range.append(_date)
#         for each in date_range:
#             url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
#             requests.get(url=url)
#     elif command in ["block-current-week", "unblock-current-week"]:
#         _command = "block-all" if command == 'block-current-week' else 'unblock-all'
#         if keywords["modality"] == None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)
#         start_date = datetime.datetime.now()
#         end_date = calculate_date_for_asked_iso_weekday_from_ref_date(start_date, iso_weekday=7)
#         date_range = []
#         number_of_days = (end_date - start_date).days
#         for i in range(number_of_days):
#             _date = start_date + datetime.timedelta(days=i)
#             date_range.append(_date)
#         for each in date_range:
#             url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{_command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
#             requests.get(url=url)
#     elif command in ["block-time-range", "unblock-time-range"]:
#         _command = "block-slot-range" if command == 'block-time-range






























# import re
# import os
# import sys
# import argparse
# import json
# import threading
# import requests
# import datetime
# import websocket
# from uuid import uuid4
# import time

# param_patterns = {
#     "CENTER_ID": r"CENTER_ID=(\d+)",
#     "BLOCK-TIME-RANGE": r"BLOCK-TIME-RANGE",
#     "MODALITY": r"MODALITY=([\w\s]+)",
#     "SDATE": r"SDATE=([\w\d\+\-]+)",
#     "STIME": r"STIME=([\d:]+)",
#     "ETIME": r"ETIME=([\d:]+)",
# }

# variables = {
#     "CENTER_ID": None,
#     "BLOCK-TIME-RANGE": False,
#     "MODALITY": None,
#     "SDATE": None,
#     "STIME": None,
#     "ETIME": None,
# }

# config_file_path = "test-cases/sanity/conversation-2.tc"

# with open(config_file_path, "r") as config_file:
#     config_lines = config_file.readlines()

# for line in config_lines:
#     for param, pattern in param_patterns.items():
#         match = re.search(pattern, line)
#         if match:
#             if param == "CENTER_ID":
#                 variables[param] = int(match.group(1))
#             elif param == "BLOCK-TIME-RANGE":
#                 variables[param] = True
#             else:
#                 variables[param] = match.group(1)


# center_id = variables['CENTER_ID']

# print(f"Using center_id: {center_id}")
# print(f"Block Time Range: {variables['BLOCK-TIME-RANGE']}")
# print(f"Modality: {variables['MODALITY']}")
# print(f"Start Date: {variables['SDATE']}")
# print(f"Start Time: {variables['STIME']}")
# print(f"End Time: {variables['ETIME']}")
# # center_id = 1
# response_mode = "PUSH"



# class TestFailed(Exception):
#     def __init__(self, *args: object) -> None:
#         super().__init__(*args)
#         print(args)
#         sys.exit(1)

# def striphtml(data):
#     p = re.compile(r'<.*?>')
#     return " ".join(p.sub('', data).split())

# def calculate_date_for_asked_iso_weekday_from_ref_date(ref_date: datetime.datetime, iso_weekday: int):
#     days_ahead = iso_weekday - ref_date.isoweekday()
#     if days_ahead <= 0:
#         days_ahead += 7
#     return ref_date + datetime.timedelta(days_ahead)

# def cls():
#     os.system('cls' if os.name == 'nt' else 'clear')

# def prRed(skk): 
#     print("\033[91m{}\033[00m" .format(skk))

# def prGreen(skk): 
#     print("\033[92m{}\033[00m" .format(skk))

# def prYellow(skk): 
#     print("\033[93m{}\033[00m" .format(skk))

# def prLightPurple(skk): 
#     print("\033[94m {}\033[00m" .format(skk))

# def prPurple(skk): 
#     print("\033[95m{}\033[00m" .format(skk))

# def prCyan(skk): 
#     print("\033[96m{}\033[00m" .format(skk))

# def prLightGray(skk): 
#     print("\033[97m{}\033[00m" .format(skk))

# def prBlack(skk): 
#     print("\033[98m{}\033[00m" .format(skk))

# parser = argparse.ArgumentParser()
# parser.add_argument("-H", "--hostname", dest="hostname", default="https://chat-staging.vengage.ai", help="Server name")
# parser.add_argument("-p", "--port", dest="port", default="443", help="Server port")
# # parser.add_argument("-cid", "--center-id", dest="center_id", default="1", help="Center ID")
# # parser.add_argument("-rm", "--response-mode", dest="response_mode", default="PUSH", help="Response mode: PUSH/POLL")
# parser.add_argument("-tc", "--test-case", dest="test_case", default=None, help="Test case file path")


# args = parser.parse_args()

# conversation_id = str(uuid4())

# # Initialize center_id using the command line argument
# # center_id = int(args.center_id)
# caller_id = "load-" + conversation_id[-12:]
# test_case_file_path = args.test_case


# test_script = """
# ==SETUP START==
# center_id=15
# ==SETUP END==

# ==CONVERSATION START==
# [thanks for calling] are you looking for a new appointment >>> yes
# Please read out the [requested scan] as mentioned by your doctor in the referral letter >>> US hand
# You have requested for US hand . [Is that correct?] >>> yes that is correct
# [When would you like to visit us?] >>> saturday at 1pm
# ==CONVERSATION END==
# """

# center_id_match = re.search(r"==SETUP START==\s*\nCENTER_ID=(\d+)", test_script)

# if center_id_match:
#     center_id = int(center_id_match.group(1))

# print(f"Using center_id: {center_id}")

# # args = parser.parse_args()

# # conversation_id = str(uuid4())

# # center_id = int(args.center_id)
# # caller_id = "load-" + conversation_id[-12:]
# # response_mode = args.response_mode
# # test_case_file_path = args.test_case

# ws_url = f"{args.hostname.replace('http','ws')}:{args.port}/api/chatter"
# response_url = f"{args.hostname}:{args.port}/response/{conversation_id}"

# # if test_case_file_path is None:
# #     prRed("Missing argument: -tc/--test-case (Please provide the test case file that you wish to execute!)")
# #     sys.exit(1)

# RIS_SIMULATOR_ENDPOINT = os.getenv("RIS_SIMULATOR_ENDPOINT")

# MACROS = {}
# for i in range(30):
#     MACROS[f"TODAY+{i}"] = (datetime.datetime.now() + datetime.timedelta(days=i)).date().strftime("%Y-%m-%d")

# def execute_setup_instruction(instruction: str):
#     global center_id

#     instruction_list = list(map(lambda x: x.strip().lower(), instruction.split(",")))

#     command = instruction_list[0]
#     args = instruction_list[1:]

#     keywords = {"modality": None, "sdate": None, "edate": None, "stime": None, "etime": None}
#     for each in args:
#         _args = each.split("=")
#         keywords[_args[0]] = _args[1]

#     if command == "center_id":
#         center_id = int(keywords.get("value", center_id))
#         print(f"Switched center_id to {center_id}")

#     if command in ["block-all", "unblock-all"]:
#         if keywords["sdate"] == None:
#             prRed("Start date cannot be: None")
#             sys.exit(1)
#         if keywords["modality"] == None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)
#         start_date = datetime.datetime.strptime(keywords['sdate'], '%Y-%m-%d')
#         date_range = [start_date]

#         if keywords["edate"] is not None:
#             end_date = datetime.datetime.strptime(keywords['edate'], '%Y-%m-%d')
#             number_of_days = (end_date - start_date).days
#             for i in range(number_of_days):
#                 _date = start_date + datetime.timedelta(days=i)
#                 if _date not in date_range:
#                     date_range.append(_date)

#         for each in date_range:
#             url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
#             requests.get(url=url)

#     if command in ["block-current-week", "unblock-current-week"]:
#         _command = "block-all" if command == 'block-current-week' else 'unblock-all'
#         if keywords["modality"] == None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)
#         start_date = datetime.datetime.now()
#         end_date = calculate_date_for_asked_iso_weekday_from_ref_date(start_date, iso_weekday=7)
#         date_range = []
#         number_of_days = (end_date - start_date).days
#         for i in range(number_of_days):
#             _date = start_date + datetime.timedelta(days=i)
#             date_range.append(_date)
#         for each in date_range:
#             url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{_command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
#             requests.get(url=url)

#     if command in ["block-time-range", "unblock-time-range"]:
#         _command = "block-slot-range" if command == 'block-time-range' else 'unblock-slot-range'
#         if keywords["modality"] == None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)

#         if keywords["sdate"] == None:
#             prRed("Start date cannot be: None")
#             sys.exit(1)

#         if keywords["stime"] == None:
#             prRed("Start time cannot be: None")
#             sys.exit(1)

#         if keywords["etime"] == None:
#             prRed("End time cannot be: None")
#             sys.exit(1)

#         url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{_command}?modality={keywords['modality'].upper()}&slot_date={keywords['sdate']}&start_time={keywords['stime']}&end_time={keywords['etime']}"
#         print(url)
#         response = requests.put(url=url)
#         print(response.text)

# with open(test_case_file_path, "r") as fd:
#     test_script = fd.read()

#     regex = r"==SETUP START==[A-Za-z\-\+0-9=\s,:\n]*==SETUP END=="
#     matches = re.finditer(regex, test_script, re.MULTILINE)
#     setup_section = None
#     for matchNum, match in enumerate(matches, start=1):
#         setup_section = match.group()

#     prGreen("Setup:\n===============")

#     if setup_section is not None:
#         for macro, value in MACROS.items():
#             setup_section = setup_section.replace(macro, value)

#         setup_section = setup_section.strip()
#         setup_section = setup_section.splitlines()
#         for each in setup_section:
#             if each in ["==SETUP START==", "==SETUP END=="]:
#                 continue
#             execute_setup_instruction(each)
#     else:
#         print("Setup section not found in the input file.")

# print("-" * 30)
# print("-" * 30)
# regex = r"==CONVERSATION START==[\[\]A-Za-z\-\+0-9=\s,:\n>.?]*==CONVERSATION END=="
# matches = re.finditer(regex, test_script, re.MULTILINE | re.IGNORECASE)
# conversation_section = None
# for matchNum, match in enumerate(matches, start=1):
#     conversation_section = match.group()
# conversation = conversation_section.splitlines()[1:-1]
# print(conversation)


# is_running = True
# current_step = 0

# def fetch_response(ws):
#     while is_running:
#         req = requests.get(url=response_url, timeout=15)
#         if req.text == "null":
#             time.sleep(1)
#             continue
#         msg = req.text.replace('"', '')
#         on_message(ws=ws, message=msg)

# def send_request(ws, text: str):
#     msg = json.dumps({
#         "event": "DATA",
#         "conversation_id": conversation_id,
#         "data": text,
#         "center_id": center_id,
#     })
#     prGreen(f"CLI:{text}")
#     ws.send(msg)

# current_step = 0

# def on_message(ws, message):
#     global is_running
#     global current_step
#     message = striphtml(message)
#     prYellow(f"BOT:{message}")
#     time.sleep(1)

#     if current_step < len(conversation):
#         conversation_step = conversation[current_step].split(">>>")
#         current_step += 1

#         bot_utterance = conversation_step[0]

#         if current_step < len(conversation):
#             user_response = conversation_step[1]

#             regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
#             matches = re.finditer(regex, bot_utterance, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
#             for matchNum, match in enumerate(matches, start=1):
#                 _match = match.group().replace("[", "")
#                 _match = _match.replace("]", "")
#                 if _match.lower() in message.lower():
#                     send_request(ws, text=user_response)
#                     break
#         else:
#             is_running = False
#             ws.close()
#             sys.exit(0)

#     else:
#         user_response = "US hand"  
#         send_request(ws, text=user_response)

#     conversation_step = conversation[current_step].split(">>>")
#     current_step = current_step + 1
#     bot_utterance = conversation_step[0]
#     user_response = conversation_step[1]
#     regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
#     matches = re.finditer(regex, bot_utterance, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
#     for matchNum, match in enumerate(matches, start=1):
#         _match = match.group().replace("[","")
#         _match = _match.replace("]","")
#         if _match.lower() in message.lower():
#             send_request(ws, text=user_response)
#             break

# def on_error(ws, error):
#     print(error)

# def on_close(ws, close_status_code, close_msg):
#     print("### closed ###")

# def on_open(ws: websocket):
#     msg = json.dumps({
#         "event": "CONNECTED",
#         "conversation_id": conversation_id,
#         "type": "MOBILE",
#         "contact": caller_id,
#         "center_id": center_id,
#         "response_mode": response_mode
#     })
    
#     ws.send(msg)
#     msg = json.dumps({ "event": "NEW-CONVERSATION", "center_id": center_id, "conversation_id": conversation_id, "contact": caller_id })
#     ws.send(msg)
#     if response_mode == "POLL":
#         x = threading.Thread(target=fetch_response, args=(ws,), daemon=True)
#         x.start()
    
# ws = websocket.WebSocketApp(ws_url,
#                             on_open=on_open,
#                             on_message=on_message,
#                             on_error=on_error,
#                             on_close=on_close)
# ws.run_forever() 
# is_running = False



# with open(test_case_file_path, "r") as fd:
#     test_script = fd.read()

#     setup_section_match = re.search(r"==SETUP START==[\s\S]*?center_id=(\d+)[\s\S]*?==SETUP END==", test_script)
#     if setup_section_match:
#         CENTER_ID = int(setup_section_match.group(1))
#         print(f"Switched CENTER_ID to {CENTER_ID}")
#     else:
#         print("CENTER_ID not found in the setup section of the input file.")











# config_file_path = "test-cases/sanity/conversation-2.tc"

# with open(config_file_path, "r") as config_file:
#     config_lines = config_file.readlines()

# for line in config_lines:
#     if line.strip().startswith("CENTER_ID="):
#         center_id = int(line.strip().split("=")[1])


# # center_id = 1
# response_mode = "PUSH"




# {
#     "CENTER_CONFIG_IMAGING_WORKFLOWS": {
#         "MAX_ATTEMPTS_IN_SCAN_CONFIRMATION_STEP": 2,
#         "check_medicare_at_start": "NO_CHECK",
#         "do_provisional_booking": 1,
#         "inform_time_class_version": "v1",
#         "is_EOS_machine_available": 0,
#         "leave_contactno_for_manual_reconciliation": 0,
#         "leave_dob_for_manual_reconciliation": 0,
#         "modality_options_system_utterance": "Is it XRay, Ultrasound, C T, or M R I ? ",
#         "ris_service_code_is_mandatory": 0,
#         "take_cost_consent_after_slot_selection": 0,
#         "use_new_ux_for_scan_confirmation": 0
#     },
#     "MISC_CONFIG_INFO": {
#         "escalation_message_for_OOH_calls": null,
#         "escalation_number_for_OOH": null
#     },
#     "active_centers_list_for_provided_dummy_center": [],
#     "additional_costing_confirmed": null,
#     "additional_instructions_over_email_post_booking": {
#         "custom_question": null,
#         "is_email_required": false,
#         "required_documents": null
#     },
#     "age_check_result": null,
#     "asr_corrected_utterance": "conversation_started",
#     "available_slots_time_range": null,
#     "bodypart": null,
#     "bodypart_generic": null,
#     "bodypart_group": null,
#     "bodypart_group_generic": null,
#     "callSid": "chat-84e8a9e788b2",
#     "call_start_time": "2023-10-23 19:37:47.518767",
#     "callerNo": "+91 6268875447",
#     "center_address": "29 Grose St, Parramatta",
#     "center_closing_time": "18:00:00",
#     "center_id": 1,
#     "center_name": "Specailist Medical Imaging, Parramatta Grose St.",
#     "center_opening_time": "08:00:00",
#     "center_short_name": null,
#     "center_timezone": "Australia/Sydney",
#     "centers_where_service_available": {},
#     "config_ASK_MOBILE_NUMBER_FOR_LANDLINE_SOURCE": 1,
#     "config_COVID_WORKFLOW": 0,
#     "config_FEMALE_SONOGRAPHER_OPTION_AVAILABLE": 0,
#     "config_IS_ORDER_CANCELLATION_ALLOWED": 0,
#     "config_IS_ORDER_RESCHEDULING_ALLOWED": 0,
#     "config_acceptable_timegap_between_calls": 0,
#     "conversationWorkflowType": "IMAGING_APPT",
#     "conversation_context": null,
#     "conversation_id": "chat-84e8a9e788b2",
#     "conversation_source": "MOBILE",
#     "conversation_tags": [
#         "OUT_OF_OFFICE_HOURS"
#     ],
#     "country_isd": "+91",
#     "current_internal_state": "CHECK_IF_CALLED_FOR_NEW_APPOINTMENT",
#     "current_state": "GreetingState",
#     "current_state_id": 0,
#     "customer_id": 1,
#     "date_of_birth": null,
#     "day_specific_duration_rules": null,
#     "direct_reception_number": "+61123456789",
#     "disconnect_call": null,
#     "email_id": null,
#     "enquiry_date": null,
#     "entity_in_original_utterance": {
#         "bodypart": "",
#         "bodypart_group": "",
#         "laterality": "",
#         "misc_info": "",
#         "modality": "",
#         "protocol": "",
#         "purpose_of_study": "",
#         "speciality": ""
#     },
#     "ereferral_details": null,
#     "ereferral_uid": null,
#     "escalation_action": null,
#     "escalation_type": 0,
#     "event_timeline": {},
#     "fasting_guideline_confirmed": null,
#     "final_datetime": null,
#     "find_slots_retry_count": 0,
#     "first_name": null,
#     "first_name_original_text": null,
#     "insurance_type": null,
#     "intent": "nlu_fallback",
#     "is_female_sonographer_required": null,
#     "is_low_confidence_text": 0,
#     "is_mobile_number_saved_in_record": false,
#     "is_nursing_call_required": false,
#     "is_pregnancy_flow": null,
#     "is_requested_scan_a_repeat": null,
#     "is_screening_call_required": false,
#     "is_single_pregnancy": null,
#     "is_specific_center_requested": null,
#     "language_code": "en",
#     "last_name": null,
#     "last_name_original_text": null,
#     "last_response": "Sorry, I did not hear. Thanks for calling Specailist Medical Imaging, Parramatta Grose St.. <prosody rate=\"fast\">Are you looking to book a new</prosody> <prosody volume=\"loud\">appointment?</prosody>",
#     "last_user_response_time": "2023-10-23 19:37:47.564309",
#     "laterality": null,
#     "laterality_generic": null,
#     "mobile_number": "+91 6268875447",
#     "modality": null,
#     "modality_generic": null,
#     "nursing_call_in_minutes_after_appointment": null,
#     "original_text": "CONVERSATION_STARTED",
#     "patient_age_profile": null,
#     "patient_gender": null,
#     "patient_master_data_ref_id": null,
#     "pregnancy_flow_protocol": null,
#     "procedure_allowed_rooms": null,
#     "protocol": null,
#     "protocol_generic": null,
#     "provisional_booking_information_required": null,
#     "purpose_of_study": null,
#     "purpose_of_study_generic": null,
#     "referrer_type": null,
#     "response_code": [
#         "img_greeting.greeting_message",
#         "common.user_no_response_prepend_message"
#     ],
#     "service_code": null,
#     "service_request_consolidated_utterance": null,
#     "site_code": "PAR",
#     "speciality": null,
#     "switch_state_machine": null,
#     "system_proposed_slot": null,
#     "time_needed_for_procedure": null,
#     "total_ssml_pause_time": 0,
#     "user_last_utterance": "conversation_started",
#     "user_proposed_datetime": null,
#     "user_service_request_utterance": "",
#     "webbot_backend_keys": {
#         "available_slots": null,
#         "is_conversation_AI_success": false
#     },
#     "weeks_since_pregnant": null
# }