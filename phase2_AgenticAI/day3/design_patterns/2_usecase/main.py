# -*- coding: utf-8 -*-

import streamlit as st
import time,os, datetime
import loanrisk

st.set_page_config(layout='wide')
now = datetime.datetime.now()
today = now.strftime('%A') + ", " + now.strftime("%B %d, %Y")
st.sidebar.button(today,icon="⏳")

# Sidebar header
st.sidebar.title("Design Patterns")

models = ['Loan Risk Assessment', 'Quit']
parent_model = st.sidebar.selectbox(" ", models,index=None)

if (parent_model == "Loan Risk Assessment"):
    loanrisk.main()
elif parent_model == "Quit":
    st.header("Close Application")
    st.divider()
    st.subheader("Are you sure you want to terminate this session ?")
    st.write("\n")
    c1,c2 = st.columns(2)
    btn_close = c1.button(":red_circle:",help="Close Application")
    # btn_cancel = c2.button(":black_right_pointing_triangle_with_double_vertical_bar:",help="Cancel")
    
    if btn_close:    
        with (st.spinner("Closing application ...")):
            time.sleep(2)
                
            import keyboard,psutil
            
            keyboard.press_and_release('ctrl+w')
            pid = os.getpid()
            p = psutil.Process(pid)
            p.terminate()
    
else:
    pass