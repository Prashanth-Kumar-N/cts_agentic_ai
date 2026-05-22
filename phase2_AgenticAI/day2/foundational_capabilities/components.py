# -*- coding: utf-8 -*-
# author: Sriraman.Rajagopalan

'''
Component	In Your Use Case
---------   ----------------
Goal	    Categorise a news headline and route it for publishing
Perception	Read the headline/article
Reasoning	Understand topic, intent, entities, urgency
Plan	    Decide steps: classify → fetch related news → assign editor
Act	        Produce genre, top 3 related news, editor
Feedback	Editor accepts/rejects classification
Memory	    Store past classifications and editor preferences
'''

import streamlit as st
from openai import OpenAI
import time, pandas as pd, datetime, json, ast
from PIL import Image

# features = ["article"]

TABS = ["Home", "Categorize News", "View Routing", "View Article"]
bg_intro="D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/code_ref/bg/agenticai.jpg"

# list of input and output files
headline_filename = "D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/dataset/headlines.csv"
editor_filename = "D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/dataset/editor_data.csv"
routing_filename = "D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/dataset/headline_routing.csv"
headline_article = "D:/stackroute/2_AI-assisted-programming/learning_requirements/cognizant/2025/1/code/2_AgenticAI/dataset/headline_articles.csv"

# a refresh counter to create and delete session states
if "ctr" not in st.session_state:
    st.session_state.ctr = 0
    
if "headline_data" not in st.session_state:
    st.session_state["headline_data"] = None
    
if "hid" not in st.session_state:
    st.session_state["hid"] = 0
    
if "hid_to_process" not in st.session_state:
    st.session_state["hid_to_process"] = None

if "headline" not in st.session_state:
    st.session_state["headline"] = None

if "editor_data" not in st.session_state:
    st.session_state["editor_data"] = None
    
if "edited_routing_data" not in st.session_state:
    st.session_state["edited_routing_data"] = None

if "headline_article_data" not in st.session_state:
    st.session_state["headline_article_data"] = None
    
if "headline_text" not in st.session_state:
    st.session_state["headline_text"] = None
    

# get all the headlines data
data = pd.read_csv(headline_filename)
st.session_state["headline_data"] = data

# get the Editor data
editor_data = pd.read_csv(editor_filename)
st.session_state["editor_data"] = editor_data

# Headline content Data
headline_article_data = pd.read_csv(headline_article)
st.session_state["headline_article_data"] = headline_article_data

# Active Tab selection 
st.session_state["active_tab"] = TABS[0]

# =================
# session functions
# =================
def Spaces():
    st.markdown(""" <style> .block-container {padding-top: 3rem;} h1 {margin-top: 1rem; } </style> """, unsafe_allow_html=True)

def Initialise():
    for ft in features:
        key = f"{ft}_{st.session_state.ctr}"
        if key not in st.session_state:
            st.session_state[key] = None

def ClearData():
    for key in features:
        key = f"{key}_{st.session_state.ctr}"
        if key in st.session_state:
            del st.session_state[key]
            
    st.session_state.ctr+=1

def Home():
    df1 =  pd.DataFrame({ "Goals": ["Agent sets a clear goal based on user input"],
            "Perception" : ["Simulates gathering information from an external source or environment"],
            "Reasoning": ["Analyzes perceived data to make inferences"],
            "Plan": ["Creates a strategy or sequence of actions"],
            "Act": ["Executes actions as per the plan"],
            "Feedback": ["Evaluates results of the action to decide next steps"],
            "Memory": ["Stores results or learnings for future use"]
           }).T.reset_index()
    df1.columns = ["Component", "Description"]
    
    return(df1)

def GetResponse(system_prompt, user_prompt):
    try:
        response = []

        client = OpenAI()

        msg = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]

        resp = client.chat.completions.create(model='gpt-4o', messages=msg)
        answer = resp.choices[0].message.content
        response.extend(["SUCCESS", answer])  # success

    except Exception as e:
        response.extend(["EXCEPTION", "EXCEPTION from getresponse(). " + str(e)])

    return (response)


def IsHeadlineProcessed():
    try:
        ret = {"status":"", "message":""}
        
        routing_data = pd.read_csv(routing_filename)
        hid = st.session_state["hid"]
    
        routing_data = routing_data[routing_data.hid == hid]
        if len(routing_data) > 0:
            ret["status"] = "ERROR"
            ret["message"] = f"Headline ID {hid} already processed"
        else:
            ret["status"] = "SUCCESS"
            ret["message"] = f"Processing Headline ID {hid}"
     
    except Exception as e:
        ret["status"] = "EXCEPTION"
        ret["message"] = str(e)
        
    return (ret)
    

