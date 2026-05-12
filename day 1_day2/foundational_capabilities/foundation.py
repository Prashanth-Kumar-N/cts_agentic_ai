# Classification
import streamlit as st
from PIL import Image
import pandas as pd
import time
from sklearn.model_selection import train_test_split
import statsmodels.api as sm
import numpy as np
from sklearn.feature_selection import f_classif, SelectFdr
import json
from openai import OpenAI

# st.set_page_config(layout='wide')

# session state variables
if "fraud_data" not in st.session_state:
    st.session_state["fraud_data"] = None

if "cust_trans_id" not in st.session_state:
    st.session_state["cust_trans_id"] = None
    
if "new_data" not in st.session_state:
    st.session_state["new_data"] = None
    
if "classification_model" not in st.session_state:
    st.session_state["classification_model"] = None

if "clf_trainx" not in st.session_state:
    st.session_state["clf_trainx"] = None

if "clf_testx" not in st.session_state:
    st.session_state["clf_testx"] = None

if "clf_trainy" not in st.session_state:
    st.session_state["clf_trainy"] = None

if "clf_testy" not in st.session_state:
    st.session_state["clf_testy"] = None

if "fdr" not in st.session_state:
    st.session_state["fdr"] = None

if "pred_data" not in st.session_state:
    st.session_state["pred_data"] = None
    
if "selected_record" not in st.session_state:
    st.session_state["selected_record"] = None
    
if "show_transaction_record" not in st.session_state:
    st.session_state["show_transaction_record"] = True
    
# constants
bg_intro="D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/code_ref/bg/agenticai.jpg"
bg_fraud="D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/code_ref/bg/fraud.jpg"

file="D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/dataset/2_fraud.csv"
Y = "is_fraud"

OPENAICLIENT = OpenAI()

def Spaces():
    st.markdown(""" <style> .block-container {padding-top: 2rem;} h1 {margin-top: 1rem; } </style> """, unsafe_allow_html=True)

