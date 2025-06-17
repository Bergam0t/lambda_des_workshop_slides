import micropip

await micropip.install("simpy")
await micropip.install("matplotlib")

import streamlit as st
import simpy
import random
import math
from matplotlib import pyplot as plt
import pandas as pd

# Set page config for wide layout
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stMetricDelta"] svg {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Healthcare Waiting List Simulation")

# Create two columns
col1, col2 = st.columns([1, 2])

# Left column - Options
with col1:
    st.header("Community Pathway Clinic")

    patients = st.slider(
        "Average new patients per week",
        min_value=5,
        max_value=50,
        value=25,
        help="This sets up a normal distribution with a mean of this value, and a standard deviation of 1/10th of this value."
    )

    waiting_list_start_length = 0

    clinicians = st.number_input(
        "Number of clinicians",
        min_value=1,
        max_value=20,
        value=4
    )

    patients_per_clinician_per_week = st.number_input(
        "Patients per clinician per week",
        min_value=1,
        max_value=20,
        value=5
    )

    sim_duration_years = 3

    run_simulation = st.button("Run Simulation", type="primary")

# Right column - Results
with col2:
    if run_simulation:
        st.header("Simulation Results")

        # Initialize tracking variables
        waiting_times = []
        queue_lengths = []
        time_points = []
        patients_seen = []
        all_patients = []  # Track all patients including those still waiting

        # Set random seed for reproducibility
        random.seed(42)

        def patient(env, name, nurses, arrival_time):
            """A patient arrives, requests a clinician, is seen, and then leaves."""
            service_time = 1 / patients_per_clinician_per_week

            # Record patient in all_patients when they arrive
            patient_record = {
                'name': name,
                'arrival_time': arrival_time,
                'service_start': None,
                'wait_time_weeks': None,
                'status': 'waiting'
            }
            all_patients.append(patient_record)

            with nurses.request() as request:
                yield request
                wait_time = env.now - arrival_time
                waiting_times.append(wait_time)

                # Update patient record when seen
                patient_record['service_start'] = env.now
                patient_record['wait_time_weeks'] = wait_time
                patient_record['status'] = 'seen'

                patients_seen.append(patient_record.copy())
                yield env.timeout(service_time)

        def patient_generator(env, nurses):
            """Generates new patients based on a weekly schedule."""
            # Create initial patients on waiting list
            for i in range(waiting_list_start_length):
                env.process(patient(env, f"Initial Patient {i+1}", nurses, 0))

            # Generate new patients each week
            while True:
                num_arrivals = math.ceil(random.normalvariate(patients, patients*0.2))
                num_arrivals = max(0, num_arrivals)

                for i in range(num_arrivals):
                    env.process(patient(env, f"Week {math.ceil(env.now)} Patient {i+1}",
                                      nurses, env.now))

                yield env.timeout(1)

        def monitor_queue(env, nurses):
            """Monitor queue length over time."""
            while True:
                queue_lengths.append(len(nurses.queue))
                time_points.append(env.now)
                yield env.timeout(1)  # Check every week

        # Run simulation
        env = simpy.Environment()
        nurses_resource = simpy.Resource(env, capacity=clinicians)

        # Start processes
        env.process(patient_generator(env, nurses_resource))
        env.process(monitor_queue(env, nurses_resource))

        # Run simulation
        env.run(until=sim_duration_years*52)

        # Create the matplotlib graph
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(time_points, queue_lengths, linewidth=2, color='#1f77b4')
        ax.set_xlabel('Time (weeks)')
        ax.set_ylabel('Waiting List Length')
        ax.set_title('Waiting List Length Over Time')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

        # Metric cards
        final_waiting_list = len(nurses_resource.queue)
        col2a, col2b, col2c = st.columns(3)

        with col2a:
            st.metric(
                label="Final Waiting List",
                value=final_waiting_list,
                help="Number of patients still waiting after simulation"
            )

        with col2b:
            st.metric(
                label="Patients Seen",
                value=len(patients_seen),
                help="Total number of patients who received treatment"
            )

    else:
        st.info("👈 Configure your simulation parameters and click 'Run Simulation' to see results")
