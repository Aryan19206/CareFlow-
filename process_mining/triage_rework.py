
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# CAREFLOW: TRIAGE REWORK LOOP DETECTION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "hospital_event_logs.csv"
OUTPUT_DIR = PROJECT_ROOT / "process_mining" / "outputs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    # Load event log
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Event log not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    # Identify the correct column names
    patient_candidates = ["Patient_ID", "Case_ID", "case_id"]
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
            f"Required column not found: {candidates}. "
            f"Available columns: {df.columns.tolist()}"
        )

    patient_col = find_column(patient_candidates)
    activity_col = find_column(activity_candidates)
    timestamp_col = find_column(timestamp_candidates)

    # Standardize data for analysis
    df[timestamp_col] = pd.to_datetime(
        df[timestamp_col], errors="coerce"
    )

    df = df.dropna(
        subset=[patient_col, activity_col, timestamp_col]
    )

    df[activity_col] = df[activity_col].astype(str).str.strip()

    # Sort events chronologically for each patient
    df = df.sort_values(
        [patient_col, timestamp_col]
    ).reset_index(drop=True)

    # Select triage-related events
    triage_mask = df[activity_col].str.contains(
        "triage", case=False, na=False
    )

    triage_events = df.loc[
        triage_mask,
        [patient_col, activity_col, timestamp_col],
    ].copy()

    # Count triage events for each patient
    triage_counts = (
        triage_events.groupby(patient_col)
        .size()
        .reset_index(name="Triage_Event_Count")
    )

    # More than one triage event is a potential rework signal
    rework_patients = triage_counts[
        triage_counts["Triage_Event_Count"] > 1
    ].copy()

    # Save all patients with repeated triage events
    rework_patients = rework_patients.sort_values(
        "Triage_Event_Count", ascending=False
    )

    output_path = OUTPUT_DIR / "triage_rework_patients.csv"
    rework_patients.to_csv(output_path, index=False)

    # Summary
    total_patients = df[patient_col].nunique()
    patients_with_triage = triage_events[patient_col].nunique()
    repeated_triage_patients = rework_patients[patient_col].nunique()
    total_triage_events = len(triage_events)

    print("\n========== CAREFLOW TRIAGE REWORK REPORT ==========")
    print(f"Total patients analyzed: {total_patients}")
    print(f"Patients with triage events: {patients_with_triage}")
    print(f"Total triage events: {total_triage_events}")
    print(f"Patients with repeated triage: {repeated_triage_patients}")

    if patients_with_triage:
        percentage = (
            repeated_triage_patients / patients_with_triage
        ) * 100
        print(f"Repeated-triage percentage: {percentage:.2f}%")

    print("\nPatients with repeated triage:")
    if rework_patients.empty:
        print("No repeated triage events found.")
    else:
        print(rework_patients.to_string(index=False))

    print(f"\nResults saved to: {output_path}")
    print("===================================================\n")


if __name__ == "__main__":
    main()
