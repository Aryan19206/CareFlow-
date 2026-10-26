
from pathlib import Path
import random

import pandas as pd


# ============================================================
# CAREFLOW: SIMULATED HOSPITAL EHR EVENT LOG GENERATOR
# Scope: Week 1 - EHR Simulation
# ============================================================

RANDOM_SEED = 42
NUMBER_OF_PATIENTS = 200

random.seed(RANDOM_SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "hospital_event_logs.csv"

ACTIVITIES = [
    "Registration",
    "Triage",
    "Doctor Consultation",
    "Laboratory Test",
    "X-Ray",
    "Treatment",
    "Discharge",
]


ACTIVITY_DURATIONS = {
    "Registration": (3, 10),
    "Triage": (5, 20),
    "Doctor Consultation": (10, 35),
    "Laboratory Test": (15, 60),
    "X-Ray": (10, 40),
    "Treatment": (10, 45),
    "Discharge": (3, 15),
}


def random_duration(activity):
    """Return a simulated duration for an activity in minutes."""
    minimum, maximum = ACTIVITY_DURATIONS[activity]
    return random.randint(minimum, maximum)


def generate_patient_events(patient_number):
    """Generate a chronological event sequence for one patient."""

    case_id = f"CF{patient_number:04d}"

    arrival_time = (
        pd.Timestamp("2026-01-01 08:00:00")
        + pd.Timedelta(minutes=random.randint(0, 30 * 24 * 60))
    )

    events = []
    current_time = arrival_time

    # The standard starting activities.
    events.append(("Registration", current_time))
    current_time += pd.Timedelta(
        minutes=random_duration("Registration")
        + random.randint(1, 10)
    )

    events.append(("Triage", current_time))
    current_time += pd.Timedelta(
        minutes=random_duration("Triage")
        + random.randint(5, 30)
    )

    events.append(("Doctor Consultation", current_time))
    current_time += pd.Timedelta(
        minutes=random_duration("Doctor Consultation")
        + random.randint(5, 45)
    )

    
    pathway = random.choices(
        population=[
            "simple",
            "laboratory",
            "imaging",
            "laboratory_and_imaging",
        ],
        weights=[30, 30, 25, 15],
        k=1,
    )[0]

    if pathway in ("laboratory", "laboratory_and_imaging"):
        current_time += pd.Timedelta(minutes=random.randint(5, 25))
        events.append(("Laboratory Test", current_time))

        current_time += pd.Timedelta(
            minutes=random_duration("Laboratory Test")
        )

    if pathway in ("imaging", "laboratory_and_imaging"):
        current_time += pd.Timedelta(minutes=random.randint(5, 25))
        events.append(("X-Ray", current_time))

        current_time += pd.Timedelta(
            minutes=random_duration("X-Ray")
        )

    # Simulate operational rework.
    # Some patients must return to Triage after a test.
    if pathway in ("imaging", "laboratory_and_imaging"):
        if random.random() < 0.40:
            current_time += pd.Timedelta(minutes=random.randint(2, 15))
            events.append(("Triage", current_time))

            current_time += pd.Timedelta(
                minutes=random_duration("Triage")
            )

   
    if random.random() < 0.15:
        current_time += pd.Timedelta(minutes=random.randint(5, 20))
        events.append(("Doctor Consultation", current_time))

        current_time += pd.Timedelta(
            minutes=random_duration("Doctor Consultation")
        )

    # Treatment and discharge.
    current_time += pd.Timedelta(minutes=random.randint(5, 20))
    events.append(("Treatment", current_time))

    current_time += pd.Timedelta(
        minutes=random_duration("Treatment")
        + random.randint(5, 20)
    )

    events.append(("Discharge", current_time))

    # Convert events into raw EHR-style records.
    records = []

    for sequence_number, (activity, timestamp) in enumerate(events, start=1):
        records.append(
            {
                "Patient_ID": case_id,
                "Event_ID": f"{case_id}-E{sequence_number:02d}",
                "Activity": activity,
                "Event_Timestamp": timestamp,
                "Department": (
                    "Radiology"
                    if activity == "X-Ray"
                    else "Laboratory"
                    if activity == "Laboratory Test"
                    else "Emergency"
                ),
                "Resource": f"Staff-{random.randint(1, 15):02d}",
            }
        )

    return records


def main():
    """Generate and save the complete simulated event log."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_events = []

    for patient_number in range(1, NUMBER_OF_PATIENTS + 1):
        all_events.extend(generate_patient_events(patient_number))

    event_log = pd.DataFrame(all_events)

    # Sort events chronologically for the raw event log.
    event_log = event_log.sort_values(
        ["Event_Timestamp", "Patient_ID", "Event_ID"]
    ).reset_index(drop=True)

    event_log.to_csv(OUTPUT_FILE, index=False)

    rework_count = (
        event_log.groupby("Patient_ID")["Activity"]
        .apply(lambda activities: (activities == "Triage").sum() > 1)
        .sum()
    )

    print("=" * 60)
    print("CAREFLOW: EHR EVENT LOG GENERATION COMPLETED")
    print("=" * 60)
    print(f"Patients generated: {event_log['Patient_ID'].nunique()}")
    print(f"Total events: {len(event_log)}")
    print(f"Patients with repeated Triage: {rework_count}")
    print(f"Output file: {OUTPUT_FILE}")
    print("\nFirst 10 event records:")
    print(event_log.head(10).to_string(index=False))
    print("\nMissing values per column:")
    print(event_log.isna().sum().to_string())
    print("=" * 60)


if __name__ == "__main__":
    main()
