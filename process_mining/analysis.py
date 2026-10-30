from pathlib import Path

import pandas as pd
import pm4py



PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "hospital_event_logs.csv"
OUTPUT_DIR = PROJECT_ROOT / "process_mining" / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_event_log():
    """Load and validate the hospital event log."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Event log not found: {DATA_PATH}\n"
            "Check that hospital_event_logs.csv exists in data/raw/."
        )

    df = pd.read_csv(DATA_PATH)

    # Support the column names used by the current project.
    case_candidates = ["Case_ID", "Patient_ID", "case_id"]
    activity_candidates = ["Activity", "Activity_Name", "activity"]
    timestamp_candidates = [
        "Event_Timestamp",
        "Timestamp",
        "timestamp",
    ]

    def find_column(candidates):
        for column in candidates:
            if column in df.columns:
                return column
        raise ValueError(
            f"Required column not found. Expected one of: {candidates}. "
            f"Available columns: {df.columns.tolist()}"
        )

    case_col = find_column(case_candidates)
    activity_col = find_column(activity_candidates)
    timestamp_col = find_column(timestamp_candidates)

    # Normalize the required fields for PM4Py.
    df = df.rename(
        columns={
            case_col: "case:concept:name",
            activity_col: "concept:name",
            timestamp_col: "time:timestamp",
        }
    )

    df["time:timestamp"] = pd.to_datetime(
        df["time:timestamp"], errors="coerce"
    )

    # Remove rows that cannot be used for process discovery.
    df = df.dropna(
        subset=["case:concept:name", "concept:name", "time:timestamp"]
    ).copy()

    df["case:concept:name"] = df["case:concept:name"].astype(str)
    df["concept:name"] = df["concept:name"].astype(str)

    # Sort each patient's events chronologically.
    df = df.sort_values(
        ["case:concept:name", "time:timestamp"]
    ).reset_index(drop=True)

    return df


def discover_process_map(df):
    """Discover a process model and save its visualization."""
    event_log = pm4py.convert_to_event_log(df)

    net, initial_marking, final_marking = (
        pm4py.discover_petri_net_inductive(event_log)
    )

    output_path = OUTPUT_DIR / "process_map.png"

    pm4py.save_vis_petri_net(
        net,
        initial_marking,
        final_marking,
        str(output_path),
    )

    print(f"Process map saved to: {output_path}")


def analyze_activities(df):
    """Calculate event and activity counts."""
    activity_counts = (
        df["concept:name"]
        .value_counts()
        .rename_axis("Activity")
        .reset_index(name="Event_Count")
    )

    activity_counts.to_csv(
        OUTPUT_DIR / "activity_frequencies.csv", index=False
    )

    print("\nActivity frequencies:")
    print(activity_counts.to_string(index=False))


def detect_triage_rework(df):
    """
    Identify patients who have more than one triage event.

    This detects repeated triage activity, not the cause of the repetition.
    """
    triage_mask = df["concept:name"].str.contains(
        "triage", case=False, na=False
    )

    triage_events = df.loc[
        triage_mask,
        ["case:concept:name", "concept:name", "time:timestamp"],
    ].copy()

    triage_counts = (
        triage_events.groupby("case:concept:name")
        .size()
        .rename("Triage_Event_Count")
    )

    repeated_cases = triage_counts[triage_counts > 1]

    result = repeated_cases.reset_index()
    result = result.rename(
        columns={"case:concept:name": "Case_ID"}
    )

    result.to_csv(
        OUTPUT_DIR / "triage_rework_cases.csv", index=False
    )

    print("\nTriage rework summary:")
    print(f"Patients with triage events: {len(triage_counts)}")
    print(f"Patients with repeated triage: {len(repeated_cases)}")

    if not result.empty:
        print("\nPatients with repeated triage:")
        print(result.to_string(index=False))
    else:
        print("No repeated triage events were found.")


def save_clean_event_log(df):
    """Save a normalized event log for later analysis."""
    output = df.rename(
        columns={
            "case:concept:name": "Case_ID",
            "concept:name": "Activity",
            "time:timestamp": "Timestamp",
        }
    )

    output.to_csv(
        OUTPUT_DIR / "normalized_event_log.csv", index=False
    )

    print(f"\nNormalized event log saved in: {OUTPUT_DIR}")


def main():
    print("=" * 55)
    print("CAREFLOW PROCESS MINING ANALYSIS")
    print("=" * 55)

    df = load_event_log()

    print(f"\nValid events loaded: {len(df)}")
    print(f"Unique cases: {df['case:concept:name'].nunique()}")
    print(f"Unique activities: {df['concept:name'].nunique()}")

    save_clean_event_log(df)
    analyze_activities(df)
    detect_triage_rework(df)
    discover_process_map(df)

    print("\nAnalysis completed successfully.")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
