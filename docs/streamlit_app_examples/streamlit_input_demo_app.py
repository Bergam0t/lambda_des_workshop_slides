import streamlit as st
import numpy as np
import pandas as pd

col1, col2 = st.columns(2)

with col1:

  st.slider("Choose the average number of patients", 5, 50, value=25)

  st.slider("Choose the maximumum and minimum number of weekly patients",
            value=[10, 20],
            min_value=1,
            max_value=100)

  st.number_input("Enter the number of years the simulation should run for",
                    min_value = 1, max_value = 10, value = 3)

with col2:
  st.date_input("Choose a simulation start date")

  st.time_input("Choose a simulation start time", "08:00:00")

  st.multiselect(
    "Choose the patient types to include",
    ["High severity", "Medium severity", "Low severity"]
    )

st.divider()

clinic = st.selectbox(
  "Choose a clinic to model",
  ["Elm Clinic", "Pine Clinic"]
  )

if clinic == "Pine Clinic":
  df = pd.DataFrame([
    {"Staff Member": "Marty McFly", "Monday": 3, "Tuesday": 2, "Wednesday": 0, "Thursday": 3, "Friday": 1},
    {"Staff Member": "Dr Emmett Brown", "Monday": 1, "Tuesday": 0, "Wednesday": 3, "Thursday": 3, "Friday": 2},
    {"Staff Member": "Biff Tannen", "Monday": 3, "Tuesday": 1, "Wednesday": 3, "Thursday": 3, "Friday": 2}
  ])
else:
  df = pd.DataFrame([
    {"Staff Member": "Gary Oak", "Monday": 0, "Tuesday": 2, "Wednesday": 0, "Thursday": 3, "Friday": 0},
    {"Staff Member": "Ash Ketchum", "Monday": 0, "Tuesday": 0, "Wednesday": 3, "Thursday": 3, "Friday": 1},
    {"Staff Member": "Brock Harrison", "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 2}
  ])

st.data_editor(df.set_index("Staff Member"))