def AnalyzeHeadline():
    hid = st.session_state["hid"]
    headline = st.session_state["headline"]
    
    if headline is None or len(headline) <= 0:
        st.toast("No Headline selected for Analysis !!!",icon="☝")
    else:
        # First check if a headline is already processed
        ret = IsHeadlineProcessed()
        status = ret["status"]
        message = ret["message"]
        
        if status != "SUCCESS": # Already processed; do not process again and Return
            st.toast(message)
            return
        
        with st.spinner("Analyzing Headline to determine Category and prepaing Routing... "):
            editor_data = st.session_state["editor_data"]
            categories = editor_data['category'].tolist()

            sys_prompt = """ You are an expert news classification and relevance analysis assistant. """
            
            user_prompt = f"""
                Analyze the following news headline.

                Your tasks:
                1. Identify the MOST relevant category for the headline from the list of categories below.
                2. Assign a relevancy score from 1 to 5 based on how globally impactful, timely, or socially/economically 
                important the topic is in the current world.

                CATEGORY RULES:
                1. Return ONLY the category name.
                2. Do NOT return explanations, punctuation, numbering, or extra text.
                3. The output must EXACTLY match one category from the list.
                4. If the headline does not clearly belong to any category, return: others
                5. Choose the MOST specific category when multiple categories seem relevant.
                   Example:
                   - AI-related news -> artificial intelligence
                   - Stock market news -> finance & markets
                   - Cyber attacks -> cybersecurity

                RELEVANCY SCORING RULES:
                - 1 = Very low relevance (local gossip, minor events, low impact)
                - 2 = Low relevance (niche or limited audience interest)
                - 3 = Moderate relevance (popular or moderately important topic)
                - 4 = High relevance (major industry, national, or global importance)
                - 5 = Very high relevance (critical global impact, major breakthrough, war, economy, AI, climate, public health, etc.)

                OUTPUT FORMAT: 
                Strictly follow the JSON style with the following keys:
                {'category', 'relevancy' }. 
                Do not include any other extra text or characters

                CATEGORIES: 
                {categories}

                HEADLINE:
                {headline}
                """

            # execute prompt
            response = GetResponse(system_prompt=sys_prompt, user_prompt=user_prompt)
            
            if response[0] == "SUCCESS":
                output = response[1]
                
                if isinstance(output,dict):
                    pass
                else:
                    output = ast.literal_eval(output)

                category = output["category"].strip()
                score = output["relevancy"]

                email = editor_data.email[editor_data.category == category].tolist()[0]
                st.toast(f"Category : {category}\nEmail: {email}\nScore = {score}")
                
                # create the routing data
                cols = ','.join(['hid', 'headline','category','email','score'])
                
                headline = ' '.join(headline.split())
                headline = '"' + headline.strip() + '"'
                
                rec = ','.join([str(hid), headline,category, email, str(score)])
                
                with open(routing_filename,"a+",encoding="utf-8") as fp: # (Assignment 1: Write the contents into a Database)
                    fp.seek(0)
                    data = fp.readlines()
                    if len(data) <= 0:
                        fp.write(cols)

                    fp.seek(0,2)
                    fp.write("\n")
                    fp.write(rec)

def ProcessHeadline():
    
    headline_article_data = pd.read_csv(headline_article)
        
    # based on the selected Headlines, compose an article and display it
    edited_routing_data = st.session_state["edited_routing_data"]
    
    edited_routing_data = edited_routing_data[edited_routing_data["selected"]]
    
    # headline_article_data = st.session_state["headline_article_data"]
    
    if len(edited_routing_data) <= 0:
        st.error("There are no Headlines to process at this time")
        return
    
    hids = edited_routing_data['hid'].tolist()
    headlines = edited_routing_data['headline'].tolist()
    categories = edited_routing_data['category'].tolist()
    
    total = len(hids)
    
    cols = ','.join(['hid','category','headline','article'])
    
    sys_prompt = "You are an excellent writer on any given topic, headline or category"
    
    with st.spinner("Processing Headline IDs to generate the Article ..."):
        time.sleep(1)
        for i in range(total):
            hid = hids[i]
            headline = headlines[i]
            category = categories[i]
            
            df = headline_article_data[headline_article_data["hid"] == hid]
            if len(df) > 0:
                st.toast(f"This headline ID {hid} has already been processed. Skipping ...")
            else:
                user_prompt = f''' Create a well drafted and professionally written article, in about 250 words, based on the 
                                given headline and category.
                                Return only the article. Do not return any other text or characters. The article will be used in a news portal.

                                HEADLINE: 
                                {headline}

                                CATEGORY:
                                {category}

                                ARTICLE:

                                '''
                response = GetResponse(system_prompt=sys_prompt, user_prompt=user_prompt)
                status = response[0]
                if status == "SUCCESS":
                    article = response[1]
                    
                    headline = ' '.join(headline.split())
                    headline = '"' + headline.strip() + '"'
                    article = '"' + article.strip() + '"'

                    rec = ','.join([str(hid),category,headline,article])

                    with open(headline_article,"a+",encoding="utf-8") as fp:
                        fp.seek(0)
                        data = fp.readlines()
                        if len(data) <= 0:
                            fp.write(cols)

                        fp.seek(0,2)
                        fp.write("\n")
                        fp.write(rec)
    
