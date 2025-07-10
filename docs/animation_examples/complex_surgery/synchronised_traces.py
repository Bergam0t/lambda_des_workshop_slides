import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from animation_examples.complex_surgery.simulation_execution_functions import multiple_replications
from animation_examples.complex_surgery.model_classes import Scenario, Schedule
from vidigi.prep import reshape_for_animations, generate_animation_df
from vidigi.animation import generate_animation
from plotly.subplots import make_subplots

import plotly.io as pio
pio.renderers.default = "notebook"

TRACE = False

def trace(msg, show=TRACE):
    '''
    Utility function for printing a trace as the
    simulation model executes.
    Set the TRACE constant to False, to turn tracing off.

    Params:
    -------
    msg: str
        string to print to screen.
    '''
    if show:
        print(msg)


debug_mode=False

schedule = Schedule()

(pd.DataFrame.from_dict(schedule.sessions_per_weekday, orient="index")
        .rename(columns={0: "Sessions"}).merge(

        pd.DataFrame.from_dict(schedule.theatres_per_weekday, orient="index")
            .rename(columns={0: "Theatre Capacity"}),
            left_index=True, right_index=True

        ).merge(

        pd.DataFrame.from_dict(schedule.allocation, orient="index"),
        left_index=True, right_index=True

        ))

n_beds = 35

primary_hip_los = 4.4

primary_knee_los = 4.7

revision_hip_los = 6.9

revision_knee_los = 7.2

unicompart_knee_los = 2.9

los_delay = 16.5
los_delay_sd = 15.2

prop_delay = 0.076

replications = 30
runtime = 60
warmup=7

args = Scenario(schedule=schedule,
                primary_hip_mean_los=primary_hip_los,
                primary_knee_mean_los=primary_knee_los,
                revision_hip_mean_los=revision_hip_los,
                revision_knee_mean_los=revision_knee_los,
                unicompart_knee_mean_los=unicompart_knee_los,
                prob_ward_delay=prop_delay,
                n_beds=n_beds,
                delay_post_los_mean=los_delay,
                delay_post_los_sd=los_delay_sd
                )


results = multiple_replications(
                return_detailed_logs=True,
                scenario=args,
                n_reps=replications,
                results_collection=runtime
            )




# Join the event log with a list of patients to add a column that will determine
# the icon set used for a patient (in this case, we want to distinguish between the
# knee/hip patients)
event_log = results[4]
event_log = event_log[event_log['rep'] == 1].copy()
event_log['patient'] = event_log['patient'].astype('str') + event_log['pathway']

primary_patients = results[2]
primary_patients = primary_patients[primary_patients['rep'] == 1]
primary_patients['patient class'] = primary_patients['patient class'].str.title()
primary_patients['ID'] = primary_patients['ID'].astype('str') + primary_patients['patient class']

revision_patients = results[3]
revision_patients = revision_patients[revision_patients['rep'] == 1]
revision_patients['patient class'] = revision_patients['patient class'].str.title()
revision_patients['ID'] = revision_patients['ID'].astype('str') + revision_patients['patient class']

full_log_with_patient_details = event_log.merge(pd.concat([primary_patients, revision_patients]),
                                                    how="left",
                                                left_on=["patient", "pathway"],
                                                right_on=["ID", "patient class"]).reset_index(drop=True).drop(columns="ID")

pid_table = full_log_with_patient_details[['patient']].drop_duplicates().reset_index(drop=True).reset_index(drop=False).rename(columns={'index': 'pid'})

full_log_with_patient_details = full_log_with_patient_details.merge(pid_table, how='left', on='patient').drop(columns='patient').rename(columns={'pid':'patient'})


