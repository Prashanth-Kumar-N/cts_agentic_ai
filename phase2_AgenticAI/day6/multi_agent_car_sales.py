# -*- coding: utf-8 -*-

# ************************************************************
# Use Case: LLM-powered Multi-Agent Car Sales Team (LangGraph)
# ************************************************************

# ------------------------ libraries ------------------------------------
import os, json, re
from typing import TypedDict, List, Dict, Optional, Literal,Any
from math import ceil
from langgraph.graph import StateGraph, END
from openai import OpenAI
import pandas as pd
import re,datetime,random

path = os.getcwd() + "\\dataset\\"

# ---------------------- common variables ---------------------------------
# initialize the OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# read the input data file
INVENTORY = pd.read_csv(path + "car_inventory.csv")
BANK = pd.read_csv(path + "bank_loan.csv")


# ------------------------- common functions -------------------------------
def LogMessage(msg):
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_msg = now + " " + msg
    return(log_msg)

def getResponse(msg):
    resp = client.chat.completions.create(model='gpt-4o',messages=msg,temperature=0.3)
    answer = resp.choices[0].message.content
    return(answer)


# ------------------- Shared State ----------------------------------------
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

# ---------------- List of Agents ---------------------------------

# *********************************************************
# Agent: FindCars
# description: Get all cars by the given filter conditions
# ********************************************************

def FindCars(state: SalesState) -> SalesState:
    '''
        Read the state[filters] and then call FindCarsByCriteria to get the relevant records
        Update the state with the matches
    '''

    log = state["log"]

    log.append(LogMessage("Calling Agent: FindCarsByCriteria()"))

    # call the Tool
    matches, need_finance = FindCarsByCriteria(ss)
    ctr = len(pd.DataFrame(matches))

    log.append(LogMessage(f"Total records fetched: {ctr}"))

    return ({**state, "matches": matches, "need_finance": need_finance, "log": log})


# *****************************************************
# Agent: SelectCar
# description: Select a random car as the final choice
# ****************************************************

def SelectCar(state: SalesState) -> SalesState:
    ''' Pick a random car from the given set of cars '''

    log = state["log"]

    log.append(LogMessage("Calling Agent: SelectCar()"))

    list_of_cars = pd.DataFrame(state['matches'])['id']

    if len(list_of_cars) > 0:
        car_id = random.choice(list_of_cars)
    else:
        car_id = "default"

    # pick a random value for car trade in
    trade_in = random.choice([True, False])

    log.append(LogMessage(f"SelectCar(). Car ID = {car_id}"))

    return ({**state, "car_id": car_id, "trade_in": trade_in, "log": log})


# *******************************************
# Agent: GetPrice
# description: Negotiate the final car price
# *******************************************

def GetPrice(state: SalesState) -> SalesState:
    ''' negotiate the car price '''

    log = state["log"]
    price_ok = state["price_ok"]

    log.append(LogMessage("Calling Agent: GetPrice()"))

    car_id = state['car_id']
    trade_in = state['trade_in']

    if "final_price" not in state:
        mycar = INVENTORY[INVENTORY.id == car_id]
        base_price = mycar['price'].tolist()[0]
        final_price = base_price
    else:
        final_price = state['final_price']

    log.append(LogMessage(f"GetPrice(). Before negotiation: Price = {final_price}"))

    # Tool call
    final_price = NegotiatePrice(price_ok, car_id, trade_in, final_price)

    log.append(LogMessage(f"GetPrice(). After negotiation: Price = {final_price}"))

    # simulate the final price selection
    return ({**state, "price_ok": random.choice([False, True]), "final_price": final_price, "log": log})


# **********************************************
# Agent: AcceptPrice
# description: Accept the final negotiated price
# **********************************************
def AcceptPrice(state: SalesState) -> SalesState:
    log = state["log"]

    log.append(LogMessage("Calling Agent: AcceptPrice()"))
    log.append(LogMessage(f"AcceptPrice(). Price Finalized"))

    return ({**state, "log": log, "price_ok": True})


# **************************************
# Agent: Finance
# description: Lists all finance options
# **************************************
def Finance(state: SalesState) -> SalesState:
    log = state["log"]
    log.append(LogMessage("Calling Agent: Finance()"))

    # finance_options = FinanceOptions(car_id, final_price)
    finance_options = FinanceOptions("A")

    return ({**state, "finance_options": finance_options, "log": log})


# *******************************************
# Agent: SelFinance
# description: Select a random Finance option
# *******************************************
def SelFinance(state: SalesState) -> SalesState:
    log = state["log"]

    log.append(LogMessage("Calling Agent. SelFinance()"))

    # select a random Finance option
    finance_details = Finance("R")

    return ({**state, "finance_details": finance_details})


# ***************************
# Agent: Close
# description: Close the Deal
# ***************************

def CloseDeal(state: SalesState) -> SalesState:
    log = state["log"]

    log.append(LogMessage("Calling Agent: CloseDeal()"))

    # Prepare the closing deal

    cols = ['id', 'make', 'model', 'year', 'fuel', 'body']
    car_details = INVENTORY[cols][INVENTORY.id == 'HO-173'].to_dict(orient="records")[0]
    car_details["price"] = state['final_price']

    car_details.update(state["finance_details"])

    prompt = f''' {car_details}

            Given above are the details of the car purchase and finance. 
            Prepare a complete sales document for the above deal. Have separate paragraphs for the car and finance details.
            The document date should be the current date and time.

            Do not include any other text or content in the output.
            '''
    sys_content = "You are a car deal closure expert well versed in preparing the deal documents"

    msg = [{'role': 'system', 'content': sys_content},
           {'role': 'user', 'content': prompt}]

    answer = getResponse(msg)

    return ({**state, "final_proposal": answer, "log": log})

