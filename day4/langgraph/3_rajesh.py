import os
import pandas as pd
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from typing import TypedDict
import mysql.connector
from dotenv import load_dotenv

load_dotenv("db_connections.env")

# Database Connections
host = os.getenv("HOST")
port = os.getenv("PORT")
user = os.getenv("USER")
pwd = os.getenv("PASSWORD")
db = "medical"

CONN = None
CURSOR = None

def ConnectDB():
    try:
        ret = {"status": "", "message": ""}

        global CONN

        CONN = mysql.connector.connect(
            host=host, user=user, password=pwd, database=db)

        ret["status"] = "SUCCESS"
        ret["message"] = "Connected to MySQL"

    except Exception as e:
        ret["status"] = "EXCEPTION"
        ret["message"] = str(e)

    return (ret)


ConnectDB()


# State definition
class PatientState(TypedDict):
    query: str
    values: str
    response: list[dict]  # this should be a list[dict] for conversion


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
            if values is None:
                CURSOR.execute(query)
            else:
                CURSOR.execute(query,values)

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


def agent_updatepatient(state: PatientState):
    try:
        query = state["query"]
        values = state["values"]
        ret = ExecuteQuery("U", query, values)

    except Exception as e:
        df_dict = {"status": "Exception", "msg": str(e)}

    return ({**state, "query": query, "response": "Record updated"})


def agent_selectpatient(state: PatientState) -> PatientState:
    try:
        query = "select * from patients where patient_id=%s"
        values = (state["values"])

        ret = ExecuteQuery("S", query, values)
        df = ret["record"]
        df_dict = df.to_dict(orient="records")

    except Exception as e:
        df_dict = {"status": "Exception", "msg": str(e)}

    return ({**state, "query": query, "response": df_dict})


def buildgraph():
    graph = StateGraph(PatientState)

    graph.add_node("updatequery", agent_updatepatient)
    graph.add_node("selectquery", agent_selectpatient)

    graph.set_entry_point("updatequery")

    graph.add_edge("updatequery", 'selectquery')
    graph.add_edge("selectquery", END)

    graph = graph.compile()
    return (graph)

# execute the function
graph = buildgraph()

patientId = 'PT0014'
query = "update patients set bp_s = %s where patient_id = %s;"
values = (120.3,patientId)

if graph:
    result = graph.invoke({"query": query, "values":values, "response":[{}]} )

print(result)

# print the results separately
result['query']
result['values']
# pd.DataFrame(result['response'])

# print(pd.DataFrame(result['response']))

# visualise the graph
png_data = graph.get_graph().draw_mermaid_png()

with open("select_agent.png", "wb") as f:
    f.write(png_data)