event_position_df = pd.DataFrame([
            # {'event': 'arrival', 'x':  10, 'y': 250, 'label': "Arrival" },

            # Triage - minor and trauma
            {'event': 'enter_queue_for_bed',
                'x':  300, 'y': 600, 'label': "Waiting for<br>Availability of<br>Bed to be Confirmed<br>Before Surgery" },

            {'event': 'no_bed_available',
                'x':  800, 'y': 600, 'label': "No Bed<br>Available:<br>Surgery Cancelled" },

            {'event': 'post_surgery_stay_begins',
                'x':  850, 'y': 220, 'resource':'n_beds', 'label': "In Bed:<br>Recovering from<br>Surgery" },

            {'event': 'discharged_after_stay',
                'x':  770, 'y': 50, 'label': "Discharged from Hospital<br>After Recovery"}
            # {'event': 'exit',
            #  'x':  670, 'y': 100, 'label': "Exit"}

            ])

full_patient_df = reshape_for_animations(full_log_with_patient_details,
                                         entity_col_name="patient",
                                            every_x_time_units=1,
                                            limit_duration=runtime,
                                            step_snapshot_max=50,
                                            debug_mode=debug_mode
                                            )

if debug_mode:
    print(f'Reshaped animation dataframe finished construction at {time.strftime("%H:%M:%S", time.localtime())}')

full_patient_df_plus_pos = generate_animation_df(
                            full_entity_df=full_patient_df,
                            entity_col_name="patient",
                            event_position_df=event_position_df,
                            wrap_queues_at=20,
                            wrap_resources_at=40,
                            step_snapshot_max=50,
                            gap_between_entities=20,
                            gap_between_resources=20,
                            gap_between_queue_rows=175,
                            gap_between_resource_rows=175,
                            debug_mode=debug_mode
                    )

def set_icon(row):
    if row["surgery type"] == "p_knee":
        return "🦵<br>1️⃣<br> "
    elif row["surgery type"] == "r_knee":
        return "🦵<br>♻️<br> "
    elif row["surgery type"] == "p_hip":
        return "🕺<br>1️⃣<br> "
    elif row["surgery type"] == "r_hip":
        return "🕺<br>♻️<br> "
    elif row["surgery type"] == "uni_knee":
        return "🦵<br>✳️<br> "
    else:
        return f"CHECK<br>{row['icon']}"

full_patient_df_plus_pos = full_patient_df_plus_pos.assign(icon=full_patient_df_plus_pos.apply(set_icon, axis=1))

# TODO: Check why this doesn't seem to be working quite right for the 'discharged after stay'
# step. e.g. 194Primary is discharged on 28th July showing a LOS of 1 but prior to this shows a LOS of 9.
def add_los_to_icon(row):
    if row["event"] == "post_surgery_stay_begins":
        return f'{row["icon"]}<br><br>{row["snapshot_time"]-row["time"]:.0f}'
    elif row["event"] == "discharged_after_stay":
        return f'{row["icon"]}<br>{row["los"]:.0f}'
    else:
        return row["icon"]

full_patient_df_plus_pos = full_patient_df_plus_pos.assign(icon=full_patient_df_plus_pos.apply(add_los_to_icon, axis=1))


def indicate_delay_via_icon(row):
    if row["delayed discharge"] is True:
        return f'{row["icon"]}<br>*'
    else:
        return f'{row["icon"]}<br> '

full_patient_df_plus_pos = full_patient_df_plus_pos.assign(icon=full_patient_df_plus_pos.apply(indicate_delay_via_icon, axis=1))

cancelled_due_to_no_bed_available = len(full_log_with_patient_details[full_log_with_patient_details['event'] == "no_bed_available"]["patient"].unique())
total_patients = len(full_log_with_patient_details["patient"].unique())

cancelled_perc = cancelled_due_to_no_bed_available/total_patients

# st.markdown(f"Surgeries cancelled due to no bed being available in time: {cancelled_perc:.2%} ({cancelled_due_to_no_bed_available} of {total_patients})")

# st.markdown(
#     """
#     **Key**:

#     🦵1️⃣: Primary Knee

#     🦵♻️: Revision Knee

#     🕺1️⃣: Primary Hip

#     🕺♻️: Revision Hip

#     🦵✳️: Primary Unicompartment Knee

#     An asterisk (*) indicates that the patient has a delayed discharge from the ward.

#     The numbers below patients indicate their length of stay.

