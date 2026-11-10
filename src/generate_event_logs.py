
import pandas as pd
import random
from pathlib import Path
from datetime import datetime, timedelta

# --------------------------------------------------
# CAREFLOW: HOSPITAL EVENT LOG GENERATOR
# --------------------------------------------------

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "hospital_event_logs.csv"

ACTIVITIES = [
    "Registration",
    "Triage",
    "Doctor Consultation",
    "Laboratory Test",
    "X-Ray",
    "Treatment",
    "Discharge"
]

DEPARTMENTS = [
    "Emergency",
    "General Medicine",
    "Laboratory",
    "Radiology"
]

RESOURCES = [
    "Nurse",
    "Doctor",
    "Lab Technician",
    "Radiologist"
]


def generate_events():

    events = []
    event_id = 1

    for patient_id in range(1, 201):

        current_time = datetime(2026, 1, 1) + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 12)
        )

        activities = ACTIVITIES.copy()

        # Introduce repeated triage events
        if random.random() < 0.20:
            activities.insert(2, "Triage")

        # Introduce occasional repeated consultation
        if random.random() < 0.10:
            activities.insert(4, "Doctor Consultation")

        for activity in activities:

            current_time += timedelta(
                minutes=random.randint(5, 60)
            )

            events.append({
                "Patient_ID": patient_id,
                "Event_ID": event_id,
                "Activity": activity,
                "Event_Timestamp": current_time,
                "Department": random.choice(DEPARTMENTS),
                "Resource": random.choice(RESOURCES)
            })

            event_id += 1

    df = pd.DataFrame(events)

    df = df.sort_values(
        ["Patient_ID", "Event_Timestamp"]
    )

    df.to_csv(OUTPUT_FILE, index=False)

    print("CareFlow event log generated successfully!")
    print(f"Total events: {len(df)}")
    print(f"Total patients: {df['Patient_ID'].nunique()}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_events()
