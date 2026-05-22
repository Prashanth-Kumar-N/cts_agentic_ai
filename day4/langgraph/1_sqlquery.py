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

# State definition
class PatientState(TypedDict):
    query: str
    values: str
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
        else:
            CURSOR.execute(query)

        if action == "S":  # select query
            data = CURSOR.fetchall()
            ret["status"] = "SUCCESS"
            ret["message"] = f"{len(data)} Record(s) {act_msg} "
            ret["record"] = pd.DataFrame(data)

        elif action in ["I", "U", "D"]:
            CONN.commit()

            if CURSOR.rowcount == 0:
                ret["status"] = "ERROR"
                ret["message"] = "No matching record found"
                ret["record"] = ""
            else:
                ret["status"] = "SUCCESS"
                ret["message"] = f"{CURSOR.rowcount} Record(s) {act_msg}"
                ret["record"] = ''

    except Exception as e:
        ret["status"] = "EXCEPTION"
        ret["message"] = str(e)
        ret["record"] = ''
        CURSOR.close()

    finally:
        CURSOR.close()

    return (ret)

def agent_selectpatient(state:PatientState) -> PatientState:
    try:
        query = state["query"]
        values = state["values"]
        ret = ExecuteQuery("S",query,values)
        df = ret["record"]
        df_dict = df.to_dict(orient="records")

    except Exception as e:
        df_dict = {"status":"Exception", "msg":str(e)}

    return( {**state, "query":query, "response":df_dict} ) # refresh

def buildgraph():
    graph = StateGraph(PatientState)

    graph.add_node("selectquery", agent_selectpatient)
    graph.set_entry_point("selectquery")
    graph.add_edge("selectquery", END)

    graph = graph.compile()
    return(graph)

# execute the function
graph = buildgraph()

query = "select * from patients limit 5;"

if graph:
    result = graph.invoke({"query":query, "values":None, "response":[{}]})

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

os.getcwd()



# *******************************************************************************************


from pydantic import BaseModel, StrictStr

# -------------------------------
# All the variables are mandatory
# -------------------------------
class SupplierState(BaseModel):
    var1: str
    var2: str
    query: StrictStr
    values: StrictStr
    record: list[dict]

s1 = SupplierState(var1="var1")
s1 = SupplierState(var1="var1", var2="var2", query="query", values="values", record=[{}] )
print(s1.record)
print(s1)

# ------------------------------
# All the variables are optional
# ------------------------------
class SupplierState(BaseModel):
    var1: str = None
    var2: str = None
    query: StrictStr = None
    values: StrictStr = None
    record: list[dict] = None

s1 = SupplierState(var1="var1")
s1 = SupplierState(var1="var1", var2="var2", query="query", values="values" )
s1 = SupplierState(record = [{'name':'sriraman'}])
s1.query = "select * from customers"
print(s1)

