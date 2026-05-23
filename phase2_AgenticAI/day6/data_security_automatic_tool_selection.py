# app_langgraph_sql_tools.py

import os
import mysql.connector
import pandas as pd
from typing import TypedDict, Literal, List, Dict, Any
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

# ------------------- list of variables -------------------------
env_file = "db_connections.env"

load_dotenv(env_file)

# MySQL connections
MS_HOST=os.getenv("MS_HOST")
MS_PORT=os.getenv("MS_PORT")
MS_USER=os.getenv("MS_USER")
MS_PASSWORD=os.getenv("MS_PASSWORD")
MS_DATABASE = "finance"

# 1) Get MySQL Connection
# -----------------------
def get_mysql_conn():
    try:
        conn = mysql.connector.connect( host=MS_HOST, port=MS_PORT, database=MS_DATABASE, user=MS_USER, password=MS_PASSWORD)
    except Exception as e:
        conn = str(e)

    return(conn)

CONN = get_mysql_conn()

# 2) Run a query in the database
# --------------------------------
def ExecuteQuery(CONN,query,action):
    try:
        cursor = CONN.cursor()
        status = []

        cursor.execute(query)

        if action == "S": # select query
            data = cursor.fetchall()
            cols = [c[0] for c in cursor.description]
            data = pd.DataFrame(data, columns=cols)
            status.extend(["SUCCESS", data])
        elif action in ["I","U","D"]:
            CONN.commit()
            status.extend(["SUCCESS", pd.DataFrame({"status": ["Record added / changed"]})])

    except Exception as e:
        status.extend(["EXCEPTION", str(e)])

    cursor.close()
    return (status)

# 3. SQL Tool Definitions
# -----------------------------
def user_access_tool():
    query = """
    SELECT * FROM data_security  WHERE failed_logins_24h > 3 AND department = 'Risk';
    """
    return ExecuteQuery(CONN,query,"S")

def risk_threat_scoring_tool():
    query = """
    SELECT department, AVG(risk_score) AS avg_risk
    FROM data_security
    GROUP BY department
    ORDER BY avg_risk DESC;
    """
    return ExecuteQuery(CONN,query,"S")

def data_exfiltration_tool():
    query = """
    SELECT user_id, device_type, data_sensitivity_level
    FROM data_security
    WHERE data_sensitivity_level > 4;
    """
    return ExecuteQuery(CONN,query,"S")

def device_endpoint_compliance_tool():
    query = """
    SELECT device_type, encryption_in_transit_flag, unmanaged_device_flag
    FROM data_security
    WHERE unmanaged_device_flag = 0;
    """
    return ExecuteQuery(CONN,query,"S")

def fallback_sql_tool():
    query = """ SELECT * FROM data_security LIMIT 10; """
    return ExecuteQuery(CONN,query,"S")

# 4) LangGraph State
# -----------------------------
class AgentState(TypedDict):
    prompt: str
    selected_tool: str
    sql_result: List[Dict[str, Any]]
    final_answer: str

# 5) LLM-Based Tool Selector
# -----------------------------
llm = ChatOpenAI(model="gpt-4o", temperature=0)

def select_tool(state: AgentState) -> AgentState:

    prompt = state["prompt"]

    system_prompt = """
You are a tool-selection agent for a BFSI data security dataset.

Choose exactly one tool from the following:

1. user_access
Use for:
- failed logins
- suspicious login behavior
- privileged users
- non-business hours access
- authentication issues

2. risk_threat_scoring
Use for:
- risk score
- threat score
- high-risk users
- department-wise risk
- average risk

3. data_exfiltration
Use for:
- DLP violations
- customer financial records
- data sensitivity
- data transfer
- data leakage
- exfiltration

4. device_endpoint_compliance
Use for:
- unmanaged devices
- endpoint compliance
- encryption
- non-compliant devices
- device security

Return only the tool name.
"""

    response = llm.invoke( [("system", system_prompt), ("human", prompt) ] )
    selected_tool = response.content.strip().lower()

    valid_tools = [ "user_access", "risk_threat_scoring", "data_exfiltration",
                    "device_endpoint_compliance", ]

    if selected_tool not in valid_tools:
        selected_tool = "fallback"

    state["selected_tool"] = selected_tool
    return state

