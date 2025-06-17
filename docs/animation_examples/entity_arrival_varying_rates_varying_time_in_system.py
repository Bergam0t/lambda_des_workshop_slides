from vidigi.logging import EventLogger
from vidigi.utils import EventPosition, create_event_position_df
from vidigi.animation import animate_activity_log, generate_animation
from vidigi.prep import generate_animation_df, reshape_for_animations
import simpy
import numpy as np

class Patient:
    def __init__(self, p_id):
        self.id = p_id

class SimpleActivityModel:
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
      self.logger.log_queue(entity_id=patient.id, event="wait_here")
      yield self.env.timeout(self.rng.uniform(low=1, high=20))
      self.logger.log_departure(entity_id=patient.id)

    def run(self):
        self.env.process(self.generate_arrivals())
        self.env.run(until=180)

model = SimpleActivityModel()
model.run()
event_log = model.logger.to_dataframe()
# event_log.to_csv("test_log.csv")

event_position_df =    event_position_df = create_event_position_df([
    EventPosition(event="wait_here", x=250 , y=15 , label="Wait Here!"),
    EventPosition(event="depart", x=300, y=5, label="Exit")
    ])

animation_df = generate_animation_df(
    full_entity_df=reshape_for_animations(
    event_log=event_log,
    every_x_time_units=1,
    limit_duration=60,
    step_snapshot_max=100
),
    event_position_df=event_position_df,
    gap_between_entities=20,
    wrap_queues_at=3,
    gap_between_queue_rows=10
)

# def show_priority_icon(row):
#     if "more" not in row["icon"]:
#         if row["category"] == "Ambulance":
#             return "🚑"
#         elif row["category"] == "Walk-in":
#             return "🚶‍➡️"
#         elif row["category"] == "111":
#             return "☎️"
#         else:
#             return row["icon"]
#     else:
#         return row["icon"]

# animation_df = animation_df.assign(
#             icon=animation_df.apply(show_priority_icon, axis=1)
#             )

generate_animation(
    animation_df,
    event_position_df,
    display_stage_labels=False,
    override_x_max=300,
    override_y_max=100,
    plotly_height=600,
    plotly_width=1100
).update_layout(
        plot_bgcolor='white',
    )



# animate_activity_log(
#   event_log = event_log,
#   event_position_df = create_event_position_df([
#     EventPosition(event="wait_here", x=250 , y=15 , label="Wait Here!"),
#     EventPosition(event="depart", x=300, y=5, label="Exit")
#     ]),
#   every_x_time_units=1,
#   limit_duration=60,
#   override_x_max=300,
#   override_y_max=50,
#   plotly_height=600,
#   plotly_width=1100,
#   display_stage_labels=False,
#   # time_display_units="%M minutes",
#   gap_between_entities=20,
#   entity_icon_size=70,
#   wrap_queues_at=10,
#   simulation_time_unit="minutes",
#   debug_write_intermediate_objects=True
# ).update_layout(
#         plot_bgcolor='white',
#     )
