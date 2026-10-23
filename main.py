
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = PROJECT_ROOT / "data" / "raw" / "hospital_event_logs.csv"
OUTPUT_DIR = PROJECT_ROOT / "process_mining" / "outputs"

PROCESS_MAP_PATH = OUTPUT_DIR / "process_map.png"
ACTIVITY_PATH = OUTPUT_DIR / "activity_frequencies.csv"
TRIAGE_PATH = OUTPUT_DIR / "triage_rework_cases.csv"
NORMALIZED_PATH = OUTPUT_DIR / "normalized_event_log.csv"



st.set_page_config(
    page_title="CareFlow | Clinical Process Mining",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 CareFlow")
st.subheader("Clinical Pathway Process Mining")
st.caption(
    "Explore hospital patient pathways, activity frequencies, "
    "and repeated triage events."
)

st.divider()


@st.cache_data
def load_csv(path):
    return pd.read_csv(path)


if not DATA_PATH.exists():
    st.error(f"Hospital event log not found: {DATA_PATH}")
    st.stop()

try:
    raw_df = load_csv(DATA_PATH)
except Exception as exc:
    st.error(f"Could not load the hospital event log: {exc}")
    st.stop()


# Support the column names used in the project.
case_candidates = ["Case_ID", "Patient_ID", "case_id"]
activity_candidates = ["Activity", "Activity_Name", "activity"]
timestamp_candidates = [
    "Event_Timestamp",
    "Timestamp",
    "timestamp",
]

def find_column(candidates, columns):
    for column in candidates:
        if column in columns:
            return column
    return None


case_col = find_column(case_candidates, raw_df.columns)
activity_col = find_column(activity_candidates, raw_df.columns)
timestamp_col = find_column(timestamp_candidates, raw_df.columns)

if not case_col or not activity_col or not timestamp_col:
    st.error("The event log is missing one or more required columns.")
    st.write("Available columns:", raw_df.columns.tolist())
    st.stop()

df = raw_df.copy()

df[timestamp_col] = pd.to_datetime(
    df[timestamp_col], errors="coerce"
)

df = df.dropna(
    subset=[case_col, activity_col, timestamp_col]
).copy()

df = df.sort_values(
    [case_col, timestamp_col]
).reset_index(drop=True)



st.sidebar.title("CareFlow Navigation")

page = st.sidebar.radio(
    "Select a page",
    [
        "Overview",
        "Process Map",
        
        
        "Activity Analysis",
        "Triage Rework",
        "Event Log Explorer",
    ],
)

st.sidebar.divider()
st.sidebar.write("**Data source:** Hospital event log CSV")
st.sidebar.write(f"**Valid events:** {len(df):,}")
st.sidebar.write(f"**Patient cases:** {df[case_col].nunique():,}")


# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

if page == "Overview":
    st.header("Project Overview")

    total_events = len(df)
    total_patients = df[case_col].nunique()
    total_activities = df[activity_col].nunique()
    missing_values = int(raw_df.isna().sum().sum())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Events", f"{total_events:,}")
    col2.metric("Unique Patients", f"{total_patients:,}")
    col3.metric("Unique Activities", f"{total_activities:,}")
    col4.metric("Missing Cells", f"{missing_values:,}")

    st.divider()

    st.subheader("Hospital Activity Distribution")

    activity_counts = (
        
        df[activity_col]
        .value_counts()
        .rename_axis("Activity")
        .reset_index(name="Event Count")
    )

    st.bar_chart(
        activity_counts.set_index("Activity")["Event Count"]
    )

    st.subheader("Event Log Preview")
    st.dataframe(df.head(10), use_container_width=True)

    st.info(
        
        "Use the sidebar to explore the discovered process map, "
        "activity frequencies, and repeated triage events."
    )



# PROCESS MAP


elif page == "Process Map":
    st.header("Discovered Clinical Process")

    if PROCESS_MAP_PATH.exists():
        st.image(
            str(PROCESS_MAP_PATH),
            caption="PM4Py Inductive Miner process map",
            use_container_width=True,
        )
        st.success("Process map loaded from the existing analysis output.")
    else:
        
        st.warning("The process map has not been generated yet.")
        st.code("python process_mining/analysis.py", language="bash")

    st.markdown(
        """
        **How to read the map**

        
        - Rectangles represent activities.
        - Circles represent process states or transitions.
        - Arrows represent possible paths through the patient journey.
        - Branches indicate alternative routes in the discovered model.
        """
    )




elif page == "Activity Analysis":
    st.header("Activity Frequency Analysis")

    activity_counts = (
        df[activity_col]
        
        .value_counts()
        
        .rename_axis("Activity")
        .reset_index(name="Event Count")
    )

    if ACTIVITY_PATH.exists():
        try:
            saved_counts = load_csv(ACTIVITY_PATH)
            st.caption("Saved process-mining activity summary")
        
            st.dataframe(saved_counts, use_container_width=True)
        except Exception:
            st.dataframe(activity_counts, use_container_width=True)
    else:
        
        st.dataframe(activity_counts, use_container_width=True)

    st.subheader("Compare Activity Counts")
    st.bar_chart(
        activity_counts.set_index("Activity")["Event Count"]
    )

    csv_bytes = activity_counts.to_csv(index=False).encode("utf-8")

    st.download_button(
        
        "Download Activity Frequencies",
        data=csv_bytes,
        file_name="activity_frequencies.csv",
        
        mime="text/csv",
    )



# TRIAGE REWORK


elif page == "Triage Rework":
    st.header("Triage Rework Detection")

    triage_mask = df[activity_col].astype(str).str.contains(
        "triage", case=False, na=False
    )

    triage_events = df.loc[triage_mask].copy()

    triage_counts = (
        triage_events.groupby(case_col)
        .size()
        .rename("Triage Event Count")
        .reset_index()
    )

    repeated_triage = triage_counts[
        triage_counts["Triage Event Count"] > 1
    ].copy()

    col1, col2, col3 = st.columns(3)

    col1.metric("Patients with Triage", f"{len(triage_counts):,}")
    col2.metric("Repeated Triage Cases", f"{len(repeated_triage):,}")
    col3.metric("Triage Events", f"{len(triage_events):,}")

    st.subheader("Patients with Repeated Triage")

    if not repeated_triage.empty:
        st.dataframe(
            
            repeated_triage,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Repeated Triage Cases",
            data=repeated_triage.to_csv(index=False).encode("utf-8"),
            
            file_name="triage_rework_cases.csv",
            mime="text/csv",
        )
    else:
        st.success("No repeated triage events were detected.")

    st.caption(
        "Repeated triage is an indicator of possible rework. "
        "It does not, by itself, explain why the patient returned."
    )

    if TRIAGE_PATH.exists():
        with st.expander("View saved analysis results"):
            
            try:
                saved_triage = load_csv(TRIAGE_PATH)
            
                st.dataframe(saved_triage, use_container_width=True)
            except Exception as exc:
                st.warning(f"Could not read saved triage results: {exc}")


# EVENT LOG EXPLORER

elif page == "Event Log Explorer":
    st.header("Hospital Event Log Explorer")

    st.write("Filter the event log to inspect individual patient pathways.")

    patient_ids = sorted(df[case_col].astype(str).unique().tolist())

    selected_patient = st.selectbox(
        "Select a patient or case",


        options=["All Patients"] + patient_ids,

    )


    filtered_df = df.copy()


    if selected_patient != "All Patients":
        filtered_df = filtered_df[
            filtered_df[case_col].astype(str) == selected_patient
        ]

    st.metric("Events Displayed", f"{len(filtered_df):,}")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "Download Displayed Events",


        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="careflow_event_log.csv",

        mime="text/csv",
    )



st.divider()
st.caption(

    "CareFlow | Clinical Pathway Process Mining | "
    "Educational project using simulated hospital event data"
)
