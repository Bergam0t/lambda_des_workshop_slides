import streamlit as st
import simpy
import random
import math
import matplotlib.pyplot as plt
import pandas as pd

# Set page config for wide layout
st.set_page_config(layout="wide")

st.title("Healthcare Waiting List Simulation")

# Create two columns
col1, col2, col3 = st.columns([1, 0.25, 2])

# Left column - Options
with col1:
    st.header("Simulation Parameters")

    patients = st.slider(
        "Average new patients per week",
        min_value=5,
        max_value=50,
        value=25
    )

    waiting_list_start_length = st.number_input(
        "Initial waiting list length",
        min_value=0,
        max_value=1000,
        value=140
    )

    st.divider()

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

    st.divider()

    sim_duration_years = st.number_input(
        "Simulation duration (years)",
        min_value=1,
        max_value=10,
        value=3
    )

    run_simulation = st.button("Run Simulation", type="primary")

with col2:
    pass

# Right column - Results
with col3:
    if run_simulation:
        st.warning("Wait times don't include patients who were on the waiting list before the simulation began")

        st.header("Simulation Results")

        # Initialize tracking variables
        waiting_times = []
        queue_lengths = []
        time_points = []
        patients_seen = []

        # Set random seed for reproducibility
        random.seed(42)

        def patient(env, name, nurses, arrival_time):
            """A patient arrives, requests a clinician, is seen, and then leaves."""
            service_time = 1 / patients_per_clinician_per_week

            with nurses.request() as request:
                yield request
                wait_time = env.now - arrival_time
                waiting_times.append(wait_time)
                patients_seen.append({
                    'name': name,
                    'arrival_time': arrival_time,
                    'service_start': env.now,
                    'wait_time_weeks': wait_time
                })
                yield env.timeout(service_time)

        def patient_generator(env, nurses):
            """Generates new patients based on a weekly schedule."""
            # Create initial patients on waiting list
            for i in range(waiting_list_start_length):
                env.process(patient(env, f"Initial Patient {i+1}", nurses, 0))

            # Generate new patients each week
            while True:
                num_arrivals = math.ceil(random.normalvariate(patients, patients*0.1))
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

        with col2c:
            avg_wait = sum(waiting_times) / len(waiting_times) if waiting_times else 0
            st.metric(
                label="Average Wait (weeks)",
                value=f"{avg_wait:.1f}",
                help="Average waiting time for patients who were seen"
            )

        # Wait time breakdown
        st.subheader("Wait Time Analysis")

        if patients_seen:
            # Convert to DataFrame for easier analysis
            df_patients = pd.DataFrame(patients_seen)

            # Calculate wait time categories
            over_18_weeks = len(df_patients[df_patients['wait_time_weeks'] > 18])
            over_36_weeks = len(df_patients[df_patients['wait_time_weeks'] > 36])
            over_52_weeks = len(df_patients[df_patients['wait_time_weeks'] > 52])

            # Display breakdown in columns
            col3a, col3b, col3c = st.columns(3)

            with col3a:
                st.metric(
                    label="Waited > 18 weeks",
                    value=over_18_weeks,
                    delta=f"{(over_18_weeks/len(patients_seen)*100):.1f}%"
                )

            with col3b:
                st.metric(
                    label="Waited > 36 weeks",
                    value=over_36_weeks,
                    delta=f"{(over_36_weeks/len(patients_seen)*100):.1f}%"
                )

            with col3c:
                st.metric(
                    label="Waited > 52 weeks",
                    value=over_52_weeks,
                    delta=f"{(over_52_weeks/len(patients_seen)*100):.1f}%"
                )

            # Optional: Show distribution histogram
            fig2, ax2 = plt.subplots(figsize=(10, 3))
            ax2.hist(df_patients['wait_time_weeks'], bins=20, alpha=0.7, color='#ff7f0e')
            ax2.axvline(x=18, color='red', linestyle='--', alpha=0.7, label='18 weeks')
            ax2.axvline(x=36, color='orange', linestyle='--', alpha=0.7, label='36 weeks')
            ax2.axvline(x=52, color='darkred', linestyle='--', alpha=0.7, label='52 weeks')
            ax2.set_xlabel('Wait Time (weeks)')
            ax2.set_ylabel('Number of Patients')
            ax2.set_title('Distribution of Patient Wait Times')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)
        else:
            st.warning("No patients were seen during the simulation period.")

    else:
        st.info("👈 Configure your simulation parameters and click 'Run Simulation' to see results")
