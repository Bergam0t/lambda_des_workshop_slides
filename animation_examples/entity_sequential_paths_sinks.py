from vidigi.logging import EventLogger
from vidigi.utils import EventPosition, create_event_position_df
from vidigi.animation import animate_activity_log
import simpy
import numpy as np

class Patient:
    def __init__(self, p_id):
        self.id = p_id

class SimpleActivityModelSequentialActivitiesSinks:
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

      self.logger.log_queue(entity_id=patient.id, event="wait_here_triage")

      yield self.env.timeout(abs(self.rng.normal(loc=3, scale=1)))

      if self.rng.uniform(low=0.0, high=1.0) < 0.2:
          self.logger.log_queue(entity_id=patient.id, event="died")
          yield self.env.timeout(2)
          self.logger.log_departure(entity_id=patient.id)

      else:
        self.logger.log_queue(entity_id=patient.id, event="wait_here_stabilisation")
        yield self.env.timeout(abs(self.rng.normal(loc=14, scale=3)))

        if self.rng.uniform(low=0.0, high=1.0) < 0.1:
          self.logger.log_queue(entity_id=patient.id, event="died")
          yield self.env.timeout(2)
          self.logger.log_departure(entity_id=patient.id)
        elif self.rng.uniform(low=0.0, high=1.0) < 0.2:
            self.logger.log_queue(entity_id=patient.id, event="transferred")
            yield self.env.timeout(2)
            self.logger.log_departure(entity_id=patient.id)
        elif self.rng.uniform(low=0.0, high=1.0) < 0.5:
            self.logger.log_queue(entity_id=patient.id, event="ward")
            yield self.env.timeout(2)
            self.logger.log_departure(entity_id=patient.id)
        else:
          self.logger.log_queue(entity_id=patient.id, event="wait_here_treatment")
          yield self.env.timeout(abs(self.rng.normal(loc=8, scale=2)))

          if self.rng.uniform(low=0.0, high=1.0) < 0.2:
              self.logger.log_queue(entity_id=patient.id, event="transferred")
              yield self.env.timeout(2)
              self.logger.log_departure(entity_id=patient.id)
          elif self.rng.uniform(low=0.0, high=1.0) < 0.7:
              self.logger.log_queue(entity_id=patient.id, event="ward")
              yield self.env.timeout(2)
              self.logger.log_departure(entity_id=patient.id)
          else:
              self.logger.log_queue(entity_id=patient.id, event="home")
              yield self.env.timeout(2)
              self.logger.log_departure(entity_id=patient.id)

    def run(self):
        self.env.process(self.generate_arrivals())
        self.env.run(until=180)

model = SimpleActivityModelSequentialActivitiesSinks()
model.run()
event_log = model.logger.to_dataframe()
# event_log.to_csv("test_log.csv")

animate_activity_log(
  event_log = event_log,
  event_position_df = create_event_position_df([
    EventPosition(event="wait_here_triage", x=50 , y=225 , label="Arrived<br>in ED"),
    EventPosition(event="wait_here_stabilisation", x=150 , y=225 , label="Being<br>Stabilised"),
    EventPosition(event="wait_here_treatment", x=250 , y=225 , label="Being<br>Treated"),


    EventPosition(event="died", x=40 , y=50 , label="Died"),
    EventPosition(event="transferred", x=100 , y=50 , label="Transferred<br>to other<br>Hospital"),
    EventPosition(event="ward", x=160 , y=50 , label="Admitted<br>to Ward"),
    EventPosition(event="home", x=220 , y=50 , label="Discharged<br>home"),


    EventPosition(event="depart", x=150, y=-30, label="Exit")
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
  debug_write_intermediate_objects=True,
  add_background_image="animation_examples/background_files/sinks.drawio.png"
).update_layout(
        plot_bgcolor='white',
    )