# 6) Router Function
# -----------------------------
def route_tool(state: AgentState):

    tool = state["selected_tool"]

    if tool == "user_access":
        return "user_access_node"
    elif tool == "risk_threat_scoring":
        return "risk_threat_scoring_node"
    elif tool == "data_exfiltration":
        return "data_exfiltration_node"
    elif tool == "device_endpoint_compliance":
        return "device_endpoint_compliance_node"
    else:
        return "fallback_node"

# 7) Tool Nodes
# -----------------------------
def user_access_node(state: AgentState) -> AgentState:
    state["sql_result"] = user_access_tool()
    return state

def risk_threat_scoring_node(state: AgentState) -> AgentState:
    state["sql_result"] = risk_threat_scoring_tool()
    return state

def data_exfiltration_node(state: AgentState) -> AgentState:
    state["sql_result"] = data_exfiltration_tool()
    return state

def device_endpoint_compliance_node(state: AgentState) -> AgentState:
    state["sql_result"] = device_endpoint_compliance_tool()
    return state

def fallback_node(state: AgentState) -> AgentState:
    state["sql_result"] = fallback_sql_tool()
    return state

# 8) Final Answer Generator
# -----------------------------
def generate_answer(state: AgentState) -> AgentState:
    prompt = state["prompt"]
    selected_tool = state["selected_tool"]
    sql_result = state["sql_result"]

    sys_prompt = """
    You are a BFSI cyber-security analyst.
    Summarize the SQL result clearly.
    Mention:
    1. Selected tool
    2. What the result means
    3. Key observations
    4. Recommended next action
    
    Do not invent facts beyond the SQL result.
    """
    user_prompt = f"""
    User prompt:
    {prompt}

    Selected tool:
    {selected_tool}

    SQL result:
    {sql_result[:20]}
    """

    response = llm.invoke( [( "system", sys_prompt), ("human",user_prompt) ] )
    state["final_answer"] = response.content
    return state

# 9) Build LangGraph
# -----------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("select_tool", select_tool)

    graph.add_node("user_access_node", user_access_node)
    graph.add_node("risk_threat_scoring_node", risk_threat_scoring_node)
    graph.add_node("data_exfiltration_node", data_exfiltration_node)
    graph.add_node("device_endpoint_compliance_node", device_endpoint_compliance_node)
    graph.add_node("fallback_node", fallback_node)

    graph.add_node("generate_answer", generate_answer)

    graph.set_entry_point("select_tool")

    graph.add_conditional_edges(
        "select_tool",
        route_tool,
        {
            "user_access_node": "user_access_node",
            "risk_threat_scoring_node": "risk_threat_scoring_node",
            "data_exfiltration_node": "data_exfiltration_node",
            "device_endpoint_compliance_node": "device_endpoint_compliance_node",
            "fallback_node": "fallback_node",
        },
    )

    graph.add_edge("user_access_node", "generate_answer")
    graph.add_edge("risk_threat_scoring_node", "generate_answer")
    graph.add_edge("data_exfiltration_node", "generate_answer")
    graph.add_edge("device_endpoint_compliance_node", "generate_answer")
    graph.add_edge("fallback_node", "generate_answer")

    graph.add_edge("generate_answer", END)

    return graph.compile()

# 10. Run Application
# -----------------------------
app = build_graph()
user_prompt = "Show non-compliant endpoints connected to confidential banking resources."

initial_state = { "prompt": user_prompt, "selected_tool": "",
                    "sql_result": [],  "final_answer": "", }

result = app.invoke(initial_state)

print("\nSelected Tool:", result["selected_tool"])
print("\nFinal Answer:")
print(result["final_answer"])
print(result["sql_result"][1])