#     Note that the "No Bed Available: Surgery Cancelled" and "Discharged from Hospital after Recovery" stages in the animation are lagged by one day.
#     For example, on the 2nd of July, this will show the patients who had their surgery cancelled on 1st July or were discharged on 1st July.
#     These steps are included to make it easier to understand the destinations of different clients, but due to the size of the simulation step shown (1 day) it is difficult to demonstrate this differently.
#     """
# )

counts_not_avail = full_patient_df_plus_pos[full_patient_df_plus_pos['event']=='no_bed_available'][['snapshot_time','patient']].groupby('snapshot_time').agg('count')
counts_not_avail = counts_not_avail.reset_index().merge(full_patient_df_plus_pos[['snapshot_time']].drop_duplicates(), how='right').sort_values('snapshot_time')
counts_not_avail['patient'] = counts_not_avail['patient'].fillna(0)
counts_not_avail['running_total'] = counts_not_avail['patient'].cumsum()

counts_not_avail = counts_not_avail.reset_index(drop=True)


counts_ops_completed = full_patient_df_plus_pos[full_patient_df_plus_pos['event']=='post_surgery_stay_begins'][['snapshot_time','patient']].drop_duplicates('patient').groupby('snapshot_time').agg('count')
counts_ops_completed = counts_ops_completed.reset_index().merge(full_patient_df_plus_pos[['snapshot_time']].drop_duplicates(), how='right').sort_values('snapshot_time')
counts_ops_completed['patient'] = counts_ops_completed['patient'].fillna(0)
counts_ops_completed['running_total'] = counts_ops_completed['patient'].cumsum()

counts_ops_completed = counts_ops_completed.reset_index(drop=True)

counts_not_avail = counts_not_avail.merge(counts_ops_completed.rename(columns={'running_total':'completed'}), how="left", on="snapshot_time")
counts_not_avail['perc_slots_lost'] = counts_not_avail['running_total'] / (counts_not_avail['running_total'] + counts_not_avail['completed'])

counts_not_avail = counts_not_avail.reset_index(drop=True)

fig = generate_animation(
        full_entity_df_plus_pos=full_patient_df_plus_pos,
        entity_col_name="patient",
        event_position_df=event_position_df,
        scenario=args,
        plotly_height=600,
        plotly_width=1000,
        override_x_max=1000,
        override_y_max=700,
        entity_icon_size=11,
        resource_icon_size=13,
        text_size=14,
        wrap_resources_at=40,
        gap_between_resources=20,
        include_play_button=True,
        add_background_image=None,
        # we want the stage labels, but due to a bug
        # when we add in additional animated traces later,
        # they will disappear - so better to leave them out here
        # and then re-add them manually
        display_stage_labels=True,
        custom_resource_icon="🛏️",
        time_display_units="d",
        simulation_time_unit="days",
        start_date="2022-06-27",
        setup_mode=False,
        frame_duration=1500, #milliseconds
        frame_transition_duration=1000, #milliseconds
        debug_mode=False
    )
# Set up the desired subplot layout
ROWS = 4

sp = make_subplots(
    rows=ROWS,
    cols=1,
    row_heights=[0.75, 0.05, 0.05, 0.15],
    vertical_spacing=0.05,
    subplot_titles=(
        "", # Original Animation
        "", # Completed Operations
        "", # Lost Slot Cumulative Counts
        "" # Daily Lost Slots Plot
        )
    )

# Overwrite the domain of our original x and y axis with domain from the new axis
fig.layout['xaxis']['domain'] = sp.layout['xaxis']['domain']
fig.layout['yaxis']['domain'] = sp.layout['yaxis']['domain']

for i in range(2, ROWS+1):

    # Add in the attributes for the secondary axis from our subplot
    fig.layout[f'xaxis{i}'] = sp.layout[f'xaxis{i}']
    fig.layout[f'yaxis{i}'] = sp.layout[f'yaxis{i}']

