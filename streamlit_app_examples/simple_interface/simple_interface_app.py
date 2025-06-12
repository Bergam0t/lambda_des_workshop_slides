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
col1, col2 = st.columns([1, 2])

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
        max_value=200,
        value=80
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

            st.write("**Patients Who Were Seen:**")
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
            ax2.set_title('Distribution of Wait Times - Patients Who Were Seen')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            st.pyplot(fig2)
        else:
            st.warning("No patients were seen during the simulation period.")

        # Analysis for patients still waiting
        st.subheader("Patients Still Waiting")

        # Calculate current wait times for patients still in queue
        patients_still_waiting = [p for p in all_patients if p['status'] == 'waiting']

        if patients_still_waiting:
            # Calculate current wait times
            current_wait_times = []
            for patient in patients_still_waiting:
                current_wait = (sim_duration_years*52) - patient['arrival_time']
                patient['current_wait_weeks'] = current_wait
                current_wait_times.append(current_wait)

            df_waiting = pd.DataFrame(patients_still_waiting)

            # Calculate wait time categories for still waiting patients
            waiting_over_18 = len(df_waiting[df_waiting['current_wait_weeks'] > 18])
            waiting_over_36 = len(df_waiting[df_waiting['current_wait_weeks'] > 36])
            waiting_over_52 = len(df_waiting[df_waiting['current_wait_weeks'] > 52])

            st.write("**Patients Still in Queue:**")
            col4a, col4b, col4c = st.columns(3)

            with col4a:
                st.metric(
                    label="Waiting > 18 weeks",
                    value=waiting_over_18,
                    delta=f"{(waiting_over_18/len(patients_still_waiting)*100):.1f}%"
                )

            with col4b:
                st.metric(
                    label="Waiting > 36 weeks",
                    value=waiting_over_36,
                    delta=f"{(waiting_over_36/len(patients_still_waiting)*100):.1f}%"
                )

            with col4c:
                st.metric(
                    label="Waiting > 52 weeks",
                    value=waiting_over_52,
                    delta=f"{(waiting_over_52/len(patients_still_waiting)*100):.1f}%"
                )

            # Additional metrics for still waiting patients
            avg_current_wait = sum(current_wait_times) / len(current_wait_times)
            max_current_wait = max(current_wait_times)

            col5a, col5b = st.columns(2)
            with col5a:
                st.metric(
                    label="Average Current Wait",
                    value=f"{avg_current_wait:.1f} weeks",
                    help="Average wait time for patients still in queue"
                )
            with col5b:
                st.metric(
                    label="Longest Current Wait",
                    value=f"{max_current_wait:.1f} weeks",
                    help="Longest wait time among patients still in queue"
                )

            # Show distribution histogram for patients still waiting
            fig3, ax3 = plt.subplots(figsize=(10, 3))
            ax3.hist(current_wait_times, bins=20, alpha=0.7, color='#d62728')
            ax3.axvline(x=18, color='red', linestyle='--', alpha=0.7, label='18 weeks')
            ax3.axvline(x=36, color='orange', linestyle='--', alpha=0.7, label='36 weeks')
            ax3.axvline(x=52, color='darkred', linestyle='--', alpha=0.7, label='52 weeks')
            ax3.set_xlabel('Current Wait Time (weeks)')
            ax3.set_ylabel('Number of Patients')
            ax3.set_title('Distribution of Current Wait Times - Patients Still Waiting')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            st.pyplot(fig3)
        else:
            st.success("No patients are currently waiting - all patients have been seen!")

    else:
        st.info("👈 Configure your simulation parameters and click 'Run Simulation' to see results")
