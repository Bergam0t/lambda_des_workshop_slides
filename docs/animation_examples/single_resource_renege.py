from vidigi.logging import EventLogger
from vidigi.utils import EventPosition, create_event_position_df
from vidigi.animation import animate_activity_log, generate_animation
from vidigi.prep import generate_animation_df, reshape_for_animations
from vidigi.resources import VidigiStore
import simpy
import numpy as np

class g:
    n_cubicles = 1
    leaving_reasons = [
        "I've had<br>enough",
        "I can't<br>wait any<br>longer",
        "I'm going<br>to miss<br>my bus",
        "This queue<br>is<br>ridiculous",
        "I'm<br>bored",
        "What a<br>useless<br>service!",
        "My car<br>parking has<br>run out"
    ]

class Patient:
    def __init__(self, p_id, patience):
        self.id = p_id
        self.patience = patience

class SimpleActivityModel:
    def __init__(self, master_seed=42):
        self.env = simpy.Environment()
        self.patient_counter = 0
        self.patient_inter = 3.5
        self.logger = EventLogger(env=self.env)

        # Seed setup using numpy's SeedSequence
        self.master_seed = master_seed
        self.seed_seq = np.random.SeedSequence(master_seed)
        self.rng = np.random.default_rng(self.seed_seq)

        self.cubicles = VidigiStore(self.env, num_resources=g.n_cubicles)

    def generate_arrivals(self):
        while True:
            self.patient_counter += 1
            p = Patient(self.patient_counter, patience=self.rng.uniform(low=5, high=20))
            self.logger.log_arrival(entity_id=p.id)
            self.env.process(self.patient_journey(p))
            sampled_inter = self.rng.exponential(scale=self.patient_inter)
            yield self.env.timeout(sampled_inter)

    def patient_journey(self, patient):
      self.logger.log_queue(entity_id=patient.id, event="wait_here")

      with self.cubicles.request() as req:
            results = yield req | self.env.timeout(patient.patience)
            # print(req)
            # print(results)

            if req in results:

                cubicle = results[req]

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
            else:
                # They decide to leave
                self.logger.log_queue(
                    entity_id=patient.id,
                    event="reneging",
                    leaving_reason=self.rng.choice(g.leaving_reasons, size=1)
                    )
                # We'll keep them on screen for a little while to make it clear what's happening
                yield self.env.timeout(5)
                # Make sure to cancel their request (otherwise they'll leave and it will)
                # never be fulfilled, but they'll block it for everyone else too
                req.cancel()

      self.logger.log_departure(entity_id=patient.id)

    def run(self):
        self.env.process(self.generate_arrivals())
        self.env.run(until=120)

model = SimpleActivityModel()
model.run()
event_log = model.logger.to_dataframe()
# event_log.to_csv("test_log.csv")

event_position_df = create_event_position_df([
    EventPosition(event="wait_here", x=150 , y=100 , label="Wait Here!"),
    EventPosition(event="start_treatment", x=150 , y=25 , resource="n_cubicles", label="Be Treated"),
    EventPosition(event="reneging", x=250 , y=225 , label=" "),
    EventPosition(event="depart", x=250, y=50, label="Exit")
    ])

# animate_activity_log(
#   event_log = event_log,
#   event_position_df = event_position_df,
#   scenario=g(),
#   every_x_time_units=1,
#   limit_duration=180,
#   override_x_max=300,
#   override_y_max=250,
#   plotly_height=600,
#   plotly_width=1100,
#   display_stage_labels=True,
#   gap_between_entities=20,
#   entity_icon_size=40,
#   wrap_queues_at=5,
#   gap_between_resources=30,
#   gap_between_queue_rows=30,
#   resource_icon_size=80,
#   simulation_time_unit="minutes",
#   custom_resource_icon="☐",
#   resource_opacity=0.7,
#   debug_write_intermediate_objects=True
# ).update_layout(
#         plot_bgcolor='white',
#     )


animation_df = generate_animation_df(
    full_entity_df=reshape_for_animations(
    event_log=event_log,
    every_x_time_units=1,
    limit_duration=120,
    step_snapshot_max=100
),
    event_position_df=event_position_df,
    gap_between_entities=30,
    wrap_queues_at=5,
    gap_between_queue_rows=30
)

def show_priority_icon(row):
    if "more" not in row["icon"]:
        if row["event"] == "reneging":
            return f'{row["icon"]}<br>{row["leaving_reason"][0]}'
        else:
            return row["icon"]
    else:
        return row["icon"]

animation_df = animation_df.assign(
            icon=animation_df.apply(show_priority_icon, axis=1)
            )

generate_animation(
    animation_df,
    event_position_df,
    scenario=g(),
    entity_icon_size=20,
    override_x_max=300,
    override_y_max=300,
    plotly_height=600,
    plotly_width=1100,
    custom_resource_icon="☐",
    resource_icon_size=80,
).update_layout(
        plot_bgcolor='white',
    )
