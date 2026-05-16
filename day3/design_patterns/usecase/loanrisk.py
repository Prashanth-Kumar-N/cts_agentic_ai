# import section
import streamlit as st
from PIL import Image
import pandas as pd, time, mysql.connector, psycopg as psy, json, faiss, numpy as np, os, random
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
# from tabulate import tabulate

# initialization section
CLIENT = OpenAI()
file = r"D:\stackroute\2_AI-assisted-programming\learning_requirements\cognizant\2025\1\code\2_AgenticAI\dataset\credit_risk.csv"
bg = r"D:\stackroute\2_AI-assisted-programming\learning_requirements\cognizant\2025\1\code\2_AgenticAI\code_ref\bg\dp.jpg"
list_of_actions = ["Check Risk","Loan Decision", "Reflection"]

FEATURE_COLS = [ "annual_income_usd", "debt_to_income_ratio", "payment_to_income_ratio", "credit_utilization_ratio", "num_delinquencies_12m", 
                "num_late_payments_24m", "loan_amount_requested_usd", "prior_defaults_flag", "bankruptcies_count", "hard_inquiries_6m",
                "total_outstanding_debt_usd", "credit_risk_score" ]


env_file = "D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/db_connections.env"
load_dotenv(env_file)
MS_HOST=os.getenv("MS_HOST")
MS_PORT=os.getenv("MS_PORT")
MS_USER=os.getenv("MS_USER")
MS_PASSWORD=os.getenv("MS_PASSWORD")
MS_DATABASE = "finance"

# session state data
if "rows_to_show" not in st.session_state:
    st.session_state["rows_to_show"] = 6
    
if "credit_risk_data" not in st.session_state:
    st.session_state["credit_risk_data"] = None

if "applicant_data" not in st.session_state:
    st.session_state["applicant_data"] = None
    
if "proceed" not in st.session_state:
    st.session_state["proceed"] = False

if "risk" not in st.session_state:
    st.session_state["risk"] = None

if "reason" not in st.session_state:
    st.session_state["reason"] = None

if "retriever" not in st.session_state:
    st.session_state["retriever"] = None

if "scaler" not in st.session_state:
    st.session_state["scaler"] = None

for l in list_of_actions:
    l = l.replace(" ","").lower()
    
    if l not in st.session_state:
        st.session_state[l] = None

# 1) Load Dataset
if st.session_state["credit_risk_data"] is None:
    credit_risk_data = pd.read_csv(file)
    st.session_state["credit_risk_data"] = credit_risk_data


# function section
def Spaces():
    st.markdown(""" <style> .block-container {padding-top: 2rem;} h1 {margin-top: 1rem; } </style> """, unsafe_allow_html=True)

def home():
    
    desc = ''' Financial institutions process thousands of loan applications daily, each containing multiple financial, behavioral, and credit-related indicators.
Manually evaluating these applications for risk, fraud, repayment capability, and policy compliance is time-consuming and prone to inconsistencies.
An intelligent Agentic AI system can automate and enhance this process by continuously analyzing applicant profiles, reasoning over financial indicators, retrieving similar historical cases, collaborating across specialized agents, and recommending loan decisions with human oversight. \n

In this use case, an Agentic AI system evaluates credit applicants using factors such as income, debt-to-income ratio, credit utilization, prior defaults, bankruptcies, and overall credit risk score. 
The system demonstrates multiple Agentic AI design patterns including ReAct reasoning, Planner–Executor workflows, Multi-Agent collaboration, Reflection, Retrieval-Augmented analysis, Human-in-the-Loop validation, Memory-Augmented learning, and Event-Driven processing. Based on the analysis, the agent classifies applicant risk, recommends loan approval or rejection, assigns the appropriate review team, captures analyst feedback, and stores historical decisions for future learning and auditability.
'''
    
    st.subheader("Credit Risk Assessment and Loan Decisioning")
    st.write(desc)

def check_credit_risk():
    try:
        status = []
    
        applicant = st.session_state["applicant_data"]
        
        if applicant is not None:
            score = applicant.credit_risk_score.tolist()[0]

            if score >= 750:
                risk = "Low Risk"
            elif score >= 650:
                risk = "Medium Risk"
            elif score >= 550:
                risk = "High Risk"
            else:
                risk = "Very High Risk"
                
            st.session_state["risk"] = risk
            st.session_state["score"] = score
            status.extend(["SUCCESS", risk])
        else:
            st.session_state["risk"] = None
            st.session_state["score"] = None
            status.extend(["ERROR", "Applicant Record does not exist"])
           
    except Exception as e:
            status.extend(["EXCEPTION", str(e)])
            
    return (status)


def tool_loan_decision():
    try:
        status = []
        
        applicant = st.session_state["applicant_data"]
        risk = st.session_state["risk"]
        
        if risk is None:
            status.extend(["ERROR", "Credit Risk is not run for this Applicant"])
            st.session_state["reason"] = None
        else:
            dir = applicant["debt_to_income_ratio"].tolist()[0]
            pir = applicant["payment_to_income_ratio"].tolist()[0]
            cur = applicant["credit_utilization_ratio"].tolist()[0]
            prior_defaults = applicant["prior_defaults_flag"].tolist()[0]
            tod = applicant["total_outstanding_debt_usd"].tolist()[0]
            
            qual_score = 0
            total_params = 6
            
            # Each of these can be considered as an Agent. This will simulate Multi-Agent
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
            st.session_state["reason"] = reason
            
            status.extend(["SUCCESS", reason])

    except Exception as e:
        st.session_state["reason"] = None
        status.extend(["EXCEPTION", str(e)])
    
    return (status)


