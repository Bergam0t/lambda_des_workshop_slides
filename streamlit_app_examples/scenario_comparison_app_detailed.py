import micropip

await micropip.install("simpy")
await micropip.install("matplotlib")

import streamlit as st
import simpy
import random
import math
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np

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

st.title("Healthcare Waiting List Simulation - Two Scenario Comparison")

# Shared parameters at the top
st.header("Shared Simulation Parameters")
shared_col1, shared_col2 = st.columns(2)

with shared_col1:
    sim_duration_years = st.number_input(
        "Simulation duration (years)",
        min_value=1,
        max_value=10,
        value=3
    )

with shared_col2:
    num_runs = st.number_input(
        "Number of runs",
        min_value=1,
        max_value=50,
        value=10,
        help="More runs provide better uncertainty estimates but take longer to compute"
    )

st.divider()

# Create two columns for scenarios
col1, col2 = st.columns(2)

# Left column - Scenario 1
with col1:
    st.header("Scenario 1: Current State")

    patients_1 = st.slider(
        "Average new patients per week",
        min_value=5,
        max_value=50,
        value=25,
        key="patients_1",
        help="This sets up a normal distribution with a mean of this value, and a standard deviation of 1/10th of this value."
    )

    waiting_list_start_length_1 = st.number_input(
        "Initial waiting list length",
        min_value=0,
        max_value=5000,
        value=80,
        key="waiting_1"
    )

    input_col_1a, input_col_1b = st.columns([0.4, 0.6])

    clinicians_1 = input_col_1a.number_input(
        "Number of clinicians",
        min_value=1,
        max_value=20,
        value=4,
        key="clinicians_1"
    )

    patients_per_clinician_per_week_1 = input_col_1b.number_input(
        "Patients per clinician per week",
        min_value=1,
        max_value=20,
        value=5,
        key="capacity_1"
    )

# Right column - Scenario 2
with col2:
    st.header("Scenario 2: Proposed Changes")

    patients_2 = st.slider(
        "Average new patients per week",
        min_value=5,
        max_value=50,
        value=25,
        key="patients_2",
        help="This sets up a normal distribution with a mean of this value, and a standard deviation of 1/10th of this value."
    )

    waiting_list_start_length_2 = st.number_input(
        "Initial waiting list length",
        min_value=0,
        max_value=5000,
        value=80,
        key="waiting_2"
    )

    input_col_2a, input_col_2b = st.columns([0.4, 0.6])

    clinicians_2 = input_col_2a.number_input(
        "Number of clinicians",
        min_value=1,
        max_value=20,
        value=6,
        key="clinicians_2"
    )

    patients_per_clinician_per_week_2 = input_col_2b.number_input(
        "Patients per clinician per week",
        min_value=1,
        max_value=20,
        value=5,
        key="capacity_2"
    )

# Run simulation button
st.divider()
run_simulation = st.button("Run Simulation Comparison", type="primary")

