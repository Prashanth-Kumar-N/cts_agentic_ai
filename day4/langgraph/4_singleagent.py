# pip install langchain langchain-openai langgraph mysql-connector-python python-dotenv

# -----------------
# Without Prompting
# -----------------

import os, pandas as pd
import mysql.connector
from dotenv import load_dotenv
# from langchain.tools import tool
# from langchain.agents import create_agent
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

load_dotenv("mysql.env")

# Database Connections
host = os.getenv("HOST")
port = os.getenv("PORT")
user = os.getenv("USER")
pwd = os.getenv("PASSWORD")
db = "medical"

# -----------------------------
# MySQL Connection
# -----------------------------
def ConnectDB():
    try:
        ret = {"status":"", "message":""}

        global CONN

        CONN = mysql.connector.connect(
            host=host, user=user, password=pwd, database=db )

        ret["status"] = "SUCCESS"
        ret["message"] = "Connected to MySQL"

    except Exception as e:
        ret["status"] = "EXCEPTION"
        ret["message"] = str(e)

    return(ret)

ConnectDB()

# -----------------------------
# LangGraph State
# -----------------------------
class PatientState(TypedDict):
    patient_id: str
    session_state: dict # To store each action's State

# -----------------
# Query Execution
# -----------------
def ExecuteQuery(action, query, values=None):
    ret = {"status": '', "message": "", "record": ""}
    act_msg = ''
    CURSOR = CONN.cursor(dictionary=True)

    try:
        if action == "I":
            act_msg = "Inserted"
        elif action == "U":
            act_msg = "Updated"
        elif action == "D":
            act_msg = "Deleted"
        elif action == "S":
            act_msg = "Retrieved"

        if action in ["I", "U", "D"]:
            CURSOR.execute(query, values)
            CONN.commit()
            ret["status"] = "SUCCESS"
            ret["message"] = f"{CURSOR.rowcount} Record(s) {act_msg}"
            ret["record"] = ''
        elif action == "S":
            if values is not None:
                CURSOR.execute(query, values)
            else:
                CURSOR.execute(query)

            data = CURSOR.fetchall()
            ret["status"] = "SUCCESS"
            ret["message"] = f"{len(data)} Record(s) {act_msg} "
            ret["record"] = pd.DataFrame(data)

    except Exception as e:
        ret["status"] = "EXCEPTION"
        ret["message"] = str(e)
        ret["record"] = ''
        CURSOR.close()

    finally:
        CURSOR.close()

    return (ret)

# -----------------------------
# Tools
# -----------------------------
def get_patient_data(state:PatientState):
    """Fetch patient personal information using patient_id."""
    query = """
        SELECT patient_id, age, gender FROM patients WHERE patient_id = %s
    """

    values = (state["patient_id"],)

    response = ExecuteQuery(action="S", query=query, values=values)

    updated_session = dict(state.get("session_state", {}))
    updated_session["patient_data"] = response

    return ({"session_state": updated_session} )

def get_clinical_data(state:PatientState):
    """Fetch patient clinical/vitals data using patient_id."""
    query = """
        SELECT patient_id, bp_s, bp_d, spo2, heart_rate, temp, resp_rate
        FROM patients
        WHERE patient_id = %s
    """
    values = (state["patient_id"],)

    response = ExecuteQuery(action="S", query=query, values=values)

    updated_session = dict(state.get("session_state", {}))
    updated_session["clinical_data"] = response

    return ({"session_state": updated_session} )

def get_surgical_data(state:PatientState):
    """Fetch patient surgical history using patient_id."""
    query = """
        SELECT patient_id, past_surg_history FROM patients WHERE patient_id = %s
    """
    values = (state["patient_id"],)

    response = ExecuteQuery(action="S", query=query, values=values)
    state["session_state"]["surgical_data"] = response

    return ({"session_state": state["session_state"]} )


def get_past_history_data(state:PatientState):
    """Fetch patient past medical history using patient_id."""
    query = """
        SELECT patient_id, past_med_history, allergies, social_hist
        FROM patients
        WHERE patient_id = %s
    """
    values = (state["patient_id"],)

    response = ExecuteQuery(action="S", query=query, values=values)
    state["session_state"]["past_history_data"] = response

    return ({"session_state": state["session_state"]} )