def Initialize():
    selected_tab = st.segmented_control("  ", TABS, key="active_tab")
    
    if selected_tab == TABS[0]:
        st.session_state["headline_text"] = None
        
        homedata = Home()
        
        c1,c2,c3 = st.columns([0.15, 0.02, 0.83])
        c1.image(Image.open(bg_intro))
        c3.subheader("Components of Agentic AI")
        c3.dataframe(homedata,use_container_width=False)
    
    if selected_tab == TABS[1]: # Categorize News
        st.session_state["headline_text"] = None
        
        C1,C2,C3,C4,C5 = st.columns([0.7,0.1,0.05,0.05,0.05])
        C1.subheader("Categorise a news headline and route it for publishing")
        
        btn_showdata = C2.toggle("Show Data") #, help="Show Data")
        btn_analyze = C3.button(":chart_with_upwards_trend:", help="Categorize and Route",on_click=AnalyzeHeadline)
        
        if btn_showdata:
            headline_data = st.session_state["headline_data"]
            
            # data selection
            sel_data = st.dataframe(headline_data,hide_index=True,on_select="rerun",selection_mode="single-row",use_container_width=False)
            sel_row_id = sel_data.selection.rows
            sel_row = headline_data.iloc[sel_row_id]
            
            if len(sel_row ) > 0:
                hid = sel_row['hid'].tolist()[0]
                headline = sel_row['headline'].tolist()[0]
                
                st.session_state["hid"] = hid
                st.session_state["headline"] = headline
        else:
            st.session_state["headline"] = None
        
    if selected_tab == TABS[2]:
        st.session_state["headline_text"] = None

        routing_data = pd.read_csv(routing_filename)
        routing_data["selected"] = routing_data["score"] > 3
        routing_columns = list(routing_data.columns)
        routing_columns.remove("selected")

        C1,C2 = st.columns([0.9,0.1])
        C1.subheader("Headline Routing Details")
        btn_process = C2.button(":game_die:",help="Process Headline", on_click=ProcessHeadline)
        
        # sel_data = st.dataframe(routing_data,hide_index=True,on_select="rerun",selection_mode="single-row",use_container_width=True)
        # sel_row_id = sel_data.selection.rows
        # sel_row = routing_data.iloc[sel_row_id]
        
        edited_routing_data = st.data_editor(routing_data, hide_index=True, use_container_width=True,
                                            column_config={
                                                "selected": st.column_config.CheckboxColumn("Selected", help="Auto checked when score >= 4", default=False) 
                                                },
                                            disabled = routing_columns )

        # hid = edited_routing_data.loc[edited_routing_data["selected"],"hid"].tolist()
        # st.session_state["hid_to_process"] = hid

        st.session_state["edited_routing_data"] = edited_routing_data
        
    if selected_tab == TABS[3]:
        # headline_article_data = st.session_state["headline_article_data"]
        headline_article_data = pd.read_csv(headline_article)
        
        if len(headline_article_data) > 0:
            hids = headline_article_data['hid'].tolist()
        else:
            hids = []
        
        C1,C2 = st.columns([0.15,0.85])
        sel_category = C1.selectbox("HeadLine ID", hids, index=None, key="selected_hid", on_change=GetArticle)

        if st.session_state["headline_text"] is not None:
            st.write(st.session_state["headline_text"])
        # else:
            # st.error("Currently no Articles exist for routed Headlines ")


            
# edited_routing_data = st.session_state["edited_routing_data"]
# if edited_routing_data is not None and len(edited_routing_data) > 0:
# if hids is None or len(hids) <= 0:
# st.error("Currently no Articles exist for routed Headlines ")
# else:
# categories = edited_routing_data["category"][edited_routing_data.hid.isin(hids)].tolist()

def GetArticle():
        sel_hid = st.session_state["selected_hid"]
        
        if sel_hid is not None:
      
            # headline_article_data = st.session_state["headline_article_data"]
            headline_article_data = pd.read_csv(headline_article)
            
            if len(headline_article_data) > 0:
                headline_article_data = headline_article_data[headline_article_data.hid == sel_hid]
                
                category = headline_article_data['category'].tolist()[0]
                headline = headline_article_data['headline'].tolist()[0]
                content = headline_article_data['article'].tolist()[0]
                
                full_text = f"Category: {category} \n\n {headline} \n\n{content}"
                st.session_state["headline_text"] = full_text
            else:
                st.session_state["headline_text"] = None
   
def main():
    Spaces()
    Initialize()