if run_simulation:
    def run_single_simulation(seed, patients, waiting_list_start_length, clinicians, patients_per_clinician_per_week):
        """Run a single simulation with given parameters and random seed"""
        # Initialize tracking variables for this run
        waiting_times = []
        queue_lengths = []
        time_points = []
        patients_seen = []
        all_patients = []

        # Set random seed for this run
        random.seed(seed)

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

        # Calculate metrics for this run
        final_waiting_list = len(nurses_resource.queue)
        avg_wait = sum(waiting_times) / len(waiting_times) if waiting_times else 0

        return {
            'queue_lengths': queue_lengths,
            'time_points': time_points,
            'final_waiting_list': final_waiting_list,
            'patients_seen': len(patients_seen),
            'avg_wait': avg_wait,
            'waiting_times': waiting_times,
            'patients_seen_data': patients_seen,
            'all_patients': all_patients
        }

    def run_scenario(scenario_num, patients, waiting_list_start_length, clinicians, patients_per_clinician_per_week):
        """Run all simulations for a given scenario"""
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Store results from all runs
        all_queue_lengths = []
        all_time_points = []
        all_final_metrics = []

        # Run multiple simulations
        for run_idx in range(num_runs):
            status_text.text(f'Running scenario {scenario_num} simulation {run_idx + 1} of {num_runs}...')
            progress_bar.progress((run_idx + 1) / num_runs)

            # Use different seeds for each run
            result = run_single_simulation(42 + run_idx, patients, waiting_list_start_length, clinicians, patients_per_clinician_per_week)

            all_queue_lengths.append(result['queue_lengths'])
            all_time_points.append(result['time_points'])
            all_final_metrics.append({
                'final_waiting_list': result['final_waiting_list'],
                'patients_seen': result['patients_seen'],
                'avg_wait': result['avg_wait']
            })

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Process results for plotting
        # Find the maximum length to align all runs
        max_length = max(len(ql) for ql in all_queue_lengths)

        # Pad shorter runs with their final value
        padded_queue_lengths = []
        for i, queue_lengths in enumerate(all_queue_lengths):
            if len(queue_lengths) < max_length:
                # Pad with the last value
                padded = queue_lengths + [queue_lengths[-1]] * (max_length - len(queue_lengths))
            else:
                padded = queue_lengths[:max_length]
            padded_queue_lengths.append(padded)

        # Convert to numpy array for easier statistics
        queue_array = np.array(padded_queue_lengths)
        time_array = np.arange(max_length)  # Weeks from 0 to max_length-1

        # Calculate statistics
        mean_queue = np.mean(queue_array, axis=0)
        std_queue = np.std(queue_array, axis=0)
        percentile_25 = np.percentile(queue_array, 25, axis=0)
        percentile_75 = np.percentile(queue_array, 75, axis=0)
        min_queue = np.min(queue_array, axis=0)
        max_queue = np.max(queue_array, axis=0)

        # Create the matplotlib graph with confidence bands
        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot individual runs (lightly)
        for i, queue_lengths in enumerate(padded_queue_lengths):
            ax.plot(time_array, queue_lengths, alpha=0.2, color='lightblue', linewidth=0.5)

        # Plot confidence bands
        ax.fill_between(time_array, percentile_25, percentile_75,
                       alpha=0.3, color='#1f77b4', label='25th-75th percentile')
        ax.fill_between(time_array, min_queue, max_queue,
                       alpha=0.1, color='#1f77b4', label='Min-Max range')

        # Plot mean line
        ax.plot(time_array, mean_queue, linewidth=3, color='#1f77b4', label='Mean')

        ax.set_xlabel('Time (weeks)')
        ax.set_ylabel('Waiting List Length')
        ax.set_title(f'Scenario {scenario_num}: Waiting List Length Over Time ({num_runs} simulation runs)')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Calculate summary metrics
        final_waiting_mean = np.mean([m['final_waiting_list'] for m in all_final_metrics])
        final_waiting_std = np.std([m['final_waiting_list'] for m in all_final_metrics])
        patients_seen_mean = np.mean([m['patients_seen'] for m in all_final_metrics])
        patients_seen_std = np.std([m['patients_seen'] for m in all_final_metrics])
        avg_wait_mean = np.mean([m['avg_wait'] for m in all_final_metrics])
        avg_wait_std = np.std([m['avg_wait'] for m in all_final_metrics])

        # Get detailed wait time analysis
        all_seen_metrics = []
        all_waiting_metrics = []

        for run_idx in range(num_runs):
            # Re-run simulation to get detailed patient data
            detailed_result = run_single_simulation(42 + run_idx, patients, waiting_list_start_length, clinicians, patients_per_clinician_per_week)
            patients_seen_data = detailed_result['patients_seen_data']
            all_patients_data = detailed_result['all_patients']

            # Calculate metrics for patients who were seen
            if patients_seen_data:
                df_patients = pd.DataFrame(patients_seen_data)
                seen_over_18 = len(df_patients[df_patients['wait_time_weeks'] > 18])
                seen_over_36 = len(df_patients[df_patients['wait_time_weeks'] > 36])
                seen_over_52 = len(df_patients[df_patients['wait_time_weeks'] > 52])
                total_seen = len(patients_seen_data)

                all_seen_metrics.append({
                    'over_18_count': seen_over_18,
                    'over_36_count': seen_over_36,
                    'over_52_count': seen_over_52,
                    'over_18_pct': (seen_over_18/total_seen*100) if total_seen > 0 else 0,
                    'over_36_pct': (seen_over_36/total_seen*100) if total_seen > 0 else 0,
                    'over_52_pct': (seen_over_52/total_seen*100) if total_seen > 0 else 0,
                    'total_seen': total_seen
                })

            # Calculate metrics for patients still waiting
            patients_still_waiting = [p for p in all_patients_data if p['status'] == 'waiting']
            if patients_still_waiting:
                # Calculate current wait times
                current_wait_times = []
                for patient in patients_still_waiting:
                    current_wait = (sim_duration_years*52) - patient['arrival_time']
                    current_wait_times.append(current_wait)

                waiting_over_18 = sum(1 for wait in current_wait_times if wait > 18)
                waiting_over_36 = sum(1 for wait in current_wait_times if wait > 36)
                waiting_over_52 = sum(1 for wait in current_wait_times if wait > 52)
                total_waiting = len(patients_still_waiting)

                all_waiting_metrics.append({
                    'over_18_count': waiting_over_18,
                    'over_36_count': waiting_over_36,
                    'over_52_count': waiting_over_52,
                    'over_18_pct': (waiting_over_18/total_waiting*100) if total_waiting > 0 else 0,
                    'over_36_pct': (waiting_over_36/total_waiting*100) if total_waiting > 0 else 0,
                    'over_52_pct': (waiting_over_52/total_waiting*100) if total_waiting > 0 else 0,
                    'total_waiting': total_waiting,
                    'avg_wait': np.mean(current_wait_times) if current_wait_times else 0,
                    'max_wait': max(current_wait_times) if current_wait_times else 0
                })

        return {
            'fig': fig,
            'final_waiting_mean': final_waiting_mean,
            'final_waiting_std': final_waiting_std,
            'patients_seen_mean': patients_seen_mean,
            'patients_seen_std': patients_seen_std,
            'avg_wait_mean': avg_wait_mean,
            'avg_wait_std': avg_wait_std,
            'all_seen_metrics': all_seen_metrics,
            'all_waiting_metrics': all_waiting_metrics
        }

    # Run both scenarios
    scenario1_results = run_scenario(1, patients_1, waiting_list_start_length_1, clinicians_1, patients_per_clinician_per_week_1)
    scenario2_results = run_scenario(2, patients_2, waiting_list_start_length_2, clinicians_2, patients_per_clinician_per_week_2)

    # Add a comparison summary at the bottom
    st.divider()
    st.header("Key Differences")

    diff_col1, diff_col2, diff_col3 = st.columns(3)

    with diff_col1:
        final_diff = scenario2_results['final_waiting_mean'] - scenario1_results['final_waiting_mean']
        st.metric(
            label="Final Waiting List Difference",
            value=f"{final_diff:+.0f}",
            delta=f"Scenario 2 vs Scenario 1",
            delta_color="off"
        )

    with diff_col2:
        patients_diff = scenario2_results['patients_seen_mean'] - scenario1_results['patients_seen_mean']
        st.metric(
            label="Patients Seen Difference",
            value=f"{patients_diff:+.0f}",
            delta=f"Scenario 2 vs Scenario 1",
            delta_color="off"
        )

    with diff_col3:
        wait_diff = scenario2_results['avg_wait_mean'] - scenario1_results['avg_wait_mean']
        st.metric(
            label="Average Wait Difference",
            value=f"{wait_diff:+.1f} weeks",
            delta=f"Scenario 2 vs Scenario 1",
            delta_color="off"
        )

    # Display results in two columns
    st.header("Detailed Results")

    result_col1, result_col2 = st.columns(2)

    def display_scenario_results(col, scenario_num, results):
        with col:
            st.subheader(f"Scenario {scenario_num} Results")

            # Show the plot
            st.pyplot(results['fig'])

            # Summary statistics
            st.write("**Summary Statistics**")

            # Metric cards with uncertainty
            metric_col1, metric_col2, metric_col3 = st.columns(3)

            with metric_col1:
                st.metric(
                    label="Final Waiting List",
                    value=f"{results['final_waiting_mean']:.0f}",
                    delta=f"± {results['final_waiting_std']:.0f}",
                    delta_color="off",
                    help=f"Mean ± standard deviation across {num_runs} runs"
                )

            with metric_col2:
                st.metric(
                    label="Patients Seen",
                    value=f"{results['patients_seen_mean']:.0f}",
                    delta=f"± {results['patients_seen_std']:.0f}",
                    delta_color="off",
                    help=f"Mean ± standard deviation across {num_runs} runs"
                )

            with metric_col3:
                st.metric(
                    label="Average Wait (weeks)",
                    value=f"{results['avg_wait_mean']:.1f}",
                    delta=f"± {results['avg_wait_std']:.1f}",
                    delta_color="off",
                    help=f"Mean ± standard deviation across {num_runs} runs"
                )

            # Wait time analysis for patients who were seen
            if results['all_seen_metrics']:
                seen_18_mean = np.mean([m['over_18_count'] for m in results['all_seen_metrics']])
                seen_18_std = np.std([m['over_18_count'] for m in results['all_seen_metrics']])
                seen_36_mean = np.mean([m['over_36_count'] for m in results['all_seen_metrics']])
                seen_36_std = np.std([m['over_36_count'] for m in results['all_seen_metrics']])
                seen_52_mean = np.mean([m['over_52_count'] for m in results['all_seen_metrics']])
                seen_52_std = np.std([m['over_52_count'] for m in results['all_seen_metrics']])

                seen_18_pct_mean = np.mean([m['over_18_pct'] for m in results['all_seen_metrics']])
                seen_36_pct_mean = np.mean([m['over_36_pct'] for m in results['all_seen_metrics']])
                seen_52_pct_mean = np.mean([m['over_52_pct'] for m in results['all_seen_metrics']])

                st.write("**Patients Who Were Seen:**")
                seen_col1, seen_col2, seen_col3 = st.columns(3)

                with seen_col1:
                    st.metric(
                        label="Waited > 18 weeks",
                        value=f"{seen_18_mean:.0f} ± {seen_18_std:.0f}",
                        delta=f"{seen_18_pct_mean:.1f}% avg",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )

                with seen_col2:
                    st.metric(
                        label="Waited > 36 weeks",
                        value=f"{seen_36_mean:.0f} ± {seen_36_std:.0f}",
                        delta=f"{seen_36_pct_mean:.1f}% avg",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )

                with seen_col3:
                    st.metric(
                        label="Waited > 52 weeks",
                        value=f"{seen_52_mean:.0f} ± {seen_52_std:.0f}",
                        delta=f"{seen_52_pct_mean:.1f}% avg",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )

            # Wait time analysis for patients still waiting
            if results['all_waiting_metrics']:
                waiting_18_mean = np.mean([m['over_18_count'] for m in results['all_waiting_metrics']])
                waiting_18_std = np.std([m['over_18_count'] for m in results['all_waiting_metrics']])
                waiting_36_mean = np.mean([m['over_36_count'] for m in results['all_waiting_metrics']])
                waiting_36_std = np.std([m['over_36_count'] for m in results['all_waiting_metrics']])
                waiting_52_mean = np.mean([m['over_52_count'] for m in results['all_waiting_metrics']])
                waiting_52_std = np.std([m['over_52_count'] for m in results['all_waiting_metrics']])

                waiting_18_pct_mean = np.mean([m['over_18_pct'] for m in results['all_waiting_metrics']])
                waiting_36_pct_mean = np.mean([m['over_36_pct'] for m in results['all_waiting_metrics']])
                waiting_52_pct_mean = np.mean([m['over_52_pct'] for m in results['all_waiting_metrics']])

                avg_wait_mean = np.mean([m['avg_wait'] for m in results['all_waiting_metrics']])
                avg_wait_std = np.std([m['avg_wait'] for m in results['all_waiting_metrics']])
                max_wait_mean = np.mean([m['max_wait'] for m in results['all_waiting_metrics']])
                max_wait_std = np.std([m['max_wait'] for m in results['all_waiting_metrics']])

                st.write("**Patients Still Waiting:**")
                waiting_col1, waiting_col2, waiting_col3 = st.columns(3)

                with waiting_col1:
                    st.metric(
                        label="Waiting > 18 weeks",
                        value=f"{waiting_18_mean:.0f} ± {waiting_18_std:.0f}",
                        delta=f"{waiting_18_pct_mean:.1f}% avg",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )

                with waiting_col2:
                    st.metric(
                        label="Waiting > 36 weeks",
                        value=f"{waiting_36_mean:.0f} ± {waiting_36_std:.0f}",
                        delta=f"{waiting_36_pct_mean:.1f}% avg",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )

                with waiting_col3:
                    st.metric(
                        label="Waiting > 52 weeks",
                        value=f"{waiting_52_mean:.0f} ± {waiting_52_std:.0f}",
                        delta=f"{waiting_52_pct_mean:.1f}% avg",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )

                # Additional summary metrics for patients still waiting
                additional_col1, additional_col2 = st.columns(2)
                with additional_col1:
                    st.metric(
                        label="Average Current Wait",
                        value=f"{avg_wait_mean:.1f} ± {avg_wait_std:.1f} weeks",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )
                with additional_col2:
                    st.metric(
                        label="Longest Current Wait",
                        value=f"{max_wait_mean:.1f} ± {max_wait_std:.1f} weeks",
                        help=f"Mean ± std dev across {num_runs} runs",
                        delta_color="off"
                    )

    # Display results for both scenarios
    display_scenario_results(result_col1, 1, scenario1_results)
    display_scenario_results(result_col2, 2, scenario2_results)

else:
    st.info("👆 Configure your simulation parameters for both scenarios and click 'Run Simulation Comparison' to see results")
