import simpy
import numpy as np
import random
import matplotlib.pyplot as plt


class WardSimulation:
    def __init__(self, env, num_beds, arrival_rate, los_mean):
        self.env = env
        self.beds = simpy.Resource(env, capacity=num_beds)
        self.arrival_rate = arrival_rate
        self.los_mean = los_mean

        # Metrics
        self.total_patients = 0
        self.rejected_patients = 0

        self.env.process(self.patient_generator())

    def patient_generator(self):
        while True:
            yield self.env.timeout(random.expovariate(self.arrival_rate))
            self.total_patients += 1
            self.env.process(self.handle_patient())

    def handle_patient(self):
        request = self.beds.request()
        result = yield request | self.env.timeout(0)  # Try to get bed instantly
        if request not in result:
            self.rejected_patients += 1
        else:
            los = random.expovariate(1 / self.los_mean)
            yield self.env.timeout(los)
            self.beds.release(request)


def run_simulation(num_beds, arrival_rate, los_mean, sim_time_days, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    env = simpy.Environment()
    sim = WardSimulation(env, num_beds, arrival_rate, los_mean)
    env.run(until=sim_time_days * 24)  # in hours
    rejection_rate = sim.rejected_patients / sim.total_patients
    return rejection_rate


# Parameters
SIM_TIME_DAYS = 365
LOS_MEAN = 3.0  # mean length of stay in days
NUM_BEDS = 100
los_mean_hours = LOS_MEAN * 24
NUM_REPLICATIONS = 30

utilization_levels = np.linspace(0.6, 1.05, 20)
rejection_rates = []

for i, util in enumerate(utilization_levels):
    arrival_rate_per_hour = (NUM_BEDS * util) / los_mean_hours
    reps = [
        run_simulation(
            NUM_BEDS,
            arrival_rate_per_hour,
            los_mean_hours,
            SIM_TIME_DAYS,
            seed=1000 * i + j,
        )
        for j in range(NUM_REPLICATIONS)
    ]
    avg_rejection = np.mean(reps)
    rejection_rates.append(avg_rejection)

# Convert to percentages for plotting
util_percent = [u * 100 for u in utilization_levels]
rejection_percent = [r * 100 for r in rejection_rates]

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(util_percent, rejection_percent, marker='o')
plt.xlabel("Average Bed Occupancy (%)")
plt.ylabel("Patients Turned Away (%)")
plt.title("Impact of Bed Occupancy on Patient Access")
plt.grid(True)
plt.axvline(65, color='green', linestyle='--', label="65% occupancy")
plt.axvline(85, color='orange', linestyle='--', label="85% occupancy")
plt.axvline(100, color='red', linestyle='--', label="100% occupancy")
plt.legend()
plt.tight_layout()
plt.show()

# Summary
# print("\n--- Summary ---")
# print("This plot shows the relationship between average bed occupancy and the proportion of patients who")
# print("are turned away due to a lack of available beds. The simulation runs each scenario multiple times to smooth variation.")
# print("At around 70–75% occupancy, very few patients are turned away.")
# print("As occupancy increases beyond 85–90%, the rejection rate rises sharply — reaching over 20% near 100% occupancy.")
# print("This highlights the nonlinear risk of operating wards too close to full capacity.")
