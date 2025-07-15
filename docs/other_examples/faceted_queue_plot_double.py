import pandas as pd
import numpy as np
import plotly.express as px
from datetime import time

def generate_queue_data():
    """
    Generates a pandas DataFrame simulating queue data for triage and nurse queues
    over the course of a week.

    The simulation models two daily peaks and low overnight activity.
    """
    # Create a time series for one week at 15-minute intervals
    timestamps = pd.to_datetime(pd.date_range(start='2024-07-01', end='2024-07-08', freq='15min'))

    data = []

    # Define peak hours and their relative intensity
    morning_peak_hour = 12.0
    evening_peak_hour = 19.0

    for ts in timestamps:
        day_of_week = ts.weekday() # Monday=0, Sunday=6
        hour_float = ts.hour + ts.minute / 60.0

        # --- Base low-level oscillation for overnight queues ---
        base_triage_queue = np.random.uniform(1, 5)
        base_nurse_queue = np.random.uniform(0, 4)

        # --- Simulate the daily surges using Gaussian (normal distribution) curves ---
        # This creates a smooth rise and fall around the peak hours.
        # The 'scale' parameter (standard deviation) controls the width of the surge.
        morning_surge = np.exp(-((hour_float - morning_peak_hour)**2) / (2 * 3**2))
        evening_surge = np.exp(-((hour_float - evening_peak_hour)**2) / (2 * 2**2))

        # --- Calculate Triage Queue Length ---
        triage_queue = 0
        # The main queue activity happens between 8 AM and 11 PM
        if time(8, 0) <= ts.time() <= time(23, 0):
            # Scale the surges to create the queue peaks
            triage_queue = (morning_surge * 40) + (evening_surge * 20)

        # Add the base overnight queue and random noise for realism
        triage_queue += base_triage_queue + np.random.uniform(-2, 2)

        # --- Calculate Nurse Queue Length ---
        # The nurse queue follows the triage queue, with a slight delay and different magnitude
        nurse_morning_surge = np.exp(-((hour_float - (morning_peak_hour + 0.5))**2) / (2 * 3.5**2))
        nurse_evening_surge = np.exp(-((hour_float - (evening_peak_hour + 0.75))**2) / (2 * 2.5**2))

        nurse_queue = 0
        if time(8, 30) <= ts.time() <= time(23, 59):
             nurse_queue = (nurse_morning_surge * 45) + (nurse_evening_surge * 22)

        nurse_queue += base_nurse_queue + np.random.uniform(-2, 2)

        # On weekends, the queues are generally smaller
        if day_of_week >= 5: # Saturday or Sunday
            triage_queue *= 0.6
            nurse_queue *= 0.6

        # Append the calculated values, ensuring no negative queue lengths
        data.append({'timestamp': ts, 'queue_name': 'Triage Queue', 'queue_length': max(0, round(triage_queue))})
        data.append({'timestamp': ts, 'queue_name': 'Nurse Queue', 'queue_length': max(0, round(nurse_queue))})

    # Create the final DataFrame
    df = pd.DataFrame(data)
    return df

def plot_faceted_queue_simulation(df):
    """
    Generates and customizes a faceted Plotly line chart from the simulated queue data.
    """
    fig = px.line(df,
                  x='timestamp',
                  y='queue_length',
                  facet_row='queue_name', # This creates the separate plots for each queue
                  color='queue_name',     # Assigns a unique color to each queue
                  labels={
                      "timestamp": "Date and Time",
                      "queue_length": "Patients in Queue",
                      "queue_name": "Queue Type"
                  },
                  title="Simulated Patient Queue Lengths: Triage vs. Nurse")

    # --- Customize the plot's appearance ---
    fig.update_layout(
        height=500,
        width=900,
        showlegend=False,
        title_font_size=20,
        title_x=0.5
    )

    # Set independent y-axes for each facet to best show individual trends
    fig.update_yaxes(matches=None, title_standoff=5)

    # Improve facet labels
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font_size=14))

    return fig

# --- Main execution block ---
# 1. Generate the simulated data
simulated_df = generate_queue_data()

# 2. Create the plot from the data
simulation_plot = plot_faceted_queue_simulation(simulated_df)

# 3. Display the interactive plot
simulation_plot.show()
