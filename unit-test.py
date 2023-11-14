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

config_file_path = "/Users/abhishekagarwal/Downloads/appointment-regression-test-framework-main/test-cases/sanity/conversation-2.tc"


import dotenv
dotenv.load_dotenv(os.path.join(os.getcwd(),".env"))

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

response_mode="PUSH"

class TestFailed(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        print(args)
        sys.exit(1)


import re
def striphtml(data):
    p = re.compile(r'<.*?>')
    return " ".join(p.sub('', data).split())

def calculate_date_for_asked_iso_weekday_from_ref_date(ref_date: datetime.datetime, iso_weekday: int):
    days_ahead = iso_weekday - ref_date.isoweekday()
    if days_ahead <= 0:
        days_ahead += 7
    return ref_date + datetime.timedelta(days_ahead)

parser = argparse.ArgumentParser()
parser.add_argument("-H", "--hostname", dest="hostname", default="https://chat-staging.vengage.ai", help="Server name")
parser.add_argument("-p", "--port", dest="port", default="443", help="Server port")
# parser.add_argument("-cid", "--center-id", dest="center_id", default="1", help="Center ID")
parser.add_argument("-rm", "--response-mode", dest="response_mode", default="PUSH", help="Response mode: PUSH/POLL")
parser.add_argument("-tc", "--test-case", dest="test_case", default=None, help="Test case file path")

args = parser.parse_args()


test_script = """

"""
conversation_id = str(uuid4())
test_case_file_path = args.test_case
caller_id = "load-" + conversation_id[-12:]
center_id_match = re.search(r"==SETUP START==\s*\nCENTER_ID=(\d+)", test_script)


# if center_id_match:
#     center_id = int(center_id_match.group(1))

# print(f"Using center_id: {center_id}")

ws_url = f"{args.hostname.replace('http','ws')}:{args.port}/api/chatter"
response_url = f"{args.hostname}:{args.port}/response/{conversation_id}"


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

def prGreen(skk): 
    print("\033[92m{}\033[00m" .format(skk))
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



def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def prRed(skk): print("\033[91m{}\033[00m" .format(skk))
def prGreen(skk): print("\033[92m{}\033[00m" .format(skk))
def prYellow(skk): print("\033[93m{}\033[00m" .format(skk))
def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
def prPurple(skk): print("\033[95m{}\033[00m" .format(skk))
def prCyan(skk): print("\033[96m{}\033[00m" .format(skk))
def prLightGray(skk): print("\033[97m{}\033[00m" .format(skk))
def prBlack(skk): print("\033[98m{}\033[00m" .format(skk))

prYellow(os.getcwd())
dotenv.load_dotenv(os.path.join(os.getcwd(),".env"))
prCyan(os.getenv("RIS_SIMULATOR_ENDPOINT"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--hostname", dest="hostname", default="https://chat-staging.vengage.ai", help="Server name")
    parser.add_argument("-p", "--port", dest="port", default="443", help="Server port")
    parser.add_argument("-tc", "--test-case", dest="test_case", default=None, help="Test case file path")
    args = parser.parse_args()

    conversation_id = str(uuid4())
    test_case_file_path = args.test_case


ws_url = f"{args.hostname.replace('http','ws')}:{args.port}/api/chatter"
response_url=f"{args.hostname}:{args.port}/response/{conversation_id}"

if test_case_file_path is None:
    prRed("Missing argument: -tc/--test-case (Please provide the test case file that you wish to execute!)")
    sys.exit(1)

# print(args.hostname, args.port, ws_url, center_id)
RIS_SIMULATOR_ENDPOINT = os.getenv("RIS_SIMULATOR_ENDPOINT")

MACROS = {}
for i in range(30):
    MACROS[f"TODAY+{i}"] = (datetime.datetime.now()+datetime.timedelta(days=i)).date().strftime("%Y-%m-%d")
# prCyan(f"MACROS:\n{json.dumps(MACROS, indent=4)}")


print("-"*30)
print("-"*30)
regex = r"==CONVERSATION START==[\[\]A-Za-z\-\+0-9=\s,:\n>.?]*==CONVERSATION END=="
matches = re.finditer(regex, test_script, re.MULTILINE|re.IGNORECASE)
conversation_section = None
for matchNum, match in enumerate(matches, start=1):
    conversation_section = match.group()
conversation = conversation_section.splitlines()[1:-1]
print(conversation)



is_running = True
current_step=0

def fetch_response(ws):
    while is_running:
        req = requests.get(url=response_url, timeout=15)
        if req.text == "null":
            time.sleep(1)
            continue
        msg = req.text.replace('"','')
        on_message(ws=ws, message=msg)

def send_request(ws, text:str):
    msg = json.dumps({
                    "event": "DATA",
                    "conversation_id": conversation_id,
                    "data": text,
                    "center_id": center_id,
                })
    prGreen(f"CLI:{text}")
    ws.send(msg)

def on_message(ws, message):
    global is_running
    global current_step
    message = striphtml(message)
    prYellow(f"BOT:{message}")
    time.sleep(1)
    
    if message.lower() == "hangup_call":
        is_running = False
        ws.close()
        sys.exit(1)

    try:
        conversation_step = conversation[current_step].split(">>>")
        current_step += 1
        bot_utterance = conversation_step[0]
        user_response = conversation_step[1]
        regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
        matches = re.finditer(regex, bot_utterance, re.MULTILINE | re.IGNORECASE | re.VERBOSE)

        for matchNum, match in enumerate(matches, start=1):
            _match = match.group().replace("[", "")
            _match = _match.replace("]", "")
            if _match.lower() in message.lower():
                send_request(ws, text=user_response)
                break

    except Exception as e:
        print(f"An error occurred in the for loop: {e.__class__.__name__}: {str(e)}")



# def on_message(ws, message):
#     global is_running
#     global current_step
#     message = striphtml(message)
#     prYellow(f"BOT:{message}")
#     time.sleep(1)

#     if message.lower() == "hangup_call":
#         is_running = False
#         ws.close()
#         sys.exit(1)

#     while current_step < len(conversation):
#         print("Current Step:", current_step)
#         print("Length of Conversation:", len(conversation))
#         print("Conversation:", conversation)

#         conversation_step = conversation[current_step].split(">>>")
#         bot_utterance = conversation_step[0]
#         user_response = conversation_step[1]

#         regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
#         matches = re.finditer(regex, bot_utterance, re.MULTILINE | re.IGNORECASE | re.VERBOSE)

#         response_found = False

#         for matchNum, match in enumerate(matches, start=1):
#             _match = match.group().replace("[", "")
#             _match = _match.replace("]", "")
#             if _match.lower() in message.lower():
#                 send_request(ws, text=user_response)
#                 response_found = True
#                 break

#         current_step += 1

#         if response_found:
#             break

#     if current_step >= len(conversation):
#         print("End of conversation steps reached.")
#         is_running = False
#         ws.close()
#         sys.exit(1)
#     elif not response_found and current_step < len(conversation):
#         print("Invalid response. Please try again.")
#         send_request(ws, text=conversation[current_step].split(">>>")[0])


# def on_message(ws, message):
#     global is_running
#     global current_step
#     message = striphtml(message)
#     prYellow(f"BOT:{message}")
#     time.sleep(1)
#     if message.lower() == "hangup_call":
#         is_running=False
#         ws.close()
#         sys.exit(1)

        
#     conversation_step = conversation[current_step].split(">>>")
#     # print("Conversation section:", conversation_section)
#     # print("Conversation steps:", conversation)

#     current_step =current_step+1
#     bot_utterance = conversation_step[0]
#     user_response = conversation_step[1]
#     regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
#                 # \[[A-Za-z\-\+0-9=\s,\n:?]*\]
#     matches = re.finditer(regex, bot_utterance, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
#     for matchNum, match in enumerate(matches, start=1):
#         _match = match.group().replace("[","")
#         _match = _match.replace("]","")
#         if _match.lower() in message.lower():
#             send_request(ws, text=user_response)
#             break

#     # if current_step < len(conversation):
#     #     conversation_step = conversation[current_step].split(">>>")
#     #     current_step += 1
#     #     bot_utterance = conversation_step[0]
#     #     user_response = conversation_step[1]
#     # else:
        # print("End of conversation steps reached.")
        # is_running = False
        # ws.close()


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



#try catch

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws:websocket):
    # print("Opened connection")
    msg = json.dumps({
                        "event": "CONNECTED",
                        "conversation_id": conversation_id,
                        "type": "MOBILE",
                        "contact": caller_id,
                        "center_id": center_id,
                        "response_mode":response_mode
                    })
    
    ws.send(msg)
    msg = json.dumps({ "event": "NEW-CONVERSATION", "center_id": center_id, "conversation_id": conversation_id, "contact": caller_id })
    ws.send(msg)
    if response_mode=="POLL":
        x = threading.Thread(target=fetch_response, args=(ws,), daemon=True)
        x.start()
    # ws.close()

    # websocket.enableTrace(True)
ws = websocket.WebSocketApp(ws_url,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
# print(type(ws))
ws.run_forever()  
is_running=False


    





























# # ------------ORIGINAL CODE---------------


# import websocket
# import time
# import argparse
# import json
# from uuid import uuid4
# import sys, os
# import threading
# import requests
# import datetime
# import dotenv
# import urllib
# from urllib import parse
# dotenv.load_dotenv(os.path.join(os.getcwd(),".env"))

# class TestFailed(Exception):
#     def __init__(self, *args: object) -> None:
#         super().__init__(*args)
#         print(args)
#         sys.exit(1)

# import re
# def striphtml(data):
#     p = re.compile(r'<.*?>')
#     return " ".join(p.sub('', data).split())

# def calculate_date_for_asked_iso_weekday_from_ref_date(ref_date:datetime.datetime, iso_weekday:int):
#     """get date of 

#     Args:
#         d (datetime.datetime): source date
#         iso_weekday (int): ISO weekday. Mon:1, Tue:2, Wed:3, Thu:4, Fri:5, Sat:6, Sun:7

#     Returns:
#         _type_: _description_
#     """    
#     days_ahead = iso_weekday - ref_date.isoweekday()
#     if days_ahead <= 0: # Target day already happened this week
#         days_ahead += 7
#     return ref_date + datetime.timedelta(days_ahead)


# def cls():
#     os.system('cls' if os.name=='nt' else 'clear')

# def prRed(skk): print("\033[91m{}\033[00m" .format(skk))
# def prGreen(skk): print("\033[92m{}\033[00m" .format(skk))
# def prYellow(skk): print("\033[93m{}\033[00m" .format(skk))
# def prLightPurple(skk): print("\033[94m {}\033[00m" .format(skk))
# def prPurple(skk): print("\033[95m{}\033[00m" .format(skk))
# def prCyan(skk): print("\033[96m{}\033[00m" .format(skk))
# def prLightGray(skk): print("\033[97m{}\033[00m" .format(skk))
# def prBlack(skk): print("\033[98m{}\033[00m" .format(skk))

# prYellow(os.getcwd())
# dotenv.load_dotenv(os.path.join(os.getcwd(),".env"))
# prCyan(os.getenv("RIS_SIMULATOR_ENDPOINT"))


# parser = argparse.ArgumentParser()
# parser.add_argument("-H","--hostname",dest="hostname",default="https://chat-staging.vengage.ai",help="Server name")
# parser.add_argument("-p","--port",dest="port",default="443",help="Server port")
# parser.add_argument("-cid","--center-id",dest="center_id",default="1",help="Center ID")
# parser.add_argument("-rm","--response-mode",dest="response_mode",default="PUSH",help="Response mode: PUSH/POLL")
# parser.add_argument("-tc","--test-case",dest="test_case",default=None,help="Test case file path")

# args = parser.parse_args()

# conversation_id=str(uuid4())

# center_id = int(args.center_id)
# caller_id = "load-"+conversation_id[-12:]
# response_mode = args.response_mode
# test_case_file_path = args.test_case

# ws_url = f"{args.hostname.replace('http','ws')}:{args.port}/api/chatter"
# response_url=f"{args.hostname}:{args.port}/response/{conversation_id}"

# if test_case_file_path is None:
#     prRed("Missing argument: -tc/--test-case (Please provide the test case file that you wish to execute!)")
#     sys.exit(1)

# # print(args.hostname, args.port, ws_url, center_id)
# RIS_SIMULATOR_ENDPOINT = os.getenv("RIS_SIMULATOR_ENDPOINT")

# MACROS = {}
# for i in range(30):
#     MACROS[f"TODAY+{i}"] = (datetime.datetime.now()+datetime.timedelta(days=i)).date().strftime("%Y-%m-%d")
# # prCyan(f"MACROS:\n{json.dumps(MACROS, indent=4)}")

# def execute_setup_instruction(instruction:str):
#     instruction_list = list(map(lambda x:x.strip().lower(), instruction.split(",")))
#     command = instruction_list[0]
#     args = instruction_list[1:]

#     print("command:",command, ", args",args)
#     keywords = {"modality":None,"sdate":None, "edate":None,"stime":None, "etime":None}
#     for each in args:
#         _args = each.split("=")
#         keywords[_args[0]]=_args[1]

#     if command in ["block-all","unblock-all"]:
#         if keywords["sdate"]==None:
#             prRed("Start date cannot be: None")
#             sys.exit(1)
#         if keywords["modality"]==None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)
#         start_date = datetime.datetime.strptime(keywords['sdate'],'%Y-%m-%d')
#         date_range = [start_date]
        
#         if keywords["edate"] is not None:
#             end_date = datetime.datetime.strptime(keywords['edate'],'%Y-%m-%d')
#             number_of_days = (end_date-start_date).days
#             for i in range(number_of_days):
#                 _date = start_date+datetime.timedelta(days=i)
#                 if _date not in date_range:
#                     date_range.append(_date)
        
#         for each in date_range:
#             url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
#             requests.get(url=url)

#     if command in ["block-current-week","unblock-current-week"]:
#         _command = "block-all" if command=='block-current-week' else 'unblock-all'
#         if keywords["modality"]==None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)
#         start_date = datetime.datetime.now()
#         end_date = calculate_date_for_asked_iso_weekday_from_ref_date(start_date, iso_weekday=7)
#         date_range =[]
#         number_of_days = (end_date-start_date).days
#         for i in range(number_of_days):
#             _date = start_date+datetime.timedelta(days=i)
#             date_range.append(_date)
#         for each in date_range:
#             url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{_command}?modality={keywords['modality'].upper()}&query_date={each.date()}"
#             requests.get(url=url)

#     if command in ["block-time-range","unblock-time-range"]:
#         _command = "block-slot-range" if command=='block-time-range' else 'unblock-slot-range'
#         if keywords["modality"]==None:
#             prRed("Modality cannot be: None")
#             sys.exit(1)
        
#         if keywords["sdate"]==None:
#             prRed("Start date cannot be: None")
#             sys.exit(1)
        
#         if keywords["stime"]==None:
#             prRed("Start time cannot be: None")
#             sys.exit(1)
        
#         if keywords["etime"]==None:
#             prRed("End time cannot be: None")
#             sys.exit(1)
        
#         url = f"{os.getenv('RIS_SIMULATOR_ENDPOINT')}/{_command}?modality={keywords['modality'].upper()}&slot_date={keywords['sdate']}&start_time={keywords['stime']}&end_time={keywords['etime']}"
#         print(url)
#         response = requests.put(url=url)
#         print(response.text)

# with open(test_case_file_path,"r") as fd:
#     test_script = fd.read()
#     prPurple(test_script)
#     regex = r"==SETUP START==[A-Za-z\-_\+0-9=\s,:\n]*==SETUP END=="
#     matches = re.finditer(regex, test_script, re.MULTILINE)
#     setup_section = None
#     for matchNum, match in enumerate(matches, start=1):
#         setup_section = match.group()

#     prGreen("Setup:\n===============")
#     for macro, value in MACROS.items():
#         setup_section = setup_section.replace(macro,value)
    
#     setup_section = setup_section.strip()
#     setup_section = setup_section.splitlines()
#     for each in setup_section:
#         if each in ["==SETUP START==","==SETUP END=="]:
#             continue
#         execute_setup_instruction(each)

# print("-"*30)
# print("-"*30)
# regex = r"==CONVERSATION START==[\[\]A-Za-z\-\+0-9=\s,:\n>.?]*==CONVERSATION END=="
# matches = re.finditer(regex, test_script, re.MULTILINE|re.IGNORECASE)
# conversation_section = None
# for matchNum, match in enumerate(matches, start=1):
#     conversation_section = match.group()
# conversation = conversation_section.splitlines()[1:-1]
# print(conversation)

# is_running = True
# current_step=0
# def fetch_response(ws):
#     while is_running:
#         req = requests.get(url=response_url, timeout=15)
#         if req.text == "null":
#             time.sleep(1)
#             continue
#         msg = req.text.replace('"','')
#         on_message(ws=ws, message=msg)

# def send_request(ws, text:str):
#     msg = json.dumps({
#                     "event": "DATA",
#                     "conversation_id": conversation_id,
#                     "data": text,
#                     "center_id": center_id,
#                 })
#     prGreen(f"CLI:{text}")
#     ws.send(msg)

# def on_message(ws, message):
#     global is_running
#     global current_step
#     message = striphtml(message)
#     prYellow(f"BOT:{message}")
#     time.sleep(1)
#     if message.lower() == "hangup_call":
#         is_running=False
#         ws.close()
#         sys.exit(1)
    
#     conversation_step = conversation[current_step].split(">>>")
#     current_step =current_step+1
#     bot_utterance = conversation_step[0]
#     user_response = conversation_step[1]
#     regex = r"""\[[A-Za-z\-\+0-9=\s,\n:?]*\]"""
#                 # \[[A-Za-z\-\+0-9=\s,\n:?]*\]
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

# def on_open(ws:websocket):
#     # print("Opened connection")
#     msg = json.dumps({
#                         "event": "CONNECTED",
#                         "conversation_id": conversation_id,
#                         "type": "MOBILE",
#                         "contact": caller_id,
#                         "center_id": center_id,
#                         "response_mode":response_mode
#                     })
    
#     ws.send(msg)
#     msg = json.dumps({ "event": "NEW-CONVERSATION", "center_id": center_id, "conversation_id": conversation_id, "contact": caller_id })
#     ws.send(msg)
#     if response_mode=="POLL":
#         x = threading.Thread(target=fetch_response, args=(ws,), daemon=True)
#         x.start()
#     # ws.close()

#     # websocket.enableTrace(True)
# ws = websocket.WebSocketApp(ws_url,
#                             on_open=on_open,
#                             on_message=on_message,
#                             on_error=on_error,
#                             on_close=on_close)
# # print(type(ws))
# ws.run_forever()  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
# is_running=False




# #---------------- ORIGINAL CODE ENDS HERE --------------------