def getresponse(user_prompt):
    try:
        sys_prompt = 'You are an expert in investigating and detecting Finance related frauds.'
        response = {}

        msg = [
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        resp = OPENAICLIENT.chat.completions.create(model='gpt-4o', messages=msg)
        answer = resp.choices[0].message.content
        response["status"] = "SUCCESS"
        response["content"] = answer

    except Exception as e:
        response["status"] = "EXCEPTION"
        response["content"] = "getresponse(). " + str(e)

    return (response)


def intropage():
    c1,c2 = st.columns([0.2,0.8])
    c1.image(Image.open(bg_intro))

    intro = ''' Foundational capabilities like autonomy, reasoning, and action define the shift from simple chatbots to true AI agents that can think, decide, and execute tasks with minimal human intervention \n\n
Autonomy\n
AI agents today are designed to operate independently, running continuously until a task is completed. They can set sub‑goals, adapt to changing conditions, and execute multi-step workflows without constant human prompting. This marks a major leap from traditional automation, which only follows predefined rules. \n\n
Reasoning\n
Reasoning enables agents to interpret context, evaluate options, and make decisions. Advanced models now support high-level reasoning, including spatial understanding, relational logic, and complex problem-solving—critical for tasks like robotics, inspections, or IT incident resolution. \n\n
Action\n
The defining feature of agentic AI is its ability to take meaningful actions—calling tools, updating systems, triggering workflows, or interacting with physical environments. This moves AI from being a passive assistant to an active operator capable of executing tasks end-to-end.
'''
    c2.header("Introduction to Agentic AI")
    c2.write(intro)
    
    
def mainmenu():
    t1,t2,t3,t4 = st.tabs(['Introduction', 'Home', 'View Dataset', 'Action'])
    
    with t1:
        intropage()
    
    with t2:
        homepage()
    
    with t3:
        c1,c2 = st.columns([0.8,0.2])
        
        data = st.session_state["fraud_data"]
        rows_to_show = c2.number_input("Rows to display", min_value=5, max_value=len(data))
        c1.dataframe(data.head(rows_to_show))
        
        # rows = len(data)
        cols = len(data.columns) - 1
        c2.success(f"Total Features = {cols}") 
        # st.success("Total Records = " + str(rows) + ".  Total Features = " + str(cols) + ".  Feature to Predict: " + Y)
    
    with t4:
        show_transaction_record = st.session_state["show_transaction_record"]
        
        c1,c2,c3,c4 = st.columns([0.1,0.01,0.445,0.445])
        
        btn_build = c1.button(":white_check_mark:", help="Build Classification Model")
        btn_predict = c1.button(":zap:", help="Predict Fraud")
        btn_show = c1.button(":eye:", help="View a Prediction data")
        btn_analyze = c1.button(":telescope:", help="Analyze")

        if btn_build:
            if st.session_state["classification_model"] is None:
                with st.spinner("Building Classification Model ..."):
                    time.sleep(2)

                    data = st.session_state["fraud_data"]

                    # categorical columns
                    fc = list(data.select_dtypes(include=['object','category']).columns.values)

                    # make dummy variables for all the Categorical variables
                    new_data = data.copy()
                    for c in fc:
                        dummy = pd.get_dummies(new_data[c],drop_first=True,prefix=c)
                        new_data = new_data.join(dummy)
        
                    # Drop the old Categorical columns
                    new_data.drop(columns=fc,inplace=True)

                    # Boolean columns, if any, should be converted to Integer/Float
                    bc = new_data.select_dtypes(include=['bool']).columns
                    if len(bc) > 0:
                        new_data[bc] = new_data[bc].astype(int)
                        
                    trainx,testx,trainy,testy = train_test_split(new_data.drop(Y,axis=1), new_data[Y], test_size=0.1)
                    
                    model = sm.Logit(trainy,trainx).fit()
                    
                    # False Detection Rate
                    selector = SelectFdr(score_func=f_classif, alpha=0.05)
                    selector.fit_transform(trainx, trainy)
                    df_fdr = pd.DataFrame({ "feature": trainx.columns, "f_score": selector.scores_, "p_value": selector.pvalues_,  "selected": selector.get_support() })
                    df_fdr = df_fdr.sort_values("selected",ascending=False)
                    
                    # store session state values
                    st.session_state["new_data"] = new_data
                    st.session_state["clf_trainx"] = trainx
                    st.session_state["clf_testx"] = testx
                    st.session_state["clf_trainy"] = trainy
                    st.session_state["clf_testy"] = testy
                    st.session_state["classification_model"] = model
                    st.session_state["fdr"] = df_fdr
                
            st.success("Model Built ...!!!")
        
        if btn_predict:
            model = st.session_state["classification_model"]
            
            if model is None:
                st.error("Model not built")
            else:
                # st.toast("Classification Model loaded ...", icon = "🔓")
                with st.spinner("Predicting Fraud Transaction ..."):
                    time.sleep(2)
                    
                    data = st.session_state["new_data"]
                    testx = st.session_state["clf_testx"]
                    df_fdr = st.session_state["fdr"]
                    
                    p1 = model.predict(testx)
                    sig_features = df_fdr.feature[df_fdr.selected == True].tolist()

                    # row numbers of Predicted rows
                    p1_ndx = p1.index
                    
                    # For the Predicted rows, extract only the significant features
                    pred_rows_with_sig_features = data[sig_features][data.index.isin(p1_ndx)]
                    pred_rows_with_sig_features['fraud_prob'] = p1.tolist()
                    
                    st.session_state["pred_data"] = pred_rows_with_sig_features
                    st.toast("Done", icon = "🔓")
                    
        if btn_show or show_transaction_record:
            pred_data = st.session_state["pred_data"]
            
            if pred_data is None:
                # st.error("Unable to retrieve Predicted data")
                pass
            else:
                cust_trans_id = st.session_state["cust_trans_id"]
                
                ndx = np.random.choice(pred_data.index)
                prob = round(pred_data['fraud_prob'][pred_data.index == ndx].tolist()[0] * 100,2)
                
                rec = cust_trans_id[cust_trans_id.index == ndx]
                
                rec = cust_trans_id[['transaction_id','customer_id']][cust_trans_id.index==ndx]
                trans_id = rec['transaction_id'].tolist()[0]
                cust_id = rec['customer_id'].tolist()[0]
                
                c3.header(f"Transaction ID = {trans_id}")
                c3.subheader(f"Fraud Probability : {prob}%")
                c3.write("Transaction Data with Significant Features only")
                c3.dataframe(pred_data.loc[ndx].drop("fraud_prob"), use_container_width = False)
                
                st.session_state["selected_record"] = pred_data[pred_data.index == ndx]

        # with t4:
            # st.header("Analyze Transaction and Fraud Probability")
            # btn_analyze = st.button(":telescope:", help="Analyze")
            
        if btn_analyze:
            c4.header("Fraud Transaction Analysis")
            
            sel_rec = st.session_state["selected_record"]
            if sel_rec is None:
                st.error("Select a Valid Transaction Record")
            else:
                with st.spinner("Analyzing Transaction Data ... Please Wait !"):
                    time.sleep(2)
                    
                    fraud_prob = sel_rec["fraud_prob"].tolist()[0]
                    sel_rec.drop(columns=["fraud_prob"], inplace=True)
                    sel_rec_json = json.dumps(sel_rec.iloc[0].to_dict())
                    time.sleep(1)
                    
                    prompt = f'''
                    You have been given 2 inputs. 
                    1.) Transaction Data - in a JSON format 
                    2.) Fraud Probability - in Percentage

                    Analyse the Transaction data and the Fraud probability. Determine whether the fraud probability matches with the transaction data.
                    If Yes, give a suitable name for the fraud type eg: Account Take Over.

                    Also, suggest what kind of action needs to be taken based on the above findings.
                    If the Transaction is valid, give the message as "Good to Go".
                    Else, give a suitable name eg: "Block Transaction" / "Trigger MFA and Step up Authentication" etc.

                    The final output should be in a JSON format with the following schema:
                    is_fraud: Yes or No
                    fraud_type: <Fraud type>
                    action: <Action>
                    confidence: how sure the decision is
                    risk_level: Low / Medium / High
                    risk_signals: Key drivers (very important for auditability)
                    probability_alignment: Does model output match rule-based reasoning
                    recommended_action: Operational next step
                    priority: For case queue
                    explanation: Human-readable reasoning
                     
                    Do not include any other extra characters / text in the output. 
                    Do not include ```json at the beginning of the output.
                    It must be a strict JSON format.
                     
                    Transaction Data: {sel_rec_json}
                     
                    Fraud Probability: {fraud_prob}
                    '''
                    
                    response = getresponse(prompt)
                    time.sleep(2)
                    
                    c4.write(json.loads(response['content']))
            
        
def homepage():
    c1,c2 = st.columns([0.2,0.8])
    c1.image(Image.open(bg_fraud))

    intro = ''' Fraud detection in finance involves identifying and stopping fake or unauthorized activities in financial systems. \n
    It ensures customer security by monitoring transactions for unusual patterns that indicate fraud, such as fake transactions, UPI frauds, or e-commerce fraud. \n\n
    Fraud detection systems focus less on individual events and more on patterns over time. They start with consolidating data—transactions, customer profiles, 
    historical behavior, and device signals—into a single analytical view.
'''
    c2.header("Demo : Fraud Detection")
    c2.write(intro)

    if st.session_state["fraud_data"] is None:
        data = pd.read_csv(file)
        cust_trans_id = data[['transaction_id', 'customer_id']]

        cols_to_remove = ['transaction_id','customer_id','txn_timestamp','account_age_days']
        data.drop(columns=cols_to_remove,inplace=True)
                  
        st.session_state["fraud_data"] = data
        st.session_state["cust_trans_id"] = cust_trans_id
    
def main():
    Spaces()
    mainmenu()


ac = "Loan Decision"
list_of_actions = ["Check Risk","Loan Decision", "Reflection"]
list_of_actions.index(ac)

for l in list_of_actions:
    l = l.replace(" ","").lower()
    print(l)
