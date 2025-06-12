import streamlit as st
import simpy
import random
import math

waiting_list_start_length = 80

st.title("Run a Simulation!")

clinicians = st.number_input("Choose the number of clinicians", 1, 10, 5)

patients = st.slider("Set the average number of new patients per week", 5, 30, 10)

patients_per_clinician_per_week = st.number_input("How many people can each clinician see per week?", 2, 16, )

SIM_DURATION_WEEKS = 52

random.seed(42)

def patient(env, name, nurses):
    """A patient arrives, requests a clinician, is seen, and then leaves."""

    # The time it takes one nurse to see one patient is the inverse of their weekly capacity
    service_time = 1 / patients_per_clinician_per_week

    # print(f"{name} arrives at the clinic at week {env.now:.2f}") # Uncomment to see details

    # Request a nurse. The 'with' statement handles waiting, acquiring, and releasing.
    with nurses.request() as request:
        yield request

        # print(f"{name} is seen by a nurse at week {env.now:.2f}") # Uncomment to see details
        yield env.timeout(service_time) # Patient is being seen

    # print(f"{name} leaves the clinic at week {env.now:.2f}") # Uncomment to see details


def patient_generator(env, nurses):
    """Generates new patients based on a weekly schedule."""

    # Create the initial 50 patients who are already on the waiting list at the start
    for i in range(waiting_list_start_length):
        env.process(patient(env, f"Initial Patient {i+1}", nurses))

    # This loop runs each week to generate that week's new patients
    while True:
        # Determine how many patients arrive this week using a normal distribution
        num_arrivals = math.ceil(random.normalvariate(patients, patients*0.1))
        num_arrivals = max(0, num_arrivals) # Ensure the number is not negative

        # Create a process for each new patient
        for i in range(num_arrivals):
            env.process(patient(env, f"Weekly Patient (Week {math.ceil(env.now)})", nurses))

        # Wait for the next week to start
        yield env.timeout(1)


# --- Running the Simulation ---
# Set up the simulation environment
env = simpy.Environment()

# Create the nurse resource with a capacity of NUM_NURSES
nurses_resource = simpy.Resource(env, capacity=clinicians)

# Add the patient generator to the environment
env.process(patient_generator(env, nurses_resource))

# Run the simulation
env.run(until=SIM_DURATION_WEEKS)

# --- Final Result ---
# The waiting list is the number of patients in the resource's queue
final_waiting_list = len(nurses_resource.queue)
st.write(f"After {SIM_DURATION_WEEKS}, the waiting list length is {final_waiting_list}")
