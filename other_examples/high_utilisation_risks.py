import simpy
import numpy as np
import random
import matplotlib.pyplot as plt

class WardSimulation:
    def __init__(self, env, num_beds, arrival_rate, los_mean, max_queue_length=4):
        self.env = env
        self.beds = simpy.Resource(env, capacity=num_beds)
        self.arrival_rate = arrival_rate
        self.los_mean = los_mean
        self.max_queue_length = max_queue_length

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
        # Check if queue is too long (realistic rejection criterion)
        if len(self.beds.queue) >= self.max_queue_length:
            self.rejected_patients += 1
            return

        # Request bed and wait (patients queue rather than being instantly rejected)
        with self.beds.request() as request:
            yield request

            # Patient gets bed, stay for length of stay
            los = random.expovariate(1 / self.los_mean)
            yield self.env.timeout(los)

def run_simulation(num_beds, arrival_rate, los_mean, sim_time_days, max_queue_length=4, seed=None):
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    env = simpy.Environment()
    sim = WardSimulation(env, num_beds, arrival_rate, los_mean, max_queue_length)
    env.run(until=sim_time_days * 24)  # in hours

    rejection_rate = sim.rejected_patients / sim.total_patients if sim.total_patients > 0 else 0
    return rejection_rate

# Parameters
SIM_TIME_DAYS = 365
LOS_MEAN = 3.5  # mean length of stay in days (slightly longer for more variability)
NUM_BEDS = 100
MAX_QUEUE_LENGTH = 4  # Reduced queue capacity for earlier rejections
los_mean_hours = LOS_MEAN * 24
NUM_REPLICATIONS = 30

# Extended range to show the full curve
utilization_levels = np.linspace(0.65, 0.98, 25)
rejection_rates = []

for i, util in enumerate(utilization_levels):
    arrival_rate_per_hour = (NUM_BEDS * util) / los_mean_hours

    reps = [
        run_simulation(
            NUM_BEDS,
            arrival_rate_per_hour,
            los_mean_hours,
            SIM_TIME_DAYS,
            MAX_QUEUE_LENGTH,
            seed=1000 * i + j,
        )
        for j in range(NUM_REPLICATIONS)
    ]

    avg_rejection = np.mean(reps)
    rejection_rates.append(avg_rejection)

# Convert to percentages for plotting
util_percent = [u * 100 for u in utilization_levels]
rejection_percent = [r * 100 for r in rejection_rates]

# Plotting with improved aesthetics
plt.figure(figsize=(12, 7))
plt.plot(util_percent, rejection_percent, marker='o', linewidth=2, markersize=6,
         color='darkblue', markerfacecolor='lightblue', markeredgecolor='darkblue')

plt.xlabel("Average Bed Occupancy (%)", fontsize=12)
plt.ylabel("Patients Turned Away (%)", fontsize=12)
plt.title("Impact of Bed Occupancy on Patient Access\n(Patients turned away when queue exceeds 4 waiting)",
          fontsize=14, pad=20)

# Set reasonable y-axis limits to focus on the meaningful range
plt.ylim(0, max(rejection_percent) * 1.1)

plt.grid(True, alpha=0.3)

# Add reference lines
plt.axvline(70, color='green', linestyle='--', alpha=0.7, label="70% occupancy (safe)")
plt.axvline(80, color='orange', linestyle='--', alpha=0.7, label="80% occupancy (caution)")
plt.axvline(90, color='red', linestyle='--', alpha=0.7, label="90% occupancy (danger)")

plt.legend(loc='upper left')
plt.tight_layout()
plt.show()

# Print some key statistics
print(f"\n--- Key Findings ---")
print(f"Queue limit: {MAX_QUEUE_LENGTH} patients")
print(f"At 70% occupancy: {rejection_percent[np.argmin(np.abs(np.array(util_percent) - 70))]:5.2f}% turned away")
print(f"At 80% occupancy: {rejection_percent[np.argmin(np.abs(np.array(util_percent) - 80))]:5.2f}% turned away")
print(f"At 90% occupancy: {rejection_percent[np.argmin(np.abs(np.array(util_percent) - 90))]:5.2f}% turned away")
print(f"Maximum rejection rate: {max(rejection_percent):.2f}% at {util_percent[np.argmax(rejection_percent)]:.1f}% occupancy")