# Final key step - copy over the _grid_ref attribute
# This isn't meant to be something we modify but it's an essential
# part of the subplot code because otherwise plotly doesn't truly know
# how the different subplots are arranged and referenced
fig._grid_ref = sp._grid_ref

fig.update_layout(
    xaxis2=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=False,
    ),
    yaxis2=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=False,
    ),
    xaxis3=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=False,
    ),
    yaxis3=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        showticklabels=False,
    ),
    xaxis4=dict(
        showticklabels=False
    )
)

#####################################################
# Adding additional animation traces
#####################################################

#####################################################
# Initialize static and animated traces
#####################################################

## First, add each trace so it will show up initially

# Plotly requires that all traces that will appear in animation frames are first
# defined in `fig.data`. Otherwise, they appear to "fly in" from undefined positions,
# or exhibit flickering due to missing interpolation references.

# We add each trace in order, with placeholder data and correct styling,
# so the animation engine has full knowledge of the traces from the outset.

# Due to issues detailed in the following SO threads, it's essential to initialize the traces
# outside of the frames argument else they will not show up at all (or show up intermittently)
# https://stackoverflow.com/questions/69867334/multiple-traces-per-animation-frame-in-plotly
# https://stackoverflow.com/questions/69367344/plotly-animating-a-variable-number-of-traces-in-each-frame-in-r
# TODO: More explanation and investigation needed of why sometimes traces do and don't show up after being added in
# via this method. Behaviour seems very inconsistent and not always logical (e.g. order you put traces in to the later
# loop sometimes seems to make a difference but sometimes doesn't; making initial trace transparent sometimes seems to
# stop it showing up when added in the frames but not always; sometimes the initial trace doesn't disappear).

# First, extract the trace containing the resource icons
position_label_trace = fig.data[1]
icon_trace = fig.data[2]

# Now keep our figure data as just the initial trace.
fig.data = (fig.data[0],)

# 1. BED ICONS TRACE
# Readd the bed icons trace in a consistent manner
# Confusingly, when we start messing with the naimation frames, we lose the bed/resource icon trace
# even though it appeared fine until this point - so we have to handle it here
fig.add_trace(icon_trace)

# print(f"Length after adding bed trace: {len(fig.data)}")

# 2. EVENT LABELS (static position text, but added dynamically per frame to avoid disappearing)
# This is a similar thing to the fig labels - except we never added them in the first place!
# Add trace for the event labels (as these get lost from the animation once we start trying to add other things in,
# so need manually re-adding)
# fig.add_trace(go.Scatter(
#         x=[pos+10 for pos in event_position_df['x'].to_list()],
#         y=event_position_df['y'].to_list(),
#         mode="text",
#         name="",
#         text=event_position_df['label'].to_list(),
#         textposition="middle right",
#         hoverinfo='none'
#     ))

fig.add_trace(position_label_trace)

# Finally, match the font size for the position labels
fig.data[-1].textfont.size

# print(f"Length after adding 'position labels:' trace: {len(fig.data)}")

# 3. OPERATIONS COMPLETED TEXT (animated text annotation)
# Add animated text trace that gives running total of operations completed
fig.add_trace(go.Scatter(
                x=[5],
                y=[10],
                # text="",
                text=f"Operations Completed: {int(counts_ops_completed['running_total'][0])}",
                mode='text',
                textposition="middle left",
                textfont=dict(size=20),
                # opacity=0,
                showlegend=False,
                xaxis="x2",
                yaxis="y2"
        ), row=2, col=1)

# print(f"Length after adding 'operations completed:' trace: {len(fig.data)}")

# 4. SLOTS LOST TEXT (animated text annotation)
# Add animated trace giving running total of slots lost and percentage of total slots this represents
fig.add_trace(go.Scatter(
    x=[5],
    y=[10],
    # text="",
    text=f"Total slots lost: {int(counts_not_avail['running_total'][0])} ({counts_not_avail['perc_slots_lost'][0]:.1%})",
    mode='text',
    textfont=dict(size=20),
    # opacity=0,
    showlegend=False,
    textposition="middle left",
    xaxis="x3",
    yaxis="y3"
), row=3, col=1)

