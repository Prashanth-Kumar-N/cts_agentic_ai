# -*- coding: utf-8 -*-

# ************************************************************
# Use Case: LLM-powered Multi-Agent Car Sales Team (LangGraph)
# ************************************************************

# globals().clear()

# ------------------------ libraries ------------------------------------
import os, json, re
from typing import TypedDict, List, Dict, Optional, Literal, Any
from math import ceil
from langgraph.graph import StateGraph, END
from openai import OpenAI
import pandas as pd
import re, datetime, random

path = os.getcwd() + "\\dataset\\"

# read the input data file
INVENTORY = pd.read_csv(path + "car_inventory.csv")
BANK = pd.read_csv(path + "bank_loan.csv")

def ListFinanceOptions():
    # finance_options = FinanceOptions(car_id, final_price)
    finance_options = Finance("A")

    return(finance_options)

def SelectFinance():
    # select a random Finance option
    finance_details = Finance("R")

    return(finance_details)

def Finance(flag):
    if flag == "A":
        bankdetails = BANK.to_dict(orient="records")
    else:
        bank_selection = BANK.sample(1)

        bankname = bank_selection.bank_name.tolist()[0]
        interest_rate = bank_selection.interest_rate.tolist()[0]
        tenure = bank_selection.tenure.tolist()[0]
        emi = bank_selection.emi.tolist()[0]

        bankdetails = {"bank": bankname, "interest": interest_rate, "tenure": tenure, "emi": emi}

    return (bankdetails)

ret1 = ListFinanceOptions()
type(ret1)
print(ret1)

ret2 = SelectFinance()
type(ret2)
print(ret2)

# ------------------------------------------------------------------------------------------------------

# Langgraph version

import os, json, re
from typing import TypedDict, List, Dict, Optional, Literal,Any
from math import ceil
from langgraph.graph import StateGraph, END
import pandas as pd
import re,datetime,random

path = os.getcwd() + "\\dataset\\"

# read the input data file
BANK = pd.read_csv(path + "bank_loan.csv")

def LogMessage(msg):
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_msg = now + " " + msg
    return(log_msg)

class SalesState(TypedDict, total=False):
    log: List
    filters: Dict
    matches: Dict
    price_ok: bool
    car_id: str
    trade_in: bool
    final_price: int
    need_finance: bool
    finance_options: List
    finance_details: Dict
    final_proposal: str

def ListFinanceOptions(state: SalesState) -> SalesState:

    log = state["log"]
    log.append(LogMessage("Calling Agent: Finance()"))

    finance_options = Finance("A")

    return ({**state, "finance_options": finance_options, "log": log})


def SelectFinance(state: SalesState) -> SalesState:
    log = state["log"]

    log.append(LogMessage("Calling Agent. SelFinance()"))

    # select a random Finance option
    finance_details = Finance("R")

    return ({**state, "finance_details": finance_details, "log":log})

def Finance(flag):

    if flag == "A":
        return (BANK.to_dict(orient="records") )
    else:
        bank_selection = BANK.sample(1).iloc[0]

    return {
        "bank": bank_selection["bank_name"],
        "interest": bank_selection["interest_rate"],
        "tenure": bank_selection["tenure"],
        "emi": bank_selection["emi"]
    }

g = StateGraph(SalesState)
g.add_node("listfinanceoptions",ListFinanceOptions)
g.add_node("selectfinance",SelectFinance)
g.set_entry_point("listfinanceoptions")
g.add_edge("listfinanceoptions","selectfinance")
g.add_edge("selectfinance",END)

# compile the Graph
graph = g.compile()

# create the filters
ss:SalesState = {'log':[],    "finance_options": [], "finance_details": {} }

# run the Graph
result = graph.invoke(ss)

print(result['finance_options'])
print(result['finance_details'])



