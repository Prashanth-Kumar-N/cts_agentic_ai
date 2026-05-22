# -------------------------
# Design Patterns explained
# -------------------------
# ReAct / Planner Executor / Multi-Agent Collaborator / Reflection / Tool-Using
# Memory Augmented / Hierarchical / Human-In-The-Loop / Retrieval-Augmented / Event Driven

# --------
# Workflow
# --------
# CSV → Event Trigger → Planner → Executors → Tools → Memory → Feedback → Reflection

# Uses:
# LLM (for reasoning)
# FAISS (for retrieval)
# MySQL (for memory)
# Pandas (CSV)

import pandas as pd, mysql.connector, psycopg as psy, json, faiss, numpy as np, os, random
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from tabulate import tabulate

env_file = "D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/db_connections.env"

load_dotenv(env_file)

# MySQL connections
MS_HOST=os.getenv("MS_HOST")
MS_PORT=os.getenv("MS_PORT")
MS_USER=os.getenv("MS_USER")
MS_PASSWORD=os.getenv("MS_PASSWORD")
MS_DATABASE = "finance"

client = OpenAI()

file = os.getcwd() + "\\dataset\\credit_risk.csv"

# 1) Load Dataset
credit_risk_data = pd.read_csv(file)
print(credit_risk_data.head().T)
credit_risk_data.dtypes

nc = credit_risk_data.select_dtypes(exclude=["object"]).columns.values
fc = credit_risk_data.select_dtypes(include=["object"]).columns.values
print(nc)
print(fc)

# 2) Find Similar Customers (Retrieval-Augmented Pattern)
feature_cols = [
    "annual_income_usd", "debt_to_income_ratio", "payment_to_income_ratio", "credit_utilization_ratio",
    "num_delinquencies_12m", "num_late_payments_24m", "loan_amount_requested_usd",
    "prior_defaults_flag", "bankruptcies_count", "hard_inquiries_6m",
    "total_outstanding_debt_usd", "credit_risk_score" ]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(credit_risk_data[feature_cols])
retriever = NearestNeighbors(n_neighbors=4, metric="euclidean")
retriever.fit(X_scaled)

def retrieve_similar_applicants(applicant):
    input_scaled = scaler.transform(applicant)

    distances, indices = retriever.kneighbors(input_scaled)

    similar_records = credit_risk_data.iloc[indices[0]] [["applicant_id" ]]
    similar_records = similar_records[similar_records.applicant_id != appl_id]

    # similar_records = credit_risk_data.iloc[indices[0]][
    #     [
    #         "applicant_id", "annual_income_usd", "debt_to_income_ratio",
    #         "loan_amount_requested_usd", "prior_defaults_flag",
    #         "bankruptcies_count", "credit_risk_score" ]
    # ]

    return similar_records.to_dict(orient="records")

appl_id = "A100003"
applicant = credit_risk_data[feature_cols][credit_risk_data.applicant_id == appl_id]
similar_records = retrieve_similar_applicants(applicant)
print(similar_records)

# 3) ReAct Pattern  (Reason and Act)
# Tool
def tool_check_risk(applicant):
    score = applicant.credit_risk_score.tolist()[0]
    if score >= 750:
        risk = "Low Risk"
    elif score >= 650:
        risk = "Medium Risk"
    elif score >= 550:
        risk = "High Risk"
    else:
        risk = "Very High Risk"

    return (score, risk)

def tool_loan_decision(lov):
    risk = lov["risk"]
    dir = lov["debt_to_income_ratio"]
    pir = lov["payment_to_income_ratio"]
    cur = lov["credit_utilization_ratio"]
    prior_defaults = lov["prior_defaults_flag"]
    tod = lov["total_outstanding_debt_usd"]

    qual_score = 0
    total_params = 6

    # Each of these can be considered as an Agent
    # This will simulate Multi-Agent
    # 1
    if "Low" in risk or "Medium" in risk:
        qual_score+=random.randint(8,10)
    else:
        qual_score+=random.randint(1,5)

    # 2
    if dir > 0.3:
        qual_score+=random.randint(6,10)
    else:
        qual_score+=random.randint(1,5)

    # 3
    if pir > 0.23:
        qual_score+=random.randint(7,10)
    else:
        qual_score+=random.randint(1,6)

    # 4
    if cur > 0.34:
        qual_score+=random.randint(7,10)
    else:
        qual_score+=random.randint(1,6)

    # 5
    if prior_defaults == 0:
        qual_score+=random.randint(8,10)
    else:
        qual_score+=random.randint(1,7)

    # 6
    if tod > 100000:
        qual_score += random.randint(6, 10)
    else:
        qual_score += random.randint(1, 5)

    qual_score = int(round((100 * qual_score) / (total_params * 10), 0))

    if qual_score > 75:
        reason = "Loan Process for Application has been APPROVED."
    else:
        reason = "Loan Process for Application has been REJECTED / PUT ON HOLD."

    reason+= f"Qual Score is: {qual_score}"

    return(reason)


score, risk = tool_check_risk(applicant)
# Based on research, top factors that can influence a loan are:
lov = {"risk":risk,
       "debt_to_income_ratio":applicant["debt_to_income_ratio"].values,
        "payment_to_income_ratio":applicant["payment_to_income_ratio"].values,
        "credit_utilization_ratio":applicant["credit_utilization_ratio"].values,
        "prior_defaults_flag":applicant["prior_defaults_flag"].values,
        "total_outstanding_debt_usd":applicant["total_outstanding_debt_usd"].values
       }

reason = tool_loan_decision(lov)
print(reason)

def reflection():
    sim_appl_ids = []; sim_risks = []; sim_reasons = []

    for rec in similar_records:
        sim_appl_id = rec['applicant_id']
        sim_appl_rec = credit_risk_data[feature_cols][credit_risk_data.applicant_id == sim_appl_id]
        score, risk = tool_check_risk(sim_appl_rec)

        # Based on research, top factors that can influence a loan are:
        lov = {"risk": risk,
               "debt_to_income_ratio": sim_appl_rec["debt_to_income_ratio"].values,
               "payment_to_income_ratio": sim_appl_rec["payment_to_income_ratio"].values,
               "credit_utilization_ratio": sim_appl_rec["credit_utilization_ratio"].values,
               "prior_defaults_flag": sim_appl_rec["prior_defaults_flag"].values,
               "total_outstanding_debt_usd": sim_appl_rec["total_outstanding_debt_usd"].values
               }

        reason = tool_loan_decision(lov)
        sim_appl_ids.append(sim_appl_id)
        sim_risks.append(risk)
        sim_reasons.append(reason)

    df_sim = pd.DataFrame({"ApplId":sim_appl_ids, "Risk":sim_risks, "Reason":sim_reasons})
    print(df_sim)

    tbl_data = list(zip(sim_appl_ids,sim_risks,sim_reasons))
    tbl_headers = ['Applicant ID', 'Risk', 'Reason']
    print(tabulate(tbl_data, headers=tbl_headers, tablefmt="grid"))

        # print(f"Sim Appl ID: {sim_appl_id}, \nRisk: {risk}, \nReason: {reason}")
        # print()

reflection()