# print(f"Length after adding 'slots lost:' trace: {len(fig.data)}")


# # 5. LINE PLOT ON SECONDARY AXIS (animated line in subplot)
# Initialize with a single point and assign it to subplot axes (x2/y2)
fig.add_trace(go.Scatter(
    x=[counts_not_avail['snapshot_time'].iloc[0]],
    y=[counts_not_avail['patient_x'].iloc[0]],
    mode="lines",
    line=dict(color="rgba(255,0,0,1)"),  # semi-transparent initial
    showlegend=False,
    name="slots_lost_line",
    xaxis="x4",
    yaxis="y4"
    # We place it in our new subplot using the following line
), row=4, col=1)


# Add an initial trace to our secondary line chart
fig.add_trace(go.Scatter(
    x=counts_not_avail['snapshot_time'],
    y=counts_not_avail['patient_x'],
    mode='lines',
    showlegend=False,
    # name='line',
    opacity=0.2,
    xaxis="x4",
    yaxis="y4"
    # We place it in our new subplot using the following line
), row=4, col=1)

# print(f"Length after adding additional line plot trace: {len(fig.data)}")


##########################################################
# Define animation frames: one per simulation time step
##########################################################

##########################################################
# Now we need to add our traces to each individual frame
##########################################################
# IMPORTANT: To work correctly, these need to be provided in the same order as the traces above

# This includes:
# 0: bed icons
# 1: event labels
# 2: operations completed text
# 3: slots lost text
# 4: time series line in subplot

# # Now ensure we tell it which traces we are animating
# # (as per https://chart-studio.plotly.com/~empet/15243/animating-traces-in-subplotsbr/#/)
for i, frame in enumerate(fig.frames):
    # Your original frame.data
    # This will be a tuple
    # We'll ensure we only take the first entry
    # original_data = (frame.data[0], )

    original_data = frame.data

    # if i == 5:
    #     print(original_data)

    # The new data you want to add for this specific frame
    new_data = (
        # 0: bed icons
        icon_trace,

        # 1: Position labels
        go.Scatter(
            x=[pos+10 for pos in event_position_df['x'].to_list()],
            y=event_position_df['y'].to_list(),
            mode="text",
            text=event_position_df['label'].to_list(),
            textposition="middle right",
            hoverinfo='none',
            showlegend=False,
        ),

        # 2: Slots used/operations occurred
        go.Scatter(
            x=[5],
            y=[10],
            text=f"Operations Completed: {int(counts_ops_completed.sort_values('snapshot_time')['running_total'][i])}",
            mode='text',
            textposition="middle left",
            textfont=dict(size=20),
            showlegend=False,
            xaxis='x2',
            yaxis='y2'
        ),

        # 3: Slots lost
        go.Scatter(
            x=[5],
            y=[10],
            text=f"Total slots lost: {int(counts_not_avail.sort_values('snapshot_time')['running_total'][i])} ({counts_not_avail.sort_values('snapshot_time')['perc_slots_lost'][i]:.1%})",
            mode='text',
            textfont=dict(size=20),
            textposition="middle left",
            showlegend=False,
            xaxis='x3',
            yaxis='y3'
        ),

        # 4: Line subplot
        go.Scatter(
            x=counts_not_avail.sort_values('snapshot_time')['snapshot_time'][0: i+1].values,
            y=counts_not_avail.sort_values('snapshot_time')['patient_x'][0: i+1].values,
            mode="lines",
            showlegend=False,
            name="line_subplot",
            line=dict(color="rgba(255,0,0,1)"),  # semi-transparent initial
            xaxis='x4',
            yaxis='y4'
        ),
    )

    # print(f"Type of new data: {type(new_data)}")

    # Combine the original frame data with your new data
    frame.data = original_data + new_data

    # if i == 5:
    #     print(frame.data)

    # print(f"Type of final frame data: {type(frame.data)}")

# Finally, match the font size for the position labels
fig.data[2].textfont.size

fig.update_layout(
        plot_bgcolor='white',
    )
