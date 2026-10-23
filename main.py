from pathlib import Path
import io
import tempfile

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

# PM4Py is required for process discovery.
try:
    import pm4py
    PM4PY_AVAILABLE = True
    PM4PY_IMPORT_ERROR = None
except Exception as exc:
    PM4PY_AVAILABLE = False
    PM4PY_IMPORT_ERROR = str(exc)


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="CareFlow | Clinical Pathway Process Mining",
    page_icon="🏥",
    layout="wide",
)

st.title("CareFlow: Clinical Pathway Process Mining")

st.write(
    "Explore recorded clinical activities, pathways, case durations, "
    "process transitions, and elapsed time between events."
)

st.info(
    "Use authorized data only. This public research dataset is for "
    "practice and does not establish clinical recommendations."
)

if not PM4PY_AVAILABLE:
    st.warning(
        "PM4Py could not be imported. Install it in the active project "
        "environment with: python -m pip install pm4py"
    )
    st.caption(f"Import detail: {PM4PY_IMPORT_ERROR}")


# --------------------------------------------------
# 2. DATA LOADING
# --------------------------------------------------

DEFAULT_FILE = Path("data/sepsis_careflow.csv")


@st.cache_data
def load_data(file_bytes, filename):
    buffer = io.BytesIO(file_bytes)

    if filename.lower().endswith(".xlsx"):
        return pd.read_excel(buffer)

    return pd.read_csv(buffer)


uploaded = st.sidebar.file_uploader(
    "Upload event log (CSV or Excel)",
    type=["csv", "xlsx"],
)

