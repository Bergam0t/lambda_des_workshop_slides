from vidigi.logging import EventLogger
from vidigi.utils import EventPosition, create_event_position_df
from vidigi.animation import animate_activity_log
import simpy
import numpy as np

class Patient:
    def __init__(self, p_id):
        self.id = p_id

class SimpleActivityModelThreeSequentialActivities:
    def __init__(self, master_seed=42):
        self.env = simpy.Environment()
        self.patient_counter = 0
        self.patient_inter = 4
        self.logger = EventLogger(env=self.env)

        # Seed setup using numpy's SeedSequence
        self.master_seed = master_seed
        self.seed_seq = np.random.SeedSequence(master_seed)
        self.rng = np.random.default_rng(self.seed_seq)

    def generate_arrivals(self):
        while True:
            self.patient_counter += 1

            p = Patient(self.patient_counter)

            self.logger.log_arrival(entity_id=p.id)
            self.env.process(self.patient_journey(p))
            sampled_inter = self.rng.exponential(scale=self.patient_inter)
            yield self.env.timeout(sampled_inter)

    def patient_journey(self, patient):

      self.logger.log_queue(entity_id=patient.id, event="wait_here_receptionist")

      yield self.env.timeout(abs(self.rng.normal(loc=3, scale=1)))

      self.logger.log_queue(entity_id=patient.id, event="wait_here_blood_test")

      yield self.env.timeout(abs(self.rng.normal(loc=14, scale=3)))

      self.logger.log_queue(entity_id=patient.id, event="wait_here_doctor_consult")

      yield self.env.timeout(abs(self.rng.normal(loc=8, scale=2)))

      self.logger.log_departure(entity_id=patient.id)

    def run(self):
        self.env.process(self.generate_arrivals())
        self.env.run(until=180)

model = SimpleActivityModelThreeSequentialActivities()
model.run()
event_log = model.logger.to_dataframe()
# event_log.to_csv("test_log.csv")

animate_activity_log(
  event_log = event_log,
  event_position_df = create_event_position_df([
    EventPosition(event="wait_here_receptionist", x=50 , y=25 , label="Registering<br>with receptionist"),
    EventPosition(event="wait_here_blood_test", x=125 , y=125 , label="Having a<br>blood test"),
    EventPosition(event="wait_here_doctor_consult", x=200 , y=225 , label="Seeing<br>a doctor"),
    EventPosition(event="depart", x=400, y=125, label="Exit")
    ]),
  every_x_time_units=1,
  limit_duration=60,
  override_x_max=300,
  override_y_max=275,
  plotly_height=600,
  plotly_width=1100,
  display_stage_labels=True,
  # time_display_units="%M minutes",
  gap_between_entities=15,
  wrap_queues_at=5,
  entity_icon_size=30,
  simulation_time_unit="minutes",
  debug_write_intermediate_objects=True
).update_layout(
        plot_bgcolor='white',
    )
