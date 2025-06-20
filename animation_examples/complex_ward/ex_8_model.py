import numpy as np
import pandas as pd

from animation_examples.complex_ward.ex_8_model_classes import g, Trial

from vidigi.animation import animate_activity_log

import plotly.io as pio
pio.renderers.default = "notebook"

clinic_simulation = Trial()

event_position_df = pd.DataFrame([
                    # {'event': 'arrival',
                    #  'x':  50, 'y': 800,
                    #  'label': " " },

                    # Triage - minor and trauma
                    {'event': 'bed_wait_begins',
                     'x':  205, 'y': 700,
                     'label': "Waiting for Bed"},

                    {'event': 'stay_begins',
                     'x':  205, 'y': 175,
                     'resource':'number_of_beds',
                     'label': " "},

                    {'event': 'depart',
                     'x':  270, 'y': 70,
                     'label': " "}

                ])

animate_activity_log(
        event_log=clinic_simulation.trial_results[clinic_simulation.trial_results['run_number']==1],
        event_position_df= event_position_df,
        scenario=g(),
        # Key animation prep parameters
        every_x_time_units=6,
        simulation_time_unit="hours",
        limit_duration=60*24*5,
        step_snapshot_max=125,
        # Animation display parameters
        time_display_units="dhm",
        include_play_button=True,
        setup_mode=False,
        debug_mode=False,
        frame_duration=200,
        # Text parameters
        display_stage_labels=True,
        text_size=20,
        # Entity and queue size and spacing
        entity_icon_size=20,
        wrap_queues_at=25,
        gap_between_entities=6,
        gap_between_queue_rows=30,
        # Resource size and spacing
        gap_between_resources=150,
        gap_between_resource_rows=100,
        resource_icon_size=40,
        wrap_resources_at=2,
        custom_resource_icon='🛏️',
        # Plot size
        plotly_height=600,
        plotly_width=1000,
        # Internal plot coordinates
        override_x_max=300,
        override_y_max=900,
        )
