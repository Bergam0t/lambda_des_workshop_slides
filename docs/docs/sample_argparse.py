import simpy
import random
import math
import matplotlib.pyplot as plt
import argparse

# --------------------------
# Parse command-line arguments
# --------------------------
parser = argparse.ArgumentParser(description="Healthcare Waiting List Simulation")
parser.add_argument("--patients", type=int, default=25, help="Average new patients per week (default: 25)")
parser.add_argument("--clinicians", type=int, default=4, help="Number of clinicians (default: 4)")
parser.add_argument("--patients_per_clinician_per_week", type=int, default=5, help="Patients each clinician can see per week (default: 5)")
parser.add_argument("--duration_years", type=int, default=3, help="Simulation duration in years (default: 3)")
parser.add_argument("--initial_waitlist", type=int, default=0, help="Initial waiting list length (default: 0)")

args = parser.parse_args()

# --------------------------
# Assign from arguments
# --------------------------
patients = args.patients
clinicians = args.clinicians
patients_per_clinician_per_week = args.patients_per_clinician_per_week
sim_duration_years = args.duration_years
waiting_list_start_length = args.initial_waitlist

# --------------------------
# Tracking variables
# --------------------------
waiting_times = []
queue_lengths = []
time_points = []
patients_seen = []
all_patients = []

random.seed(42)

# --------------------------
# Simulation functions
# --------------------------
def patient(env, name, nurses, arrival_time):
    service_time = 1 / patients_per_clinician_per_week
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

        patient_record['service_start'] = env.now
        patient_record['wait_time_weeks'] = wait_time
        patient_record['status'] = 'seen'

        patients_seen.append(patient_record.copy())
        yield env.timeout(service_time)

def patient_generator(env, nurses):
    for i in range(waiting_list_start_length):
        env.process(patient(env, f"Initial Patient {i+1}", nurses, 0))

    while True:
        num_arrivals = math.ceil(random.normalvariate(patients, patients * 0.2))
        num_arrivals = max(0, num_arrivals)
        for i in range(num_arrivals):
            env.process(patient(env, f"Week {math.ceil(env.now)} Patient {i+1}", nurses, env.now))
        yield env.timeout(1)

def monitor_queue(env, nurses):
    while True:
        queue_lengths.append(len(nurses.queue))
        time_points.append(env.now)
        yield env.timeout(1)

# --------------------------
# Run simulation
# --------------------------
env = simpy.Environment()
nurses_resource = simpy.Resource(env, capacity=clinicians)
env.process(patient_generator(env, nurses_resource))
env.process(monitor_queue(env, nurses_resource))
env.run(until=sim_duration_years * 52)

# --------------------------
# Plot results
# --------------------------
plt.figure(figsize=(10, 4))
plt.plot(time_points, queue_lengths, linewidth=2, color='#1f77b4')
plt.xlabel('Time (weeks)')
plt.ylabel('Waiting List Length')
plt.title('Waiting List Length Over Time')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# --------------------------
# Print summary
# --------------------------
final_waiting_list = len(nurses_resource.queue)
patients_seen_count = len(patients_seen)
avg_wait = sum(waiting_times) / len(waiting_times) if waiting_times else 0

print("\n--- Simulation Summary ---")
print(f"Final Waiting List: {final_waiting_list}")
print(f"Patients Seen: {patients_seen_count}")
print(f"Average Wait (weeks): {avg_wait:.1f}")