def retrieve_similar_applicants():
    try:
        status = []
        
        credit_risk_data = st.session_state["credit_risk_data"]
        applicant = st.session_state["applicant_data"]
        scaler =   st.session_state["scaler"]
        
        if applicant is not None:
            appl_id = applicant["applicant_id"].tolist()[0].strip()
            
            applicant = applicant[FEATURE_COLS]

            retriever = st.session_state["retriever"]
            input_scaled = scaler.transform(applicant)
            
            distances, indices = retriever.kneighbors(input_scaled)
            similar_records = credit_risk_data.iloc[indices[0]] [["applicant_id" ]]
            similar_records = similar_records[similar_records.applicant_id != appl_id] # do not retrieve the same record.
            
            status.extend(["SUCCESS", similar_records.to_dict(orient="records")])
        else:
            status.extend(["ERROR", "No Applicant Data found"])
    
    except Exception as e:
            status.extend(["EXCEPTION", str(e)])
        
    return (status)


def scale_data():
    # retriever = st.session_state["retriever"]
    
    credit_risk_data = st.session_state["credit_risk_data"]
    scaler = StandardScaler()
    
    X_scaled = scaler.fit_transform(credit_risk_data[FEATURE_COLS])
    retriever = NearestNeighbors(n_neighbors=4, metric="euclidean")
    retriever.fit(X_scaled)
    
    st.session_state["retriever"] = retriever
    st.session_state["scaler"] = scaler
    
def mainmenu():
    t2,t3,t4 = st.tabs(['Home', 'View Dataset', 'Applicant Loan Processing'])
    
    with t2:
        home()
        
    with t3:
        
        data = st.session_state["credit_risk_data"]
        
        c1,c2,c3 = st.columns([0.2,0.2,0.6])
        
        btn_show_all = c2.checkbox("Show All Rows")
        
        # If checkbox selected, update rows_to_show
        if btn_show_all:
            st.session_state["rows_to_show"] = len(data)
        else:
            st.session_state["rows_to_show"] = 6
            
        rows_to_show = c1.number_input("Rows to display", min_value=6, max_value=len(data),key="rows_to_show")
        st.dataframe(data.head(rows_to_show))
        
        cols = len(data.columns) - 1
        c3.success(f"Total Features = {cols}")
        
        
    with t4:
        scale_data()
        c1,c2,c3,c4 = st.columns([0.2,0.2,0.05,0.55])

        appl_id = c1.text_input("Applicant ID",max_chars=10)
        btn_get = c1.button(":arrow_forward:",help="Retrieve Data")
        pattern = c2.selectbox("Action", list_of_actions,index=None)
        
        c1,c2 = st.columns([0.3,0.7])
        # Verify the Applicant ID
        if len(appl_id) > 0:
            data = data = st.session_state["credit_risk_data"]
            df_appl = data[data.applicant_id == appl_id]
            if len(df_appl) > 0:
                st.session_state["applicant_data"] = df_appl
                st.session_state["proceed"] = True
                c1.dataframe(df_appl.T)
            else:
                st.session_state["applicant_data"] = None
                st.session_state["proceed"] = False
                st.toast(f"Applicant with ID '{appl_id}' not found")
        
        # After Applicant ID verification
        proceed = st.session_state["proceed"]
        if (proceed):
            if pattern == list_of_actions[0]: # Credit Risk
                ret = check_credit_risk()
                status,risk = ret
                st.toast(risk)
            elif pattern == list_of_actions[1]: # Loan Decision"
                ret = tool_loan_decision()
                status,reason = ret
                st.toast(reason)
            elif pattern == list_of_actions[2]: # Reflection
                ret = retrieve_similar_applicants()
                status = ret[0]
                if status == "SUCCESS":
                    credit_risk_data = st.session_state["credit_risk_data"]
                    similar_records = ret[1]
                    
                    sim_appl_ids = []; sim_risks = []; sim_reasons = []
                    
                    for rec in similar_records:
                        sim_appl_id = rec['applicant_id']
                        sim_appl_rec = credit_risk_data[FEATURE_COLS][credit_risk_data.applicant_id == sim_appl_id]
                        st.session_state["applicant_data"] = sim_appl_rec
                        
                        ret = check_credit_risk()
                        status,risk = ret
                        
                        ret = tool_loan_decision()
                        status,reason = ret
                        
                        sim_appl_ids.append(sim_appl_id)
                        sim_risks.append(risk)
                        sim_reasons.append(reason)

                    df_sim = pd.DataFrame({"ApplId":sim_appl_ids, "Risk":sim_risks, "Reason":sim_reasons})
                    c4.subheader("Applicants with similar profiles")
                    c4.dataframe(df_sim)

def main():
    Spaces()
    mainmenu()