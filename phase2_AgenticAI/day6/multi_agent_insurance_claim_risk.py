# -*- coding: utf-8 -*-

'''
An Intelligent Insurance Claim Risk Assessment System uses a multi-agent architecture to evaluate insurance claims and identify potential fraud risks.

-------------------------------
What is Loss Amount calculation
-------------------------------
** The Loss Amount Calculation estimates how much money the insurance company is likely to pay for a claim
   after considering damage estimates, repair costs, and policy deductions.

Agent 1
--------
Performs financial and risk-related calculations such as estimated loss amount and claim risk scoring using structured
claim data.

------------------------------
What is Risk Score calculation
------------------------------
** The Risk Score Calculation determines how risky or potentially fraudulent an insurance claim is based on
   multiple behavioral, financial, and historical factors.
   “How suspicious or risky is this claim?”

Agent 2
-------
Performs reasoning on these calculated outputs to recommend actions like approval, manual review, escalation, or fraud investigation.

This approach helps insurance companies automate claim assessment, improve accuracy, and reduce fraudulent payouts.
'''


# ------------------------ libraries ------------------------------------
import os
from typing import TypedDict, List, Dict, Optional, Literal, Any
from langgraph.graph import StateGraph, END
from openai import OpenAI
import pandas as pd
import datetime, math

path = os.getcwd() + "\\dataset\\"

# ---------------------- common variables ---------------------------------
# initialize the OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# read the input data file
INSURANCE = pd.read_csv(path + "insurance_claim_risk.csv")
print(INSURANCE.head())

# ------------------------- common functions -------------------------------
def LogMessage(msg):
    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_msg = now + " " + msg
    return (log_msg)


def getResponse(msg):
    resp = client.chat.completions.create(model='gpt-4o', messages=msg, temperature=0.3)
    answer = resp.choices[0].message.content
    return (answer)


# ------------------- Shared State ----------------------------------------
class InsuranceClaimState(TypedDict):
    log: List
    claim_id: str
    est_loss_amt: float
    risk_score: int
    reason: str


# *********************************************************
# Agent & Tools
# ********************************************************
# 1)
def Agent_ClaimEvaluation(state: InsuranceClaimState) -> InsuranceClaimState:
    '''
        Read the Insurance data and calculate the Loss Amount and Risk Score
        Store the values in the State and Log the transaction
    '''

    log = state["log"]
    claim_id = state["claim_id"]
    log.append(LogMessage("Transaction Started"))

    log.append(LogMessage(f"Processing Claim Evaluation for Claim ID : {claim_id}"))
    log.append(LogMessage("Invoking Agent: ClaimEvaluation"))

    # call Tool 1
    log.append(LogMessage("Calling Tool: CalculateLossAmount"))
    loss_amount = CalculateLossAmount(claim_id)

    # call Tool 2
    log.append(LogMessage("Calling Tool: CalculateRiskScore"))
    risk_score = CalculateRiskScore(claim_id)
    log.append(LogMessage("Transaction Ended"))

    return ({**state, "est_loss_amt": loss_amount, "risk_score": risk_score, "log": log})

def CalculateLossAmount(claim_id):
    cust_data = INSURANCE[INSURANCE.claim_id == claim_id]

    claim_amt = (0.4) * cust_data.claim_amount.values
    repair_inv_amt = (0.3) * cust_data.repair_invoice_amount.values
    assessor_est_loss = (0.3) * cust_data.assessor_estimated_loss.values
    ded_amt = cust_data.deductible_amount.values

    est_loss_amt = (claim_amt + repair_inv_amt + assessor_est_loss) - ded_amt
    return (est_loss_amt)

def CalculateRiskScore(claim_id):
    cust_data = INSURANCE[INSURANCE.claim_id == claim_id]

    fp = cust_data.fraud_probability.values
    cf = cust_data.claim_frequency_12m.values
    pcc = cust_data.previous_claim_count.values
    iar = cust_data.invoice_to_assessor_ratio.values
    ds = cust_data.documents_submitted_pct.values
    ad = cust_data.accident_report_delay_days.values

    risk_score = (fp*40) + (cf*5) + (pcc*4) + (iar*10) + ((100-ds)*0.2) + (ad*0.5)
    risk_score = math.ceil(risk_score[0])

    return(risk_score)

# 2)
def Agent_Reasoning(state: InsuranceClaimState) -> InsuranceClaimState:

    log = state["log"]
    risk_score = state["risk_score"]

    log.append(LogMessage("Transaction Started"))
    log.append(LogMessage("Invoking Agent: ReAct"))
    reason = ReAct(risk_score)

    log.append(LogMessage("Transaction Ended"))

    return ({**state, "reason":reason, "log": log})

def ReAct(risk_score):
    if risk_score > 80:
        reason = "Critical Risk. Action: Reject / Fraud Team Escalation"
    elif risk_score > 60:
        reason = "High Risk. Action: Investigation"
    elif risk_score > 30:
        reason = "Medium Risk. Action: Manual Review"
    else:
        reason = "Low Risk. Action: Auto Approve"

    return(reason)

def BuildGraph():
    g = StateGraph(InsuranceClaimState)

    g.add_node("claimevaluation", Agent_ClaimEvaluation)
    g.add_node("reasoning", Agent_Reasoning)

    g.set_entry_point("claimevaluation")
    g.add_edge("claimevaluation","reasoning")
    g.add_edge("reasoning",END)

    # compile the Graph
    graph = g.compile()

    return (graph)

graph = BuildGraph()

# create the filters
ict:InsuranceClaimState = {'claim_id':'CLM00011', 'log':[], }

# run the Graph
result = graph.invoke(ict)
print(result['log'])
print(result['est_loss_amt'])
print(result['risk_score'])
print(result['reason'])