def BuildGraph():
    builder = StateGraph(PatientState)
    builder.add_node("patient_data", get_patient_data)
    builder.add_node("clinical_data", get_clinical_data)
    builder.add_node("surgical_data", get_surgical_data)
    builder.add_node("past_history_data", get_past_history_data)

    builder.set_entry_point("patient_data")

    builder.add_edge("patient_data", "clinical_data")
    builder.add_edge("clinical_data", "surgical_data")
    builder.add_edge("surgical_data", "past_history_data")
    builder.add_edge("past_history_data", END)

    graph = builder.compile()

    return(graph)

graph = BuildGraph()

patient_id = "PT0972"

response = graph.invoke({ "patient_id": patient_id, "session_state": {} })
response

# Individual State info
response['session_state']['patient_data']['record']
response['session_state']['surgical_data']['record']
response['session_state']['clinical_data']['record']
response['session_state']['past_history_data']['record']

# -------------------------------------------------------------------------------------------

# --------------
# With Prompting
# ---------------

import os
import mysql.connector
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
import pandas as pd

load_dotenv("mysql.env")

host = os.getenv("HOST")
user = os.getenv("USER")
pwd = os.getenv("PASSWORD")
db = "medical"

def ConnectDB():
    try:
        ret = {"status":"", "message":""}

        conn = mysql.connector.connect(
            host=host, user=user, password=pwd, database=db )

        ret["status"] = "SUCCESS"
        ret["message"] = "Connected to MySQL"
        ret["connection"] = conn

    except Exception as e:
        ret["status"] = "EXCEPTION"
        ret["message"] = str(e)
        ret["connection"] = None

    return(ret)

def ExecuteQuery(action, query, values=None):
    ret = {"status": '', "message": "", "record": ""}
    act_msg = ''

    connect = ConnectDB()
    status = connect["status"]
    message = connect["message"]
    conn = connect["connection"]

    if status == "SUCCESS":
        cursor = conn.cursor(dictionary=True)

        try:
            if action == "I":
                act_msg = "Inserted"
            elif action == "U":
                act_msg = "Updated"
            elif action == "D":
                act_msg = "Deleted"
            elif action == "S":
                act_msg = "Retrieved"

            if action in ["I", "U", "D"]:
                cursor.execute(query, values)
                conn.commit()
                ret["status"] = "SUCCESS"
                ret["message"] = f"{CURSOR.rowcount} Record(s) {act_msg}"
                ret["record"] = ''
            elif action == "S":
                if values is not None:
                    cursor.execute(query, values)
                else:
                    cursor.execute(query)

                data = cursor.fetchall()
                ret["status"] = "SUCCESS"
                ret["message"] = f"{len(data)} Record(s) {act_msg} "
                ret["record"] = pd.DataFrame(data)

        except Exception as e:
            ret["status"] = "EXCEPTION"
            ret["message"] = str(e)
            ret["record"] = ''
            cursor.close()
            conn.close()

        finally:
            cursor.close()
            conn.close()

    return (ret)

@tool
def get_patient_data(patient_id: str) -> dict:
    """Fetch patient personal data using patient_id."""

    query = """
        SELECT patient_id, age, gender FROM patients WHERE patient_id = %s
    """

    response = ExecuteQuery( action="S", query=query, values=(patient_id,) )

    return {"patient_data": response}


@tool
def get_clinical_data(patient_id: str) -> dict:
    """Fetch patient clinical/vitals data using patient_id."""

    query = """
        SELECT patient_id, bp_s, bp_d, spo2, heart_rate, temp, resp_rate
        FROM patients
        WHERE patient_id = %s
    """

    response = ExecuteQuery(action="S",query=query,values=(patient_id,))

    return {"clinical_data": response}


tools = [get_patient_data, get_clinical_data]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

system_prompt = """
You are a patient data assistant.

You MUST use tools to answer patient data questions.

Rules:
- Never answer from your own knowledge.
- If the user asks for patient data, you must call the relevant tools.
- If the user asks for complete patient details, you must call both:
  1. get_patient_data
  2. get_clinical_data
- Use patient_id exactly as given by the user.
- After tool calls, summarize the records.
"""

agent = create_agent(model=llm,tools=tools,system_prompt=system_prompt)

patient_id = "PT0001"

response = agent.invoke({"messages": [{
                            "role": "user",
                            "content": f"Fetch complete patient details for patient id {patient_id}"
                            }]
                    })

print(response["messages"][-1].content)

# print(get_patient_data.invoke({"patient_id": "PT0001"}))
# print(get_clinical_data.invoke({"patient_id": "PT0001"}))

# ---------------------------------------------------------------------------------------

# globals().clear()