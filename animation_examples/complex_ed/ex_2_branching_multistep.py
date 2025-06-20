from animation_examples.complex_ed.ex_2_model_classes import Trial, g
from vidigi.animation import animate_activity_log
from vidigi.utils import create_event_position_df, EventPosition
import plotly.io as pio
pio.renderers.default = "notebook"

my_trial = Trial()

my_trial.run_trial()

event_position_df = create_event_position_df([
    EventPosition(event='arrival', x=10, y=250, label="Arrival"),

    # Triage - minor and trauma
    EventPosition(event='triage_wait_begins', x=160, y=375, label="Waiting for<br>Triage"),
    EventPosition(event='triage_begins', x=160, y=315, resource='n_triage', label="Being Triaged"),

    # Minors (non-trauma) pathway
    EventPosition(event='MINORS_registration_wait_begins', x=300, y=145, label="Waiting for<br>Registration"),
    EventPosition(event='MINORS_registration_begins', x=300, y=85, resource='n_reg', label='Being<br>Registered'),

    EventPosition(event='MINORS_examination_wait_begins', x=465, y=145, label="Waiting for<br>Examination"),
    EventPosition(event='MINORS_examination_begins', x=465, y=85, resource='n_exam', label="Being<br>Examined"),

    EventPosition(event='MINORS_treatment_wait_begins', x=630, y=145, label="Waiting for<br>Treatment"),
    EventPosition(event='MINORS_treatment_begins', x=630, y=85, resource='n_cubicles_non_trauma_treat', label="Being<br>Treated"),

    # Trauma pathway
    EventPosition(event='TRAUMA_stabilisation_wait_begins', x=300, y=560, label="Waiting for<br>Stabilisation"),
    EventPosition(event='TRAUMA_stabilisation_begins', x=300, y=490, resource='n_trauma', label="Being<br>Stabilised"),

    EventPosition(event='TRAUMA_treatment_wait_begins', x=630, y=560, label="Waiting for<br>Treatment"),
    EventPosition(event='TRAUMA_treatment_begins', x=630, y=490, resource='n_cubicles_trauma_treat', label="Being<br>Treated"),

    EventPosition(event='depart', x=670, y=330, label="Exit")
])

animate_activity_log(
        event_log=my_trial.all_event_logs[my_trial.all_event_logs['run']==1],
        event_position_df= event_position_df,
        scenario=g(),
        entity_col_name="patient",
        debug_mode=False,
        setup_mode=False,
        every_x_time_units=5,
        include_play_button=True,
        gap_between_entities=11,
        gap_between_resources=15,
        gap_between_resource_rows=30,
        gap_between_queue_rows=30,
        plotly_height=600,
        plotly_width=1000,
        override_x_max=700,
        override_y_max=675,
        entity_icon_size=10,
        resource_icon_size=13,
        text_size=15,
        wrap_queues_at=10,
        step_snapshot_max=20,
        limit_duration=g.sim_duration,
        time_display_units="dhm",
        display_stage_labels=False,
        add_background_image="https://raw.githubusercontent.com/Bergam0t/vidigi/refs/heads/main/examples/example_2_branching_multistep/Full%20Model%20Background%20Image%20-%20Horizontal%20Layout.drawio.png",
    )
