from vidigi.logging import EventLogger
from vidigi.utils import EventPosition, create_event_position_df
from vidigi.animation import animate_activity_log, generate_animation
from vidigi.prep import generate_animation_df, reshape_for_animations
from vidigi.resources import VidigiStore
import simpy
import numpy as np

class g:
    n_cubicles =5

class Patient:
    def __init__(self, p_id):
        self.id = p_id

class SimpleActivityModel:
    def __init__(self, master_seed=42):
        self.env = simpy.Environment()
        self.patient_counter = 0
        self.patient_inter = 2
        self.logger = EventLogger(env=self.env)

        # Seed setup using numpy's SeedSequence
        self.master_seed = master_seed
        self.seed_seq = np.random.SeedSequence(master_seed)
        self.rng = np.random.default_rng(self.seed_seq)

        self.cubicles = VidigiStore(self.env, num_resources=g.n_cubicles)

    def generate_arrivals(self):
        while True:
            self.patient_counter += 1
            p = Patient(self.patient_counter)
            self.logger.log_arrival(entity_id=p.id)
            self.env.process(self.patient_journey(p))
            sampled_inter = self.rng.exponential(scale=self.patient_inter)
            yield self.env.timeout(sampled_inter)

    def patient_journey(self, patient):
      self.logger.log_queue(entity_id=patient.id, event="wait_here")

      with self.cubicles.request() as req:
            cubicle = yield req

            self.logger.log_resource_use_start(
                entity_id=patient.id,
                event="start_treatment",
                resource_id=cubicle.id_attribute
                )

            yield self.env.timeout(self.rng.uniform(low=1, high=10))

            self.logger.log_resource_use_end(
                entity_id=patient.id,
                event="end_treatment",
                resource_id=cubicle.id_attribute
                )

      self.logger.log_departure(entity_id=patient.id)

    def run(self):
        self.env.process(self.generate_arrivals())
        self.env.run(until=180)

model = SimpleActivityModel()
model.run()
event_log = model.logger.to_dataframe()
# event_log.to_csv("test_log.csv")

event_position_df = create_event_position_df([
    EventPosition(event="wait_here", x=150 , y=150 , label="Wait Here!"),
    EventPosition(event="start_treatment", x=150 , y=75 , resource="n_cubicles", label="Be Treated"),
    EventPosition(event="depart", x=150, y=5, label="Exit")
    ])

animate_activity_log(
  event_log = event_log,
  event_position_df = event_position_df,
  scenario=g(),
  every_x_time_units=1,
  limit_duration=60,
  override_x_max=300,
  override_y_max=250,
  plotly_height=600,
  plotly_width=1100,
  display_stage_labels=True,
  gap_between_entities=20,
  entity_icon_size=40,
  wrap_queues_at=10,
  gap_between_resources=30,
  gap_between_queue_rows=30,
  resource_icon_size=80,
  simulation_time_unit="minutes",
  custom_resource_icon="☐",
  resource_opacity=0.7,
  debug_write_intermediate_objects=True
).update_layout(
        plot_bgcolor='white',
    )