try:
    if uploaded is not None:
        df = load_data(uploaded.getvalue(), uploaded.name)
        source_name = uploaded.name

    elif DEFAULT_FILE.exists():
        df = pd.read_csv(DEFAULT_FILE)
        source_name = str(DEFAULT_FILE)

    else:
        st.warning(
            "Upload an event-log CSV or Excel file to begin."
        )
        st.stop()

    # Standardize column names
    df.columns = [
        str(column).strip().lower()
        for column in df.columns
    ]

    # Support common alternate names where possible.
    aliases = {
        "case:concept:name": "case_id",
        "case id": "case_id",
        "caseid": "case_id",
        "concept:name": "activity",
        "activity_name": "activity",
        "activity name": "activity",
        "time:timestamp": "timestamp",
        "time_stamp": "timestamp",
        "date": "timestamp",
    }
    df = df.rename(
        columns={col: aliases[col] for col in df.columns if col in aliases}
    )

    required_columns = {"case_id", "activity", "timestamp"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        st.error(
            "Missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
        st.write("Columns found:", df.columns.tolist())
        st.stop()

    # --------------------------------------------------
    # 3. DATA CLEANING
    # --------------------------------------------------

    df["case_id"] = df["case_id"].astype("string").str.strip()
    df["activity"] = df["activity"].astype("string").str.strip()

    # Parse timestamps. utc=True handles timezone-aware and naive timestamps.
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True,
    )

    df = df.dropna(
        subset=["case_id", "activity", "timestamp"]
    ).copy()

    df = df[
        (df["case_id"] != "") &
        (df["activity"] != "")
    ].copy()

    if df.empty:
        st.error("No valid events remain after data cleaning.")
        st.stop()

    # Sort chronologically within each case.
    df = df.sort_values(
        ["case_id", "timestamp"]
    ).reset_index(drop=True)

    st.caption(f"Data source: {source_name}")
 # --------------------------------------------------
    # 4. DATASET OVERVIEW
    # --------------------------------------------------

    st.header("Dataset Overview")

    case_summary = (
        df.groupby("case_id")["timestamp"]
        .agg(
            start_time="min",
            end_time="max",
            event_count="size",
        )
    )

    case_summary["duration_hours"] = (
        case_summary["end_time"] - case_summary["start_time"]
    ).dt.total_seconds() / 3600

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric("Recorded Events", f"{len(df):,}")
    metric2.metric("Unique Cases", f"{df['case_id'].nunique():,}")
    metric3.metric("Unique Activities", f"{df['activity'].nunique():,}")
    metric4.metric(
        "Median Case Duration",
        f"{case_summary['duration_hours'].median():.2f} hours",
    )

    st.divider()

    # --------------------------------------------------
    # 5. ACTIVITY FREQUENCY
    # --------------------------------------------------

    st.header("1. Activity Frequency")

    activity_counts = (
        df["activity"]
        .value_counts()
        .rename_axis("Activity")
        .reset_index(name="Event Count")
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    plot_counts = activity_counts.head(15).sort_values("Event Count")

    ax.barh(plot_counts["Activity"], plot_counts["Event Count"])
    ax.set_title("Most Frequently Recorded Activities")
    ax.set_xlabel("Number of Events")
    ax.set_ylabel("Activity")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.dataframe(
        activity_counts,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------
    # 6. CASE DURATION DISTRIBUTION
    # --------------------------------------------------

    st.header("2. Case Duration")

    st.caption(
        "Duration is the time between the first and last recorded event "
        "for each case. It is not necessarily the patient's total hospital stay."
    )

    durations = case_summary["duration_hours"].dropna()
    durations = durations[durations >= 0]

    duration1, duration2 = st.columns(2)
    duration1.metric(
        "Median Duration",
        f"{durations.median():.2f} hours" if not durations.empty else "N/A",
    )
    duration2.metric(
        "Cases with One Recorded Event",
        int((case_summary["event_count"] == 1).sum()),
    )

    if not durations.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.hist(durations, bins=30, edgecolor="black")
        ax.set_title("Distribution of Recorded Case Durations")
        ax.set_xlabel("Elapsed Time (Hours)")
        ax.set_ylabel("Number of Cases")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # --------------------------------------------------
    # 7. MOST COMMON RECORDED PATHWAYS
    # --------------------------------------------------

    st.header("3. Most Common Recorded Pathways")

    pathway_rows = []

    for case_id, group in df.groupby("case_id", sort=False):
        activities = group["activity"].tolist()
        pathway_rows.append({
            "case_id": case_id,
            "event_count": len(activities),
            "pathway": " → ".join(activities),
        })

    pathways = pd.DataFrame(pathway_rows)

    pathway_counts = (
        pathways.groupby("pathway")
        .agg(
            cases=("case_id", "nunique"),
            events_per_pathway=("event_count", "first"),
        )
        .reset_index()
        .sort_values("cases", ascending=False)
    )

    st.dataframe(
        pathway_counts.head(20),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Pathways are sequences of recorded activity labels. "
        "Cases with the same sequence are grouped together."
    )

    # --------------------------------------------------
    # 8. PROCESS TRANSITIONS
    # --------------------------------------------------

    st.header("4. Process Flow Analysis")

    transitions = df.copy()
    transitions["next_activity"] = (
        transitions.groupby("case_id")["activity"].shift(-1)
    )
    transitions["next_timestamp"] = (
        transitions.groupby("case_id")["timestamp"].shift(-1)
    )
    transitions["elapsed_hours"] = (
        transitions["next_timestamp"] - transitions["timestamp"]
    ).dt.total_seconds() / 3600

    transitions = transitions.dropna(
        subset=["next_activity", "elapsed_hours"]
    ).copy()
    transitions = transitions[transitions["elapsed_hours"] >= 0].copy()

    transition_summary = pd.DataFrame()

    if transitions.empty:
        st.info("No valid consecutive activity transitions were found.")
    else:
        transitions["transition"] = (
            transitions["activity"] + " → " + transitions["next_activity"]
        )

        transition_summary = (
            transitions.groupby("transition")
            .agg(
                occurrences=("elapsed_hours", "size"),
                median_elapsed_hours=("elapsed_hours", "median"),
                mean_elapsed_hours=("elapsed_hours", "mean"),
            )
            .reset_index()
            .sort_values("occurrences", ascending=False)
        )

        st.subheader("Most Frequent Transitions")
        st.bar_chart(
            transition_summary.head(15).set_index("transition")["occurrences"]
        )
        st.dataframe(
            transition_summary.head(20),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Transitions with Longest Median Elapsed Time")
        longest_transitions = (
            transition_summary.sort_values(
                "median_elapsed_hours", ascending=False
            ).head(15)
        )
        st.dataframe(
            longest_transitions,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Elapsed time is the interval between consecutive recorded events. "
            "It is a candidate delay measure, not necessarily actual waiting time."
        )

        st.subheader("Inspect an Individual Transition")
        available_transitions = sorted(transitions["transition"].unique().tolist())
        selected_transition = st.selectbox(
            "Choose a transition",
            available_transitions,
        )
        selected_rows = transitions[
            transitions["transition"] == selected_transition
        ]

        a, b, c = st.columns(3)
        a.metric("Occurrences", f"{len(selected_rows):,}")
        b.metric(
            "Median Elapsed Hours",
            f"{selected_rows['elapsed_hours'].median():.2f}",
        )
        c.metric(
            "Mean Elapsed Hours",
            f"{selected_rows['elapsed_hours'].mean():.2f}",
        )

    # --------------------------------------------------
    # 9. REPEATED-ACTIVITY REWORK ANALYSIS
    # --------------------------------------------------

    st.header("5. Repeated-Activity Rework Analysis")

    st.write(
        "Analyze repeated clinical activities in the current sepsis event log. "
"This section does not assume X-Ray events exist."
    )

    rework_source = df.sort_values(
        ["case_id", "timestamp"]
    ).copy()

    rework_source["_activity_norm"] = (
        rework_source["activity"]
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    # Allow an activity label to be selected from those present in the dataset.
    activity_labels = sorted(
        rework_source["activity"].dropna().astype(str).unique().tolist()
    )

    if not activity_labels:
        st.info("No activity labels are available for rework analysis.")
    else:
        selected_rework_activity = st.selectbox(
            "Choose an activity to check for repeated occurrences",
            activity_labels,
            index=(
                next(
                    (
                        i for i, label in enumerate(activity_labels)
                        if "triage" in label.casefold()
                    ),
                    0,
                )
            ),
            key="repeated_activity_selector",
        )

        selected_norm = selected_rework_activity.strip().casefold()
        rework_rows = []

        # A case is flagged if the selected activity occurs at least twice.
        # Each case is counted once in the case-level rate.
        for case_id, group in rework_source.groupby("case_id", sort=False):
            group = group.sort_values("timestamp").reset_index(drop=True)
            normalized = group["_activity_norm"].tolist()
            matching_positions = [
                i for i, activity in enumerate(normalized)
                if activity == selected_norm
            ]

            if len(matching_positions) >= 2:
                first_pos = matching_positions[0]
                second_pos = matching_positions[1]
                first_time = group.loc[first_pos, "timestamp"]
                second_time = group.loc[second_pos, "timestamp"]
                elapsed_minutes = (
                    second_time - first_time
                ).total_seconds() / 60

                rework_rows.append({
                    "case_id": case_id,
                    "activity": selected_rework_activity,
                    "occurrences_in_case": len(matching_positions),
                    "first_occurrence": first_time,
                    "second_occurrence": second_time,
                    "elapsed_minutes_between_first_two": elapsed_minutes,
                    "pathway": " → ".join(
                        group["activity"].astype(str).tolist()
                    ),
                })

        repeated_df = pd.DataFrame(rework_rows)
        total_cases = rework_source["case_id"].nunique()
        affected_cases = (
            repeated_df["case_id"].nunique()
            if not repeated_df.empty
            else 0
        )
        repeated_rate = (
            affected_cases / total_cases * 100
            if total_cases
            else 0
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cases", f"{total_cases:,}")
        col2.metric(
            "Cases with Repeated Activity",
            f"{affected_cases:,}",
        )
        col3.metric(
            "Repeated-Activity Case Rate",
            f"{repeated_rate:.2f}%",
        )

        if repeated_df.empty:
            st.info(
                f"No case contains the activity '{selected_rework_activity}' "
                "two or more times."
            )
        else:
            st.subheader("Cases with Repeated Activity")
            st.dataframe(
                repeated_df,
                use_container_width=True,
                hide_index=True,
            )

            st.metric(
                "Median Time Between First Two Occurrences",
                f"{repeated_df['elapsed_minutes_between_first_two'].median():.1f} minutes",
            )

            st.download_button(
                "Download Repeated-Activity Results",
                data=repeated_df.to_csv(index=False).encode("utf-8"),
                file_name="careflow_repeated_activity_analysis.csv",
                mime="text/csv",
            )

        st.caption(
            "A repeated activity is a potential rework signal, not proof of an error "
            "or a cause of delay. The case rate is the share of all cases containing "
            "the selected activity at least twice."
        )

    # --------------------------------------------------
    # 10. PM4Py PROCESS MINING
    # --------------------------------------------------

    st.header("6. PM4Py Process Mining")

    st.write(
        "Discover a Petri-net process model from the observed event log "
        "and inspect the most common process variants."
    )

    if not PM4PY_AVAILABLE:
        st.warning(
            "PM4Py is unavailable in this Python environment. "
            "Install it with: python -m pip install pm4py"
        )
    else:
        pm_df = df[["case_id", "activity", "timestamp"]].copy()
        pm_df = pm_df.rename(
            columns={
                "case_id": "case:concept:name",
                "activity": "concept:name",
                "timestamp": "time:timestamp",
            }
        )
        pm_df = pm_df.sort_values(
            ["case:concept:name", "time:timestamp"]
        ).reset_index(drop=True)

        st.metric(
            "Cases for Process Mining",
            f"{pm_df['case:concept:name'].nunique():,}",
        )
        st.metric("Events for Process Mining", f"{len(pm_df):,}")

        if st.button("Discover Process Model", key="discover_pm4py"):
            try:
                with st.spinner("Discovering process model with PM4Py..."):
                    event_log = pm4py.convert_to_event_log(pm_df)

                    net, initial_marking, final_marking = (
                        pm4py.discover_petri_net_inductive(
                            event_log,
                            noise_threshold=0.0,
                        )
                    )

                    st.success("PM4Py process discovery completed.")
                    st.subheader("Discovered Petri Net")

                    with tempfile.TemporaryDirectory() as temp_dir:
                        image_path = str(
                            Path(temp_dir) / "careflow_process_model.png"
                        )

                        pm4py.save_vis_petri_net(
                            net,
                            initial_marking,
                            final_marking,
                            image_path,
                        )

                        with open(image_path, "rb") as image_file:
                            st.image(
                                image_file.read(),
                                caption="Petri net discovered from the event log",
                                use_container_width=True,
                            )

                    st.subheader("Observed Process Variants")
                    variants = pm4py.get_variants_as_tuples(event_log)

                    variant_rows = []
                    for activities, cases in variants.items():
                        variant_rows.append({
                            "Activity Sequence": " → ".join(
                                str(activity) for activity in activities
                            ),
                            "Case Count": len(cases),
                        })

                    variants_df = pd.DataFrame(variant_rows)

                    if not variants_df.empty:
                        variants_df = variants_df.sort_values(
                            "Case Count", ascending=False
                        )
                        st.dataframe(
                            variants_df.head(20),
                            use_container_width=True,
                            hide_index=True,
                        )
                        st.download_button(
                            "Download Process Variants",
                            data=variants_df.to_csv(index=False).encode("utf-8"),
                            file_name="careflow_pm4py_variants.csv",
                            mime="text/csv",
                        )
                    else:
                        st.info("PM4Py did not return any process variants.")

            except Exception as error:
                st.error(f"PM4Py process mining failed: {error}")
                st.info(
                    "If the error mentions Graphviz, install it on macOS with "
                    "'brew install graphviz', then restart the terminal and "
                    "rerun the dashboard."
                )

    # --------------------------------------------------
    # 11. SPAGHETTI DIAGRAM: ACTUAL PATIENT JOURNEYS
    # --------------------------------------------------

    st.header("11. Spaghetti Diagram: Patient Flow")

    st.write(
        "Visualize recorded patient journeys, repeated activities, "
        "and transitions between clinical activities."
    )

    flow_df = df.sort_values(
        ["case_id", "timestamp"]
    ).copy()

    flow_df["next_activity"] = (
        flow_df.groupby("case_id")["activity"].shift(-1)
    )

    edges_df = flow_df.dropna(
        subset=["next_activity"]
    ).copy()

    edge_counts = (
        edges_df.groupby(["activity", "next_activity"])
        .size()
        .reset_index(name="frequency")
    )

    activity_counts = df["activity"].value_counts().to_dict()

    if edge_counts.empty:
        st.warning(
            "At least one case must contain two recorded activities "
            "to draw a patient-flow diagram."
        )
    else:
        max_edges = min(50, len(edge_counts))

        edge_limit = st.slider(
            "Maximum transitions to display",
            min_value=1,
            max_value=max_edges,
            value=min(20, max_edges),
            key="spaghetti_edge_limit",
        )

        visible_edges = edge_counts.sort_values(
            "frequency", ascending=False
        ).head(edge_limit)

        graph = nx.DiGraph()

        for _, edge in visible_edges.iterrows():
            source = str(edge["activity"])
            target = str(edge["next_activity"])
            frequency = int(edge["frequency"])

            if graph.has_edge(source, target):
                graph[source][target]["weight"] += frequency
            else:
                graph.add_edge(source, target, weight=frequency)

        positions = nx.spring_layout(
            graph,
            seed=42,
            k=1.4,
            iterations=100,
        )

        fig, ax = plt.subplots(figsize=(15, 9))

        node_sizes = [
            700 + 100 * activity_counts.get(node, 1)
            for node in graph.nodes()
        ]

        edge_widths = [
            1.0 + 0.7 * graph[u][v]["weight"] ** 0.5
            for u, v in graph.edges()
        ]

        nx.draw_networkx_nodes(
            graph,
            positions,
            node_size=node_sizes,
            node_color="lightblue",
            edgecolors="black",
            ax=ax,
        )

        nx.draw_networkx_labels(
            graph,
            positions,
            font_size=8,
            ax=ax,
        )

        nx.draw_networkx_edges(
            graph,
            positions,
            width=edge_widths,
            edge_color="gray",
            arrows=True,
            arrowsize=18,
            connectionstyle="arc3,rad=0.08",
            min_source_margin=15,
            min_target_margin=20,
            ax=ax,
        )

        edge_labels = {
            (u, v): graph[u][v]["weight"]
            for u, v in graph.edges()
        }

        nx.draw_networkx_edge_labels(
            graph,
            positions,
            edge_labels=edge_labels,
            font_size=8,
            ax=ax,
            label_pos=0.5,
        )

        ax.set_title(
            "Observed Patient Activity Flow "
            "(edge labels = transition frequency)"
        )
        ax.axis("off")
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        st.caption(
            "Thicker arrows indicate more recorded transitions. "
            "This is an aggregated flow diagram, not a geographical map "
            "or proof of a clinical cause."
        )

        st.subheader("Inspect Individual Patient Journeys")

        case_ids = sorted(
            df["case_id"].dropna().unique().tolist(),
            key=str,
        )

        selected_case = st.selectbox(
            "Select a case to inspect its actual recorded journey",
            case_ids,
            key="spaghetti_selected_case",
        )

        selected_path = df[
            df["case_id"] == selected_case
        ].sort_values("timestamp")

        journey_text = " → ".join(
            selected_path["activity"].astype(str).tolist()
        )

        st.write(f"**Selected case:** {selected_case}")
        st.write(journey_text)

        st.dataframe(
            selected_path[["case_id", "activity", "timestamp"]],
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------
    # 12. DATA QUALITY
    # --------------------------------------------------

    st.header("12. Data Quality")

    quality1, quality2, quality3 = st.columns(3)

    quality1.metric(
        "Valid Events",
        f"{len(df):,}",
    )

    quality2.metric(
        "Duplicate Full Rows",
        int(df.duplicated().sum()),
    )

    quality3.metric(
        "Missing Required Values",
        int(
            df[["case_id", "activity", "timestamp"]]
            .isna()
            .sum()
            .sum()
        ),
    )

    st.subheader("Event Log Preview")

    st.dataframe(
        df.head(50),
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------
    # 13. DOWNLOAD RESULTS
    # --------------------------------------------------

    st.header("13. Export Results")

    cleaned_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Cleaned Event Log",
        data=cleaned_csv,
        file_name="careflow_cleaned_event_log.csv",
        mime="text/csv",
    )

    pathway_csv = pathway_counts.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Pathway Summary",
        data=pathway_csv,
        file_name="careflow_pathway_summary.csv",
        mime="text/csv",
    )

    if not transition_summary.empty:
        transition_csv = transition_summary.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Transition Analysis",
            data=transition_csv,
            file_name="careflow_transition_analysis.csv",
            mime="text/csv",
        )

    # --------------------------------------------------
    # 13. FOOTER
    # --------------------------------------------------

    st.divider()
    st.caption(
        "CareFlow | Clinical Pathway Process Mining | "
        "Exploratory data analysis only"
    )

except Exception as error:
    st.error(f"Could not analyze the dataset: {error}")


# ==================================================
# 14. PROCESS DISCOVERY VISUALIZATION
# ==================================================

from pathlib import Path

st.header("14. Discovered Clinical Process Model")

BASE_DIR = Path(__file__).resolve().parent
PROCESS_MAP = BASE_DIR / "outputs" / "process_map.png"

if PROCESS_MAP.exists():
    st.image(
        str(PROCESS_MAP),
        caption="Process model discovered using PM4Py",
        use_container_width=True,
    )

    st.success("Process map loaded successfully.")

else:
    st.warning(
        "Process map not found. "
        "Run process_discovery.py first."
    )

    # ==================================================
# 15. PROCESS CONFORMANCE ANALYSIS
# ==================================================


st.header("15. Process Conformance Analysis")

BASE_DIR = Path(__file__).resolve().parent

CONFORMANCE_FILE = (
    BASE_DIR / "outputs" / "conformance_summary.csv"
)

if CONFORMANCE_FILE.exists():

    conformance_df = pd.read_csv(CONFORMANCE_FILE)

    if not conformance_df.empty:

        total_cases = len(conformance_df)

        fit_cases = (
            conformance_df["is_fit"]
            .astype(str)
            .str.lower()
            .eq("true")
            .sum()
        )

        fitness = pd.to_numeric(
            conformance_df["trace_fitness"],
            errors="coerce"
        ).dropna()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Cases Evaluated",
            f"{total_cases:,}"
        )

        col2.metric(
            "Cases Marked Fit",
            f"{fit_cases:,}"
        )

        col3.metric(
            "Mean Trace Fitness",
            f"{fitness.mean():.3f}" if not fitness.empty else "N/A"
        )

        st.subheader("Trace Fitness Distribution")

        if not fitness.empty:

            fitness_chart = (
                fitness.rename("Trace Fitness")
                .reset_index(drop=True)
            )

            st.bar_chart(fitness_chart.value_counts().sort_index())

        st.subheader("Case-Level Conformance Results")

        st.dataframe(
            conformance_df.head(100),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            label="Download Conformance Results",
            data=conformance_df.to_csv(index=False).encode("utf-8"),
            file_name="careflow_conformance_summary.csv",
            mime="text/csv"
        )

        st.caption(
            "Interpretation: fitness measures how recorded traces "
            "fit the discovered process model. The model was learned "
            "from this dataset, so these results are not independent "
            "validation of clinical correctness."
        )

    else:
        st.warning("The conformance report is empty.")

else:
    st.warning(
        "Conformance results not found. "
        "Run conformance_analysis.py first."
    )