import streamlit as st
import pandas as pd, numpy as np

h = r"D:\stackroute\2_AI-assisted-programming\learning_requirements\cognizant\2025\1\code\2_AgenticAI\dataset\headline_routing.csv"
h_data = pd.read_csv(h)

# h_data["score"] = np.random.randint(1,6,len(h_data))
h_data["selected"] = h_data["score"] > 3
columns = list(h_data.columns)
columns.remove("selected")


edited_df = st.data_editor(h_data, hide_index=True, use_container_width=True,
                        column_config={
                            "selected": st.column_config.CheckboxColumn("Selected", help="Auto checked when score >= 4", default=False) },
                        disabled = columns
                        )

hid = edited_df.loc[edited_df["selected"],"hid"].tolist()
st.write(hid)