# ----------------- / List of Agents ------------------------------


# ----------------------------------- tools ----------------------------------------------------------

# **********************************************************
# TOOL 1) find the list of cars matching the search criteria
# **********************************************************
def FindCarsByCriteria(filter_cond:Dict[str,Any]) -> List[Dict[str,Any]]:
    
    ''' Retrieve a list of cars for a given a set of filters .
    This is only a Tool, Deterministic and does not make decision.
    '''
    
    try:
        inventory = INVENTORY.copy()
        default = 'default'
        
        filters = filter_cond['filters']

        for k,v in filters.items():
            if k == "price":
                v = tuple(v)
                if len(v) >= 2:
                    minval = min(v); maxval = max(v)
                else:
                    minval = min(v); maxval = min(v) + 2000 # if only 1 price is given, set a range of [min, min+2000]
                    
                inventory = inventory[inventory[k].between(minval,maxval)]
            else:
                inventory = inventory[inventory[k].isin(v)]
    
        # filter the cars based on user choices
        if len(inventory) > 0:
            inventory = inventory[['id','make','model','year','fuel', 'price']].to_dict(orient="records")
        else:
            inventory = {'id':[default],'make':[default], 'model':[default],
                         'year':[0], 'fuel':[default], 'price':[0]}
        
        # set the 'need_finance' to T/F.
        if( ("need_finance" in filter_cond.keys()) and (filter_cond['need_finance']) ):
            need_finance = True
        else:
            need_finance = False

    except Exception as e:
            inventory = {'id':[default],'make':[default], 'model':[default],
                         'year':[0], 'fuel':[default], 'price':[0]}
        
    return(inventory,need_finance)

# ********************************************************
# TOOL 2) Negotiate the Car Price till the user accepts it
# ********************************************************
def NegotiatePrice(price_ok, car_id,trade_in,final_price) -> int:
    
    if not price_ok:
        mycar = INVENTORY[INVENTORY.id == car_id]
        base_price = mycar['price'].tolist()[0]
    
        base_discount = 0.05  # 5%
        trade_extra = 0.03 if trade_in else 0.0
    
        if final_price <= 0:
            n_price = ceil(base_price * (1 - base_discount - trade_extra))
        else:
            n_price = ceil(final_price * (1 - base_discount - trade_extra))
    else:
        n_price = final_price
    
    return(n_price)

# *******************************************
# TOOL 3) Fetch the Finance options avaialble 
# *******************************************
def FinanceOptions(flag):

    if flag == "A":
        bankdetails = BANK.to_dict()
    else:
        bank_selection = BANK.sample(1)

        bankname = bank_selection.bank_name.tolist()[0]
        interest_rate = bank_selection.interest_rate.tolist()[0]
        tenure = bank_selection.tenure.tolist()[0]
        emi = bank_selection.emi.tolist()[0]

        bankdetails = {"bank":bankname, "interest":interest_rate, "tenure":tenure, "emi":emi}

    return(bankdetails)

# ------------------------------------ Graph ----------------------------------------------------

g = StateGraph(SalesState)

g.add_node("findcars", FindCars)
g.add_node("selectcar",SelectCar)
g.add_node("negotiateprice",GetPrice)
g.add_node("acceptprice",AcceptPrice)
g.add_node("financeoptions",Finance)
g.add_node("selectfinance",SelFinance)
g.add_node("closedeal",CloseDeal)

g.set_entry_point("findcars")

g.add_edge("findcars","selectcar")
g.add_edge("selectcar","negotiateprice")

# conditional edge
def check_price(state:SalesState):
    return "price_accept" if state["price_ok"] else "price_retry"

g.add_conditional_edges("negotiateprice",check_price, 
                        {"price_retry":"negotiateprice", "price_accept":"acceptprice"})

def check_finance(state:SalesState):
    return "finance_yes" if state["need_finance"] else "finance_no"

g.add_conditional_edges("acceptprice",check_finance,
                        {"finance_yes":"financeoptions", "finance_no":"closedeal"})

g.add_edge("financeoptions","selectfinance")
g.add_edge("selectfinance", "closedeal")
g.add_edge("closedeal",END)

# compile the Graph
graph = g.compile()

# create the filters
ss:SalesState = {'filters':{'price':[12000,20000], 'make':['Honda'], 'year':[2021]},
                 'log':[],
                 'price_ok':False,
                 'need_finance':True
                 }

# run the Graph
result = graph.invoke(ss)

# View the results
print(result)
result['log']
result['car_id']
result['final_price']
result['trade_in']
result['need_finance']
result['finance_options']
result['finance_details'] = result['finance_options'][0]
print(result['final_proposal'])






# ------------------------------------------------ testing --------------------------------------------------

# # myfinance = random.sample(result['finance_options'],1)[0]
# # del myfinance['option']
# # myfinance

# cols = ['id','make','model','year','fuel','body']
# car_details = INVENTORY[cols][INVENTORY.id == 'HO-173'].to_dict(orient="records")[0]
# car_details["price"] = result['final_price']

# car_details

# car_details.update(result['finance_details'])
# car_details

