# Simple agent
# Write an SQL Query that will fetch information from a MySQL database

import os
import pandas as pd
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
# from typing import TypedDict
import mysql.connector
from dotenv import load_dotenv

'''
typing: A python library used to define data types clearly  
> TypedDict is a way to define the structure of a dictionary in Python.
> It is like a template for a dictionary.
> It tells Python:
    "This dictionary should contain these keys, and each key should have a specific data type."
'''

load_dotenv("mysql.env")

# Database Connections
host = os.getenv("HOST")
port = os.getenv("PORT")
user = os.getenv("USER")
pwd = os.getenv("PASSWORD")
db = "medical"

print(host,user,pwd,db)

CONN = None
CURSOR = None

# ----------------------
# Connect to the Database
# ----------------------
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

# ----------------
# State definition
# ----------------
class PatientState(TypedDict):
    patient_id: str
    status_message: str
    query: str
    values: tuple
    response:list[dict] # this should be a list[dict] for conversion

# Run a query in the database
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

def agent_updatepatient(state:PatientState) -> PatientState:
    try:
        patientid = state["patient_id"]
        query = state["query"]
        values = state["values"]

        ret = ExecuteQuery("U",query,values)

        message = ret["message"]
        df = ret["record"]
        # df_dict = df.to_dict(orient="records")

    except Exception as e:
        df_dict = {"status":"Exception", "msg":str(e)}
        message = "Exception in updatepatient()"

    return( {**state, "status_message":message, "response":df} ) # refresh

def agent_selectpatient(state:PatientState) -> PatientState:
    try:
        query = "select * from patients where patient_id = %s;"
        values = (state["patient_id"],)

        ret = ExecuteQuery("S",query,values)
        df = ret["record"]
        df_dict = df.to_dict(orient="records")

    except Exception as e:
        df_dict = {"status":"Exception", "msg":str(e)}

    return( {**state, "query":query, "response":df_dict} )

def buildgraph():
    graph = StateGraph(PatientState)

    graph.add_node("updatequery", agent_updatepatient)
    graph.add_node("selectquery", agent_selectpatient)

    graph.set_entry_point("updatequery")

    graph.add_edge("updatequery", "selectquery")
    graph.add_edge("selectquery", END)

    graph = graph.compile()
    return(graph)

# execute the function
graph = buildgraph()

patient_id = 'PT1000'
in_val = {'bp_s':111, 'bp_d':88, 'heart_rate':100,
          'weight':88.8, 'temp':40.4,
          'present_complaint':'Stressed Syndrome',
          'allergies':'Cold food and drinks'
        }

items = list(in_val.items())
query = "UPDATE patients SET "
values = ()

for k,v in in_val.items():
    query+= f"{k} = %s,"
    values+=(v,)
query = query.rstrip(",")
query+= " WHERE patient_id = %s"
values+=(patient_id,)

if graph:
    result = graph.invoke({"query":query, "values":values, "patient_id": patient_id,
                            "status_message": '', "response":[{}] } )
print(result)

# print the results separately
result['query']
result['values']
pd.DataFrame(result['response'])

# visualise the graph
png_data = graph.get_graph().draw_mermaid_png()

# file will be created in the Current Working Directory
with open("select_agent.png", "wb") as f:
    f.write(png_data)

# *******************************************************************************************
