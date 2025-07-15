import simpy
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


class WardSimulation:
    def __init__(self, env, num_beds, arrival_rate, los_mean):
        self.env = env
        self.beds = simpy.Resource(env, capacity=num_beds)
        self.arrival_rate = arrival_rate
        self.los_mean = los_mean

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
        result = yield request | self.env.timeout(0)
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
    env.run(until=sim_time_days * 24)
    rejection_rate = sim.rejected_patients / sim.total_patients
    return rejection_rate, sim.total_patients


# --- Parameters ---
SIM_TIME_DAYS = 365
LOS_MEAN_DAYS = 3.0
LOS_MEAN_HOURS = LOS_MEAN_DAYS * 24
ARRIVAL_RATE_PER_DAY = 30
ARRIVAL_RATE_PER_HOUR = ARRIVAL_RATE_PER_DAY / 24
NUM_REPLICATIONS = 10

# Cost assumptions
WARD_COST_PER_BED_PER_DAY = 400  # fixed cost per bed per day
OUT_OF_AREA_COST_PER_PATIENT = 3000  # marginal cost per rejection

# Define occupancy levels to simulate (from 50% to 100%)
occupancy_targets = np.linspace(0.5, 1.0, 20)
occupancies = []
total_costs = []
rejection_percents = []
bed_counts = []

for i, target_occ in enumerate(occupancy_targets):
    # Calculate required beds to achieve target occupancy
    required_beds = int(np.ceil((ARRIVAL_RATE_PER_HOUR * LOS_MEAN_HOURS) / target_occ))
    bed_counts.append(required_beds)

    rejections = []
    totals = []
    for j in range(NUM_REPLICATIONS):
        rejection_rate, total_patients = run_simulation(
            required_beds,
            ARRIVAL_RATE_PER_HOUR,
            LOS_MEAN_HOURS,
            SIM_TIME_DAYS,
            seed=1000 * i + j
        )
        rejections.append(rejection_rate)
        totals.append(total_patients)

    avg_rejection_rate = np.mean(rejections)
    avg_total_patients = np.mean(totals)

    occupancy_percent = target_occ * 100
    rejections_abs = avg_rejection_rate * avg_total_patients

    # Cost calculations
    fixed_cost = WARD_COST_PER_BED_PER_DAY * required_beds * SIM_TIME_DAYS
    out_of_area_cost = OUT_OF_AREA_COST_PER_PATIENT * rejections_abs
    total_cost = fixed_cost + out_of_area_cost

    occupancies.append(occupancy_percent)
    rejection_percents.append(avg_rejection_rate * 100)
    total_costs.append(total_cost)



# --- Plot 1: Occupancy vs Rejection ---
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(occupancies, rejection_percents, marker='o')
plt.xlabel("Average Occupancy (%)")
plt.ylabel("Patients Turned Away (%)")
plt.title("Occupancy vs Turned-Away Rate")
plt.grid(True)

# --- Plot 2: Occupancy vs Total Cost ---
plt.subplot(1, 2, 2)
plt.plot(occupancies, np.array(total_costs) / 1e6, marker='o', color='darkred')
plt.xlabel("Average Occupancy (%)")
plt.ylabel("Total Annual Cost (£ millions)")
plt.title("Occupancy vs Total Cost")
plt.grid(True)
plt.gca().yaxis.set_major_formatter(mtick.FormatStrFormatter('£%.1fM'))

plt.tight_layout()
plt.show()

# --- Text Summary ---
min_cost_idx = int(np.argmin(total_costs))
optimal_beds = bed_counts[min_cost_idx]
optimal_occupancy = occupancies[min_cost_idx]
optimal_cost = total_costs[min_cost_idx]

# print("\n--- Summary ---")
# print(f"The simulation suggests that the **lowest total cost** is achieved at around {optimal_occupancy:.1f}% occupancy,")
# print(f"which corresponds to running the ward with approximately {optimal_beds} beds.")
# print(f"This balances the cost of underused capacity against the high cost of sending patients to out-of-area care.")
# print(f"The model restricts occupancy to 100% or below to reflect realistic operational planning.")
