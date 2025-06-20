import pandas as pd
import math
from animation_examples.complex_community_booking.model_classes import Scenario, generate_seed_vector
from animation_examples.complex_community_booking.simulation_execution_functions import single_run
from vidigi.prep import reshape_for_animations, generate_animation_df
from vidigi.animation import generate_animation
import plotly.io as pio
pio.renderers.default = "notebook"

shifts = pd.read_csv("animation_examples/complex_community_booking/data/shifts.csv")
# if scenario_choice == "As-is" or scenario_choice == "With Pooling":
# prop_carve_out = [0.0, 0.9, 0.15, 0.01]
prop_carve_out = 0.15

#depending on settings and CPU this model takes around 15-20 seconds to run
RESULTS_COLLECTION = 90 * 1

# We use a warm-up period
# because the model starts up empty which doesn't reflect reality
WARM_UP = 60 * 1
RUN_LENGTH = RESULTS_COLLECTION + WARM_UP

# Set up the scenario for the model to run.
scenarios = {}

scenarios['as-is'] = Scenario(
    RUN_LENGTH,
    WARM_UP,
    prop_carve_out=prop_carve_out,
    seeds=generate_seed_vector(),
    slots_file=shifts
    )

scenarios['pooled'] = Scenario(
    RUN_LENGTH,
    WARM_UP,
    prop_carve_out=prop_carve_out,
    pooling=True,
    seeds=generate_seed_vector(),
    slots_file=shifts
    )

scenarios['no_carve_out'] = Scenario(
    RUN_LENGTH,
    WARM_UP,
    pooling=True,
    prop_carve_out=0.0,
    seeds=generate_seed_vector(),
    slots_file=shifts
    )

clinic_lkup_df = pd.DataFrame([
    {'clinic': 0, 'icon': "🟠"},
    {'clinic': 1, 'icon': "🟡"},
    {'clinic': 2, 'icon': "🟢"},
    {'clinic': 3, 'icon': "🔵"},
    {'clinic': 4, 'icon': "🟣"},
    {'clinic': 5, 'icon': "🟤"},
    {'clinic': 6, 'icon': "⚫"},
    {'clinic': 7, 'icon': "⚪"},
    {'clinic': 8, 'icon': "🔶"},
    {'clinic': 9, 'icon': "🔷"},
    {'clinic': 10, 'icon': "🟩"}
])


def show_home_clinic(row):
        if "more" not in row["icon"]:
            if row["home_clinic"] == 0:
                return "🟠"
            if row["home_clinic"] == 1:
                return "🟡"
            if row["home_clinic"] == 2:
                return "🟢"
            if row["home_clinic"] == 3:
                return "🔵"
            if row["home_clinic"] == 4:
                return "🟣"
            if row["home_clinic"] == 5:
                return "🟤"
            if row["home_clinic"] == 6:
                return "⚫"
            if row["home_clinic"] == 7:
                return "⚪"
            if row["home_clinic"] == 8:
                return "🔶"
            if row["home_clinic"] == 9:
                return "🔷"
            if row["home_clinic"] == 10:
                return "🟩"
            else:
                return row["icon"]
        else:
            return row["icon"]

def show_priority_icon(row):
    if "more" not in row["icon"]:
        if row["pathway"] == 2:
            return "🚨"
        else:
            return row["icon"]
    else:
        return row["icon"]

def add_los_to_icon(row):
    if row["event_original"] == "have_appointment":
        return f'{row["icon"]}<br>{int(row["wait"])}'
    else:
        return row["icon"]

def generate_scenario_results(scenario):
    results_all, results_low, results_high, event_log = single_run(scenarios[scenario])
    event_log_df = pd.DataFrame(event_log)
    event_log_df['event_original'] = event_log_df['event']
    event_log_df['event'] = event_log_df.apply(lambda x: f"{x['event']}{f'_{int(x.booked_clinic)}' if pd.notna(x['booked_clinic']) else ''}", axis=1)

    full_patient_df = reshape_for_animations(
        event_log_df,
        entity_col_name="patient",
        limit_duration=WARM_UP+180,
        every_x_time_units=1,
        step_snapshot_max=50,
        )

    # Remove the warm-up period from the event log
    full_patient_df = full_patient_df[full_patient_df["snapshot_time"] >= WARM_UP]

    clinics =  [x for x in event_log_df['booked_clinic'].sort_values().unique().tolist() if not math.isnan(x)]

    clinic_waits = [{'event': f'appointment_booked_waiting_{int(clinic)}',
        'y':  950-(clinic+1)*80,
        'x': 625,
        'label': f"Booked into<br>clinic {int(clinic)}",
        'clinic': int(clinic)}
        for clinic in clinics]

    clinic_attends = [{'event': f'have_appointment_{int(clinic)}',
        'y':  950-(clinic+1)*80,
        'x': 850,
        'label': f"Attending appointment<br>at clinic {int(clinic)}"}
        for clinic in clinics]

    event_position_df = pd.concat([pd.DataFrame(clinic_waits),(pd.DataFrame(clinic_attends))])

    referred_out = [{'event': f'referred_out_{int(clinic)}',
        'y':  950-(clinic+1)*80,
        'x': 125,
        'label': f"Referred Out From <br>clinic {int(clinic)}"}
        for clinic in clinics]

    event_position_df = pd.concat([event_position_df,(pd.DataFrame(referred_out))])

    # if scenario == "pooled" or "no_carve_out":
    #     event_position_df = event_position_df.merge(clinic_lkup_df, how="left")
    #     event_position_df["label"] = event_position_df.apply(
    #         lambda x: f"{x['label']} {x['icon']}" if pd.notna(x['icon']) else x['label'],
    #         axis=1
    #         )
    #     event_position_df = event_position_df.drop(columns="icon")

    event_position_df.drop(columns="clinic")

    full_patient_df_plus_pos = generate_animation_df(
                    full_entity_df=full_patient_df,
                    entity_col_name="patient",
                    event_position_df=event_position_df,
                    wrap_queues_at=25,
                    step_snapshot_max=50,
                    gap_between_entities=15,
                    gap_between_queue_rows=15,
                    debug_mode=False
            )

    return full_patient_df, full_patient_df_plus_pos, event_position_df


full_patient_df, full_patient_df_plus_pos, event_position_df = generate_scenario_results(
    'as-is'
    )

def generate_clinic_animation(final_df):
    fig = generate_animation(
        full_entity_df_plus_pos=final_df,
        event_position_df=event_position_df,
        scenario=None,
        entity_col_name="patient",
        plotly_height=800,
        plotly_width=1000,
        override_x_max=1000,
        override_y_max=1000,
        entity_icon_size=10,
        text_size=10,
        include_play_button=True,
        add_background_image=None,
        display_stage_labels=True,
        time_display_units="d",
        simulation_time_unit="days",
        start_date="2022-06-27",
        setup_mode=False,
        frame_duration=1500, #milliseconds
        frame_transition_duration=1000, #milliseconds
        debug_mode=False
    )

    return fig

    #TODO
    # Add in additional trace that shows the number of available slots per day
    # using the slot df

    #TODO
    # Pooled booking version where being in non-home clinic makes you one colour
    # and home clinic makes you another

    #TODO
    # Investigate adding a priority attribute to event log
    # that can be considered when ranking queues if present

generate_clinic_animation(full_patient_df_plus_pos)
